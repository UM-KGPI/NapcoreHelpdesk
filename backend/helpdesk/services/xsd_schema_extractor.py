"""
Extract actual XSD schema element definitions for semantic search.

Instead of just storing "Journey is a concept", extract the actual XSD definition:
  <xs:element name="DepartureTime" type="xs:time"/>
  <xs:element name="Journey" type="JourneyType"/>
  <xs:complexType name="JourneyType">
    <xs:sequence>
      <xs:element name="DepartureTime" type="xs:time"/>
      <xs:element name="ArrivalTime" type="xs:time"/>
    </xs:sequence>
  </xs:complexType>

This provides structural information crucial for answering "How is X represented?"
questions.

Created: 2026-07-03
"""

from __future__ import annotations

import logging
import re
import ssl
from xml.etree import ElementTree as ET
from typing import Optional
from urllib.request import urlopen
from urllib.error import URLError

logger = logging.getLogger(__name__)

# Local XSD file paths (repositories cloned locally)
# Search multiple locations for element definitions
NETEX_XSD_PATHS = {
    "journey_times": "/Users/andrejt/Research/repositories/git/NeTEx/xsd/netex_part_2/part2_journeyTimes/netex_passingTimes_version.xsd",
    "service_journey": "/Users/andrejt/Research/repositories/git/NeTEx/xsd/netex_part_2/part2_journeyTimes/netex_serviceJourney_version.xsd",
    "netex_framework": "/Users/andrejt/Research/repositories/git/NeTEx/xsd/netex_framework/netex_all_objects_framework.xsd",
    "netex_part1": "/Users/andrejt/Research/repositories/git/NeTEx/xsd/netex_part_1/netex_all_objects_part1.xsd",
    "netex_part2": "/Users/andrejt/Research/repositories/git/NeTEx/xsd/netex_part_2/netex_all_objects_part2.xsd",
}

SIRI_XSD_PATHS = {
    "siri_framework": "/Users/andrejt/Research/repositories/git/SIRI/xsd/siri_all_framework-v2.0.xsd",
}

OPRA_XSD_PATHS = {
    "opra_framework": "/Users/andrejt/Research/repositories/git/OpRa/xsd/opra_all_objects.xsd",
}

# Map standards to their XSD paths
STANDARD_XSD_MAP = {
    "NeTEx": NETEX_XSD_PATHS,
    "SIRI": SIRI_XSD_PATHS,
    "OpRa": OPRA_XSD_PATHS,
}


def _read_xsd_file(file_path: str) -> Optional[str]:
    """Read XSD file from local filesystem."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (FileNotFoundError, IOError) as e:
        logger.debug(f"Failed to read XSD file {file_path}: {e}")
        return None


def _find_element_in_xsd(xsd_content: str, element_name: str) -> Optional[str]:
    """
    Find an element definition in XSD content.

    Returns the complete element definition as a string, or None if not found.
    Handles both simple elements and complex types.

    Example matches:
      <xs:element name="DepartureTime" type="xs:time"/>
      <xs:complexType name="JourneyType">...</xs:complexType>
    """
    # Try to parse as XML for precision
    try:
        root = ET.fromstring(xsd_content)
        ns = {"xs": "http://www.w3.org/2001/XMLSchema"}

        # Search for element with matching name
        for elem in root.findall(".//xs:element[@name='" + element_name + "']", ns):
            # Extract the element and nearby context
            element_str = ET.tostring(elem, encoding="unicode")
            return element_str

        # Search for complexType or simpleType with matching name
        for type_elem in root.findall(".//xs:complexType[@name='" + element_name + "']", ns):
            type_str = ET.tostring(type_elem, encoding="unicode")
            return type_str

        for type_elem in root.findall(".//xs:simpleType[@name='" + element_name + "']", ns):
            type_str = ET.tostring(type_elem, encoding="unicode")
            return type_str

    except ET.ParseError as e:
        logger.debug(f"Failed to parse XSD as XML: {e}, falling back to regex")

    # Fallback: regex search for element definition
    # Matches: <xs:element name="ElementName" ... />
    pattern = rf'<xs:element\s+name="{element_name}"[^>]*(?:>.*?</xs:element>|/>)'
    match = re.search(pattern, xsd_content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(0)

    # Try to find type definition
    type_pattern = rf'<xs:(?:complex|simple)Type\s+name="{element_name}".*?</xs:(?:complex|simple)Type>'
    match = re.search(type_pattern, xsd_content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(0)

    return None


def extract_schema_definition(element_name: str, standard: str = "NeTEx") -> Optional[str]:
    """
    Extract XSD schema definition for an element name from local XSD files.

    Args:
        element_name: XML element name (e.g., "DepartureTime", "Journey")
        standard: Standard name ("NeTEx", "SIRI", "OpRa")

    Returns:
        XSD definition snippet, or None if not found
    """
    xsd_paths = STANDARD_XSD_MAP.get(standard)
    if not xsd_paths:
        logger.warning(f"Standard {standard} not configured for XSD extraction")
        return None

    # Try each schema file for the standard
    for schema_name, file_path in xsd_paths.items():
        logger.debug(f"Searching {schema_name} ({file_path}) for {element_name}")
        xsd_content = _read_xsd_file(file_path)
        if not xsd_content:
            logger.debug(f"Could not read XSD file: {file_path}")
            continue

        definition = _find_element_in_xsd(xsd_content, element_name)
        if definition:
            logger.info(f"Found {element_name} in {schema_name}")
            return definition

    logger.debug(f"Element {element_name} not found in any {standard} XSD schema")
    return None


def format_schema_definition_as_chunk(element_name: str, definition: str, standard: str = "NeTEx") -> dict:
    """
    Format an XSD definition as a searchable chunk.

    Creates a chunk with metadata linking back to the XSD source.
    """
    # Clean up the definition
    definition_clean = definition.strip()

    # Truncate if too long
    if len(definition_clean) > 2000:
        definition_clean = definition_clean[:2000] + "\n... [truncated]"

    chunk_id_str = f"xsd-def-{element_name.lower()}"
    chunk_id_int = hash(chunk_id_str) % (10 ** 8)

    chunk_text = f"""
XSD SCHEMA DEFINITION: {element_name}
Standard: {standard}
Element: {element_name}

Definition:
{definition_clean}
"""

    # Map standards to their GitHub repository URLs
    repo_urls = {
        "NeTEx": "https://github.com/TransmodelEcosystem/NeTEx",
        "SIRI": "https://github.com/TransmodelEcosystem/SIRI",
        "OpRa": "https://github.com/TransmodelEcosystem/OpRa",
    }

    repo_url = repo_urls.get(standard, "https://github.com/TransmodelEcosystem/NeTEx")

    return {
        "id": chunk_id_int,
        "chunkId": chunk_id_str,
        "chunk_id": chunk_id_str,
        "retrievalEventId": f"xsd-{chunk_id_int}",
        "label": f"XSD Definition: {element_name}",
        "text": chunk_text.strip(),
        "doc_type": "xsd-definition",
        "quality_score": 0.96,  # High quality - direct from XSD
        "standards_scope": [standard],
        "match_type": "schema_definition",
        "similarity_reason": f"XSD schema definition for {element_name} element",
        "repositoryUrl": repo_url,
        "repository_url": repo_url,
        "commitSha": "master",
        "commit_sha": "master",
        "sourcePath": "xsd/netex_framework/",
        "source_path": "xsd/netex_framework/",
        "embedding_vector": None,
        "heading": f"{element_name} - {standard} XSD Definition",
    }


def retrieve_schema_definitions_for_concepts(concept_names: list[str], standard: str = "NeTEx") -> list[dict]:
    """
    Retrieve XSD schema definitions for multiple concept names.

    Args:
        concept_names: List of element names (e.g., ["DepartureTime", "Journey"])
        standard: Standard name

    Returns:
        List of chunks with schema definitions
    """
    chunks = []

    for concept_name in concept_names:
        logger.debug(f"Retrieving schema definition for {concept_name}")
        definition = extract_schema_definition(concept_name, standard)

        if definition:
            chunk = format_schema_definition_as_chunk(concept_name, definition, standard)
            chunks.append(chunk)
            logger.info(f"Created XSD definition chunk for {concept_name}")
        else:
            logger.debug(f"No XSD definition found for {concept_name}")

    return chunks


if __name__ == "__main__":
    # Test extraction
    test_elements = ["DepartureTime", "ArrivalTime", "Journey", "Stop"]

    for element in test_elements:
        print(f"\nExtracting: {element}")
        definition = extract_schema_definition(element)
        if definition:
            chunk = format_schema_definition_as_chunk(element, definition)
            print(f"  ✅ Found ({len(definition)} chars)")
            print(f"  Chunk ID: {chunk['chunkId']}")
            print(f"  Text preview: {chunk['text'][:100]}...")
        else:
            print(f"  ❌ Not found")
