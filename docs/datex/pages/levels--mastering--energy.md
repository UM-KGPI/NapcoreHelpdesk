url: https://docs.datex2.eu/v3.7/levels/mastering/energy/
title: EnergyInfrastructure

## EnergyInfrastructure
(uses the «D2Namespace» Facilities)
### Energy Infrastructure
The DATEX model in this namespace specifies details of infrastructure for vehicle energy supply. The provided data model is separated into two publications:
- EnergyInfrastructureTablePublication for static, i.e. low frequently updated information
- and EnergyInfrastructureStatusPublication for dynamic, i.e. high frequently updated information.
The static part covers all relevant information on vehicle energy infrastructure, e.g. sites, stations and refill points for electric vehicles as well as petrol, gasoline or gas-based/hydrogen refuelling for vehicles. In terms of dynamic information, the availability of the infrastructure, possible faults and a price indication are covered.
Three core elements define the model:
- «D2Class» "EnergyInfrastructureSite" represents an energy infrastructure site, i.e. a site where vehicles can refill energy. It is described by a number of properties and parameters like for example its included energy infrastructure stations, operation hours or its location.
- «D2Class» "EnergyInfrastructureStation" represents an energy infrastructure station that is located on an energy infrastructure site. The station is the location on the site where the refilling can be carried out. For fuels, it usually offers different kinds of petrol (super, regular) and diesel. For electro mobility, it may offer different kind of connectors. Furthermore, it may offer options for the client to pay for the product (energy) they refilled.
- «D2Class» "RefillPoint" represents a refill point that is part of an energy infrastructure station. A refill point is defined by its ability to charge one vehicle at a time by establishing a connection between the station and the vehicle. In most cases, a refill point is specialised to only be able to provide one kind of energy.
These three classes are each a specialisation of a 'Facility' (see separate documentation). This implies, that these classes inherit a number of facility properties, like being versioned identifiable, operating hours, rates, URLs, information about operator and owner and more.
### EnergyInfrastructureTablePublication
The basic hierarchal structure for this publication is (Table) – Site – Station – RefillPoint.
Note that the three elements are all specialisations of Facility, which means all standard description elements like rates, location, operating hours etc. are available at each level. The following figure is an structural view only, attributes and further relations are not shown:
The model in more detail looks like this:
A RefillPoint can be specified in a couple of manners to describe infrastructure for all non-electric energy sources:
In addition, a RefillPoint can be specified as an ElectricChargingPoint – see next figure. This allows the specification of a couple of very specific electric details, and also the information about energy-mixes that are sold.
For the Rates class (which comes from the Facilities namespace), a specific EnergyPricingPolicy class was added to have access on specific features in terms of Energy. Note that, as stated above, the Rates class is also available for each out of EnergyInfrastructureStation, EnergyInfrastructureSite and RefillPoint (/ElectricChargingPoint), i.e. the hierarchy level where to define prices can be chosen quite individually.
The 'Connector' class provides information on the connector used at an electric charging point, such as the charging interface and information on the cable.
Some literals of the following elements make use of termonology from the denoted standards:
- ChargingModeEnum
- IEC 61851-1 Electric vehicle conductive charging system - Part 1: General requirements
- VehicleToGridCommunicationTypeEnum
- EN ISO 15118-1 Road vehicles - Vehicle to grid communication interface - Part 1: General information and use-case definition
- IEC TS 61980-2 Electric vehicle wireless power transfer (WPT) systems - Part 2: Specific requirements for communication between electric road vehicle (EV) and infrastructure
- ConnectorTypeEnum
- IEC 60309-2:1999/AMD2 Amendment 2 - Plugs, socket-outlets and couplers for industrial purposes - Part 2: Dimensional interchangeability requirements for pin and contact-tube accessories
- IEC 62196-1 Plugs, socket-outlets, vehicle connectors and vehicle inlets - Conductive charging of electric vehicles - Part 1: General requirements
- EN 17186:2019 Identification of vehicles and infrastructures compatibility - Graphical expression for consumer information on EV power supply
The 'VehicleSpace' class provides information about an adjacent space for a single vehicle, usually direct linked with the electric charging station. It may be specified to allow parking after charging. As a VehicleSpace class inherits all the properties from a Facility, the space can be described by using all the common facility features, such as location, dimension and many others. Only data that overrides that of the ElectricChargingPoint itself should be populated.
The 'ElectricEnergyMix' and 'ElectricEnergySourceRatio' can specify a certain energy source mix that is available at the specified electric charging point. The different types of sources can be combined with a percentage ratio. All specified ratios should sum up to 100%. Further information on green energy, carbon dioxide or nuclear waste impact can be given. Each electric energy source mix can be combined with an energy provider and with specific rates, both by using classes from the Facilities namespace.
The 'EnergyPricingPolicy' class adds some additional pricing policy information to the Rates class from the Facilities namespace. It can be used to specify a discount or a combination with parking fees. Minimum or maximum delivery fees can also be specified there.
### EnergyInfrastructureStatusPublication
Finally, the dynamic status publication allows to give status information on all levels or to redefine operating hours, rates, etc.
Note once again, that the site status, the station status and the refill point status all are specialisations of the FacilityStatus class, that provides some standard properties regarding the status.
### Annex: Structural view on classes and namespaces
This figure shows an abstracted view on the structure of classes for the EnergyInfrastructure (yellow) and the Facilities (green) namespaces. Note that not all classes are denoted here.
Go back to the previous page
