# OPRA Alignment Gap Report

Standard ontology: `opra.ttl`
Alignment file: `nits-opra-align.ttl`

| Metric | Count |
|--------|-------|
| Total classes in opra.ttl | 106 |
| Already aligned | 102 |
| **Unaligned (gap)** | **4** |

---

## Proposed additions by NITS category

> Copy the TTL block for a category into `nits-opra-align.ttl` after review.
> Delete or comment out lines you want to skip.

### Skip candidates (4 classes)

These are enumeration types, list containers, or abstract base classes.
They are typically not useful retrieval targets.
You may bulk-align them all as `nits:DataArtifact` or leave them unaligned.

```
opra:AbstractCtxIndicator  # Abstract base class — derives from parent alignment
opra:AbstractLogEntry  # Abstract base class — derives from parent alignment
opra:AbstractLoggableObject  # Abstract base class — derives from parent alignment
opra:TypeOfDelay  # Enumeration/classifier type — bulk-align or skip
```

---

## Full proposed TTL block (all non-skip classes)

```turtle
```

---

## Next steps

1. Review the proposed TTL block above
2. Copy approved lines into `nits-opra-align.ttl`
3. Bump `owl:versionInfo` in the alignment file
4. Run `make graphdb-load`
5. Re-run this command to confirm gap is closed
