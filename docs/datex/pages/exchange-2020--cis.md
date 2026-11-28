url: https://docs.datex2.eu/v3.7/exchange-2020/cis/
title: Collaborative ITS Services (CIS) FEP+EP PIM and SOAP WS PSM definition

## Collaborative ITS Services (CIS) FEP+EP PIM and SOAP WS PSM definition
The following sections will describe Collaborative ITS Services Exchange Pattern for chosen Functional Exchange profiles.
The SOAP WS PSM related clauses express requirements for implementation of Collaborative ITS Services business scenarios FEP+EP which are fully described at PIM level referencing their exchange agent and relative interfaces.
Note
A system can be both a CIS requester and a CIS provider for another CIS requester simultaneously, defining multiple separated CIS exchange contexts (e.g. set of exchange nodes defined to exchange information in a specific business scenario with a specified EP+FEP).
### Simple CIS
Simple CIS FEP+EP PIM is based on description of interactions which enable service request and feedback exchange among a service requester and one to many service providers as illustrated in informative Annex H .
It can be implemented in several technological platforms with specific interactions methods e.g., SOAP WebService methods.
The simple CIS FEP+EP frameworks enables a common communication interface to embed ITS service request and feedback in a way that two or more TMC, TIC or SP systems can perform in a common interoperable way.
Simple CIS FEP +EP framework is not designed to implement Data Delivery business scenario, but it may be based on payload content which is assumed to be exchanged by Data Delivery which can be enabled by Data Delivery FEP+EP. Only Specific features enabling CIS are described and introduced for Simple CIS. Feature which are not related to this FEP+EP are martked as "Not applicable" in Table 9.
To describe the EP+FEP at PIM level all features are described in a general abstract format, independently from the specific technology platform in which this model will be implemented. (e.g., http/get XML, WebService).
Features Area | Feature | Simple Push available
Subscription contract | Contract | N
Catalogue | N
Session | Session life cycle | N
Link monitoring | N
Information management | Operating modes | Not applicable
Update methods | Not applicable
Life cycle management | Not applicable
Support information processing | Y
Distributed transaction | Y, not atomic transactions
Data delivery | Data delivery | Not applicable
Data request | Not applicable
Large datasets handling | Not applicable
Synchronisation | Not applicable
Self-Description | Handshake | N
Communication | Security | At PSM level
Compression | At PSM level
Communication | At PSM level
#### Exchange pattern and messages definition
"Simple CIS" FEP+EP enable 1 service requester node to implement CIS service sequest interaction for 1 to several service providers.
The interaction is described as the CIS service requester addressing all involved CIS service providers through their Simple CIS Exchange interfaces which provides methods to deliver service requests from a requester to a multiplicity of service providers (Figure 31).
"Simple CIS" exchange actors
The “Simple CIS” exchange pattern is described in the following subclauses.
#### Basic exchange pattern
In a "Simple CIS" context, the service provider provides a mechanism to receive a service request from action taken at a service requester site. This will result in the service requester invoking specific methods /resource offered by the service provider. On the reverse side a mechanism is also needed to enable the service provider to feed back the result of processing or action triggered by the service request, so the service requester itself provides a mechanism to receive a service feedback from the involved service providers when their actions or processes results are available.
The next figure shows the communication diagram for "Simple CIS" FEP + EP.
In this FEP+EP framework the service requester delivers a service request trigger to the service provider and the service provider delivers service feedback information to the service requester.
Therefore the "Service Requester" logically "pushes" "CIS Service Requests" messages, embedded in a "MessageContainer", to the "Service Provider" which shall acknowledge the reception of such messages by a return message, embedded in an "ExchangeInformation". This exchange information return message is available to bring information back from the "Service Provider" to the "Service Requester", such as failure, success. Return message information is logically described in this PIM, while implementation will be defined at PSM level.
At the same time, the involved "Service Providers" logically push "CIS Service Feedback" messages, embed in a "Message Container" to the "Service Requester" which symmetrically shall acknowledge the reception of suche messages by a return message, embedded in an "ExchangeInformation". This exchange information return message is available to bring some information back to the "Service Provider" which management is not relevant to this FEP+EP and is not described in this document.
The management of any further workflow based on any processing or action errors is in this workflow framework pattern based on CIS "Service Feedback" is only in charge of the "Service Requester" System and is defined at application level based on the specific application requirements needed to enable the specific collaborative ITS services.
In the context of this "Simple Push" FEP +EP framework, to enable interoperability among CIS service requester and CIS service providers, all rules defined in this clause apply.
Any simple CIS service provider exchange system SHALL realise a simple CIS service provider interface which provides a putCISServiceRequest method.
Any simple push service requester exchange system SHALL realise a simple cis service requester interface which can invoke the putCISServiceRequest method provided by the simple cis service provider interface to deliver cis service request to trigger action/process by the service provider systems.
Any simple CIS service requester exchange system SHALL realise a simple CIS service requester interface which provides a putCISServiceFeedback method.
Any simple CIS service provider exchange system SHALL realise a simple CIS service provider interface which can invoke the putServiceRequest method provided by the simple CIS service requester interface to deliver CIS service feedback to the service requester systems.
Figure 32 shows the communication diagram for simple push FEP + EP.
In this FEP+EP framework the service requester “pushes” service requests messages to the service provider and the service provider "pushes" service feedback messages to the service requester.
Both service provider and service requester shall acknowledge the received service request or service feedback messages by a return information to the corresponding counterpart i.e., respectively to the service requester and to the service provider. This return information shall be coded as ExchangeInformation.
Note
This return message is available to bring some exchange information back from the receiver system which may be used for any further exchange features implementations or application-level checks or processing and/or workflow management decision in CIS implementation which are out of scope of this document.
Simple CIS exchange subsystems, interface interactions and methods
#### Relevant exchange information from exchange data model
Basic exchange data model has been provided to allow the implementation to enable CIS features to support information processing and enable distributed transactions features.
CIS Information embed all information needed to request for specific processing and to enable workflow management to support transaction negotiation processes by service request and service feedback messages.
Exchange information enables to deliver the Exchange context of involved service requester and service providers to enable orchestration of ITS services supply and exchange dynamic information which enables general exchange status information to monitor transactions negotiation or service processing in general.
Exchange information
Some non-mandatory information which should be managed in the exchange information for easy application development are fully described in basic exchange data model:
- Service Provider Identification
- Requirement: Supplier identification. (String)
- Client Identification
- Requirement: Client identification. (String)
- Exchange Information (provided both by the client and the supplier) wraps exchange and exchange status information "Success", "Fail", "Close Session Request", “SessionId”
- Generation timestamp information
- Requirement: timely, reliable Information
CIS information
- Service Request
- It provides the reference to element to be processed and the requested action, also addressing the service for which the action is triggered:
- Predefined service
- Requirements: Support for information processing, Distributed transaction
- Requested Action
- Requirements: Support for information processing, distributed transaction, distributed atomic transaction
- Service Feedback
- Requirements: Support for feedback on information processing, distributed transaction,
- Service request status
- Requirements: Support information processing, Support for feedback on information processing, distributed transaction
#### Exchanged messages
Different messages or supplier / client interactions (invoked method) are exchanged in Simple Push which are needed to manage synchronisation, payload exchange, link monitoring. These are formally contained in pushed messages to a client from a supplier or in return messages from client to supplier.
Interaction message | Direction requester provider | Designation | Description | Exchanged information | Optional
Push delivery of a service request, which has to be delivered from service requester to the service provider.
CIS Information is delivered in the specific container to address the instruction to process information and/or implement the requested service.
Exchange information such as requester and service provider identification and exchange status are provided to easy controls.
Message Container including:
Payload (optional when not delivered in former Data Delivery Exchange) + CIS Information (Mandatory service request information) + Exchange Information with relevant information to enable exchange features
Service Request | Direct | putCISServiceRequest | N
Push delivery of a CIS Service Feedback.
CIS service feedback Information is delivered in the specific container to address the status and result of processing and/or and/or implementation of the requested service.
Exchange information such as client and supplier identification and exchange status may be provided to easy exchange related controls.
Message Container including:
Payload (optional when not delivered in Data Delivery Exchange) + CIS Information (Mandatory service feedback information) + Exchange information with relevant information to enable exchange features
Service Feedback | Return | putCISServicefeedback | N
Exchange Information Return | Return (Direct on Service Feedback) | D2Exchange Information | Exchange information is returned from client to supplier to provide return status i.e. Success, Fail and exchange context information to easy controls such as supplier and client identification. | Exchange Information | N
#### State Diagrams
State diagram are not needed and not developed for stateless FEP+EP as Simple CIS.
#### Features implementation description
This subclause provides a description and the corresponding specification for each feature identified in the context diagram, according to the Simple Push data exchange architecture. The following features are specified:
- Subscription contract
- Subscription (also known as session)
- Information management
- Data delivery
- Communication protocol
#### Subscription contract
Contract
Managed offline, not automated. It assumes information for controls to be implemented in client to assess the identity of supplier and authenticate the supplier request in messages exchange.
Catalogue
Managed offline, not automated.
#### Session
Session life cycle
No session is managed for the current EP+FEP.
Link monitoring
Not managed in this EP+FEP.
#### Information management
Overview of information management features
CIS features implementation is based on Service Request and Service Feedback implementation.
As explained in Annex H, besides Exchange actors involvement "Collaborative ITS Services" workflow management to support information process and transactions features involves application level management. These application-level checking and triggers, which are needed to implement control and triggers to start exchange features, are considered existing and are not described in this document, which only assumes these processing and triggering functions are needed and implemented at "Service Requester System" and "Service Provider System" and are only indicated in the sequence diagrams as placeholders to support understanding of exchange workflows.
Note
Application-level triggers and checkings are depending on specific payload domain which is managed in the exchange and can be specified only based on the payload content itself which is out of scope of this document. Examples of specific domain information are referred in the Basic Exchange Data Model CIS Information (ref. Annex C ) as predefined services such as: VMS message processing, information broadcast delivery or traffic management plans activation and implementation.
The below figure describes the interaction to implement a service request from the "Service Requester System" to one up to many "Service Provider Systems" by the "Simple CIS" exchange.
After the application level "Service Requester" system has triggered the "Service Request" exchange management, at first outcome it will receive the information that Service Request have been delivered to involved "Service Provider" systems, or some errors happened or had been recognised by the "Service Provider" systems in the service request itself. Returned "Exchange Information" is the first outcome of the Service Request delivery to the Service Provider and Service Provider System.
For CIS it is also assumed that at "Service Requester System" some application-level management of service requests which had been delivered is needed and feedback and error/timeout management is done as application level implementation. The outcomes of such management will lead some application logic to decide the next workflow and exchange action needed but are not described in this specification.
Simple CIS sequence diagram for Service Request
As stated above only interaction among "Exchange Interfaces" i.e., Service Requester and Service Provider are considered normative for the specific FEP+EP in this document. Other interactions are assumed but are dependent on application logic and requirements which are external to the exchange system which are not in the scope of this document. General aspect for CIS and some application-level workflow requirements are described at Annex H.
Figure 34 describes the interaction to implement a service feedback from the "Service Provider System" to the "Service Requester System" by the "Simple CIS" exchange.
After the application level "Service Provider" system has delivered the feedback to the "Service Requester" exchange management, at first outcome it will receive the information that service feedback have been delivered to the "Service Requester" system or some errors happened or had been recognised by the "Service Requester" systems in the service feedback itself. Returned Exchange Information is the first outcome of the "Service Feedback" delivery to the Service Requester and Service Requester System.
For CIS it is also assumed that at "Service Requester System" some application-level management of service feedbacks which had been delivered is needed and feedback and error/timeout management is done as application level implementation. The outcomes of such management will lead some application logic to decide the next workflow and exchange action needed but are not described in this specification.
Simple CIS sequence diagram for Service Feedback
Support information processing
While the workflow to enable the support to information processing is defined in sub-clause 6.4.4.1 of this document, the information needed to enable such information process are described in the Basic Exchange Data Model at Annex C , specifically at CIS Information description.
Predefined services are possible as well as not predefined services, which are enabled by specific attributes in the CIS Information classes.
Distributed transaction
While the workflow to enable the support to distribute not atomic transactions processing is defined in sub-clause 6.4.4.1 of this document, the information needed to enable such information process are described in the Basic Exchange Data Model at Annex C, specifically at "CIS Information" description.
Predefined services are possible as well as not predefined services, which are enabled by specific attributes in the "CIS Information" classes.
Data delivery
Not managed in this EP+FEP.
In Simple CIS FEP+EP PIM it is assumed that data delivery requirements to deliver data to be processed are enabled by a parallel Data Delivery exchange and referenced in CIS Information to specify the relative processing action, despite payload data can be also delivered in a Service Request or Service Feedback when needed by specific application-level management, it can be assumed delivered in a previous exchange. The responsibility of data availability to support actions and processing requests are assumed to be in charge of the "Service Requester System" itself.
#### Self-Description
Handshake not available.
#### Communication
Communication features are implemented at PSM level, they are relevant to the specific Platform chosen on which the Exchange pattern will be implemented (e.g. http/XML, Web Services SOAP, REST).
#### "Simple CIS" SOAP webservices PSM definition
In the “Simple CIS" SOAP webservices exchange interface at service provider side:
- The SOAP WSDL method to implement putCISServiceRequest shall be the wsdl method named "putCISServiceRequest" which shall accept as input an "MessageContainer" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
In the “Simple CIS" SOAP webservices exchange interface at service requester side:
- The SOAP WSDL method to implement putCISServiceFeedback shall be the wsdl method named "putCISServiceRequest" " which shall accept as input an "MessageContainer" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
Messages are implemented by SOAP protocol adding SOAP envelope information.
The corresponding WSDL file is can be downloaded
Specific xsd definition profiled for the Simple CIS FEP+EP can be downloaded.
Note
Full model xsd definitions for Basic Exchange Data Model MessageContainer can be downloaded, FEP+EP profiled xsd are strongly suggested to reduce data redundancy and enable clearer data exchange to implement.
### Stateful CIS
"Stateful CIS" is an extension of the "Simple CIS", described and specified for the "Simple CIS" FEP+EP PIM (i.e. clause 5.5 in this document), with session management and link monitoring features which are enabled by the same mechanisms which are defined for the "Stateful Push" FEP + EP PIM (i.e. section 5 in this document). The overall implementation of "Stateful CIS" will be a combination of features described for both “Simple CIS" service requedt and service feedback mechanism, with session management and link monitoring features implemented as per "Stateful Push".
Only specific "Stateful Push" definition will be described in the current section, all definition and specification which are the same for "Stateful Push" or "Simple CIS" FEP+EP PIM will be addressed to the specific sections in this document.
Note
All definition applies which are related to "Simple CIS" and "Stateful Push"FEP + EP PIM, but supplier role and name is to be associated to the requester system and client role and name is to be associated to the provider systems.
"Stateful CIS" FEP+EP PIM is based on description of interactions which enable service request and feedback exchange among a service requester and one to many service providers as illustrated in informative Annex H.
It can be implemented in several technological platforms with specific interactions methods e.g., SOAP WebService methods.
The "Stateful CIS" FEP+EP frameworks enables a common communication interface to embed ITS service request and feedback in a way that two or more TMC, TIC or SP systems can perform in a common interoperable way.
"Stateful CIS" FEP +EP framework is not designed to implement Data Delivery business scenario, but it may be based on payload content which is assumed to be exchanged by Data Delivery which can be enabled by Data Delivery FEP+EP. Only Specific features enabling CIS are described and introduced for Simple CIS. Feature which are not related to this FEP+EP are martked as "Not applicable" in Table 9.
To describe the "Stateful CIS" EP+FEP at PIM level all features are described in a general abstract format, independently from the specific technology platform in which this model will be implemented. (e.g., http/get XML, WebService).
Features Area | Feature | Simple Push available
Subscription contract | Contract | N
Catalogue | N
Session | Session life cycle | Y
Link monitoring | Y
Information management | Operating modes | Not applicable
Update methods | Not applicable
Life cycle management | Not applicable
Support information processing | Y
Distributed transaction | Y, not atomic transactions
Data delivery | Data delivery | Not applicable
Data request | Not applicable
Large datasets handling | Not applicable
Synchronisation | Not applicable
Self-Description | Handshake | N
Communication | Security | At PSM level
Compression | At PSM level
Communication | At PSM level
#### Exchange pattern and messages definition
As Simple CIS "Stateful CIS" FEP+EP enable one service requester node to implement CIS service sequest interaction for one up to several service providers. At the same time Session Management and Link Monitoring features allows "Stateful CIS" Service Requester and Service Provider Systems to be aware of network communication features among them to enable reliable and timely exchange and take initiative to trigger any required actions besides CIS actions themselves in case a session or link are broken by system or network failures.
The interaction is described as the CIS service requester addressing all involved CIS service providers through their Stateful CIS Exchange interfaces which provides methods to deliver service requests from a requester to a multiplicity of service providers.
"Stateful CIS" exchange actors
The “Simple CIS” exchange pattern is described in the following subclauses.
#### Basic exchange pattern
In a "Stateful CIS" context, the service provider provides a mechanism to receive a service request from action taken at a service requester site. This will result in the service requester invoking specific methods /resource offered by the service provider. On the reverse side a mechanism is also needed to enable the service provider to feed back the result of processing or action triggered by the service request, so the service requester itself provides a mechanism to receive a service feedback from the involved service providers when their actions or processes results are available.
Besides "Simple CIS" service request and service feedback methods the stateful cis client also provides a "keep alive" method to implement link monitoring capabilities among service requester and service providers, the keepAlive method is used from the service requester to advise the client when no service request are to be delivered, so the service requester delivers a "keep alive" message to check and enable the service providers to verify that exchange systems and network connection are available, despite the service requester doesn't need to exchange payload content. "Keep Alive" messages are delivered by the service requester to the service providers, according to a time interval which is defined among them.
"Stateful CIS" session management methods are available to implement session management features in the same way they are described and available for "Stateful Push" FEP+EP PIM; such methods, namely openSession and closeSession usage which are used to define dynamic exchange information context to enable session management exchange features.
Figure 36 shows the communication diagram for "Stateful CIS" FEP + EP.
In this FEP+EP framework the service requester delivers a service request trigger to the service provider and the service provider delivers service feedback information to the service requester.
Therefore, the "Stateful CIS Service Requester" logically "pushes" "CIS Service Requests" messages, embedded in a "MessageContainer", to the "Stateful CIS Service Provider" which shall acknowledge the reception of such messages by a return message, embedded in an "ExchangeInformation". This exchange information return message is available to bring information back from the "Service Provider" to the "Service Requester", such as failure, success. Return message information is logically described in this PIM, while implementation will be defined at PSM level.
At the same time, the involved " Stateful CIS Service Providers" logically push "CIS Service Feedback" messages, embed in a "Message Container" to the " Stateful CIS Service Requester" which symmetrically shall acknowledge the reception of suche messages by a return message, embedded in an "ExchangeInformation". This exchange information return message is available to bring some information back to the "Service Provider" which management is not relevant to this FEP+EP and is not described in this document.
The management of any further workflow based on any processing or action errors is in this workflow framework pattern based on CIS "Service Feedback" is only in charge of the "Service Requester" System and is defined at application level based on the specific application requirements needed to enable the specific collaborative ITS services.
In the context of this "Stateful Push" FEP +EP framework, to enable interoperability among CIS service requester and CIS service providers, all rules defined in this clause apply.
Any simple CIS service provider exchange system SHALL realise a stateful CIS service provider interface which provides a putCISServiceRequest method, and an openSession, closeSession and keepalive methods.
Any simple push service requester exchange system SHALL realise a simple cis service requester interface which can invoke the putCISServiceRequest, openSession, closeSession, keepAlive methods provided by the simple cis service provider interface to deliver cis service request to trigger action/process by the service provider systems.
Any simple CIS service requester exchange system SHALL realise a simple CIS service requester interface which provides a putCISServiceFeedback method.
Any simple CIS service provider exchange system SHALL realise a simple CIS service provider interface which can invoke the putServiceRequest method provided by the simple CIS service requester interface to deliver CIS service feedback to the service requester systems.
The next figure shows the communication diagram for simple push FEP + EP.
In this FEP+EP framework the service requester “pushes” service requests messages to the service provider and the service provider "pushes" service feedback messages to the service requester.
Both service provider and service requester shall acknowledge the received service request or service feedback messages by a return information to the corresponding counterpart, i.e. respectively to the service requester and to the service provider. This return information shall be coded as ExchangeInformation.
Note
This return message is available to bring some exchange information back from the receiver system which may be used for any further exchange features implementations or application-level checks or processing and/or workflow management decision in CIS implementation which are out of scope of this document.
Stateful CIS exchange subsystems, interface interactions and methods
#### Relevant exchange information from exchange data model
Basic exchange data model has been provided to allow the implementation to enable CIS features to support information processing and enable distributed transactions features.
CIS Information embed all information needed to request for specific processing and to enable workflow management to support transaction negotiation processes by service request and service feedback messages.
Exchange information enables to deliver the Exchange context of involved service requester and service providers to enable orchestration of ITS services supply and exchange dynamic information which enables general exchange status information to monitor transactions negotiation or service processing in general.
Exchange information
Some non-mandatory information which should be managed in the exchange information for easy application development are fully described in basic exchange data model:
- Service Provider Identification
- Requirement: Supplier identification. (String)
- Client Identification
- Requirement: Client identification. (String)
- Exchange Information (provided both by the client and the supplier) wraps exchange and exchange status information "Success", "Fail", "Close Session Request", “SessionId”
- Generation timestamp information
- Requirement: timely, reliable Information
CIS information
- Service Request
- It provides the reference to element to be processed and the requested action, also addressing the service for which the action is triggered:
- Predefined service
- Requirements: Support for information processing, Distributed transaction
- Requested Action
- Requirements: Support for information processing, Distributed transaction, Distributed atomic transaction
- Service Feedback
- Requirements: Support for feedback on information processing, Distributed transaction,
- Service request status
- Requirements: Support information processing, Support for feedback on information processing, Distributed transaction
Exchanged messages
Different messages or supplier / client interactions (invoked method) are exchanged in Simple Push which are needed to manage synchronisation, payload exchange, link monitoring. These are formally contained in pushed messages to a client from a supplier or in return messages from client to supplier.
Interaction message | Direction requester provider | Designation | Description | Exchanged information | Optional
Open Session | Direct | openSession | Service requester initialise a stateful cis session with the involved service provider. | Exchange Information | N
Push delivery of a service request, which has to be delivered from service requester to the service provider.
CIS Information is delivered in the specific container to address the instruction to process information and/or implement the requested service.
Exchange information such as requester and service provider identification and exchange status are provided to easy controls.
Message Container including:
Payload (optional when not delivered in former Data Delivery Exchange) + CIS Information (Mandatory service request information) + Exchange Information with relevant information to enable exchange features
Service Request | Direct | putCISServiceRequest | N
Push delivery of a CIS Service Feedback.
CIS service feedback Information is delivered in the specific container to address the status and result of processing and/or and/or implementation of the requested service.
Exchange information such as client and supplier identification and exchange status may be provided to easy exchange related controls.
Message Container including:
Payload (optional when not delivered in Data Delivery Exchange) + CIS Information (Mandatory service feedback information) + Exchange information with relevant information to enable exchange features
Service Feedback | Return | putCISServicefeedback | N
Keep Alive | Direct | keepAlive | Test exchange link and confirm session validity when no service request or feedback is exchanged. It shall deliver the Session ID of a previously opened session, wrapped in Exchange Information. | Exchange Information | N
Close Session | Direct | closeSession | Message to gracefully close a stateful cis session, initiated by the service requester. | Exchange Information | N
Exchange Information Return | Return (Direct on Service Feedback) | D2Exchange Information | Exchange information is returned from client to supplier to provide return status i.e. Success, Fail and exchange context information to easy controls such as supplier and client identification. | Exchange Information | N
#### State Diagrams
The service requester initiates the communication and by open session and keep alive messages can be aware of the service provider status based on return messages or possible communication errors.
The following diagram describes the internal service requester status and the corresponding service provider status as monitored and managed by the service requester.
CIS requester-side Stateful CIS state diagram
The following diagram describes the internal service provider status and the service requester status as monitored and managed by the service provider.
CIS Provider-side Stateful CIS state diagram
Specific management in the initialisation and termination of a push process should be considered at the application level in the supplier and client systems.
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
After the session state management diagrams, at exchange initialisation a session needs to be initiated, an “Open Session” is tried in loop until it succeeds.
A failure when opening a session includes cases of a client who has not subscribed or is not authorised. Checking this can be ensured at the PSM level (e.g., this could include VPN setting or IP firewall or signatures handling), logical information may be included in exchange data to be managed in subscription check at the service provider side.
When a session is "ON" the service requester may send service request to involved service providers when all conditions to start a CIS service are triggered.
In case no CIS Service requester triggering condition occurs a" Keep Alive" message is used to check session status for the supplier and the client.
When no "Keep Alive" message or no payload is received, after a "Keep Alive" time-out the service provider invalidates the session on its side and returns a "Close Session" message at firse received message of any type.
If any service request or keep alive fails, the service requester invalidates the session and starts a new loop to open session.
Any message and return in the sequence diagram (Figure 38) will be mapped in PSM definition to real platform available implementation such as a web service "Service request and return" or any other available mechanism in a specific platform.
Link monitoring
After "Keep Alive" mechanism introduced in the previous session life cycle, service requests and keep alive messages are exchanged which give evidence to the service requester and service providers about the session and systems status.
When no service request or feedback are exchanged and a time-out has expired a "Keep Alive" message is exchanged to check the network and system availability.
In case service request or service feedback or "Keep Alive" fail, the session shall be invalidated.
#### Information management
Overview of information management features
Besides the Service Request and Service Feedback handshaking which is fully described in the equivalent "Stateful CIS" clause, Stateful CIS implements them in the framework of a stateful session, which implementation make aware the application side Service Requester about the availability and session status of all service providers which are involved in the Collaborative ITS Service implementation. This enables the decision process to trigger and manage CIS to involve information about involved CIS Service Provider status and availability.
All application-level rules about decisions to trigger services and involved providers orchestration functionalities of CIS are out of scope of the exchange specification and are not described in this document.
Support information processing
This clause description and specification for "Stateful CIS" are the same as the equivalent "Simple CIS" clause.
Distributed transaction
This clause description and specification for "Stateful CIS" are the same as the equivalent "Simple CIS" clause.
Data delivery
Not managed in this EP+FEP.
In Stateful CIS FEP+EP PIM it is assumed that data delivery requirements to deliver data to be processed are enabled by a parallel Data Delivery exchange and referenced in CIS Information to specify the relative processing action, despite payload data can be also delivered in a Service Request or Service Feedback when needed by specific application-level management, it can be assumed delivered in a previous exchange. The responsibility of data availability to support actions and processing requests are assumed to be in charge of the "Service Requester System" itself.
#### Self-Description
Handshake not available.
#### Communication
Communication features are implemented at PSM level, they are relevant to the specific Platform chosen on which the Exchange pattern will be implemented (e.g., http/XML, Web Services SOAP, REST).
#### "Stateful CIS" SOAP webservices PSM definition
The “Stateful CIS" SOAP web services implementation is defined according to the "Stateful CIS" FEP + EP PIM description.
In the “Stateful CIS" SOAP webservices exchange interface at service provider side:
- The SOAP WSDL method to implement putCISServiceRequest shall be the wsdl method named " putCISServiceRequest" which shall accept as input an "MessageContainer" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
- The SOAP WSDL client method to implement openSession shall be the wsdl method named "openSession" " which shall accept as input an "ExchangeInformation" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
- The SOAP WSDL client method to implement closeSession shall be the wsdl method named "closeSession" " which shall accept as input an "ExchangeInformation" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
- The SOAP WSDL client method to implement keepAlive shall be the wsdl method named "keepAlive" which shall accept as input an "ExchangeInformation" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
In the “Simple CIS" SOAP webservices exchange interface at service requester side:
- The SOAP WSDL method to implement putCISServiceFeedback shall be the wsdl method named "putCISServiceRequest" " which shall accept as input an "MessageContainer" XML message data structure and shall return an "ExchangeInformation" XML message data structure.
Messages are implemented by SOAP protocol adding SOAP envelope information. The corresponding WSDL file is can be downloaded.
Specific xsd definition profiled for the Stateful CIS FEP+EP can be downloaded.
Note
Full model xsd definitions for Basic Exchange Data Model MessageContainer can be downloaded, FEP+EP profiled xsd are strongly suggested to reduce data redundancy and enable clearer data exchange to implement.
Go back to the previous page
