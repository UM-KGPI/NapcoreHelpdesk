# Transmodel RDF/Turtle Ontology

## Overview

This document describes the **Transmodel v6.2 (2024)** ontology expressed in RDF/Turtle format. The ontology is derived directly from the Enterprise Architect (EA) model:

```
TransmodelEcoSystem2024-EAv16-nk84_OpRa-v13.qea
```

**Location**: [`standards/transmodel.ttl`](standards/transmodel.ttl)

---

## Coverage

### Transmodel Parts Included

| Part | Code | Title | Classes |
|------|------|-------|---------|
| Part 1 | CC | Common Concepts | ~180 |
| Part 2 | NT | Public Transport Network Topology | ~220 |
| Part 3 | TI | Timing Information & Vehicle Scheduling | ~180 |
| Part 4 | OM | Operations Monitoring & Control | ~160 |
| Part 5 | FM | Fare Management | ~180 |
| Part 6 | PI | Passenger Information | ~140 |
| Part 7 | DM | Driver Management | ~120 |
| Part 8 | MI | Management Information & Statistics | ~180 |
| Part 10 | NM | Alternative Modes | ~90 |

**Total**: **1,648 classes** from 477 packages

---

## File Structure

### Format
- **Format**: RDF/Turtle (.ttl)
- **Character Encoding**: UTF-8
- **Ontology Namespace**: `https://transmodel-cen.eu/6.2/`
- **Prefix**: `tm:`

### Prefix Declarations

```turtle
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix tm: <https://transmodel-cen.eu/6.2/> .
```

### Ontology Header

```turtle
tm:TransmodelOntology a owl:Ontology ;
  rdfs:label "Transmodel Core Ontology v6.2" ;
  rdfs:comment "Transmodel v6.2 (2024) - Parts 1-10" ;
  owl:versionInfo "6.2" .
```

### Class Definition Pattern

Each Transmodel class is represented as an OWL class:

```turtle
tm:ROUTE a owl:Class ;
  rdfs:label "ROUTE" ;
  rdfs:comment "A SCHEDULED STOP POINT SEQUENCE along which a public transport SERVICE is operated." .
```

- **Class IRI**: `tm:<CLASS_NAME>` (where CLASS_NAME is the sanitized Transmodel class name)
- **Label**: Original class name from EA model (preserved exactly)
- **Comment**: Class description from EA model's Note field

---

## Content Summary

### Statistics

| Metric | Count |
|--------|-------|
| Total Classes | 1,648 |
| Total Lines | 4,950 |
| File Size | 341 KB |
| Packages | 477 |
| Ontology Version | 6.2 |

### Sanitization Rules

Class names are converted to valid RDF identifiers using these rules:

1. Replace non-alphanumeric characters (except underscore) with underscores
2. Prefix with underscore if name starts with a digit
3. Preserve case (original names are UPPERCASE)

**Examples**:
- `ROUTE` → `tm:ROUTE`
- `TYPE OF SERVICE` → `tm:TYPE_OF_SERVICE`
- `3-CYCLE MAINTENANCE` → `tm:_3_CYCLE_MAINTENANCE`

---

## Related Artifacts

### Complementary Documents

| Artifact | Purpose | Location |
|----------|---------|----------|
| **Transmodel Glossary** | Two-column table of class names and descriptions | [`../transmodel-glossary.md`](../transmodel-glossary.md) |
| **NeTEx Ontology** | NeTEx (Network and Timetable Exchange) ontology | [`standards/netex.ttl`](standards/netex.ttl) |
| **SIRI Ontology** | Service Interface for Real-time Information | [`standards/siri.ttl`](standards/siri.ttl) |
| **OpRa Ontology** | Open Reservation API | [`standards/opra.ttl`](standards/opra.ttl) |
| **DATEX II Ontology** | Data Exchange for Traffic and Travel Information | [`standards/datex.ttl`](standards/datex.ttl) |
| **NAPCORE ITS Ontology** | Unified NAPCORE ITS ontology (integrates above) | [`napcore-its.ttl`](../napcore-its.ttl) |

---

## Integration with NAPCORE System

### Usage in the Helpdesk

The Transmodel ontology can be integrated into the NAPCORE FAQ helpdesk to:

1. **Semantic Grounding**: Map FAQ questions and answers to Transmodel entities
2. **Source Traceability**: Track which standard(s) define each concept
3. **Relationship Discovery**: Use RDF reasoners to find related classes and concepts
4. **Multi-Standard Alignment**: Link between Transmodel and other standards (NeTEx, SIRI, OpRa, DATEX II)

### Integration Steps

1. **Load into GraphDB**:
   ```bash
   make backend-index REPO_URL=... REPO_PATH=... PROFILE=transmodel
   ```

2. **Query with SPARQL**: Example query to find all classes in Part 1:
   ```sparql
  PREFIX tm: <https://transmodel-cen.eu/6.2/>
   PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
   
   SELECT ?class ?label ?comment
   WHERE {
     ?class a <http://www.w3.org/2002/07/owl#Class> ;
            rdfs:label ?label ;
            rdfs:comment ?comment .
    FILTER(STRSTARTS(STR(?class), "https://transmodel-cen.eu/6.2/"))
   }
   LIMIT 100
   ```

3. **Align with FAQ Content**: Tag FAQ entries with Transmodel class URIs for automatic linking

---

## Source Information

| Attribute | Value |
|-----------|-------|
| **Source Model** | TransmodelEcoSystem2024-EAv16-nk84_OpRa-v13.qea |
| **EA Tool Version** | EA v16 |
| **Transmodel Version** | 6.2 (2024) |
| **Generation Date** | 2026-05-05 |
| **Generation Tool** | Python 3 + sqlite3 |

---

## Validation

### RDF/Turtle Compliance

The ontology is valid RDF/Turtle and can be:

- **Parsed** with any RDF parser (Jena, RDF4J, RDFlib, etc.)
- **Loaded** into RDF triple stores (GraphDB, Virtuoso, Fuseki, etc.)
- **Queried** with SPARQL
- **Reasoned** with OWL 2 DL reasoners

### Validation Commands

```bash
# Validate with rapper (Raptor RDF tool)
rapper -g /path/to/transmodel.ttl

# Load into GraphDB via command-line
/opt/graphdb/bin/graphdb -Dgraphdb.home=/data import -i transmodel.ttl -r ttl
```

---

## Next Steps

1. **Load into GraphDB**: Import transmodel.ttl into the NAPCORE GraphDB repository
2. **Create SPARQL Views**: Build SPARQL queries to expose Transmodel concepts via REST API
3. **Semantic FAQ Indexing**: Index FAQ entries against Transmodel class URIs
4. **Cross-Standard Alignment**: Map corresponding classes between Transmodel, NeTEx, SIRI, etc.
5. **RAG Augmentation**: Use Transmodel ontology for context in RAG retrieval for FAQ generation

---

## References

- **Transmodel Official**: http://transmodel.org/
- **Transmodel EA Model**: CEN TC 278 WG 3 SG4 Repository
- **RDF/Turtle Specification**: https://www.w3.org/TR/turtle/
- **OWL 2 Specification**: https://www.w3.org/TR/owl2-overview/

---

**Last Updated**: 2026-05-05  
**Ontology Version**: 6.2  
**Maintainer**: NAPCORE Helpdesk Project
