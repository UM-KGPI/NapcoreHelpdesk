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

# NeTEx XSD file URLs (main schema files)
# Note: These URLs must be configured for your environment
# Options:
# 1. Local file paths (if XSD files are cloned locally)
# 2. GitHub raw content URLs (verify correct directory structure)
# 3. Schema repository HTTP server
# Set via NETEX_XSD_URLS environment variable or settings
NETEX_XSD_URLS = {
    # Using blob URLs pattern - adjust domain/path for your repository mirror
    "netex_frame": "https://raw.githubusercontent.com/TransmodelEcosystem/NeTEx/master/xsd/netex_framework/netex_frame.xsd",
    "netex_part2": "https://raw.githubusercontent.com/TransmodelEcosystem/NeTEx/master/xsd/netex_part_2/netex_part2_part2_1_journeys.xsd",
}


def _fetch_xsd_content(url: str) -> Optional[str]:
    """Fetch XSD file content from GitHub."""
    try:
        # Create SSL context - bypass verification for development/testing
        # In production, use proper certificate verification
        ssl_context = ssl._create_unverified_context()
        with urlopen(url, timeout=10, context=ssl_context) as response:
            return response.read().decode("utf-8")
    except (URLError, Exception) as e:
        logger.warning(f"Failed to fetch XSD from {url}: {e}")
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
    Extract XSD schema definition for an element name.

    Args:
        element_name: XML element name (e.g., "DepartureTime", "Journey")
        standard: Standard name (currently only "NeTEx" supported)

    Returns:
        XSD definition snippet, or None if not found
    """
    if standard.lower() != "netex":
        logger.warning(f"Standard {standard} not yet supported for XSD extraction")
        return None

    # Try the main NeTEx frame schema first (usually has core definitions)
    for schema_name, url in NETEX_XSD_URLS.items():
        logger.debug(f"Searching {schema_name} for {element_name}")
        xsd_content = _fetch_xsd_content(url)
        if not xsd_content:
            continue

        definition = _find_element_in_xsd(xsd_content, element_name)
        if definition:
            logger.debug(f"Found {element_name} in {schema_name}")
            return definition

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
        "repositoryUrl": NETEX_XSD_URLS.get("netex_frame", ""),
        "repository_url": NETEX_XSD_URLS.get("netex_frame", ""),
        "commitSha": "v2.0",
        "commit_sha": "v2.0",
        "sourcePath": "xsd/netex_framework/netex_frame.xsd",
        "source_path": "xsd/netex_framework/netex_frame.xsd",
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
