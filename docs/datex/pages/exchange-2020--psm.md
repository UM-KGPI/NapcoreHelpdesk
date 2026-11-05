url: https://docs.datex2.eu/v3.7/exchange-2020/psm/
title: Platform Specific Model

## Platform Specific Model
### Exchange modelling framework
#### Web Services overview and options
Web Services provides standard means of interoperating between different software applications, running on a variety of platforms and/or frameworks.
Definition (W3C - Web Service architecture - http://www.w3.org/TR/2004/NOTE-ws-arch-20040211): « A Web Service is a software system designed to support interoperable machine-to-machine interaction over a network. It has an interface described in a machine-processable format (specifically WSDL). Other systems interact with the Web Service in a manner prescribed by its description using SOAP messages, typically conveyed using HTTP with an XML serialisation in conjunction with other Web-related standards. »
Web services definitions offer several options. Table 1 shows the options chosen by the PSMs described in this document.
Web Service Options | Decision
Discovery | Not dynamic : UDDI is not used, the Web Services are described in this DATEX II document which is the reference for development
Security | The security set-up has to be decided by the Supplier, should be negotiated with the Clients, and is outside the scope of this specification
Encryption | This has to be agreed between the Supplier and the Client, before starting data exchange
Table 1 Web Services options
#### Web Services PSM mapping of FEP+EP PIMs
Platform Specific Model (PIM) specification to implement FEP+EP PIM based on WS SOAP technology consists in mapping the abstract UML messages ( invocation methods and data types ) defined at FEP+EP PIM level as UML collaboration and sequence diagrams in ISO TS 19468 clauses to the corresponding SOAP WSDL methods and data structure.
Go back to the previous page
