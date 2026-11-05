"""
DATEX II as a retrieval source: the v3.x data model and the DATEX II documentation portal.

DATEX II (CEN/TS 16157) is the European standard for road traffic and travel information; MMTIS names it
next to NeTEx and SIRI. Two parts are indexed, both from docs.datex2.eu, pinned to one release:

- the data model: the Enterprise Architect model the portal publishes (an SQLite ".qea" file) reduced to a
  JSON file with every class, enumeration and data type, its definition, attributes, literals and
  associations (docs/datex/model-v3.7.json). The XSD files carry no definitions, so they are not used;
- the documentation pages of that release (user guide, levels, recommended profiles), as text snapshots
  (docs/datex/pages/*.md), fetched from the portal's sitemap.

Built like the napcore.eu source (services/napcore_site.py): fetched once on a development machine,
reviewed in git, indexed from there, also on deploy, without network access.

The chunks belong to the opt-in scope "DATEX II": searched only when a question names DATEX II. SIRI's own
copy of the DATEX II situation schema (xsd/datex2/ in the SIRI repository) keeps its SIRI scope as well.

Licence: the DATEX II site and repositories state none (to be clarified with the DATEX II community before
the source is deployed).

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-06  |  Modified: 2026-11-06
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import tempfile
import time
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path

from helpdesk.models import IndexedSourceFile, SourceChunk
from helpdesk.services.embeddings import build_text_embeddings_batch
from helpdesk.services.index_builder import build_chunk_embedding_text, build_content_hash
from helpdesk.services.napcore_site import Snapshot, chunk_snapshot, html_to_text, read_snapshot

SCOPE = "DATEX II"
DOC_TYPE = "datex"
VERSION = "3.7"
PORTAL = "https://docs.datex2.eu"
MODEL_FILE_URL = (
    f"{PORTAL}/_static/data/v{VERSION}/umlmodel/AssembledModelsForConvenience/DatexIIStableV3Namespaces.qea"
)
MODEL_PAGE_URL = f"{PORTAL}/downloads/modelv{VERSION.replace('.', '')}/"
SITEMAP_URL = f"{PORTAL}/v{VERSION}/sitemap.xml"
DATEX_DIR = Path(__file__).resolve().parents[3] / "docs" / "datex"
MODEL_PATH = DATEX_DIR / f"model-v{VERSION}.json"
PAGES_DIR = DATEX_DIR / "pages"
MAX_CHUNK_CHARS = 1500
# Part of the stored content hash: bump it when parsing or chunking changes, so the next run re-indexes.
PARSER_VERSION = "1"
_USER_AGENT = "NAPCORE-Helpdesk-indexer/1.0 (+https://kgpi.fgpa.um.si/napcore-helpdesk/)"
_ELEMENT_TYPES = ("Class", "Enumeration", "DataType")
# Portal pages that are not documentation of the release: downloads lists, the version index.
_SKIPPED_PAGES = re.compile(r"/(?:downloads|json|exchange-2020/downloads)(?:/|$)")


def is_datex_url(url: str) -> bool:
    """True for a link to the DATEX II documentation portal (citation allow-list)."""
    return urllib.parse.urlparse(url or "").netloc.lower() == "docs.datex2.eu"


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:  # nosec B310 - fixed https host
        return response.read()


# ---- The data model -------------------------------------------------------------------------------


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("<br/>", " ")).strip()


def extract_model(qea_path: Path) -> dict:
    """Every class, enumeration and data type of the model with its namespace, definition and members.

    In the model, definitions are tagged values ("definition") of elements and attributes; a namespace is
    a package with the stereotype D2Namespace; associations are D2Relation aggregations."""
    db = sqlite3.connect(f"file:{qea_path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    packages = {row["Package_ID"]: row for row in db.execute("SELECT Package_ID, Name, Parent_ID FROM t_package")}
    # A package's own element (t_object) holds the package id in PDATA1, as text.
    namespace_packages = {
        int(row["PDATA1"])
        for row in db.execute("SELECT PDATA1 FROM t_object WHERE Object_Type='Package' AND Stereotype='D2Namespace'")
        if str(row["PDATA1"] or "").isdigit()
    }

    def location(package_id: int) -> tuple[str, str]:
        """(namespace, package path below it), e.g. ("Situation", "Classes/Impact")."""
        names: list[str] = []
        while package_id in packages:
            if package_id in namespace_packages:
                return packages[package_id]["Name"], "/".join(reversed(names))
            names.append(packages[package_id]["Name"])
            package_id = packages[package_id]["Parent_ID"]
        return "", "/".join(reversed(names))

    def tags(table: str, key: str, ident: int) -> dict[str, str]:
        rows = db.execute(f"SELECT Property, Value, Notes FROM {table} WHERE {key}=?", (ident,))  # nosec B608
        return {row["Property"]: _clean(row["Notes"] or row["Value"]) for row in rows}

    objects = {
        row["Object_ID"]: row
        for row in db.execute(
            "SELECT Object_ID, Name, Object_Type, Stereotype, Package_ID, Note FROM t_object "
            f"WHERE Object_Type IN ({','.join('?' * len(_ELEMENT_TYPES))})",
            _ELEMENT_TYPES,
        )
    }
    supertypes: dict[int, list[str]] = {}
    associations: dict[int, list[dict]] = {}
    for row in db.execute(
        "SELECT Connector_Type, Stereotype, Start_Object_ID, End_Object_ID, DestRole, DestCard, SourceRole, "
        "SourceCard FROM t_connector WHERE Connector_Type IN ('Generalization', 'Aggregation')"
    ):
        start, end = objects.get(row["Start_Object_ID"]), objects.get(row["End_Object_ID"])
        if not (start and end):
            continue
        if row["Connector_Type"] == "Generalization":
            supertypes.setdefault(start["Object_ID"], []).append(end["Name"])
        elif row["Stereotype"] == "D2Relation":
            # The navigable end is the one with a role name; its multiplicity sits on that end.
            if row["DestRole"]:
                owner, target, role, card = start, end, row["DestRole"], row["DestCard"]
            else:
                owner, target, role, card = end, start, row["SourceRole"], row["SourceCard"]
            if role:
                associations.setdefault(owner["Object_ID"], []).append(
                    {"role": role, "target": target["Name"], "multiplicity": card or ""}
                )

    elements = []
    for ident, row in sorted(objects.items(), key=lambda item: (item[1]["Name"] or "").lower()):
        namespace, package = location(row["Package_ID"])
        element_tags = tags("t_objectproperties", "Object_ID", ident)
        members = []
        for attribute in db.execute(
            "SELECT ID, Name, Type, LowerBound, UpperBound FROM t_attribute WHERE Object_ID=? ORDER BY Pos, Name",
            (ident,),
        ):
            attribute_tags = tags("t_attributetag", "ElementID", attribute["ID"])
            lower, upper = attribute["LowerBound"] or "", attribute["UpperBound"] or ""
            members.append(
                {
                    "name": attribute["Name"],
                    "type": attribute["Type"] or "",
                    "multiplicity": f"{lower}..{upper}" if lower or upper else "",
                    "definition": attribute_tags.get("definition", ""),
                }
            )
        elements.append(
            {
                "name": row["Name"],
                "kind": {"Class": "class", "Enumeration": "enumeration", "DataType": "data type"}[row["Object_Type"]],
                "stereotype": row["Stereotype"] or "",
                "namespace": namespace,
                "package": package,
                "definition": element_tags.get("definition") or _clean(row["Note"]),
                "supertypes": sorted(set(supertypes.get(ident, []))),
                "members": members,
                "associations": sorted(associations.get(ident, []), key=lambda a: a["role"].lower()),
            }
        )
    db.close()
    return {"version": VERSION, "source": MODEL_FILE_URL, "elements": elements}


def fetch_model(out_dir: Path) -> int:
    """Download the release's model file and store the extracted model; returns the number of elements."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".qea") as qea:
        qea.write(_get(MODEL_FILE_URL))
        qea.flush()
        model = extract_model(Path(qea.name))
    (out_dir / MODEL_PATH.name).write_text(json.dumps(model, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return len(model["elements"])


def element_text(element: dict) -> str:
    """The element as answers read it: what it is, its definition, then its attributes or literals."""
    place = " / ".join(p for p in (element["namespace"], element["package"]) if p)
    lines = [f"DATEX II {element['kind']} {element['name']} (namespace {place})"]
    if element["definition"]:
        lines.append(f"Definition: {element['definition']}")
    if element["supertypes"]:
        lines.append(f"Subtype of: {', '.join(element['supertypes'])}")
    if element["members"]:
        lines.append("Values:" if element["kind"] == "enumeration" else "Attributes:")
        for member in element["members"]:
            if element["kind"] == "enumeration":
                lines.append(f"- {member['name']}: {member['definition']}".rstrip(": "))
            else:
                detail = ", ".join(p for p in (member["type"], member["multiplicity"]) if p)
                lines.append(f"- {member['name']} ({detail}): {member['definition']}".rstrip(": "))
    if element["associations"]:
        lines.append("Associations:")
        for association in element["associations"]:
            card = f", {association['multiplicity']}" if association["multiplicity"] else ""
            lines.append(f"- {association['role']} -> {association['target']}{card}")
    return "\n".join(lines)


def _pieces(text: str, head: str) -> list[str]:
    """Text in pieces of at most MAX_CHUNK_CHARS, split between lines; later pieces repeat the head line."""
    pieces, current = [], ""
    for line in text.split("\n"):
        if current and len(current) + len(line) + 1 > MAX_CHUNK_CHARS:
            pieces.append(current)
            current = f"{head} (continued)"
        current = f"{current}\n{line}" if current else line
    pieces.append(current)
    return [piece[i : i + MAX_CHUNK_CHARS * 2] for piece in pieces for i in range(0, len(piece), MAX_CHUNK_CHARS * 2)]


def model_records(model: dict) -> list[dict]:
    records = []
    for element in model["elements"]:
        if not element["name"]:
            continue
        key = f"{element['namespace']}.{element['name']}"
        text = element_text(element)
        head = text.split("\n", 1)[0]
        for part, piece in enumerate(_pieces(text, head)):
            records.append(
                {
                    "chunk_id": f"datex-model-{_key(key)}-{part:02d}",
                    "source_path": f"datex-model-v{model['version']}/{key}",
                    "label": f"DATEX II {element['kind']} {element['name']} ({element['namespace']})"[:255],
                    "heading": head[:512],
                    "text": piece,
                    "quality_score": 0.85 if element["definition"] else 0.6,
                    "structured_metadata": {
                        "sourceUrl": MODEL_PAGE_URL,
                        "title": f"DATEX II v{model['version']} {element['name']}",
                        "namespace": element["namespace"],
                    },
                }
            )
    return records


# ---- The documentation portal ----------------------------------------------------------------------


def sitemap_pages(sitemap: bytes) -> list[str]:
    """Pages of the release, as /v<version>/ URLs (the sitemap lists them under the portal root)."""
    urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sitemap.decode("utf-8"))
    pages = []
    for url in urls:
        path = urllib.parse.urlparse(url).path
        if _SKIPPED_PAGES.search(path):
            continue
        pages.append(f"{PORTAL}/v{VERSION}{path if path.startswith('/') else '/' + path}")
    return list(dict.fromkeys(pages))


def page_text(content: str) -> tuple[str, str]:
    """(title, text) of a portal page: the article of the MkDocs page, without navigation and theme."""
    match = re.search(r'(?s)<article class="md-content__inner[^"]*"[^>]*>(.*?)</article>', content)
    body = match.group(1) if match else ""
    body = re.sub(r"(?s)<!--.*?-->", "", body)
    title_match = re.search(r"(?s)<h1[^>]*>(.*?)</h1>", body)
    title = _clean(re.sub(r"<[^>]+>", "", title_match.group(1))) if title_match else ""
    return title.replace("¶", "").strip(), html_to_text(body)


def page_name(url: str) -> str:
    path = urllib.parse.urlparse(url).path.strip("/").removeprefix(f"v{VERSION}").strip("/")
    return re.sub(r"[^A-Za-z0-9._-]+", "_", path.replace("/", "--")) or "home"


def fetch_pages(out_dir: Path, report=None) -> dict[str, int]:
    """Fetch every documentation page of the release into out_dir/pages as text snapshots."""
    pages_dir = out_dir / PAGES_DIR.name
    pages_dir.mkdir(parents=True, exist_ok=True)
    counts = {"pages": 0, "empty": 0, "failed": 0}
    for url in sitemap_pages(_get(SITEMAP_URL)):
        try:
            title, text = page_text(_get(url).decode("utf-8", errors="replace"))
        except Exception as error:  # a page that fails is reported; the others are still fetched
            counts["failed"] += 1
            if report:
                report(f"failed {url}: {error}")
            continue
        if len(text.strip()) < 80:
            counts["empty"] += 1
            continue
        snapshot = f"url: {url}\ntitle: {title or page_name(url)}\n\n{text.strip()}\n"
        (pages_dir / f"{page_name(url)}.md").write_text(snapshot, encoding="utf-8")
        counts["pages"] += 1
        if report:
            report(f"fetched {url}")
        time.sleep(0.2)
    return counts


def _key(name: str) -> str:
    """A chunk id part: a readable prefix plus a hash of the whole name (long page names share a prefix)."""
    return f"{name[:60]}-{hashlib.sha1(name.encode('utf-8')).hexdigest()[:8]}"


def page_records(snapshot: Snapshot) -> list[dict]:
    key = page_name(snapshot.url)
    records = []
    for index, (heading, text, _) in enumerate(chunk_snapshot(snapshot)):
        label = f"DATEX II documentation: {snapshot.title}" + (f" — {heading}" if heading and heading != snapshot.title else "")
        records.append(
            {
                "chunk_id": f"datex-doc-{_key(key)}-{index:03d}",
                "source_path": f"docs.datex2.eu/v{VERSION}/{key}",
                "label": label[:255],
                "heading": (heading or snapshot.title)[:512],
                "text": f"DATEX II v{VERSION} documentation: {snapshot.title}\n{heading}\n\n{text}".replace("\n\n\n", "\n\n"),
                "quality_score": 0.8,
                "structured_metadata": {"sourceUrl": snapshot.url, "title": snapshot.title},
            }
        )
    return records


# ---- Indexing (also on deploy) ---------------------------------------------------------------------

EMBED_SLICE = 4
EMBED_PAUSE_SECONDS = 0.5


def _embed(texts: list[str]) -> list[list[float]]:
    """Embed a few texts at a time with pauses on prod's small embedder (see napcore_site._embed)."""
    from helpdesk.services.embeddings import semantic_enabled

    if not semantic_enabled():
        return build_text_embeddings_batch(texts)
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_SLICE):
        vectors.extend(build_text_embeddings_batch(texts[start : start + EMBED_SLICE]))
        time.sleep(EMBED_PAUSE_SECONDS)
    return vectors


def _index_records(repository_url: str, file_name: str, content: str, records: list[dict]) -> tuple[str, int]:
    content_hash = build_content_hash(f"parser {PARSER_VERSION}\n{content}")
    indexed = IndexedSourceFile.objects.filter(repository_url=repository_url, source_path=file_name).first()
    if indexed and indexed.content_hash == content_hash:
        return "unchanged", SourceChunk.objects.filter(repository_url=repository_url).count()
    embeddings = _embed(
        [
            build_chunk_embedding_text(
                chunk_text=record["text"],
                doc_type=DOC_TYPE,
                chunk_type="prose",
                heading=record["heading"],
                standards_scope=[SCOPE],
                repository_url=repository_url,
                source_path=record["source_path"],
            )
            for record in records
        ]
    )
    SourceChunk.objects.filter(repository_url=repository_url).delete()
    SourceChunk.objects.bulk_create(
        [
            SourceChunk(
                repository_url=repository_url,
                commit_sha=f"v{VERSION}",
                standards_scope=[SCOPE],
                chunk_type="prose",
                doc_type=DOC_TYPE,
                embedding_vector=embedding,
                **record,
            )
            for record, embedding in zip(records, embeddings)
        ]
    )
    IndexedSourceFile.objects.update_or_create(
        repository_url=repository_url,
        source_path=file_name,
        defaults={"commit_sha": f"v{VERSION}", "content_hash": content_hash},
    )
    return "indexed", len(records)


def index_datex(model_path: Path = MODEL_PATH, pages_dir: Path = PAGES_DIR, report=None) -> dict[str, int]:
    """Index the model and every page whose file changed; remove pages no longer present."""
    counts = {"indexed": 0, "unchanged": 0, "removed": 0, "chunks": 0}
    content = model_path.read_text(encoding="utf-8")
    status, chunks = _index_records(MODEL_PAGE_URL, model_path.name, content, model_records(json.loads(content)))
    counts[status] += 1
    counts["chunks"] += chunks
    present = {MODEL_PAGE_URL}
    for path in sorted(pages_dir.glob("*.md")):
        snapshot = read_snapshot(path)
        present.add(snapshot.url)
        status, chunks = _index_records(
            snapshot.url, path.name, path.read_text(encoding="utf-8"), page_records(snapshot)
        )
        counts[status] += 1
        counts["chunks"] += chunks
        if report and status == "indexed":
            report(f"indexed {chunks:4d} chunks  {path.name}")
    stale = SourceChunk.objects.filter(doc_type=DOC_TYPE).exclude(repository_url__in=present)
    counts["removed"] = stale.values("repository_url").distinct().count()
    stale.delete()
    IndexedSourceFile.objects.filter(commit_sha=f"v{VERSION}").exclude(repository_url__in=present).delete()
    return counts


@lru_cache(maxsize=1)
def _page_titles() -> dict[str, str]:
    return {f"docs.datex2.eu/v{VERSION}/{page_name(read_snapshot(p).url)}": read_snapshot(p).title for p in PAGES_DIR.glob("*.md")}


def citation_title(source_path: str) -> str:
    """A readable name for a cited DATEX II passage ("DATEX II v3.7 Roadworks"), else ""."""
    source_path = source_path or ""
    if source_path.startswith("datex-model-v"):
        version, _, key = source_path.removeprefix("datex-model-v").partition("/")
        namespace, _, name = key.partition(".")
        return f"DATEX II v{version} {name} ({namespace})"
    if source_path.startswith("docs.datex2.eu/"):
        return f"DATEX II documentation: {_page_titles().get(source_path) or source_path.rsplit('/', 1)[-1]}"
    return ""
