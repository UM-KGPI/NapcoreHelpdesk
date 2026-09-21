# SIRI Alignment Gap Report

Standard ontology: `siri.ttl`
Alignment file: `nits-siri-align.ttl`

| Metric | Count |
|--------|-------|
| Total classes in siri.ttl | 310 |
| Already aligned | 297 |
| **Unaligned (gap)** | **13** |

---

## Proposed additions by NITS category

> Copy the TTL block for a category into `nits-siri-align.ttl` after review.
> Delete or comment out lines you want to skip.

### Skip candidates (13 classes)

These are enumeration types, list containers, or abstract base classes.
They are typically not useful retrieval targets.
You may bulk-align them all as `nits:DataArtifact` or leave them unaligned.

```
siri:AbstractDiscoveryDelivery  # Abstract base class — derives from parent alignment
siri:AbstractDiscoveryRequest  # Abstract base class — derives from parent alignment
siri:AbstractFunctionalServiceCapabilitiesRequest  # Abstract base class — derives from parent alignment
siri:AbstractFunctionalServiceCapabilitiesResponse  # Abstract base class — derives from parent alignment
siri:AbstractFunctionalServiceDelivery  # Abstract base class — derives from parent alignment
siri:AbstractFunctionalServiceRequest  # Abstract base class — derives from parent alignment
siri:AbstractFunctionalServiceSubscriptionRequest  # Abstract base class — derives from parent alignment
siri:AbstractRequest  # Abstract base class — derives from parent alignment
siri:AbstractResponse  # Abstract base class — derives from parent alignment
siri:AbstractServiceRequest  # Abstract base class — derives from parent alignment
siri:AbstractTrackedRequest  # Abstract base class — derives from parent alignment
siri:KeyList  # XSD list container — not a retrieval target
siri:TypeOfValue  # Enumeration/classifier type — bulk-align or skip
```

---

## Full proposed TTL block (all non-skip classes)

```turtle
```

---

## Next steps

1. Review the proposed TTL block above
2. Copy approved lines into `nits-siri-align.ttl`
3. Bump `owl:versionInfo` in the alignment file
4. Run `make graphdb-load`
5. Re-run this command to confirm gap is closed
