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
Created: 2026-11-06  |  Modified: 2026-11-24
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import time
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path

from helpdesk.models import IndexedSourceFile, SourceChunk
from helpdesk.services import ea_model
from helpdesk.services.embeddings import build_text_embeddings_batch
from helpdesk.services.service_status import mark_embedding
from helpdesk.services.index_builder import build_chunk_embedding_text, build_content_hash
from helpdesk.services.napcore_site import Snapshot, chunk_snapshot, decode_entities, html_to_text, read_snapshot

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
# What the general Enterprise Architect reader (services/ea_model.py) keeps of the DATEX II model: every class,
# enumeration and data type of the file; the definition from the tagged value "definition", else the Note; every
# connector between two of them is a relation except a note's anchor (NoteLink); a namespace is a package with
# the stereotype D2Namespace.
PROFILE = ea_model.Profile(
    element_types=("Class", "Enumeration", "DataType"),
    definition_tag="definition",
    definition_text=ea_model.COLLAPSED,
    excluded_relations=("NoteLink",),
    namespace_stereotype="D2Namespace",
)
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
    return decode_entities((text or "").replace("<br/>", " "))


def extract_model(qea_path: Path, *, member_facts: bool = False) -> dict:
    """Every class, enumeration and data type of the model with its namespace, definition and members.

    In the model, definitions are tagged values ("definition") of elements and attributes; a namespace is
    a package with the stereotype D2Namespace; associations are the connectors between two elements other than
    generalisations (in v3.7 the D2Relation aggregations, most of them without a role name). A target and a
    supertype are named with their namespace, because a name alone repeats across namespaces. The tables are
    read by the general Enterprise Architect reader (services/ea_model.py) with the DATEX II profile.

    member_facts: every member also says where it stands ("position", 1-based, the model's order), what kind of
    member it is ("stereotype"), and which element its type is ("type_namespace": the namespace of the element
    whose id the attribute's classifier holds, None where the type is no element of the model). The model's JSON
    (docs/datex/model-v3.7.json) is written without them, so it does not change."""
    model = ea_model.read_model(qea_path, PROFILE, attributes=True)
    objects = model.elements
    namespaces = {ident: model.location(element.package_id)[0] for ident, element in objects.items()}
    supertypes: dict[int, set[tuple[str, str]]] = {}
    associations: dict[int, list[dict]] = {}
    for connector in model.generalizations:
        end = objects[connector.end]
        supertypes.setdefault(connector.start, set()).add((end.name, namespaces[end.id]))
    for connector in model.relations:
        start, end = objects[connector.start], objects[connector.end]
        # Every other connector between two elements is a relation. The owner is the end that holds the
        # other (the aggregate end of an aggregation or composition; the start of anything else); the
        # property's role name and multiplicity sit on the opposite end. A relation without any role name
        # is kept with an empty role (the model leaves many unnamed).
        if connector.dest_is_aggregate and not connector.source_is_aggregate:
            owner_is_start = False
        elif connector.source_is_aggregate and not connector.dest_is_aggregate:
            owner_is_start = True
        else:  # no aggregate end: the end that has a role name owns, the start when neither does
            owner_is_start = bool(connector.dest_role) or not connector.source_role
        if owner_is_start:
            owner, target, role, card = start, end, connector.dest_role, connector.dest_card
        else:
            owner, target, role, card = end, start, connector.source_role, connector.source_card
        relation = {
            "role": role,
            "target": target.name,
            "target_namespace": namespaces[target.id],
            "multiplicity": card,
        }
        if connector.type != "Aggregation":
            relation["relation"] = connector.type.lower()
        associations.setdefault(owner.id, []).append(relation)

    elements = []
    for ident, element in sorted(objects.items(), key=lambda item: item[1].name.lower()):
        namespace, package = model.location(element.package_id)
        members = [
            {
                "name": attribute.name,
                "type": attribute.type,
                "multiplicity": f"{attribute.lower}..{attribute.upper}" if attribute.lower or attribute.upper else "",
                "definition": attribute.definition,
                **(_member_facts(attribute, objects, namespaces) if member_facts else {}),
            }
            for attribute in model.attributes.get(ident, [])
        ]
        elements.append(
            {
                "name": element.name,
                "kind": {"Class": "class", "Enumeration": "enumeration", "DataType": "data type"}[element.type],
                "stereotype": element.stereotype,
                "namespace": namespace,
                "package": package,
                "definition": element.definition,
                "supertypes": sorted({name for name, _ in supertypes.get(ident, ())}),
                "supertype_refs": [{"name": n, "namespace": ns} for n, ns in sorted(supertypes.get(ident, ()))],
                "members": members,
                "associations": sorted(
                    associations.get(ident, []),
                    key=lambda a: (a["role"].lower(), a["target"], a["target_namespace"], a.get("relation", "")),
                ),
            }
        )
    return {"version": VERSION, "source": MODEL_FILE_URL, "elements": elements}


def _member_facts(attribute: ea_model.Attribute, objects: dict, namespaces: dict) -> dict:
    """What the model's JSON leaves out of a member: its place, its stereotype, the lower and upper bound as the
    model has them, and the element its type is (namespace and name), by the classifier id and not by the name,
    which repeats across namespaces."""
    target = objects.get(attribute.classifier)
    return {
        "position": attribute.position,
        "stereotype": attribute.stereotype,
        "lower": attribute.lower,
        "upper": attribute.upper,
        "type_namespace": namespaces[target.id] if target is not None else None,
        "type_element": target.name if target is not None else None,
    }


def fetch_model(out_dir: Path) -> int:
    """Download the release's model file and store the extracted model; returns the number of elements."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".qea") as qea:
        qea.write(_get(MODEL_FILE_URL))
        qea.flush()
        model = extract_model(Path(qea.name))
    (out_dir / MODEL_PATH.name).write_text(json.dumps(model, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return len(model["elements"])


def ambiguous_names(model: dict) -> frozenset[str]:
    """Element names that occur in more than one namespace of the model."""
    seen: dict[str, set[str]] = {}
    for element in model["elements"]:
        seen.setdefault(element["name"], set()).add(element["namespace"])
    return frozenset(name for name, spaces in seen.items() if len(spaces) > 1)


def _shown(name: str, namespace: str | None, ambiguous: frozenset[str]) -> str:
    """A name as text shows it: with its namespace where the bare name would not say which element is meant."""
    return f"{namespace}.{name}" if namespace and name in ambiguous else name


def element_text(element: dict, ambiguous: frozenset[str] = frozenset()) -> str:
    """The element as answers read it: what it is, its definition, then its attributes or literals.
    ambiguous: names that repeat across namespaces (ambiguous_names); those are shown with their namespace."""
    place = " / ".join(p for p in (element["namespace"], element["package"]) if p)
    lines = [f"DATEX II {element['kind']} {element['name']} (namespace {place})"]
    if element["definition"]:
        lines.append(f"Definition: {element['definition']}")
    if element["supertypes"]:
        refs = element.get("supertype_refs") or [{"name": n, "namespace": ""} for n in element["supertypes"]]
        lines.append(f"Subtype of: {', '.join(_shown(r['name'], r['namespace'], ambiguous) for r in refs)}")
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
            role = association["role"] or "(unnamed)"
            kind = f" [{association['relation']}]" if association.get("relation") else ""
            target = _shown(association["target"], association.get("target_namespace"), ambiguous)
            lines.append(f"- {role} -> {target}{card}{kind}")
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


def model_record_path(version: str, namespace: str, name: str) -> str:
    """The source path of the record of a model element (all pieces of a record share it)."""
    return f"datex-model-v{version}/{namespace}.{name}"


def concept_id_of_source_path(source_path: str) -> str | None:
    """The concept id of the class a model record's source path stands for ("datex:Situation.Delays"), else None: the
    inverse of model_record_path, for the class card (services/class_card.py). The id is the local name of the
    element's IRI in docs/ontology/standards/datex.ttl, which build_datex_ontology writes as namespace.name."""
    prefix = f"datex-model-v{VERSION}/"
    if not (source_path or "").startswith(prefix):
        return None
    key = source_path[len(prefix) :]
    namespace, _, name = key.partition(".")
    return f"datex:{key}" if namespace and name else None


def model_records(model: dict) -> list[dict]:
    records = []
    ambiguous = ambiguous_names(model)
    for element in model["elements"]:
        if not element["name"]:
            continue
        key = f"{element['namespace']}.{element['name']}"
        text = element_text(element, ambiguous)
        head = text.split("\n", 1)[0]
        for part, piece in enumerate(_pieces(text, head)):
            records.append(
                {
                    "chunk_id": f"datex-model-{_key(key)}-{part:02d}",
                    "source_path": model_record_path(model["version"], element["namespace"], element["name"]),
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
    mark_embedding()
    from helpdesk.services.embeddings import semantic_enabled

    if not semantic_enabled():
        return build_text_embeddings_batch(texts)
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_SLICE):
        vectors.extend(build_text_embeddings_batch(texts[start : start + EMBED_SLICE]))
        time.sleep(EMBED_PAUSE_SECONDS)
    return vectors


def _index_records(repository_url: str, file_name: str, content: str, records: list[dict], units=None) -> tuple[str, int]:
    """units(): the document's units of the prepared cut, used when the document is of that cut."""
    content_hash = build_content_hash(f"parser {PARSER_VERSION}\n{content}")
    indexed = IndexedSourceFile.objects.filter(repository_url=repository_url, source_path=file_name).first()
    if indexed and indexed.content_hash == content_hash:
        return "unchanged", SourceChunk.objects.filter(repository_url=repository_url).count()
    if units is not None:
        from helpdesk.services import prepared_index

        prepared = prepared_index.harvested_document(
            repository_url, DOC_TYPE, units, commit_sha=f"v{VERSION}", standards_scope=[SCOPE]
        )
        if prepared is not None:
            IndexedSourceFile.objects.update_or_create(
                repository_url=repository_url,
                source_path=file_name,
                defaults={"commit_sha": f"v{VERSION}", "content_hash": content_hash},
            )
            return "indexed", prepared
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
    from helpdesk.services import prepared_cut

    model = json.loads(content)
    status, chunks = _index_records(
        MODEL_PAGE_URL, model_path.name, content, model_records(model), lambda: prepared_cut.datex_model_units(model)
    )
    counts[status] += 1
    counts["chunks"] += chunks
    present = {MODEL_PAGE_URL}
    for path in sorted(pages_dir.glob("*.md")):
        snapshot = read_snapshot(path)
        present.add(snapshot.url)
        status, chunks = _index_records(
            snapshot.url, path.name, path.read_text(encoding="utf-8"), page_records(snapshot),
            lambda snapshot=snapshot: prepared_cut.datex_page_units(snapshot),
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
