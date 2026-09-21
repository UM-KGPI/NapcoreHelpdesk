#!/usr/bin/env python3
"""
Full pipeline: enrich netex.ttl with owl:ObjectProperty / owl:DatatypeProperty
triples extracted from the complete NeTEx XSD tree, plus materialized
skos:related pairs for the GraphDB-mode expansion path (SKOS_RELATIONS).

Layer-1 only (shared helpdesk-RAG / validator vocabulary):
  - object properties: rdfs:domain / rdfs:range between netex.ttl classes
  - datatype properties: rdfs:domain netex class, rdfs:range xsd:* builtin
    (named simpleTypes resolved through their restriction-base chain;
     enumeration type name kept in rdfs:comment for traceability)
  - NO cardinalities / enumeration value lists — that is the validator
    project's generated-shapes layer, not this file.

Extraction rules as in the ifopt prototype (own-content only; inherited
content stays on the base class). Self-loop object properties are kept in
the OWL output but omitted from skos:related (no expansion value).

Writes: netex.ttl.new next to the canonical netex.ttl + stats to stdout.
"""

import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

XSD_NS = "{http://www.w3.org/2001/XMLSchema}"
NETEX_XSD_ROOT = Path("/Users/andrejt/Research/repositories/git/NeTEx/xsd")
SCOPE_DIRS = [
    "netex_framework",
    "netex_part_1",
    "netex_part_2",
    "netex_part_3",
    "netex_part_5",
    "netex_service",
]
TTL_PATH = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "/Users/andrejt/Research/repositories/git/NapcoreHelpdesk/docs/ontology/standards/netex.ttl"
)
OUT_PATH = Path(sys.argv[2]) if len(sys.argv) > 2 else TTL_PATH.with_suffix(".ttl.new")

# Structure-type suffixes used across the NeTEx schema, most specific first
# (the match loop stops at the first hit). "_VersionedChlldStructure" is a
# genuine typo in the NeTEx XSDs, not ours. Plain "Structure" must stay last:
# it only binds when the stripped stem is an ontology class, so list-helper
# types like quays_RelStructure never match.
CLASS_STRUCT_SUFFIXES = (
    "_VersionedChildStructure",
    "_VersionedChlldStructure",
    "_VersionFrameStructure",
    "_VersionedStructure",
    "__VersionStructure",
    "_VersionStructure",
    "_ValueStructure",
    "_EntityStructure",
    "Structure",
)
VERSION_OLDS = (
    '"0.2-xsd-rebuild-with-relationships"',
    '"0.3-with-object-and-datatype-properties"',
)
VERSION_NEW = '"0.4-expanded-classes-and-structure-suffixes"'


def load_ttl_classes(text: str) -> set[str]:
    return set(re.findall(r"^netex:([A-Za-z0-9_]+)\n\s+a owl:Class", text, re.M))


def local(tag: str) -> str:
    return tag.replace(XSD_NS, "")


class SchemaIndex:
    def __init__(self):
        self.complex_types: dict[str, ET.Element] = {}
        self.groups: dict[str, ET.Element] = {}
        self.simple_types: dict[str, ET.Element] = {}
        self.type_source: dict[str, str] = {}

    def scan(self, root_dir: Path, subdirs: list[str]):
        files = []
        for sub in subdirs:
            files.extend(sorted((root_dir / sub).rglob("*.xsd")))
        for path in files:
            try:
                tree_root = ET.parse(path).getroot()
            except ET.ParseError as exc:
                print(f"WARN: parse error {path.name}: {exc}", file=sys.stderr)
                continue
            rel = str(path.relative_to(root_dir))
            for child in tree_root:
                tag, name = local(child.tag), child.get("name")
                if not name:
                    continue
                if tag == "complexType":
                    self.complex_types.setdefault(name, child)
                    self.type_source.setdefault(name, rel)
                elif tag == "group":
                    self.groups.setdefault(name, child)
                elif tag == "simpleType":
                    self.simple_types.setdefault(name, child)
        return len(files)

    def resolve_simple_base(self, tname: str, depth: int = 0) -> str | None:
        """Resolve a named simpleType to an xsd:* builtin via restriction/list/union chain."""
        if depth > 10:
            return None
        if tname.startswith("xsd:"):
            return tname
        st = self.simple_types.get(tname)
        if st is None:
            return None
        for node in st.iter():
            tag = local(node.tag)
            if tag == "restriction":
                base = node.get("base", "")
                if base:
                    return self.resolve_simple_base(base, depth + 1)
            elif tag == "list":
                item = node.get("itemType", "")
                if item:
                    return self.resolve_simple_base(item, depth + 1)
            elif tag == "union":
                members = (node.get("memberTypes") or "").split()
                if members:
                    return self.resolve_simple_base(members[0], depth + 1)
        return None


def first_doc(elem: ET.Element) -> str:
    ann = elem.find(f"{XSD_NS}annotation/{XSD_NS}documentation")
    if ann is not None and ann.text:
        return " ".join(ann.text.split())
    return ""


def own_content_entries(ctype: ET.Element, idx: SchemaIndex) -> list[ET.Element]:
    seen_groups: set[str] = set()
    found: list[ET.Element] = []

    def walk(node: ET.Element):
        for child in node:
            tag = local(child.tag)
            if tag in ("sequence", "choice", "all", "complexContent", "extension", "restriction"):
                walk(child)
            elif tag == "group":
                gname = child.get("ref")
                if gname and gname not in seen_groups:
                    seen_groups.add(gname)
                    grp = idx.groups.get(gname)
                    if grp is not None:
                        walk(grp)
            elif tag == "element":
                found.append(child)

    walk(ctype)
    return found


def resolve_relstructure_targets(
    rel_name: str, idx: SchemaIndex, known_classes: set[str]
) -> set[str]:
    ctype = idx.complex_types.get(rel_name)
    if ctype is None:
        stem = rel_name[: -len("_RelStructure")]
        candidates = []
        for plural_suffix in ("s", "es"):
            if stem.endswith(plural_suffix):
                singular = stem[: -len(plural_suffix)]
                if singular.endswith("Ref"):
                    singular = singular[:-3]
                candidates.append(singular[0].upper() + singular[1:])
        for cand in candidates:
            if cand in known_classes:
                return {cand}
        return set(candidates[:1])
    targets: set[str] = set()
    for el in ctype.iter(f"{XSD_NS}element"):
        ref = el.get("ref") or el.get("name")
        if not ref:
            continue
        targets.add(ref[:-3] if ref.endswith("Ref") else ref)
    return targets


def classify_object(el: ET.Element, idx: SchemaIndex, known: set[str]):
    """Object-property candidates: list of (prop_name, range_class, mechanism, doc)."""
    out = []
    doc = first_doc(el)
    ref, name, etype = el.get("ref"), el.get("name"), el.get("type", "")

    if ref:
        if ref.endswith("Ref"):
            out.append((ref, ref[:-3], "reference", doc))
        else:
            out.append((ref, ref, "containment", doc))
        return out
    if not name:
        return out
    if etype.endswith("RefStructure"):
        out.append((name, etype[: -len("RefStructure")], "reference", doc))
    elif etype.endswith("_RelStructure"):
        for target in resolve_relstructure_targets(etype, idx, known):
            out.append((name, target, "containment-list", doc))
    else:
        for suffix in CLASS_STRUCT_SUFFIXES:
            if etype.endswith(suffix):
                out.append((name, etype[: -len(suffix)], "containment", doc))
                break
    return out


def classify_datatype(el: ET.Element, idx: SchemaIndex):
    """Datatype-property candidate: (prop_name, xsd_range, xsd_type_name, doc) or None."""
    name, etype = el.get("name"), el.get("type", "")
    if not name or not etype:
        return None
    if etype == "MultilingualString":
        return (name, "xsd:string", etype, first_doc(el))
    if etype.startswith("xsd:"):
        return (name, etype, "", first_doc(el))
    if etype in idx.simple_types:
        base = idx.resolve_simple_base(etype) or "xsd:string"
        return (name, base, etype, first_doc(el))
    return None


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def main():
    ttl_text = TTL_PATH.read_text(encoding="utf-8")
    ttl_classes = load_ttl_classes(ttl_text)
    print(f"netex.ttl classes: {len(ttl_classes)}")

    idx = SchemaIndex()
    nfiles = idx.scan(NETEX_XSD_ROOT, SCOPE_DIRS)
    print(f"scanned {nfiles} XSD files: {len(idx.complex_types)} complexTypes, "
          f"{len(idx.groups)} groups, {len(idx.simple_types)} simpleTypes")

    class_to_type: dict[str, str] = {}
    for tname in idx.complex_types:
        for suffix in CLASS_STRUCT_SUFFIXES:
            if tname.endswith(suffix):
                cls = tname[: -len(suffix)]
                if cls in ttl_classes:
                    class_to_type.setdefault(cls, tname)
                break
    print(f"TTL classes with a structure type: {len(class_to_type)} / {len(ttl_classes)}")

    obj_edges: dict[tuple[str, str, str], dict] = {}
    dt_edges: dict[tuple[str, str], dict] = {}
    dangling: defaultdict[str, int] = defaultdict(int)

    for cls, tname in sorted(class_to_type.items()):
        ctype = idx.complex_types[tname]
        source = idx.type_source[tname]
        for el in own_content_entries(ctype, idx):
            cands = classify_object(el, idx, ttl_classes)
            if cands:
                for prop_name, target, mechanism, doc in cands:
                    if target in ttl_classes:
                        obj_edges.setdefault(
                            (cls, prop_name, target),
                            {"mechanism": mechanism, "doc": doc, "source": source},
                        )
                    else:
                        dangling[target] += 1
                continue
            dt = classify_datatype(el, idx)
            if dt:
                prop_name, xsd_range, xsd_type, doc = dt
                dt_edges.setdefault(
                    (cls, prop_name),
                    {"range": xsd_range, "xsd_type": xsd_type, "doc": doc, "source": source},
                )

    print(f"\nobject-property edges: {len(obj_edges)}")
    by_mech = defaultdict(int)
    for meta in obj_edges.values():
        by_mech[meta["mechanism"]] += 1
    for mech, count in sorted(by_mech.items(), key=lambda x: -x[1]):
        print(f"  {mech:>18}: {count}")
    print(f"datatype-property edges: {len(dt_edges)}")
    print(f"dangling range targets: {len(dangling)} distinct, {sum(dangling.values())} refs")

    in_deg = defaultdict(int)
    out_deg = defaultdict(int)
    for (dom, _p, rng) in obj_edges:
        if dom != rng:
            in_deg[rng] += 1
            out_deg[dom] += 1
    print("\ntop-20 range in-degree (hubs):")
    for cls, deg in sorted(in_deg.items(), key=lambda x: -x[1])[:20]:
        print(f"  {deg:4d}  {cls}")
    print("\ntop-10 domain out-degree:")
    for cls, deg in sorted(out_deg.items(), key=lambda x: -x[1])[:10]:
        print(f"  {deg:4d}  {cls}")
    print("\ntop-15 dangling:")
    for tgt, count in sorted(dangling.items(), key=lambda x: -x[1])[:15]:
        print(f"  {count:4d}  {tgt}")

    # Qualified naming for property names used by >1 domain (object + datatype pools kept separate
    # from each other deliberately: an IRI must not be both Object and Datatype property).
    obj_name_domains = defaultdict(set)
    for (dom, prop, _rng) in obj_edges:
        obj_name_domains[prop].add(dom)
    dt_name_domains = defaultdict(set)
    for (dom, prop) in dt_edges:
        dt_name_domains[prop].add(dom)
    cross = set(obj_name_domains) & set(dt_name_domains)
    obj_collisions = {p for p, d in obj_name_domains.items() if len(d) > 1} | cross
    dt_collisions = {p for p, d in dt_name_domains.items() if len(d) > 1} | cross
    print(f"\nqualified names: object={len(obj_collisions)}, datatype={len(dt_collisions)}, "
          f"cross-kind={len(cross)}")

    def prop_iri(dom: str, prop: str, collisions: set[str]) -> str:
        base = prop[0].lower() + prop[1:]
        return f"netex:{base}_{dom}" if prop in collisions else f"netex:{base}"

    # Guard: no property IRI may collide with an existing class IRI.
    class_locals = set(ttl_classes)
    all_iris = set()
    for (dom, prop, _rng) in obj_edges:
        all_iris.add(prop_iri(dom, prop, obj_collisions)[len("netex:"):])
    for (dom, prop) in dt_edges:
        all_iris.add(prop_iri(dom, prop, dt_collisions)[len("netex:"):])
    clash = all_iris & class_locals
    if clash:
        sys.exit(f"FATAL: property IRIs collide with class IRIs: {sorted(clash)[:10]}")

    lines = []
    lines.append("\n#################################################################\n")
    lines.append("# Object Properties (extracted from XSD content models)\n")
    lines.append("# Rules: element ref XxxRef / XxxRefStructure -> reference;\n")
    lines.append("#        xxx_RelStructure / class structure type -> containment.\n")
    lines.append("# Own-content only: inherited elements stay on the base class.\n")
    lines.append("#################################################################\n\n")
    for (dom, prop, rng), meta in sorted(obj_edges.items()):
        iri = prop_iri(dom, prop, obj_collisions)
        lines.append(f"{iri}\n    a owl:ObjectProperty ;\n")
        if meta["doc"]:
            lines.append(f'    skos:definition "{esc(meta["doc"])}"@en ;\n')
        lines.append(f"    rdfs:domain netex:{dom} ;\n")
        lines.append(f"    rdfs:range netex:{rng} ;\n")
        lines.append(f'    rdfs:comment "Extracted from: {meta["source"]} ({meta["mechanism"]})"@en .\n\n')

    lines.append("#################################################################\n")
    lines.append("# Datatype Properties (extracted from XSD content models)\n")
    lines.append("# Named simpleTypes resolved to their xsd:* restriction base;\n")
    lines.append("# original XSD type name retained in rdfs:comment.\n")
    lines.append("#################################################################\n\n")
    for (dom, prop), meta in sorted(dt_edges.items()):
        iri = prop_iri(dom, prop, dt_collisions)
        lines.append(f"{iri}\n    a owl:DatatypeProperty ;\n")
        if meta["doc"]:
            lines.append(f'    skos:definition "{esc(meta["doc"])}"@en ;\n')
        lines.append(f"    rdfs:domain netex:{dom} ;\n")
        lines.append(f"    rdfs:range {meta['range']} ;\n")
        note = f" (XSD type: {meta['xsd_type']})" if meta["xsd_type"] else ""
        lines.append(f'    rdfs:comment "Extracted from: {meta["source"]}{note}"@en .\n\n')

    lines.append("#################################################################\n")
    lines.append("# Materialized skos:related pairs (one per object-property edge)\n")
    lines.append("# Consumed by GraphDB-mode concept expansion (SKOS_RELATIONS path).\n")
    lines.append("#################################################################\n\n")
    skos_pairs = set()
    for (dom, _prop, rng) in obj_edges:
        if dom != rng:
            skos_pairs.add(tuple(sorted((dom, rng))))
    for a, b in sorted(skos_pairs):
        lines.append(f"netex:{a} skos:related netex:{b} .\n")
    print(f"skos:related pairs: {len(skos_pairs)}")

    merged = ttl_text
    for version_old in VERSION_OLDS:
        merged = merged.replace(version_old, VERSION_NEW, 1)
    if VERSION_NEW not in merged:
        print("WARN: versionInfo string not found; keeping original header")
    merged = merged.rstrip("\n") + "\n" + "".join(lines)
    OUT_PATH.write_text(merged, encoding="utf-8")
    print(f"\nwrote {OUT_PATH} ({len(merged.splitlines())} lines, "
          f"{len(obj_edges)} obj props, {len(dt_edges)} dt props)")


if __name__ == "__main__":
    main()
