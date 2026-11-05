url: https://docs.datex2.eu/v3.7/levels/mastering/trafficregulation/
title: Traffic Regulation

## Traffic Regulation
### The Traffic Regulation model
The Traffic Regulation model provides a structure for publishing machine interpretable traffic regulations while reusing existing classes and datatypes from the DATEX II Common and LocationReferencing namespaces (see Figure 1).
The video below describes the concept of the Traffic Regulation model, even though the model has been changed since.
#### Traffic Regulation namespace dependencies
Figure 1 – Traffic Regulation Namespace relations and dependencies
#### Traffic Regulation model package structure
The traffic regulation model is divided into packages as shown in Figure 2.
Figure 2 – Traffic Regulation model package structure
### The "TrafficRegulationPublication" package
Figure 3 – "TrafficRegulationPublication" class diagram
This is the top-level package of the "Traffic Regulation" model and contains the "TrafficRegulationPublication" class, which is a specialisation of the "PayloadPublication" class and hence forms the top of the hierarchy of the traffic regulation publication sub-model.
A "TrafficRegulationPublication" may be composed of one of the following four classes specifying different ways of publishing traffic regulations:
"TrafficRegulationsFromCompetentAuthorities": Traffic regulations that are issued by a competent authority.
"TrafficRegulationsByAuthorisedActors": Traffic regulations from an actor that has received a general permission from a competent authority.
"AdHocTrafficRegulations": Traffic regulations implemented by road operators without formal order due to urgent safety requirements.
"PlannedDynamicTrafficRegulations": Traffic regulations, often dynamically changeable, implemented by means of an automated or controllable technical system.
### The "TrafficRegulationOrder" package
This package contains models for the different ways of publishing traffic regulations (as described above).
#### Traffic Regulations by Authorised Actors and Ad Hoc Traffic Regulations
The class "TrafficRegulationsByAuthorisedActors" (see Figure 4) defines traffic regulations that may be implemented by authorised actors in urgent or safety-relevant situations. These actors are authorised by a traffic regulation order to implement traffic regulations without exact specification of when they are activated or deactivated. An "ActivatedRegulation" contains one or more implemented traffic regulations.
The "AdHocTrafficRegulations" (see Figure 5) class is a container for traffic regulations that are implemented by an actor that has received a general permission to implement traffic regulations in urgent, safety related situations (e.g. a road operator in case of road damage requiring urgent response). An "AdHocTrafficRegulation" contains one or more traffic regulations.
Figure 4 – "AdHocTrafficRegulations" class diagram
#### Planned Dynamic Traffic Regulations
Planned dynamic traffic regulations are often dynamically changeable and implemented by means of an automated or controllable technical system.
The "PlannedDynamicTrafficRegulations" class (see Figure 5) is a container for "PlannedDynamicTrafficRegulation" instances, which is either an "AutomatedTrafficManagement" or a "TrafficSignal". The latter is a hook to CEN EN 16157-9. An "AutomatedTrafficManagement" class instance may be composed of traffic regulations.
Figure 5 – "PlannedDynamicTrafficRegulations" class diagram
#### Traffic Regulations from Competent Authorities
Traffic regulations from competent authorities (see Figure 6) are published through a traffic regulation order. Therefore, the class "TrafficRegulationsFromCompetentAuthorities" is composed of one or more "TrafficRegulationOrder" instances. Each traffic regulation order may be composed of the following elements:
An optional "LegalBasis" defined by name, version, and date of the legal document.
An optional "implementedLocation" and/or "locationByOrder" defining the overall location of the traffic regulations contained in the traffic regulation order.
An optional "implementedValidity" and/or "validityByOrder\ " defining the overall time validity of the traffic regulations contained in the traffic regulation order.
One or more "TrafficRegulation\ " instances defining the regulations that are issued via the traffic regulation order, which are described in detail in the following.
Figure 6 - "TrafficRegulationsFromCompetentAuthorities" class diagram
### The "TrafficRegulation" package
A "TrafficRegulation" (see Figure 7) is composed of the following elements:
One or more "TypeOfRegulation" instances defining the regulations that apply (see section "The "TypeOfRegulation" package").
A set of conditions under which the traffic regulation applies defined by the Condition model (see Figure 8).
The corresponding road sign of the traffic regulation.
Information on available permits that exempts the permit owner from the traffic regulation.
Figure 7 - "TrafficRegulation" class diagram
The "Condition" model (see Figure 8) offers to define an arbitrarily complex set of bitwise operations using the operators and, or, xor and not. The abstract "Condition" class can be specialised in one of the following ways:
"ConditionDueToExternalRegulation",
"RoadCondition",
"OccupantCondition",
"DriverCondition",
"AccessCondition",
"LocationCondition",
"ValidityCondition",
"VehicleCondition",
"NonVehicularRoadUserCondition",
"RequiredPermitCondition",
as well as the "ConditionSet" class, which can be used to specify a combination of conditions. Besides the here listed classes, additional specializations of the "Condition" class are added in the "ControlledZone" model that are only relevant for defining conditions for controlled zones. Each "ConditionSet" contains a collection of "Condition" specialisations and an operator, which connects the conditions. A "Condition" can also be negated by setting the "negate" attribute to "true", which means that the condition is exempted.
Figure 8 - "Condition" class diagram
### The "TypeOfRegulation" package
Figure 9 shows the above mentioned "TypeOfRegulation" model, which specifies different types of traffic regulations. The abstract class may be instantiated by the following classes:
"Warning": see section "The "Warning" package"
"OvertakingBan": an overtaking ban
"RushHourLaneRestriction": restriction of the rush hour lane (e.g. clear rush hour lane)
"MinimumDistanceRestriction": specification of a minimum distance between two vehicles
"DirectionRestriction": restriction of the direction in which the vehicle may travel and information on who to respect when following the specified direction
"AccessRestriction": access restrictions
"SpeedLimit": speed limits (e.g. maximum speed)
"AlternateRoadOrCarriagewayOrLaneLayout": specification of alternate layouts for roads, carriageways or lanes (e.g. deviation to hard shoulder)
"StandingOrParkingRestriction": standing and or parking restrictions (e.g. no standing for more than two minutes)
"PriorityRule": different priority rules (e.g. give way to oncoming vehicle, priority at next junction)
"MandatoryRoadOrCarriagewayOrLaneUsage": mandatory roads or carriageways or lanes (e.g. mandatory bus road or carriageway or lane)
"Rerouting": specification of rerouting
Figure 9 –"TypeOfRegulation" class diagram
### The "Warning" package
The "Warning" package (see Figure 10) specifies four different types of warnings. The abstract class shall be instantiated by one of the following classes:
"TrafficAhead": warnings for traffic ahead (e.g. traffic queues)
"SteepHill": steep hill warnings
"RoadWarning": warnings concerning the road or condition or the road (e.g. road narrows both sides, slippery road)
"AmbientWarning": warnings about ambient factors (e.g. falling rocks)
Figure 10 – "Warning" class diagram
Go back to the previous page
