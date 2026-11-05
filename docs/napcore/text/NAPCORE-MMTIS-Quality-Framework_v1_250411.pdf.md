url: https://napcore.eu/wp-content/uploads/2025/06/NAPCORE-MMTIS-Quality-Framework_v1_250411.pdf
title: NAPCORE MMTIS Quality Framework v1 250411

[page 1]
A Quality Framework for Multimodal Travel
Information Services (MMTIS)
Report by Task 3.2: European NAPs data quality
Status: final
Version: 1.0
Date: 11/04/2025
Legal disclaimer
The sole responsibility for the content of this document lies with the authors. It does not necessarily
reflect the opinion of the European Union. The European Commission is not responsible for any use
that may be made of the information contained therein. All imag es are provided by the respective
partners (unless otherwise noted) and are approved for reproduction in this publication.
[page 2]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 2
Document information
Project acronym NAPCORE
Full project title National Access Point Coordination Organisation for Europe
Grant Agreement No. MOVE/B4/SUB/2020-123/SI2.852232
Activity no. and title WG 3 NAP content and accessibility
Author(s) Anastasia Founta (ITxPT)
Co-author(s) David Ariño-Montoya (ITxPT)
Related to Milestone no. M3.8
External Milestone No
Document history
Version Date created/ modified by Comments
0.1 June 2023 David Ariño-Montoya
(ITxPT)
First draft
0.2 January 2025 Anastasia Founta
(ITxPT)
Synthesis of all input. Version for review
0.3 February 2025 Matthias Gunter (CH)
Yves Amsler (UITP)
Benjamin Witsch (AT)
Brede Dammen (NO)
Petr Bures (CZ/TTR)
Jaakko Rintamäki (FI)
Review
0.4 March 2025 Anastasia Founta
(ITxPT)
Incorporation of the comments and
relevant updates.
1.0 April 2025 Peter Lubrich (BASt) Activity Leader Review
Action requested
☐ To be revised by partners involved in the preparation of the document
☐ For review/ approval by the Core Alignment Team
☐ For approval by the NAPCORE Steering Committee
Abstract
This deliverable is part of a set of quality frameworks being developed under the scope of NAPCORE
WG 3. It comprises a Quality Framework dedicated to Multimodal Travel Information Services (MMTIS)
data. The document contains a detailed description of quality criteria and metrics aligned with the
characteristics and elements of MMTIS.
[page 3]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 3
Abbreviations
Abbreviation Meaning
DR Delegated Regulation
EC European Commission
EU EIP EU ITS Platform
ITPS Intelligent Truck Parking Services
ITS Intelligent Transport System
LOS Level Of Service
MMTIS Multimodal Travel Information Services
NAP National Access Point
NAPCORE National Access Point Coordination Organisation for Europe
QF Quality Framework
RTTI Real-Time Traffic Information Services
SRTI Safety-Related Information Services
WG Working Group
[page 4]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 4
Table of contents
1. Introduction................................ ................................ ................................ .......................... 6
1.1. Why do we need a Quality Framework for MMTIS Data and Services? ................................ .... 6
1.2. What is a Quality Framework for MMTIS Data and Services? ................................ .................. 6
2. Scoping ................................ ................................ ................................ ................................ . 7
2.1. What data? ................................ ................................ ................................ ........................... 7
2.2. Which stakeholders are targeted ................................ ................................ ........................... 9
2.3. Which use cases are relevant to MMTIS QF ................................ ................................ ............ 9
3. Methodology ................................ ................................ ................................ ...................... 11
3.1. Working structure ................................ ................................ ................................ ............... 11
3.2. Expert pool ................................ ................................ ................................ ......................... 11
3.3. Results of Stage 1: Review of existing EU EIP Quality Framework................................ .......... 12
3.4. Results of Stage 2: Collection of input from stakeholders ................................ ..................... 13
3.4.1. Poll results ................................ ................................ ................................ ................. 13
3.4.2. Dedicated presentations ................................ ................................ ............................. 14
3.5. Input from relevant NAPCORE deliverables and other projects ................................ ............. 16
3.5.1. Input from other QFs ................................ ................................ ................................ .. 16
3.5.2. Input from NAPCORE MMTIS Data Dictionary................................ .............................. 17
3.5.3. Input from DATA4PT guidance document ................................ ................................ .... 18
4. Proposal for Quality Criteria ................................ ................................ ................................ 19
5. Proposal for Quality Levels ................................ ................................ ................................ .. 22
6. Quality Assessment: Approaches and Methods ................................ ................................ .... 33
6.1. Introduction................................ ................................ ................................ ........................ 33
6.2. Description of approaches and methods ................................ ................................ .............. 33
6.2.1. Perform quality assessment in different stages of data provision chain/process .......... 33
6.2.2. Establish different types of errors and relevant errors management ............................ 33
6.2.3. Data user/consumer feedback ................................ ................................ .................... 35
6.2.4. Quality reports ................................ ................................ ................................ ........... 36
6.2.5. General guidelines ................................ ................................ ................................ ...... 36
6.3. Description of tools ................................ ................................ ................................ ............. 37
6.3.1. Compatibility to standards and logical precision validation ................................ .......... 37
6.3.2. Visualization ................................ ................................ ................................ .............. 37
6.3.3. Stop registries for uniqueness ................................ ................................ ..................... 38
7. Conclusions ................................ ................................ ................................ ......................... 39
Appendix I ................................ ................................ ................................ ................................ .. 40
Appendix II ................................ ................................ ................................ ................................ . 43
[page 5]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 5
Appendix III ................................ ................................ ................................ ................................ 44
Appendix IV ................................ ................................ ................................ ............................... 46
Appendix V ................................ ................................ ................................ ................................ 47
Appendix VI ................................ ................................ ................................ ............................... 54
[page 6]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 6
1. Introduction
1.1. Why do we need a Quality Framework for MMTIS Data and Services?
Multimodal Travel Information Services is one very important piece of the sustainable mobility puzzle.
The expectations for these services are quite high in order to have a significant and positive impact to
travellers’ behaviour towards more sustainable mobility habits . Therefore, these services need to
address the entire door-to-door journey, seamlessly and with very high level of reliability. Considering
the importance of information systems to leverage the potential of multimodal services that the
mobility operators and authorities provide, the MMTIS Delegated Regulation (EU) 2017/19261 and its
amendment (EU) 2024/4902 put a lot of attention on the quality aspect.
In particular, in recital 18, the MMTIS Delegated Regulation ( DR) underlines that “the provision of
accurate and reliable travel information by service providers is essential for travellers across the
Union”. It highlights the need that “when changes occur, the relevant data should be updated by the
transport authorities or transport operators through the national access point in a timely manner ”.
The regulation stressed out the negative impact an inaccurate information might have for the traveller
and requires that “when any inaccuracies are detected by transport authorities, transport operators,
infrastructure managers or transport on demand service providers, such errors should be corrected in
a timely manner.”
Those requirements are extended in the amended Delegated Regulation (EU) 2024/490) under its
recital 12 that states: “Member States and ITS stakeholders should cooperate to reach an agreement
on common definitions of data quality with a view to use common data quality indicators throughout
the travel and traffic data value chain, such as the completeness, accuracy and up-to-datedness of the
data as well as the quality checks applied, in particular for cross border services. They should also be
encouraged to work further to establish associated methods of quality measurement and monitoring
of the different data types. Member States should be encouraged to share with each other their
knowledge, experience and best practices in the data quality field in on-going and future coordination
projects.”
Subsequently NAPCORE project , under Working Group 3 , focused on putting in place a quality
framework to support NAP operators and other relevant stakeholders to meet the needs of data
quality, detecting inaccuracies, errors and set timeliness criteria.
1.2. What is a Quality Framework for MMTIS Data and Services?
The Quality Framework of MMTIS Data and Services should be interpreted as a useful tool that aims
to support primarily NAP operators but also data providers in different stages of data provision chain,
like mobility operators and authorities. The tool contains recommendations for quality criteria and
relevant requirements based on best practices implemented so far and the feedback of NAP operators,
experts of NAPCORE project and invited experts . The criteria concern the quality of the datasets
provided to the NAP, which contain data categories and data types included in the Annex of MMTIS
DR. The Quality Framework also refers to existing methods and tools of assessment as successfully
implemented by NAP operators until the date this report is produced.
1 https://eur-lex.europa.eu/eli/reg_del/2017/1926/oj/eng
2 https://eur-lex.europa.eu/eli/reg_del/2024/490/oj/eng
[page 7]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 7
2. Scoping
2.1. What data?
The current report targets the development of a quality framework (QF) for data categories and data
types included in MMTIS Delegated Regulation (DR) (EU) 2017/1926 and its amendment ( DR (EU)
2024/490). In particular it focuses on static3 and dynamic4 traffic and travel data. Historic and observed
data are partially in the scope (relevant only “for compatibility with the standards” criterion with the
required data standards) as are not yet in implementation. However, this QF might be useful as a basis
for future inclusion of those data categories.
Moreover, this report aims to address quality dimensions to most of the data types under those data
categories. Nevertheless, the analysis o f the different characteristics of the data types is made to
propose quality criteria that are feasible to be implemented based on the experience of the
stakeholders and the nature of the data. The following tables list the data types of the MMTIS DR that
are considered in the scope of this report and distinguished depending on whether they correspond
to location, time and service- related derivatives. Data types in Table 1 and 2 are in the main scope of
the report. Appendix I presents the rest of the data types included in amended DR that are relevant to
generic quality criteria such as compatibility and completeness.
It is very important that this report is used in conjunction with NAPCORE MMTIS Data dictionary5 which
contains the definition of each data type, the correspondence with the Transmodel data standard,
required by the DR, and the best practices regarding completeness of the data types.
Table 1 Location related data types included in MMTIS Delegated Regulation (2024/490). (“S” stands for “static”,
“D” stands for “dynamic”)
Data
category -
Level of
Service
Data type and data type description when available
S-1 Location search (origin/destination) addresses (building number, street name, postcode)
S-1 Location search (origin/destination) topographic places (city, town, village, suburb,
administrative unit)
S-1 Location search (origin/destination) points of interest (related to transport information) to
which people may wish to travel
S-1 Location search (access nodes) - for
scheduled transport and transport on
demand where relevant
identified access nodes
S-1 Location search (access nodes) geometry/map layout structure of access nodes
S-1 Trip plan computation - for scheduled
transport and transport on demand where
relevant
connection where interchanges may be made
3 “static travel and traffic data” meaning data related to different transport modes that do not change often, or data on
planned changes, as listed in point 1 of the Annex of 2024/490 DR.
4 “dynamic travel and traffic data” meaning data related to different transport modes that change often, or data on unexpected
events or circumstances, as listed in point 2 of the Annex of 2024/490 DR.
5 https://github.com/NAPCORE/Data-dictionary/blob/main/DR%20(EU)%202024-490.md
[page 8]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 8
Data
category -
Level of
Service
Data type and data type description when available
S-1 Trip plan computation - for scheduled
transport and transport on demand where
relevant
network topology and routes/lines (topology)
S-1 Trip plan computation - for scheduled
transport and transport on demand where
relevant
accessibility of access nodes, and paths within an
interchange (such as existence of lifts, escalators)
S-1 Trip plan computation Road network (including segregated lanes for bus/taxi)
S-1 Trip plan computation Cycle network (cycle tracks, cycle lanes, bus-and-cycle
lanes, on-road shared with vehicles, on-path shared with
pedestrians)
S-1 Trip plan computation Pedestrian network
S-2 Location search - for transport on demand
and personal transport
location of parking places (on and off-street), including
accessible parking places for persons with disabilities and
persons with reduced mobility
S-2 Location search - for transport on demand
and personal transport
Park & Ride stops
S-2 Location search - for transport on demand
and personal transport
Park & Drive stops
S-2 Location search - for transport on demand
and personal transport
bike-sharing stations
S-2 Location search - for transport on demand
and personal transport
car-sharing stations
S-2 Location search - for transport on demand
and personal transport
secure bike parking (such as locked bike garage)
S-2 Location search - for transport on demand
and personal transport
scooter parking zones
S-2 Information service where and how to buy tickets for scheduled transport,
including retail channels, fulfilment methods, payment
methods
S-2 Information service where and how to pay for parking, including retail
channels, fulfillment methods, payment methods
D-2 Availability check and location - for
transport on demand and personal
transport where relevant
Car-sharing availability and location, bike-sharing
availability and location, scooter-sharing availability and
location, and other vehicle-sharing availability and
location
D-2 Availability check and location - for
transport on demand and personal
transport where relevant
Car parking spaces available (on and off-street)
Table 2 Time and service related data types included in MMTIS Delegated Regulation (2024/490). (“S” stands for
“static”, “D” stands for “dynamic”)
Data
category -
Level of
Service
Data types and data type description when available
S-1 Trip plans operational calendar, mapping day types to calendar
dates
S-1 Trip plan computation - for scheduled transport
and transport on demand where relevant
default transfer times at interchanges
[page 9]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 9
S-1 Trip plan computation - for scheduled transport
and transport on demand where relevant
Timetables
S-1 Trip plan computation - for scheduled transport
and transport on demand where relevant
planned interchanges between guaranteed
scheduled services
S-1 Trip plan computation - for scheduled transport
and transport on demand where relevant
hours of operation
S-1 Trip plan computation - for scheduled transport
and transport on demand where relevant
transport operators
S-1 Trip plan computation - for scheduled transport
and transport on demand where relevant
facilities of access nodes (including platform
information, help desk/information points, ticket
booths, lifts/stairs, entrances and exit locations)
S-1 Trip plan computation - for scheduled transport
and transport on demand where relevant
vehicles, including their accessibility (such as low
floor, wheelchair accessible, pram accessible) and
accessibility of on-board services (such as toilets)
S-1 Trip plan computation - for scheduled transport
and transport on demand where relevant
existence of assistance services (such as existence of
on-site assistance)
S-3 Trip plan computation: estimated travel times by
day type and time-band by transport
mode/combination of transport modes
D-1 Passing times, trip plans and auxiliary
information
disruptions, such as network closures and/or
diversions, and when possible, the reasons
D-1 Passing times, trip plans and auxiliary
information
real-time status information, such as estimated
departure and arrival times of services, delays,
cancellations, guaranteed connections monitoring
D-1 Passing times, trip plans and auxiliary
information
status of access node features (including dynamic
platform information, operational lifts/escalators,
closed entrances and exit locations) - for scheduled
transport
2.2. Which stakeholders are targeted
This QF addresses primarily to NAP operators. However more stakeholders can benefit and use it in
order to ensure data quality in a unified way across EU. Overall, the relevant stakeholders are:
• NAP operators
• Data and service providers to the NAPs (mobility service operators). They can use the rules and
tools to check their data before submitting them to NAP operator or to improve afterwards
• Public Transport journey planners
• National Bod ies or Competent Authority 6 (Ministry and Organisation) delegated to check
implementation of MMTIS DR
Data providers that share data to NAP should have access to the results on the quality process (quality
of data shared). Service providers can also benefit from the access to the results by fixing appeared
issues in the datasets.
2.3. 7Which use cases are relevant to MMTIS QF
6 According to Article 9 of MMTIS DR, "Providers of data and services must submit a dataset or a description of
their data (metadata) to a NAP in accordance with the DR. The provision of (meta)data shall be accompanied by
a ‘declaration of compliance’ and ‘accompanying documentation’.
7 ISO (2008): ISO/TR 21707:2008 - Intelligent transport systems -- Integrated transport information, management
and control -- Data quality in ITS systems
[page 10]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 10
Several use cases might be relevant for the use and re-use of data which have as prerequisite data of
“high” quality. The use cases in the scope of the MMTIS Quality Framework help defining the quality
dimensions and criteria, as another parameter to be considered, beyond the nature of the data which
was mentioned in the previous paragraph. In this paragraph we list two main use cases.
• Multimodal and intermodal routing (including demand responsive transport and combination
of different modes of operations in general) and relevant passenger information systems are
the use cases of the core scope of the quality framework. Multimodal and intermodal routing
requires the us e and the combination of many different data types , static and dynamic ,
describing different modes of operations, in order to propose to passengers’ itineraries
alternatives in an efficient way. The data of good quality that are synced in a good manner is
prerequisite. Therefore, in this report, the aim is to define quality criteria that ensure as much
as possible the conformity with the standards (so different data types to be combined
efficiently), prevent inaccuracy of physical points coordinates and make sure data are updated
in an accurate manner.
• Fleet management and service quality assessment is another use case that can be envisaged.
This kind of use cases is more relevant to the historic and observed data. This data can be used
to improve performance of the provided service, when they are accurate enough. They can
also be used as reference to compare quality aspects (for example accuracy) with the current
data. However, quality criteria regarding this kind of data are not analysed in this report, as
their implementation is not yet in place and no previous experience or best practices is shared.
[page 11]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 11
3. Methodology
3.1. Working structure
The work of the MMTIS Quality Framework was developed in different phases.
In the first stage, internal group meetings were held to study and evaluate the existing EU EIP MMTIS
quality framework8. Following that, a poll with representatives of the member states t o collect more
information about the implementation of quality frameworks was carried out.
At the second stage, a series of workshops was run with different member states to share more details
about the quality frameworks implemented or planned in the different European countries.
Finally, input was collected from other Quality Frameworks developed in the framework of NAPCORE,
in particular the Quality Framework for UVAR Data and the Quality Framework for Floating Car Data9,
to have an aligned format and concept. Input was also considered from DATA4PT project and other
relevant reference documents, like MMTIS NAPCORE Data Dictionary10.
The Table below summarises the activities that took place for the development of the MMTIS Quality
Framework:
Table 3. Initial planning of the Quality Framework for Multimodal Travel Information Services.
Activities
Stage 1
Preparatory actions
Group kick-off
Review of existing quality framework
• Identify points for update
• Identify points for addition
Stage 2
Collection of current methods and approaches
• Organisation of workshops with MS & experts
• Desktop research (DATA4PT, etc.)
• Consolidation of inputs
Stage 3
Make a structure for future quality framework aligned with the Quality Frameworks on Floating
Car data, Parking and UVAR.
Define quality criteria/requirements for the selected data categories
Recommendations on assessment methods
Report preparation
Report review by SWG4.3 and WG3 partners
3.2. Expert pool
The contributors of this working group represent NAP operators from the following countries: Austria,
Belgium, Finland, Germany, Norway and Switzerland. In addition, the French authority responsible for
the assessment of implementation of the MMTIS Regulation ( L’Autorité de régulation des transports
(ART))11, as external to NAPCORE consortium expert, contributed to the activities of Stage 1 (reviewing
existing EU EIP quality framework) and 2 (collection of current methods and approaches).
8https://www.its-platform.eu/wp-content/uploads/ITS-
Platform/AchievementsDocuments/Quality%20Frameworks/EU%20EIP_SA41_MMTIS%20quality%20packagedefinitions_v2.0_191031.pdf
9 https://napcore.eu/quality/
10 https://github.com/NAPCORE/Data-dictionary
11 https://www.autorite-transports.fr/
[page 12]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 12
Leader of the group was ITxPT, as expert on Transmodel standards and in particular on NeTEx datasets
validation, making the liaison with the outputs/results of DATA4PT project 12.
3.3. Results of Stage 1: Review of existing EU EIP Quality Framework
During the first stage of this work, a review of the existing EU EIP Quality Framework for MMTIS was
performed as the only available document to provide a unified quality framework for the NAP
operators across EU until NAPCORE. The objective was to evaluate the criteria and the requirements
proposed by this document and to identify the points that are still valid, the points that need updates
and the points that are not relevant anymore.
The EIP report was focused to a sub-set of the full list of the data types required by the DR (Appendix
II). Some of data types have been transferred to other Delegated regulation , after the MMTIS DR
amendment.
Considering the EIP data types, the experts’ group proceeded to the evaluation of the quality criteria.
In the following table, they are summarised the criteria that the group confirmed as valid to be
considered with some updates for this QF. Appendix III presents the criteria that were assessed as very
complicated or not relevant to be considered for this QF.
Table 4 Evaluation of EIP Quality Framework – Criteria that are assessed as valid to be updated.
Number Quality Criteria for
MMTIS based on EIP
document
Description of EIP criteria Assessment from NAPCORE Quality framework task
force
1.1 Geographical
coverage
Percentage of the transport
system infrastructure covered
by the (content provision)
service.
To be updated and to be complemented with KPIs
beyond geographical area. For road networks, the
considered roads need to be of a certain
categorisation (for example forest utility roads
should not be considered in the percentage).
1.2 Availability Percentage of the time that
the (content provision)
service is available
It might have 2 different aspects:
1. The availability of the dataset should have a
threshold that is acceptable (e.g., a dataset being
unavailable for 50% is not acceptable).
2. The availability of the provided service refers to
whether the availability of the infrastructure or
operations is mentioned on the dataset. Concerns
specific data types (like accessibility data, facilities
etc.).
2.1 Timeliness Timeliness (start): The time
between the occurrence of an
event and the acceptance of
the event.
To be updated depending on data types (static and
real time data) and depending on data categories
(disruptions, cancellations etc.).
2.2 Timeliness Reporting period: The time
interval for refreshing /
updating the status reports –
replacing “Timeliness (start)”,
as with status reporting there
is no start.
To be updated. Timeliness depends on service. It is
not the same for airplanes as for buses. Also, all
frequency-oriented traffic needs to measure the
timeliness different.
12 https://data4pt-project.eu/
[page 13]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 13
2.3 Timeliness Timeliness (update): The time
between the end or relevant
change of condition and the
acceptance of this change.
To be updated. It depends on the event. The door
now closed is more important than a detour in 4
hours’ time.
2.7 Accuracy Location accuracy: The
relative precision of the
referenced location for the
published entity or event with
respect to what is considered
as the corresponding true
position of the actual entity
or event. (NB: several
possibilities – for a point,
stop, access node, road or
area).
Location accuracy is very important. MMTIS data is
useless if the location of stops, routes and vehicles
are not within a few meters. To complement or
improve the criterion.
Coherence between a static data set (e.g. NeTEx) and
corresponding dynamic data set (e.g. SIRI) can also
be used as an accuracy indicator.
2.11 Completeness Completeness of data:
Percentage of data entities
available in the service
provision with respect to the
total data entities of that
service or data type for which
quality criteria have been
defined. More precisely, for a
given service or data type, are
all the data entities foreseen
in the Regulation provided?
Completeness of data is a good indicator. For
example, how many organizations are providing the
data, and which organizations are missing. Priority
should be given to operators that serve the biggest
areas and populations.
Very simple indicator to set up with GTFS datasets, a
little more complicated for NeTEx static datasets
since several profiles exist. For EPIP, Greenlight
validator may work.
For real-time datasets, this is a very complicated
criterion, and they are no existing validators.
3.4. Results of Stage 2: Collection of input from stakeholders
3.4.1. Poll results
A form was shared with the Member States to obtain information about their national quality
frameworks. The questions asked were:
1- Do you have a national data quality framework for Multimodal Travel Information Services to
check the data in your National Access Point?
2- Are you aware of the “Framework for the quality of European services for Multimodal Travel
Information (EU EIP)”?
3- Please, explain about the preparation of your national MMTIS Quality Framework (if existing):
Is it elaborated from the European Quality Framework? Is it inspired by any other country in
the elaboration of the Quality Framework? Other relevant information?
The participants that answered the polls were representatives of the following countries: Austria,
Belgium, Cyprus, Czechia, Estonia, Finland, Germany, Greece, Hungary, Latvia, Malta, Portugal,
Romania, Slovenia and Switzerland and The Netherlands.
Most of the respondents confirmed that there is no national data quality framework implemented nor
planned (Belgium, Cyprus, Czechia, Greece, Hungary and The Netherlands). Other assistants informed
that although there is no national data quality framework for MMTIS implemented, it is already
planned (Estonia, Latvia, Malta, Romania, Slovenia and Switzerland). Only a couple of countries
confirmed the existence and implementation of a MMTIS quality framework: Austria and Finland.
In addition, most of the participants that answered were aware of the Framework for the quality of
European services for Multimodal Travel Information (EU EIP). The countries that selected this answer
were Austria, Belgium, Cyprus, Greece, Latvia, Romania, Slovenia, Switzerland and The Netherlands.
[page 14]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 14
Following that, 5 countries answered that were not aware of the existence of that Framework: Czechia,
Estonia, Hungary, Malta and Portugal. Finally, 2 respondents were aware of the EU EIP document but
confirmed that it was not relevant to the national MMTIS quality Framework of their countries: Finland
and Germany.
Finally, regarding whether the existing or planned national quality frameworks are inspired or not by
previously implementing QFs, Austria confirmed that the MMTIS Quality Framework was developed
independently from EU EIP but they are (both) comparable. On the other hand, Finland explained that
the existing quality framework implemented in MMTIS NAP is now rather basic in Finland. Now, a new
validation and conversion environment is on development which will radically improve the validation
process. This new environment uses quality frameworks published by mobility data foundation and
ENTUR as a base line.
Other country that seemingly started recently working in their own MMTIS quality framework is The
Netherlands, that confirmed that recently started with the National Access Point for Mobility Data.
They want to implement a quality framework, and they are not that far in the development.
Estonia shared that it is planned to use EU EIP as base for their future quality framework. Latvia will
take a similar approach making use of EU EIP and learning for the experience of other countries.
Romania, Hungary and Cyprus showed interest in developing their own MM TIS quality framework in
the future. Czechia also wants to prepare a MMTIS quality framework, for now, the working party has
been established. Finally, Germany pointed out its previous answer about DELFI “there some quality
frameworks but not at national level”. Belgium, Greece, Malta, Portugal, Slovenia, Switzerland and The
Netherlands did not provide further insights to this question.
The detailed responses of the poll are presented in Appendix IV
3.4.2. Dedicated presentations
Three workshops were held on the topic of “national implementation of MMTIS Quality Framework”
where the presenters shed light to the national approaches of quality frameworks:
• First workshop (19th April 2023):
o Norway national MMTIS quality framework . In Norway, the quality checks are
performed by ENTUR, which is the Norwegian NAP operator. The assessment
encompasses checks against the CEN standards and the Nordic NeTEx profile, since all
data is delivered to the NAP in NeTEx and SIRI format. When a NeTEx or SIRI dataset is
uploaded to the NAP it is validated. For NeTEx datasets, when an error is detected its
uploading stops, while for SIRI datasets the uploading continues as-is at that moment.
o Switzerland national MMTIS quality framework . For Swiss Operators, mobility
services do not start at the national border, and it is very important the
communication with the neighbour countries. There are several standards considered
in Switzerland. Often these are the CEN standards, but also others generated by CEN
(German standards) and industry standards like GBFS and GTFS. A national profile is
derived from each standard in a similar way as in the Nordic countries. Regarding
quality, they highlight the need to control the quality of the published datasets and to
have complete highly homogenised data sets. It is noted that sometimes, there are
organisations in the European context that publish data which is obviously not
consumed by themselves as their NeTEx datasets obviously never were validated.
• Second workshop (11th May 2023):
[page 15]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 15
o Austria national MMTIS quality framework. Austria has a centralized data collection
and provision service for public transport data. There are nine federal states in Austria
with seven data systems for public transport. All are connected in one centralized
system providing one user interface to end users (https://anachb.vor.at/). Moreover,
there are also private and regional train transport data operators that provide data to
the centralized system from Austria. The side systems that provide information to the
centralized system are:
▪ Network platform for spatial data and referencing system.
▪ Export interfaces for the end users.
Figure 1 Static public MMTIS data processing in Austria (Source: NAPCORE workshops)
• Third workshop (20th September 2023):
o Finland national MMTIS quality framework. Finland implemented national mobility
data validation service as a modular solution for MMTIS national access point
(https://finap.fi/#/ ). In Finland, the legislation obliges that MMTIS datasets are open
data. Validation module checks all listed services, watermarks the quality of the data
in NAPs data catalogue and if necessary, initiates data correction process with the
original publisher/provider of the feed. Validation module called “Vaco” integrates
valid data sets to the national mobility data database which is the master source for
all mobility data information in Finland. If data is not valid, data is not integrated into
a database.
o France national MMTIS quality framework. France provides quality checks through a
national body which is responsible to assess how MMTIS DR is implemented in the
country, the Autorité de régulation des transports (ART). In France, it was already
mandatory to publish real-time data in the National Access Point, before the amended
version of MMTIS DR by the DR (EU) 2024/490. Regarding the different standards used
in public transport, it is estimated that 15% of the datasets are natively published in
NeTEx. If a dataset is uploaded in GTFS, then it is converted to NeTEx in the National
Access Point.
[page 16]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 16
The insights from the different countries fed the definition of the proposed quality levels (as presented
in 5. Proposal for (minimum) Quality Levels) and methods and tools (as presented in the 6. Proposal
for Quality Assessment Methods). The summary of each country is presented in Appendix VI.
Beyond the presentation of the quality framework approaches in national level, some general remarks
and considerations were highlighted as input for the de finition of the quality framework at EU level.
Those considerations are summarized as follows:
✓ Cost of validation for data providers/ consumers should be considered in the process
✓ Different requirements for static data and real-time data lead to different criteria
✓ Quick reaction to errors is important for the reliability to the validation process
✓ Monitoring in different levels/stages of data provision process
✓ Quality aspect to be introduced in the “ Service contracts”, where details of what is required,
what is the response time, how issues are managed etc. are defined.
✓ Feedback loop for data providers and consumers to be available.
3.5. Input from relevant NAPCORE deliverables and other projects
The NAPCORE MMTIS Data Dictionary 13 is one of the main documents that was considered as it
indicates many parameters regarding completeness of data, compliance and other quality aspects. In
the following tables, it is summarised the main input concerned for QF.
Moreover, the quality frameworks for other data types were a very important input as well . The
objective is to adopt a harmonised approach as much as possible between different data types to
facilitate the integration of such frameworks. In the following paragraphs are presented which part s
of the other QFs are considered for MMTIS.
3.5.1. Input from other QFs
One of the aspects for a harmonised approach was the selection of the elements that a quality
framework should contain. Based on the Quality Framework s for Floating Car Data and for UVAR
(Urban Vehicle Access Regulation) Data14, the main elements to be considered are the following:
• quality dimension
• quality criterion
• description of the quality criterion
• description of each metric, whenever is relevant depending on the criterion
• mathematical formula, whenever is relevant depending on the criterion
• the possible values for each criterion
Moreover, the focus was given on the selected quality dimensions and criteria from those two QFs,
with the intention to assess whether those dimensions and criteria can be adopted also by MMTIS QFs.
In the following table, it is indicated which quality dimensions and criteria are common between the
different QFs. The quality dimensions can be actually common between all QFs, h owever, since the
nature of data is different, the criteria and their descriptions are not always the same among the
different QFs. The Appendi x I presents the quality dimensions and criteria of the different QFs in
details. Finally, this QF should be used in a complementary way with the Cross-Domain Quality
Framework which focus es on metadata information. Compatibility (or compliance) criterion and
trustworthiness, which examines whether a dataset is checked by a validator or other quality method,
13 https://github.com/NAPCORE/Data-dictionary/blob/main/DR%20(EU)%202024-490.md
14 https://napcore.eu/quality/
[page 17]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 17
may also be considered by cross -domain QF. The next t able presents the q uality dimensions and
criteria among different QFs . Accordingly, t he quality dimensions are common, however definitions
may be adapted per QF due to the different nature of the data.
Table 5 Quality dimensions and criteria among different QFs
Quality dimension FCD
Quality criteria
UVAR
Quality criteria
MMTIS
Quality criteria
Correctness Accuracy – error rate Location accuracy Location accuracy
Bias rate Validity of data
Classification correctness
Granularity
Completeness Spatial coverage Required data coverage Spatial coverage
Network coverage Provision of additional
information
Network coverage
Missing values Operators coverage
Granularity Operations coverage
Timeliness
OR Currency
Freshness Update frequency
(static UVARs)
Timeliness (dynamic UVARs)
Update frequency
(static data)
Freshness (real time data)
Latency Update in advance
Reliability
OR Relevance
Logical precision Logical precision
Uniqueness Data duplication Uniqueness
Trustworthiness Trustworthiness
Usability
OR Consistency
Compatibility Compliance with data standards Compatibility
Service availability
Accessibility Level of accessibility
NAP accessibility
3.5.2. Input from NAPCORE MMTIS Data Dictionary
The NAPCORE MMTIS Data dictionary15 contains valuable information to perform quality assessment
primarily against two main quality criteria : “Completeness” and “Reliability and Usability ” (includes
compliance to standards) of different data types. Nevertheless, depending on the data type , further
quality aspects are defined, like timeliness, uniqueness and coverage. The table below presents a quick
inventory of the data types where quality dimensions are mentioned in NAPCORE MMTIS data
dictionary, as incorporated in this QF. Detailed information is available at the Appendix V.
Table 6 Data types and relevant quality dimensions mentioned in MMTIS Data dictionary
Data types Relevant quality dimensions
mentioned in MMTIS Data
dictionary
Location search (origin/destination):
• topographic places (city, town, village, suburb, administrative unit):
• for scheduled transport and transport on demand where relevant:
identified access nodes
• for transport on demand and personal transport: secure bike parking
(such as locked bike garage)
Completeness
Reliability and Usability (includes
compliance to standards)
15 https://github.com/NAPCORE/Data-dictionary
[page 18]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 18
Data types Relevant quality dimensions
mentioned in MMTIS Data
dictionary
Trip plan computation for scheduled transport and transport on demand where
relevant:
• connection where interchanges may be made
• transport operators
• planned interchanges between guaranteed scheduled services
• hours of operation
• road network (including segregated lanes for bus/taxi)
Completeness
Reliability and Usability (includes
compliance to standards)
Location search (origin/destination):
• points of interest (related to transport information) to which people
may wish to travel
Completeness, Timeliness,
Uniqueness,
Reliability and Usability (includes
compliance to standards)
Trip plan computation:
• for scheduled transport and transport on demand where relevant:
timetables
3.5.3. Input from DATA4PT guidance document
Important information for this QF was gathered from the guidance paper16 prepared by DATA4PT
experts’ team. This paper proposes best practices and provides guidelines for National Access Points
(NAPs) to follow for a better implementation of MMTIS Delegated regulation (EU ) 2017/1926 and its
amendment (EU) 2024/490). In this document , the importance of quality of the data in NAP is
underlined as one of the basic parameters that will allow interoperability and usability of the data
(“Only complete, homogenised, integrated data sets are of interest. Quality assurance needs to be an
integral part of all NAPs .”). The document mentions the significance of NAPs providing “tools to be
accessible by the transit agencies that present high-quality mobility data accessibly, equitably, and in
real-time to assist travelers in meeting their mobility needs.” Therefore, in this QF a particular section
is dedicated to available tools.
Regarding quality dimensions and criteria, the guidance paper highlights the up-to-datedness
(freshness) of the data and the compatibility - required by the DR - with the data exchange standards.
In particular, the following standards shall be used: NeTEx (stop registry, schedules, fares), SIRI (real -
time), OJP (API to a journey planner), and in general the ones based on Transmodel (CEN standard) ,
also OpRa, as soon it becomes available. In addition, other formats/ specifications might be shared in
NAPs if useful by data consumers like GTFS/GBFS.
Considering the recommendation that “the NAPs should provide a Quality-of-Service statement for its
operation”, this QF aims to contribute to this effort.
The recommendations of the guidance paper are incorporated in “Proposal for Quality Assessment
Methods” section.
16 https://data4pt.org/w/index.php?title=National_Access-Points
[page 19]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 19
4. Proposal for Quality Criteria
The quality criteria are organised in four (4) dimensions: Correctness, Completeness, Timeliness,
Reliability and Usability. The dimensions and the criteria correspond to specific data types, depending
on their nature: whether are static, real-time, location related or service and time related.
The following table shows the classification of the data types and their relation to the Annex of the
MMTIS DR, as applied for the definitions made later in this QF.
Table 7 Classification of the data types
Classification of data types Relation to the Annex of the MMTIS DR
Static data, locationrelated
Level of service 1
Trip plan computation for scheduled transport and transport on demand where relevant:
- connection where interchanges may be made
- network topology and routes/lines (topology)
Location search (origin/destination):
- addresses, topographic places, points of interest
- identified access nodes
- geometry/map layout structure of access nodes
- connection where interchanges may be made
- accessibility of access nodes, and paths within an interchange (such as existence
of lifts, escalators),
- planned interchanges between guaranteed scheduled services
- facilities of access nodes (including platform information, help desk/information
points, ticket booths, lifts/stairs, entrances and exit locations)
- accessibility of access nodes, and paths within an interchange (such as existence
of lifts, escalators).
Level of service 2
Location search – for transport on demand and personal transport:
- location of parking places (on and off-street), including accessible parking places
for persons with disabilities and persons with reduced mobility
- Park & Ride stops, Park & Drive stops, bike-sharing stations, car-sharing stations,
secure bike parking (such as locked bike garage), scooter parking zones.
Static data, time/service
related
Level of service 1
Trip plans: operational calendar, mapping day types to calendar dates:
- operating day, service calendar.
Trip plan computation – for scheduled transport and transport on demand where
relevant:
- Default transfer times at interchanges. Time-related attributes of TRANSFER
- Timetables: timetabled passing time, dated passing time: encompasses
expected departure times, expected waiting times, and in some cases (partially
on demand) earliest departure times, and latest arrival times.
- Hours of operation. The time of starting services and time of closing services
(e.g. for local public transport which may propose timetables, but also only
headways per period of the day).
Dynamic data Level of service 1 – Dynamic data
Passing times, trip plans and auxiliary information:
- disruptions, such as network closures and/or diversions, and when possible, the
reason
real-time status information, such as estimated departure and arrival times of services,
delays, cancellations, guaranteed connections monitoring.
Completeness and Reliability (technical and conceptual) & Usability is relevant to all data types ,
whereas the other dimensions are relevant only for some data types.
The following tables show the related definitions for the quality definitions, divided per data type.
[page 20]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 20
Table 8 Overview of quality dimensions and criteria targeted for all data types
Data types targeted: All data types
Quality dimension Quality criterion Description of quality criterion
Completeness Completeness of a
dataset
Indication of whether, for a given service or
data type, all the data entities expected by the
MMTIS Delegated Regulation are provided17.
To check completeness of datasets an
automated tool might be used to check against
EU profiles. Completeness should follow
recommendations of MMTIS Data Dictionary
about the necessary and optional elements a
data is described with.
Reliability (technical and conceptual) &
Usability
Compatibility
Extent to which the dataset is provided in the
relevant standard according to DR (EU)
2024/490.
Usability The number of services which use the provided
data.
Table 9 Overview of quality dimensions and criteria targeted for static data, location-related
Data types targeted: Static data, location-related
Quality criterion Description of quality criterion
Completeness 18 Network coverage Percentage of network shared by a dataset compared to
the full network covered by the service provider.
Detailed:
- % of lines
- % of stops;
- % of stations;
- % of vehicles for on demand services.
Spatial coverage Percentage of service area provided in the dataset
compared to the full service area covered by the service
provider.
Reliability (technical and
conceptual) & Usability
Logical precision Extent to which dataset contains logical errors (for
example distance between stops are very small/very big
depending on the transport mode).
Uniqueness Indicates whether there are duplicated data elements in a
dataset (for example IDs are not unique in a given
dataset, subsequent stops have the same coordinates for
a given headway).
Correctness Location Accuracy Extent to which the provided location coordinates of
network elements are represented in an accurate
manner. Correctness can be measured when exists a
national (or European) stop registry where comparison
can be made compared to the shared location reference
information.
17 Completeness compared to MMTIS DR data categories is a “must”, but it can be also in respect to a specific Service.
Therefore, completeness to an EU profile is important. Currently countries deal with completeness by using national profiles
that defined requested information among the different data categories. For example in Italy, the national profile includes
timetables, network for STOP POINTS which are adequate for MMTIS DR, but non -sufficient for Journey Calculation where
QUAYS are needed too.
18 Data holders should release complete data set. If there are missing parts, probably should not be considered as
quality issue but instead as a legal issue. Network coverage and spatial coverage is also proposed by NAP operators
to be assessed as an on-off situation. Data should either be 100 % complete or not available at all.
[page 21]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 21
Table 10 Overview of quality dimensions and criteria targeted for static data, time/service related
Data types targeted: Static data, time/service related
Quality criterion Description of quality criterion
Timeliness Update frequency
(static data)
How often the static dataset is updated
regarding interregional journeys (long distance transport
services).
How often the static dataset is updated regarding local
journeys (short distance transport services).
Update in advance Extent to which the dataset was shared before the
validity date of the operations.
Reliability (technical and
conceptual) & Usability
Logical precision Extent to which dataset contains logical errors (e.g.,
vehicles arrive at final stop before leaving previous stop).
Uniqueness Indicates whether there are duplicated data elements in a
dataset (e.g. same ID for different services).
Completeness Operators’ coverage Percentage of Public Transport (PT) operators in a specific
region covered by the dataset compared to all PT
operators operating in a specific region.
Operations coverage % of trips for regular services.
Table 11 Overview of quality dimensions and criteria targeted for dynamic data
Data types targeted: Dynamic data
Quality dimension Quality criterion Description of quality criterion
Timeliness Freshness Assess the frequency on which the real- time dataset is
updated.
Timeliness (start) Timeliness (start): The time between the occurrence of an
event and the acceptance of the event. (i.e. the time
between the occurrence of the disruption and the
acceptance of it).
Timeliness (update) The time between the end or relevant change of
condition and the acceptance of this change.
Reliability & Usability Logical precision Extent to which dataset contains logical errors (e.g.,
vehicles arrive at final stop before leaving previous stop).
Uniqueness Indicates whether there are duplicated data elements in a
dataset
[page 22]
5. Proposal for Quality Levels
Beyond the quality dimensions and criteria, this QF proposes a system to assign a quality level depending on the status the dataset has compared to the
corresponding criteria. Possible values and formulas are added when relevant. In case of using the proposed values, a higher score usually means a better quality.
The table below, inspired by the QFs for other data types, encompasses input from the experts’ pool. However, more elaboration from more NAP operators is
needed to lead to a concrete set of KPIs and quality levels calculation. The table is split based on data types to match them with corresponding criteria and KPIs.
The tools and methods proposed per each criterion are also included, when available.
Table 12 Data criteria relevant to all data types and corresponding proposed values
Data types targeted: All data types
Quality
dimension
Quality
criterion
Criterion
description
Metrics
Metric
description
Mathematical /
Theoretical
formulation
Possible values Tools or methods Notes/Comments
Completeness Completeness
of a dataset
Indication of
whether all
expected
entities by the
referenced
standard, for a
given service or
data type, is
provided.
(for example,
no coordinates,
stop has no
traffic mode,
stop has no
place name)
In case it exists
a EU profile,
the dataset
should be
checked
compared to
the profile.
Respectively if
Percentage of
fulfilment of
requested
entities in the
dataset.
In what
percentage
the dataset is
complete?
Percentage Automated tool to
check completeness of
data might be
produced based on EU
profiles
To identify which
information is
expected per each
data category consult
the MMTIS data
dictionary. An extract
of this information is
also available in this
QF report.
For interchanges, trip
planners might
calculate the time and
distance derivatives of
the connection. Thus,
interchanges might
not be part of the
dataset.
Completeness is also
linked to the way a
dataset is structured
(what data types it
includes). Each NAP
[page 23]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 23
there is a
national profile.
might have each one
dataset rules in terms
of content however to
enable a unified
assessment of the
quality across
countries and be able
to build common tools
it is necessary to
follow the same rules.
Rules on how to create
a dataset are included
in MMTIS data
dictionary (also in the
DATA4PT guidance
document).
Reliability
(technical and
conceptual) &
usability
Compatibility
Extent to which
data is
provided in the
relevant
standard
according to
EU(DR)
2024/490. In
case it exists a
EU profile, the
dataset should
comply with
the profile.
Respectively if
there is a
national profile.
Binary
classification
Qualitative
measure in
which the
dataset
complies with
the required
format.
Does the dataset
comply with the
relevant standard
according to
EU(DR)2024/490?
(e.g. Transmodel,
NeTEx, SIRI, etc.).
In case it is not
comply, to list the
differences compared
to the profile.
0: No; 1: Yes Open-source tools:
ANTU (ENTUR)
VACO (FINAP)
Greenlight validator for
NeTEx datasets
Usability The number of
services which
use the data
provided.
Absolute
number
Not available Not available Not available Not available Not available
[page 24]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 24
Table 13 Data criteria relevant to location - related static data and corresponding proposed values
Data types targeted: Static data, location-related
Quality
dimension
Quality criterion Criterion
description
Metrics
Metric
description
Mathematical /
Theoretical
formulation
Possible values Methods/tools Notes/Comments
Completeness
Network
coverage
Percentage of
network shared
by a dataset
compared to
the full network
covered by the
service
provider.
- % of lines
or/and
- % of stops
or/and
- % of stations
or/and
- % of vehicles
or/and
- % of km.
% of vehicles
relevant to on
demand
services
Percentage
Length (km)
of network
links covered
in the
datasets: X
Total length
(km) of
network links
covered by
the service
provider of
the dataset: Y
(if km) LC = x/y*100 0 to 100 %
For road networks,
the considered roads
need to be of a
certain categorisation
(for example forest
utility roads should
not be considered in
the percentage).
Spatial coverage Percentage of
service area
provided in the
dataset
compared to
the full service
area covered by
the service
provider.
Spatial
Coverage (SC)
Percentage
Surface (km2)
where the
service
described in
the dataset is
performed: X
Total surface
(Km2) where
service
provider
operates: Y
SC = X/Y*100 0 to 100 %
<75% coverage 0,
<90% coverage 1 ,
<95% coverage 2
95%-99%
coverage 3
99-100%
coverage 4
Coverage: The degree
of
coverage/completene
ss should be declared
per geographical
region (e.g. country)
in terms of
percentages/fractions
(e.g. “100 % of trains
in country A are
covered” and a
description which
modes, operators are
missing.
[page 25]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 25
Quality
dimension
Quality criterion Criterion
description
Metrics
Metric description Mathematical /
Theoretical
formulation
Possible values Methods Notes/Comments
Reliability
(technical and
conceptual) &
usability
Logical precision Extent to
which dataset
contains
logical errors
(for example
distance
between
stops are very
small/very big
depending on
the transport
mode).
Errors number
based on
errors
classification.
Estimates the
number of logical
errors in a record
based on errors
classification.
How many errors and
of which importance
the dataset has?
Number of critical
errors (errors that
are classified as
critical (making
data unusable).
Number of
warnings (errors
that are classified
not critical but
they imply some
issues)
Examples of errors
classification is provided
in Chapter 6. For this
kind of evaluation, a
data validator with
precise validation rules
is needed. For NeTEx
(static) datasets there
are available open
source tools and
proprietary ones.
https://data4pt.org/w/i
ndex.php?title=NeTEX#
Data_validation_tools
For SIRI (real-time data),
relevant tools are
https://data4pt.org/w/i
ndex.php?title=SIRI#Da
ta_validation_tools.
Uniqueness Indicates
whether
there are
duplicated
data
elements in a
dataset (for
example ID is
not unique,
subsequent
stops have
the same
coordinates
for a given
headway.)
Binary
classification
Check whether
elements/attribut
es in the dataset
are unique.
0: No; 1: Yes This is one of the basic
validation rules to
consider. Basic XSD
(XML schema)
Usability Indicates
whether
identifiers in
the dataset
Is dataset using local
and/or global unique
identifiers referenced
to a master file?
No: Data no
usable (binary
value 0)
[page 26]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 26
are useful, so
they are
fulfilling local
and/or global
uniqueness
while are
referenced to
a master file.
Yes: Data are
usable (binary
value 1)
[page 27]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 27
Quality
dimension
Quality
criterion
Criterion description Metrics
Metric
description
Mathematical /
Theoretical
Formulation
Possible values Tools/Methods Notes/Comments
Correctness Location
Accuracy
Extent to which the
provided location
coordinates of
network elements
are represented in an
accurate manner.
Horizontal
location
accuracy (for 2
dimensional
location points)
Xmi, ymi =
measured
position
coordinates
(shared with the
dataset)
Xti, Yti= true
position – true
coordinates
For a number of
points (N), the
measured
positions are
given as xmi and
ymi coordinates.
A corresponding
set of coordinates
xti and yti are
considered to
represent the
true positions.
D=√[(xmi2 − xti 1)2 +
(ymi2 − yti1)2]
Possible values
proposed in cells
below.
Vertical location
accuracy is also
important for elements
that are in different
elevation compared to
the ground floor but
currently no metrics are
proposed
Accuracy of
coordinates of link
nodes for all provided
network elements,
compared to ground
truth.
Same metric,
different values
proposed per
different location
point.
Same formula,
different thresholds
For Network
topology and
routes/lines:
For bus network
(stop points):
< 2 m : value 1
> 2m : value 0
For railway stations:
< 50 m: value 1,
>50m : value 0
Vertical location
accuracy is also
important for elements
that are in different
elevation compared to
the ground floor but
currently no metrics are
proposed
Accuracy of
coordinates of
geographic position
for all provided
Same metric,
different values
proposed per
Same formula,
different thresholds
For planned
interchanges
between
guaranteed
It might be also be
useful to have a
measure that deals with
outliers.
[page 28]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 28
interchanges
compared to ground
truth.
different location
point.
scheduled services:
< 50 m: value 1,
>50m : value 0
Accuracy of entry
positions for each
provided stop or
station, compared to
the actual position of
the entry. It is
measured on the
ground as a “direct
line-of-sight”
distance between the
actual position and
the one indicated to
the observer on the
map.
Same metric,
different values
proposed per
different location
point.
Same formula,
different thresholds
Park & Ride stops: <
10m: value 1, >10m:
value 0
Bike sharing
stations: < 10m:
value 1, >10m: value
0Car-sharing
stations: < 10m:
value 1, >10m: value
0
Vertical location
accuracy is also
important for elements
that are in different
elevation compared to
the ground floor but
currently no metrics are
proposed
[page 29]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 29
Table 14 Data criteria relevant to time-service related static data and corresponding proposed values.
Data types targeted: Static data, time/service related
Quality
dimension
Quality
criterion
Criterion
description
Metrics
Metric
description
Mathematical /
Theoretical
formulation
Possible values Tools methods Notes/Comments
Timeliness Time
horizon of
operations
Is the time
horizon of the
services
described in
the provided
data within the
limit of 120
days in
advance?
Binary classification Not available 0: less or equal to 120 days
1: more than 120 days
Based on MMTIS data
dictionary: The time
horizon of the
timetable is of
importance. In some
cases, booking occurs
up to 120 days in
advance. Having a
prospective time
horizon of timetables
of those 120 days
would be idea and
should be aspired to.
For long distance trips
3 information can be
obtained up to 3
months in advance.
Update
frequency
(static data)
How often the
static dataset is
updated?
Indication of the
times per week, or
per month or per
year that updates
occur.
Not available How often is
updated the static
data?
2: once or more per week
1: once or more per month
0: when updates are made
beyond the time horizon as
set above.
Updates should be
available before they
occur within the time
horizon.
Update in
advance
The dataset
was shared
before the
validity date of
the operations.
This criterion is
relevant also
when planned
changes are
occurred
before the time
horizon of the
Binary classification
Not available The dataset was
shared before the
validity date of
the operations.
0: No
1: Yes
French NAP requests
providers to update
their dataset at least
48-72 hours before
the expiration date of
the operations.
[page 30]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 30
of static data
should be
shared in
advance.
Reliability
(technical and
conceptual) &
usability
Logical
precision
Extent to which
dataset
contains logical
errors (e.g.,
vehicles arrive
at final stop
before leaving
previous stop).
Number of not
critical errors based
on errors
classification.
Estimates the
number of logical
errors in a record
based on errors
classification.
Are there critical
errors in the
dataset?
How many not
critical errors
(warnings) has
the dataset?
Number of critical errors
should be 0 (errors that are
classified as critical making
data unusable).
Number of warnings to be
counted (errors that are
classified not critical, but
they imply some issues)
Uniqueness Indicates
whether there
are duplicated
data elements
in a dataset
Binary classification Check unique IDs
in a dataset /
datafile
Are the datasets /
datafiles IDs
unique?
0: No; 1: Yes
[page 31]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 31
Table 15 Data criteria relevant to dynamic data (real-time data) and corresponding proposed values.
Data types targeted: Dynamic data (check MMTIS data dictionary for definitions)
Quality
dimension
Quality
criterion
Criterion description Metrics
Metric description Mathematical /
Theoretical
formulation
Possible values Tools methods Notes/Comments
Correctness Arrival time
estimate
accuracy
Indicates whether
there are differences
between estimate
arrival time and
actual arrival time
The estimate
delta is measured
as the mean
absolute
difference (in
seconds) between
the estimated
remaining travel
time and the
actual remaining
travel time 10
minutes before
arrival.
Values are not at this Quality
Framework.
Real time arrival
estimates are
compared at
1,3,5,10,15,20,30,45
minutes before actual
arrival. Different delta
metrics can be chosen
from the drop-down.
If no estimate is
available at x minutes
before arrival it
contributes to the %
of missing estimates.
19
Timeliness Update
frequency
Assess the frequency
on which the real -
time dataset is
updated.
Depends on the
mode of
transport.
Formula is not
defined at this QF.
Values are not defined at this
QF.
It shall be dynamically
updated as soon as it
becomes available to
reflect the latest
operational status of
transport services.
Based on Norway
example, real -time
data (SIRI) received at
maximum every
minute (usually
between 10 -30
seconds).
Timeliness
(start)
Timeliness (start):
The time between the
occurrence of an
event and the
Formula is not
defined at this QF.
Values are not defined at this
QF.
19 ENTUR approach: https://lookerstudio.google.com/reporting/1d6d59e5-05a2-42ee-b965-a1d390f323e8/page/p_k0lb171bkd
[page 32]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 32
presentation of the
event in the service of
the event. (i.e. The
time between the
occurrence of the
disruption and the
moment is made
available in the
service (NAP)
acceptance of it)
Timeliness
(update)
The time between the
end or relevant
change of condition
and the acceptance of
this change.
Time interval for
announcing the
progress or end of
the disruption.
Time interval for
calculating and
refreshing new
travel times
Formula is not
defined at this QF.
Values are not defined at this
QF.
Reliability
(technical and
conceptual) &
usability
Logical
precision
Extent to which
dataset contains
logical errors (e.g.,
vehicles arrive at final
stop before leaving
previous stop).
Binary
classification
Does the dataset
present logical
errors?
0:errors
1:with errors and provision of
the number of warnings.
Uniqueness
Indicates whether
there are duplicated
data elements in a
dataset
Binary
classification
Check unique IDs
in a dataset /
datafile
Are the datasets /
datafiles IDs
unique?
0: No; 1: Yes
Coherence between a
static data set (e.g.
NeTEx) and
corresponding
dynamic data set (e.g.
SIRI) can also be used
as accuracy indicator.
[page 33]
6. Quality Assessment: Approaches and Methods
6.1. Introduction
This chapter aims to summarise the best practices for quality assessment approaches and methods
and present in more details the tools that can be implemented to support the evaluation of quality
levels, to identify errors, as well as to manage errors in order to contribute to the “sanitation” of the
datasets.
6.2. Description of approaches and methods
6.2.1. Perform quality assessment in different stages of data provision chain/process
The provision of data to NAPs is one of the last stages of the data production and provision chain.
Previous stages concern the production and collection of the data from the source, the processing
(aggregation or other actions) and the final supply to the end user/consumer or the entity which may
evaluate the implementation of the NAP . Different actors can be involved and depending on the
country the NAP operator might have several roles in this chain. The best practice is to perform quality
checks in different stages so to capture errors and inconsistencies early enough to be able to correct
them efficiently. At each stage different quality criteria are assessed via different methods.
This practice is adopted by Austrian Mobility Database. The NAP in this case is involved in the stage 3
of checks “during data supply and provision”.
Table 16 Quality assessment in different stages of data collection and provision chain - the approach from Austria.
Stages of data collection and provision chain
Stage 1: During data collection
- Software quality checks (i.e. format)
- Sample checks on content
- User feedback
Stage 2: During data processing
- Software quality checks (integrity, consistency, plausibility, availability, completeness of
stops, sections, lines, etc.)
- Checks on content (logical), Connection queries (samples), Data processability, Automated
log monitoring (process)
- Reference queries (samples)
Stage 3: During data supply and provision
- Schema validation, Availability / accessibility, Plausibility / completeness, User feedback
- Service use statistics
Similar approach is also adopted by Italian NAP. In Italy, there are two stages of validation: a) one at
producer level, where also an aggregation of data from public transport operators at Regional Level is
realized, and b) second at NAP level, which verifies datasets before importing them in a Transmodel
compliant database. For the seven (7) Italian Regions (currently) a third level of check is performed to
verify that datasets are importable in OTP for Trip calculation.
6.2.2. Establish different types of errors and relevant errors management
There are different types of errors that can appear during the data quality process. Some of those are
critical and some are not so critical. Depending on the significance of the errors , a different
management is required. For example, for some errors, the harvesting of dataset might stop, while for
some other errors, the dataset might be adopted. The approach of Austria is to have three types of
[page 34]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 34
errors: a) critical error, b) error, c) warning. If a critical error is detected, it stops the harvesting of the
complete data set while when an error is not critical (generating a warning) the data can be published.
The following table shows an o verview of national approaches which led to the criteria used in this
MMTIS QF. For details on national approaches, check Appendix VI.
Table 17 Types of errors and their correlation with quality criteria and quality dimensions
Error types
Criteria
France Austria Finland Norway Correspondence
to
QF MMTIS
criteria
Correspondance
to
QF MMTIS
dimensions
Level 1: Fatal –
very critical
error 20
Accessibility Compatibility Reliability &
usability
Level 1: Fatal –
very critical
error
Readability Readability
(Schema
validation)
Readability
(Schema
validation)
Readability
(Schema
validation)
Compatibility Reliability &
usability
Level 1: Fatal –
very critical
error
Up to date Up to date Update
frequency
/Freshness
Timeliness
Level 1: Fatal –
very critical
error
Normality Plausibility Plausibility Plausibility Logical
precision
Correctness
Level 1: Fatal-
Critical- very
critical error
Uniqueness Uniqueness Uniqueness Uniqueness Uniqueness
Level 2: Quality
data
assessment
/error/critical
Completeness Completeness Completeness Completeness Completeness
of a dataset
(checked with
EU or national
profiles)
Completeness
Level 2: Quality
data
assessment
/error/critical
Relevance Availability Completeness
of a dataset
(checked with
EU or national
profiles)
Completeness
Level 2: Quality
data
assessment
/error/critical
Consistency Consistency Consistency Consistency Logical
precision
Correctness
Level 3:
Dataset quality
certification/
warning/not
critical
Exhaustiveness
Level 3:
Dataset quality
certification/
warning/not
critical
Accuracy Accuracy Accuracy (i.e.
arrival time
estimate
precision)
Location
Accuracy
Correctness
In Norway, fixes are done by the NAP operator depending on the error. For major errors data are
pushed back to the provider. In Norway, if the datas et, consisted of static data ( NeTEx datasets) ,
contains an error based on their validator, the dataset is not uploaded to the NAP until is corrected.
20 As an example in Italy, a frequent error is on SCHEDULED STOP POINT, when those are not in the correct temporal order.
[page 35]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 35
For datasets consisted of real-time data (SIRI), the uploading to the NAP continues even though errors
are detected.
Similar approach is adopted by French national body “Autorité de régulation des transports ” (ART).
Static data is interrupted to upload if there is an error detected in the system, while real time (dynamic)
data is not stopped.
Figure 2 Example of control framework divided into level of errors, set up by ART. (Source: NAPCORE workshops).
In Finland, if published datasets are recognized as GTFS and/or NeTEx files, they are checked against
the relevant standards. In case discrepancies are found (e.g. missing mandatory files, the files are
empty, files did not include the standard) data is given either a status of warning and/or error. If data
receives an error status, the MMTIS NAP starts the automated correction process with the feed
publisher organization. NAP lists also broken data with validation markings and report. If data is
broken, it won’t get included into national mobility database which is service that offers all NAP
datasets with easy access.
In Italy, if a dataset is not valid after the validation process of NAP, an automatic notification is sent to
Data Producer (Region) with errors indication.
6.2.3. Data user/consumer feedback
The data user is one of the most important channels to provide feedback and therefore to contribute
to the improvement of data quality . The NAP itself might also be the consumer of the provided data
(in case it provides passenger information services ), which gives an advantage in detecting errors in
efficient way. Stakeholders notice that there are organisations that publish data which is not consumed
by them. For example, they provide NeTEx datasets that are non-valid XML files. Therefore, there is
the need to ensure that data shared are also data consumed.
[page 36]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 36
In Italy , currently, the most important "users" are the MaaS Operators, that download a so called
“snapshot” (huge NeTEx file which includes all the data of a specific Region) and import it in Open Trip
Planner (OTP) for Trip Calculation while matching with SIRI data (match of ID).
The collection of data users feedback can be achieved by relevant questionnaires. Best practices come
from Norway (ENTUR), Austria.
Possible questions for the collection of user’s feedback are.
• To what extent has the data you have accessed via NAP data platform been useful?
• How satisfied are you with the services NAP provides regarding data quality assessment?
6.2.4. Quality reports
Data quality reports are necessary to be openly available also to incentivise data providers. Best
practices from ENTUR21, Italy and other countries are already implemented.
Figure 3 Example of d ata quality dashboard with overall scores assigned to public transport authorities and operators in
Norway concerning real-time data (Source: ENTUR).
6.2.5. General guidelines
The following statements are based on the DATA4PT guidance22.
- The NAPs should incentivise data producers to provide correct data: complete, quality -
assured, and valid on syntactic and semantic levels. This can be done by checks performed by
the NAPs themselves (as e.g. the French NAP does for GTFS).
- Data providers should have instructions and a unified understanding of what to publish and a
unified way to verify the quality of the dataset published in the NAP. MMTIS QF aims to support
this effort of NAP operators.
- The NAPs should provide an open issue tracker to report data problems . Data providers that
share data to NAP should have access to the results of the quality process.
- NAPs should provide cross-references to relevant other datasets that are temporal or spatial
in nature. The new timetable for next year, the timetable of a neighboring region, or an
adjacent data theme.
21 https://data-quality.entur.no/
22 https://data4pt.org/w/index.php?title=National_Access-Points
[page 37]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 37
- The NAP is responsible for upstream communication about quality issues.
- The NAP gives guidance on the relevant ID and master data management.
6.3. Description of tools
The paragraph includes a presentation of existing open-source tools that can be used by the NAP
operators and other stakeholders to allow the validation against the presented quality criteria . Some
of those might also be incorporated into the quality assessment process as integrated tools.
6.3.1. Compatibility to standards and logical precision validation
• Validator tool developed in the framework of DATA4PT project (Greenlight validator).
Extended information about this presentation can be found in a webinar presented by
Data4PT23 .
The Greenlight validator performs a series of checks in the datasets to assess their quality. The most
basic check is to confirm that the XML schema and the format of the dataset is correct and there are
no errors present (syntactic check). Moreover, additional rules (checks) can be applied to the validator
to tailor it to the national requirements. The results of these validations are linked to different severity
levels.
• VACO validation module in Finnish NAP.
VACO supports NeTEx, GTFS and GBFS standards validation. From 2024, SIRI and GTFS RT standards
are also supported. VACO checks all compatible mobility data sources listed in the MMTIS NAP. Vaco
is an independent validator and conversion rule module and service . Its current form incorporates
NeTEx validation rules from Entur and GTFS validation rules directly from Mobilitydata.org. The VACO
UI-generated validation report gives detailed access for each individual feeds provided by mobility
service providers. The validation report is generated from all data sources ( i.e., indicating if valid or
not). The tool is available at Fintraffic website VACO24 and in GitHub25.
• Open-source validation library and services by Entur
To secure interoperable cross -border date available in the different NAPs we should use the same
validation tool. Entur developed the NeTEx-validator-java26 library that can be used by everyone,
regardless of profiles. Optional you could use the stand alone Antu validator27 with local adaptations.
In this way we secure harmonization of data to make it easy to use by any third-party open data users.
The NeTEx-validator-java library validates towards the NeTEx standard, profiles and some logical tests.
6.3.2. Visualization
The visualisation maps enable the assessment of data in a manual way. They are meant to detect
obvious inconsistencies or abnormal situations in the circulation of the vehicles. Major errors regarding
stop points, or journey patterns might be detected visually. Relevant tools are provided by Norway
(ENTUR):
23 https://www.youtube.com/watch?v=xgI6Gd57574
24 https://validator.fintraffic.fi/ui/
25 https://github.com/tmfg/digitraffic-tis-vaco
26 https://github.com/entur/netex-validator-java
27 https://github.com/entur/antu
[page 38]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 38
• New modes visualization map (floating vehicles and docking stations) https://mobility -
map.entur.org/.
• Scheduled modes vehicles visualization map (bus, ferry, metro, tram, coaches, rail, air)
https://vehicle-map.entur.org/.
6.3.3. Stop registries for uniqueness
Tiamat is the Stop Place Register backend developed by Entur. It is used nationally in Norway, and
other places. It fully supports NeTEx.
Abzu is the Stop Place Register frontend. Uses Stop Place Register backend Tiamat's graphQL API.
Supports the use case of maintaining all stops and quays in Norway and internationally when needed.
If we need to support new use cases, often an update of the front end is enough, since the backend
are fully NeTEx supported.
[page 39]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 39
7. Conclusions
High quality is a pre-requisite to make the data in a NAP useful. It requires NAP operators and other
authorities to undertake the role of validation in a harmonized way in order to overcome
interoperability issues. It is highlighted that the provision of data to a NAP is the last stage of the data
production and provision chain, and quality assessment , to be efficient , needs to be performed at
previous stages.
So far, the first attempt to create a European quality framework was in the context of EU EIP project
in 2019. This report proposed some quality criteria and presented evaluation me thods that were
available at that time . H owever, it was not adopted during the following years by national
stakeholders, also because of the late implementation of the MMTIS DR in terms of data collection and
provision, and as well because of the latest recent changes of the legislation.
Nevertheless, at national level several initiatives took place , like in Norway, France, Finland, Austria
and more, while other countries started to plan the establishment of a framework. Those countries
leveraged the knowledge and experience acquired while advancing in the collection and provision of
data in the NAP and the interaction they had with other countries. Their experience on understanding
the needs but also the restrictions on building a quality framework was the main input of this report,
together with other important papers produced in the context of NAPCORE and DATA4PT.
Based on th is input, t his Quality Framework presents an updated set of quality definitions for the
MMTIS data domain , such as quality dimensions and criteria for various data types . Regarding the
quality criteria, the following conclusions are given:
The primary quality criterion is the Compatibility with the reference data exchange standard for each
data type. Compatibility is seen as one of the reliability and usability parameters . The information
about the reference data exchange standard is included in MMTIS Data Dictionary (NAPCORE, 2024).
This is the first step for all quality assessment methods.
The second more important dimension is the Completeness of data. The completeness of a dataset
can be relatively easily assessed using a common EU data exchange standard profile. Completeness
compared to MMTIS DR data categories is a “must”, but it can be also in respect to a specific Service.
Therefore, completeness to an EU profile which addresses service-related requirements is important.
Currently countries deal with completeness by using national profiles that defined requested
information among the different data cat egories. It is essential that EU countries adopt common EU
profiles to achieve data interoperability. Even if national profiles might exist but for local use, NAP data
should be published at least based on EU profiles of the relevant MMTIS standards. Guidelines about
profiles definitions are included in the DATA4PT guidance28.
Location accuracy is equally important for all location-related data ( stop places, quays, points of
interest, etc.). Inaccurate coordinates make the datasets unusable. The same stands for Timeliness for
time and service-related data. The update frequency, the update in advance, the accurate valid period
of a service, are significant for passenger information systems and their lack leads to lack of passengers’
trust.
Finally, it is suggested to continue the elaboration of the criteria and how better they can be measured
with the appropriate metrics and values as a next step of this work.
28 https://data4pt.org/w/index.php?title=National_Access-Points
[page 40]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 40
Appendix I
Table 18 Data types included in MMTIS Delegated Regulation (2024/490 ) that are not in the main
scope of this MMTIS QF.
“S” stands for “static” (S = Point 1 of MMTIS DR ANNEX), “D” stands for “dynamic” ((D = Point 2
of MMTIS DR ANNEX) .
Data
category/Level
of service Data type Data type description
S-4
Historic travel and traffic data on
delays - for scheduled transport and
transport on demand where relevant
S-4 Observed data on delays and passing time - for scheduled transport
length of, and when possible, the reason
for, delays of at least 60 minutes for rail
passenger services (in accordance with
Article 19 of Regulation (EU) 2021/782)
S-4 Observed data on delays and passing time - for scheduled transport
length of, and when possible, the reason
for, delays in departure of more than 90
minutes for sea and inland waterways
passenger services (in accordance with
Article 18 of Regulation (EU) No
1177/2010)
S-4 Observed data on delays and passing time - for scheduled transport
length of, and when possible, the reason
for, delays in departure from a terminal
of more than 120 minutes for regular bus
and coach passenger services with a
scheduled distance of 250 km or more (in
accordance with Article 19 of Regulation
(EU) No 181/2011)
S-4 Observed data on delays and passing time - for scheduled transport
length of, and when possible, the reason
for, flight delays at departure of at least
120 minutes; and flight delays at arrival
of at least 180 minutes (in accordance
with Articles 5 and 6 of Regulation (EC)
No 261/2004)
S-4 Observed data on cancellations - for scheduled transport cancellations, and when possible, the reason, of rail passenger services
S-4 Observed data on cancellations - for scheduled transport cancellations, and when possible, the reason, of sea and inland waterways passenger services
S-4 Observed data on cancellations - for scheduled transport
cancellations, and when possible, the
reason, of regular bus and coach services
with a scheduled distance of 250 km or
more
S-4 Observed data on cancellations - for scheduled transport cancellations, and when possible, the reason, of flights
[page 41]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 41
S-2
Auxiliary information - for scheduled
transport and transport on demand
where relevant
basic common standard fares: fare
network data (fare zones/stops and fare
stages)
S-2
Auxiliary information - for scheduled
transport and transport on demand
where relevant
basic common standard fares: standard
fare structures (point to point including
daily and weekly fares, zonal fares, flat
fares)
S-2
Auxiliary information - for scheduled
transport and transport on demand
where relevant
vehicle facilities, including classes of
carriage, on-board Wi-Fi, capacity and
access conditions for bicycles
S-3
Detailed common standard and
special fare query - for scheduled
transport and transport on demand
where relevant
passenger classes (classes of passenger
such as adult, child, senior, student,
military/veteran, passenger with
disability and passenger with reduced
mobility, and qualifying conditions, and
classes of travel)
S-3
Detailed common standard and
special fare query - for scheduled
transport and transport on demand
where relevant
common fare products (access rights
such as zone/point-to-point including
daily and weekly tickets/single/return,
eligibility of access, basic usage
conditions such as validity
period/operator/time of
travel/interchanging, standard point-topoint fares prices for different point-topoint pairs including daily and weekly
fares/zonal fare prices/flat fare prices)
S-3
Detailed common standard and
special fare query - for scheduled
transport and transport on demand
where relevant
special fare products (offers with
additional special conditions such as
promotional fares, group fares, season
passes, aggregated products combining
different products, and add-on products
such as parking and travel, minimum
stay)
S-3
Detailed common standard and
special fare query - for scheduled
transport and transport on demand
where relevant
basic commercial conditions such as
refunding, replacing, exchanging or
transferring
S-3
Detailed common standard and
special fare query - for scheduled
transport and transport on demand
where relevant
basic booking conditions such as
purchase windows, validity periods,
routing restrictions zonal sequence fares,
minimum stay
S-3
Information service - for transport on
demand
how to book demand-responsive
transport services, including retail
channels, fulfilment methods, payment
methods
S-3 Trip plans
detailed cycle network attributes
(surface quality, side-by-side cycling,
shared surface, on/off road, scenic route,
'walk only', turn or access restrictions,
e.g. against flow of traffic)
[page 42]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 42
S-3 Trip plans
parameters needed to calculate an
environmental factor such as greenhouse
gas emissions per vehicle type or
passenger mile or per distance walked
S-3 Trip plans
parameters needed to calculate fuel
consumption of conventional and
alternative fuels
S-4 Information on parking tariffs
D-2
Information service on parking tariffs -
for transport on demand and personal
transport
D-3
Occupancy information of the vehicle -
for scheduled transport and transport
on demand where relevant
[page 43]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 43
Appendix II
The Table below shows the data types considered in the EU EIP MMTIS Quality Package29, and which
are also in the scope of this QF (as presented in the §2.1).
Table 19 Data types considered in EIP report and also in the scope of this QF. “S” stands for “static” (S
= Point 1 of MMTIS DR ANNEX), “D” stands for “dynamic” ((D = Point 2 of MMTIS DR ANNEX)
Data category -
Level of Service
Data types considered in EIP report Description of data type
S-1 Trip plan computation - for scheduled
transport and transport on demand
where relevant
connection where interchanges may
be made
S-1 Trip plan computation - for scheduled
transport and transport on demand
where relevant
network topology and routes/lines
(topology)
S-1 Trip plan computation Road network
S-1 Trip plan computation Cycle network
S-2 Location search - for transport on
demand and personal transport
Park & Ride stops
S-2 Location search - for transport on
demand and personal transport
Park & Drive stops
S-2 Location search - for transport on
demand and personal transport
bike-sharing stations
S-2 Location search - for transport on
demand and personal transport
car-sharing stations
S-1 Trip plan computation - for scheduled
transport and transport on demand
where relevant
timetables
D-1 Passing times, trip plans and auxiliary
information
disruptions, such as network
closures and/or diversions, and
when possible, the reasons
D-1 Passing times, trip plans and auxiliary
information
real-time status information, such as
estimated departure and arrival
times of services, delays,
cancellations, guaranteed
connections monitoring
29https://www.its-platform.eu/wp-content/uploads/ITS-
Platform/AchievementsDocuments/Quality%20Frameworks/EU%20EIP_SA41_MMTIS%20quality%20packagedefinitions_v2.0_191031.pdf
[page 44]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 44
Appendix III
The following tables present the criteria that were assessed as very complicated to be considere d in
this QF.
Table 20: Evaluation of EIP Quality Framework – Criteria that are assessed as very complicated to be
implemented (numbering follows from EIP document).
Number Quality
Criteria for
MMTIS based
on EIP
document
Description of EIP
criteria
Assessment from NAPCORE Quality framework
task force
2.8 Accuracy Error rate: Percentage
of the values for a
service which are
different from the
ground truth.
Very complicated because it requires manual
control and it's quite impossible to figure out
global statistics. Scrapping information from
websites and comparing it with information
released by datasets could be a solution but very
technical.
It is not easy to calculate totals . What if
organizations are using different sets of stops and
interchange link data? Times between links and
interchanges are in most cases calculated in
route planners thus results var y in
link/interchange times.
2.9 Accuracy Event coverage:
Percentage of the
occurring events which
are known to be
correctly detected and
published by type, time
and location (i.e.
Detection Rate).
Very complicated to do. Only the users' feedback
could give an estimation.
2.10 Accuracy Report coverage: The
percentage of reporting
locations for which a
status report is
received in any given
reporting period –
replacing “event
coverage” for status
reporting.
Very complicated to do. Only the users' feedback
could give an estimation.
Table 21: Evaluation of EIP Quality Framework – Criteria that are assessed as not relevant to be
implemented (numbering follows from EIP document).
Number Quality Criteria
for MMTIS based
on EIP document
Description of EIP criteria Assessment from
NAPCORE Quality
framework task force
[page 45]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 45
2.5 timeliness Latency (content side): The time between the
acceptance of the event and the moment the
information is provided by the content access
point.
Not relevant.
2.6 timeliness Latency (content side): The time between the
calculation of the reporting data and the
moment the information is provided by the
content access point – redefinition of
“Latency (content side)” for status reporting.
Not relevant
[page 46]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 46
Appendix IV
Poll results in detail.
Table 22. Answers to question “Do you have a national data quality framework for Multimodal Travel
Information Services to check the data in your National Access Point?
Answer Votes Countries
Yes, and it is implemented 2 Austria, Finland
No, but it is planned 6
Estonia, Latvia, Malta,
Romania, Slovenia,
Switzerland
No, neither implemented nor
planned 11
Belgium, Cyprus, Cyprus,
Czechia, Greece, Hungary,
The Netherlands
Other: I am not aware of the
existence of a quality framework
for MMTIS data
1 Portugal
Other: Not that I know of.
Certainly not national, maybe
regional
1 Belgium
Other: There are some works done
by DELFI, an Organisation of
German PT operators that share
data for MMTIS. Only some of the
data are published on our NAP.
Also, the DELFI quality works are
rather meant for Organisation -
internal QMS. Thus, this is not
really a “national QF”.
1 Germany
Table 23. Answers to question “Are you aware of the Framework for the quality of European
services for Multimodal Travel Information (EU EIP)”?
Answer Votes Countries
Yes, and it is relevant to the
national MMTIS quality
framework
12
Austria, Belgium, Cyprus,
Greece, Latvia, Romania,
Slovenia, Switzerland, The
Netherlands
Yes, but it is not relevant to the
national MMTIS quality
framework
3 Finland, Germany
No 6 Czechia, Estonia, Hungary, Malta, Portugal
Other: I am not aware of the
details of EU EIP framework for
MMTIS
1 Cyprus
[page 47]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 47
Appendix V
Detailed input from NAPCORE MMTIS Data dictionary. The tables present the data types where quality
dimensions such as completeness, uniqueness, timeliness and others are mentioned in the MMTIS
Data Dictionary and are considered for the QF.
Table 24 Extract of MMTIS Data dictionary (NAPCORE, 2024) with focus on the data types where
quality dimensions are mentioned.
Data type Location search (origin/destination) – addresses (building
number, street name, postcode):
Quality dimension Completeness
Obligatory elements The following data needs to be provided for an address:
• Identifier (must be globally unique)
• Name
• Coordinates (Centroid)
• Topographic or address identifiers
• Category of classification
Optional elements The following data is optional for an address:
• External identifiers (e.g., for OpenStreetMap (KeyList)
• Additional coordinates (access)
• Area
• Validity
Best practices: Addresses that appear in this data type are mostly relevant to
the postal address.
It should be made clear if the reference for origin and
destination is the physical location of the departure or arrival of
the customer’s trip (e.g. from home and to a shopping mall), or
the public transport point of origin and destination.
Quality dimension Compliance
The reference for postal address format is INSPIRE.
The reference for road address is NeTEx.
Data category Location search (origin/destination) – topographic places (city,
town, village, suburb, administrative unit):
Quality dimension Completeness
Obligatory elements The following data needs to be provided for topographic places:
• Identifier (must be globally unique)
• Name
• Coordinates (Centroid)
• Topographic or address identifiers
• Category or classification
Optional elements The following data is optional for an address:
• External identifiers (e.g., for OSM) (KeyList)
• Area
• Validity
Quality dimension Compliance
Transmodel/NeTEx
[page 48]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 48
Data category Location search (origin/destination) – points of interest
(related to transport information) to which people may wish to
travel:
Quality dimension Completeness
Obligatory elements • Identifier
• Name.
• Coordinates (Centroid): A version in WGS84 is
mandatory. A local projection can be added.
• Category or classifications
Recommended elements • External references (e.g., for OSM or a national
GeoBase): This helps in using the POI in the diverse
world we have.
• Source: A reference to the source of the data.
• Topographic or address identifiers : If such IDs exist,
they should be provided.
• Access and egress points to the road network (doors and
gates) – with coordinates: For bigger structures they are
needed.
Optional elements • Area: Some POIs are big, and the area covered is of
importance.
• Validity: If a POI is valid only for a given period. This data
can be provided.
• Opening hours.
Quality dimension Timeliness
The data must be actualized at least once a year. In the ideal case
any update to a POI (content, existence, coordinates) should be
available on the following day.
Quality dimension Uniqueness
The identifier must be globally unique. The identifier that is used
afterwards in all other data.
Quality dimension Compliance
The data must follow NeTEx Part 4 (EN 12896 -4, European
Passenger Information Profile, EPIP) in the structure for the data
export.
An export as Open Journey Planner (OJP) Location Information
is also possible (TS17118, version 2).
There can be multiple classification systems used. It is
recommended that at least the OSM map feature classification
is supported.
INSPIRE can be considered as reference standard only for a
limited set of POIs categories (Utilities and Governmental
Services (US), Buildings (BU), and Protected Sites (PS)), each of
which has its own specific data model.
Data category Location search (access nodes) – for scheduled transport and
transport on demand where relevant: identified access nodes:
Quality dimension Completeness
Obligatory elements • Coordinates
[page 49]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 49
Data category Trip plan computation – for scheduled transport and transport
on demand where relevant: connection where interchanges
may be made:
Quality dimension Completeness
Obligatory elements A passenger transfer shall be time - and distance-feasible to be
considered valid. In this respect, the attributes of connection
links encompassed by this data category should at least include
the distance and time duration of each connection link, also
allowing for alternative durations for different types of impaired
mobility. Moreover, connection links should be mode -specific
including at least (and as applies) walking and cycling modes.
Data category Trip plan computation – for scheduled transport and transport
on demand where relevant: transport operators
Quality dimension Completeness
Data category Trip plan computation – for scheduled transport and transport
on demand where relevant: timetables:
Quality dimension Completeness
Obligatory elements passing time information encompasses expected departure
times, expected waiting times, and in some cases (partially on
demand) earliest departure times, and latest arrival times.
Quality dimension Coverage
The timetable datasets should be as complete as possible for a
given country or region. The degree of coverage/completeness
should be declared per geographical region (e.g. country) in
terms of percentages/fractions (e.g. “100 % of trains in country
A are cove red”) and a description which modes, operators are
missing.
Quality dimension Timeliness
The time horizon of the timetable is of importance.
The information must be known in advance.
Recommended prospective time horizon of timetables : 120
days.
For long distance trips: I nformation can be obtained up to 3
months in advance,
For local-operated services : I nformation can be obtained 1
months in advance.
Timetable datasets (ZIP archives) should be generated on a
regular periodic basis, at least weekly.
Quality dimension Uniqueness
The ID has to match the ID in the real-time data.
The interchanges in the real -time data should match the
interchanges in the timetable data.
Quality dimension Compliance
[page 50]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 50
For scheduled transport timetables must be provided in NeTEx
format (part 1 and 2).
To allow for European interoperability, they must adhere to the
European Passenger Information Profile (EPIP; part 4) and/or to
the European Passenger Information Accessibility Profile (EPIAP;
part 6, under definition).
For transport on demand , offers must be provided in NeTEx
format (part 1+2).
For vehicle pooling , offers must be provided in NeTEx format
(part 5).
Compliance in respect with the datasets organisation
(partitioning) of files based on the recommendations below:
As the redundancy can’t always be avoided, importers must be
able to identify identical copies (e.g. replicated stop place
information when dealing with a line-oriented approach):
• One file (network approach)
• Complete lines
• Complete operators (and sometimes regions, but this might
cause integration problems)
• Complete groups based on modes or mode groups
• Site frame and lines without site in separate files
• Files per (NeTEx) frame and multiple timetable frames.
• Datasets should be published in compressed form (ZIP
archives).
• Cross-border services (e.g. international trains) may be
included in datasets end -to-end but using whenever
possible internationally harmonized/aligned identifiers.
• The data is aggregated.
In addition to NeTEx (EPIP and/or EPIAP profiles), GTFS versions
of the timetables may be provided as well. IDs in GTFS are equal
to IDs in NeTEx, so data consumers can use the data best suited
to the purpose of need.
Data category Trip plan computation – for scheduled transport and transport
on demand where relevant: planned interchanges between
guaranteed scheduled services:
Quality dimension Completeness
Obligatory elements • What is “guaranteed” must be clarified, and by whom.
The interchange time provided in the booking phase by
the trip planner is the responsibility of the trip planner30,
but the customer should know who is responsible for
what in case of missed interchange, and it should be
specified if the minimum interchange time is accepted
30 As for the SERA Rail systems the TSI Telematics under approval defines in its Articles 14, 15
and 16 a "Lead Railway Undertaking" and a "Station Manager" who have responsibilities in
connection times settings.
[page 51]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 51
by the operator(s) providing services before and after
the interchange.
Data category Trip plan computation – for scheduled transport and transport
on demand where relevant: hours of operation:
Quality dimension Completeness
Obligatory elements • Each scheduled journey has a precise date and time of
operation.
• Hours of operations may refer to:
o The time of starting services and time of closing
services (e.g. for local public transport which
may propose timetables, but also only
headways per period of the day).
o They may refer to DAY TYPEs for long distance
bus and rail services.
o They may refer to long periods in case of air
travel (low-cost airlines may operate only part
of the year).
• For on -demand transport it is necessary to provide
information on the time between ordering a trip and the
time of actual start of the trip, and the trip time
computation in itself is a two steps process.
Data category Trip plan computation – road network (including segregated
lanes for bus/taxi):
Quality dimension Completeness
Obligatory elements • Spatial dimension: Geometric (point, line, and area
(topographic)) representation of various elements that
are parts of a road network. Typically, the road network
is handled as a network of connected linear elements
(links) with points (nodes) at the ends of the lines (at
junctions, road ends, etc.). Real objects with a function
in a network may also be represented in a dataset.
Network connectivity within the roads network is
essential but between elements in the other networks is
an optional spatial aspect.
• Temporal dimension: All elements in a network may
have a temporal validity (i.e., description of when a
network element exists or is available in the real world).
Optional meta-information on when information about
a network element was entered, modified, or deleted
may also be included in a dataset.
• Thematic dimension: The road schema can be
thematically displayed via several of the attributes
defined within the specification.
[page 52]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 52
Quality dimension Compliance
The primary dimensions modelled for road network elements
include (INSPIRE – reference).
Data category Location search – for transport on demand and personal
transport: secure bike parking (such as locked bike garage):
Quality dimension Completeness
Obligatory elements The location of the (e -)bike/e-scooter is not sufficient: the
conditions of access and use are provided in other locations than
the cycle storage equipment.
Quality dimension Compliance
The primary dimensions modelled for road network elements
include (INSPIRE – reference).
Data category Auxiliary information – for scheduled transport and transport
on demand where relevant: vehicle facilities, including classes
of carriage, on-board Wi-Fi, capacity and access conditions for
bicycles:
Quality dimension Completeness
Obligatory elements The above -mentioned facilities/amenities may involve an
indication of whether a) on -board Wi -Fi, b) equipment
supporting bicycle or scooter boarding, c) monitors providing
vehicle tracking or declaring the next stop is/are available. They
may also involve information about the available classes of
carriage and the included facilities/amenities. For instance, in
rail transport services there are various types of wagons, such as
luxury class, first class, second class, third class, economy class.
Each of these classes offer different amenities/facilities ranging
from private compartments, including private beds, showers,
and toilets, to shared compartments, including their own backs,
lights, tables, and luggage spaces.
TYPES OF THE DYNAMIC TRAVEL AND TRAFFIC DATA
Quality dimension Completeness
Passing times, trip plans and
auxiliary information:
disruptions, such as network
closures and/or diversions, and
when possible, the reason:
Changes to the planned timetable and continuously keep track
of minor deviations, cancellations and other disruptions, prior
to- or during the service operation.
NeTEx can be used to exchange alterations to the planned
timetable including last-minute changes to the passing times.
Passing times, trip plans and
auxiliary information: real-time
status information, such as
estimated departure and arrival
times of services, delays,
This information may provide further details about delays,
cancellations, and guaranteed connections among different
modes (e.g., foreseen delay duration, cancellation timeframe). It
shall be dynamically updated as soon as it becomes available to
reflect the latest operational status of transport services.
[page 53]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 53
cancellations, guaranteed
connections monitoring: the
Availability check and location
– for transport on demand and
personal transport where
relevant: car-sharing
availability and location, bikesharing availability and
location, scooter-sharing
availability and location, and
other vehicle-sharing
availability and location:
The availability of a shared vehicles (car, bike, scooter) at a
specific location dedicated to vehicle sharing may be derived
from the capacity of a given area and the vehicle location
information at a specific time.
Availability check and location –
for transport on demand and
personal transport where
relevant: car parking spaces
available (on and off -street):
The
The minimum dynamic information about car parking spaces
available for on -street and off -street parking.
The dynamic availability of a parking includes accessible parking
places for wheelchair users (as they require more space for
accessing and leaving the vehicle).
Occupancy information of the
vehicle – for scheduled
transport and transport on
demand where relevant:
The minimum dynamic information about occupancy of the
vehicle.
[page 54]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 54
Appendix VI
National Approaches
France
France provides quality checks through a national body which is responsible to assess how MMTIS DR
is implemented in the country, the “Autorité de régulation des transports ” (ART). In France, it was
already mandatory to publish real time data in the National Access Point, before the amended version
of the DR 2024/490.
Regarding the different standards used in public transport, it is estimated that 15% of the datasets are
natively published in NeTEx. If a dataset is uploaded in GTFS, then it is converted to NeTEx in the
National Access Point. Static data is interrupted to upload if there is an error detected in the system.
Dynamic data is not stopped.
Table 25 Summary of Quality Framework approach in France
Criteria
Checks against GTFS/CEN standards formats
Checks against National profiles (include content wise validation rules, accuracy etc.)
Process
Datasets are uploaded to NAP by data producers (if dataset is GTFS, then it is converted to NeTEx).
Check the source datasets (GTFS) and compared with NeTEx equivalent dataset.
ART developed a built-in control framework according to importance of errors.
Validation tools
For GTFS, many tools to check different parameters (GTFSvtor, Transitfeed, MobilityData and PAN) do
not control the accessibility and freshness of metadata (but good to control consistency of data).
NAP has 2 validators in place for Transmodel datasets:
• Greenlight validator tool (DATA4PT)
• Data validator developed internally at ART (to be shared in the future)
Other supportive tools to facilitate validation
Documentation on standards and national profile is available for producers.
Automated convertors provided by National Access Point for GTFS to NeTEx.
Table 26 Types of error and their description in the French data quality framework
Error type Description
Level 0: Data provision
assessment
[page 55]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 55
Level 1: Fatal error • Accessibility
• Readability
• Up to date
• Normality
Level 2: Quality data
assessment
• Completeness
• Relevance
• Consistency
Level 3: Dataset
quality certification
• Exhaustiveness
• Accuracy
Norway
In Norway, the quality checks are performed by ENTUR, which is the Norwegian NAP operator. The
assessment encompasses checks against the CEN standards and the Nordic NeTEx profile. When a
NeTEx dataset is uploaded to the NAP it is validated. If there is an error in the validation process, it
stops the upload and the dataset has to be a mended. If a warning happens, then a message appears
to inform the involved stakeholder, but the dataset is uploaded to the NAP.
Regarding SIRI data, there is a slightly different validation process. The same principles than with NeTEx
are followed and the Quality checks are performed against the SIRI standards and the Nordic profile.
The main difference observed is that NeTEx error s stop the dataset upload, while in SIRI data is used
as-is at the moment.
Table 27 Summary of Quality Framework approach in Norway
Criteria
Checks against CEN standards formats
Checks against National profiles (include content wise validation rules, accuracy etc.)
Process
Validation happens directly on the NeTEx/SIRI files when are being uploaded.
Uploading stops when there is an error in static data (NeTEx).
Uploading continues for real-time data (SIRI).
Fixes are done by the NAP operator depending on the error. For major errors data are pushed back
to the provider.
Real-time data (SIRI) received at maximum every minute (usually between 10-30 seconds).
Validation tools
Available for both NeTEx and SIRI datasets.
Open source.
Other supportive tools to facilitate validation
National stop place registry: https://stoppested.entur.org/ (visualization tool). The National stop
registry enables to check and validate the accuracy of the stop places coordinates.
New modes visualization map (floating vehicles and docking stations) https://mobilitymap.entur.org/. Visualisation maps enable the validation of accuracy of location related data.
Scheduled modes vehicles visualization map (bus, ferry, metro, tram, coaches, rail, air)
https://vehicle-map.entur.org/. Visualisation maps enable the validation of accuracy of location
related data.
Onboard vehicle location systems are used to share real -time information of vehicle position. This
kind of tools refer to interoperability and data exchange in the data sources.
Switzerland
[page 56]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 56
For Swiss Operators, mobility does not start at the national border, and it is very important the
communication with the neighbour countries.
There are several standards considered in Switzerland. Often these are the CEN standards, but also
others generated from CEN (German standards) and industry standards like GBFS and GTFS. A national
profile is derived from each standard in a similar way as in the Nordic countries.
Regarding quality, they highlight the need to control the quality of the published datasets and to have
complete highly homogenised data sets. It is noted that sometimes, there are organisations in the
European context that publish data which is obviously not consumed by themselves as their NeTEx
datasets obviously never were validated.
A way to fix things, as explained in the presentation, is to put “top-to-down” pressure. For example,
for GTFS datasets, the shapes that show the exact route should be provided. However, it might be a
first step that the NAP operator builds estimated shapes from the sequence of stops and later uses
them to validate real shapes provided by the operators. When in Switzerland check tools are
developed, then they are made open source.
Table 28 Summary of Quality Framework approach in Switzerland
Criteria
Check against profiles – create national profiles mostly done. Check software created or used.
Adopt customer perspective “what the customer needs to get” – currently data providers do not
consume the provided data and quality is not checked at all. Also, the NAP must take responsibility.
Compare Disruptions and real-time to timetables and to base information.
Completeness of the route (included stops), which can be assessed with visual inspection.
Process
Fix things upstream. Sometimes it also creates some downstream pressure to achieve it.
Apply tests to datasets.
Consumption of the received datasets (to check correctness).
Issues – errors management.
Validation tools
XML check (xmllint), Splunk, QS for operators.
Mobility data GTFS validator.
Open source to check inconsistencies in timetables and others. They are not yet developed but the
approach is to use existing ones from other countries.
Other supportive tools to facilitate validation
OJP Demo (opentdatach.github.io) Visualisation of the OJP engine. This kind of tool can be used to
consume the received datasets and therefore identify inconsistencies in location related data and
conformity errors.
Situation map: https://github.com/openTdataCH/siri-sx-map.
Converters from different NeTEx forms almost done.
GTFS visualisation of network (leaflet).
Austria
Austria has a centralized data collection and provision service for public transport data. There are nine
federal states in Austria with seven data systems for public transport. All are connected in one
centralized system providing one user interface to end users (https://anachb.vor.at/). Moreover, there
are also private and regional train transport data operators that provide data to the centralized system
from Austria.
[page 57]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 57
The side systems that provide information to the centralized system are:
• Network platform for spatial data and referencing system.
• Export interfaces for the end users.
The steps followed in the quality check are the following ones. The first quality check is done during
the data collection and maintenance. The second quality check happens during the data processing.
The third and final quality check is done during the data supply and data provision. Depending on the
stage, different quality dimensions and criteria are considered. For example : during Stage 1: data
collection, focus is given on s oftware quality checks (i.e. format), user feedback; during Stage 2: data
process, checks on content (logical), connection queries (samples), data processability and others are
introduced; while at the Stage 3: Data supply and provision, s chema validation, completeness and
content wise checks, user feedback are repeated.
Table 29 Summary of Quality Framework approach in Austria
Criteria
Software quality checks (i.e. format), Sample checks on content, User feedback.
Software quality checks (integrity, consistency, plausibility, availability, completeness of stops,
sections, lines, etc.).
Checks on content (logical), Connection queries (samples), Data processability, Automated log
monitoring (process).
Reference queries (samples).
Schema validation, Availability / accessibility, Plausibility / completeness, User feedback.
Service use statistics.
Process
Quality assurance checks in 3 stages:
Stage 1: At harvesting data from Provider
Stage 2: At processing Data
Stage 3: Quality Routines
Differentiation between critical errors/ errors/ warnings.
Validation tools
At stage 1: Different Validators such as Stop Validator, Route Validator, Calendar / Timetable
At stage 2: Raw data Validator, Transformation Validator, System validator
At stage 3: Greenlight (DATA4PT) NeTEx validator , manual checks.
Other supportive tools to facilitate validation
-
There are different types of errors that can appear during the data quality process of the Austrian NAP.
If a critical error is detected, it stops the harvesting of the complete data set. For normal errors and
warnings do not stop the data set harvesting. Some examples of the different types of errors appear
in the following table:
Table 30 Types of error and their description in the Austrian data quality framework
Error type Description
Critical error Global-ID is not unique
Air distance between points is bigger than 50 km
Error No coordinates
Air distance between points is bigger than 1 km
Numeration of stops not consistent
[page 58]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 58
Stop has no traffic mode
Stop has no place name
Stop is not reachable by foot
Warnings Distance between stops is very small
More operators for one line
Connection point of a stop has a high distance
No Tariff zone named
Global ID not found
Speed reference is not realistic
Finland
Finland implemented national mobility data validation service as a modular solution for MMTIS
national access point (finap.fi). Validation module checks all listed services, watermarks the quality of
the data in NAPs data catalogue and if necessary, initiates data correction process with the original
publisher/provider of the feed. Validation module called “Vaco” integrates valid data sets to the
national mobility data database which is the master source for all mobility data information in Finland.
If data is not valid, data is not integrated into a database. Finnish current and still developing quality
process includes:
• National feed validator Vaco checks all compatible mobility data sources listed in MMTIS
National Access Point. Currently Vaco supports NeTEx and GTFS standards. In 2024 standard
support will include also GBFS, SIRI and GTFS RT data sources.
• Vaco is an independent validator and conversion rule module and service which current form
incorporates NeTEx validation rules from Entur and GTFS validation rules directly from
Mobilitydata.org.
• Vaco UI and generated validation report gives detailed access for each individual feeds
provided by mobility service providers. Validation report generated from all data sources (valid
or not).
Currently only one mobility service provider in Finland publishes data natively on NeTEx. All other data
requires GTFS to NeTEx conversion, which is provided the MMTIS NAP process. In real-time data SIRI’s
coverage of all available sources is approximately 10-15 %.
In terms of process, if published datasets are recognized as GTFS and/or NeTEx files, there are checked
against the relevant standards. In the case that discrepancies are found (e.g. missing mandatory files,
the files are empty, files did not include the s tandard) data is given either a status of warning and/or
error. If data receives an error status, MMTIS NAP starts the automated correction process with the
feed publisher organization.
Table 31 Summary of Quality Framework approach in Finland
Criteria
FINAP: Syntax validation.
Public transport database: Syntax and logical validation.
Process
When data is published (GTFS/NeTEx) Finap.fi makes validation cycle.
Validation cycle is done for all data when changes are recognized.
If discrepancies are detected, then the service will notify the publisher about all the findings that
were made on the data. Notifications will cycle every single day until data has been corrected.
[page 59]
A Quality Framework for Multimodal Travel Information Services (MMTIS)
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 59
Fintraffic uses Finap.fi data through national public transport database, which also make syntax and
logical validation modules.
OTP validation on top of all validation rounds before that.
Validation tools
Development of Vaco (National mobility data feed validator).
Other supportive tools to facilitate validation
-
