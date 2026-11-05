url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-670/3-rr-a1-access-conditions-for-tunnels/
title: DATEX&nbsp;II packages addressed by the RRP Other types of data on regulations and restrictions

## DATEX II packages addressed by the RRP Other types of data on regulations and restrictions
### The location and identification of traffic signs reflecting traffic regulations and identifying dangers
#### Access conditions for tunnels
This reference outlines the minimum information required for identifying the geographic location and disseminating the type and direction of traffic signs (or panels) that indicate traffic regulations or potential hazards within tunnels.
#### Scope
Traffic signs in tunnels are essential for conveying safety instructions, access conditions, and driving regulations to road users. These signs may refer to:
- Access conditions for tunnels: Legal or physical restrictions, such as prohibitions for certain vehicle categories (e.g., dangerous goods, height restrictions) or classifications based on tunnel categories;
- Permanent access restrictions: Such as structural limitations or legal prohibitions applying to specific tunnel links;
- Other traffic regulations: Including speed limits, mandatory or prohibited turns, and requirements regarding vehicle equipment (e.g., snow chains, audible signals).
#### Location Encoding
Tunnel-related traffic signs may be referenced using:
- A point location (e.g., tunnel entrance or a specific lane entry point),
- Or a linear location (e.g., when a sign applies to a stretch of tunnel road).
The applicable direction (e.g., inbound traffic, specific lanes) must be explicitly indicated.
#### Relevant Sign Types and Restrictions
In line with CEN/TS 17268 (TN-ITS model) and the ISO 14826 Graphic Data Dictionary (GDD), the following sign types are supported:
- Mandatory directions (e.g., compulsory turn, lane usage)
- Prohibited maneuvers or zones (e.g., no turns, no stopping)
- Vehicle equipment requirements (e.g., snow chains required)
- Vehicle restriction signs (e.g., max weight, length, height, or fuel type)
- Warning signs (e.g., sharp turns, slippery surface, smoke presence)
#### Minimum Information Package
The minimum data required for each tunnel-related traffic sign includes:
- Exact location (coordinates or road segment)
- Type of regulation or warning
- Applicable direction (e.g., traffic flow direction, lane number)
- Applicable vehicle categories (e.g., HGVs, gas-powered vehicles)
- Entry and exit points, especially for large or complex tunnel areas
- Time validity (e.g., permanent, time-based, weather-dependent)
#### Standards and Interoperability
The following standards ensure semantic and technical interoperability for tunnel sign information exchange:
- TN-ITS (CEN/TS 17268) – for structured transport network data exchange;
- ISO 14823 – for graphic symbol definitions of road signs;
- INSPIRE Transport Networks – for spatial and location referencing;
- DATEX II Traffic Regulation Extension – for modelling traffic rules dynamically or statically.
Go back to the previous page
