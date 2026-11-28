url: https://docs.datex2.eu/v3.7/exchange-2020/pim/
title: Platform Independent Model

## Platform Independent Model
### Business scenario: Information delivery
#### Overview
One of the most common applications of a data exchange system is the exchange of traffic and travel information between two nodes. In such a scenario, one node acts as the supplier of the information while the other acts as the intended receiver of that information, i.e. the client.
EXAMPLE: It is done by using the form of publications, e.g. in the European DATEX II.
The data delivery business scenario considers the actors as defined in following figure:
General Data Delivery Business Scenario actors
The following table provides the basic definitions for exchange:
Name | Definition
Supplier System | A system which gathers information (road information) which needs to be conveyed to another system named client system. Examples of supplier systems are traffic control centres or traffic information centres or service provider systems, gathering road data from any available source they have.
Client System | A system which needs to update its internal information based on information which is available from another system named supplier. Examples of client systems are traffic control centres or traffic information centres or service provider systems.
Exchange Environment | The set of components which enables information exchange among client systems and supplier systems via a data exchange protocol.
Supplier | The component of exchange environment which is devoted to providing data to client, retrieving them from supplier system.
Client | The component of exchange environment which is devoted to collecting data from supplier, delivering them to the client system.
Main Definitions in Exchange
Road and traffic information is gathered in a system which is named "Supplier System”. In case this information is needed by another system, named "Client System”, for any purpose, it has to be transferred among the two systems by the exchange environment.
The data delivery business scenario describes the exchange pattern and messages which are needed to be exchanged among supplier and client systems besides the underneath technology and exchange pattern. The purpose for which information is exchanged is not considered in this use case description.
As explained in the information delivery background in Annex F , any update of information status at the supplier system shall be replicated to the client system via information delivery. The main objective of information delivery is that information on the client system is updated exactly in the same way as it is in the supplier system without any difference in information values and semantics.
"Exchange message” is defined as the data structure in which the information is coded to transfer information in the exchange system from the supplier to the client.
Assuming Sc = Client status, Ss = Supplier status, exchange is a mean to have Sc equivalent to Ss,
Formally:
Ss >> Information >> Supplier >> Exchange Message >> Client >> Information >> Sc
i.e. Client System Status is updated in equivalent mode as Supplier System Status by means of Data Delivery Exchange Messages through Supplier and Client.
Information delivery business scenario scope is implemented by selected exchange features which enable this scope and other secondary requirements which are based on available features on considered platforms and patterns.
- Supplier system characterisation
- Shall provide data as input to the data exchange environment
- Is mandatory for the information data delivery process
- Data exchange environment
- Shall be an environment supporting the exchange of information and data by means of messages
- The supplier, of data exchange system, shall produce and transmit the messages (Notification)
- The client, of data exchange system, should receive and process the messages
- Client system characterisation
- Shall receive traffic and travel related data from the data exchange environment
- Can be either another system for further processing or a simple client for the content visualization, the purpose of information exchange is not considered to be relevant in information delivery business scenario
- Is mandatory for the information data delivery process
#### Requirements
The normative Annex B provides a description of all requirements that can exist for a specific Business Scenario including Information Delivery whether they are used in a particular functional exchangeprofile or not. All requirements are organised into groups based ontheir characteristics.
Note
A FEP is a different concept from content profile. The description of the content profiles that can exist in an information delivery scenario is not in the scope of this document. Content profiles are handled in respect to which information is exchanged.
#### Data Delivery Exchange Pattern
For data delivery the concept of ”EP” is introduced, as well as PIM and FEP. These are defined as in Terms and definitions in the introduction.
Examples of exchange pattern are the GET method of HTTP, Pull, Push, PubSub, etc.
Once an exchange pattern and a selection of features (FEP) which can be implemented on this exchange pattern are set, a set of specification at PIM level for EP+FEP is well defined.
A PIM for EP+FEP that enables all mandatory requirements is a valid platform for the corresponding business case (information delivery or collaborative ITS services).
#### Specific Exchange Pattern Specification PIM included in this PIM part
In the following chapters PIM for Exchange Pattern/FEP will be described for the following platform:
- Snapshot Pull
- Snapshot Push
- Simple Push
- Stateful Push
The normative Annex E Major Functional Exchange Profile details the features of the main FEPs considered here for the corresponding exchange pattern.
### Business scenario: Collaborative ITS Service
#### Overview
A service is any processing of data which enable a value to the data themselves.
In ITS fieald "ITS Services” can be considered as the processing of information to address specific requirement such as to manage traffic, deliver information.
"Collaborative ITS services” (CIS) are "ITS Services” which can be enabled by combing different "ITS Services” which are provided by several stakeholders which may have different roles (e.g. Traffic Management Centers, Traffic Information Centres, Service Providers).
CIS exchange specification explore user requirements and define common techniques to address them to implement collaborative "ITS services” by different centres. They are based on exchanging information to be processed by the different nodes and receiving the processing outcomes (feedback), giving a simple mechanism, upon which it could be possible to build more sophisticated workflows, enabling to coordinate operations distributed among many centres.
In CIS business scenario the exchange of information among centres is considered as a base mechanism to trigger specific processing and to provide services on this data, so the data exchange layer is to be considered as an "ITS services” enabler.
"ITS Services” description is out of the scope of this document: a detailed description of possible usage of CIS detailed in informative Annex G.
Example of "ITS Service” in the different "ITS domain” are:
- TIS: Traffic Information Services
- Information Delivery
- Allowed Channels
- TMS: Traffic Management Systems
- Hard Shoulder Running
- Dynamic Speed
- Dynamic Lane Management
- etc.
- F&L: Freight&Logistic
- Secure Truck Parking
- etc.
#### Data exchange enabling service request and feedback paradigm
The involved systems, which in data delivery had been considered as supplier and client, can be considered in this paradigm respectively as service requester and service provider.
At application level, for implementing a business case, such as management of TMP, workflow management is usually requested; this could be a simple workflow (one shot request and acceptancs or rejection) or a more complex one: complex workflow modelling at application level is out of the scope of this document. This document provides the essential tools as building blocks to implement such simple workflow to a raise service request and provide feedback as exchange of payload to be processed and processing results.
CIS enabling mechanism:
- Service request delivery from service requester to the involved service providers.
- Service feedback delivery from service provider to the relative service requester.
CIS main characteristics are as follows:
- collaborative: 2 to many systems interact to achieve a common objective by processing data and exchange processing results;
- CIS modelling consider using a set of "1 to n" exchange connections considering any single CIS triggering request as 1 service requester and 1 to many service providers so that any complex interaction can be considered a combination of single usages from multiple requesters;
- possible lock of resources at service provider sides which are to be managed at application or human operator level are not described in the document.
#### Requirements
The normative Annex B provides a description of all requirements that can exist for specific business scenario including Collaborative Information Services
#### Specific CIS exchange pattern specification PIM
- Simple CIS
- Stateful CIS
The normative Annex G Collaborative ITS Services Background details the features for the corresponding exchange pattern.
### Exchange Data Model
To implement some exchange features, such as session management or link monitoring, or security features, extra information is to be added to the informational (payload) content. This extra information, named exchange information, enables messages to convey information and data which are related to client and supplier status, identity, authorisation, etc.
Exchange information could be different among EP+FEP selection, but some common general information models are considered, which can be specialised to manage specific exchange pattern and PIM.
A general UML model for managing a minimum set of information for exchange is provided in Annex C.
### Data exchange features
#### Context Diagram
This document defines the features and rules that systems shall implement in order to be able to communicate in the traffic and travel data exchange world.
The context diagram below in Figure 5 shows the entities and the features specified in this document and which need to be addressed by the technical implementations. The diagram presents the features in different layers for communication, message rules and application:
- The "Application layer” is used for defining how using and implementing different business and application needs. This document describes the features to deal with how and when the information is published and made available, how subscriptions are managed, how to handle services and transactions. This layer defines the semantics of the communication.
- The "Messages Rules layer” defines the features and the rules used for the transport of the messages. This is the layer where the rules (protocol) are defined that enable different systems (suppliers and clients) to communicate and understand each other, i.e. for sending and receiving messages. This layer defines the syntax of the communication.
- The "Communication layer” deals with the support for communication between systems, and defines the protocols and services used by the data exchange applications, e.g. TCP/IP, security, web services. The communication layer deals with rules at the lowest level, i.e. the physical exchange. This layer provides solutions to the defined requirements and features although it is up to upper applications to define what protocols to use and how to use them. This layer defines the physical support for the communication.
The context diagram below (Figure 5) shows the topics broken up into boxes representing the exchange features and the relation with each layer.
Figure 5 - Context diagram
#### Features
The features that support the requirements defined by use cases specified in this document are detailed below:
The "Subscription contract”, detailed in the table below, supports all features related to the contract or agreement, such as:
- Contract and contract life cycle: a model and features that can be used for the support of the information of a subscription contract
- Catalogue: a model for handling catalogues;
The subscription contract is optional and may include the following features:
Features | Requirement Type | Requirement Name
Contract | Information | Subscription
Client profiles
Filter handling
Catalogue | Information | Catalogue exchange
The "Session" feature group, detailed in the table below, supports all features related to the establishment of a logical session.
- Session life cycle – features for managing the life cycle of a logical session (create, manage and terminate);
- Link Monitoring – features for link monitoring and control;
The session feature group is optional and includes the following Features:
Features | Requirement Type | Requirement Name
Session life cycle | Communication | Error handling
Timeout management
Session
Link Monitoring | Communication | Error handling
Timeout management
Full reliability
Link monitoring and control
The "Information management" handles the features related to the management of the information, includes features such as:
- "Operating modes": features to specify what portion of the information shall be exchanged
- "Update methods": features that let a data exchange system specify when the information should be exchanged
- "Lifecycle management": features for handling the life cycle management of exchanged payload information for payload for which life cycle is applicable;
- Situation lifecycle management
- Filter handling
- "Support information processing": feature for handling directives to process exchanged data and send feedback on processing outcomes.
- Distributed transaction: features for handling a transaction on several systems consistently, i.e. an operation is capable to keep data consistency among several systems based on operator undertaken actions. The information management group includes the following features:
The "information management" group includes the features listed in the following table.
Features | Requirement Type | Requirement Name
Operating modes | Information | Reference datasets for different versions
Update methods | Information | Full audit trail data delivery (all state changes)
Lifecycle management | Information | Support for life cycle management
Support Information Processing | Information | Support for information management
Support for feedback on information management
Distributed transaction | Information | Distributed transaction
Distributed atomic transaction
The "data delivery" feature group supports all features to exchange data between the supplier and client. In the publish-subscribe pattern this feature group will support all related interfaces between the producer and the consumer; it supports features such as:
- Data delivery: features to delivery information by the supplier to the client on a push mode (direct delivery and fetched delivery);
- Data request: features to exchange information requested by the client;
- Large datasets: support the exchange messages with large volumes;
- Synchronisation: how to ensure data synchronisation between the systems that are communicating.
The "data delivery" group includes features and requirements listed in the next table.
Features | Requirement Type | Requirement Name
Data delivery | Information | Extensibility
Communication | Delivery/response
Message sequence
Snapshot data delivery (last known state)
Exchange quality measures (ex. response timestamp)
On occurrence update
Periodic update
Security | Client identification
Supplier identification
Information | Incremental data delivery
Data request | Information | Extensibility
Communication | Request/response
Message sequence
Snapshot data delivery (last known state)
Exchange quality measures (ex. response timestamp)
On occurrence update
Periodic update
Security | Client identification
Supplier identification
Large datasets handling | Information | Data delivered as soon as possible
Delayed delivery
Multi-part data delivery
Synchronisation | Information | Synchronisation
Communication | With state supplier
Failed data recovery
Communication – Handles all features related to the protocol (close to the physical layer). It is used by the application for the message transport.
- Communication – describe the protocols of communication that can be used;
- Security – describe how security features can be implemented;
- Compression – how data compression can be used while transmitting data.
- Bidirectional communication – enable client to send back data to supplier as feedback on data exchanged and processing status of data based on supplier processing directive in Collaborative ITS Services The communication function is responsible for implementing the following Features:
The communication function is responsible for implementing the following features:
Features | Requirement Type | Requirement Name
Security | Security | Security (data)
Integrity
Confidentiality
State the intended recipient
Client authentication
Supplier authentication
Client authorization
Non-repudiation
Compression | Communication | Compression
Communication | Communication | Timely responses
Bidirectional communication | Communication | Bidirectional communication
### Exchange Pattern modelling using UML
Exchange patterns which enables features for selected FEP can be described by use of some UML diagrams which describe which actors are involved in the exchange, and the specific interactions among them which enable the features themselves.
Exchange system description assumes external systems like TCC and TMC are external to exchange and exchange agents are the actors which may implement the exchange role of client, supplier, service requester or service provider as defined in the business case.
The Figure 6 describes the main exchange involved actors as well as other interacting actor external to exchange.
Figure 6 — Exchange actors
Systems (e.g. TCC or TMC system) may act both as client or supplier and for exchange purposes, systems need to interact with the exchange agent, of the same client or supplier type, which realise a system interface enabling the exchange features.
Based on multiple option for a system to be a client or supplier for Data Delivery, or a Service Requester or Service Provider for Collaborative ITS Services business scenario, the relative system and interfaces can specialise. Figure 7 and Figure 9 shows the exchange agent and interfaces specialisation respectively for data delivery
Figure 7 — Data Delivery Exchange actors definitions
Figure 8 — Communication: Features and requirements
Figure 9 — CIS Exchange agents definition
Figure 10 — CIS Exchange systems, agents and interfaces
This system, exchange agents and interfaces classes will be used in any of the FEP+EP specification descriptions in the following clauses to describe the provided interfaces and interactions. Each of exchange interface realisation will be implemented as a specific specialisation for its FEP+EP, e.g. Snapshot Push will have its specific "snapshot push" supplier interface", i.e. the "Snapshot Push Client Interface", which will be described as a specialisation of the exchange snapshot push client interface. The modelling for a snapshot push client system and its Exchange agent and interface is shown in Figure 11.
Figure 11 — Sample of "Snapshot Push" client system and its Exchange agent and interface
The relevant Communication Diagrams will be introduced in the FEP+EP descriptions in the following clauses. In the description of the interactions among exchange systems and subsystems UML Sequence Diagrams will be used. Interactions among actors and their interfaces are described using the actor themselves, the realised specialised interfaces are not mentioned for schema understanding convenience. Figure 12 is an example of provided Sequence Diagram.
Figure 12 — CIS Exchange actors
State Diagrams can be used as well to specify specific status of exchange operation which will lead to specific interfaces behaviours such as return messages definition and specific interaction provided (e.g. synchronisation, synchronisation request). State Diagram are not needed for understanding in simple cases such as stateless FEP+EP so they will not be described in some FEP+EP descriptions.
Go back to the previous page
