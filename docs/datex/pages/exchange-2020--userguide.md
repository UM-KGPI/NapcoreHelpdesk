url: https://docs.datex2.eu/v3.7/exchange-2020/userguide/
title: A Userguide to better understand Exchange 2020

## A Userguide to better understand Exchange 2020
### Guide to Exchange documentation
#### Definitions
Term | Definition
Exchange | The transfer of information or data among IT Systems. DATEX II is mostly concerned among Road Information exchange among Traffic Control Centres, Traffic Management Centre, Traffic Information Centres and Service Providers.
Platform Independent Model (PIM) | an abstract description of an Exchange Environment in a way that is independent of any technical solution or technology.
these explain the context and global purpose for which Exchange is needed; two main business scenarios have been identified as:
- Information Delivery
- Collaborative ITS Services
Business Scenarios
Requirements | list of general properties of systems which should be implemented in a real environment to grant functionalities based on selected use cases: not all requirements are applicable or needed to all Use Cases or even consistent among themselves, this allow that a subset of requirements leads to different Features needed and consequent choices in Platform.
Exchange Environment | list of systems and subsystems which are needed to implement Exchange
Exchange Pattern (EP) | a combination of Systems/Subsystems and means of communication among them which enable information exchange which can be combined to implement the Exchange Environment and its requirements.
Features | a combination of Systems/Subsystems and means of communication among them which enable information exchange which can be combined to implement the Exchange Environment and its requirements.
Functional Exchange Profile (FEP) | available characteristics implemented in the Exchange Environment, Features can satisfy one or more requirements.
FEP/EP based Platform Indipendent Model (FEP/EP PIM) | a description of interaction among actors ( systems/subsystems) which describes an Exchange based on the implementation of features, in a way that is independent of specific technology.
Platform Specific model (PSM) | a definite Implementation of a FEP/EP based PIM which describes subsystems and means of communication under a specific choosen technology / Platform
Note
Exchange 2018 specification had been focused on basic use cases such as Snapshot Pull and Snapshot Push, then Simple Push had been introduced to enable link monitoring and Stateful Push adding further controls including session management capabilties, all these may be considered basic exchange pattern, with increasing complexity which is needed to implement a wider set of features to fulfil a wider set of requirements depending on data exchange usage. Those grants most of needed functionalities in everyday use cases. CIS Use case FEP have also been developed enabling service request and service feedback interaction as a basis to implement TMPlan services and general CIS workflows.
#### Exchange approach
Figure 1 — Exchange PIM/PSM modelling approach
Exchange Global Business Scenarios in the context of Traffic Control Centres are derived abstracting from several use cases and requirements collection. This level is named Platform Independent Model (PIM) which describe exchange interaction among system in an abstract way not depending from a specific technology: the description of subsystem interaction is made by use of UML methodology as Collaboration, Sequence and State Diagrams.
As PIM level fully describe the interaction among systems, the implementation of the abstract model to a specific implementation technology is mostly focused on how interaction among subsystems are implemented and data are encoded into specific implementation framework used. E.g. deriving XML Schema for the Basic Exchange Data Model and naming and definition of WSDL methods which implements the abstract message interaction in the sequence diagrams.
Based on above schema the reference for all documentation provided for Exchange 2020 is as follows, including a reference to actually described PIMs and PSMs.
Document type
Support
Reference
Document Name
Exchange PIM
Exchange PSM
Content Description
Modeling Approach
PIM to PSM modeling
Selected FEP + EP PIM definition
Snapshot Pull
WS SOAP
Add link to the specific WSDL when deployed on website
http/get
Snapshot Push
WS SOAP
Simple Push
WS SOAP
Stateful Push
WS SOAP
CIS Service Request
WS SOAP
CIS Service Feedback
WS SOAP
Note
A platform-independent model for a “full publish subscribe” exchange pattern, aiming to describe a WS Notification (Oasis) specification based PSM , is available but has not been prioritised for implementation.
### Exchange methods most suitable for implementations
In DATEX 2020 Exchange specification several Exchange methods are available, suiting different Use Cases defined for Road and Traffic Data Exchange among centres.
It is useful to recap DATEX II Exchange is designed to exchange Road and Traffic Information among Traffic Control Centres (TCC) Traffic Information Centres and / or Service Providers.
As defined in ISO 19468 Information among centres may be exchanged for many purposes, we had defined 2 major Business Scenarios as:
- Data Delivery: only the information exchange requirements are considered, Exchange goal is information delivery itself and no further information processing scope is considered
- Collaborative ITS Services: after data Exchange a processing is needed and the outcome of the process is needed to fulfill specific goal such as Traffic Management Operation decision, VMS Setting, other devices / network resources configuration enabled.
Based on information usage requirements had been defined and collected and the more appropriate Exchange Platform can be selected according to the best fitting to requirements. The following table will provide some guidance in selecting the best usable Platform Exchange at the needed effort / implementation cost.
Use Case | Business Scenario | Available Exchange Methods | Triggered
Delivery of Road Traffic Data from Sensors for standard processing | Data Delivery | Snapshot Pull Snapshot Push | Periodic Condition Triggered
Delivery of Road Traffic Data from Sensors for real time processing | Data Delivery | Simple Push (Snapshot / Delta) | Periodic Condition Triggered On Occurrence
Delivery of Road Traffic Data for ITS delivery Services such broadcast or VMS Setting or Traffic Management | Data Delivery | Simple Push Stateful Push | Condition Triggered On Occurrence
Delivery of Road Traffic Data for Traffic Management / VMS Setting | Collaborative ITS Services | Simple CIS Stateful CIS | On Occurrence
Examples of the four cases stated above:
Delivery of Road Traffic Data from sensors for standard processing
Information gathered at the centre is delivered to other centre for internal use and Traffic Analysis to be managed, data are processed at discrete time interval, not dramatically depending on specific time. Error recovery is possible in case of network errors to gather data after the error had been recovered.
Delivery of Road Traffic Data from sensors for real time processing
Information gathered at the centre is delivered to other centre for internal use and Traffic Analysis to be managed, data are processed when available, to deliver information to implement some services e.g. travel time information or any other real time information which evolve time to time. Error network or data unavailability invalid the data processed which can’t be delivered further, until the exchange is fully recovered.
Delivery of Road Traffic Data for ITS delivery Services such broadcast or VMS Setting or Traffic Management
Information is delivered to be processed within shortest time period to grant information is delivered to final services users
Delivery of Road Traffic Data for Traffic Management / VMS Setting
Information is delivered to be processed within shortest time period to implement road network management decision. Precise Feedback on information processing is given to proceed further to any further processing and operation decision.
Note
The difference among Simple CIS and Stateful CIS is that Simple CIS allows to exchange Service Request and Service Feedback without need to establish a session so they are stateless for connection purposes, while Stateful CIS is based on Session and link monitoring is enabled to monitor network and connection status besides.
The following qualitative table resumes main requirements available in the different platforms
Exchange Methods
Snapshot Push / Pull
Simple Push
Stateful Push
Pub Sub
Requirements
Periodic
Condition Triggered
Timely Information(on occurrence)
N
N
Y
Y
Y
Network Error Management
N
N
Y
Y
Y
Accurate Information(full lifecycle)
N
N
N
Y
Y
Implementation Complexity / Cost
Low
Low
Medium
High
Highest
Functionality
Low
Low
Medium
Medium-High
Full
Note
This diagram is a qualitative one provided to easily orientate users to analysis and choices, a full set of requirement analysis and requirement implementation table by Platform Specific Model is defined in Exchange PIM annexes.
Exchange Methods
Delivery Method
Feature
argument
return
Snapshot Pull
pullSnapshotData
Data Delivery
ExchangeInformation
MessageContainer
Snapshot Push
putSnapshotData
Data Delivery
MessageContainer
ExchangeInformation
Simple Push
putSnapshotData
Data Delivery
MessageContainer
ExchangeInformation
putData
Data Delivery
MessageContainer
ExchangeInformation
keepAlive
Link Monitoring
ExchangeInformation
ExchangeInformation
Stateful Push
putData
Data Delivery
putSnapshotData
Data Delivery
openSession
Session Management
closeSession
keepAlive
The following table lists the available methods available per implemented WSDL web service.
Exchange Methods available / Feature implemented
pullData
putSnapshotData
putData
openSession
closeSession
keepAlive
puCISServiceRequest
putCISServiceFeedback
Data Delivery
Session Lifecycle
SessionLifecycle
Link Monitoring
Support Information Processing
Support Information Processing
Snapshot Pull
X
Snapshot Push
X
Simple Push
X
X
X
Stateful Push
X
X
X
X
X
CIS Service Request/Feedback
X
X
X
X
X
### Exchange Data Model: how to use to include profiled/extended Payload Publication
Basic Data Exchange Model is delivered within DATEX II documentation as a plug and play tool to wrap Payload Information adding information needed to improve and implement Exchange functionalities and Information Management.
The hook to implement profiled payload information is the PayloadPublication class A set of XSD needed for CIS are provided which are included in Message Container description schema and will then include Payload Publication as well through MessageContainer xsd definition:
- DATEXII_3_CISInformation.xsd
- DATEXII_3_ExchangeInformation.xsd
- DATEXII_3_InformationManagement.xsd
- DATEXII_3_MessageContainer.xsd
Based on DATEX II methodology and tool any user has to create his own D2Payload from a pre-packaged Model that contains Exchange and Common, plus all other package he needs. Then generate the schemas with DATEX II tool (webtool at http://webtool.datex2.eu) and use the schemas created that way together with the WSDLs provided.
Warning
PROGRAMMER NOTE Code Generation by JAXB: Please note that importing the WSDL and xsd schemas generated with JAXB the generated code need a manual update to set XMLRoot for ExchangeInformation and MessageContainer such as - add tag @XmlRootElement to ExchangeInformation and MessageContainer classes after they had been generated by JAXB
Go back to the previous page
