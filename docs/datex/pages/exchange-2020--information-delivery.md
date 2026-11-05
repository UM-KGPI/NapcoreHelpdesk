url: https://docs.datex2.eu/v3.7/exchange-2020/information-delivery/
title: Information Delivery FEP + EP PIM and SOAP WS PSM definition

## Information Delivery FEP + EP PIM and SOAP WS PSM definition
The following sections will describe Information Delivery Exchange Pattern for chosen Functional Exchange profiles.
The SOAP Web Services PSM related clauses express requirements for implementation of Data Delivery business scenarios FEP+EP which are fully described at PIM level by referencing their exchange agent and relative interfaces.
Note
A system can be both a client and a supplier of another system simultaneously, defining multiple separated exchange contexts (e.g., set of exchange nodes defined to exchange information in a specific business scenario with a specified EP+FEP).
### Snapshot Pull
The “Snapshot Pull” EP+FEP at PIM level is based on information retrieval by a client from a supplier which delivers a snapshot of information i.e., all currently available information content, to the client. It can be implemented in several platforms: some examples are XML retrieval of generated XML files by http/get, or supplier exposing a SOAP Web Service method (e.g., named "PULL"), from which currently available data is retrieved by the client.
This “Snapshot Pull” does not manage session life cycle and link monitoring requirements, as well as synchronisation. This feature and related requirements are not considered in this pattern, synchronisation is not needed as implicit when delivering snapshots of currently available information content.
To describe the Snapshot Pull EP+FEP at PIM level all features are described in a general abstract format, independently from the specific technology platform this model will be implemented with (e.g. http/get XML, WebService).
Features Area | Feature | Snapshot Pull implemented
Subscription Contract | Contract | N
Catalogue | N
Session | Session life cycle | N
Link Monitoring | N
Information management | Operating modes | Periodic or On Occurrence (i.e. Triggered by Client Condition)
Update methods | Snapshot
Lifecycle management | Y, based on snapshot: new and updated content delivered, outdated data not delivered.
Data delivery | Data delivery | Y
Data request | N
Large datasets handling | N
Synchronisation | Y
Self-Description | Handshake | N
Communication | Security | To be defined at PSM Level
Compression | To be defined at PSM Level
Communication | To be defined at PSM Level
#### Exchange pattern messages definition
The information delivery business scenario description and definition states that data exchange is needed to align the information kept by the supplier system into the client system. For this purpose, an exchange systems is used which provides tools enabling messages generation and their transfer between supplier and client.
Figure: Snapshot Pull exchange actors
The “Snapshot Pull” exchange pattern is described in the following subclauses.
#### Exchange pattern definition
In a snapshot pull contex the supplier exchange system provides a mechanism to retrieve currently available and valid data (i.e., a snapshot of information) from action taken at client side, which will invoke this specific mechanism offered by the supplier.
In the context of the "Snapshot Pull" FEP +EP framework, to enable interoperability among client and supplier, all rules defined in this clause apply.
A snapshot pull supplier exchange system shall realise a snapshot pull supplier interface wich provides a " " method which implements the snapshot pull mechanism.
A snapshot pull client exchange system shall realise a snapshot pull client interface which invokes the "pullSnapshotData" Method provided by the snapshot pull supplier interface to retrieve snapshot data.
The next figure shows the communication diagram for Snapshot Pull FEP + EP.
In this FEP+EP framework the client “pulls” messages from the supplier.
The client shall deliver in the pull request no information to the supplier.
The Supplier shall retun the client pull request by delivering a "MessageContainer" information which includes ExchangeInformation.
Note
This return message is available to bring some information from the client to the supplier e.g., exchange information, which may be used for any further exchange features implementations or application-level checks or processing which are out of scope of this FEP+EP specification.
Figure: Snapshot Pull exchange subsystems, interface interactions and methods
The client takes the initiative to retrieve the data based on application-level requirements which determine the needed exchange operating mode (e.g., on occurrence, condition triggered or periodic).
#### Relevant exchange information in exchange data model
No exchange information is needed in this pattern to implement data delivery features. Nevertheless "Basic Exchange Data Model" has been provided to allow the implementation to deliver more than one payload content on the same message and further information to allow managing extra features not required by the Snapshot Pull exchange.
A “MessageContainer” instance should be retrieved using the basic exchange data model as reported in the previous figure, alternatively a payload may be retrieved without any further information.
Information related to Exchange that should be managed to make application development easier are fully described in basic exchange data model.
Exchange Context information related are:
- Supplier related Information
- Requirement: Supplier identification.
Dynamic Information information related are:
- Exchange DynamicInformation (provided both by the client and the supplier) wraps information such as exchangeStatus ("online", "offline", "undefined", etc.)
- Message Generation timestamp information
- Requirement: reliable Information.
#### Exchange Messages
- Payload Message
- Payload messages should be delivered wrapped into a container (see Basic Exchange Data Model ) with Exchange data.
- Payload Messages contain Payload Update Timestamp which may be used to understand when payload has been created/updated for error management and processing saving.
#### State Diagrams
State diagram are not needed and not developed for stateless FEP+EP as Snapshot Pull.
#### Features implementation description
This subclause provides a description and the corresponding specification for each feature identified in the context diagram, according to the Snapshot Pull exchange architecture. The following features are specified:
- Subscription contract
- Subscription (also known as session)
- Information management
- Data delivery
- Communication/protocol
#### Subscription contract
Contract
Managed offline, not automated. It assumes information for controls to be implemented in client to assess the identity of supplier and authenticate the supplier request in message exchange.
Catalogue
Managed offline, not automated.
#### Session
Session life cycle
No session is managed for the current EP+FEP.
Link monitoring
Link monitoring is not managed for the current EP+FEP.
#### Information management
Operating modes
Available operating mode for client Pull is Periodic, or On Occurrence (i.e., a condition triggered based on client). Pull-exchange based on client-side conditions.
Update methods
Available update method is Snapshot i.e., retrieval of only currently valid data.
Life cycle management
Currently available information is included in the payload at a supplier system to prepare message delivery. It can be done at time-out on a cycle basis or at specific triggering condition as “data updated” condition.
For life cycle management information, a snapshot includes all active information, outdated information is not delivered in content.
For sampled information, the snapshot information contains last sampled data available at supplier site.
Whenever a condition is raised the supplier system triggers it to the supplier to manage the creation of a payload pull delivery message (see figure below).
Figure: Snapshot Pull Payload delivery creation: information management at supplier side
Information management for Snapshot Pull at client side is implemented as follows: when a client gets a snapshot of the last updated/created items it includes all valide active information: information which had been delivered and which is not available in the last delivered payload shall not be considere after last devlivery, i.e. it had been invalidated either as closed or cancelled information.
#### Data delivery
Data delivery
The sequence diagram for data delivery is as follows in the next figure:
Figure: Snapshot Pull sequence diagram for data retrieval: implicit data delivery
When a pullSnapshotData request is triggered from the client to the interface method on supplier SnapshotPull interface, the corresponding snapshot payload(s) available shall be delivered as return message by the supplier enclosed in a MessageContainer.
Data request
Not implemented in this pattern.
Large datasets handling
Not described in this pattern at PIM level (it may be implemented at PSM level as optimisation – see 6.3.8).
Synchronisation
Implicit synchronisation is available as only currently available elements are retrieved by Snapshot Pull.
#### Self-description**
Handshake is not available.
#### Communication
Communication feature are implemented at PSM level, they are relevant for the specific platform chosen on which the exchange pattern will be implemented (e.g. http/XML, Web Services SOAP, REST, etc.).
#### General optimisation issues
Some exchange pattern features of any context diagrams features groups (e.g. information management, data delivery etc.) allow the implementation of general optimisation such as processing saving and bandwith.
Payload timestamp information is available for client-side processing optimisation made at the application level.
Pull message may be generated for all clients reducing processing resources at the supplier-side.
No extra optimisation issues are considered in this EP+FEP.
#### Snapshot Pull SOAP webservices PSM definition
The "Snapshot Pull" SOAP web services implementation is defined according to the "Snapshot Pull" FEP + EP PIM description which is described at Snapshot Pull Section of Exchange 2020 PIM, where "Snapshot Pull" exchange system functional characteristics and features implementation are fully described.
In the "Snapshot Pull" SOAP webservices exchange interface, the SOAP WSDL supplier method to implement pullSnapshotData shall be the WSDL method named "pullSnapshotData" which shall not require any input and shall return a "MessageContainer" information XML message data structure.
Messages are implemented by SOAP protocol adding SOAP envelope information. The corresponding WSDL file can be downloaded.
Specific xsd definition profiled for the Snapshot Pull FEP+EP can be downloaded.
Note
Full model xsd definitions for Basic Exchange Data Model MessageContainer can be downloaded, however FEP+EP profiled xsd are strongly suggested to reduce data redundancy and enable clearer data exchange to implement.
An alternative implementation of Snapshot Pull is the "Snapshot Pull with simple http server” profile definition which specification are described here
### Snapshot Push
The “Snapshot Push” exchange pattern / FEP at PIM level is based on pushing information by the supplier to the client delivering a snapshot of information, i.e. all currently available information content, to the client. This exchange pattern can be implemented in several platforms: some examples are XML delivering of generated XML files by http/post, or a client exposing a SOAP web service method (e.g. named "PUSH") when currently available data can be sent by the supplier to the client.
This “Snapshot Push” does not manage session life cycle and link monitoring requirements, as well as synchronisation, these features and related requirements are not considered in this pattern. Synchronisation is not needed as implicit by snapshot delivering of currently available information content.
To describe Snapshot Push exchange pattern/FEP at PIM level all features are described in a general abstract format, independently from the specific technology platform in which this model will be implemented (e.g. http/get XML, WebService).
Features Area | Feature | Snapshot Push implemented
Subscription Contract | Contract | N
Catalogue | N
Session | Session life cycle | N
Link Monitoring | N
Information management | Operating modes | Periodic or On Occurrence (i.e. Triggered by Supplier Condition)
Update methods | Snapshot
Lifecycle management | Y, based on snapshot: new and updated content delivered, outdated data not delivered.
Data delivery | Data delivery | Y
Data request | N
Large datasets handling | N
Synchronisation | Y
Self-Description | handshake | N
Communication | Security | To be defined at PSM Level
Compression | To be defined at PSM Level
Communication | To be defined at PSM Level
#### Exchange pattern messages definition
The information delivery business scenario description and definition imply that data exchange is needed to align the information kept by the supplier system into the client system; for this purpose, an exchange system is used which provides tools enabling message generation and their transfer between supplier and client (see the following figure).
Figure: Snapshot Push exchange actors
The “Snapshot Push” exchange pattern is described by the following subclauses.
#### Basic exchange pattern
In a snapshot push context the client provides a mechanism to receive data from action taken at a supplier site invoking specific resources / methods offered by the client.
The snapshot push client provides a mechanism to the snapshot push supplier to push currently available data, also called “snapshot” of information, i.e., current information at supplier system or last retrieved information for sampled data (see Annex F /).
In the context of the "Snapshot Push" FEP +EP framework, to enable interoperability among client and supplier, all rules defined in this clause apply.
A snapshot push Client exchange system SHALL realise a snapshot push client interface wich provides a putSnapshotData method.
A snapshot push supplier exchange system SHALL realise a snapshot push Supplier interface which invokes the putSnapshotData Method provided by the snapshot push Client interface to deliver snapshot data.
The next figure shows the communication diagram for Snapshot Push FEP + EP.
In this FEP+EP framework the supplier “pushes” messages to the client.
The client shall acknowledge the received message by a return information to the supplier. This return information shall be coded as ExchangeInformation.
Note
This return message is available to bring some exchange information from the client to the supplier which may be used for any further exchange features implementations or application-level checks or processing which are out of scope of this document.
The supplier takes the initiative to deliver the data based on application-level requirements which determine the needed exchange operating mode (e.g. on occurrence or periodic).
Figure: Snapshot Push exchange subsystems, interfaces interactions and methods
#### Relevant exchange information in exchange data model
No extra exchange information is needed in this pattern to implement any described features.
Basic exchange data model has been provided to allow the implementation to deliver more payload contents in the same message and further information to allow managing some extra features not required by the basic “Snapshot Push” exchange. The usage of the exchange data model wrapping is for harmonisation with other exchange patterns such as “Simple Push” or “Stateful Push”.
A container should be retrieved using basic exchange data model as reported in the previous figure, alternatively a payload may be delivered.
An ExchangeInformation is returned to convey information about exchange operation and connection status.
- Supplier related Information
- Requirement: Supplier identification.
- Client related Information
- Requirement: Client identification.
Dynamic Information information related are:
- Exchange DynamicInformation (provided both by the client and the supplier) wraps information such as exchangeStatus ("Success", "Fail", "Close Session Request", "Snapshot Synchronisation Request")
- Message Generation timestamp information
- Requirement: timely, reliable Information, session management.
#### Exchanged Messages
- Payload Message
- Simple payload messages may be exchanged within this FEP+EP.
- Payload messages should be delivered wrapped into a container (see Basic Exchange Data Model Annex C ) with exchange data.
- Payload Messages contain payload update timestamp which may be used to understand when payload has been updated for error management and processing saving.
#### State Diagrams
State diagram are not needed and not developed for stateless FEP+EP as Snapshot Push.
#### Features implementation description
This subclause provides a description and the corresponding specification for each feature identified in the context diagram, according to the Snapshot Pull exchange architecture. The following features are specified:
- Subscription contract
- Subscription (also known as session)
- Information management
- Data delivery
- Communication/protocol
#### Subscription contract
#### Contract
Managed offline, not automated. It assumes information for controls to be implemented in client to assess the identity of supplier and authenticate the supplier request in messages exchange.
Catalogue
Managed offline, not automated.
#### Session
Session life cycle
No session is managed for the current EP+FEP.
Link monitoring
Link monitoring is not managed for the current EP+FEP.
#### Information management
Operating modes
Available operating mode for Snapshot Push is “Periodic”, or “On Occurrence” (i.e. a condition triggered based on supplier) Push-based on supplier-side conditions.
Update methods
Available updated method is Snapshot, i.e. retrieval of only currently valid data.
Life cycle management
Currently available information is included in the payload at supplier system to prepare message delivery; this can be done at time-out on a cycle basis or at specific triggering condition as “data updated” condition.
For life cycle management information, snapshots include all active information, outdated information is not delivered in content.
For sampled information the snapshot information contains last sampled data available at supplier site.
Information management for Snapshot Push is implemented as follows: when client gets snapshot of last updated/created items including all active items, it has to check for information which has been removed from payload to deduce it had been invalidated (i.e. closed or cancelled).
#### Data delivery
Data delivery
For all clients which have an active subscription, whenever a payload delivery condition is triggered, the supplier system shall manage the creation of a payload push message in a MessageContainer and shall deliver it by its SnapshotPush supplier interface to the corresponding snapshoPush method available via the SnapshotPush client interfaced.
The figure below illustrates the sequence diagrams which describes the interaction amont exchange supplier and its clients.
Figure: Snapshot Push sequence diagram: Information management at supplier side
Note
Snapshot Push message generation may create different payload based on the client to which messages are to be delivered based on subscription information. Optional payload delivery processing based on ExchangeInformation and client subscriptions information are out of scope of this FEP+EP specification and are not described.
The client may verify the message delivered by the supplier and shall return an ExchangeInformation message to the supplier with information back to the supplier about the delivered message, i.e. return status and exchange status defined in basic exchange data model, which may be processed by the supplier to implemente optional exchange checks.
Note
ExchangeInformation provided by the supplier and client may optionally be checked to implement optional features enabled by Supplier and defined by Supplier and Client in the optional Subscription process which is out of scope of this FEP+EP specification.
Note
ExchangeInformation delivered in the return message by the snapshot push client may contain any information which can be used to inform the snapshot push supplier about any client request processing, which may be implemented in an optional check. Optional processing to deliver payload information based on agreements among client and supplier may be implemented by the supplier based on offline subscription agreements. These processing description and specification are out of scope of this FEP+EP specification.
Data request
Not implemented in this pattern.
Large datasets handling
Not described in this pattern at PIM level. May be implemented at PSM level (see optimisation subclause).
Synchronisation
Implicit synchronisation is available as only currently available elements are retrieved by Snapshot Push.
#### Self-Description
Handshake is not available.
#### Communication
Communication features are implemented at PSM level, they are relevant for the specific platform chosen on which the exchange pattern will be implemented (e.g. http/XML, Web Services SOAP, REST, etc.).
#### General optimisation issues
Some exchange pattern features of any context diagrams features groups (e.g. information management, data delivery etc.) allow the implementation of general optimisation such as processing saving and bandwith.
Payload timestamp information is available for client-side processing optimisation made at the application level.
Push message may be generated for all clients reducing processing resources at the supplier-side.
No extra optimisation issues are considered in this EP+FEP.
#### Snapshot Push SOAP webservices PSM definition
The "Snapshot Push" SOAP web services implementation is defined according to the "Snapshot Push" FEP + EP PIM description which is described at Snapshot Push section of Exchange 2020 PIM, where "Snapshot Push" exchange system functional characteristics and features are fully described.
In the "Snapshot Push" SOAP webservice exchange interface, the SOAP WSDL client method to implement putSnapshotData shall be the WSDL method named "putSnapshotData" which shall accept as input a "MessageContainer" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
Messages are implemented by SOAP protocol adding SOAP envelope information. The corresponding WSDL file is given in downloaded.
Specific xsd definition profiled for the Snapshot Push FEP+EP can be downloaded.
Note
Full model xsd definitions for Basic Exchange Data Model MessageContainer can be downloaded, FEP+EP profiled xsd are strongly suggested to reduce data redundancy and enable clearer data exchange to implement.
### Simple Push
The "Simple Push" exchange pattern / FEP at PIM level is based on information messages sent or pushed by the supplier to a client. It can be implemented in several platforms: some examples are push of generated XML content by http/post, or client providing a SOAP WebService method “push” by which data can be provided by the supplier to the client.
This “Simple Push” adds extra features to the basic Snapshot Push exchange pattern to manage link monitoring, as well as synchronisation/realignment in case of communication lacks or system maintenance. This mechanism will be detailed at PIM level in the following subclauses.
To describe the exchange pattern/FEP at PIM level all features are described in a general abstract format, independently from the specific technology platform in which this model will be implemented. (e.g. http/get XML, WebService).
Features Area | Feature | Simple Push implemented
Subscription Contract | Contract | N
Catalogue | N
Session | Session life cycle | N
Link Monitoring | Y
Information management | Operating modes | Periodic / On Occurrence based on triggering of Supplier condition
Update methods | Snapshot, Single Element Update, All Element Update
Lifecycle management | Y
Data delivery | Data delivery | Y
Data request | N
Large datasets handling | N
Synchronisation | Y, optional
Self-Description | handshake | N
Communication | Security | At PSM Level
Compression | At PSM Level
Communication | At PSM Level
#### Exchange pattern messages definition
Information delivery business scenario description and definition state that data exchange is needed to align the information kept by the supplier system into the client system; for this purpose, an exchange system is used which provides tools enabling messages generation and their transfer between a supplier and a client.
Figure: Simple Push exchange actors
The “Simple Push” exchange pattern is described in the following subclauses.
#### Basic exchange pattern
In a simple push context, the client provides a mechanism to receive data from action taken at a supplier site, invoking specific resources / methods offered by the client.
Therefore, the supplier logically “pushes” messages to the client. The client shall acknowledge what is received by a return exchange information to the supplier. This exchange information return message is available to bring information back from the client to the supplier, such as SessionId, failure, success, snapshot synchronisation request. Return message information is logically described in this PIM, while implementation will be defined at PSM level.
The simple push client provides two mechanism to the simple push supplier to push data: - a "push" method is intended to push "available data" which had not yet been delivered to the client, based on some supplier side logic and status, - a "snapshot push" is intended to push "all currently available data", also called “snapshot” of information, i.e. current information at supplier system or last retrieved information for sampled data (see Annex F ). this snapshot push method is used for synchronisation purposes among client and supplier.
Besides these push data delivery methods the simple push client also provides a "keep alive" method to implement link monitoring capabilities among client and supplier, the keep alive method is used from the supplier to advise the client when no information updates are to be delivered, so the supplier delivers a "keep alive" message to check and enable the client to check that echange systems and network connection are available, despite the supplier doesn't need to exchange payload content. "Keep Alive messaged are delivered by the supplier to the client, according to a time interval which is defined among them.
In the context of this "Simple Push" FEP +EP framework, to enable interoperability among client and supplier, all rules defined in this clause apply.
Any simple push client exchange system SHALL realise a simple push client interface wich provides a putSnapshotData, a putData and a keepalive method.
Any simple push supplier exchange system SHALL realise a simple push supplier interface which can invoke the putSnapshotData, putData, keepAlive methods provided by the simple push Client interface to deliver data or snapshot data and information to implement link monitoring.
The next figure shows the communication diagram for simple push FEP + EP.
In this FEP+EP framework the supplier “pushes” messages to the client.
The client shall acknowledge the received message by a return information to the supplier. This return information shall be coded as ExchangeInformation.
Note
This return message is available to bring some exchange information from the client to the supplier which may be used for any further exchange features implementations or application-level checks or processing which are out of scope of this document.
Figure: Simple Push exchange subsystems, interface interactions and methods
The supplier takes the initiative to push the data under the following conditions:
- On Occurrence push: as soon as information is updated at the supplier systems, this condition triggers the supplier to send push data to the client for updating the client system as soon as possible after this update.
- Periodic push: at a predefined time interval the supplier starts an exchange based on client and supplier agreement (subscription contract).
- A snapshot synchronisation with the whole currently available content snapshot at exchange initialitation e.g., the first time data are exchanged among supplier and client.
- Response to a snapshot synchronisation request: one snapshot alignment may also be transmitted to the client for internal system needs/maintenance/debug, it can be requested by the client via any return messages i.e., as a specific return value in returned exchange information.
#### Relevant exchange information from exchange data model
Basic exchange data model has been provided to allow the implementation to deliver more payload contents on the same message and further information to allow managing extra features not required by the Simple Push exchange.
For interoperability convenience the exchange data model wrapping shall be managed in this exchange.
A payload shall be pushed to a client using basic exchange data model as reported in the previous figure.
An ExchangeInformation shall be returned from putData to convey information about exchange operation and connection status.
Exchange information
Information related to Exchange that should be managed to make application development easier are fully described in basic exchange data model.
Exchange Context information related are:
- Supplier related Information
- Requirement: Supplier identification.
- Client related information
- Requirement: Client identification.
Dynamic Information information related are:
- Exchange DynamicInformation (provided both by the client and the supplier) wraps information such as exchangeStatus ("Success", "Fail", "Close Session Request", "Snapshot Synchronisation Request"), and SessionID
- Requirement: Session management, Link monitoring.
- Message Generation timestamp information
- Requirement: timely, reliable information, session management
#### List of exchanged messages
Different messages or supplier / client interactions (invoked method) are exchanged in Simple Push which are needed to manage synchronisation, payload exchange, link monitoring. These are formally contained in messages pushed to a client by a supplier or in messages returned from client to supplier.
direction
Interaction Message | Supplier Client | designation | description | Exchanged information | Optional
Payload Push | Direct | putData | Push Delivery of Payload, which has to be delivered from Supplier to Client. Exchange information such as client and supplier identification and exchange status may be provided to easy controls. | Payload + Exchange Information (MessageContainer) | N
Snapshot Payload Push | Direct | putSnapshotdata | Push delivery of current available payload, i.e. snapshot after a first initialised session in case of first connection or after an explicit snapshot realignment request from the client. Exchange information such as client and supplier identification and exchange status may be provided to easy controls. | Snapshot Payload + Exchange Information (MessageContainer) | Y
Keep Alive | Direct | keepAlive | Test exchange link and confirm session validity when no payload push update is needed, exchange information such as client and supplier identification and exchange status may be provided to easy controls and supplier identification. | Exchange Information | N
Exchange Information Return | Return | Exchange Infomation | Exchange information is returned from client to supplier to provide return status i.e. Success, Fail, Snapshot Synchronisation Request and to easy controls such as supplier and client identification. | Exchange Information | N
#### State Diagrams
The supplier initiates the communication and is made aware of the client status based on the client return response to the supplier.
The following diagram describes the client status as monitored and managed by the supplier.
Figure: Supplier-side Simple Push state diagram
The following diagram describes the supplier status as monitored and managed by the client.
Figure: Client-side Simple Push state diagram
Special management in initialisation and termination of Push process is to consider at the application level in supplier and client systems.
#### Features implementation description
This subclause provides a description and the corresponding specification for each feature identified in the context diagram, according to the Simple Push data exchange architecture. The following features are specified:
- Subscription contract
- Subscription (also known as session)
- Information management
- Data delivery
- Communication/protocol
#### Subscription contract
Contract
Managed offline, not automated. It assumes information for controls to be implemented in client to assess the identity of supplier and authenticate the supplier request in messages exchange.
Catalogue
Managed offline, not automated.
#### Session
Session life cycle
No session is managed for the current EP+FEP.
Link monitoring
Link monitoring is done by Payload Push and KeepAlive. When data is available a payload Push is exchanged which also informs client and supplier about the session and systems status: Push received from supplier on client side and return of push on payload push on supplier side guarantee the network is available and the systems are up and running.
When no data is available at supplier and a time-out has expired a KeepAlive message is exchanged to check network and system availability.
In case payload push or KeepAlive fails or times out, the supplier assumes the client is offline and keeps trace of its status for any management purposes at the supplier system side (for delivery retry mechanism is to be described at PSM level defining a logical push mapping iterated for a maximum number of times).
Figure: Simple Push sequence diagram for link monitoring and data delivery
#### Information management
Operating modes
Available operating mode for Simple Push is “Periodic”, or “On Occurrence” (i.e. condition is triggered based on supplier) push based on supplier-side conditions.
Description of operating modes is done at a general PIM level; no extra details are needed in this subclause for PIM/Exchange Pattern / FEP.
A Payload Push condition is triggered based on the agreed operating mode defined at subscription among client and supplier.
Update methods
Available updated methods are: Snapshot, Single Element Update, All Element Update.
All updates available are conveyed in a payload publication push message.
Description of update methods is done at PIM level; no extra details are needed in this subclause for PIM/exchange pattern / FEP.
Life cycle management
Description of life cycle management is done at PIM level.
Life cycle management to exchange data between client and supplier is embedded with the operating mode and update method chosen at subscription contract.
Push delivery method allows conveying information from supplier to client as two different pieces of information.
Sampled data may be conveyed as Periodic or On Occurrence push of a snapshot payload containing all current active data or last collected data.
A Single/All Element updated push can be done for any operating mode as well with On Occurrence or Periodic Push.
#### Data delivery
Data delivery
Based on sequence diagram described in the previous figure, the supplier after initialisation starts sending push information to a client: in case of stateful information delivery and based on the possibly agreed conditions of the subscription contract, e.g. it manages a snapshot push whenever it has no historical information about client status, deriving it is the first connection ever and a Snapshot Push is needed to align the client system when it is not the first time the supplier sends to the client normal payload push data, but the client for internal system needs can also require for snapshot push data by its return status.
After initialisation ready data condition at the supplier system side triggers a payload push delivery.
A periodic push condition is also possible based on contract agreement between supplier and client.
See sequence diagram at link monitoring life cycle for all messaging details.
Data request
Not fully implemented in this pattern.
A snapshot synchronisation request can be managed in the client return data, by the return status described in the "Basix Exchange Data Model" by returnStatus set as snapshotSynchronisationRequest.
This feature implementation is not mandatory in this FEP, agreement to manage among client and supplier are needed to enable full interoperability.
Large datasets handling
Not fully implemented in this pattern.
A multi-part data delivery can be optionally implemented by supplier by setting in the delivered message within exchange "Dynamic Information" setting the completedPayload as false, as described in Basic Exchante Data Model, it will inform the client one or more subsequent message will be delivered to complete the payload information, until the attribute completedPayload will be set as true.
This feature implementation is not mandatory in this FEP, agreement to manage among client and supplier are needed to enable full interoperability.
Synchronisation
Snapshot synchronisation and delta synchronisation are available in Simple Push.
Snapshot synchronisation is optionally managed at first connection with a client or under client request. In all other cases a Simple Push is delivered based on supplier site data available and conditions.
#### Self-Description
Handshake not available.
#### Communication
Communication features are implemented at PSM level, they are relevant to the specific Platform chosen on which the Exchange pattern will be implemented (e.g. http/XML, Web Services SOAP, REST).
#### General optimisation issues
Some exchange pattern features of any context diagrams features groups (e.g. information management, data delivery etc.) allow the implementation of general optimisation such as processing saving and bandwith.
Payload timestamp information is available for client-side processing optimisation made at the application level.
Snapshot Push messages may be generated for all clients reducing processing resources at the supplier-side.
No extra optimisation issues are considered in this EP+FEP.
#### "Simple Push" SOAP webservices PSM definition
The “Simple Push" SOAP web services implementation is defined according to the "Simple Push" FEP + EP PIM description which is described at "Simple Push" Section of Exchange 2020 PIM, where "Simple Push" exchange system functional characteristics and features are fully described.
In the “Simple Push" SOAP webservices exchange interface:
- the SOAP WSDL client method to implement putSnapshotData shall be the wsdl method named "putSnapshotData" which shall accept as input a "MessageContainer" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
- the SOAP WSDL client method to implement putData shall be the wsdl method named "putData" which shall accept as input a "MessageContainer" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
- the SOAP WSDL client method to implement keepAlive shall be the wsdl method named "keepAlive" which shall accept as input an "ExchangeInformation" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
Messages are implemented by SOAP protocol adding SOAP envelope information. The corresponding WSDL file is given in downloaded.
Specific xsd definition profiled for the Simple Push FEP+EP can be downloaded.
Note
Full model xsd definitions for Basic Exchange Data Model MessageContainer can be downloaded, FEP+EP profiled xsd are strongly suggested to reduce data redundancy and enable clearer data exchange to implement.
### Stateful Push
The "Stateful Push" exchange pattern / FEP at PIM level is based on information messages sent or pushed by a supplier to a client. This exchange pattern can be implemented in several platforms: some examples are pushing generated XML content by http/post, or client providing a SOAP Web service method “push” by which data can be provided to a client by a supplier.
This “Stateful Push” adds extra features to the "Snapshot Push" exchange pattern to manage "Session life cycle" and "Link monitoring", as well as synchronisation/realignment in case of communication breaks or system maintenance. Further for "Data Delivery" features it enables, besides "snapshot" payload delivery, any update of information e.g., allowing single element updates. These mechanisms will be fully explained at the PIM level in the following subclauses.
To describe the exchange pattern/FEP at PIM level all the features are described in a general abstract format, independently from the specific technologic platform in which this model will be implemented (e.g. http/get XML or Web services).
Features Area | Feature | Stateful Push available
Subscription Contract | Contract | N
Catalogue | N
Session | Session life cycle | Y
Link Monitoring | Y
Information management | Operating modes | Periodic / On Occurrence based on triggering of Supplier condition
Update methods | Snapshot, Single Element Update, All Element Update
Lifecycle management | Y
Data delivery | Data delivery | Y
Data request | Snapshot realignment
Large datasets handling | N
Synchronisation | Y
Self-Description | handshake | N
Communication | Security | At PSM Level
Compression | At PSM Level
Communication | At PSM Level
#### Exchange pattern messages definition
Information delivery business scenario description and definition state that data exchange is needed to align the information kept by the supplier system into the client system; for this purpose, an exchange system is used which provides tools enabling messages generation and their transfer between a supplier and a client.
Figure: Stateful Push exchange actors
The “Stateful Push” exchange pattern is described in the following subclauses.
#### Basic exchange pattern
In a stateful push context, the client provides a mechanism to receive data from an action taken at the supplier site invoking specific resources / methods offered by the client.
Therefore, the supplier logically “pushes” messages to the client. The client shall acknowledge what is received by a return exchange information to the supplier. This exchange information return message is available to bring information back from the client to the supplier, such as SessionId, failure, success, snapshot synchronisation request. Return message information is logically described in this PIM, while implementation will be defined at PSM level.
As in "Simple Push", the "Stateful Push" client provides two mechanism to the "Stateful Push" supplier to push data:
- a "push" method is intended to push "available data" which had not yet been delivered to the client, based on some supplier side logic and status,
- a "snapshot push" is intended to push "all currently available data", also called “snapshot” of information, i.e. current information at supplier system or last retrieved information for sampled data (see Annex F ). This "snapshot push" method is used for synchronisation purposes among client and supplier.
Besides "push" data delivery methods the simple push client also provides a "keep alive" method to implement link monitoring capabilities among client and supplier, the keep alive method is used from the supplier to advise the client when no information updates are to be delivered, so the supplier delivers a "keep alive" message to check and enable the client to check that exchange systems and network connection are available, despite the supplier does not need to exchange payload content. "Keep Alive" messages are delivered by the supplier to the client, according to a time interval which is defined among them.
"Stateful Push" session management methods are available to implement session management features; such methods, namely openSession and closeSession usage which are used to define dynamic exchange information context to enable session management exchange features.
In the context of this "Stateful Push" FEP+EP framework, to enable interoperability among client and supplier, all rules defined in this clause apply.
Any stateful push client exchange system SHALL realise a stateful push client interface wich provides a putSnapshotData, a putData, an openSession, a closeSession mehod and a keepalive method.
Any stateful push supplier exchange system SHALL realise a stateful push supplier interface which can invoke the putSnapshotData, putData, openSession, closeSession and keepAlive methods provided by the stateful push Client interface to deliver data or snapshot data and information to implement link monitoring and session management.
The next figure shows the communication diagram for simple push FEP + EP.
In this FEP+EP framework the supplier “pushes” messages to the client.
The client shall acknowledge the received message by a return information to the supplier. This return information shall be coded as ExchangeInformation.
This return message is available to bring some exchange information from the client to the supplier which may be used for any further exchange features implementations or application-level checks or processing which are out of scope of this document.
Figure: Stateful Push exchange subsystems, interface interactions and methods
The supplier takes the initiative to push the data, or the snapshot data, under the following conditions:
- On occurrence push: as soon as an information is updated at the supplier systems, this condition triggers the exchange supplier to manage an alignment to the exchange client to update the client system as soon as possible after this update.
- Periodic push: at predefined time interval the supplier starts an exchange based on client and supplier agreement (subscription contract).
- A snapshot synchronisation with the whole currently available content snapshot at exchange initialitation, e.g. the first time data are exchanged among supplier and client.
- First session initialisation: a global snapshot alignment is needed to convey all currently valid data at the first connection of exchange.
- Session initialisation: after a session had been created the client shall be aligned with an incremental delta synchronisation when a partial update feature is enabled, delivering all updated content since last exchange, or with a global synchronisation with all the current active content in case the snapshot alignment feature is enabled (this may also depend on specific payload depending on the agreement between client and supplier or contract).
- Response to a snapshot synchronisation request: one snapshot alignment may also be transmitted to the client for internal system needs/maintenance/debug, it can be requested by the client via any return messages, i.e. as a specific return value in returned exchange information.
#### Relevant exchange information from exchange data model
Basic exchange data model has been provided to allow an implementation that delivers more payload contents in the same message and further information to allows managing extra features which are not required by the basic Snapshot Push exchange.
To ensure interoperability, the exchange data model wrapping shall be used in this exchange pattern.
A container shall be pushed to client using basic exchange data model as stated in the previous figure.
An ExchangeInformation object shall be returned from putData to convey information about exchange operation and connection status.
Exchange information
Information related to Exchange that should be managed to make application development easier are fully described in basic exchange data model.
Exchange Context information related are:
- Supplier related information
- Requirement: Supplier identification.
- Client related information
- Requirement: Client identification.
- Exchange DynamicInformation (provided both by the client and the supplier) wraps information such as exchangeStatus ("Success", "Fail", "Close Session Request", "Snapshot Synchronisation Request"), and SessionID
- Requirement: Session management, link monitoring
- Message Generation timestamp information
- Requirement: Timely, reliable information, session management.
#### Payload Information
- Generation Timestamp Information
- Requirement: Timely, reliable information, session management.
#### List of exchanged messages
Different messages or supplier/client interactions are exchanged in the Stateful Push which are needed to manage session, synchronisation, payload exchange, link monitoring. These are formally contained in messages pushed to a client by a supplier or in messages returned from client to supplier.
direction
Interaction Message | Supplier Client | designation | description | Exchanged information | Optional
Open Session | Direct | openSession | Supplier initialise a push delivery Session. | Exchange Information | N
Push Delivery of Payload, which has not been yet delivered from Supplier to Client.
It shall contain in Exchange information the Session ID, previously obtained with OpenSession, referring which session it is pushing data.
Payload +
Exchange Information
(MessageContainer)
Payload Push | Direct | putData | N
Snapshot Payload +
Exchange Information
(MessageContainer)
Snapshot Payload Push | Direct | putSnapshotdata | Push Delivery of current available Payload, i.e. Snapshot after a First Initialised Session in caso of first connection or after an explicit Snapshot realignment request from the Client. It SHALL contain in Exchange information the Session ID, previously obtained with OpenSession, referring which session it is pushing data.. | N
Test Exchange Link and confirm Session Validity when no Payload Push update is needed.
It shall deliver the Session ID of a previously opened Session, wrapped in Exchange Information.
Keep Alive | Direct | keepAlive | Exchange Information | N
Close Session | Direct | closeSession | Message to gracefully close a delivery Session, initiated by the Supplier | Exchange Information | N
Exchange Information Return | Return | Exchange Information | Exchange information is returned from Client to supplier to provide Return status i.e. Success, Fail, Snapshot Synchronisation Request and to easy controls such as Supplier and Client Identification. | Exchange Information | N
#### State Diagrams
The supplier initiates the communication and can be aware of the client status based on the client return response to the supplier.
The following diagram describes the client status as monitored and managed by the supplier.
Figure: Supplier-side Stateful Push state diagram
The following diagram describes the supplier status as monitored and managed by the client.
Figure: Client-side Stateful Push state diagram
Specific management in the initialisation and termination of a push process should be considered at the application level in the supplier and client systems.
#### Features implementation description
This subclause provides a description and the corresponding specification for each feature identified in the context diagram, according to the Publish-Subscribe data exchange architecture. The following features are specified:
- Subscription contract
- Subscription (also known as session)
- Information management
- Data delivery
- Communication/protocol
The corresponding classes, attributes and relationships described in the class diagrams included in the next subclauses are described in C.4.
#### Subscription contract
Contract
Managed offline, not automated. It assumes information for controlling to be implemented in a client to assess the identity of supplier and authenticate the supplier request in messages exchange.
Catalogue
Managed offline, not automated.
#### Session
Session life cycle
After the session status management diagrams, the following sequence diagram illustrates the exchanged message and the expected return and behaviour.
When a session needs to be initiated, an “Open Session” is tried in loop until it succeeds.
A failure when opening a session includes cases of a client who has not subscribed or is not authorised. Checking this can be ensured at the PSM level (e.g., this could include VPN setting or IP firewall or signatures handling), logical information may be included in exchange data to be managed in subscription check at the client side.
When a session is "ON" the supplier pushes available payload data to the client in case one of the 2 conditions is fulfilled:
- payload available for On Occurrence operating mode
- payload delivery time-out for Periodic push operating mode.
In case no payload is available a" Keep Alive" message is used to check session status for the supplier and the client.
When no "Keep Alive" message or no payload is received, after a "Keep Alive" time-out the client invalidates the session on its side and returns a "Close Session" message to prevent any attempt of push from the supplier.
If any push or keep alive fails, the supplier invalidates the session and starts a new loop to open session.
Realignment messages are managed when a session is opened, a global synchronisation request from the client is returned in opening session when needed. Further any global synchronisation may be asked by a client in any push return as well, but this does not close the session.
Any message and return in the sequence diagram will be mapped in PSM definition to real platform available implementation such as a web service "Service request and return" or any other available mechanism in a specific platform.
Figure: Stateful Push sequence diagram for session life cycle and data delivery
Link monitoring
"Keep Alive" is based as described in the previous session life cycle.
When data is available a payload push is exchanged which informs the client and the supplier about the session and systems status: The push is received from the supplier on the client side and the return of Push on payload push on the supplier side guarantees the network is available and the systems are up and running.
When no data is available and a time-out has expired a "Keep Alive" message is exchanged to check the network and system availability.
In case a payload push or a "Keep Alive" fails the session shall be invalidated (the retry mechanism is to describe at the PSM level introducing a logical push mapping iterated for a maximum number of attempts).
#### Information management
Operating modes
The available operating modes for supplier Push are either periodic, or condition-triggered (based on the supplier-side conditions and the interchange agreement at the subscription).
The general description of the operating modes is done at the PIM level, no extra details are needed in this subclause for PIM/exchange pattern / FEP.
A payload Push is triggered based on the agreed operating mode defined at the subscription between the client and the supplier.
Update methods
Available updated methods are: Snapshot, Single Element Update, All Elements Update.
All updates available are conveyed in a payload publication push message.
The general description of the update methods is done at the PIM level, no extra details are needed in this subclause for PIM/exchange pattern / FEP.
Life cycle management
The description of life cycle management is done at the PIM level.
The life cycle management for exchanging data among a client and a supplier is embedded in the operating mode and the update method which have been chosen in the subscription contract.
The push delivery method allows conveying information from a supplier to a client as two different sets of information.
Sampled data can be conveyed (pushed) as “Periodic” or “On occurrence” of a global payload containing all currently active data or last collected data.
A "Single element" or "All elements" update push can be done for any operating mode i.e., with "On occurrence" or "Periodic" push.
#### Data delivery
Data delivery
Session life cycle online section allows sending data when available at the supplier system by triggering a data ready condition.
A periodic push condition is also possible based on contract agreement among supplier and client.
See sequence diagram at the session life cycle for messaging details.
Data request
Not fully implemented in this pattern.
A snapshot synchronisation request can be managed in the client return data, by the return status described in the "Basix Exchange Data Model" by returnStatus set as snapshotSynchronisationRequest.
This feature implementation is not mandatory in this FEP, agreement to manage among client and supplier are needed to enable full interoperability.
Large datasets handling
Not fully implemented in this pattern.
A multi-part data delivery can be optionally implemented by supplier by setting in the delivered message within exchange "Dynamic Information" setting the completedPayload as false, as described in Basic Exchante Data Model, it will inform the client one or more subsequent message will be delivered to complete the payload information, until the attribute completedPayload will be set as true.
This feature implementation is not mandatory in this FEP, agreement to manage among client and supplier are needed to enable full interoperability.
Synchronisation
Global synchronisation and delta synchronisation are available in Stateful Push.
The global synchronisation is managed at the first session with a client or under a client request.
The delta synchronisation is managed once a session had been created and closed due to a network error or any other condition, so that not-delivered payload data is stored at the supplier side and delivered to the client as soon as a session is established again.
Self-description
The handshake is not available.
#### Communication
The communication features are implemented at the PSM level; they are relevant to a specific platform chosen on which the exchange pattern will be implemented (e.g. http/XML, Web services with SOAP, REST, etc.).
#### General optimisation issues
Some exchange pattern features of any context diagrams features groups (e.g. information management, data delivery etc.) allow the implementation of general optimisation such as processing saving and bandwith.
Payload timestamp information is available for client-side processing optimisation made at the application level.
Snapshot Push messages may be generated for all clients reducing processing resources at the supplier-side.
No extra optimisation issues are considered in this EP+FEP.
#### "Stateful Push" SOAP webservices PSM definition
In the “Stateful Push" SOAP webservices exchange interface:
- The SOAP WSDL client method to implement openSession shall be the wsdl method named "openSession" " which shall accept as input an"ExchangeInformation" XML message data structure and shall return an"ExchangeInformation" XML message data structure.
- The SOAP WSDL client method to implement closeSession shall be the wsdl method named "closeSession" " which shall accept as input an"ExchangeInformation" XML message data structure and shall return an"ExchangeInformation" XML message data structure.
- the SOAP WSDL client method to implement putSnapshotData shall be the wsdl method named "putSnapshotData" which shall accept as input a"MessageContainer" XML message data structure and shall return an"ExchangeInformation" XML message data structure.
- the SOAP WSDL client method to implement putData shall be the wsdl method named "putData" which shall accept as input a"MessageContainer" XML message data structure and shall return an"ExchangeInformation" XML message data structure.
- the SOAP WSDL client method to implement keepAlive shall be the wsdl method named "keepAlive" which shall accept as input an"ExchangeInformation" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
Messages are implemented by SOAP protocol adding SOAP envelope information. The corresponding WSDL file is given in downloaded.
Specific xsd definition profiled for the Stateful Push FEP+EP can be downloaded.
Note
Full model xsd definitions for Basic Exchange Data Model MessageContainer can be downloaded, FEP+EP profiled xsd arestrongly suggested to reduce data redundancy and enable clearer data exchange to implement.
Go back to the previous page
