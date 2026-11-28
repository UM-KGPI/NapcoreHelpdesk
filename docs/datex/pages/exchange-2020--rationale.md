url: https://docs.datex2.eu/v3.7/exchange-2020/rationale/
title: Exchange Specification rationale

## Exchange Specification rationale
Unlike payload content DATEX II Specifications, which had been well assessed and designed through more than a decade and standardised into CEN TS/EN 16157 family standard, Exchange Specification had taken a longer process. This has led to several option to implement DATEX II content exchange, based on different requirement from different DATEX II application field.
To grant the correct exchange of data among Traffic Control (and Management) Centres (TCC/TMC) and Traffic Information Centres (TIC) and Service Provider, the so-called Low Cost Profile (LCP) specification based on HTTP/get, had been fully available since 2006 DATEX II version 1.0 and fully specified in DATEX II version 2.0 specification. This HTTP/get method enables content exchange among centres based on a simple handshaking providing snapshot of information from the supplier to the clients it delivers its payload, all the content always is sent and needs to be processed to fully obtain the current valid information (cancelled or closed information is not present in the snapshot).
To optimise bandwidth and processing a push on occurrence exchange specification had been introduced since version 1.0 but this specification had not been fulfilled to achieve a fully consistent and reliable specification, with error management and fulfilling all requirements e.g.- restarting a link connection after some maintenance activities or network unavailability.
But requirements for exchange may be of a very different nature and contradictory, such as to have a stateless server and save bandwidth and most of processing at client size, so there is a need to gather a set of consistent requirements which may be implemented by a number of exchange features to define a set of consistent and effective exchange specifications.
A concept of Functional Exchange Profile and implementing Exchange Pattern (FEP+EP) had been introduced to define the set of consistent features enabled by a certain abstract technology which may fulfil a set of such consistent requirements. Those FEP+EP behaviour specification may be defined at abstract level in a Platform Independent Model (PIM) which can be afterwards described for a specific technology as Platform Specific Model (PSM)
This approach led to Exchange 2018 Specification which had been released to support DATEX II version 3.0 which had been now evolved and completed in Exchange 2020 Specification, supporting DATEX II version 3.1 specification.
Exchange specification supporting DATEX II are being standardised by a joint CEN and ISO process, leading to 2 different ISO/CEN specifications:
- PIM specification as ISO/CEN TS 19468:2019 as Exchange specification 2018 which are evolving in a revision to fulfil all Exchange 2020
- PSM specification as ISO/CEN TS 14827-4: standardisaton process undergoing
### Data Delivery Business Scenario
Data Delivery is the major feature which is supposed to be enabled by an Exchange System: data are available at a site named supplier which are needed at a different site name client, the objective of Data Delivery Business Scenario is to have the information available at supplier site exactly duplicated at client site.
Based on different requirements Information Delivery Data Exchange Business scenarios may be implemented by several FEP+EP pattern as explained in the Exchange Guide.
Information Delivery FEP+EP defined in Exchange 2018 and Exchange 2020 led to Platform Specification model specification based on SOAP webservice which also include a specific http/GET profile (also known as LCP profile)
- Snapshot Pull (which may be implemented also as HTTP/get specification)
- Snapshot Push
- Simple Push
- Stateful Push
### Collaborative ITS Services Business Scenario
Exchange specification supporting DATEX II version 1.0 and 2.0 had taken into account only requirements to support Information Delivery Business Scenario, e.g. the objective of the exchange specification was intended only to deliver information content from a supplier to a number of clients and supplier are not interested to be fed back of any information processing outcome which may be undertaken at client sites.
Instead for some kind of applications, information is delivered among a supplier and its clients to enable and support some coordinated processing which results are needed as feedback at supplier side in order to be aware requested process has been correctly implemented in order to trigger further "actions". Example of such processing are activation of specific Traffic Management Plans or setting of peripherals such as messages to be displayed by variable message signs.
These application features based on exchange are the Collaborative ITS Services business cases which are enabled among TCCs, TICs, and SPs, in a model a node acts as a CIS service requester and other nodes act as CIS service provider, by further FEP+EP besides the Data Delivery ones.
Collaborative ITS Services CIS specification had been elaborated by DATEX II organisation among the years. To implement a CIS FEP+EP pattern compatible with DATEX II version 2.x specification, an official DATEX PSA released extension based on version 2.3 and implementable by Information Delivery exchange specification had been provided in 2018 leading to DATEX Collaborative ITS Services and Traffic Management Plans Extension available at DATEX website extension directory as https://datex2.eu/implementations/extension_directory/datex-collaborative-its-services-and-traffic-management-plans which includes
- Traffic Management Plan (TMPlan) managed by a TMPlan Table publication and TMPlan activation publication
- CIS specification: processing support and TMPlan workflow coordination features implemented by CIS Service Request and CIS Service Feedback publications.
Those specifications had led to a CIS demonstrator which had been explained and documented on a recent website article after a CIS demonstrator had been developed and run in Italy and UK https://datex2.eu/news/collaborative-its-services-cis-demonstrator.
Those solutions, which had been developed for DATEX II version 2.3 as an official release DATEX II extension available on DATEX II website but won’t be standardised in this format.
For Traffic Management Plan content specification, after version 2.3 harmonised proposal, a joint action with CEN among two sub-groups (CEN TC 278/WG8 and CENTC278) led to an updated specification which is contained today in TS 16157-8 which had been recently delivered by CEN: this specification deal with Traffic Management Plan content which will be available in DATEX II version 3.1 to be delivered.
The part which deals with the exchange specification led to Exchange 2018 (deprecated) which is not supported fully as Exchange 2020. CIS standardisation process is still undergoing and is currently being managed as explained in joint Work Items both in CEN and ISO.
For DATEX II version 3.1 communication Exchange Specification 2020 are available at https://docs.datex2.eu/exchange2020/userguide/index.md.
### Synopsis of Available Exchange Specifications
- DATEX II version 3.x
- Exchange 2020: updated exchange model and fully described exchange specification PIM and PSM including,
- Data Delivery Business Scenario specification for SOAP WS
- Snapshot Pull
- Snapshot Push
- Simple Push
- Stateful Push
- Collaborative ITS Services Business Scenario specification for SOAP WS
- Simple CIS
- Stateful CIS
Note
For TMPlan management DATEX II version 3.1 includes TMPlan payload model which will also be published as CEN TS 16157-8
- DATEX II version 2.3
- Data Delivery specification available supporting DATEX 2.x version
- PIM https://docs.datex2.eu/exchange/downloads/modelv23.md#datex-ii-exchange-pim.
- PSM https://docs.datex2.eu/exchange/downloads/modelv23.md#datex-ii-exchange-psm.
- Implemented methods
- Pull
- Snapshot Pull as HTTP/get
- Push
- Collaborative ITS Services official extension available on website https://datex2.eu/implementations/extension_directory/datex-collaborative-its-services-and-traffic-management-plans
- Exchange specification based on Data Delivery Business Scenario described as CIS model implementation
- CIS Service Request
- CIS Service Feedback
- Payload available in format 2.3 for Data Delivery
- TMPlan
Go back to the previous page
