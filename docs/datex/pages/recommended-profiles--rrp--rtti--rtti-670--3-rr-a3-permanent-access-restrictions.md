url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-670/3-rr-a3-permanent-access-restrictions/
title: DATEX&nbsp;II packages addressed by the RRP Other types of data on regulations and restrictions

## DATEX II packages addressed by the RRP Other types of data on regulations and restrictions
### The location and identification of traffic signs reflecting traffic regulations and identifying dangers
#### Permanent access restrictions
This section outlines the minimum information required for identifying the geographic location and disseminating the details of permanent access restrictions applied to road segments, including those on bridges, tunnels, or other infrastructure. These restrictions are legal or physical limitations on vehicle access that do not change over time (i.e., they are static, as opposed to event- or condition-based restrictions).
#### Scope
Permanent access restrictions refer to rules that continuously prevent certain types of vehicles or traffic from entering or using a specific road link, infrastructure element, or zone. Such restrictions may result from safety concerns, infrastructure limitations, environmental regulations, or urban planning strategies.
Typical examples include:
- Vehicle type prohibitions (e.g., HGVs, buses, hazardous materials, agricultural vehicles)
- Size and dimension limitations:
- Maximum height
- Maximum width
- Maximum length
- Weight-based restrictions:
- Total gross weight
- Axle load limits
- Fuel or propulsion type restrictions (e.g., banning diesel vehicles in low-emission zones)
- Restricted access zones (e.g., residential zones, environmental zones, pedestrian-only streets)
- Prohibited entry based on registration category or emissions class
#### Location Encoding
The restricted area must be precisely referenced using:
- Point location (e.g., a single entry point),
- Linear location (e.g., a restricted road segment),
- Zonal boundaries (e.g., an entire urban low-emission zone), with directionality included where applicable.
#### Minimum Information Package
To enable accurate and interoperable dissemination of permanent access restrictions, the following data elements are required:
- Exact location of the restriction:
- Point, segment, or zone (with boundaries)
- Direction of restriction (if applicable)
- Type of restriction:
- Vehicle type
- Vehicle characteristics (weight, dimensions)
- Propulsion or fuel type
- Applicability:
- Affected vehicle categories
- Lane-specific or general
- Legal basis or reference to the issuing authority
- Time validity: Permanently active (indication of permanency)
- Entrance/exit locations, if the restriction applies to a bounded area (e.g., environmental zone)
#### Standards and Interoperability
Permanent access restrictions should be represented in compliance with relevant European standards, including:
- TN-ITS (CEN/TS 17268) – for structured transport network data exchange;
- INSPIRE Transport Networks – for spatial and location referencing;
- DATEX II Traffic Regulation Extension – for modelling traffic rules dynamically or statically;
- ETSI Technical Specification 102 894-2 v2.3.1.
Go back to the previous page
