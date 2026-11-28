url: https://docs.datex2.eu/v3.7/user-guide/PayloadPublication/
title: PayloadPublication

## PayloadPublication
The payloadPublication package contains 4 namespaces. Situation is standardized as version 3.0 and described below. The other namespaces have a different status and can be found here.
### Situation and SituationPublication
A situation publication can group several situations.
Situation definition: An identifiable instance of a traffic/travel situation comprising one or more traffic/travel circumstances which are linked by one or more causal relationships. Each traffic/travel circumstance is represented by a Situation Record.
Warning
Each situation has a unique versioned identifier. This versioned identifier comprises a part established when the situation is first created in a DATEX II system database and kept within that system for all its life. The second part ("version") is established at every new version of the situation.
Such mechanism allows having several versions of the same situation in the same publication The situation severity on traffic can be indicated: "overallSeverity".
If this situation relates to another situation, its reference can be indicated: "relatedSituation" (this reference is the "versioned identifier" of the corresponding situation object).
With this publication, attributes can be given in the InformationHeader which provide clients with information management details (area of interest, confidentiality, urgency, information status) relating to this situation.
Note
Special case: when the Supplier sends SituationPublication to Clients in Operating Mode 1 "Publisher Push on occurrence", the situation management has to follow different rules.
#### Situation record
A situation may be composed of one or more situation records.
Situation record definition: An identifiable instance of a single record/element within a situation.
This class is abstract.
Each situation record has a unique versioned identifier. This first part of this identifier is established when the situation record is first created in the DATEX II system database. It is completed by a version part. The first part is kept within that system for all its life. The subsequent versions of this situation record must differ by their version part of the identifier. If the situation record is forwarded down a supply chain, each DATEX II system within that chain will assign its own unique identifier to the record when it first creates a corresponding record in its database, but the (compound) identifier created by the original supplier in the chain may optionally be forwarded in the record’s situationRecordCreationReference attribute.
In DATEX Version 3.0, the SituationRecord class and adds the attribute "safetyRelatedMessage" of type Boolean. This attribute indicates, whether the corresponding SituationRecord specifies a safety-related message according to the Commission Delegated Regulation (EU) No 886/2013 with regard to data and procedures for the provision, where possible, of road safety-related minimum universal traffic information free of charge to user. A subset of DATEX II elements, which should be used to meet the requirements of the delegated regulation, can be found in the document "Safety related message sets –Selection of DATEX II Codes, TPEG2-TEC-Causes and TMC-Events for EC high level Categories" from the ITS Directive Working Group.
It is located with one group of locations.
It can have one cause.
It can have one impact on the traffic (when the record type is "TrafficElement" or "OperatorAction"), qualified with:
- Indications on delays (code, value range, value)
- Other details (capacity remaining, effect on lanes, restriction type)..
Source information can be given (country, identifier, name, type, if reliable or not)
A situation record has a validity composed of:
- An validity status which defines if the record has an "active" or "suspended" status, or this status is defined according to periods of time,
- One mandatory global first start time "overallStartTime",
- One optional global real end time "overallEndTime",
- One or several validity periods, each having a start date and an end date, for which the situation record is active/valid, detailed with hours/days/weeks/months,
- One or several exception periods, each having a start date and an end date, for which the situation record is not active/valid, detailed with hours/days/weeks/months,
- The optional "overrunning" means the activity/action is still in progress, overrunning its planned duration as indicated in a previous version of the record.
Remarks for forecasts:
- When a record is created, with a start time in the future, it means it is a « forecast » and therefore for traffic elements, probabilityOfOccurrence should never have the value « certain ».
- When this start time arrives, the Supplier should update or end this information if it has not really occurred. If a supplier does not provide updated information at this time a client can not assume that the traffic element is now active, only that it was predicted to be active now.
There are 3 main categories of situation records:
- Traffic element: An event which is not planned by the traffic operator, which is affecting, or has the potential to affect traffic flow (note this does includes events planned by external organisations e.g. exhibitions, sports events etc.).
- Operator action: Actions that a traffic operator can decide to implement to prevent or help correct dangerous or poor driving conditions, including maintenance of the road infrastructure.
- Non-road event information: Information about an event which is not on the road, but which may influence the behaviour of drivers and hence the characteristics of the traffic flow.
These 3 categories are detailed in the following paragraphs.
#### TrafficElement
This class is abstract.
There are 6 kinds of traffic elements:
- Abnormal traffic,
- Activity
- Accident,
- Conditions
- Equipment or system fault,
- Obstruction,
Obstruction
Any stationary or moving obstacle of a physical nature (e.g. obstacles or vehicles from an earlier accident, shed loads on carriageway, rock fall, abnormal or dangerous loads, or animals etc.) which could disrupt or endanger traffic.
This class is abstract.
For each obstruction type, the number of obstructions can be given.
For each obstruction type, details can be given of:
- Mobility type: mobile/stationary,
There are 5 kinds of obstructions:
- Animal presence (alive or not, presence type)
- Environmental obstruction (depth, type),
- Infrastructure damage obstruction (type),
- General obstruction (type),
- Vehicle obstruction (type + individual vehicles characteristics)
- Abnormal traffic: A traffic condition which is not normal.
Details can be given: type, number of vehicles waiting, queue length, relative traffic flow, traffic flow characteristics, traffic trend type.
Accident
Accidents are events in which one or more vehicles lose control and do not recover. They include collisions between vehicle(s) or other road user(s), between vehicle(s) and any obstacle(s), or they result from a vehicle running off the road.
Details can be given:
- cause type,
- accident type,
- overview of people involved (number, injury status, involvement role, type),
- overview of vehicles involved per type (number, status, type, usage),
- details of involved vehicles (type + individual vehicle characteristics)
Equipment or system fault
Equipment or system which is faulty, malfunctioning or not in a fully operational state that may be of interest or concern to road operators and road users. The type of equipment or system and the type of fault must be given.
The type of equipment or system and the type of fault must be given.
Activities
Deliberate human actions external to the traffic stream or roadway which could disrupt traffic. Details must be given in term of: types of authority operations / disturbance / public event, and possibly in term of mobility(mobile/stationary).
Conditions
Any conditions which have the potential to degrade normal driving conditions. A general indicator can be given with 8 possible values "drivingConditionType":
- impossible,
- very hazardous,
- hazardous,
- passable with care,
- winter conditions (driving conditions are consistent with those expected in winter),
- normal,
- other,
- unknown.
There are 3 conditions categories:
- road surface conditions that are related to the weather which may affect the driving conditions, such as ice, snow or water,
- road surface conditions that are not related to the weather but which may affect driving conditions, such as mud, oil or loose chippings…,
- environment conditions which may be affecting the driving conditions without being directly linked to the road (precipitation, visibility, pollution, temperature, wind)
#### Operator action
For each operator action type, details can be given of:
- Origin: internal / external,
- Status: requested, approved, being implemented, implemented, rejected, termination requested, being terminated,
- Considered action plan
There are 4 kinds of operator actions:
- Roadworks,
- Sign setting,
- Network management,
- Roadside assistance.
Roadworks
Highway maintenance, installation and construction activities that may potentially affect traffic operations.
This class is abstract.
Details can be given of:
- duration,
- scale: major / medium / minor
- under traffic or not,
- urgent or not,
- mobility type: mobile / stationary,
- construction work type: blasting / construction / demolition, road improvement, road widening,
- road maintenance type (e.g. grass cutting, resurfacing, repair, road marking, salting…,
- subject type of works (e.g. bridge, crash barrier, gantry, road tunnel,…,
- information on associated maintenance vehicles
Network management
Changes to the configuration or usability of the road network whether by legal order or by operational decisions. It includes road and lane closures, weight and dimensional restrictions, speed limits, vehicle restrictions, contra-flows and rerouting operations.
There are 6 types of network management:
- Rerouting management (type, itinerary description, sign posted or not,…),
- Speed management (type, speed value),
- Road, carriageway or lane management (type, specified lane or carriageway, minimum number of persons in a vehicle required for HOV/car pool lane),
- Winter driving management (type),
- General instructions to road users (type),
- General network management (type of management and type of person that is manually directing traffic in case of manually directed traffic).
Information on whether the network management instruction or the control resulting from a network management action is advisory or mandatory shall be given.
Other details can be given:
- In which traffic direction the traffic management is applicable,
- For which vehicles the traffic management is applicable,
- If the traffic management instruction has been automatically initiated or not,
- The places (defined in generic terms) where the network management applies (e.g. at toll plaza, in galleries, at high altitude, on slip roads, on the crest of hills),
- Vehicles characteristics for which the network management applies,
Roadside assistance
Details of roadside assistance required.
The roadside assistance type can be given: food delivery, helicopter rescue, vehicle repair …
#### Service information
There are 3 kinds of Service information:
- transit information,
- Information about other transport means,
- For example, cancellation, or delay, on a tram, train, plane, etc. journey,
- service disruption (rest area closed, no diesel…),
- road service disruption (no patrol, emergency call out of order …).
Go back to the previous page
