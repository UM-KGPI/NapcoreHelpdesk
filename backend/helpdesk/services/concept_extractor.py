"""
Extract domain-specific concepts from questions for improved semantic retrieval.

Identifies XML element names, properties, classes, and standards so retrieval can
search for them explicitly rather than relying only on natural language similarity.

Example:
  Input: "How is a journey departure time represented in NeTEx XML?"
  Output: {
    "properties": ["departure time", "DepartureTime"],
    "classes": ["journey", "Journey"],
    "standards": ["NeTEx", "XML"],
    "intent": "representation"
  }
"""

import re
from typing import TypedDict


class ExtractedConcepts(TypedDict, total=False):
    """Extracted concepts from a question."""
    properties: list[str]
    classes: list[str]
    standards: list[str]
    intent: str


# Known NeTEx/transport properties (space-separated → CamelCase conversions)
PROPERTY_PATTERNS = {
    "departure time": "DepartureTime",
    "arrival time": "ArrivalTime",
    "wait time": "WaitTime",
    "run time": "RunTime",
    "dwell time": "DwellTime",
    "duration": "Duration",
    "frequency": "Frequency",
    "headway": "Headway",
    "interval": "Interval",
    "day type": "DayType",
    "service calendar": "ServiceCalendar",
    "vehicle journey": "VehicleJourney",
    "service journey": "ServiceJourney",
    "journey pattern": "JourneyPattern",
    "stop place": "StopPlace",
    "scheduled stop point": "ScheduledStopPoint",
    "timing point": "TimingPoint",
    "operating day": "OperatingDay",
    "operating period": "OperatingPeriod",
}

# Known NeTEx/transport classes
CLASS_PATTERNS = {
    "journey": "Journey",
    "journeys": "Journey",
    "service": "Service",
    "services": "Service",
    "route": "Route",
    "routes": "Route",
    "line": "Line",
    "lines": "Line",
    "stop": "Stop",
    "stops": "Stop",
    "timetable": "Timetable",
    "schedule": "Schedule",
    "trip": "Trip",
    "trips": "Trip",
}

# Standards and formats
STANDARD_PATTERNS = {
    "netex": "NeTEx",
    "siri": "SIRI",
    "opra": "OpRa",
    "gtfs": "GTFS",
    "ifopt": "IFOPT",
    "xml": "XML",
    "json": "JSON",
    "xsd": "XSD",
    "rdf": "RDF",
}

# Intent/action words that indicate what the question is about
INTENT_KEYWORDS = {
    "represent": "representation",
    "represented": "representation",
    "structure": "structure",
    "defined": "definition",
    "example": "example",
    "format": "format",
    "element": "element",
    "attribute": "attribute",
    "property": "property",
    "schema": "schema",
    "model": "model",
    "mapping": "mapping",
}


def _to_camel_case(text: str) -> str:
    """Convert space-separated or snake_case text to CamelCase."""
    # Split on spaces or underscores
    parts = re.split(r'[\s_-]+', text.lower())
    # Capitalize first letter of each part
    return ''.join(part.capitalize() for part in parts if part)


def extract_concepts(question: str) -> ExtractedConcepts:
    """
    Extract domain-specific concepts from a question.

    Returns dict with:
    - properties: Property names (both original and CamelCase)
    - classes: Class/entity names
    - standards: Standards and format names
    - intent: What the question is asking about (representation, example, etc.)
    """
    question_lower = question.lower()
    concepts: ExtractedConcepts = {
        "properties": [],
        "classes": [],
        "standards": [],
    }

    # Extract property terms
    for property_name, camel_case in PROPERTY_PATTERNS.items():
        if property_name in question_lower:
            concepts["properties"].append(property_name)
            if camel_case not in concepts["properties"]:
                concepts["properties"].append(camel_case)

    # Extract class terms
    for class_name, camel_case in CLASS_PATTERNS.items():
        if class_name in question_lower:
            concepts["classes"].append(class_name)
            if camel_case not in concepts["classes"]:
                concepts["classes"].append(camel_case)

    # Extract standards
    for standard, proper_case in STANDARD_PATTERNS.items():
        if standard in question_lower:
            concepts["standards"].append(proper_case)

    # Extract intent
    for keyword, intent in INTENT_KEYWORDS.items():
        if keyword in question_lower:
            concepts["intent"] = intent
            break

    return concepts


def build_enriched_query(question: str, base_query: str = "") -> str:
    """
    Build an enriched search query that includes extracted domain concepts.

    This helps semantic search find chunks about specific XML elements,
    properties, and structures rather than just natural-language similarity.

    Args:
        question: Original user question
        base_query: Base semantic query (if empty, use question as base)

    Returns:
        Enriched query combining natural language and domain concepts
    """
    if not base_query:
        base_query = question

    concepts = extract_concepts(question)

    # Build enriched query: original + specific technical terms
    enriched_parts = [base_query]

    if concepts.get("properties"):
        enriched_parts.append(" ".join(concepts["properties"]))

    if concepts.get("classes"):
        enriched_parts.append(" ".join(concepts["classes"]))

    if concepts.get("standards"):
        enriched_parts.append(" ".join(concepts["standards"]))

    if concepts.get("intent"):
        enriched_parts.append(concepts["intent"])

    enriched_query = " ".join(enriched_parts)
    return enriched_query


if __name__ == "__main__":
    # Test extraction
    test_questions = [
        "How is a journey departure time represented in NeTEx XML?",
        "What is the structure of a ServiceJourney?",
        "Show me examples of stop definitions in GTFS",
        "How do I model timetables in OpRa?",
    ]

    for q in test_questions:
        concepts = extract_concepts(q)
        enriched = build_enriched_query(q)
        print(f"\nQuestion: {q}")
        print(f"Concepts: {concepts}")
        print(f"Enriched: {enriched}")
