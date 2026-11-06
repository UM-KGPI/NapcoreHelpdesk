url: https://docs.datex2.eu/v3.7/user-guide/ExchangeSpecifications/
title: Exchange specifications

## Exchange specifications
### Exchange references
For DATEX II, one of the objectives was to clearly split the content data modelling and the data exchange specification.
Two documents deal with data exchange:
- A high level document, called here Exchange PIM, which is independent from technological platforms and presents, definitions, subsystems, use cases, metadata, and operating modes.
- A detailed specification, called here Exchange PSM, which is specific for one platform which has been chosen to be for DATEX II, "Web Services over http".
These documents which contain the details on the exchange process may not be of direct interest for stakeholders who only want to know the main exchange features and the main options they have to decide. This chapter provides a brief overview of what DATEX II exchanges comprise.
### Exchange Overview
#### Logical view
An exchange system between a Supplier and its Client(s) is composed of 2 main subsystems:
- A Publisher subsystem, which makes data available and creates the payload publications,
- A Delivery subsystem, which adds exchange specific information and performs the physical delivery.
The DATEX II exchange specification only describes the delivery subsystem.
A subscription specifies the payload type to be exchanged. It can be defined by the Supplier or by the Client, online or offline. DATEX II allows users to have the liberty to develop subscriptions with the refinements they need.
There are 3 possible operating modes for data delivery:
- Publisher Push on occurrence: Data delivery is initiated by the Publisher every time data is changed
- Publisher Push periodic: Data delivery is initiated by the Publisher on a cycle time basis
- Client Pull: Data delivery is initiated by the Client and data is returned as a response
Remarks:
- operating mode "Publisher Push on occurrence":
- in this mode, for situation publications (events, operator actions, …), situation and situation records lifecycles have to be managed (update, cancel, and end). This is described in section: "Special case: Publisher Push on occurrence",
The main advantage of this mode is the response time (which can be measured in seconds).
- operating modes "Publisher Push on occurrence and Publisher Push periodic":
- after a link failure between the Supplier and his Client(s), recovery mechanisms have to be built, see also Exchange PSM.
Depending on operating mode and publication type, different update methods are possible:
- singleElementUpdate
- If an atomic part of the data has been changed, this atomic part, and only this atomic part, will be exchanged (e.g. only a single situation record update in a multi element situation)
- allElementUpdate
- If an atomic part of the data has been changed, all data associated with the atomic part will be exchanged (e.g. all situation records in a multi element situation)
- snapshot
- A snapshot contains all information available, at a given time, for a subscription
Remarks:
With "Client Pull" operating mode:
- Only "snapshot" update method is used,
- For situations publication, there is no need to manage situation and situation records lifecycles because the exchanged situations are only the active ones at the time of the snapshot (i.e. in the last received exchange),
- After a link failure, no recovery mechanism is needed (the first Pull automatically gets the latest versions).
OPTIONS: depending on his needs, a stakeholder has to decide, at this logical level:
- The refinement of subscriptions, from the "exchange everything" to sophisticated filtering,
- The operating modes he wants to implement (as Supplier and/or as Client), the Pull operating mode being the more simple to develop,
- The update methods he wants to implement, if he uses Publisher Push operating modes
#### Technical view
At this technical level, we distinguish 2 kinds of systems:
- Pull systems,
- Supplier: it can use either:
- Web services over http, with DATEX II WSDL description,
- Only a http server.
- Client: it can use either:
- Web services over http, with DATEX II WSDL description,
- Basic http requests, either GET or POST.
- Push systems
- Supplier: it uses Web services over http, with DATEX II WSDL description,
- Client: it uses Web services over http, with DATEX II WSDL description.
OPTIONS: depending on his needs, the stakeholder has to decide, at this technical level, for the operating modes he has chosen:
- for Pull supplier systems, the usage of Web Services technologies and tools or basic http technology,
- for Pull client systems, the usage of Web Services technologies and tools or basic http technology.
Remark: specialists do not agree on the solutions which have the lowest cost for a Pull system:
- Web Services technology or basic http technology, the choices depend essentially on general policy for software development.
Go back to the previous page
