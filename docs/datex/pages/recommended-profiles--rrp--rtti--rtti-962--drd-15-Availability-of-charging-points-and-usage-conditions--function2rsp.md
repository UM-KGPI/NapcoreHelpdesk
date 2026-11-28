url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-962/drd-15-Availability-of-charging-points-and-usage-conditions/function2rsp/
title: Functional mapping of IDACS datarequirements to DATEX II RSPs

## Functional mapping of IDACS datarequirements to DATEX II RSPs
The Generic components of the different alternative fueltypes are all the same. Therefore there is one specific mapping to DATEX II available, where only the energy source specifics are a variation.
The entire mapping is provided in the Annex 1 of this document.
### EV charging stations
#### EV charging stations infrastructure
The following information elements are defined as the minimum dataset to be provided
- Location:
- GNSS
- Address (street name, zip code, city,…).
- List of available charge-solutions (Power, Modes);
- List of available connectors (plugs, sockets, induction plate...);
- Opening hours, identification and payment methods;
- Contact info for owner/operator;
- Full e-mobility code of the charging point (outlet).
The details of this dataset and how they map to OCPI and DATEX II are provided in Annex 1
#### EV charging stations actual status
The following information elements are part of the dynamic availability
- Availability (if the station is operational/ non-operational);
- Occupation status (free, occupied);
- Price for ad-hoc charging.
The details of this dataset and how they map to OCPI and DATEX II are included in in Annex 2
### Alternative fuels
#### Static Data [static-data-1]
In the Grant Agreement, for Other fuels only the exchange of static data is mentioned. There is no focus on dynamic data (e.g. operational status or fuel availability), because of technical difficulties with sharing these data and because fuel availability is not a problem for other fuels.
To achieve the project goal, it is important that there is harmonisation between the data elements that are exchanged for electricity, hydrogen and other fuels. Therefore, the list of static data elements for electricity was used as a base for the data elements for other fuels. All participating countries agreed on sharing the data elements in figure XX. Countries are allowed to add extra data categories, but at this moment none of the participants has plans to add dynamic data.
description
Static Data
Gas station owner name | Name of the company that owns the gas station
Fuel type | Type of fuel, when applicable percentage of bio component
Fuel Station Latitude | Latitude on the exact location of the station. Should be in WGS84 decimal standard.
Fuel Station Longitude | Longitude on the exact location of the station. Should be in WGS84 decimal standard.
Fuel station address | Street Name where the station l is located. If available, as not all locations have Street Names.
Postal Code + Addition (if used) | Postal Code where the fuel station is located. This should be the main Postal Code + addition (if used) and can include alpha/digit characters.
City/Location | The City/Town/Location where the fuel station is located.
Country | Country where the fuel station is located. This should be the ISO 31661 Alpha-2 Country Codes.
Opening Time | The time periods when a fuel station is open to the public. This could indicate the availability of a public charging station, but also indicate the times or days that a private station becomes a public station. This is a complex type of data as it will include several different components to define the times when the fuel station can be used.
Timezone | Timezone where the fuel station resides. This is used to make sure that the availability is shown correctly and also to make reservation possible in the future.
Payment and identification methods | available identification and payment methods described as a list
### H2 refueling stations
#### H2 refueling stations infrastructure
#### Location (GNSS coordinates/ street name)
Data on the location has to be collected in two different ways: as GNSS coordinates and street name. As streets may cover long distances, occur numerous times in the same city or in different cities, the consortium opts for indicating a house number, postal code, town and country in order to get an unambiguous address. Therefore, the following definitions apply:
‘GNSS coordinates’ means the geographical location of the driveway to a hydrogen refuelling point accessible to the public determined by a Global Navigation Satellite System (GNSS) consisting of a constellation of satellites and a global network of ground stations;
‘Street name’ means the address of a hydrogen refuelling point accessible to the public consisting of a street name and, if applicable, a house number, postal code, city, country and additional information
#### Opening hours
‘Opening hours’ means the period in which a hydrogen refuelling point is accessible to the public
#### Identification and payment methods
‘Identification and payment methods’ means the way with which users identify themselves and the methods with which they can pay for the gaseous hydrogen dispensed as fuel on board motor vehicles
#### Contact info for owner/operator
‘Contact info for owner/operator’ means a valid phone number at which the operator of a refuelling point dispensing gaseous hydrogen used as fuel on board motor vehicles can be contacted
#### H2 refueling stations actual status
#### Operational Status
‘Operational status’1 means a status signalling whether dispensing gaseous hydrogen used as fuel on board motor vehicles at a refuelling point is possible
The following minimum statuses shall be displayed:
- “Available”: dispensing gaseous hydrogen at the refuelling point is possible without restrictions
- “Not available”: dispensing gaseous hydrogen at the refuelling point is not possible
- “Outside opening hours”: dispensing gaseous hydrogen at the refuelling point is not possible as the refuelling point is currently not accessible to the public
- “No information”: there is no information available as to whether dispensing gaseous hydrogen at the refuelling point is possible without restrictions
The operational status of refuelling points dispensing gaseous hydrogen shall be refreshed every 300 seconds as a minimum. A time of 300 seconds is chosen as that is average time it takes to refuel a FCEV and malfunctions occur mostly as a result of wrong handling of the dispenser and associated hardware during the refuelling process. Operators of refuelling points dispensing gaseous hydrogen may choose different symbols in order to illustrate these statuses.
#### Additional information
‘Additional information’ means any information not covered in data categories a) to e)
Apart from the data categories that are to be collected mandatorily as part of IDACS, certain other categories could be useful to the end consumer. For example, other data categories could include:
- The amount of hydrogen left in the station (once progress to a mass market is made)
- Current prices for hydrogen in Euros per kg
- Share of green hydrogen (e.g. according to the CertifHy scheme)
- Images of the station
- Origin of funding
- Refuelling manuals (video training)
- Payment and billing information
- General information on hydrogen
The consortium opts not to make the display of such criteria mandatory as part of IDACS, especially as new data categories entail higher costs and maintenance efforts. However, the consortium may find value added in defining these categories at the end of deliverable 2.2.2. even as many of these will be relevant in a future mass market only.
This category should not be mistaken with “availability” in the sense of real-time information on an occupational status, i.e. whether someone is refuelling their car there. ↩
Go back to the previous page
