url: https://docs.datex2.eu/v3.7/exchange-2020/demo/
title: Exchange 2020 profiles and demonstrators

## Exchange 2020 profiles and demonstrators
### Exchange 2020 BEDM profile
Exchange 2020 specification have been released to support DATEX II version 3.x data delivery and collaborative ITS services business scenario and relative use cases implementation. The corresponding Exchange Rationale and Exchange Guide helping developers to get oriented among the described functional profiles and exchange pattern have been provided at DATEX II docs website.
After specification Exchange 2020 PIM, the SOAP WS Services Platform Specific Model had been finalised which implements the Information Delivery and Collaborative ITS Service in SOAP Web Services technology, for which SOAP WSDL interfaces had been released which refers beside DATEX II v 3.0 to the Exchange related information described as Basic Exchange Data Model by specific XML Schema definition files which implement the information of messages as Message Container wrapping Payload ( DATEX II v3.0 content), Exchange Information, Information Management and CIS Information as described in Basic Exchange Data Model (BEDM).
As the Basic Exchange Data Model is a generic model designed to support the implementation of the several Pull and Push and CIS Exchange Pattern, tailored profiles to simplify the implementation of the specific FEP+EP defined in Exchange 2020 had been provided. Those profiles reduce the options of the BEDM model leaving in the XML only the information for the specific FEP+EP.
These profiles retailed XSD are available here:
- Snapshot Pull
- Snapshot Push
- Simple Push
- Stateful Push
- Simple CIS
- Stateful CIS
The option to obtain the complete set of XML Schemas, including BEDM, needed for DATEX II v3.0 implementation by SOAP WSDL will be released also as optional feature delivered embed the DATEX II profiling webtool, so to generate a complete set of XSD including profiled BEDM ones.
To grant WSDL and BEDM xsd had been well designed some exchange 2020 sample had been implemented in C# and JAVA using javaws and JAXB environment. That lead to the Exchange2020 demonstrator which is available for trial at the following link https://exchangedemo.datex2.eu/Exchange2020Client/.
The overall testing process for java is shown in the following figure:
The current Exchange 2020 user interface allow to test the different WSDL methods which are available in the Exchange 2020 FULL.wsdl which is an overall WSDL implementing all methods managed for any Exchange 2020 FEP+EP which is available here from the download page.
Choosing the WSDL operation method the GUI set an input XML when needed and allows to edit the XML itself, cut and pasting a custom XML which can also be uploaded from the "upload file" option; "restore default" reset the input content to the predefined test XML.
The SHOW WSDL button call the wsdl interface and display the runtime result in a window. For security reason in this demonstrator only the WSDL client GUI is accessible, the WSDL is in an internal organisation domain.
The arrow button allows to run the WSDL method and receive the output XML.
In case there is some formal error on the input XML a validation error is returned in the ouput windows as shown in the following example.
Another example of elementary test implemented is on session management choosing a close session method. When a session ID is not provided closing a session a logical error is detected and an error returned.
Specific XML feed had been retailed in the different Push and Pull cases based on the possible BEDM profiles which had been derived as explained above. You are invited to try and provide your sample to test your understanding of Exchange 2020 demo at the provided link https://exchangedemo.datex2.eu/Exchange2020Client/.
Go back to the previous page
