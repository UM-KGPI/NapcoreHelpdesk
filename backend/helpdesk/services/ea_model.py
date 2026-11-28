"""
One reader for Enterprise Architect models (.qea files, which are SQLite databases).

DATEX II and Transmodel are both published as Enterprise Architect models, and both become an ontology from
the same tables: t_package (the package tree), t_object (the elements), t_connector (generalisations and
relations), t_objectproperties / t_attribute / t_attributetag (tagged values and attributes). What differs
between the models is data, held in a Profile:

- which elements are kept: their element types, and the packages they must sit in (patterns that the
  package's path must match; no patterns keeps the whole file), minus packages left out by name with
  everything below them;
- where an element's definition is: a tagged value (DATEX II "definition"), else the element's Note;
- how the definition text is cleaned (whitespace collapsed, or only stripped);
- which connectors are relations: a list of connector types, or every type except the excluded ones
  (generalisations are always read as supertypes, never as relations);
- which package stereotype marks a namespace (DATEX II "D2Namespace"), if the model has namespaces;
- where an attribute's definition is: a tagged value of the attribute (DATEX II, the same tag as for elements) or the
  attribute's own Notes (Transmodel).

With attributes=True the reader also gives, for every kept element, its attributes in the model's order with the
classifier id of the type (the id of the type's element, 0 where the type is a plain name), the bounds, the
stereotype and the definition. Whether an element is a class, an enumeration or a data type is element_kind(): the
element type of the file, and a class with the stereotype "enumeration" is an enumeration (its attributes are its
values).

The reader only reads; turning the result into Turtle or JSON is the caller's work (services/datex.py,
services/transmodel_model.py). Rows come in a fixed order (elements by Object_ID, connectors by
Connector_ID), so the callers' output is deterministic.

The file is opened read-only (mode=ro&immutable=1) and never written.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Created: 2026-11-24  |  Modified: 2026-11-25
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

COLLAPSED = "collapsed"
STRIPPED = "stripped"


@dataclass(frozen=True)
class Profile:
    """What to read from one model; data only, no rule naming a class of the model."""

    element_types: tuple[str, ...]
    # Every pattern must match the element's package path ("Root > Part > Package", whitespace collapsed),
    # ignoring case. Empty: every package of the file.
    package_path_patterns: tuple[str, ...] = ()
    # Names of packages left out with everything below them (compared with whitespace collapsed, ignoring case).
    excluded_packages: tuple[str, ...] = ()
    definition_tag: str | None = None
    definition_text: str = COLLAPSED
    # Connector types read as relations; None means every type except generalisations and `excluded_relations`.
    relation_types: tuple[str, ...] | None = None
    excluded_relations: tuple[str, ...] = ()
    namespace_stereotype: str | None = None
    # An attribute's definition is its own Notes (Transmodel) instead of a tagged value; the tag wins when set.
    attribute_definition_from_notes: bool = False


@dataclass(frozen=True)
class Package:
    id: int
    name: str
    parent_id: int


@dataclass(frozen=True)
class Element:
    id: int
    name: str
    type: str
    stereotype: str
    package_id: int
    note: str
    guid: str
    definition: str


@dataclass(frozen=True)
class Connector:
    id: int
    type: str
    start: int
    end: int
    source_role: str
    dest_role: str
    source_card: str
    dest_card: str
    source_is_aggregate: int
    dest_is_aggregate: int


@dataclass(frozen=True)
class Attribute:
    name: str
    type: str
    lower: str
    upper: str
    definition: str
    # Fields added for the class card; defaults keep every other caller as it was.
    classifier: int = 0  # Object_ID of the type's element, 0 where the type is a plain name
    position: int = 0  # 1-based place in the model's order (Pos, then Name)
    stereotype: str = ""


@dataclass
class Model:
    profile: Profile
    packages: dict[int, Package]
    elements: dict[int, Element]  # in Object_ID order
    generalizations: list[Connector] = field(default_factory=list)  # in Connector_ID order
    relations: list[Connector] = field(default_factory=list)  # in Connector_ID order
    namespace_packages: frozenset[int] = frozenset()
    attributes: dict[int, list[Attribute]] = field(default_factory=dict)

    def package_path(self, package_id: int) -> str:
        """"Root > Part > Package", from the root down."""
        return " > ".join(self.package_names(package_id))

    def package_names(self, package_id: int) -> list[str]:
        """The names of the package and its ancestors, from the root down."""
        names: list[str] = []
        seen: set[int] = set()
        while package_id in self.packages and package_id not in seen:
            seen.add(package_id)
            package = self.packages[package_id]
            names.append(package.name)
            if package.parent_id <= 0 or package.parent_id == package_id:
                break
            package_id = package.parent_id
        return list(reversed(names))

    def location(self, package_id: int) -> tuple[str, str]:
        """(namespace, package path below it), e.g. ("Situation", "Classes/Impact"); the namespace is the
        nearest package with the profile's namespace stereotype, "" when there is none."""
        names: list[str] = []
        while package_id in self.packages:
            if package_id in self.namespace_packages:
                return self.packages[package_id].name, "/".join(reversed(names))
            names.append(self.packages[package_id].name)
            package_id = self.packages[package_id].parent_id
        return "", "/".join(reversed(names))


def clean_text(text: str | None, style: str = COLLAPSED) -> str:
    """Definition text: COLLAPSED turns <br/> and every run of whitespace into one space; STRIPPED only strips."""
    if style == STRIPPED:
        return (text or "").strip()
    return re.sub(r"\s+", " ", (text or "").replace("<br/>", " ")).strip()


def element_kind(element: Element) -> str:
    """"class", "enumeration" or "data type": the element type of the file; a class with the stereotype
    "enumeration" is an enumeration (Transmodel keeps four that way, with their values as attributes)."""
    if element.type == "Enumeration" or element.stereotype.casefold() == "enumeration":
        return "enumeration"
    return "data type" if element.type == "DataType" else "class"


_MULTIPLICITY = re.compile(r"^(\d+|\*)(?:\.\.(\d+|\*))?$")


def parse_multiplicity(text: str | None) -> tuple[str, str] | None:
    """(lower, upper) of a multiplicity written "1", "0..1", "1..*" or "*" ("*" alone is 0..*), else None.
    The models hold typos ("O..*" with a letter O, "0.*", "1.."); they are not read as numbers."""
    match = _MULTIPLICITY.match((text or "").strip())
    if not match:
        return None
    lower, upper = match.group(1), match.group(2)
    if upper is None:
        return ("0", "*") if lower == "*" else (lower, lower)
    return lower, upper


def _columns(db: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in db.execute(f"PRAGMA table_info({table})")}  # nosec B608 - fixed table names


def _same(kind: str, kinds: tuple[str, ...]) -> bool:
    """Connector type comparison as in the model's own columns (COLLATE NOCASE)."""
    return kind.casefold() in {k.casefold() for k in kinds}


def open_model(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    db.row_factory = sqlite3.Row
    return db


def read_model(path: Path, profile: Profile, *, attributes: bool = False) -> Model:
    """The elements, generalisations and relations of the model that the profile keeps.

    A connector is kept only when both its ends are kept elements. attributes: also read every kept
    element's attributes with their definitions (tagged value, as for elements)."""
    db = open_model(path)
    try:
        packages = {
            int(row["Package_ID"]): Package(int(row["Package_ID"]), row["Name"] or "", int(row["Parent_ID"] or 0))
            for row in db.execute("SELECT Package_ID, Name, Parent_ID FROM t_package")
        }
        model = Model(profile=profile, packages=packages, elements={})
        if profile.namespace_stereotype:
            # A package's own element (t_object) holds the package id in PDATA1, as text.
            model.namespace_packages = frozenset(
                int(row["PDATA1"])
                for row in db.execute(
                    "SELECT PDATA1 FROM t_object WHERE Object_Type='Package' AND Stereotype=?",
                    (profile.namespace_stereotype,),
                )
                if str(row["PDATA1"] or "").isdigit()
            )
        patterns = [re.compile(p, re.IGNORECASE) for p in profile.package_path_patterns]
        excluded = {" ".join(name.split()).casefold() for name in profile.excluded_packages}

        def in_scope(package_id: int) -> bool:
            if excluded and any(" ".join(name.split()).casefold() in excluded for name in model.package_names(package_id)):
                return False
            if not patterns:
                return True
            path = " ".join(model.package_path(package_id).split())
            return bool(path) and package_id in packages and all(p.search(path) for p in patterns)

        object_columns = _columns(db, "t_object")
        guid = "ea_guid" if "ea_guid" in object_columns else "''"
        stereotype = "Stereotype" if "Stereotype" in object_columns else "''"
        scope_cache: dict[int, bool] = {}
        rows = db.execute(
            f"SELECT Object_ID, Name, Object_Type, {stereotype} AS Stereotype, Package_ID, Note, {guid} AS ea_guid "  # nosec B608
            f"FROM t_object WHERE Object_Type IN ({','.join('?' * len(profile.element_types))}) ORDER BY Object_ID",
            profile.element_types,
        ).fetchall()
        for row in rows:
            package_id = int(row["Package_ID"] or 0)
            if package_id not in scope_cache:
                scope_cache[package_id] = in_scope(package_id)
            if not scope_cache[package_id]:
                continue
            ident = int(row["Object_ID"])
            definition = ""
            if profile.definition_tag:
                definition = _tags(db, "t_objectproperties", "Object_ID", ident, profile).get(profile.definition_tag, "")
            model.elements[ident] = Element(
                id=ident,
                name=row["Name"] or "",
                type=row["Object_Type"] or "",
                stereotype=row["Stereotype"] or "",
                package_id=package_id,
                note=row["Note"] or "",
                guid=row["ea_guid"] or "",
                definition=definition or clean_text(row["Note"], profile.definition_text),
            )

        for row in db.execute(
            "SELECT Connector_ID, Connector_Type, Start_Object_ID, End_Object_ID, DestRole, DestCard, SourceRole, "
            "SourceCard, SourceIsAggregate, DestIsAggregate FROM t_connector ORDER BY Connector_ID"
        ):
            start, end = row["Start_Object_ID"], row["End_Object_ID"]
            if start not in model.elements or end not in model.elements:
                continue
            kind = row["Connector_Type"] or ""
            connector = Connector(
                id=int(row["Connector_ID"]),
                type=kind,
                start=int(start),
                end=int(end),
                source_role=row["SourceRole"] or "",
                dest_role=row["DestRole"] or "",
                source_card=row["SourceCard"] or "",
                dest_card=row["DestCard"] or "",
                source_is_aggregate=int(row["SourceIsAggregate"] or 0),
                dest_is_aggregate=int(row["DestIsAggregate"] or 0),
            )
            if _same(kind, ("Generalization",)):
                model.generalizations.append(connector)
            elif profile.relation_types is not None:
                if _same(kind, profile.relation_types):
                    model.relations.append(connector)
            elif not _same(kind, profile.excluded_relations):
                model.relations.append(connector)

        if attributes:
            columns = _columns(db, "t_attribute")
            select = ", ".join(
                [
                    "ID",
                    "Name",
                    "Type",
                    "LowerBound",
                    "UpperBound",
                    "Classifier" if "Classifier" in columns else "0 AS Classifier",
                    "Stereotype" if "Stereotype" in columns else "'' AS Stereotype",
                    "Notes" if "Notes" in columns else "'' AS Notes",
                ]
            )
            for ident in model.elements:
                model.attributes[ident] = [
                    Attribute(
                        name=row["Name"],
                        type=row["Type"] or "",
                        lower=row["LowerBound"] or "",
                        upper=row["UpperBound"] or "",
                        definition=_attribute_definition(db, row, profile),
                        classifier=int(row["Classifier"]) if str(row["Classifier"] or "").isdigit() else 0,
                        position=place,
                        stereotype=row["Stereotype"] or "",
                    )
                    for place, row in enumerate(
                        db.execute(
                            f"SELECT {select} FROM t_attribute WHERE Object_ID=? ORDER BY Pos, Name",  # nosec B608
                            (ident,),
                        ),
                        start=1,
                    )
                ]
        return model
    finally:
        db.close()


def _attribute_definition(db: sqlite3.Connection, row: sqlite3.Row, profile: Profile) -> str:
    """The definition of one attribute: the tagged value named by the profile, else (when the profile says so) the
    attribute's Notes."""
    if profile.definition_tag:
        tagged = _tags(db, "t_attributetag", "ElementID", row["ID"], profile).get(profile.definition_tag, "")
        if tagged or not profile.attribute_definition_from_notes:
            return tagged
    return clean_text(row["Notes"], profile.definition_text) if profile.attribute_definition_from_notes else ""


def _tags(db: sqlite3.Connection, table: str, key: str, ident: int, profile: Profile) -> dict[str, str]:
    """Tagged values of one element or attribute: {property: text}, the memo (Notes) before the short value."""
    rows = db.execute(f"SELECT Property, Value, Notes FROM {table} WHERE {key}=?", (ident,))  # nosec B608
    return {row["Property"]: clean_text(row["Notes"] or row["Value"], profile.definition_text) for row in rows}
