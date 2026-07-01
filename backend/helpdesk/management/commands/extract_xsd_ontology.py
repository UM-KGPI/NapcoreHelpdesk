"""
Management command to extract concept glossary from NeTEx, OpRa, and SIRI XSD schemas.

Usage:
    python manage.py extract_xsd_ontology --netex-path /path/to/NeTEx --opra-path /path/to/OpRa --siri-path /path/to/SIRI --output ontologies/standards.json
"""

import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set

import yaml
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)

# XSD namespace
XSD_NS = {"xsd": "http://www.w3.org/2001/XMLSchema"}
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

# Legacy focused NeTEx files used in early extraction passes.
# Full-tree NeTEx extraction is now the default because the federated
# ontology needs broad concept coverage for GraphDB reasoning.
KEY_NETEX_FILES = [
    "netex_part_2/part2_journeyTimes/netex_vehicleJourney_support.xsd",
    "netex_part_2/part2_journeyTimes/netex_vehicleJourneyTimes_support.xsd",
    "netex_part_2/part2_journeyTimes/netex_serviceJourney_support.xsd",
    "netex_part_1/part1_networkDescription/netex_line_version.xsd",
    "netex_part_1/part1_ifopt/netex_ifopt_stopPlace_support.xsd",
    "netex_part_3/part3_monitoring/netex_monitoredVehicleJourney_support.xsd",
]

# Legacy focused OpRa files used in early extraction passes.
# Full-tree OpRa extraction is now the default for parity with NeTEx.
KEY_OPRA_FILES = [
    "opra_indicators/opra_lateDatedVehicleJourney_version.xsd",
    "opra_indicators/opra_cancelledDatedVehicleJourney_version.xsd",
    "opra_indicators/opra_capacity_version.xsd",
    "opra_indicators/opra_serviceIntensity_version.xsd",
    "opra_indicators/opra_expectedPassengerCount_version.xsd",
    "opra_indicators/opra_externalPassengerCount_version.xsd",
    "opra_framework/opra_reusableComponents/opra_delayClassification_version.xsd",
    "opra_framework/opra_reusableComponents/opra_vehicleOccupancy_version.xsd",
    "opra_framework/opra_frames/opra_indicatorFrame_version.xsd",
]

EXAMPLE_XML_GLOB = "examples/**/*.xml"

MANUAL_CORE_CONCEPT_IDS = {
    "opra:DelayedJourney",
    "opra:CancelledJourney",
    "opra:DelayStatistics",
    "opra:LateDatedVehicleJourneyEntry",
    "opra:JourneyEventsExample",
    "netex:VehicleJourney",
    "netex:JourneyPattern",
    "netex:ScheduledStopPoint",
    "netex:TimetabledPassingTime",
    "netex:Line",
    "netex:Operator",
    "transmodel:Journey",
    "siri:VehicleMonitoring",
    "siri:StopMonitoring",
    "siri:EstimatedTimetable",
    "datex:TrafficEvent",
}

# Known noisy/technical concepts that should never be in glossary.
DENYLIST_CONCEPT_IDS = {
    "netex:Line_Dummy",
    "netex:Via_VersionedChildStructure",
    "netex:NetworkView",
    "netex:LineView",
    "netex:DestinationDisplayView",
}

PREFIX_TO_STANDARD = {
    "opra": "opra",
    "netex": "netex",
    "siri": "siri",
    "transmodel": "transmodel",
    "datex": "datex",
}

# Keep defaults in code; prefer external YAML config for expert curation.
DEFAULT_ALLOWLIST_EXACT = {
    "netex": {
        "GroupOfLines",
        "Network",
        "DestinationDisplay",
        "DestinationDisplayVariant",
        "AllowedLineDirection",
        "TypeOfLine",
    },
    "opra": {
        "LateDatedVehicleJourneyCount",
        "CancelledDatedVehicleJourneyCount",
        "PlannedCapacity",
        "ActualCapacity",
        "CapacitySpecification",
        "VehicleTypeCapacity",
        "PlannedServiceIntensity",
        "ActualServiceIntensity",
        "ExpectedServiceIntensity",
        "MeanCapacityOverNetworkDistance",
        "MeanCapacityOverRouteDistance",
        "MeanCapacityOverJourneyDistance",
        "LoadOverJourneyDistance",
        "TransportPerformance",
        "TransportPerformancePerVehicle",
        "AverageCommercialSpeed",
        "ExpectedPassengerCount",
        "ExternalPassengerCount",
        "TypeOfDelay",
        "VehicleLoadEntry",
        "PreparednessLevel",
        "IndicatorFrame",
    },
    "siri": {
        "VehicleMonitoring",
        "StopMonitoring",
        "EstimatedTimetable",
        "GeneralMessage",
        "SituationExchange",
        "FacilityMonitoring",
        "ConnectionMonitoring",
        "ConnectionTimetable",
        "ProductionTimetable",
        "StopTimetable",
        "MonitoredVehicleJourney",
        "EstimatedVehicleJourney",
        "DatedVehicleJourney",
    },
}

DEFAULT_ALLOWLIST_TOKEN = {
    "netex": {
        "journey",
        "line",
        "network",
        "destination",
        "stop",
        "operator",
    },
    "opra": {
        "delay",
        "capacity",
        "service",
        "passenger",
        "journey",
        "vehicle",
        "indicator",
    },
    "siri": {
        "vehicle",
        "journey",
        "stop",
        "monitor",
        "timetable",
        "estimated",
        "facility",
        "connection",
        "message",
        "situation",
    },
}

DEFAULT_DENYLIST_CONCEPT_IDS = set(DENYLIST_CONCEPT_IDS)

# Loaded from backend/helpdesk/ontologies/extractor_allowlist.yaml
ALLOWLIST_EXACT = DEFAULT_ALLOWLIST_EXACT
ALLOWLIST_TOKEN = DEFAULT_ALLOWLIST_TOKEN


def _iter_xsd_files(repo_root: Path, *, standard: str, key_files_only: bool = False) -> list[Path]:
    xsd_root = repo_root / "xsd"
    if standard == "netex":
        if key_files_only:
            return [xsd_root / relative_path for relative_path in KEY_NETEX_FILES]
        return sorted(
            path
            for path in xsd_root.rglob("*.xsd")
            if path.is_file()
            and path.relative_to(xsd_root).parts
            and path.relative_to(xsd_root).parts[0].startswith("netex_")
        )
    if standard == "opra":
        if key_files_only:
            return [xsd_root / relative_path for relative_path in KEY_OPRA_FILES]
        return sorted(path for path in xsd_root.rglob("*.xsd") if path.is_file())
    if standard == "siri":
        # Keep SIRI extraction focused on SIRI model/service schemas and avoid
        # broad imported utility trees (gml, ifopt, acsb, xml, datex2).
        include_prefixes = (
            "siri",
            "siri_",
            "siri_model",
            "siri_model_discovery",
            "siri_utility",
            "wsdl_model",
        )
        return sorted(
            path
            for path in xsd_root.rglob("*.xsd")
            if path.is_file()
            and path.relative_to(xsd_root).parts
            and path.relative_to(xsd_root).parts[0].startswith(include_prefixes)
        )
    raise ValueError(f"Unsupported standard: {standard}")


def _load_extractor_allowlist_config(config_path: Path) -> tuple[dict[str, set[str]], dict[str, set[str]], set[str]]:
    """Load allowlist and denylist config from YAML with safe defaults."""

    exact = {k: set(v) for k, v in DEFAULT_ALLOWLIST_EXACT.items()}
    token = {k: set(v) for k, v in DEFAULT_ALLOWLIST_TOKEN.items()}
    denylist = set(DEFAULT_DENYLIST_CONCEPT_IDS)

    if not config_path.exists():
        return exact, token, denylist

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    except Exception as exc:
        logger.warning(f"Failed to load extractor allowlist config {config_path}: {exc}")
        return exact, token, denylist

    for namespace, values in (config.get("allowlist_exact") or {}).items():
        if isinstance(values, list):
            exact[namespace] = set(str(v) for v in values)

    for namespace, values in (config.get("allowlist_token") or {}).items():
        if isinstance(values, list):
            token[namespace] = set(str(v) for v in values)

    deny_values = config.get("denylist_concept_ids") or []
    if isinstance(deny_values, list):
        denylist = set(str(v) for v in deny_values)

    return exact, token, denylist


def extract_documentation(element: ET.Element) -> str:
    """Extract documentation from xsd:annotation/xsd:documentation."""
    annotation = element.find("xsd:annotation", XSD_NS)
    if annotation is None:
        return ""

    doc = annotation.find("xsd:documentation", XSD_NS)
    if doc is not None and doc.text:
        return doc.text.strip()
    return ""


def _is_domain_concept(elem_name: str, description: str) -> bool:
    """Check if element is a meaningful domain concept (not technical infrastructure)."""
    if not elem_name:
        return False

    # Skip technical/structural types
    if any(x in elem_name for x in [
        "Ref", "RefStructure", "RelStructure", "VersionStructure", "IdType", "CodeType",
        "DerivedViewStructure", "ValueStructure", "SupportStructure", "InFrame", "AbstractStructure"
    ]):
        return False

    # Skip enums and small types
    if any(x in elem_name for x in ["Enumeration", "Enum", "Code", "Alias", "Role", "Period", "Plate", "Cleardown"]):
        return False

    # Skip explicit technical suffixes.
    if elem_name.endswith(("Structure", "Group", "Type", "Dummy", "View")):
        return False

    # Domain concepts should have substantive descriptions
    if description and len(description) > 25:
        return True

    return False


def _is_noisy_name(elem_name: str) -> bool:
    return (
        elem_name.endswith(("_Dummy", "_Structure", "_Group", "_View"))
        or "VersionedChildStructure" in elem_name
    )


def _concept_id_from_ref(ref_value: str, default_prefix: str) -> str | None:
    """Convert XSD ref value to concept id like prefix:ConceptName."""

    if not ref_value:
        return None

    if ":" in ref_value:
        prefix, local_name = ref_value.split(":", 1)
        concept_prefix = prefix
    else:
        local_name = ref_value
        concept_prefix = default_prefix

    if local_name.endswith("Ref"):
        local_name = local_name[:-3]

    if not local_name or _is_noisy_name(local_name):
        return None

    if any(token in local_name for token in ["Group", "Structure", "Version", "Frame", "DataManagedObject"]):
        return None

    if concept_prefix not in PREFIX_TO_STANDARD:
        return None

    return f"{concept_prefix}:{local_name}"


def _extract_related_concepts(element: ET.Element, default_prefix: str, self_concept_id: str) -> list[str]:
    """Extract candidate relationships from nested xsd:element[@ref] and substitutionGroup."""

    related: Set[str] = set()

    substitution_group = element.get("substitutionGroup")
    if substitution_group:
        concept_id = _concept_id_from_ref(substitution_group, default_prefix)
        if concept_id and concept_id != self_concept_id:
            related.add(concept_id)

    for nested in element.findall(".//xsd:element", XSD_NS):
        ref_value = nested.get("ref")
        if not ref_value:
            continue
        concept_id = _concept_id_from_ref(ref_value, default_prefix)
        if concept_id and concept_id != self_concept_id:
            related.add(concept_id)

    return sorted(related)


def _is_likely_auto_extracted(concept_id: str, concept_data: dict) -> bool:
    """Heuristic for stale auto-extracted records from older runs."""

    if concept_id in MANUAL_CORE_CONCEPT_IDS:
        return False

    if concept_data.get("extracted_from") == "xsd":
        return True

    source_standards = set(concept_data.get("source_standards") or [])
    has_manual_linkage = bool(concept_data.get("synonym_of") or concept_data.get("parent") or concept_data.get("related_to"))
    if source_standards and source_standards.issubset({"netex", "opra"}) and not has_manual_linkage:
        return True

    return False


def _is_allowlisted_concept(namespace_prefix: str, elem_name: str, disable_allowlist: bool) -> bool:
    if disable_allowlist:
        return True

    exact = ALLOWLIST_EXACT.get(namespace_prefix, set())
    if elem_name in exact:
        return True

    tokens = ALLOWLIST_TOKEN.get(namespace_prefix, set())
    lowered = elem_name.lower()
    return any(token in lowered for token in tokens)


def extract_concepts_from_xsd(
    xsd_path: Path,
    namespace_prefix: str,
    disable_allowlist: bool = False,
    source_root: Path | None = None,
) -> Dict[str, Dict]:
    """
    Extract concept definitions from a single XSD file.

    Returns dict mapping concept_id -> {name, description, labels}
    """
    concepts = {}

    if not xsd_path.exists():
        logger.warning(f"XSD file not found: {xsd_path}")
        return concepts

    try:
        tree = ET.parse(xsd_path)
        root = tree.getroot()
    except Exception as e:
        logger.error(f"Failed to parse {xsd_path}: {e}")
        return concepts

    # Extract top-level xsd:element definitions (best signal for domain entities).
    for elem in root.findall("xsd:element", XSD_NS):
        elem_name = elem.get("name")
        if not elem_name:
            continue

        doc = extract_documentation(elem)
        if not _is_domain_concept(elem_name, doc):
            continue
        if not _is_allowlisted_concept(namespace_prefix, elem_name, disable_allowlist):
            continue

        concept_id = f"{namespace_prefix}:{elem_name}"
        if concept_id in DENYLIST_CONCEPT_IDS:
            continue
        labels = _generate_labels(elem_name, doc)
        related_to = _extract_related_concepts(elem, namespace_prefix, concept_id)

        concepts[concept_id] = {
            "name": elem_name,
            "description": doc,
            "labels": labels,
            "source": str(xsd_path.relative_to(source_root)) if source_root else str(xsd_path.name),
            "related_to": related_to,
        }

    return concepts


def _generate_labels(name: str, description: str) -> List[str]:
    """Generate query labels from element name and documentation."""
    labels = set()

    # Add the name as-is (lowercase)
    labels.add(name.lower())

    # Split camelCase: VehicleJourney -> vehicle journey
    camel_case = re.sub(r"([a-z])([A-Z])", r"\1 \2", name).lower()
    if camel_case != name.lower():
        labels.add(camel_case)

    # Include underscore-separated variant for names like Foo_Bar.
    snake_like = re.sub(r"_+", " ", name).lower().strip()
    if snake_like and snake_like != name.lower() and snake_like != camel_case:
        labels.add(snake_like)

    # Extract first few words from documentation if they are domain-aligned.
    if description:
        words = description.split()[:5]
        if words:
            phrase = " ".join(words).lower()
            # Clean up common patterns
            phrase = re.sub(r"^(a|an|the) ", "", phrase)
            phrase = re.sub(r"[^a-z0-9\s]", "", phrase).strip()
            generic_starts = (
                "implementation of",
                "element for",
                "type for",
                "representation of",
            )
            generic_ends = (
                " of a",
                " of an",
                " of the",
                " which",
                " that",
            )
            name_tokens = {
                token
                for token in re.sub(r"([a-z])([A-Z])", r"\1 \2", name).replace("_", " ").lower().split()
                if len(token) > 2
            }
            phrase_tokens = {
                token for token in phrase.split() if len(token) > 2
            }
            token_overlap = len(name_tokens.intersection(phrase_tokens))
            if (
                phrase
                and phrase != name.lower()
                and not phrase.startswith(generic_starts)
                and not phrase.endswith(generic_ends)
                and token_overlap >= 1
            ):
                labels.add(phrase)

    return sorted(list(labels))


def _normalize_text_tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall((text or "").lower())


def _normalize_for_matching(text: str) -> str:
    return " ".join(_normalize_text_tokens(text))


def _alias_matches_text(alias: str, normalized_text: str) -> bool:
    normalized_alias = _normalize_for_matching(alias)
    if not normalized_alias:
        return False
    if normalized_alias in normalized_text:
        return True

    alias_tokens = set(normalized_alias.split())
    text_tokens = set(normalized_text.split())
    return bool(alias_tokens) and alias_tokens.issubset(text_tokens)


def _build_alias_index(concepts: dict) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for concept_id, concept_data in concepts.items():
        labels = concept_data.get("labels") or []
        if labels:
            index[concept_id] = {str(label) for label in labels}
    return index


def _safe_relative_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except Exception:
        return str(path)


def _extract_xml_text_signature(xml_path: Path, repo_root: Path) -> str:
    """Build a lexical signature from XML tags/attributes/path for concept matching."""

    terms: list[str] = []
    terms.extend(_normalize_text_tokens(xml_path.stem))
    terms.extend(_normalize_text_tokens(_safe_relative_path(xml_path, repo_root)))

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception:
        return " ".join(terms)

    for element in root.iter():
        tag_name = element.tag.split("}", 1)[-1] if "}" in element.tag else element.tag
        terms.extend(_normalize_text_tokens(re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", tag_name)))
        for attr_name in element.attrib.keys():
            attr_label = attr_name.split("}", 1)[-1] if "}" in attr_name else attr_name
            terms.extend(_normalize_text_tokens(re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", attr_label)))

    return " ".join(terms)


def extract_concept_links_from_examples(
    repo_root: Path,
    concepts: dict,
) -> tuple[dict[str, set[str]], dict[str, set[str]], int]:
    """Link ontology concepts to XML examples and infer generic co-occurrence relations."""

    examples_dir = repo_root / "examples"
    if not examples_dir.exists():
        return {}, {}, 0

    alias_index = _build_alias_index(concepts)
    concept_sources: dict[str, set[str]] = {}
    concept_relations: dict[str, set[str]] = {}
    scanned = 0

    for xml_path in sorted(repo_root.glob(EXAMPLE_XML_GLOB)):
        if not xml_path.is_file():
            continue

        scanned += 1
        signature = _extract_xml_text_signature(xml_path, repo_root)
        if not signature:
            continue

        matched_concepts: set[str] = set()
        for concept_id, aliases in alias_index.items():
            if any(_alias_matches_text(alias, signature) for alias in aliases):
                matched_concepts.add(concept_id)

        if not matched_concepts:
            continue

        relative_path = _safe_relative_path(xml_path, repo_root)
        for concept_id in matched_concepts:
            concept_sources.setdefault(concept_id, set()).add(relative_path)

        if len(matched_concepts) > 1:
            sorted_ids = sorted(matched_concepts)
            for concept_id in sorted_ids:
                concept_relations.setdefault(concept_id, set()).update(
                    {other for other in sorted_ids if other != concept_id}
                )

    return concept_sources, concept_relations, scanned


class Command(BaseCommand):
    help = "Extract concept glossary from NeTEx, OpRa, and SIRI XSD schemas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--netex-path",
            type=Path,
            help="Path to NeTEx repository root",
        )
        parser.add_argument(
            "--opra-path",
            type=Path,
            help="Path to OpRa repository root",
        )
        parser.add_argument(
            "--siri-path",
            type=Path,
            help="Path to SIRI repository root",
        )
        parser.add_argument(
            "--output",
            type=Path,
            default=Path(__file__).parent.parent.parent / "ontologies" / "standards.json",
            help="Output path for updated ontology JSON inventory",
        )
        parser.add_argument(
            "--merge",
            action="store_true",
            help="Merge with existing ontology instead of replacing",
        )
        parser.add_argument(
            "--refresh-auto",
            action="store_true",
            help="Remove auto-extracted concepts and rebuild them from XSD while preserving curated glossary entries.",
        )
        parser.add_argument(
            "--disable-allowlist",
            action="store_true",
            help="Disable namespace allowlists (imports more concepts, including lower-value ones).",
        )
        parser.add_argument(
            "--netex-key-files-only",
            action="store_true",
            help="Use the legacy focused NeTEx file subset instead of scanning the full NeTEx XSD tree.",
        )
        parser.add_argument(
            "--opra-key-files-only",
            action="store_true",
            help="Use the legacy focused OpRa file subset instead of scanning the full OpRa XSD tree.",
        )
        parser.add_argument(
            "--skip-example-xml",
            action="store_true",
            help="Skip extracting concept links from XML files under examples/.",
        )

    def handle(self, *args, **options):
        global ALLOWLIST_EXACT, ALLOWLIST_TOKEN, DENYLIST_CONCEPT_IDS

        netex_path = options.get("netex_path")
        opra_path = options.get("opra_path")
        siri_path = options.get("siri_path")
        output_path = Path(options["output"])
        merge = options.get("merge", False)
        refresh_auto = options.get("refresh_auto", False)
        disable_allowlist = options.get("disable_allowlist", False)
        netex_key_files_only = options.get("netex_key_files_only", False)
        opra_key_files_only = options.get("opra_key_files_only", False)
        skip_example_xml = options.get("skip_example_xml", False)

        config_path = Path(__file__).parent.parent.parent / "ontologies" / "extractor_allowlist.yaml"
        loaded_exact, loaded_token, loaded_denylist = _load_extractor_allowlist_config(config_path)
        ALLOWLIST_EXACT = loaded_exact
        ALLOWLIST_TOKEN = loaded_token
        DENYLIST_CONCEPT_IDS = loaded_denylist

        if not netex_path:
            netex_path = Path("/Users/andrejt/Research/repositories/git/NeTEx")

        netex_path = Path(netex_path)
        if not netex_path.exists():
            raise CommandError(f"NeTEx path does not exist: {netex_path}")

        if not opra_path:
            opra_path = Path("/Users/andrejt/Research/repositories/git/OpRa")
        opra_path = Path(opra_path)
        if not opra_path.exists():
            raise CommandError(f"OpRa path does not exist: {opra_path}")

        if not siri_path:
            siri_path = Path("/Users/andrejt/Research/repositories/git/SIRI")
        siri_path = Path(siri_path)
        if not siri_path.exists():
            raise CommandError(f"SIRI path does not exist: {siri_path}")

        self.stdout.write(f"Extracting concepts from NeTEx at {netex_path}")

        # Load existing ontology if merging
        ontology = {}
        if merge and output_path.exists():
            with open(output_path) as f:
                ontology = json.load(f) or {}

        if "concepts" not in ontology:
            ontology["concepts"] = {}

        if refresh_auto:
            removed_auto = 0
            for concept_id in list(ontology["concepts"].keys()):
                concept_data = ontology["concepts"][concept_id]
                if _is_likely_auto_extracted(concept_id, concept_data):
                    del ontology["concepts"][concept_id]
                    removed_auto += 1
            self.stdout.write(f"Removed {removed_auto} auto-extracted concepts before refresh")

        removed_noisy = 0
        for concept_id in list(ontology["concepts"].keys()):
            if concept_id in DENYLIST_CONCEPT_IDS:
                del ontology["concepts"][concept_id]
                removed_noisy += 1
        if removed_noisy:
            self.stdout.write(f"Removed {removed_noisy} denylisted concepts")

        # Extract NeTEx concepts
        netex_concepts = {}
        netex_files = _iter_xsd_files(netex_path, standard="netex", key_files_only=netex_key_files_only)
        netex_with_concepts = 0
        for xsd_file in netex_files:
            concepts = extract_concepts_from_xsd(
                xsd_file,
                "netex",
                disable_allowlist=(disable_allowlist or not netex_key_files_only),
                source_root=netex_path / "xsd",
            )
            if concepts:
                netex_with_concepts += 1
            netex_concepts.update(concepts)
            if netex_key_files_only:
                relative_path = xsd_file.relative_to(netex_path / "xsd")
                self.stdout.write(f"  ✓ {relative_path}: {len(concepts)} concepts")

        self.stdout.write(
            f"\nTotal NeTEx concepts extracted: {len(netex_concepts)} "
            f"from {len(netex_files)} XSD files ({netex_with_concepts} yielded concepts)"
        )

        self.stdout.write(f"\nExtracting concepts from OpRa at {opra_path}")
        opra_concepts = {}
        opra_files = _iter_xsd_files(opra_path, standard="opra", key_files_only=opra_key_files_only)
        opra_with_concepts = 0
        for xsd_file in opra_files:
            concepts = extract_concepts_from_xsd(
                xsd_file,
                "opra",
                disable_allowlist=(disable_allowlist or not opra_key_files_only),
                source_root=opra_path / "xsd",
            )
            if concepts:
                opra_with_concepts += 1
            opra_concepts.update(concepts)
            if opra_key_files_only:
                relative_path = xsd_file.relative_to(opra_path / "xsd")
                self.stdout.write(f"  ✓ {relative_path}: {len(concepts)} concepts")

        self.stdout.write(
            f"\nTotal OpRa concepts extracted: {len(opra_concepts)} "
            f"from {len(opra_files)} XSD files ({opra_with_concepts} yielded concepts)"
        )

        self.stdout.write(f"\nExtracting concepts from SIRI at {siri_path}")
        siri_concepts = {}
        siri_files = _iter_xsd_files(siri_path, standard="siri", key_files_only=False)
        siri_with_concepts = 0
        for xsd_file in siri_files:
            concepts = extract_concepts_from_xsd(
                xsd_file,
                "siri",
                disable_allowlist=(disable_allowlist or True),
                source_root=siri_path / "xsd",
            )
            if concepts:
                siri_with_concepts += 1
            siri_concepts.update(concepts)

        self.stdout.write(
            f"\nTotal SIRI concepts extracted: {len(siri_concepts)} "
            f"from {len(siri_files)} XSD files ({siri_with_concepts} yielded concepts)"
        )

        # Keep only relationships that point to known concept ids.
        known_concepts = (
            set(ontology["concepts"].keys())
            | set(netex_concepts.keys())
            | set(opra_concepts.keys())
            | set(siri_concepts.keys())
        )
        for concept_data in netex_concepts.values():
            concept_data["related_to"] = [
                cid for cid in concept_data.get("related_to", []) if cid in known_concepts
            ]
        for concept_data in opra_concepts.values():
            concept_data["related_to"] = [
                cid for cid in concept_data.get("related_to", []) if cid in known_concepts
            ]
        for concept_data in siri_concepts.values():
            concept_data["related_to"] = [
                cid for cid in concept_data.get("related_to", []) if cid in known_concepts
            ]

        # Add extracted concepts, preserving existing ones if merging
        extracted_at = datetime.now(timezone.utc).isoformat()
        for concept_id, concept_data in netex_concepts.items():
            if concept_id not in ontology["concepts"]:
                ontology["concepts"][concept_id] = {
                    "labels": concept_data["labels"],
                    "description": concept_data["description"],
                    "related_to": concept_data["related_to"],
                    "source_standards": ["netex"],
                    "indexed_standards": ["netex"],
                    "extracted_from": "xsd",
                    "extracted_source": concept_data["source"],
                    "extracted_at": extracted_at,
                }

        for concept_id, concept_data in opra_concepts.items():
            if concept_id not in ontology["concepts"]:
                ontology["concepts"][concept_id] = {
                    "labels": concept_data["labels"],
                    "description": concept_data["description"],
                    "related_to": concept_data["related_to"],
                    "source_standards": ["opra"],
                    "indexed_standards": ["opra"],
                    "extracted_from": "xsd",
                    "extracted_source": concept_data["source"],
                    "extracted_at": extracted_at,
                }

        for concept_id, concept_data in siri_concepts.items():
            if concept_id not in ontology["concepts"]:
                ontology["concepts"][concept_id] = {
                    "labels": concept_data["labels"],
                    "description": concept_data["description"],
                    "related_to": concept_data["related_to"],
                    "source_standards": ["siri"],
                    "indexed_standards": ["siri"],
                    "extracted_from": "xsd",
                    "extracted_source": concept_data["source"],
                    "extracted_at": extracted_at,
                }

        if not skip_example_xml:
            netex_example_sources, netex_example_relations, netex_scanned = extract_concept_links_from_examples(
                repo_root=netex_path,
                concepts=ontology["concepts"],
            )
            opra_example_sources, opra_example_relations, opra_scanned = extract_concept_links_from_examples(
                repo_root=opra_path,
                concepts=ontology["concepts"],
            )
            siri_example_sources, siri_example_relations, siri_scanned = extract_concept_links_from_examples(
                repo_root=siri_path,
                concepts=ontology["concepts"],
            )

            merged_sources: dict[str, set[str]] = {}
            for concept_id, sources in netex_example_sources.items():
                merged_sources.setdefault(concept_id, set()).update(sources)
            for concept_id, sources in opra_example_sources.items():
                merged_sources.setdefault(concept_id, set()).update(sources)
            for concept_id, sources in siri_example_sources.items():
                merged_sources.setdefault(concept_id, set()).update(sources)

            merged_relations: dict[str, set[str]] = {}
            for concept_id, related in netex_example_relations.items():
                merged_relations.setdefault(concept_id, set()).update(related)
            for concept_id, related in opra_example_relations.items():
                merged_relations.setdefault(concept_id, set()).update(related)
            for concept_id, related in siri_example_relations.items():
                merged_relations.setdefault(concept_id, set()).update(related)

            for concept_id, sources in merged_sources.items():
                concept_data = ontology["concepts"].get(concept_id)
                if not concept_data:
                    continue
                existing_sources = set(concept_data.get("example_sources") or [])
                existing_sources.update(sources)
                concept_data["example_sources"] = sorted(existing_sources)[:25]

            known_concept_ids = set(ontology["concepts"].keys())
            for concept_id, related in merged_relations.items():
                concept_data = ontology["concepts"].get(concept_id)
                if not concept_data:
                    continue
                existing_related = set(concept_data.get("related_to") or [])
                existing_related.update(
                    other
                    for other in related
                    if other in known_concept_ids and other != concept_id
                )
                concept_data["related_to"] = sorted(existing_related)[:40]

            self.stdout.write(
                f"Linked XML examples: scanned {netex_scanned + opra_scanned + siri_scanned} files, "
                f"concepts with example links: {len(merged_sources)}"
            )

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(ontology, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Ontology updated at {output_path}")
        )
        self.stdout.write(f"  Total concepts: {len(ontology.get('concepts', {}))}")

        # Also generate TTL files with full semantic relationships
        self._generate_ttl_files(ontology, output_path.parent.parent / "standards")

    def _generate_ttl_files(self, ontology: dict, output_dir: Path) -> None:
        """Generate TTL files for each standard with full semantic relationships."""
        output_dir.mkdir(parents=True, exist_ok=True)
        namespaces = ontology.get("namespaces", {})

        for standard in ["netex", "opra", "siri", "datex", "transmodel"]:
            concepts = {
                cid: cdata
                for cid, cdata in ontology.get("concepts", {}).items()
                if cid.startswith(f"{standard}:")
            }

            if not concepts:
                continue

            ttl_lines = self._build_ttl_content(standard, concepts, namespaces)
            output_file = output_dir / f"{standard}.ttl"

            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(ttl_lines))

            self.stdout.write(
                self.style.SUCCESS(f"  ✓ {standard}.ttl: {len(concepts)} concepts with full relationships")
            )

    def _build_ttl_content(self, standard: str, concepts: dict, namespaces: dict) -> list[str]:
        """Build Turtle TTL content with rdfs:subClassOf and skos:definition."""
        lines = []

        # Prefixes
        lines.append("@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
        lines.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
        lines.append("@prefix owl:  <http://www.w3.org/2002/07/owl#> .")
        lines.append("@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .")
        lines.append("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .")
        lines.append("@prefix dct:  <http://purl.org/dc/terms/> .")
        lines.append("")

        for prefix, namespace in namespaces.items():
            lines.append(f"@prefix {prefix}: <{namespace}> .")
        lines.append("")

        # Ontology header
        std_ns = namespaces.get(standard, f"https://napcore.eu/ontology/{standard}#")
        lines.append(f"<{std_ns[:-1]}>")
        lines.append("    a owl:Ontology ;")
        lines.append(f'    dct:title "{standard.upper()} Ontology with Schema Relationships"@en ;')
        lines.append(
            f'    dct:description "OWL ontology with extracted inheritance and composition relationships from XSD."@en ;'
        )
        lines.append('    owl:versionInfo "0.2-xsd-rebuild-with-relationships" ;')
        lines.append('    dct:license <https://creativecommons.org/licenses/by/4.0/> .')
        lines.append("")
        lines.append("#################################################################")
        lines.append("# Concepts with Semantic Relationships")
        lines.append("#################################################################")
        lines.append("")

        # Concept definitions
        for concept_id in sorted(concepts.keys()):
            concept = concepts[concept_id]
            lines.append(f"{concept_id}")
            lines.append("    a owl:Class ;")

            # Label
            name = concept.get("name", "")
            if name:
                lines.append(f'    rdfs:label "{name}"@en ;')

            # Definition from description (xsd:annotation/xsd:documentation)
            description = concept.get("description", "").strip()
            if description:
                escaped = description.replace('"', '\\"').replace("\n", " ")
                lines.append(f'    skos:definition "{escaped}"@en ;')

            # Preferred labels
            labels = concept.get("labels", [])
            if labels:
                lines.append(f'    skos:prefLabel "{labels[0]}"@en ;')
                for alt_label in labels[1:]:
                    lines.append(f'    skos:altLabel "{alt_label}"@en ;')

            # Relationships extracted from substitutionGroup and xsd:group refs
            related_to = concept.get("related_to", [])
            if related_to:
                for related_id in related_to:
                    lines.append(f"    rdfs:subClassOf {related_id} ;")

            # Source
            source = concept.get("source", "")
            if source:
                lines.append(f'    rdfs:comment "Extracted from: {source}"@en .')
            else:
                lines.append('    rdfs:comment "Extracted from XSD schema"@en .')

            lines.append("")

        return lines
