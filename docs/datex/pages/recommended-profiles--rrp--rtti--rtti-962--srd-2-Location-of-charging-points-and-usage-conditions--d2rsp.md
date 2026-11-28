url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-962/srd-2-Location-of-charging-points-and-usage-conditions/d2rsp/
title: The DATEX II Recommended Service Profiles

## The DATEX II Recommended Service Profiles
In order to support the implementing data sources with adequate dataprofiles DATEX II creates so called Recommended Reference profiles, containing the minimum relevant information-elements fulfilling the requirements of the delegated Regulations.
Further information on DATEX II Recommended profiles can be found here:
Recommended profiles
As the IDACS community has gone one step deeper and created consensus about European information profile, the resulting Recommended Service Profiles have been created as well. This paragraph contains the references to the DATEX II website where the additional information can be found for these profiles.
Further information on DATEX II Recommended Service Profiles can be found here:
Recommended Service Profiles
### Extending an RSP with national mandatory elements
#### Selecting additional attributes available in DATEX II
The IDACs recommended service profiles contain only those information elements that are identified as mandatory by the IDACs project. However, the DATEX II datamodel has many more attributes available (comparable to the OCPI standard). If for some reason an Operator wants (or has to) provide additional data-elements, this can be done by extending the RSP. How this is done can be found here:
Profiling guide. Especially the webinar video on youtube is very informative on how to do this.
#### Extending the DATEX II energy publication with local additions
In the situation where additional information elements are required that are not (yet) in the DATEX II EnergyInfrastructure publication, it is possible to extend the model. It is recommended to consult a known DATEX II expert, or the DATEX II helpdesk if this is required. For those that are willing to become an expert please check out the support section on this topic on the DATEX II documentation portal;
Extension introduction
And for more advanced extensions:
Extension guide
### The IDACS RSP's
The IDACS Service profiles have the datastructure as described in the next paragraphs.
### Generic topstructure
Each energystation has a similar datastructure with regard to the common elements.
At the level of refillpoint the differences per type of energy and fuel emerge.
The generic structure is
All energy type provisions have the same structure for EnergyInfrastructureSite: the grand overarching structure of a refueling/charging site.
Every Site has one or more EnergyInfrastructureStations
And every station has one or more RefillPoints.
The facility characteristics of the a site, station and point have all the same structure. This holds for the location, the address, the operator, owner and operating hours.
This way it is possible to reflect the situation where different actors are responsible for different services in an infrastructure site.
This structure also enables the datasource to bring information about operators, operating hours, locations, tariffs etc. that are identical for all refillpoints or EnergyInfrastructure Stations within a Site to the overarching structure, avoiding the replication of data. It is recommended to put the information as high as possible in the order of site – station – point.
If differentiations exist on a lower level, the higher levels shall not contain those information elements at all.
In the next paragraphs the specifics of the different kinds of refillpoints are specified.
Below you find a set of examples of the real world objects mapped to the DATEX II datastructure.
A EnergyInfrastructuresite with multiple Energy Infrastructure Stations
Energy infrastructure site with 5 Energy Infrastructure Stations:
2 stations in the front, each having 1 refillpoint of type ElectricChargingPoint (in the front), with 2 different connectors
3 stations in the back, each having multiple refillpoints of different fuelling (in the back)
An Energy Infrastructure Station with several RefillPoints of different nature
A Hydrogen refill point as a standalone Energy Infrastructure station
An Energy Infrastructure Station with refill points of different nature: Hydrogen, Petrol and Diesel
### EV charging service profiles
#### Infrastructure
The datamodel for the EV ChargingInfrastructure is a specialization of the refillpoint as shown in the diagram in paragraph 6.3, documenting the generic datastructure.
#### Actual availability status
The actual availability status of the EV-Charging infrastructure is published as a DATEX II EnergyInfrastructureStatus publication. This publication carries the following information elements as shown in the UML diagram below.
### Alternative fuels service profiles
#### Infrastructure
The datamodel for Alternative fuels refueling Infrastructure is a specialization of the refillpoint as shown in the diagram in paragraph 6.3, documenting the generic datastructure.
Depending on the type of fuel (petrol or organic gas) the specialization of the refillpoint is determined.
#### Actual availability status
Not in scope of IDACS
### Hydrogen
#### Infrastructure
The datamodel for the Hydrogen Refueling infrastructue is a specialization of the refillpoint as shown in the diagram in paragraph 6.3, documenting the generic datastructure.
#### Actual availability status
Not in scope of IDACS
Go back to the previous page
