url: https://napcore.eu/wp-content/uploads/2025/03/Annex-C-Alternative-Fuels-Demonstrator.pdf
title: Annex C Alternative Fuels Demonstrator

[page 1]
Milestone 2.10 - Interoperability demonstrators with real -world use of data
and different Levels of Service - 2nd round)
Annex C - Alternative Fuels demonstrator with real -world use of data and
different Levels of Service
Status: final
Version: 1.4
Date: 11 March 2025
Legal disclaimer
The sole responsibility for the content of this document lies with the authors. It does not necessarily
reflect the opinion of the European Union. The European Commission is not responsible for any use
that may be made of the information contained therein. All images are provided by the respective
partners (unless otherwise noted) and are approved for reproduction in this publication.
[page 2]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 ii
Document information
Project acronym NAPCORE
Full project title National Access Point Coordination Organisation for Europe
Grant Agreement No. MOVE/B4/SUB/2020-123/SI2.852232
Activity no. and title WG2, Task 2.4, Work item 2.4.4 - Interoperable NAP demonstrator with
Metadata.
Author(s) Ligia Conceição, PT-Armis; Sara Linhas , PT -Armis; Peter Lubrich, DE-
Federal Highway Research Institute (BASt)
Co-author(s)
Related to Milestone no. 2.10
External Milestone yes
Document history
Version Date created/ modified by Comments
1.0 09.09.2022 Ligia Conceição, Armis 1st Draft
1.1 29.03.2024 Sara Linhas, Armis 2nd Draft
1.2 04.12.2024 Sara Linhas & João
Montenegro, Armis
Final draft
1.3 09.01.202 João Montenegro Final draft (after CAT review)
1.4 11.03.2025 Hannah Walther Final version after SCOM written
procedure
Document status:
☐ To be revised by partners involved in the preparation of the document
☐ For review/ approval by the Core Alignment Team and Peer Reviewers
☐ For approval by the NAPCORE Steering Committee
☒ Final
☐ Updated/revised final version (e.g. when a second version of Milestone is published)
[page 3]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 iii
Abstract
This report provides insights on NAP interoperability regarding the exchange of Alternative Fuels data.
It comprises the several steps of work of the development of an Alternative Fuels Demonstrator using
the NAPs. The analysis identified important aspects needed to increase the availability of AF data
throughout the NAPs. Moreover, it draws the current scenario of NAPs in the context of Alternative
Fuels, providing some baseline for other EU -initiatives that aim to enhance the adoption of AF
infrastructure by road users, particularly to the discoverability of AF data.
[page 4]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 iv
Abbreviations
Abbreviation Meaning
AF Alternative Fuels
API Application Programming Interface
EC European Commission
EU European Union
CKAN Comprehensive Knowledge Archive Network
DCAT-AP Data Catalogue Vocabulary-Application Profile
DR Delegated Regulation
LoS Level of Service
MS Member States
NAP National Access Point
NAPCORE National Access Point Coordination Organisation for Europe
NLKF NAP LoS KPI Framework
SWG Sub-working Group
WG Working Group
WP Working Programme
EAFO The European Alternative Fuels Observatory
[page 5]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 v
Table of contents
1. Introduction................................ ................................ ................................ .......................... 7
1.1. Motivation and scope .............................................................................................................. 7
1.2. Objectives ................................................................................................................................ 8
2. Background................................ ................................ ................................ ........................... 9
2.1. National Access Points (NAPs) ................................................................................................. 9
2.2. Metadata Demonstrator ......................................................................................................... 9
2.3. IDACS project ......................................................................................................................... 10
2.4. Sustainable Transport Forum ................................................................................................ 10
3. Solution design ................................ ................................ ................................ ................... 10
3.1. Initial Approach ..................................................................................................................... 10
3.2. Relation to other initiatives ................................................................................................... 11
3.3. Technologies/methods for Implementaçtion ....................................................................... 12
API Integration for OCPI and DATEX II ........................................................................................... 12
ETL Tools for Static Data Extraction .............................................................................................. 12
3.4. Requirement Analysis ............................................................................................................ 12
3.5. Definition of use cases........................................................................................................... 13
Use case 1: ENABLING DATA DISCOVERABILITY THROUGH NAP METADATA ............................... 14
Use case 2: FILTER THE AVAILABLE DATA BY CATEGORY AND EVALUATE DATA HARVESTING .... 15
4. Detailed architecture framework ................................ ................................ ......................... 16
4.1. Requirements / user needs ................................................................................................... 16
4.2. Software stack architecture per module ............................................................................... 16
4.3. Functional architecture ......................................................................................................... 17
4.4. Considerations for the implementation ................................................................................ 18
5. Results ................................ ................................ ................................ ................................ 19
5.1. Use case 1 Enabling Data Discoverability Through NAP Metadata ....................................... 19
5.2. Use case 2 FILTER THE AVAILABLE DATA BY CATEGORY AND EVALUATE DATA HARVESTING
20
6. Conclusions ................................ ................................ ................................ ......................... 21
6.1. Feedback to other NAPCORE WG2’s tasks ............................................................................ 21
Task 2.1 – NAPs Levels of Service .................................................................................................. 21
Task 2.3 – NAP architecture .......................................................................................................... 21
6.2. Lessons learnt and recommendations .................................................................................. 24
List of tables
Table 1.1 - AF datatypes and respective categories ................................................................................ 8
[page 6]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 vi
Table 2.1 - NAP typology definition (according to Milestone 2.9) .......................................................... 9
Table 4.1 - Software stack Architecture according to Demonstrator Functionality Layers .................. 17
Table 5.1 – Status of MobilityDCAT-AP implementation and number of datasets: comparison between
2022 and 2024 ....................................................................................................................................... 19
Table 6.1 - Essential KPIs for the extraction and processing of the data in the Demonstrator ............ 21
Table 6.2 - NRA Modules importance ................................................................................................... 22
List of figures
Figure 3.1 - Initial approach for the AF demonstrator .......................................................................... 11
Figure 3.2 - Analysis of EU NAPs concerning AF data availability and "ease" of metadata extraction . 13
Figure 3.3 - Description of use cases of the AF demonstrator .............................................................. 14
Figure 6.1 – M2.9 figure. Conceptualization of the metadata NAP Architecture ................................. 23
[page 7]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 7
1. Introduction
Working Group 2 (WG2), Interoperability and level of service of National Access Points (NAPs), aims to
enhance the compatibility of the National Access Points (NAPs) regarding their features, as well as the
harmonisation of their levels of service. In order to showcase options for enhanced interoperability,
this document describes the development of the Alternative Fuels Demonstrator. This report details
the solution design, the architecture framework, results and conclusions about the Alternative Fuels
Demonstrator.
The document is structured in the following chapters:
1. Introduction – including context, scope and objectives
2. Background – including relevant background information about important concepts which are
crucial for the development of the demonstrator
3. Solution design – including the description of the approach and respective use cases, as well
as the identification of technical requirements
4. Detailed architecture framework – contains the architectural and technological details used
for the implementation of the solution
5. Results – contains the main outputs of both use cases, including some discussion and analysis
of results obtained
6. Conclusions – including the most important lessons learnt and relevant feedback to other
NAPCORE tasks
1.1. Motivation and scope
This task considers the ongoing efforts by the European Commission (EC) to accelerate the adoption
of alternative fuel infrastructures across EU member states. A key initiative, which served as the main
motivation behind this report, is the Delegated Regulation Implementing Act (2023/1804). The
document was introduced to support the EU’s goals under the Alternative Fuels Infrastructure
Regulation (AFIR). It begins with a preamble that justifies the need for consistent EU -wide targets for
recharging and refuelling infrastructures, addressing growing transportation demands and
environmental goals. This framework ensures the development of accessible, harmonized
infrastructure for electric and hydrogen -powered vehicles, underscoring the European commitment
to energy transition and sustainable mobility.
The regulation's articles outline key infrastructure requirements, covering targets for recharging points
for both light -duty and heavy -duty electric vehicles (Articles 3 and 4), and the setup of hydrogen
refuelling stations (Articles 6 and 7). For each type of infrastructure, the regulation specifies targets
that member states need to meet, ensuring the widespread availability of alternative fuels.
Additionally, it covers standards for associated services, such as shore-side electricity in maritime and
inland ports (Articles 9 and 10) and power for stationary aircraft (Article 12). These provisions aim to
ensure that users of alternative fuels—whether individuals, businesses, or public entities—have access
to consistent and reliable fuelling and charging services across Europe.
In terms of data and monitoring, Article 20 mandates that EU member states appoint an Identification
Registration Organization (IDRO) by 2025 to assign unique identification codes for recharging
operators and service providers, facilitating seamless access to real -time data on infrastructure
availability and usage. The data, including the operational status of stations, charging capacities, and
prices, is to be made accessible to the public through open APIs and national access points. The same
article outlines the AFs’ data categories and datatypes, as described in Fehler! Verweisquelle konnte
nicht gefunden werden..
[page 8]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 8
Table 1.1 - AF datatypes and respective categories
Category Data type
Static data for publicly
accessible recharging points and
refuelling points for alternative
fuels operated by them
Geographic location of the recharging points and refuelling
points for alternative fuels
Number of connectors
Number of parking spaces for people with disabilities
Contact information of the owner and operator of the
recharging station and refuelling station
Opening hours
Further static data for publicly
accessible recharging points
operated by them
ID codes, at least of the recharging point operator
Type of connector
Type of current (AC/DC)
Maximum power output (kW) of the recharging station
Maximum power output (kW) of the recharging point
Vehicle type compatibility
Dynamic data for publicly
accessible recharging points and
refuelling points for alternative
fuels operated by them
Operational status (operational/out of order)
Availability (in use/not in use)
Ad hoc price
Electricity supplied is 100% renewable (yes/no)
1.2. Objectives
Since the delegated act mandates that Member States publish information related to alternative fuels
on National Access Points (NAPs), this work focuses on demonstrating the potential for discovering
and processing Alternative Fuels datasets available on these NAPs.
To that end, we established a set of specific objectives to be reached throughout this work:
• Explore how both static and dynamic could be made available and accessible at European level,
without creating storing duplicities with Member States’ NAPs repositories, considering NAP
format and need for harmonisation (linked to other WG activities)
• How a Mobility Data Space ( e.g. European Alternative Fuel Observatory EAFO) can use the
information from the NAP
• Explore p rocesses of harvesting AF data from NAPs (link, how to find, how to extract –if
possible)
• Establish a set of recommendations for NAPs to make alternative fuels data available
The document aims to provide a step -by-step analysis of the implementation of the demonstrator,
highlighting its design approach and shedding light on the current limitations within the field of
Alternative Fuels of the NAPs. Ultimately, the document serves as a critical resource for stakeholders
and decision-makers interested in advancing the harmonization and utilization of data from different
National Access Points for more effective and integrated use on a wide scale.
[page 9]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 9
2. Background
2.1. National Access Points (NAPs)
The Directive 2010/40/EU on Intelligent Transport Systems (ITS) and its Delegated Regulations
mandate the establishment of a National Access Point (NAP) for mobility data within each European
Member State. Currently, there are over 30 operational National Access Points, spanning across nearly
all EU Member States and beyond, wherein mobility-related data is disseminated and made accessible
for purposes such as travel information services.
While defining how NAPs can be set up, NAPCORE T2.3 proposed a differentiation of two NAP types,
which are described in Table 2.1. These are relevant for the conceptualization of the demonstrator and
therefore have been included in this report for reference.
Table 2.1 - NAP typology definition (according to Milestone 2.9)
NAP type Definition Key features
Metadata
Directory
Contains descriptions of the data and services important for their
identification, assessment and subscription by consumer, i.e. metadata. It
provides facilities to authenticate data provider and functionality to insert
a metadata records. The NAP provides search and discovery services of the
hosted records to end user and via machine readable to other portals. The
NAP is not involved in the data exchange process between data providers
and data consumers
Storage & provision of
metadata records of data,
services and providers;
search/discovery
functionality; data provider
authentication
Data
platform
Contains descriptions of the data and services important for their
identification, assessment and subscription by consumer, i.e. metadata,
together with the data and/or services themselves. It provides facilities to
authenticate data provider and data consumer and functionality to insert
a data and metadata records to NAP internal database. The NAP provides
search and discovery services of the hosted records to end user and via
machine readable to other portals and distribution interface for the data
dissemination. The NAP is an intermediary between data provider and
consumer, the data however remain in the ownership of the data provider
Storage & provision of
metadata records of data,
services and providers,
storage & provision of data
and services;
search/discovery
functionality; data provider
and data user authentication
2.2. Metadata Demonstrator
One of the main functions of the NAPs is to enable access and exchange of mobility data. A detailed
and standardized dataset description, the so -called metadata, facilitates such access by enabling the
discoverability of datasets within a NAP. Metadata describes the administration, organisation, and
content of a dataset and a data service. Metadata is, therefore, a crucial element in increasing the
discoverability of datasets published on the NAPs.
Regarding this, in NAPCORE task 2.4., a Metadata Demonstrator was developed for National Access
Points (NAPs) that showcased a harmonized approach for accessing and processing metadata . This
approach was used as a baseline for the methodology adopted in the Alternative Fuels Demonstrator.
However, the present work aligned with NAPCORE’s proposed metadata specification, mobilityDCAT-
AP. Such specification offers a catalogue that offers advantages to the discoverability of a specific data
category than ks to tags such as mobilityTheme 1. In the case of alternative fuels , the data content
categories that encapsulate this field of data are:
• Filling and charging stations
o Availability of charging points for electric vehicles
o Availability of filling stations
1 Mobility Theme
[page 10]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 10
o Location and conditions of charging points
o Location and conditions of filling stations
2.3. IDACS project
The IDACS (ID and Data Collection for Sustainable Fuels) was a European Commission -led project to
create a harmonized framework for managing and sharing data related to alternative fuel
infrastructure across EU Member States. Active from 2019 to 2022, IDACS focused on developing
National Access Points (NAPs) where standardized data on electric vehicle (EV) c harging stations,
hydrogen refuelling stations, and other sustainable fuel infrastructure could be stored and accessed.
A key component of the initiative was assigning unique identification codes to Charge Point Operators
(CPOs) and e-Mobility Service Providers (EMSPs) to ensure seamless interoperability of services across
national borders. By fostering standardized data collection and exchange, the initiative supported the
EU's goals of scaling up alternative fuel adoption and creating a unified, user -friendly ecosystem for
sustainable mobility.
A relationship between IDACS and a Demonstrator dedicated to Alternative Fuels data could focus on
advancing and showcasing the potential of unified data systems to optimize infrastructure planning
and user experience. By integrating and expanding upon the data collected through NAPs, the
Demonstrator could simulate future scenarios, assess infrastructure gaps, and support policy
development aimed at accelerating the transition to sustainable mobility. Furthermore, it could serve
as a testing ground for new technologies and standards, driving innovation in data -driven decisionmaking for alternative fuels.
2.4. Sustainable Transport Forum
The EU’s Sustainable Transport Forum (STF) focuses on enhancing data quality and interoperability in
alternative fuels infrastructure. It specifically aids in the collection, sharing, and refinement of critical
data regarding electric mobility and alternat ive fuels. This initiative ensures that data around fuel
station locations, availability, pricing, and technical standards meet high standards, which is essential
for developing the infrastructure to support the widespread adoption of these fuels across Europe.
Key efforts include overseeing data provision and quality control through the European Alternative
Fuels Observatory (EAFO), where the STF also facilitates data standardization and publishes
recommendations to guide policy and technical standards for alternative fuel usage across sectors like
road, rail, and aviation. EAFO acts as a central repository that supports government agencies and
stakeholders in tracking the deployment of alternative fuel stations, measuring data reliability, and
promoting public access to high-quality data across EU countries. This improves both transparency and
accessibility for consumers and stakeholders in the alternative fuels’ ecosystem.
3. Solution design
3.1. Initial Approach
The initial approach aimed to suggest how a Mobility Data Space could harmonize the access and
management of mobility-related alternative fuels data. The project focused on integrating data
sources from the Alternative Fuels Infrastructure Regulation (AFIR) and other stakeholders, structuring
them within a National Access Point (NAP) ecosystem, labelled as a component during the
implementation phase, and creating a unified output component to facilitate AF data discoverability.
This approach positioned the NAP as a critical intermediary in the data ecosystem, where providers
would supply data and links via APIs to the NAP. The NAP, in turn, would gather different datasets from
[page 11]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 11
various providers and make them available in a standardised manner through a cohesive interface for
mobility data consumers. Figure 3.1 illustrates this approach, while further explanation is given next.
Figure 3.1 - Initial approach for the AF demonstrator
Providers were expected to share data via dedicated APIs, offering static and dynamic AF infrastructure
information, such as the location of charging and fueling stations and availability of charging and
fuelling points . This would enable the creation of a robust, real -time data flow into the NAP
component, which would provide a structure and allow filtering of such data according to predefined
metadata formats (e.g., MobilityDCAT-AP). The API links supplied by providers allowed for seamless
integration, setting up a pathway for interoperability across various datasets. The NAP component
would serve as the central (meta)data pathway according to the different NAP types (metadata
repository and data platform).
Furthermore, ensuring that the data provided adheres to the DATEXII standard would foster
compatibility and data discoverability and usability. Harmonising data formats would improve the
accessibility of such information to other systems within the Mobility Data Space. The idea was that
the demonstrator would represent the output component in this system. As a proof of concept, the
demonstrator would receive data and metadata feeds from the NAPs.
It would then be possible to deliver a centralized API link, acting as a single, accessible endpoint for
data consumers. This would provide a consolidated interface for stakeholders to access both real-time
and static data, fostering transparency and supporting the broader goals of an integrated Mobility Data
Space.
3.2. Relation to other initiatives
This demonstration relies on input from other initiatives within and outside of NAPOCRE, such as:
• EU legislation: legislative developments in the context of AF infrastructure and data interfere
with the approach selected
• Metadata specification: progress on metadata-related aspects, especially coming from the
sWG4.4, such as the mobilityDCAT-AP, determine the keywords for the text-based searches
performed throughout this work
• IDACS project: key outputs were incorporated into the requirement analysis.
• AF ambassadors: the contribution of the NAPCORE ambassadors on AF data Is crucial to
delimitate the scope of these demonstrators, due to their knowledge on the market and
related initiatives]
[page 12]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 12
As for the outcomes of this study, it has important contributions to other NAPCORE tasks:
• WG2 – Task 2.1 – Levels of service of NAPs: the demonstrator shall provide important feedback
to the NLKF, as highlighted in the section 6.1
• WG2 – Task 2.3 – NAP Reference Architecture : the demonstrator shall provide important
feedback to the architectural efforts of NAPCORE, as highlighted in section 6.1
• WG3 – Task 3.2 – Data quality: The AF data discovered as part of this work shall be further
processed and used as a use case for the Quality Framework on AF data, i.e., the quality criteria
and metrics developed for this framework will be applied/tested using datasets discovered
and eventually processed in the demonstrator
• WG4 – sWG4.1 – DATEX II: Contribution to the Reference Service Profile for of AF data from
the DATEXII standard
• WG4 – sWG4.4: relation to the Metadata Specification MobilityDCAT -AP, which is often
outlined throughout the document
3.3. Technologies/methods for Implementaçtion
The implementation of data extraction and integration within the demonstrator leveraged several key
technologies, including RESTful APIs for dynamic data sources like OCPI and DATEX II, along with ETL
tools for processing static datasets in Excel or CSV formats. These technologies ensured that data from
diverse sources could be harmonized and accessed in real-time, creating a flexible and robust pipeline
for alternative fuels data management across the NAP ecosystem.
API Integration for OCPI and DATEX II
For real-time, structured data such as electric vehicle charging information or transport infrastructure
updates, API integration was essential. The Open Charge Point Interface (OCPI) standard enables
seamless data exchange regarding charging station locations, availability, and pricing, making it a key
component in the demonstrator's data strategy. Similarly, DATEX II —widely adopted for intelligent
transport systems across Europe —facilitates the sharing of traffic and mobility data. By employing
RESTful APIs in ASP.NET Core Web API, the system could query and retrieve dynamic data from these
sources efficiently. Tools like Apigee and MuleSoft were considered for additional API management,
providing secure, scalable middleware to handle data requests across multiple endpoints.
ETL Tools for Static Data Extraction
For extracting data from static formats, ETL (Extract, Transform, Load) tools were deployed. Azure Data
Factory and Talend were suitable choices, given their capability to process and transform data stored
in Excel and CSV files. These tools automated the loading of structured data into Microsoft SQL Server,
ensuring that the database remained synchronized with the most recent datasets. This approach
facilitated the smooth integration of static data into the demonstrator, enabling complete and
comprehensive data views across both dynamic and static sources.
3.4. Requirement Analysis
To effectively integrate National Access Points (NAPs) into the Alternative Fuels (AF) demonstrator, a
thorough requirements analysis was undertaken to evaluate the current state of AF data availability
and management across participating member states. This analysis, aimed to identify which NAPs had
structured, organized data that could be easily accessed and shared within a broader European
framework. Key factors for evaluation included the presence of alternative fuel (AF) datasets within
NAPs, the organizational structure and metadata compatibility, and the use of systems such as CKAN,
a popular data management solution known for its support of metadata and open-source adaptability.
CKAN compatibility, in particular, was highlighted as a crucial element for streamlined integration, as
[page 13]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 13
it allows datasets to be indexed, searched, and shared in a consistent manner. The analysis identified
that out of 30 participating member states, only 13 had significant AF data available, and fewer still
were organized to easily interface with the AF demonstrator requirements.
Figure 3.2 - Analysis of EU NAPs concerning AF data availability and "ease" of metadata extraction
The Belgian, Greek, and Swedish NAPs stand out as good candidates for integrating alternative fuels
data due to their established infrastructure and compatibility with advanced metadata management
systems like CKAN. Belgium's NAP, for instance, has a structured dataset system that is co mpatible
with CKAN, making it easier to integrate with the AF demonstrator. CKAN is an open -source data
management system that provides a standardized framework for storing and sharing datasets. By
organizing their AF data according to CKAN's structure, Belgium’s NAP is able to facilitate smooth data
sharing and interoperability with other European NAPs, which is crucial for unified access to AF data
across the EU.
Similarly, Greece and Sweden have demonstrated strong capabilities in metadata organization,
ensuring their datasets are systematically categorized, accessible, and compatible with the
demonstrator requirements. Sweden’s NAP, in particular, has a well -established data infrastructure,
allowing for automated data collection and integration with minimal adjustments. Greece, while still
expanding its AF data coverage, has implemented key CKAN -compatible structures that enhance the
efficiency of data exchange, e nabling seamless integration with the Metadata demonstrator. This
compatibility ensures that essential AF data —such as the locations and availability of refuelling
stations—is readily accessible, thus supporting the broader objective of establishing a cohesive,
accessible European AF data network.
3.5. Definition of use cases
The solution design leverages results from the NAPCORE project to create a harmonized interaction
with the European Alternative Fuels Observatory (EAFO), aligning the Alternative Fuels Infrastructure
Regulation/Directive (AFIR/AFID) and NAPCORE activities. Therefore, it is important to introduce how
these two concepts (EAFO and AFIR provider) were incorporated within the methodology.
AFIR Data Provider – data aligned with AFIR requirements. This includes information on various
alternative fuel types, such as electric, hydrogen, and biofuels, with detailed metadata related to fuel
station locations, capacity, availability, and compatibility with different vehicle types. Providers of this
data may include public entities, private companies, or other stakeholders, all contributing to a central
data pool. The provider module supports both static data (such as station locations and fuel types) and
dynamic data (e.g., real-time availability). By leveraging this module, the NAP can ensure that all AFIR-
required data is available for integration into the broader Mobility Data Space.
EAFO2 – serves as a centralized Mobility Data Space. EAFO gathers, harmonizes, and disseminates data
on alternative fuel infrastructure across Europe, allowing for easy access to high-quality, standardized
information for policy-making and public use. This module enables the data from AFIR providers to be
incorporated into the EAFO database through an automated, standardized process. The integration
2 https://alternative-fuels-observatory.ec.europa.eu/general-information/alternative-fuels
[page 14]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 14
ensures that the NAP’s data can be queried, visualized, and accessed through EAFO’s platform, aligning
national data with EU -wide objectives and enhancing the visibility of alternative fuel infrastructure.
Describing relevant and necessary demonstrator parts.
Based on this understanding, our work developed two use cases (further detailed below). These use
cases were chosen because they ensure that the demonstrator addresses real user needs. Both of
them derived from an overall need of the service providers, described as follows: “As a Service Provider
I wish to view which NAPs have available metadata that Refers Alternative Fuels data and how the data
could be extracted”.
Both use cases are depicted in Figure 3.3Fehler! Verweisquelle konnte nicht gefunden werden.. The
upper part of the Figure describes the first use case, i.e., how the data coming from the providers is
exchanged through a Metadata Directory NAP to the data consumer (EAFO). At the bottom part of the
figure, the second use case is explained, i.e., h ow NAPs share actual data retrieved from the AFIR
providers and deliver them to the EAFO.
Figure 3.3 - Description of use cases of the AF demonstrator
Use case 1: ENABLING DATA DISCOVERABILITY THROUGH NAP METADATA
The first use case considered the functions of a Metadata Directory NAP (MD-NAP), allowing
streamlined metadata exchanges with EAFO. EAFO maintains a registry of MD -NAPs, where national
stakeholders submit AFIR -related data descriptions using standardized categories and keywords
through DCAT-AP. These descriptions (metadata) are listed in a machine-readable format within NAP,
from which EAFO retrieves and processes the information. The EAFO would be able to extract API links
from data providers, enabling direct data access.
The goal of this use case is to obtain an overview of the status of dataset availability regarding
Alternative Fuels using metadata, providing an assessment of the conditions under which EAFO would
[page 15]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 15
perform i ts task, in particular concerning data discoverability. Additionally, one of the intended
findings is to discover which NAP features allow for the proper development of those tasks.
Use case 2: FILTER THE AVAILABLE DATA BY CATEGORY AND EVALUATE DATA HARVESTING
In Use Case 2, the NAP operates as a Data Platform (DP-NAP) by directly supplying AFIR data to EAFO
through a cost-free API connection. EAFO, in turn, integrates data directly from DP -NAPs, facilitating
consistent data sharing and adherence to EU requirements. This approach enhances interoperability
across national access points, optimizes the use of national datasets, and aligns infrastructure data
with the European Union’s sustainable transport goals.
This use case aims to identify a set of characteristics that would facilitate data usage. This could be
achieved by comparing the different data providers (using data available on the NAPs) according to
suggestions from NAPCORE experts and members of the STF group on data (Activity 1).
[page 16]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 16
4. Detailed architecture framework
4.1. Requirements / user needs
Since one of the goals of this work is to discover AF data, the leading group of this task, together with
external partners and stakeholders, came up with a set of requirements for AF data providers to allow
proper AF-data discoverability and use. Some of these requirements concern access features from the
NAPs (i.e., functionalities) and others to the quality of datasets (e.g., freshness of dynamic data). Those
requirements are listed and explained below:
1. Type of Data - refers to the possibility of extracting just metadata or also related Alternative
fuels data
2. Interface to Extract Data - A collection of operations that provides access to one or more
datasets or data processing functions. (i.e., dcat:DataService)
3. Data Format – describe the syntaxes commonly used in mobility data portals , in conformity
with DATEXII (i.e., dct:format).
4. Data Category - refers to the mobility-related theme (i.e., a specific subject, category, or type)
of the delivered content. A dataset may be associated with multiple themes. A theme is
important for data seekers interested in a particular data content. (optional) (i.e.
mobilitydcatap:mobilityTheme)
5. Contact Person - An entity (e.g., an individual or an organisation) associated with Catalogues,
Catalogue Records, or Datasets. (i.e., foaf:Agent)
6. Privacy – if there is any available additional data, but not shared free of charge (e.g., Only for
registered members) (i.e. dct:accessRights)
7. Refresh rate of dynamic data
8. Assurance of the quality of the data
4.2. Software stack architecture per module
A software stack architecture is organized into layers, as it can be seen in Table 4.1, that handle
different aspects of application development. The frontend layer is responsible for the user interface
(UI), including presentation logic and client -side scripting. It encompasses elements like web pages,
mobile app screens, and interactive components, often leveraging frameworks like React or Angular
for efficient development. On the backend, the application logic resides, managing user requests,
processing data, and interacting with the database layer. Backend languages such as Python, C#, or
Node.js are used to build server -side logic, along with frameworks like Django or Express.js for
streamlined development. This layer also exposes APIs for communication between the frontend and
backend, facilitating data exchange and application functionality.
Meanwhile, the database layer handles data storage and access, utilizing databases like MySQL,
PostgreSQL, or MongoDB. It stores structured or unstructured data and manages operations such as
querying, inserting, updating, and deleting records. Object -Relational Mapping (ORM) or Object -
Document Mapping (ODM) libraries abstract away complexities, providing a higher-level interface for
interacting with databases. Together, these layers form a cohesive software stack architecture,
enabling the development of robust and scalable applications with clear separation of concerns. This
modular approach allows for easier maintenance, scalability, and flexibility in adapting to evolving
business requirements and technological advancements.
After identifying the source from extracted metadata, the demonstrator leverages an API -based data
harvesting module to retrieve relevant datasets. This module integrates seamlessly with the backend,
employing APIs that adhere to standards like OCPI or DAT EX II for structured and real -time data
exchanges. The API acts as a bridge, fetching data directly from providers and ensuring it is updated in
[page 17]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 17
near real-time. Once harvested, the data is processed through the application logic layer, where it is
validated, formatted, and prepared for further use, ensuring compatibility with the database and
frontend layers of the system. This approach guarantees a dynamic, efficient, and scalable mechanism
for incorporating external data into the NAP ecosystem.
Table 4.1 - Software stack Architecture according to Demonstrator Functionality Layers
Layer Framework Programming
Language
Purpose
Frontend ASP.NET Core MVC
User Interface: HTML,
CSS, Razor Views
C# ASP.NET Core MVC is used to
create the frontend of the web
application. Razor Views are
used to generate dynamic
HTML content, and CSS is used
for styling.
Application ASP.NET Core Web API C# This layer handles the
application logic and provides
API endpoints for
communication between the
frontend and backend.
Backend ASP.NET Core C# The backend layer contains the
business logic and data
processing code. It interacts
with the database layer for
data retrieval and storage.
Database Microsoft SQL Server SQL Purpose: Microsoft SQL Server
is used as the relational
database management system
(RDBMS) for storing and
managing structured data
Harvest and Data
Process Layer
ASP .NET Core C#, Python This component was
responsible for extracting data
from the datasets. Since it call
external scripts for processing
different data according to the
available data.
4.3. Functional architecture
Functional architecture refers to the structural design of a software system based on its functional
components and how they interact to fulfil specific tasks or requirements. In the context of the
Alternative Fuels demonstrator, four modules integrated the solution. Three of them have already
been detailed in the Metadata demonstrator report (reference). Still, their description can be
summarised as follows:
• Metadata Harvester – retrieves (meta)data from a source; it preserves the original format,
performs validity checks and attaches meta-metadata, ensuring automation and efficiency
• Metadata Processor – manipulates and processes the extracted (meta)data; it maps the
structure to conform to a certain specification, analyses the elements involved and applies
the moblityDCAT-AP scheme
• Metadata Display – allows the visualization of the discovered metadata from various NAPs
through a unified interface
[page 18]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 18
As for the fourth module, the Data Integration Interface serves as the bridge between the metadata
modules and external systems like the European Alternative Fuels Observatory (EAFO). This module
ensures that processed metadata can be harvested and integra ted seamlessly into larger mobility
ecosystems. It enables the retrieval of datasets through dynamic APIs, supports real-time updates, and
consolidates data streams into a unified repository. This interface leverages structured formats such
as OCPI and DAT EX II, ensuring that data consistency and interoperability standards are maintained.
Additionally, it provides endpoints for querying and pushing data, making it a key enabler for data -
driven decision-making in the alternative fuels infrastructure landscape.
The integration interface also incorporates mechanisms for version control and data synchronization,
ensuring that updates in source datasets are reflected accurately across connected platforms. By
establishing a robust communication layer, this module enhances the functional architecture, making
it adaptable for evolving mobility data requirements.
4.4. Considerations for the implementation
When designing and implementing a detailed architecture framework for the proposed solution, cost
considerations were paramount. One major cost factor involves the integration of external APIs within
the National Access Points (NAPs). This includes the licensing, development, and maintenance of API
functionalities that support seamless data exchange with systems like EAFO. Another cost driver is the
identification and customization of specific fields for metadata extraction or addition, which requires
mapping existing data structures to the proposed architecture. Organizations must also budget for
technical expertise to implement and test these adjustments, ensuring compatibility with standards
for data, like DATEX II, or metadata, like mobilityDCAT-AP. As such, our suggestions were in line with
that approach.
Another point to be considered was message throughput and system uptime, which are critical for
ensuring the framework's operational reliability. High message throughput is essential to handle large
volumes of real -time and static data exchanges across NAPs and external entities. Similarly,
maintaining high system uptime guarantees consistent access to data services, a vital factor for users
who rely on uninterrupted availability.
Determining the path to implementation involves assessing the frequency and complexity of metadata
updates. This includes evaluating whether metadata updates should occur in real -time, scheduled
batches, or as event -driven processes. Each approach has diff erent technical and cost implications,
from infrastructure scalability to data synchronization challenges. Additionally, the framework must
address how updates are propagated across integrated systems to maintain consistency and prevent
data redundancy. By incorporating automated processes for metadata management, the architecture
can ensure timely and efficient updates, enabling smoother integration and data accuracy across
platforms. This , along with data management , proved to be a challenge in designing the
implementation.
[page 19]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 19
5. Results
5.1. Use case 1 Enabling Data Discoverability Through NAP Metadata
The evaluation of Use Case 1 revealed significant insights into the discoverability and accessibility of
Alternative Fuels-related data within the six tested NAPs. The implementation of metadata directories
in compliance with DCAT-AP and mobilityDCAT-AP standards was assessed, focusing on their capability
to support the European Alternative Fuels Observatory (EAFO) in extracting standardized metadata.
Among the NAPs examined, there was variation in the availability and presentation of datasets. While
some NAPs demonstrated full compatibility with DCAT-AP, others were still in partial or early stages of
adopting mobilityDCAT-AP. This disparity affected t he discoverability of metadata and the ease with
which EAFO could retrieve API links. For example, metadata in certain NAPs highlighted duplication
issues, with datasets sourced from the same provider but categorized inconsistently due to local
language descriptions or format discrepancies. These inconsistencies underscored the need for more
rigorous standardization efforts to reduce redundancies and improve the clarity of data exchanges.
The test also showcased that while all participating NAPs provided data relevant to Alternative Fuels
Infrastructure Regulation (AFIR), the levels of automation and machine -readability varied. NAPs with
advanced implementation of mobilityDCAT -AP were more effective in presenting harmonized
metadata and ensuring direct data accessibility via APIs. The results indicate that fully implementing
standardized frameworks and addressing language barriers are critical for enhancing data
discoverability and interoperability within a pan-European context. Table 5.1 illustrates the outcome
of this analysis, by providing a comparison between the number of datasets and MobilityD CAT-AP
implementation in 2022, when the proof-of-concept of the Metadata demonstrator was developed,
and 2024, when the AF demonstrator technical work was performed.
Table 5.1 – Status of MobilityDCAT-AP implementation and number of datasets: comparison between 2022 and 2024
NAP # of datasets August 2022 DCAT-AP schema ? # of datasets October 2024 MobilityDCAT-AP status
Trafficdata.se 49 DCAT-AP + extensions („ext: …“) 51 preparation
du-portalui.dataudveksle
r.app.vd.dk
26 DCAT-AP 95 deployed
transportdata.b
e 176 DCAT-AP 123 testing
data.nap.gov.gr 34 DCAT-AP 47 -
mobilithek.info > 7000 Proprietary RDF model, compatible
with IDS and DCAT -AP
+ extensions („mdp:
…“)
> 9000 testing
mobilitydata.gv
.at 40 Proprietary XML model 47 preparation
[page 20]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 20
5.2. Use case 2 FILTER THE AVAILABLE DATA BY CATEGORY AND EVALUATE DATA
HARVESTING
This use case explores the process of extracting and organizing data from National Access Points
(NAPs), specifically focusing on data format compatibility, accessibility, and language standardization.
The goal is to enable consistent data extraction from various NAPs, showcasing how standardized
metadata frameworks can improve interoperability across datasets. In this scenario, volunteered NAPs
and stakeholders provide data to test both User Scenarios (US1 and US2) to assess how data is shared,
whether it’ s freely accessible, and in what formats it is provided. By examining these factors, the
project aims to pinpoint best practices for data sharing across NAPs, while also identifying challenges
associated with diverse data formats and language inconsistenci es, which prevent seamless
integration.
One of the main challenges in this use case was the availability and accessibility of the data itself. Many
datasets across NAPs are not openly accessible or are locked behind permissions, creating significant
barriers to data extraction. Additionally, datasets are often described in local languages, a dding an
extra layer of complexity to harmonization efforts. When data is described in multiple languages,
metadata standardization becomes more complex, as each dataset may use different terminology,
descriptions, or formats. This language barrier often leads to duplication of data across NAPs, as
identical datasets may be categorized differently or remain unrecognized as duplicates due to language
discrepancies.
An essential step to overcoming these obstacles is harmonizing metadata standards across NAPs. By
using standardized identifiers and a uniform data format, duplicates can be identified more easily,
streamlining the integration process. Comparison of sources, such as using specific identifiers (e.g., H2
Mobility) for reference and ensuring compatibility in data types and formats, will enhance
discoverability and improve the accuracy of the integrated dataset. This harmonized approach will
ultimately foster a more effective ecosystem where stakeholders can rely on consistent, easily
accessible, and high-quality data across borders.
For NAPs hosting both static and dynamic data, data provision relies on meeting specific technical
requirements. These include supporting standardized APIs to ensure seamless access to datasets, such
as RESTful APIs that are compatible with OCPI or DATEX II standards. Data providers must ensure data
access mechanisms are reliable and secure, allowing consistent querying and real -time updates.
Furthermore, data formats must align with established standards like JSON, XML, or DATEX II for
dynamic feeds and CS V or Excel for static data. Proper adherence to these requirements ensures
interoperability and facilitates smooth data exchange across various stakeholders in the mobility
ecosystem.
[page 21]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 21
6. Conclusions
6.1. Feedback to other NAPCORE WG2’s tasks
Task 2.1 – NAPs Levels of Service
The work methodology and the outcomes of the Metadata demonstrator provide relevant inputs for
activities related to the Levels of Service (LoS) of the NAPs. The LoS is the main focus of task 2.1, which
developed the NAP LoS KPI Framework (NLKF), a “tool” for estimating the LoS of NAPs, based on several
features translated into KPIs. When comparing the features pertaining to the NLKF with the
requirement analysis from this report (section 3.4Fehler! Verweisquelle konnte nicht gefunden
werden.), it is possible to identify the minimum requirement values for certain features (KPIs) so that
the NAP could be integrated into this demonstrator. Such KPIs and respective “minimum values”, along
with the main reasons why they are required, are listed in Table 6.1. It is worth mentioning that this
analysis considered the 2024 version of the NLKF3.
It is possible to notice that several KPIs are not mentioned because they were already covered by the
metadata demonstrator. Those include : Online Availability (1.1), Procedure for Publication Input of
Metadata or Data onto the NAP (1.12), Metadata Output and Access Restrictions (1.13), Search
Functionalities (3.1), Search Results (3.2), Machine -Readable Metadata (3.3), Operational Procedure
Information (7.3). In addition to the ones needed for the metadata demonstrator, there is one KPI
which is essential for the Alternative Fuels demonstrator – regarding data transfer in Data Platform
NAPs. Such feature is described in Table 6.1, along with the reason why it is required.
Table 6.1 - Essential KPIs for the extraction and processing of the data in the Demonstrator
KPI Value Reason
1.18 – API usage
for data transfer
1: API is available in a data platform NAP
type for automated data retrieval (API for
data consumers)
The data must be made available
in order to be extractect by the
demonstrator
Task 2.3 – NAP architecture
Table 6.2 shows the main functionalit ies needed from the NAPs for this demonstrator , namely :
machine to machines access interface (Availability), the availability to provide metadata to consumers
and to provide metadata search (Accessibility) as well as if the NAP acts as Data platform for Alternative
fuels data (Collecting data, merge data and provide data) the NAP has to provide an API for AF Data
(Accessibility). According to M2.94, which presents the first results of the NAP Reference Architecture,
these functionalities are related to metadata, data, and service:
• Metadata structure and content,
• Metadata provision to user
• Data provision to user.
Some issues regarding the Metadata quality checks might provide improvements in future iterations.
In addition to the functional view, Table 6.2 it presents important aspects of the Physical and
Organisational Views. Some of the components belonging to these views are essential for the retrieval
3 NAP LoS KPI Framework 2024 (https://github.com/NAPCORE/NAP-LoS-KPI-Framework.git)
4 https://www.napcore.eu/documents/M2.9_Harmonisation_EU_NAP.pdf
[page 22]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 22
of metadata within the Demonstrator’s approach, according to the terminology presented in M2.9.
The table lists the essential architectural components for the three views.
Table 6.2 - NRA Modules importance
Functional View Physical View Organisational View
Metadata Requesting System
(a machine) retrieves
metadata from NAP via a
dedicated API. The Data
Requesting System (machine)
NAP Metadata Management
component that handles the
management of the metadata,
its access and retrieval,
authorisation of NAP Content
Providers (in cooperation with
NAP User Management
component) and metadata
quality checks.
NAP Content Manager that
ensures that the quality
guidelines/criteria of content
(data and metadata) are met,
data formats are correct, and
content is processed in
compliance with the Service
Level Agreement contracted
with the NAP Technical
Operator.
Data Provision System
(machine) represent an
addition to Data Platform NAP
for machine-to-machine
exchange of traffic and travel
data with NAP
NAP Content Provider which is
responsible for collecting,
providing, and updating traffic
and travel data and metadata
Enables data storage and
retrieval of data
NAP Data Management
component that handles the
management of the data, its
access and retrieval,
authorisation of NAP Content
Providers (in cooperation with
NAP User Management
component).
Some of these components are depicted in Figure 6.1, extracted from one of the WG2 meetings
concerning the NAP Reference Architecture. In the figure, which depicts the functional view of the NAP
reference Architecture, it is possible to observe the relationship between some of these architectural
components, such as the “Metadata Management” and the “Metadata Quality Checks” modules.
[page 23]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 23
Figure 6.1 – M2.9 figure. Conceptualization of the metadata NAP Architecture
[page 24]
Milestone 2.10: Alternative Fuels Demonstrator
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 24
6.2. Lessons learnt and recommendations
The Alternative Fuels Proof of Concept Demonstrator, as an extension of the Metadata Demonstrator,
showcased both the strengths and limitations of utilizing metadata specifications like mobilityDCAT-
AP for improving data discoverability. It reinforced the potential of metadata interoperability to unlock
data access , in this case , by focusing on Alternative Fuels for general users and facilitating the
implementation of European guidelines. However, several challenges and observations emerged
during its development and testing.
One key limitation identified was the lack of consistent and available data on alternative fuels
infrastructure across National Access Points (NAPs). While metadata frameworks provided a
structured approach to finding and accessing data, many of the countries that allowed automatic M2M
extraction of metadata do not yet make AF data available through their NAPs. This highlighted a critical
gap in data collection and standardization that must be addressed to achieve meaningful
interoperability and support for policies like the ones pointed out by the AFIR. Moreover, the
demonstrator revealed that metadata discoverability depends not only on the presence of datasets
but also on their alignment with standardized formats and descriptions, which still remains
inconsistent across NAPs. The mobilityDCAT -AP approa ch made it possible to quickly access the
presence of alternative fuels data, thanks to the mobilityTheme property.
The demonstrator illustrated how standardized metadata descriptions can improve the user
experience. Users could easily determine whether the desired data was available, given the structured
descriptions and categorie s. However, the lack of uniformity in data formats and language
discrepancies across NAPs posed persistent challenges. Future work should focus on addressing these
barriers, including improving data standardisation through recommended data standards, such as
DATEXII, and supporting the inclusio n of underrepresented data types, such as hydrogen
infrastructure. The “Filling and chargin g stations” only differentiate electric vehicle charging points
from filling stations, not deepening into the fuel type (i.e., hydrogen or fossil fuels , for instance). A
possible approach to overcome this issue would be to add another field to the Mobility Theme
Controlled Vocabulary – which would differentiate the different fuel sources.
Another significant observation was the need for stronger collaboration between stakeholders and
NAP operators. Ensuring access to data often requires agreements around re-use and publication rules,
which can vary widely across countries. Without such agre ements, the demonstrator’s potential
impact is limited.
Therefore, the challenges described in this report should be considered when establishing a European
Access Point for Alternative Fuels data – as is intended by the EC for 2027 (as stated in the AFIR). In
sum, the key challenges identified are:
• Poor availability of AF data on the NAPs
• Lack of standardisation and harmonisation of AF data
• Lack of metadata harmonisation throughout NAPs
• Issues regarding bilateral agreements and licenses for data reuse
