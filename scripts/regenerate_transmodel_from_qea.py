#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path


PREFIX_BLOCK = """# Transmodel RDF/Turtle Ontology
# Generated: {generated}
# Source: {source}

@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix tm: <https://transmodel-cen.eu/6.2/> .

tm:TransmodelOntology a owl:Ontology ;
  rdfs:label "Transmodel Core Ontology v6.2" ;
  rdfs:comment "Transmodel v6.2 (2024) generated from EA UML model with class hierarchy, association roles, and multiplicity restrictions." ;
  owl:versionInfo "6.2" .
"""


@dataclass
class ClassDef:
	local: str
	label: str
	comment: str = ""
	parents: set[str] = field(default_factory=set)
	restrictions: list[tuple[str, str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class PropertyDef:
	local: str
	domain_local: str
	range_local: str
	label: str


CLASS_BLOCK_RE = re.compile(
	r"^(tm:[^\s]+\s+a\s+owl:Class\s*;\s*rdfs:label\s+\".*?\"\s*\n(?:\s*;\s*rdfs:comment\s+\".*?\"\s*\n)?\s*\.)",
	re.MULTILINE | re.DOTALL,
)

TRANSMODEL_PART_RE = re.compile(r"\bPart\s*(?:1|2|3|4|5|6|7|8|10)\b", re.IGNORECASE)


def _escape(text: str) -> str:
	return (
		text.replace("\\", "\\\\")
		.replace('"', '\\"')
		.replace("\r", " ")
		.replace("\n", " ")
		.strip()
	)


def _norm(text: str) -> str:
	return re.sub(r"\s+", " ", (text or "").strip()).upper()


def _tokens(text: str) -> list[str]:
	return re.findall(r"[A-Za-z0-9]+", text or "")


def _norm_identifier(text: str) -> str:
	return " ".join(_tokens(text)).upper()


def _to_property_local(role: str, fallback_target_label: str) -> str:
	role = (role or "").strip()
	tokens = _tokens(role)
	if not tokens:
		tokens = ["has"] + _tokens(fallback_target_label)
	if not tokens:
		return "relatedTo"
	head = tokens[0].lower()
	tail = [token[:1].upper() + token[1:] for token in tokens[1:]]
	return head + "".join(tail)


def _parse_cardinality(raw_cardinality: str) -> tuple[str, str] | None:
	card = (raw_cardinality or "").strip().replace(" ", "")
	if not card or card == "*":
		return None
	if re.fullmatch(r"\d+", card):
		return ("exact", card)
	if ".." in card:
		left, right = card.split("..", 1)
		if left.isdigit() and right == "*":
			return ("min", left)
		if left == "*" and right.isdigit():
			return ("max", right)
		if left.isdigit() and right.isdigit():
			return ("minmax", f"{left},{right}")
	return None


def _parse_existing_classes(ttl_path: Path) -> list[ClassDef]:
	text = ttl_path.read_text(encoding="utf-8")
	classes: list[ClassDef] = []
	for block in CLASS_BLOCK_RE.findall(text):
		local_match = re.search(r"^tm:([^\s]+)", block)
		label_match = re.search(r"rdfs:label\s+\"([^\"]+)\"", block)
		comment_match = re.search(r"rdfs:comment\s+\"([\s\S]*?)\"", block)
		if not local_match or not label_match:
			continue
		classes.append(
			ClassDef(
				local=local_match.group(1),
				label=label_match.group(1),
				comment=(comment_match.group(1) if comment_match else ""),
			)
		)
	return classes


def _load_package_paths(cur: sqlite3.Cursor) -> dict[int, str]:
	rows = cur.execute("SELECT Package_ID, Name, Parent_ID FROM t_package").fetchall()
	by_id = {int(row[0]): (row[1] or "", int(row[2] or 0)) for row in rows}
	path_cache: dict[int, str] = {}

	def build_path(package_id: int) -> str:
		if package_id in path_cache:
			return path_cache[package_id]
		if package_id not in by_id:
			path_cache[package_id] = ""
			return ""
		name, parent_id = by_id[package_id]
		if parent_id <= 0 or parent_id == package_id:
			path = name
		else:
			parent_path = build_path(parent_id)
			path = f"{parent_path} > {name}" if parent_path else name
		path_cache[package_id] = path
		return path

	for package_id in by_id:
		build_path(package_id)
	return path_cache


def _is_allowed_transmodel_part_path(path: str) -> bool:
	if not path:
		return False
	norm = " ".join(path.split())
	if "transmodel v6.2" not in norm.lower():
		return False
	return bool(TRANSMODEL_PART_RE.search(norm))


def _to_class_local(name: str) -> str:
	tokens = _tokens(name)
	if not tokens:
		return "UnnamedClass"
	local = "_".join(tokens)
	if local and local[0].isdigit():
		local = f"_{local}"
	return local


def regenerate(ttl_path: Path, qea_path: Path, include_cardinalities: bool = False) -> str:
	conn = sqlite3.connect(str(qea_path))
	cur = conn.cursor()
	package_paths = _load_package_paths(cur)
	allowed_package_ids = {
		package_id
		for package_id, path in package_paths.items()
		if _is_allowed_transmodel_part_path(path)
	}
	if not allowed_package_ids:
		raise RuntimeError("No Transmodel Part 1-10 packages found in EA repository")

	class_rows = cur.execute(
		"""
		SELECT Object_ID, Name, Note
		FROM t_object
		WHERE Object_Type='Class'
		  AND Package_ID IN ({})
		""".format(",".join("?" * len(allowed_package_ids))),
		tuple(sorted(allowed_package_ids)),
	).fetchall()
	if not class_rows:
		raise RuntimeError("No UML classes found under Transmodel Part 1-10 package scope")

	classes: list[ClassDef] = []
	object_ids_to_locals: dict[int, set[str]] = {}
	used_locals: set[str] = set()
	for object_id, name, note in class_rows:
		label = (name or "").strip()
		if not label:
			continue
		base_local = _to_class_local(label)
		local = base_local
		if local in used_locals:
			local = f"{base_local}_{int(object_id)}"
		used_locals.add(local)
		classes.append(ClassDef(local=local, label=label, comment=(note or "").strip()))
		object_ids_to_locals.setdefault(int(object_id), set()).add(local)

	if not classes:
		raise RuntimeError("No named classes found under Transmodel Part 1-10 package scope")

	class_by_local = {cls.local: cls for cls in classes}

	properties: dict[tuple[str, str, str], PropertyDef] = {}

	generalization_rows = cur.execute(
		"""
		SELECT Start_Object_ID, End_Object_ID
		FROM t_connector
		WHERE Connector_Type='Generalization'
		"""
	).fetchall()

	for child_id, parent_id in generalization_rows:
		child_locals = object_ids_to_locals.get(int(child_id), set())
		parent_locals = object_ids_to_locals.get(int(parent_id), set())
		if not child_locals or not parent_locals:
			continue
		for child_local in child_locals:
			for parent_local in parent_locals:
				if child_local != parent_local:
					class_by_local[child_local].parents.add(parent_local)

	association_rows = cur.execute(
		"""
		SELECT
			c.Start_Object_ID,
			c.End_Object_ID,
			c.SourceRole,
			c.DestRole,
			c.SourceCard,
			c.DestCard,
			so.Name,
			eo.Name
		FROM t_connector c
		JOIN t_object so ON so.Object_ID = c.Start_Object_ID
		JOIN t_object eo ON eo.Object_ID = c.End_Object_ID
		WHERE c.Connector_Type IN ('Association', 'Aggregation')
		  AND so.Object_Type='Class'
		  AND eo.Object_Type='Class'
		"""
	).fetchall()

	def add_edge(
		domain_local: str,
		range_local: str,
		role_name: str,
		fallback_target_label: str,
		card: str,
	) -> None:
		property_local = _to_property_local(role_name, fallback_target_label)
		property_label = role_name.strip() if role_name.strip() else f"has {fallback_target_label}".strip()
		key = (property_local, domain_local, range_local)
		properties[key] = PropertyDef(
			local=property_local,
			domain_local=domain_local,
			range_local=range_local,
			label=property_label,
		)
		if not include_cardinalities:
			return

		parsed = _parse_cardinality(card)
		if not parsed:
			return
		kind, value = parsed
		if kind == "exact":
			class_by_local[domain_local].restrictions.append(
				(property_local, "owl:cardinality", value)
			)
		elif kind == "min":
			class_by_local[domain_local].restrictions.append(
				(property_local, "owl:minCardinality", value)
			)
		elif kind == "max":
			class_by_local[domain_local].restrictions.append(
				(property_local, "owl:maxCardinality", value)
			)
		else:
			min_value, max_value = value.split(",", 1)
			class_by_local[domain_local].restrictions.append(
				(property_local, "owl:minCardinality", min_value)
			)
			class_by_local[domain_local].restrictions.append(
				(property_local, "owl:maxCardinality", max_value)
			)

	for (
		start_id,
		end_id,
		source_role,
		dest_role,
		source_card,
		dest_card,
		start_name,
		end_name,
	) in association_rows:
		start_locals = object_ids_to_locals.get(int(start_id), set())
		end_locals = object_ids_to_locals.get(int(end_id), set())
		if not start_locals or not end_locals:
			continue
		for start_local in start_locals:
			for end_local in end_locals:
				if start_local == end_local:
					continue
				# Role and multiplicity at destination end belong to the source-side property.
				add_edge(start_local, end_local, dest_role or "", end_name or class_by_local[end_local].label, dest_card or "")
				# Role and multiplicity at source end belong to the destination-side property.
				add_edge(end_local, start_local, source_role or "", start_name or class_by_local[start_local].label, source_card or "")

	# Deduplicate restrictions while preserving order.
	for cls in classes:
		seen: set[tuple[str, str, str]] = set()
		deduped: list[tuple[str, str, str]] = []
		for item in cls.restrictions:
			if item in seen:
				continue
			seen.add(item)
			deduped.append(item)
		cls.restrictions = deduped

	out: list[str] = []
	out.append(
		PREFIX_BLOCK.format(
			generated=dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
			source=qea_path.name,
		).rstrip()
	)
	out.append("")

	for cls in classes:
		lines = [f"tm:{cls.local} a owl:Class ;", f"  rdfs:label \"{_escape(cls.label)}\""]
		if cls.comment:
			lines[-1] += ""
			lines.append(f"  ; rdfs:comment \"{_escape(cls.comment)}\"")
		for parent_local in sorted(cls.parents):
			lines.append(f"  ; rdfs:subClassOf tm:{parent_local}")
		if include_cardinalities:
			for property_local, predicate, cardinality in cls.restrictions:
				lines.append("  ; rdfs:subClassOf [")
				lines.append("      a owl:Restriction ;")
				lines.append(f"      owl:onProperty tm:{property_local} ;")
				lines.append(
					f"      {predicate} \"{cardinality}\"^^xsd:nonNegativeInteger")
				lines.append("    ]")
		lines.append("  .")
		out.append("\n".join(lines))

	out.append("")
	out.append("# Object properties derived from UML associations/aggregations")
	out.append("")
	for prop in sorted(properties.values(), key=lambda p: (p.local, p.domain_local, p.range_local)):
		out.append(
			"\n".join(
				[
					f"tm:{prop.local} a owl:ObjectProperty ;",
					f"  rdfs:label \"{_escape(prop.label)}\" ;",
					f"  rdfs:domain tm:{prop.domain_local} ;",
					f"  rdfs:range tm:{prop.range_local} .",
				]
			)
		)

	return "\n\n".join(out).rstrip() + "\n"


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Regenerate transmodel.ttl from EA .qea (SQLite) with hierarchy and multiplicities"
	)
	parser.add_argument(
		"--qea-path",
		required=True,
		help="Absolute path to EA .qea SQLite repository",
	)
	parser.add_argument(
		"--ttl-path",
		default="docs/ontology/standards/transmodel.ttl",
		help="Target TTL file to overwrite",
	)
	parser.add_argument(
		"--with-cardinalities",
		action="store_true",
		help=(
			"Include owl:Restriction cardinalities from UML multiplicities. "
			"Disabled by default for faster reasoning and a smaller ontology."
		),
	)
	args = parser.parse_args()

	qea_path = Path(args.qea_path)
	ttl_path = Path(args.ttl_path)
	if not qea_path.exists():
		raise FileNotFoundError(f"QEA file not found: {qea_path}")
	if not ttl_path.exists():
		raise FileNotFoundError(f"TTL file not found: {ttl_path}")

	content = regenerate(
		ttl_path=ttl_path,
		qea_path=qea_path,
		include_cardinalities=bool(args.with_cardinalities),
	)
	ttl_path.write_text(content, encoding="utf-8")
	print(f"Regenerated {ttl_path} from {qea_path}")


if __name__ == "__main__":
	main()
