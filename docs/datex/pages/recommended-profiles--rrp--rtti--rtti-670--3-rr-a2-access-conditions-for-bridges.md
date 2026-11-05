url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-670/3-rr-a2-access-conditions-for-bridges/
title: DATEX&nbsp;II packages addressed by the RRP Other types of data on regulations and restrictions

## DATEX II packages addressed by the RRP Other types of data on regulations and restrictions
### The location and identification of traffic signs reflecting traffic regulations and identifying dangers
#### Access conditions for bridges
This section describes the minimum information required for identifying the geographic location and disseminating the type and direction of traffic signs or panels associated with bridges, especially those that reflect regulatory conditions, access restrictions, or potential hazards.
#### Scope
Traffic signs positioned on or near bridges are critical for ensuring road safety and infrastructure protection. These signs may represent:
- Access conditions for bridges: Legal or physical restrictions that prevent certain vehicles from entering or crossing a bridge. These may include:
- Weight limits (e.g., max gross weight, axle load)
- Height and width restrictions
- Vehicle type restrictions (e.g., prohibiting hazardous goods)
- Permanent access restrictions: Long-term regulations applying to certain vehicle classes, lanes, or directions on the bridge.
- Other traffic regulations: Including speed limits, overtaking prohibitions, one-way indications, or mandatory equipment (e.g., snow chains).
#### Location Encoding
Traffic sign data on bridges should specify the exact location using:
- Point-based location referencing (e.g., the start or end of a bridge, tolling points),
- Or linear referencing (e.g., across the full span of the bridge or between specified segments),
And should always include the applicable direction of travel (e.g., inbound, outbound, per lane).
#### Relevant Sign Types
According to the TN-ITS model (CEN/TS 17268) and ISO 14826 Graphic Data Dictionary (GDD), bridge-related signs may include:
- Maximum weight or axle load limits
- Height and width clearance signs
- Prohibited access for specific vehicle types (e.g., LPG, trucks, trailers)
- Speed limits applicable on bridges
- Prohibited or mandatory driving behavior (e.g., no overtaking, lane restrictions)
- Weather-dependent restrictions (e.g., during high winds or icing)
#### Minimum Information Package
For effective dissemination and interoperability, the following data elements should be provided for each bridge-related sign:
- Exact geographic location of the sign (point or segment)
- Type of restriction or warning (e.g., max height, prohibited goods)
- Applicable direction and lane number
- Vehicle categories affected (e.g., buses, HGVs, LPG vehicles)
- Time-based validity (permanent, scheduled, or condition-dependent)
- Entrance and exit references, where applicable (especially on long or multi-entry bridges)
#### Standards and Interoperability
Bridge sign data should conform to European standards for transport infrastructure information exchange:
- TN-ITS (CEN/TS 17268) – for structured transport network data exchange;
- ISO 14823 – for graphic symbol definitions of road signs;
- INSPIRE Transport Networks – for spatial and location referencing;
- DATEX II Traffic Regulation Extension – for modelling traffic rules dynamically or statically.
Go back to the previous page
