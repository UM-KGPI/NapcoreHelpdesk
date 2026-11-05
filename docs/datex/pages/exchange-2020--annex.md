url: https://docs.datex2.eu/v3.7/exchange-2020/annex/
title: Annexes

## Annexes
### A - Methodology presentation
(informative)
#### 1. Introduction
This informative annex presents the approach followed for this document and the rationale behind the choices made.
#### 2. Apply Model Driven Architecture
The original approach taken for modelling the full set of aspects covered by data exchange clearly identified the need to separate the exchange specifications, of what needs to be exchanged and the exchange of the data itself. This is reflected by creating two independent interoperability domains:
- The information interoperability domain as reflected in the PIM defining content (e.g. of DATEX II);
- The exchange interoperability domain as reflected by this document.
While the payload content model can be regarded as describing "what to exchange”, the present exchange specification deals with the problems about "how to exchange”.
A distinction has also been made in the modelling phase to separate the abstract model from its concrete implementation(s). In practice, this approach led to the creation of a Platform Independent Model for exchange (PIM), which described the concepts behind exchange, and one or more Platform Specific Models (PSMs) which defined how the abstract model would actually be implemented on specific technical platforms. As this basic principle of the Model Driven Architecture (MDA) has guided all the work that was already undertaken for creating the full set of specifications for content definition with notable success, it was chosen as well for the Exchange Specification definition.
Therefore, this exchange specification is based on a Platform Independent Model for exchange (the Exchange PIM), which is detailed in one or more documents containing specifications targeted to specific platform implementations (PSM).
#### 3. Use case driven
One of the principles followed in this document is to clearly identify the business scenarios that are addressed by the specifications plus the full set of features that can be available for implementing actual systems based on this document for each of those Business Scenarios.
This led to the identification of two main business scenarios:
- Information Delivery;
- Collaborative ITS Services.
The information delivery business scenario addresses the exchange of traffic and travel information between two data exchange nodes, whereas the Collaborative ITS Services business scenario broadens this approach by including the possibility of having one data exchange node stimulating actions within another data exchange node by requesting the execution of a particular service offered by this node.
These two business scenarios clearly show distinct characteristics, but in order to fully describe them, both need to be detailed further, leading to different possible options. Therefore, the approach was to further refine these general business scenarios into particular, more detailed use cases, each of which address specific requirements.
The term use case is used here to describe a set of interactions between entities (called actors) and the system being analysed, providing a better understanding of the main functions behind such interactions.
In the case of the information delivery domain, the actors involved in the corresponding use cases are the supplier of exchanged information and the receiver of such information – the client. For the Collaborative ITS Services domain, the actors involved are the entity requesting the ITS services, or the service consumer, and the entity providing the service, i.e. the service provider.
#### 4. Functional Exchange Profiles
When analysing the business scenarios and requirements for this document, it became apparent that different use cases within such a business scenario might contain disparate requirements, which could not be easily accommodated into a single, specific implementation. Even worse, some use case might even contain requirements that are, by nature, contradictory, depending on the business needs of the user community they originated from.
Having that in mind, this specification identifies the full set of features that can be available for a data exchange process to take place. Then – in a second step – the specification reflects the particular use cases and selects the best suited set of features for each of them. This selection is denoted a Functional Exchange Profile – FEP.
#### 5. Profile-to-platform mapping
By performing a short survey on the capabilities that modern ICT platforms offer it became apparent that some of the features indicated for implementing data exchange systems can be realised differently depending on the platforms chosen. As such, the one-size-fits-all approach that was followed on the previous version of the Exchange Specification for creating concrete implementations simply does not fit into the new paradigm.
At the heart of the current specification sits the Platform Independent Model (PIM) for data exchange. Its purpose is to model the interactions that were identified for each use case in an abstract, platform independent way. The Exchange PIM is detailed in this document.
This platform independent specification then has to be mapped to a realisation of the indicated FEP on a specific technical platform, described in a Platform Specific Model (PSM) for data exchange, e.g. ISO 14823-3 defines such a mapping. The act of matching a FEP to a platform is also known as profile-to-platform mapping. Each one of these mappings form what is called an interoperability domain. It is only in the scope of such an Interoperability Domain that two data exchange nodes can expect to be interoperable, i.e. if two different implementers of data exchange systems need to be sure that their system will be able to communicate, they both need to follow the same mapping. This platform independent specification then has to be mapped to a realisation of the indicated FEP on a specific technical platform, described in a Platform Specific Model (PSM) for data Exchange, covered by Part 3 of this Specification. The act of matching a FEP to a platform is also known as Profile to Platform Mapping. Each one of these mappings form what is called an Interoperability Domain. It is only in the scope of such an Interoperability Domain that two data exchange nodes can expect to be interoperable, i.e. if two different implementers of data exchange systems need to be sure that their system will be able to communicate, they both must follow the same mapping.
### B - Definition of requirements
(normative)
#### 1. Information Requirements
The primary intent of the information delivery scenario is the provision of information by a supplier to a client. This subclause provides requirements that are related to the data actually being transferred from supplier to client. For each requirement it is stated whether applicable to data delivery or Collaborative ITS Services (CIS) business scenarios, assuming for CIS supplier is intended as service requester and client as service provider and data are exchanged or processed as input to provision of services.
Table B.1 — Information requirements
Requirement | Description | Data Delivery | Collaborative ITS Services
Simple server | In a simple exchange the supplier keeps no track of previous interactions that have occurred between with any of its clients. Therefore, the client is responsible for providing the supplier with all information it can need in order to serve his request. Note that this requirement does not oblige the supplier to have a mechanism for receiving state information as that depends on the availability of other requirements described in this clause (e.g. filter handling). | Y
Stateful server | Any supplier implementing this feature should provide some sort of state keeping mechanism that will allow it to know what information was sent to his client. Therefore, it would be possible for the supplier to send only information that has not been already sent before. A supplier implementing this mechanism can also support other requirements that allow clients to shape the actual data set being received (e.g. filter handling). | Y | Y
Subscription | The information that a supplier delivers to a client is defined by a subscription. A subscription results from an interchange/license agreement, where both parties agree on parameters like, e.g. the information type and periodicity that should be observed upon data delivered. The supplier can choose to reject requests without proper subscription, or it can deliver a standard set of information. | Y | Y
Catalogue exchange | The information a supplier provides is described in a catalogue. The catalogue is used to identify the information contained in a subscription. | Y | Y
The ability of two nodes to exchange information that will allow them to negotiate the requirements supported by both of them (handshake).
This feature deals with exchange parameters, which is different from a catalogue exchange that deals with content.
Self-description | Y | Y
Filter handling | A supplier implementing this feature enables clients to provide specific filters that must be applied to the information being exchanged. | Y | Y
Client profiles | A client profile lets suppliers shape the information they send according to the requirements of the client requesting it. | Y | Y
Interchange/License agreement | Legal artefact where parties taking part in data exchange define the terms and conditions that govern the whole exchange process (e.g. Non-disclosure of information, service level agreements, etc.). | Y | Y
Integrity | This feature implies that the data that is prepared by the supplier should reach its intended recipient without being tampered in any way, semantic, structural or other. | Y | Y
Full audit trail data delivery (all state changes) | All data item versions are delivered to the client. | Y | Y
Snapshot data delivery (last known state) | Only the current version of the data items is delivered to the client. | Y | Y
Incremental Data Delivery | A mechanism where the server sends only the information that has changed since the previous exchange cycle | Y | Y
Reference datasets for different versions | Service a supplier should provide for the client to access referenced data in a versioned way. Even if new versions appear the old versions remain accessible. | Y | Y
Extensibility | Extensions to the data exchange protocol should be supported; therefore, any implementation of the data delivery use case must consider that the protocol can evolve. Thus, each message should state the protocol version it refers to. | Y | Y
Support for lifecycle management | A set of function for updating information at client systems according to updated information gathered at supplier system | Y | Y
Support for information management | A set of functions that will let the supplier (as service requester) tell the client (as service provider) what to do with the information being exchanged (processing directive). | Y
Support for feedback on information processing | A set of functions that will let the client (service provider) tell the supplier (service requester) the outcomes of processing the information by the stated directive which had been exchanged. | Y
Distributed transaction | A capability for the exchange system to coordinate among several involved service provider systems to collaborate in implementing a distributed service. | Y
Distributed atomic transaction | A capability for the exchange system to coordinate among several involved service provider systems to collaborate in implementing a distributed service keeping consistency in transaction. | Y
Synchronization | A mechanism that lets clients request the whole set of information currently known to the supplier to ensure that its internal data structures be in exactly the same state as those of the supplier. (intended for CIS the Service provider need the exact information to provide the requested services) | Y | Y
Delayed delivery | In the case that preparing and sending a data set by the supplier would take too much time to complete, the supplier should inform the client about this fact. This mechanism should also define how and when the client would be able to access the information it needs. | Y
Data delivered as soon as possible | This feature is used to ensure that the supplier sends the information as soon as it becomes available in its system. | Y | Y
On demand request (query) | The ability of the client to ask the server for information it needs whenever it wants (Client Pull). | Y
#### 2. Communication Requirements
Communication requirements characterise the mechanism that data exchange nodes implement in order to address problems specific to the communication layer of the data exchange process. These requirements are completely unaware of both the security and information features that are in use. The idea is that given a supplier has prepared a particular dataset; the requirements described in this subclause can be used to successfully convey it to the client.
Table B.2 — Communication requirements
Requirement | Description | Data Delivery | Collaborative ITS Services
Sessionless | No session is used during the data exchange process | Y | Y
Session | Client and supplier negotiate and establish a session before starting to exchange information. The session parameters constitute state information shared between both stations. | Y | Y
Request/response | A mechanism where the client requests the data and instantly receives the response. | Y | Y
Delivery/response | A mechanism where the supplier initiates the data delivery process, while the client patiently waits for it. | Y | Y
Error handling | A mechanism that allows both client and supplier to detect that an error has occurred during the exchange process and to decide what actions should be taken to handle it. | Y | Y
Timely responses | The communication layer should introduce a minimum delay on the data delivery process, ideally none. | Y | Y
Timeout management | The ability to handle timeout situations that happen during an exchange process. | Y | Y
Exchange quality measures (ex. response timestamp) | The messages exchanged should include extra information that allows both parties involved to measure the quality of service of the communication layer. | Y | Y
Logging | A mechanism for storing information about exchange activities, which could then be used to analyse the whole process. | Y | Y
Failed data recovery | When the supplier fails to deliver the information to the client, this feature ensures that the failed data messages will be successfully delivered to the client at a later time. | Y | Y
Message sequence | A mechanism that allows identifying each message exchanged between two entities by including a unique sequence number. | Y | Y
A mechanism that ensures that data sent by a supplier is really received by the client provided that both client and supplier are active and have the ability to communicate.
This does not include any semantic validation. Syntax validation is optional.
Full reliability | Y | Y
Link monitoring and control | This feature enables both parties to continually check whether the communication link works properly and act accordingly when it is broken. | Y | Y
On occurrence update | A supplier implementing this feature should send the information to the client as soon as it is available. | Y
Periodic update | A supplier implementing this feature should buffer all the information to be sent to a particular client for a pre-defined time period send information only when this period has elapsed. | Y
Multi-part data delivery | When the size of the information to be delivered is too large, the supplier can choose to deliver it in chunks. At the first request, the supplier returns the first data chunk. The response contains the message ID and the total number of parts (chunks) that comprise the dataset. The client then has to request each of the remaining parts of the message. | Y | Y
Compression | The ability to pack the same information in a smaller amount of data in order to decrease the transmission time. | Y | Y
#### 3. Security Requirements
The requirements described in this subclause deal with all aspects used to provide security services at any of the different communication levels, such as peer authentication, channel security and so on.
Table B.3 — Security requirements
Requirement | Description | Data Delivery | Collaborative ITS Services
Client Authentication | The act of establishing or confirming a client as authentic. | Y | Y
Client Authorization | The process of verifying if a client is allowed to access some resource (commonly referred to as read access) or execute some action (commonly referred to as write access). | Y | Y
Supplier Authentication | The act of establishing or confirming a supplier as authentic. | Y | Y
Supplier Authorization | The process of verifying if a supplier is allowed to access some resource (commonly referred to as read access) or execute some action (commonly referred to as write access). | Y | Y
State the intended recipient | The act of indicating the destination peer of a message. | Y | Y
Confidentiality | Ensuring that information is accessible only to those authorized to have access (ISO 27002). | Y | Y
Client identification | A mechanism that allows a client to provide his identity. | Y | Y
Supplier identification | A mechanism that allows a supplier to provide his identity. | Y | Y
Non-repudiation | A mechanism to guarantee that the sender (supplier of a client) of a message cannot later deny having sent the message. | Y | Y
#### 4. Financial/economic requirements
Although being not at the same level the requirements described in this subclause have some economic/financial impact on the actual implementation of the data exchange sub-system.
Table B.4 — Financial/economic requirements
Requirement | Description | Data Delivery | Collaborative ITS Services
Reasonable TCO (Total Cost of Ownership) | The data exchange sub-system must have a reasonable TCO (Total Cost of Ownership). | Y | Y
Expandability at a reasonable cost (scalability) | The data exchange sub-system should be implemented in such a way that it can be possible to increase the capacity of the system at a reasonable cost. Capacity relates to any of the system resources, such as data volumes, computation power, parallel processing, etc. | Y | Y
Low processing resources | It shall be possible to implement a data exchange sub-system on systems with low processing resources. | Y | Y
### C - Basic Exchange Data Model and Data Dictionary
(informative)
#### 1. Overall presentation
The described data model is based on a UML methodology that is independent from any technical platform.
Whenever exchange features as session management, link monitoring are needed some extra information need to be conveyed among supplier and client to enable control and reliable exchange management. The basic exchange data model describes the more common data needed to implement the exchange features supported by the different exchange patterns.
As in specific contexts, more than one information payload need to be exchanged, this model further allows to exchange multiple payloads based on such extra exchange requirements.
This model is suggested to implement minumum exchange information and to enable interoperability among exchange interfaces which implement the same exchange pattern, but may not be needed for specific simplified platform specific models implicitely assuming the few mandatory data defined in the model (e.g. supplier identification, protocol type, protocol version, exchange status).
#### 2. Basic Exchange Data Model
#### Overview
Exchange Data Model is used to convey information which are needed to manage Exchange Features such as Information Management, Session Management, Link Monitoring.
Further Information is needed to manage CIS.
#### MessageContainer Diagram
Figure C.1 — The MessageContainer class diagram
A MessageContainer class is introduced to allow delivery of further information besides payload such as:
- Exchange Information: which is needed to manage exchange feature such as session management and link monitoring and error management.
- Information management related information.
- Collaborative ITS Services information.
Information management and CIS Information linked classes are optional, while minimum Exchange Information is to be managed e.g. to convey information about the used protocol and version and supplier identification as exchange responsibility. Other constraints on implementation depending on different FEP+EP which implement the exchange and its features, e.g. exchange dynamic information attributes will be mandatory in a FEP+EP which wants to implement session management, such as Stateful Push FEP+EP.
The MessageContainer class also allows conveying multiple payloads within a single exchanged message.
#### The ExchangeInformation class diagram
Figure C.2 — ExchangeInformation class diagram
Exchange Information is used to convey information about exchange environment such as:
- Exchange Context, which is implied by supplier and client(s) identification represented as exchange agent which may be associated to an external international identifier, the type of protocol which is defined to be used in exchanging data, the implemented version of this protocol, the operating mode and update method used in the data delivery exchange.
- Subscription with its period validity information and delivery frequence. An external enhanced validity may support more information such as recurring periodic validity for specific time intervals within specific days.
- Dynamic Information: such as exchange status and return status (within a set of predefined exchanged status and return status enumeration lists and their reason) and SessionID for exchange patterns which manages sessions. Sequencing number for synchronisation purposes and a Boolean information about payload completion enable large dataset handling features available in some exchange pattern.
- Return Information is used in return messages to convey a first information about information delivery and cis request exchange and also to send back special request to manage such as snapshot synchronisation.
Exchange context is mostly implicit in subscription contract but it is instantiated to simplify or enable application level check for some communication features such as supplier and client identification, authentication, authorisation, which can only be implemented in a reliable way based on communication layers.
In Dynamic information the attribute exchangeStatus is the only mandatory information, but as this status may be not managed its value can be set to "undefined". Other information will be de facto mandatory whenever needed to be managed in specific FEP+EP, e.g. in case of session management feature implementation SessionID attribute in class SessionInformation will be needed to be managed.
#### The InformationManagement class diagram
Figure C.3 — InformationManagement class diagram
InformationManagement class allows delivering information management data: as defined in Annex F for life cycle information only valid information is managed in the payload, whenever an element ends its life cycle, i.e. being closed or cancelled, it is no longer conveyed in the payload and information management is to be delivered to manage closures or cancellation of such elements.
These closed and cancelled elements are conveyed linked through InformationManagedResourceList class and are addressed by ElementReference class which allows identification of the element by its reference or versioned reference, specifying its managementStatus, i.e. closed or cancelled.
- The CISInformation class diagram
Figure C.4 — The CISInformation class diagram
With reference to Annex G Collaborative ITS Services transform the vision of supplier and client in service provider and service requester: CISInformation conveys in the data model the information needed to implement service request and service feedback as described to be exchanged between service provider and service requester.
CISInformation class: allows to convey any Service Request and Service Feedback which are requested to be exchanged among Service Requester and Service Providers through the respective named classes ServiceRequest and ServiceFeedback.
ServiceRequest: conveys information related to a single Service Request
- Service Request creation and update time,
- predefinedService: to be chosen among an enumerated list such as processing, broadcast delivery, VMS message process, Traffic Management Plan activation,
- not predefined service name,
- custom service parameter: custom parameter to raise for processing,
- requestedAction: Approve, implement, terminate, cancel,
- element to process reference or external reference,
- expiry time when a service is valid only implemented within a limited time amount after which it will be no longer needed.
Service Request can be related to a Service Condition through the ServiceCondition class identifying the needs for that kind of service through some payload reference for a predefined, coded or not predefined, i.e. unpredictable condition.
ServiceRequest class also allows addressing the identification of involved Service Providers needed to implement such request and the corresponding service.
ServiceFeedback: allows to convey information about the processing of a Service request previously exchanged through reference information to the Service Request itself and specifying its Status among a set (compliant, failed, not compliant, processing, rejected, scheduled, success, timedOut) plus a reason for that status.
#### 3. Data Dictionary Overview
This data dictionary describes the characteristics of the different classes, attributes and roles appearing in the data model defined in C.2. The dictionary is specified as a set of tables grouping classes, attributes and roles for each package as they are defined in C.2.
For each package the following are successively provided:
- The class table,
- The association table,
- The attribute table.
Each table of a given type has the same structure.
The data dictionary is categorised into sections following the different UML model packages as mentioned above. It defines for every package the entities and elements corresponding.
The table columns have the following meaning:
- Column Name: they provide the symbolic name (either in Lower or Upper Camel Case) given to the corresponding class, attribute or association role.
- Column Designation: it provides the corresponding name in natural language of the corresponding class, attribute or role.
- Column Definition: it provides a comprehensive definition detailing this class, attribute or association role.
Some columns are specific for one or two tables. The class tables include the following two columns:
- Column Abstract: it indicates if the corresponding class is abstract (value "yes”) or concrete (value "no”). Abstract classes are defined in ISO/IEC 19505-1.
The attribute tables and the association tables include the following column:
- Column Multiplicity: it provides the number of occurrences a class may have when instantiating this association (resp. a class attribute may have when instantiating this class). The adopted syntax is the following: m..n where ‘m’ and ‘n’ respectively represent the minimum and the maximum value of multiplicity.
For association roles, the possible value for ‘m’ are:
- 0 in case of an optional participation of the corresponding class when instantiating the association;
- 1 in case of a mandatory participation of the corresponding class when instantiating the association;
- 2, 3, … in case a minimum number of participations of the corresponding class is explicitly defined when instantiating the association.
For association ends, the possible value for ‘n’ are:
- 1 in case only one class instance is at most participating at the association instantiation;
- * in case several instances are allowed participating at the association instantiation;
- 2, 3, .. in case a maximum number of participations of the corresponding class is explicitly defined when instantiating the association.
For attributes, the possible value for 'm' are:
- 0 in case of an optional attribute;
- 1 in case of a mandatory association / attribute;
- 2, 3, … in case a minimum number of occurrences is explicitly defined.
- For attributes, the possible value for 'n' are:
- 1 in case only one attribute instance is allowed;
- * in case several instances are allowed for this attribute without being specified;
- 2, 3, .. in case a maximum number of occurrences is explicitly defined.
For the attribute tables, the following column has been added:
- Column Type: it provides the class name used as data type. It is only provided for elements corresponding to class attributes. When the type name ends with 'Enum' this means it corresponds to an enumeration of accepted values defined in C.6.
For the association table, the following column has been added:
- Column Target: it provides the class name appearing at the second end of the relationship, i.e. linked through the corresponding association.
#### 4. Data dictionary for Basic Exchange Data Model
#### InformationManagement for "ExchangeDataModel"
#### Location of "Classes" package
The location of the classes package is MessageContainer/InformationManagement/Classes
#### Classes of the "Classes" package
Table C.1— Classes of the "Classes" package
Class name | Designation | Definition | Abstract
ElementReference | Element reference | Element Reference | no
InformationManagedResourceList | Information managed resource list | Managed Resource List | no
InformationManagement | Information management | Information Management | no
#### Associations of "Classes" package
Table C.2— Associations of the "Classes" package
Class name | Association end | Designation | Definition | Multiplicity | Target
InformationManagedResourceList | elementReference | Element reference | 1..* | ElementReference
InformationManagement | informationManagedResourceList | Information managed resource list | 0..1 | InformationManagedResourceList
#### Attributes of the "Classes" package
Table C.3— Attributes of the "Classes" package
Class name | Attribute name | Designation | Definition | Multiplicity | Type
ElementReference | managementStatus | Management status | It identifies the status of the element referenced | 1..1 | ManagementTypeEnum
reference | Reference | It identifies an element reference | 0..1 | Reference
versionedReference | Versioned reference | It identifies an element versioned reference | 0..1 | VersionedReference
#### ExchangeInformation "Classes" package
#### InformationManagement for "ExchangeDataModel"
#### Location of "Classes" package
The location of the classes package is MessageContainer/ExchangeInformation/Classes
#### Classes of the "Classes" package
Table C.4— Classes of the "Classes" package
Class name | Designation | Definition | Abstract
Agent | Agent | an actor in the exchange context | no
DynamicInformation | Dynamic information | Dynamic Exchange Information | no
ExchangeContext | Exchange context | Exchange Context e.g. which defines the specific Exchange Pattern and Functional Exchange Profile and other details about Supplier & client | no
ExchangeInformation | Exchange information | Exchange Information | no
ReturnInformation | Return information | the information provided as rerturn after a message had been delivered | no
SessionInformation | Session information | Session Information | no
Subscription | Subscription | an actor in the exchange context | no
#### Associations of "Classes" package
Table C.5— Associations of the "Classes" package
Class name | Association end | Designation | Definition | Multiplicity | Target
Agent | internationalIdentifier | International Identifier | 0..1 | InternationalIdentifier
DynamicInformation | returnInformation | Return information | 0..1 | ReturnInformation
sessionInformation | Session information | 0..1 | SessionInformation
ExchangeContext | subscription | Subscription | 0..1 | Subscription
Agent
clientOrCisProvider | Client or Cis Provider | it defines the client or CIS provider information of the exchange context, depending on Exchange Pattern it may be instantiated for single or multiple client or no one | 0..*
clientOrCisRequester | Client or Cis Requester | it defines the supplier or CIS requester information of the exchange context | 1..1 | Agent
ExchangeInformation | dynamicInformation | Dynamic information | 1..1 | DynamicInformation
exchangeContext | Exchange context | 1..1 | ExchangeContext
Subscription | validity | Validity context | 0..1 | Validity
#### Attributes of the "Classes" package
Table C.6— Attributes of the "Classes" package
Class name | Attribute name | Designation | Definition | Multiplicity | Type
Agent | address | Address | the network address of the exchange agent | 0..1 | String
name | name | name of the agent in the exchange context | 0..1 | String
referenceID | Reference ID | a reference for the agent in the exchange context | 0..1 | String
serviceURL | Service URL | the URL to address the agent service | 0..1 | String
DynamicInformation | completedPayload | Completed Payload | attribute which can be used to indicate when a payload had been completed or not within the current message, when set to false the following messages will deliver and complete all the payload content relative ot the current exchange or current session | 0..1 | Boolean
exchangeStatus | Exchange status | Status of Exchange defined by protocol Specification | 0..1 | ExchangeStatusEnum
exchangeStatusDescription | Exchange status description | multilingual textual Status description of Exchange defined by protocol Specification | 0..1 | MultilingualString
messageGenerationTimestamp | Message generation timestamp | the date time in which the message had been generated | 0..1 | DateTime
messageSequencingNumber | Message sequencing number | a number, always increasing within a same session among a client and supplier, which can be used to order message within a delivery | 0..1 | NonNegativeInteger
ExchangeContext | codedExchangeProtocol | Coded exchange protocol | the exchange protocol type as referenced by any standard or by agreement among client and supplier, e.g. Snapshot Pull, Simple Push, Collaborative ITS Services, etc | 1..1 | ProtocolTypeEnum
exchangeSpecificationVersion | Exchange specification version | the version of the protocol used for the exchange as by standard or as agreed among client and supplier | 1..1 | String
nonCodedExchangeProtocol | Non coded exchange protocol | when a protocol is used in the exchange which is not predefined coded protocol, this attribute defines protocol information among supplier and client | 0..1 | String
operatingMode | Operating mode | feature which specifies when the information should be delivered | 0..1 | OperatingModeEnum
updateMethod | Update method | feature which specifies when the information should be delivered | 0..1 | UpdateMethodEnum
ExchangeInformation | messageType | Message type | the message type which is used in specific exchange pattern to define the use of exchanged message, e,g, payload delivery, open session, keep alive, cis service request and feedback etc. | 0..1 | MessageTypeEnum
ReturnInformation | codedInvalidityReason | Coded invalidity reason | it specifies the invalid information which had been found in a message by the receiver | 0..1 | InvalidityReasonEnum
returnStatus | Return status | the return status of a message previously delivered | 1..1 | ExchangeReturnEnum
returnStatusReason | Return status reason | the reason for the setting of the return status | 0..1 | MultilingualString
SessionInformation | sessionID | Session ID | the ID of the session established among Client and Supplier | 1..1 | String
startSession | Start session | the start date and time of the session | 0..1 | DateTime
Subscription | deliveryFrequency | Delivery frequency | the planned time payload delivery frequence as number in seconds, it includes "keep alive" messages delivery when not payload is to be delivered | 0..1 | NonNegativeInteger
name | Name | the descriptive name of the subscription | 0..1 | String
#### CISInformation "Classes" package
#### Location of "Classes" package
The location of the classes package is MessageContainer/CISInformation/Classes
#### Classes of the "Classes" package
Table C.7— Classes of the "Classes" package
Class name | Designation | Definition | Stereotype | Abstract
CISInformation | CIS information | CIS information | D2Class | no
ServiceFeedback | Service feedback | Feedback about a specific Service Request from the Service Implementer to the Requester | D2Class | no
ServiceRequest | Service request | Service Request from the Service Implementer to the Requester | D2Class | no
ServiceRequestCondition | Service request condition | specifies the condition which is behind the need for the service request, e.g. a specific situation or situation record, travel times status, specific road data or external conditions | D2Class | no
#### Associations of "Classes" package
Table C.8— Associations of the "Classes" package
Class name | Association end | Designation | Definition | Multiplicity | Target
CISInformation | serviceFeedback | Service feedback | 0..* | ServiceFeedback
serviceRequest | Service request | 0..* | ServiceRequest
ServiceFeedback | serviceImplementer | Service implementer | It Identifies the international identifier requester feedback | 1..1 | InternationalIdentifier
ServiceRequest | serviceRequestCondition | Service request condition | 0..1 | ServiceRequestCondition
serviceRequester | Service requester | It Identifies the international identifier requester | 1..1 | InternationalIdentifier
serviceImplementer | Service implementer | It Identifies the list of international identifier implementer | 1..* | InternationalIdentifier
#### "Classes" package attributes
Table C.9— Attributes of the "Classes" package
Class name | Attribute name | Designation | Definition | Multiplicity | Type
ServiceFeedback | serviceRequestFeedbackReason | Service request feedback reason | additional text to feedback about the Status of the Service Request | 0..1 | MultilingualString
serviceRequestReference | Service request reference | Reference to the service request to which refers the Service Feedback | 1..1 | VersionedReference
serviceRequestStatus | Service request status | specifies the Status of Service request referenced | 1..1 | ServiceActionStatusEnum
ServiceRequest | customServiceParameter | Custom service parameter | a string conveying information for custom parameter to Service | 0..1 | String
elementToProcessReference | Element to process reference | Element reference to be process | 0..1 | Reference
elementToProcessVersionedReference | Element to process versioned reference | Element versioned reference to be process | 0..1 | VersionedReference
expiryTime | Expiry time | date time until which to implement the required action for Service | 0..1 | VersionedReference
externalReference | External reference | Extranle reference to be process | 0..1 | String
notPredefinedServiceName | Not predefined service name | Name of service not predefined | 0..1 | String
predefinedService | Predefined service | Type of predefined service | 1..1 | PredefinedServiceEnum
requestedAction | Requested action | identifies the action requested for the specified Service | 1..1 | ServiceActionEnum
servicerRequestCreationTime | Servicer request creation time | Time of creation request | 1..1 | DateTime
servicerRequestVersionTime | Servicer request version time | Time of version request time | 1..1 | DateTime
ServiceRequestCondition | conditionDescription | Condition description | A multilingual description of the condition under which the Service Request is instantiated | 0..1 | MultilingualString
externalIdCondition | External id condition | en external reference ID to the condition for the Service Request | 0..* | String
referencedCondition | Referenced condition | the list of condition information which are referenced by a Identifiebla in payload publications | 0..* | Reference
versionReferencedCondition | Version referenced condition | the list of condition information which are version referenced by a Identifiebla in payload publications | 0..* | VersionedReference
#### "Common" package
#### Location of "Common" package
The location of the Common package is MessageContainer/Common
#### Classes of the "Common" package
Table C.10 — Classes of the "Common" package
Class name | Designation | Definition | Stereotype | Abstract
#### "Common" package external classes
Table C.11 — External classes of the "Common" package
Class name | Designation | Definition
InternationalIdentifier | International identifier | An identifier/name whose range is specific to the particular country.
PayloadPublication | Payload publication | A payload publication of domain specifica information created at a specific point in time that can be exchanged an exchange interface.
Validity | Validity | Specification of validity.
#### Associations of "Common" package
There are no defined associations in the "Common" package.
#### "Common" package attributes
There are no defined attributes in the "Common" package.
#### "MessageContainer" package
MessageContainer
#### "MessageContainer" package classes
Table C.12 — Classes of the "MessageContainer" package
Class name | Designation | Definition | Stereotype | Abstract
MessageContainer | Message container | a Container class to manage further information classes as Payload, Information Management, CIS Information and Exchange Information | D2ModelRoot | no
#### Associations of "MessageContainer" package
Table C.13 — Associations of the "MessageContainer" package
Class name | Association end | Designation | Definition | Multiplicity | Target
MessageContainer | cisInformation | Cis information | 0..1 | CISInformation
informationManagement | Information management | 0..1 | InformationManagement
exchangeInformation | Exchange information | 1..1 | ExchangeInformation
payload | Payload | 0..* | PayloadPublication
#### "MessageContainer" package attributes
There are no defined attributes in the "MessageContainer" package.
#### Data Dictionary of Enumeration for "ExchangeDataModel"
#### Introduction
This clause contains the definitions of all enumerations which are used in the "ExchangeDataModel".
#### The enumeration "ExchangeReturnEnum"
Enumeration that identifies the return status
Table C.14 — Values contained in the enumeration "ExchangeReturnEnum"
Enumerated value name | Designation | Definition
ack | Ack | request fulfilled
closeSessionRequest | Close session request | client request to close session
fail | Fail | request failed
snapshotSynchronisationRequest | Snapshot synchronisation request | client request for snapshot synchronisation
#### The enumeration "ExchangeStatusEnum"
Enumeration that identifies the status of exchange session
Table C.15 — Values contained in the enumeration "ExchangeStatusEnum"
Enumerated value name | Designation | Definition
closingSession | Closing session | the closure of Session is under negotiation for protocol with Session management
offline | Offline | no exchange is possible due to lack of connectivity
online | Online | exchange connection is regular with no errors detected
openingSession | Opening session | Session Opening for protocols with Session management
resuming | Resuming | some errors had happened and Session is resuming for protocol with Session Management
#### The enumeration "InvalidityReasonEnum"
A list of possible invalidity reason for messages
Table C.16 — Values contained in the enumeration "InvalidityReasonEnum"
Enumerated value name | Designation | Definition
closingSession | Closing session | the closure of Session is under negotiation for protocol with Session management
offline | Offline | no exchange is possible due to lack of connectivity
online | Online | exchange connection is regular with no errors detected
openingSession | Opening session | Session Opening for protocols with Session management
resuming | Resuming | some errors had happened and Session is resuming for protocol with Session Management
undefined | Undefined | the exchange status is not defined in the exchange implementation
#### The enumeration "MessageTypeEnum"
The list of message type which can be implemented to define specifice exchange pattern features
Table C.17 — Values contained in the enumeration "MessageTypeEnum"
Enumerated value name | Designation | Definition
CISFeedback | CIS feedback | message conveying CIS feedback message
CISServiceRequest | CIS service request | message conveying CIS Service request
closeSession | Close session | message conveying close session request
keepAlive | Keep alive | message conveying keep alive message
openSession | Open session | message conveying open session request
payloadDelivery | Payload delivery | message conveying payload delivery
return | Return | message conveying return information
#### The enumeration "ServiceActionEnum"
The current or requested status of TMP activation during request, implementation and termination phases
Table C.18— Values contained in the enumeration "ServiceActionEnum"
Enumerated value name | Designation | Definition
agreement | Agreement | request for CIS agreement
cancellation | Cancellation | request to cancel the CIS Agreement or Implementation Request before agreement or implementation phase is completed
implementation | Implementation | the request of CIS Implementation, whenever no need of agreement proposal is needed, or a previous proposal have been agreed
processing | Processing | request to process information according to Requested Service (e.g. processing of any information to generate messages to display on VMS)
statusInformation | Status information | Request on previously delivered service request processing status information, to be delivered in Feedback
termination | Termination | request to terminate the CIS Activation once implemented
#### The enumeration "OperatingModeEnum"
The enumeration of the possible operating mode which can be adopted in the exchange
Table C.19 — Values contained in the enumeration "OperatingModeEnum"
Enumerated value name | Designation | Definition
conditionTriggered | Condition triggered | the information update is sent when a specific application level condition is found
onOccurrence | On occurrence | the delivey of information happens as soon as the information is updated on the supplier system
other | Other | other condition when supplier delivers information or client pull temporal condition
periodic | Periodic | the information is provided by the supplier or pulled for by the client on specific timing or cyclic timeout
#### The enumeration "PredefinedServiceEnum"
List of predefined service requests
Table C.20— Values contained in the enumeration "PredefinedServiceEnum"
Enumerated value name | Designation | Definition
broadcastDelivery | Broadcast delivery | Service delivery broadcast
other | Other | other service
tmpActivation | Tmp activation | Service TMP activation
vmsMessageProcessing | VMS message processing | Activation of VMS Message processign on information
#### The enumeration "ProtocolTypeEnum"
A list of protocol type as possible exchange specification available
Table C.21 — Values contained in the enumeration "ProtocolTypeEnum"
Enumerated value name | Designation | Definition
deltaPull | Delta pull | in a pull delivery the information gathered is all updated information after last delivery
deltaPush | Delta push | in a push delivery all updated information after last delivery is provided as payload
other | Other | other protocol type
simpleCIS | Simple CIS | collaborative ITSService service request and feedback are implemented without link monitoring and session management
simplePush | Simple push | a snapshot or delta Push delivery context with link monitoring but without session management
snapshotPull | Snapshot pull | all active information avaliable by the supplier is retrieved by the client in a pull operation
snapshotPush | Snapshot push | all active information available is delivered by the supplier in a push operation
statefulCIS | Stateful CIS | collaborative ITS Service Request and Feedback with session management and link monitoring
statefulPush | Stateful push | a Push delivery context with link monitoring but without session management
#### The enumeration "ServiceActionEnum"
The current or requested status of TMP activation during request, implementation and termination phases
Table C.22 — Values contained in the enumeration "ServiceActionEnum"
Enumerated value name | Designation | Definition
agreement | Agreement | request for CIS agreement
cancellation | Cancellation | request to cancel the CIS Agreement or Implementation Request before agreement or implementation phase is completed
implementation | Implementation | the request of CIS Implementation, whenever no need of agreement proposal is needed, or a previous proposal have been agreed
processing | Processing | request to process information according to Requested Service (e.g. processing of any information to generate messages to display on VMS)
statusInformation | Status information | Request on previously delivered service request processing status information, to be delivered in Feedback
termination | Termination | request to terminate the CIS Activation once implemented
#### The enumeration "ServiceActionStatusEnum"
Defines values of service status
Table C.23 — Values contained in the enumeration "ServiceActionStatusEnum"
Enumerated value name | Designation | Definition
compliant | Compliant | service request has been found compliant to required specification for the service
failed | Failed | service request failed during processing
notCompliant | Not compliant | service request has not been found compliant to required specification for the service
processing | Processing | service request processing fase is not yet completed
rejected | Rejected | service request has been rejected by the service provider
scheduled | Scheduled | the Service Request had been scheduled for processing by the Service Provider
success | Success | the Service Request had been successfully processed by the Service Provider
timedOut | Timed out | the Service Request had not been fulfilled in the agreed time
#### The enumeration "UpdateMethodEnum"
The list of the possible operating method which are managed for exchange
Table C.24 — Values contained in the enumeration "UpdateMethodEnum"
Enumerated value name | Designation | Definition
allElementUpdate | allElementUpdate | for situation delivered the information of all situation elements is updated in a single delivery
allInformationUpdate | allInformationUpdate | the payload delivers all elements which have some information updated since the last delivery, can be named “delta” update
other | other | other update method available implemented by the supplier
singleElementUpdate | singleElementUpdate | any single element update is delivered
snapshot | snapshot | all active and/or available information is delivered
#### Data Dictionary of <> for "ExchangeDataModel"
#### Overview
There are no specific data types defined in the "ExchangeDataModel". However, different attributes are used and are on generic data types which are in principle defined in the content packages. They often map to intrinsic datatypes of PSM.
#### The data type "DateTime"
A combination of integer-valued year, month, day, hour, minute properties, a decimal-valued second property and a time zone property from which it is possible to determine the local time, the equivalent UTC time and the time zone offset from UTC.
#### The data type "MultilingualString"
A multilingual string, whereby the same text may be expressed in more than one language. If the data type is not implemented as such in the targeted PSM it may mapped to a String.
#### The data type "Reference"
A reference to an identifiable managed object where the identifier is unique. It comprises an identifier (e.g. GUID) and a string identifying the class of the referenced object.
#### The data type "String"
A character string whose value space is the set of finite-length sequences of characters. Every character has a corresponding Universal Character Set code point (as defined in ISO/IEC 10646), which is an integer.
#### The data type "VersionedReference"
A reference to an identifiable version managed object where the combination of the identifier and version is unique. It comprises an identifier (e.g. GUID), a version (NonNegativeInteger) and a string identifying the class of the referenced object.
### D - Introduction to communications and protocols
(informative)
#### Overview
This informative annex includes a description of solutions and options that can give an answer to the data exchange requirements, and should allow to the exchange specification the identification of the most used technologies and standards that might be used to address those features.
At this level the data exchange protocol does not define any new specification. Instead, it identifies solutions based on the following principles:
- Security should be delivered by the communication layer;
- Identify the standards and technologies that fit to our requirements and features;
- Describe in general the technology that can be used. However, each PSM Technical Specification should identify in detail how the technology must be implemented.
#### Protocol of communication
#### Overall presentation
DATEX II is a protocol for traffic and travel data information exchange between systems typically over the Internet. The Internet protocol suite is the set of communications protocols used for the Internet.
The Internet protocol suite classifies its methods and protocols into four hierarchical abstraction layers:
- The link layer that support the technology connected directly by hardware components;
- The internet layer facilitates the interconnection of local networks, the support for the Internet Protocol (IP) communication;
- The transport layer supports the Host-to-host communication, which provides a general application-agnostic framework to transmit data between hosts using protocols like the Transmission Control Protocol (TCP) and the User Datagram Protocol (UDP)
- The application layer is the highest level, which contains all protocols such as HTTP, FTP, TLS/SSL, etc., that support the data communications services. This layer handles application-based interaction on a process-to-process level between communicating Internet hosts.
The data exchange protocol has a strong request to use current technologies like Web services to support the implementation of the exchange features. This Technical Specification identifies in each Internet protocol layer the existing standards and protocols that can be used to support each data exchange features and requirements. Each PSM standard should then describe how these protocols should be implemented.
The protocols used by this Technical specification are:
- At the link, internet and transport layers, it uses the TCP/IP protocol and can implement some requirements like security over IPsec;
- At the application layer it will base its implementation over the use of HTTP protocol. Some requirements can be implemented at this level, like support for services (Web Services), security (TLS/SSL or WS-Security) or compression.
The following diagram the most important protocols and standards that can be used to address each data exchange feature:
Figure D.1 — Communication protocols and standards
#### Web Services definition and options
Web Services provide standard means of interoperating between different software applications, running on a variety of platforms and/or frameworks.
Definition (W3C - Web Service architecture - http://www.w3.org/TR/2004/NOTE-ws-arch-20040211): "A Web Service is a software system designed to support interoperable machine-to-machine interaction over a network. It has an interface described in a machine-processable format (specifically WSDL). Other systems interact with the Web Service in a manner prescribed by its description using SOAP messages, typically conveyed using HTTP with an XML serialisation in conjunction with other Web-related standards.”
Web Services definitions offer several options. As an example the following table shows the options chosen by DATEX II.
Table D.1 — Web service options
Web Service Options | Decision
Discovery | Not dynamic: UDDI is not used, the Web Services are described in DATEX II Specification which is the reference for development
Security | The security set-up has to be decided by each PSM
#### Security
The data exchange protocol is designed to exchange data and should be able to implement different levels of security in order to support information security features. Security and their capabilities can be implemented at different layers of the Internet protocol using different solutions and technologies, all for the same capabilities:
- At the link and transport layer IPSec can be used to implement security;
- At the application layer TLS/SSL can be used over HTTP or WS-Security can be implemented over the Web Services.
Data exchange systems can implement the following features and capabilities:
- Authentication is the capability of determining whether someone or something is, in fact, who or what it is declared to be. On a dataexchange system both the supplier and the client can be authenticated.
- Authorization is the capability of giving someone permission to do or have something. This concept is related to the subscription or profiles and will not be described at the security level.
- Confidentiality is the capability that protects against the disclosure of information. In data exchange systems, it represents the assurance that only the supplier and the client are allowed to see the message.
- Integrity is the capability that determines if the information or the message is correct and was not changed.
- Nonrepudiation is the assurance that someone cannot denysomething. Typically, nonrepudiation refers to the ability to ensure that a party to a contract or a communication cannot deny the authenticity of their signature on a document or the sending of a message that they originated. On the Internet, a digital signature is used not only to ensure that a message or document has been electronically signed by the person that purported to sign the Technical Specification, but also, since a digital signature can only be created by one person, to ensure that a person cannot later deny that they furnished the signature.
All of these features can be implemented using IPSec, TLS/SSL or WS Security.
#### IPsec
With IPsec security can be implemented at the network level without having impact on the application implementation or on the data exchange implementation. IPsec supports the implementation of all security capabilities Authentication, Authorization, Confidentiality, Integrity and Nonrepudiation, and normally is used on an end-to-end communication channel that can be used between a supplier and client network link.
IPsec is an end-to-end security scheme operating in the Internet Layer of the Internet Protocol Suite. It can be used protecting data flows between a pair of hosts (host-to-host), between a pair of security gateways (network-to-network), or between a security gateway and a host (network-to-host). IPsec protects any application traffic across an IP network. Applications do not need to be specifically designed to use IPsec.
Definition (IETF - IP Security (IPsec) and Internet Key Exchange (IKE) - http://tools.ietf.org.md/rfc6071): "IPsec (Internet Protocol Security) is a suite of protocols that provides security to Internet communications at the IP layer. The most common current use of IPsec is to provide a Virtual Private Network (VPN), either between two locations (gateway-to-gateway) or between a remote user and an enterprise network (host-to-gateway); it can also provide end-to-end, or host-to-host, security. IPsec is also used by other Internet protocols (e.g., Mobile IP version 6 (MIPv6)) to protect some or all of their traffic. IKE (Internet Key Exchange) is the key negotiation and management protocol that is most commonly used to provide dynamically negotiated and updated keying material for IPsec. IPsec and IKE can be used in conjunction with both IPv4 and IPv6.”
#### TLS/SSL
TLS/SSL supports all security capabilities: Authentication, Authorization, Confidentiality, Integrity and Nonrepudiation. The implementation of TLS/SSL is used over the HTTP protocol using the Web Server application features, is wide used on Internet and has a small impact on a DATA EXCHANGE implementation.
The Transport Layer Security (TLS) / Secure Sockets Layer (SSL) is implemented at the Transport Layer of the Internet Protocol Suite. The use of TLS/SSL must be designed into an application to protect the application protocols. The implementation of SSL over HTTP is commonly called HTTPS.
Definition (IETF - The Transport Layer Security (TLS) Protocol Version 1.2 - http://tools.ietf.org.md/rfc5246 ): "The primary goal of the TLS protocol is to provide privacy and data integrity between two communicating applications. The protocol is composed of two layers: the TLS Record Protocol and the TLS Handshake Protocol. At the lowest level, layered on top of some reliable transport protocol (e.g., TCP [TCP]), is the TLS Record Protocol. The TLS Record Protocol provides connection security that has two basic properties:
- The connection is private. Symmetric cryptography is used for data encryption (e.g., AES [AES], RC4 [SCH], etc.). The keys for this symmetric encryption are generated uniquely for each connection and are based on a secret negotiated by another protocol (such as the TLS Handshake Protocol). The Record Protocol can also be used without encryption.
- The connection is reliable. Message transport includes a message integrity check using a keyed MAC. Secure hash functions (e.g., SHA-1, etc.) are used for MAC computations. The Record Protocol can operate without a MAC, but is generally only used in this mode while another protocol is using the Record Protocol as a transport for negotiating security parameters.
The TLS Record Protocol is used for encapsulation of various higher-level protocols. One such encapsulated protocol, the TLS Handshake Protocol, allows the server and client to authenticate each other and to negotiate an encryption algorithm and cryptographic keys before the application protocol transmits or receives its first byte of data. The TLS Handshake Protocol provides connection security that has three basic properties:
- The peer's identity can be authenticated using asymmetric or public key, cryptography (e.g., RSA [RSA], DSA [DSS], etc.). This authentication can be made optional, but is generally required for at least one of the peers.
- The negotiation of a shared secret is secure: the negotiated secret is unavailable to eavesdroppers, and for any authenticated connection the secret cannot be obtained, even by an attacker who can place himself in the middle of the connection.
- The negotiation is reliable: no attacker can modify the negotiation communication without being detected by the parties to the communication.”
#### WS-Security
As with the other security protocols, WS-Security supports all security capabilities Authentication, Authorization, Confidentiality, Integrity and Nonrepudiation, although further implementations must be used along with WS-Security to achieve the functionality.
The WS-Security is implemented at the Application Layer of the Internet Protocol Suite. The implementation of WS-Security has a higher impact on the implementation because is made on the Web Services implementation, is easy to implement, but forces that both supplier and client to implement the protocol in their Web Services implementation.
Definition (Web Services Security v1.1 - http://www.oasis-open.org/standards#wssv1.1 ): "This specification proposes a standard set of SOAP [SOAP11, SOAP12] extensions that can be used when building secure Web services to implement message content integrity and confidentiality. This specification refers to this set of extensions and modules as the "Web Services Security: SOAP Message Security” or "WSS: SOAP Message Security”.
This specification is flexible and is designed to be used as the basis for securing Web services within a wide variety of security models including PKI, Kerberos, and SSL. Specifically, this specification provides support for multiple security token formats, multiple trust domains, multiple signature formats, and multiple encryption technologies. The token formats and semantics for using these are defined in the associated profile documents.
This specification provides three main mechanisms: ability to send security tokens as part of a message, message integrity, and message confidentiality. These mechanisms by themselves do not provide a complete security solution for Web services. Instead, this specification is a building block that can be used in conjunction with other Web service extensions and higher-level application-specific protocols to accommodate a wide variety of security models and security technologies.
These mechanisms can be used independently (e.g., to pass a security token) or in a tightly coupled manner (e.g., signing and encrypting a message or part of a message and providing a security token or token path associated with the keys used for signing and encryption).”
#### Compression
The DATEX II protocol deals with critical information about traffic and travel data, and the community that use the protocol expect that DATEX II should be a reliable, robust platform that guarantees the exchange of the information independent of the amount of data. The transmission of traffic and travel data (ex. Measures or Elaborated Data) over XML can be in some cases very large, therefore it will take a lot of time or will spend a lot of bandwidth to deliver the information between a supplier and a client.
Using the HTTP protocol compression can help reduce the size of data on the transport. GZip is a standard and can be very easy to implement at the Application Layer of the Internet Protocol Suite by the Web Server supporting the HTTP protocol.
Definition (IETF - GZIP file format specification version 4.3 - http://tools.ietf.org.md/rfc1952): "The purpose of this specification is to define a lossless compressed data format that:
- Is independent of CPU type, operating system, file system, and character set, and hence can be used for interchange;
- Can compress or decompress a data stream (as opposed to a randomly accessible file) to produce another data stream, using only an a priori bounded amount of intermediate storage, and hence can be used in data communications or similar structures such as Unix filters;
- Compresses data with efficiency comparable to the best currently available general-purpose compression methods, and in particular considerably better than the "compress” program;
- Can be implemented readily in a manner not covered by patents, and hence can be practiced freely;
- Is compatible with the file format produced by the current widely used gzip utility, in that conforming decompressors will be able to read data produced by the existing gzip compressor.”
### E - Major Functional Exchange Profile FEP+E for Information Delivery
(informative)
In the following table a list of features available ( Y / N / Optional ) for major specific combination FEP+EP for the Information Delivery Business Scenario are listed. These features and requirement are combined to implement specific exchange environments:
- Pub Sub
- S Pull: Snapshot Pull
- S Push: Snapshot Push
- SP Push: Simple Push
- SF Push: Stateful Push
Features Area
Feature
PubSub support
S Pull
S Push
SP
Push
SF Push
Requirement Name related
Requirement Type
Subscription Contract
Contract
N
N
N
N
N
Subscription
Information
Client profiles
Filter handling
Catalogue
N
N
N
N
N
Catalogue exchange
Information
Session
Session life cycle
Y
N
N
N
Y
Error handling
Communication
Communication
Timeout management
Session
Link Monitoring
Y
N
N
Y
Y
Error handling
Timeout management
Full reliability
Link monitoring and control
Information management
Operating modes
Y
Y
Y
Y
Y
Reference datasets for different versions
Information
Update methods
Y
Y
Y
Y
Y
Full audit trail data delivery (all state changes)
Information
Lifecycle management
Y
N
N
Y
Y
Support for lifecycle management
Information
Data delivery
Data delivery
Y
Y
Y
Y
Y
Extensibility
Information
Delivery/response
Communication
Message sequence
Snapshot data delivery (last known state)
Exchange quality measures (ex. response timestamp)
On occurrence update
Periodic update
Client identification
Security
Supplier identification
Incremental data delivery
Information
Data request
Y
N
N
N
N
Extensibility
Information
Request/response
Communication
Message sequence
Snapshot data delivery (last known state)
Exchange quality measures (ex. response timestamp)
On occurrence update
Periodic update
Client identification
Security
Supplier identification
Large datasets handling
Y
N
N
N
N
Data delivered as soon as possible
Information
Delayed delivery
Multi-part data delivery
Synchronisation
Y
N
N
O
Y
Synchronisation
Information
With state supplier
Communication
Failed data recovery
Self Description
handshake
Y
N
N
N
N
self description
Communication
Security
Y
Y
Y
Y
Y
Security (data)
Security
Integrity
Confidentiality
State the intended recipient
Client authentication
Supplier authentication
Client authorization
Non-repudiation
Compression
Y
Y
Y
Y
Y
Compression
Communication
Communication
Y
Y
Y
Y
Timely responses
Communication
### F - Data Delivery background: stateless and stateful information and information lifecycle management
(informative)
Data related to the state of traffic related information are typically of 2 categories:
- Stateless information / data, i.e. they represent quantitative measurement of some physical evidence, sampled at certain point in time and consists in the last available value for a measure. In case of a situation it can be considered the snapshot of situation evolution that has been sampled at a certain time.
- Stateful information / data, i.e. they represent some information that is considered describing a status of the road that is persistent for some time when observed and this situation can evolve in time and will be updated according to information gathering process.
When Information is observed and/or measured at certain timestamps, this is considered as Sampled Information. In this case Information is sampled and its validity is referred at the sampling time and next sampling time will be considered completely new information.
Figure F.1 – Sampled Information
In other cases Information updates observed can be considered as valid from the time it has been observed till a new observation which can update it. This is the case for instance of a message displayed on VMS observed at any message update time, or a road situation which is structured as a complex set of data combined in Classed and Attributes as in Situation publication.
The latter case can be defined as Stateful Information. Even from Sample Data some processing can be implemented on these data to obtain information which can be considered valid and persistent for the road for a further period as an estimate ( e.g. measured or elaborated information such as individual vehicle or average speed, vehicle flow, road ground temperature or visibility, which values are between specified threshold).
Information gathered at first can be updated and keeps its relevancy to road status for some time until it ends.
Figure F.2 – Stateful Information
### G - Collaborative ITS Services background
(informative)
#### Service Oriented vs. Information Delivery Oriented Information Exchange
The aim of Traffic areal time information exchange among Traffic Information and Traffic Control Centres are:
- to inform the Traffic Control Centre Operators of the situation that is being taken in the near area in order to help evaluate and prevent impact that may affect its competence.
- to request for information processing and delivery of services based on such exchanged information by the Client Centre, in order to support operational decisions and consequent implementation of operations and/or to inform drivers about safety and security behavior for drivers who are approaching a specific reported situation location.
- Via broadcast and personalized Information channels (Radio, Bulletins, Call Centers, RDS-TMC Channel, web, etc.)
- Via Variable Message Signs
The first case is the plain Information Delivery Business Case, in which the only scope is Data Delivery itself and any further processing objective consideration is out of scope. Data are delivered with only request to be received and in most of implementations they are only syntactically checked.
This communication model applies when a center can ignore for its objectives the final usage and processing outcomes which are derived from the information which is exchanged. This communication pattern has been fully addressed and described in Data Delivery communication pattern for DATEX II data exchange specification.
Considering the whole process chain to transfer information gathered from a system to another system, the data delivery section is contained in the chain from the information supplier to the receiver node of a DATEX II System
Figure G.1 - Boundary of DATEX system boundaries in Centres Information Delivery Business case
The only objective of Data delivery is to monitor that information delivered has been received correctly by the Client.
Introducing MMI as Man-Machine Interface i.e. the TCC Management Systems used by the Operator the chain of information among all the systems may be described as follows
Figure G.2 - Boundary of DATEX system boundaries in Centres Information Delivery Business case
Considering this framework, as specified in the latter case mentioned before, we can consider that Information is not exchanged with the simple aim of deliverying it to other centres for their internal usage, but with the scope it will be used at the centre to implement processing and further services to be consumed by other applications and systems.
To activate a processing based on those data information need to be checked and not only Syntactical but also Semanthic errors are relevant to the processing. Furthermore, Check and Processing Results, i.e. a Feedback, is fundamental.
In some use cases distributed processing and services have to be activated as a consequence of the validity of a certain information such as a Traffic Status or a High Impact Condition which is running on the road (e.g. Traffic Element, Road or Weather or Environmental condition). Management of such conditions by the Centres may imply the need for one or more operation to be executed (i.e. services) by several Traffic Management or Service Provider Centres, for instance based on predefined Traffic Mangement Plan which had been elaborated for such conditions. This can happen also in case of extraordinary needs due to unpredictable events occurring in the road network which can affect the road operations (such as major Events and Activities).
In this case a more complex workflows is implemented by the several nodes involved. The outcomes of proposal acknowledging, and operation implementing is needed to all involved nodes to have evidence of ongoing operations.
Figure G.3 - Example of Collaborative ITS Services business case framework
** “Collaborative ITS Services” ** (CIS) explore user requirements and common techniques to address the needs and implement collaborative services by centres and they are based on exchanging information to be processed by other nodes and receiving the processing outcomes (feedback), giving a base to build more sophisticated workflows enabling to coordinate distributed operations among multiple centres.
A ** “Collaboration Workflow” ** may be seen as a composition of one or more sequences of
- Service Request ( based on exchanged Payload )
- Processing Results ( Feedback )
among a pair or more of interoperating nodes.
These "Request and Feedback” brick sequences enable to set up a Workflow, where Application Level rules can be added in very structured configuration management
Figure G.4 - Example of ITS collaborative services Workflow
In this vision DATEX Exchange acts as an Operational tool enabling to take shared decisions and implement and monitor shared actions by the CIS Collaborative Services Pattern which is described in the following chapters.
#### CIS and TMPlan Design
For Traffic Management Plan (TMP) definitions as well as design and operating concepts it is referred to the TMS Deployment Guideline (ref. http://dg.its-platform.eu/DGs2012 )
TMP may be seen in a more general vision as a road network configuration implemented by means of resources because of a scenario which conditions the road network status. The management of a TMP aims to improve the worsened status of the network (Level of Service - LOS) and achieve better global and/or local specific performances, which are based in term of traffic flow enhancement, safety and security performance and pollution reduction.
Figure G.5 describes operating TMP during time having Incidents or Road Conditions which impact on road network level of service, seen as a global indicator. Operating TMP management improves LOS and achieve better performances.
Key
I | incident
T1 | TMP 1
T2 | TMP 2
C | condition
E | end of TMP
Figure G.5 — Network status (LOS) during incidents and conditions with TMP operating on road network
When extending TMP approach description, any option for resource usage across the road network can be seen, such as commanding a Variable Message Sign or controlling a whole section of a Lane Control System as well as traffic signals in urban areas, as a service offered by a road operator or TCC operator to improve the road network performance as specified above.
Based on experience about road conditions and occurring situation frequency, traffic engineers may design solutions to cope with problems that frequently arise in road operation. A CIS design can be depicted as generalizing the TMP design expressed in EasyWay TMS DG, as shown in Figure G.6.
It starts with the description of the business scenario, i.e. the road incidents or conditions which impact the road network to be managed, then by defining the problem to which it is related and which has to be solved by the resources owned or managed by several organisations. After a feasibility study and subsequent discussion traffic engineers define a CIS (TMP) design to tackle the problem, with the resource configuration options to be used. Sometimes more than one configuration is possible to achieve the same result and this general result is named as strategy. All the possible measures to realise a strategy are inventoried. That CIS design then defines a CIS Activation Contract which states all the details and rules to exchange and make decision to operate CIS (TMP).
Figure G.6 — CIS (TMP) analysis, design, implementation and operation phases
At real-time, a service request for CIS implementation will be exchanged, as well as feedbacks, to set up the predefined configuration of needed resources, i.e. strategy activation and single actions referred as well as the resource disposal by an organisation.
Extending TMP by the CIS concept any resource configuration (VMS, LCS, CCTV, traffic signals, etc) can be meant as a specific request for service to be activated by another centre.
Strategies and relative actions are concepts defined in Deployment Guidelines, triggering conditions mean the road situation or data which requires the need for operating a TMP or in a more general way CIS.
During operation, requests for services are usually to be validated by the involved centre operators, so a standard operation to implement CIS is based on 2 phases: CIS agreement and CIS execution; each of them is implemented by a specific service request and the execution is achieved after agreement has been done. In case the agreement is not achieved for a known reason, which can and should be fed back, the requester should evaluate how to deal with and possibly ask for a different alternative CIS (as shown in Figure G.6) or should evaluate the condition at a higher decisional level.
Figure G.7 — Two-phase CIS operation
In a simpler service request, such as VMS management for only information purposes, the CIS request may still be valid, even if it will be implemented only by some of the centres involved, and it will itself be operating the same way if another centre does not execute such a request. In this case the agreement phase can be avoided and one phase execution CIS can be implemented: one of these cases is VMS setting for traffic condition information, i.e. when there is no need for coordinated management but only for information needs, any VMS setting implemented will improve the global service to road users, and no other management is needed in case, for instance, a VMS cannot represent this information due to a fault or because higher priority information is displayed on the requested VMS.
Figure G.8 — CIS implementation workflow with a requester centre and implementer centres
This can be seen in application of this workflow management for Traffic Management Plan.
Figure G.9 — TMP implementation phase description
Figure G.10 — Single TMP measure implementation via agreement and implementation phases
#### CIS Implementation Patterns
As seen in the previous paragraphs Collaborative ITS Services in this presentation is the availability, usage and shared management of ITS services implemented by centres distributed along the road network.
Figure G.11 depicts a set of connected centres, each of which exposes several services.
These services can be combined to implement CIS (through TMP) after the request of a specific requester centre (in red).
Figure G.11 — CIS as shared distributed services availability and usage among centres
In real life each service is realised by its own customised interface, using each one proprietary parameters, datatypes, syntactical rules and semantic definitions. Each TCC ITS system implements many services that could even be accessed remotely to enable other centres to use them after agreement, for real-time services. Using these proprietary legacy interfaces, and even when implemented via standard interfaces as web services adjustment and agreement are needed among centres to set appropriate parameters for defining parameters values and semantics.
In the domain of Centre-to-Centre exchange, data exchange technology is used to standardise data and give shared syntactical check rules and semantic understanding, as well as common handshaking and behaviour for data exchange patterns and communication errors or network failures management.
In this framework CIS data exchange can be seen as the usage of exchange nodes as a data exchange interface to convey information to enable and control services, adapting the legacy protocols of individual clients and server legacy systems, and wrapping individual node services, i.e. nodes acting as gateways which wrap the heterogeneity of several languages, and national legacy systems enabling interoperability and common strategies achievement.
Figure G.12 — CIS by data exchange: nodes act as gateways wrapping individual centre complexity and adapting semantics to a standardised language and interface
A service interface may be realised exposing a “common general” Collaborative ITS Service interface through which a service may be invoked by the node of the actual TCC server (ITS system) and payload(s) can be conveyed which will be processed by the invoked service.
Figure G.13 — CIS by data exchange: implementation through “web services” call
First option for a service method interface:
That could be used with conventional shared names services like"TMPlanService” or "Feedback”
Further Option use for Request CIService passing the requested Service name as data in the Request Payload and for Feedback CISFeedback.
Obviously requesting for a service via the exchange node is not directly invoking the service on that ITS system but abstracting the operation of invoking service and demanding it through the exchange node, having information or data parameters required for the service, adapted by the exchange node client gateway to the specific service parameters of the specific ITS system.
Thus invoking a service through exchange can also be equivalent as conveying one or more exchange payloads and invoking specific services through their “ServiceName” and this means in this case information delivery pattern conveying information and data through exchange nodes. This implies that information delivery of service request publication could be used to actually request for services so the same interface and WS notification can fully be used to convey payloads among exchange nodes for new service requests and service scenario exchanged payloads.
Examples:
- Requesting one or more centres to implement VMS Message sending situation record and asking it to be processed to address VMS messages based on predefined rules.
- Requesting one or more centres to implement on some specific VMS specific messages explicitly conveyed through VMS Publication.
- Requesting one or more centres to implement a specific Predefined TMPlan, sending a TMPlan Publication (or a more general CIS through CIS Service request Publication).
In the other direction, there is also the need for the node requesting the service to be informed about the success or failure of the service request, i.e. a feedback, which also is information that can be exchanged using exchange nodes wrapped in a feedback publication.
Again, the feedback can be seen as a return information from a CIS invocation or simply as a payload itself exchanged back from the node executing the service.
As seen in G.1 showing the sequence diagrams and all actors to be considered when a service is to be implemented on exchange data, to have the overall feedback of the service request implies the whole process to implement the Service needs to be completed before receiving such feedback. In this case service invocation can only be synchronous, and some IT resources allocated by the service request will be locked while waiting for such process to be completed, and further agreement phase normally implies human operator to take some manual actions and decisions.
During the service implementing phase some intermediate processing results could be notified to the requester, before the overall result is achieved, giving evidence of progressive processing phase. It is better to quickly feed the request back about only syntactical check and send other intermediate and final feedbacks based on the progressive evolution in the processing phases.
The situation can be expressed by the following Figure G.14:
Figure G.14 — Intermediate and overall processing feedback in a multiphase implementation service
#### Competition policies
A further question to consider prior to thinking about any implementation/PSM solution for managing Collaborative ITS Services, is competition policies which run and regulate the business cases.
Whenever a service is designed as a resource usage to some objective which is active and shared or notified by a service requester to a service implementer, it is necessary to think about this kind of resource and how it can be managed if some other requests get concomitantly with the current one which is first known.
Whenever there is a need to allocate the same resource to different usages and use cases consider competition policies to observe are to consider. There are two main policies:
- First Come - First Served (FIFO) policy
Request for services may be considered as they come, and there is an implicit lock of resources for booking, the resource is granted to the first request received.
An example of such is about car or lorry parks booking in a specific parking area, like secure parking areas for HGV. It implies guaranties for the booked resource and the payment of a fee to book, lost or partially refunded if the resource is not used. There may also be policies to release resources after a timeout period in case they are not used and the resource release is allowed with a partial or total refund within a certain amount of time.
In Figure G.15 the use case is depicted in which a request can be granted by a booking and payment service provider which manages communication to parking service providers implementing the locking and releasing of resources after payment guarantees.
Figure G.15 — CIS schema for booking parking resources
- Conditional priority
Either when considering services as VMS displaying information messages about road situations or Traffic Management Plans the rule to manage priority is different as a new situation may arise that is much more relevant to be displayed on VMS, or to be managed by TCC with a different network operation set leading to a completely different scenario and TMP management.
This conditional priority policy is considered when several service requests are received subsequently and a more recent one may have higher urgency, so that the first request is rejected or its cancellation/termination requested after a first approval and the higher-ranked TMP request due to a more impacting situation needs to be served.
Depending on the competition policy
First Come First Served: distributed transactions protocols are needed to ensure consistency and avoid conflicts. The field of application is related to payment and booking of resources which will be allocated and could be released under precise conditions, such as:
Parking facilities;
- Tunnel slot booking;
- Alternative path allocation per vehicle, for dynamic rerouting;
Special path prescription / Specific itinerary for HGV or abnormal indivisible goods.
Conditional priority: several decision levels can be implied, as well as an operator decision based on rules or Decision Aiding System may be needed to evaluate priority and solve conflicts. In some cases, conflicts are managed at a higher decisional level. As a requirement need for exchange there is a need to manage workflows enabling decision making and resuming.
### H - Collaborative ITS Services Exchange Pattern
(informative)
Based on data delivery model and Annex G and after the previously reported consideration one may consider that several choices exist for the service request and feedback implementation (no atomic transaction needed).
It is fully based on information delivery:
- CIS service request publication notified to CIS involved partner by requester node;
- CIS feedback publication notified to service requester by CIS involved partners.
This pattern implies 2 one-way communications that could be based on data delivery business scenario PIM:
- Agreement, when needed, and execution delivered from CIS requester to implied nodes;
- Feedback, other way round, from implied nodes to CIS requester.
This implementation of CIS exchange can be implemented in currently available data delivery FEP and exchange pattern platform based on modelling service requests and feedback information as payload content.
### I - WSDL definition
(informative)
#### General WSDL definition
In WSDL the normative part shall apply only to method names and input and output message type definition: URLs path and internal variable names definition may vary for any implementation.
#### Snapshot Pull SOAP WSDL definition
The machine readable file for this specification can be downloaded as SnapshotPull.wsdl
#### Snapshot Push SOAP WSDL definition
The machine readable file for this specification can be downloaded as SnapshotPush.wsdl
#### Simple Push SOAP WSDL definition
The machine readable file for this specification can be downloaded as SimplePush.wsdl
#### Stateful Push SOAP WSDL definition
The machine readable file for this specification can be downloaded as StatefulPush.wsdl
#### Simple CIS SOAP WSDL definition
The machine readable file for this specification can be downloaded as SimpleCIS.wsdl
This WSDL implements both Service Requester and Service Provider WSDL interface, which can be implemented separately on each agent interface.
#### Stateful CIS WSDL definition
The machine readable file for this specification can be downloaded as StatefulCIS.wsdl as StatefulCIS.wsdl
This WSDL implements both Service Requester and Service Provider WSDL interface, which can be implemented separately on each agent interface.
#### Full Exchange WSDL definition
Despite all services are implemented in each FEP+EP defined pattern, it's possible to combine Push, Pull Services as well as CIS Service Request and Feedback services in the same webserver for a node acting both as a client and as provider. For this purpose a "FULL Exchange" WSDL interface definition is provided as a merging of all methods implemented in the various FEP+EP pattern. It is intended for management of exchange information FEP + EP and implementation of their features, the specification which are defined at each single FEP+EP pattern applies.
The machine readable file for the extended union of all FEP+EP implementation described in this document can be downloaded as Full Exchange WSDL
### J - XML Schemas for exchange related content
(normative)
#### Overall presentation
Based on Basic Exchange Data Model and data dictionary defined in ANNEX C of CEN/ISO TS 19468, the information related to exchange is modelled in a Message Container which allows for inclusion
- Payload Publication content: the payload which is modelled in each domain, e.g. DATEX II payload content
- Exchange Information: information related to describe the exchange environment and its behaviour as PIM and PSM, with includes all data which enables the exchange features implementation.
- Information Management: class and attributes which enable the management of information such as lifecycle management
- CIS Information: classes and attributes which enable a service provider to implement services as requested by a service requester as modelled in collaborative ITS service description and PIM.
In the scope of the present work the Basic Exchange Data Model has been taken as input and based on DATEX II methodology and tools XML Schemas had been derived to implement the Basic Exchange Data Model in its equivalent CEN EN 16157 compliant schemas to enable data delivery and collaborative ITS services based on DATEX II EN 16157 family standard.
#### Message Container
The machine readable file for this specification can be downloaded as DATEXII_3_MessageContainer.xsd
#### Exchange Information XML schema definition
The machine readable file for this specification can be downloaded as DATEXII_3_ExchangeInformation.xsd
#### Information Management XML schema definition
The machine readable file for this specification can be downloaded as DATEXII_3_InformationManagement.xsd
#### CIS Information XML schema definition
The machine readable file for this specification can be downloaded as DATEXII_3_CISInformation.xsd
### K - "Snapshot Pull with simple http server" profile definition
(normative)
#### Overall presentation
This profile is compliant to Snapshot Pull FEP+EP PIM, it is derived from DATEX II version 2.0 Exchange Specification and it states all requirements to implement Snapshot Pull by simple http server profile, i.e. implemented by pure http/get, within the following clauses which implement all PIM specified features.
Snapshot Pull FEP+EP PIM defines the "pull message" received to be a "MessageContainer" according to Basic Exchange Data Model defined in Exchange 2020 PIM Annex C, which is implemented in XSD schema defined in this document Annex B.
Despite this rule, which always applies to Snapshot Pull implemented by WSDL, some implementation of "Snapshot Pull with simple http server" may consider to implement as delivery only the "PayloadPublication" without wrapping it in a "MessageContainer", this is assumed implicititely defined by subscription agreement among client and suppliers.
This clause uses the term "Message" to refer either a "Message Container" or a single "Payload Publication".
#### Describing payload and interfaces
The profile can handle different information to be delivered (such as different payloads), named information products by assigning a specific URL (potentially plus access credentials) per information product.
The information product itself is denoted by all but one path segments in the URL, while the ‘filename’ (i.e. the middle path segment) is “content.xml” per definition. This convention was introduced to allow the definition of related meta-data for this information product in other files in the same directory.
Payload data for Information products SHALL be denoted by a URL according to the following convention:
d2lcp_infop = "http://" host [":" port] infop_path "/content.xml" ["?" query]
where “info path” is a “path” component as specified in section 3.3 of [RFC 2396], but excluding the last path segment.
The end of this clause may sound awkward. It strives at maintaining all the regulations of the URI RFC, thus not constraining URLs for information products, but incorporating the need to have the final path element (the ‘filename’) being “content.xml” by convention.
To support authentication, the servers has to provide the credentials required to perform authentication for any particular information product.
Server requiring authentication MUST provide the required access credentials for BASIC authentication (i.e. user name & password) together with the URL for the Information Product.
#### Metadata for link management
Scenarios exist where the “If-Modified-Since” mechanism is not preferred to avoid redundant downloads. This will happen if the server provides information products by updating files on a standard, file-based www server (like Apache or Microsoft Internet Information Servers). In this option, the server would have two possible update regimes:
- Periodical update of the information product’s payload file independent from any changes in the data.
- Update the information product’s payload file on demand, when changes relevant to this product have occurred in the server’s database.
With updating regime 1, the file based www server would cyclically send the file content to the clients, as he will derive the last-modified value from the file modification times. So the client would receive redundant downloads!
Implementation based upon standard www servers and files as information products SHOULD update information product payload files only when their traffic domain content has changed.
This means that the file may stay unmodified for some time after an update. This regime has one serious drawback: the Client will not be able to determine whether the file remains unchanged because the (road) traffic situation is stable or because the backend server system itself (not the WWW server) is not operating properly. In fact, the response of the (intermediate) WWW system does not have the quality of an end-to-end acknowledgement.
This information is given in a small XML document that is periodically updated, even if the (potentially huge) content file is unchanged. The file is required to refer to an XML Schema that contains an Element called MetaData as root element with two required attributes of type xsd:dateTime called confirmationTime and confirmedTime, with confirmationTime giving the time the acknowledgement was created and confirmedTime giving a value equal to the value the Last-Modified header field would have if the payload file (i.e. content.xml) had been requested.
The following XML Schema gives a valid example:
The acknowledgement file shall be put in the information product’s directory, besides the content.xml file containing the payload, with a filename of metadata.xml. A sample file for the schema above would be:
This leads to the following specifications:
Implementation based upon standard www servers and files as information products SHOULD provide a cyclically updated acknowledgement, accessible as:
- D2LCP_infop_ack = "http:" "//" host [ ":" port ] infop_path "/metadata.xml" ["?" query]
- If an acknowledgement is provided, it SHALL be a well-formed XML document with a XML Schema reference. The acknowledgement SHALL validate successfully against the referenced XML Schema.
- The XML Schema referenced by an acknowledgement SHALL contain a root element called “MetaData”. This element SHALL contain two attributes, one named “confirmationTime” and one named “confirmedTime”, both of type “xsd:dateTime”.
- If used, acknowledgements shall be updated cyclically, with best effort update cycle, but not less than once every three minutes.
- An acknowledgement update SHALL indicate that the data server is operating properly at the time it is generated and that the content of that payload file – as last updated with modification time givenin the “confirmedTime” attribute of the “MetaData” – element iscurrently still valid.
- The “confirmationTime” attribute of the “MetaData” element SHALL contain the current time when an acknowledgement is updated.
- The “confirmedTime” attribute of the “MetaData” element SHALL contain the same value that a HTTP RESPONSE to an authorised HTTP REQUEST issued at the time of writing the acknowledgement would contain in the “Last-Modified” header field.
- A server that is based upon standard WWW servers and files as information products SHALL indicate in the subscription negotiation process whether the acknowledgement option is supported.
- Clients SHOULD use the acknowledgement option – if provided – to determine whether payload download is required.
#### Use of HTTP
This profile exchange uses HTTP Request (GET or POST) / Response dialogs to convey payload and status data from the Supplier to the Client. Note though that this profile supports POST requests only for interoperability with the Web services profile based on SOAP over HTTP exchange Information potentially included in the body of an HTTP POST request, is not processed.
This section stipulates how to use HTTP options for the Suppliers and the Clients of this profile.
#### Basic request / response pattern
- Suppliers and Clients SHALL use the HTTP/1.1 protocol. Clients and Suppliers shall fully comply with the HTTP/1.1 protocol specification in RFC 2616, as of June 1999.
This protocol is based upon a request / response pattern, where the request can take one of several possible forms, among them the GET and POST methods for retrieving data. The GET and POST differ essentially in how the parameters of a request can be conveyed to the Supplier. While these parameters are conveyed as part of the URL in the HTTP GET request, the POST request allows specifying an “entity” (i.e. a message body) that contains these parameters, thus enabling less restricted parameters. POST requests were originally intended for server upload functionality.
As the specification foresees no complex request parameters, HTTP GET requests are preferred. Since other exchange systems sometimes require HTTP POST requests, they are also accepted. Nevertheless, it is not the intention to establish another exchange protocol layer on top of HTTP, and thus systems are not obliged to process the content of the body of an HTTP POST request.
Note
Systems MAY decide not to process the body of HTTP POST requests!
Clients SHALL use the HTTP GET or POST method of the HTTP REQUEST message to request data from the Supplier
The HTTP GET or POST request is served by the Supplier by generating an HTTP response message. The "Message" conveyed in this response is passed in the entity-body.
Note
It should be noted thought that for interoperability reasons (in particular with Web Services profile Clients that require a SOAP wrapper around the XML payload) the profile does not stipulate the "Payload Publication" or the "Message Container" to be the root element of the XML content.
Suppliers SHALL use an HTTP RESPONSE message to respond to requests. If applicable, one "Message" is contained in the entity-body.
Suppliers SHALL NOT respond to HTTP REQUEST messages using the GET or POST methods by responding with 405 (Method Not Allowed) or 501 (Not Implemented) return codes.
All communication is initiated by the client. Any data flow from supplier to client can only happen as the Supplier’s response to a Client’s request. When requesting data, the Client is not able to know whether the data he would receive would be exactly the same as the one he had received in response to his last request. This would lead to a serious amount of redundant network traffic, with potential undesired impact on communication charges and supplier/client workload. HTTP supports avoiding this by letting the Client specify the modification time of the last received update of a resource in an HTTP header field (If-Modified-Since). If no newer data is available, the response message will consist only of a header without an entity, stating that no new data is available. Clients are therefore recommended to set this header field in case they already hold reasonably recent information from the accessed URL.
Suppliers shall set the ‘Last-Modified’ header field in HTTP RESPONSE messages that provide payload data (response code 200) to the value that the information product behind the URL was last updated.
Clients may set the ‘If-Modified-Since’ header field in all HTTP REQUEST messages if they already hold a consistent set of data from a particular URL in their database and the last modification time of that data is known from the ‘Last-Modified’ header field of the HTTP header of the HTTP RESPONSE message within which the payload data was received.
It shall be understood that the semantics of the timestamps used within the If-Modified-Since header field are calculated in the server. Therefore, times generated by the Client according to his own system clock may not be used here but must be filled using the content of the Last-Modified header field of the most recently received HTTP RESPONSE message. If Clients connect to a resource for the first time or want to resynchronise, they simply don’t set this header field.
When setting the ‘If-Modified-Since’ header field, the Client SHALL copy the value of the 'Last-Modified' header field received within the last successful HTTP RESPONSE containing a message (response code 200) into this field.
Suppliers SHOULD provide XML coded DATEX II payload as “text/xml” media type. Suppliers SHOULD state the used character set via the “charset” parameter; Suppliers SHOULD use the UTF-8 character set, i.e. the “Content-Type” response-header field SHOULD state “text/xml; charset=utf-8”.
Character sets, media types, etc. are a vast area that is notoriously underestimated as a source of potential interoperability problems. This clause aims at recommending the most widely used set of options, namely the use of the UTF-8 character set for XML payload. The “text/xml” is preferred to “application/xml” following a recommendation in RFC 3023 (“If an XML document -- that is, the unprocessed, source XML document -- is readable by casual users, text/xml is preferable to application/xml.”). Although in principle the profile is solely devoted to B2B communication, readability of the exchange payload has often proved to be beneficial for testing and educational purposes.
It should be noted that omitting the “charset” attribute in HTTP/1.1 for “text/*” type content implies the use of “ISO-8859-1” which is different from the UTF family (UTF-8, UTF-16) that are the minimum requirement for XML processors, and can thus be seen as the de-facto standard for XML. Consequently, sending typical XML payload like this:
If “text/xml” without parameter would be sent, HTTP/1.1 would be violated.
Note
Quote from RFC 2616: “When no explicit charset parameter is provided by the sender, media subtypes of the "text" type are defined to have a default charset value of "ISO-8859-1" when received via HTTP. Data in character sets other than "ISO-8859-1" or its subsets MUST be labelled with an appropriate charset value.”
Clients MUST accept “identity” content-coding; Clients SHOULD (and if they do, prefer to) accept “gzip” content-coding; Clients MAY accept other “content-coding” values registered by the Internet Assigned Numbers Authority (IANA) in their content-coding registry as long as they also accept “identity” and “gzip” content-coding.
When including an “Accept-Encoding” request-header field in an HTTP REQUEST message, the Client MUST NOT exclude acceptance of “identity” content-coding.
- Suppliers MUST provide “identity” content-coding of the payload; Suppliers SHOULD provide “gzip” content-coding of the payload; Suppliers MAY provide other “content-coding” values registered by the Internet Assigned Numbers Authority (IANA) in their content-coding registry as long as they also provide “identity” and “gzip” content-coding.
This set of clauses essentially ensures that a confused situation where the Supplier is not able to provide payload in a content-coding that the client understands can not exist, as all suppliers are enforced to support “identity” (which means unmodified text/xml content) content-coding, and clients are enforced to understand this content-coding.
Furthermore, these clauses include a policy that recommends the use of compression and ensures that compression is always interoperable because it requires all clients/suppliers that do support compression to support “gzip” at least as an option. This means that:
- All client/supplier interaction will work at least with “identity”
- Clients/Suppliers supporting compression will always be able to agree on “gzip”
- Clients can request preferred other compression (“deflate” or “compress”), and Suppliers will respond accordingly if they support these content-codings.
Implementers should be aware that non-transparent web caches may perform media type transformations on behalf of their clients. Thus Client running over such a cache might notice that compressed response content is automatically decompressed. However this is only problematic if there is a low bandwidth connection between the client and the cache, such as a dial up access point. If a service has a significant number of such users then the addition of the no-transform directive to the Cache-Control header field of the generated responses should be considered. For more details on the use of the Cache-Control field, please consult Section 14.9 of RFC 2616.
Servers may use the ‘no-transform’ directive in the ‘Cache-Control’ header field to avoid non-transparent caches from sending non-compressed content.
#### Authentication
Authentication is supported, i.e. only users with explicit permission are allowed to download payload data. The required access credentials have to be provided to the Client as part of the outcome of the DATEX II subscription creation with the content Supplier, which is here an offline process. The specifications make use of the simplest and most widely spread authentication scheme for HTTP, i.e. BASIC authentication.
Note
This scheme is not seen as sufficiently strong for commercial strength business and safety relevant application, as the password is not encrypted during transmission. Applications that fit into this description will either have to use other exchange profiles or they will need to establish a sufficiently secure transport layer below DATEX II Exchange.
The Client receives a username and password together with a URL which identifies a specific publication from the server. During access, the Client then builds a single string from this (“\<username>:\<password>”) and encodes it according to base64 encoding rules. The result is put into the Authorization header field of the HTTP REQUEST message.
Clients SHOULD fill access credentials they MAY have received during the subscription negotiation process into the ‘Authorization’ header field of the HTTP REQUEST message.
Server providing access credentials (username & password) during the subscription negotiation phase MAY respond with response code 401 (Unauthorized) to HTTP REQUESTS that do not contain valid access credentials in the ‘Authorization’ header field
#### Additional rules
The regulations in the previous section are a clarification on how to use standard features of HTTP/1.1 according to RFC2616.
This sub-clause contains additional regulations that go beyond ‘pure’ HTTP. Anyway, the regulations presented so far have to be seen as clarifications on top of RFC2616. They are compliant with the standard and have to be used in conjunction with the standard itself. This principle holds especially for the handling of HTTP return codes. The following clause summarises the main return codes as used in connections and refers to the standard for the handling of further codes.
Servers SHALL produce and Clients SHALL process the following return codes:
- 200 (OK), in responses carrying payload,
- 304 (Not Modified), if no payload is sent because of the specification in the ‘If-Modified-Since’ header,
- 503 (Service Unavailable), if an active HTTP server is disconnected from the content feed,
- 404 (Not Found), if a file-based HTTP server does not have a proper payload document stored in the place associated to the URL.
Servers SHOULD produce and Clients SHOULD process the following return codes:
- 401 (Unauthorised), if authentication is required but not presented in the request, or if invalid authentication is presented in the request,
- 403 (Forbidden), if the requested operation is not successful for any other reason.
Servers & Client SHALL apply an RFC2616 compliant regime for producing / handling all other return code.
Go back to the previous page
