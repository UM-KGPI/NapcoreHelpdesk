url: https://napcore.eu/wp-content/uploads/2025/06/NAPCORE-M3.8-deliverable_v1.1_250408.pdf
title: NAPCORE M3.8 deliverable v1.1 250408

[page 1]
A set of Quality Frameworks for the
assessment of NAP (meta)data quality
Report by Task 3.2: European NAPs data quality
Status: final
Version: 1.0
Date: 17 March 2025
Legal disclaimer
The sole responsibility for the content of this document lies with the authors. It does not necessarily
reflect the opinion of the European Union. The European Commission is not responsible for any use
that may be made of the information contained therein. All imag es are provided by the respective
partners (unless otherwise noted) and are approved for reproduction in this publication.
[page 2]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 2
Document information
Project acronym NAPCORE
Full project title National Access Point Coordination Organisation for Europe
Grant Agreement No. MOVE/B4/SUB/2020-123/SI2.852232
Activity no. and title WG 3 NAP content and accessibility
Author(s) Peter Lubrich, BASt
Co-author(s) Cristina Buraga, CEREMA
Petr Bureš, TTR
Anastasia Founta,ITxPT
Fruzsina Homolka, FEDRO
Marlous Hovestad, NDW
Chrysostomos Mylonas, CERTH
Mircea Steriu, UITP
Anna Schirokoff, TRAFICOM
Rodolfo Da Silva, KIOS CoE – University of Cyprus
Mihai Niculescu, ITS Romania
Related to Milestone no. M3.8
External Milestone yes
Document history
Version Date created/ modified by Comments
0.1 06.04.2022 Peter Lubrich, BASt First draft
0.2 27.04.2022 Cristina Buraga, CEREMA
Petr Bures, TTR
Anastasia Founta,ITxPT
Fruzsina Homolka, FEDRO
Various text additions/corrections
0.3 12.05.2022 Marlous Hovestad, NDW
Chrysostomos Mylonas,
CERTH
Mircea Steriu, UITP
Anna Schirokoff, TRAFICOM
Mihai Niculescu, ITS Romania
Petr Bureš (CZ/TTR)
Various text additions/corrections,
update o f horizontal quality framework
description and InQMS project
information.
0.4-0.6 17.10.2024 Peter Lubrich, BASt Report newly framed as M3.8 document,
various editorial and contextual
improvements
0.7 1.12.2024 Petr Bureš (CZ/TTR) Various textual improvements to the CDQ
and related texts, and introduction
1.0 17.03.2025 Peter Lubrich, BASt Finalisation
1.1 08.04.25 CAT CAT Review
Action requested
☐ To be revised by partners involved in the preparation of the document
☐ For review/ approval by the Core Alignment Team
☐ For approval by the NAPCORE Steering Committee
[page 3]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 3
Abstract
This deliverable by NAPCORE WG3 compiles the concept and approaches to establish the co-called
Quality Frameworks for NAP (meta)data quality and summarizes the main outcomes.
Abbreviations
Abbreviation Meaning
CDQ Cross-Domain Quality
EC European Commission
FCD Floating Car Data
ITPS Intelligent Truck Parking Services
ITS Intelligent Transport Systems
MMTIS Multimodal Travel Information Services
NAP National Access Point
NAPCORE National Access Point Coordination Organisation for Europe
QF Quality Framework
RTTI Real-Time Traffic Information Services
SRTI Safety-Related Information Services
UVAR Urban Vehicle Access Regulation
WG Working Group
[page 4]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 4
Table of contents
1. Introduction................................ ................................ ................................ .......................... 6
1. The concept of Quality Frameworks................................ ................................ ....................... 7
1.1 Why do we need Quality Frameworks in the context of ITS? ................................................ 7
1.2 What is a Quality Framework for NAP (meta)data? ............................................................... 8
1.3 Previous Quality Frameworks ............................................................................................... 11
EU EIP Quality Packages ................................................................................................................. 11
InQMS ............................................................................................................................................. 12
Data and information quality in international literature ............................................................... 13
2. Roadmap to Quality Frameworks by NAPCORE ................................ ................................ .... 14
2.1 Legacy of Quality Packages by EU EIP ................................................................................... 14
2.2 Evolution of legal frameworks .............................................................................................. 15
2.3 WG 3 Quality workshop on March 16th 2022 ...................................................................... 17
2.4 Three dimensions of quality ................................................................................................. 17
Dimension 1: Data Domain ............................................................................................................ 18
Dimension 2: Value Chain of Traffic Information........................................................................... 18
Dimension 3: “Objects being evaluated” ....................................................................................... 19
2.5 First prioritization by EU EIP and NAPCORE mini-surveys .................................................... 19
3. Proposal for new Quality Frameworks by NAPCORE ................................ ............................. 23
3.1 Overview and methodology ................................................................................................. 23
3.2 A Quality Framework for On-Street Parking Data ................................................................ 25
3.3 A Quality Framework for UVAR Data .................................................................................... 26
3.4 A Quality Framework for Alternative Fuels Data .................................................................. 27
3.5 A (renewed) Quality Framework for MMTIS data ................................................................ 28
3.6 A Quality Framework for Floating Car Data.......................................................................... 29
3.7 A Quality Framework for Network Topology Information ................................................... 31
3.8 A Cross-Domain Quality (CDQ) methodology for assessing data and services .................... 32
3.9 Publication of Quality Frameworks: the Quality Online Repository .................................... 34
4. Next steps................................ ................................ ................................ ........................... 35
Annex A: Details about former EU EIP Quality Frameworks ................................ ......................... 36
Quality of Safety-Related and Real-Time Traffic Information Services (SRTI and RTTI) ................ 36
Quality of Multimodal Travel Information Services (MMTIS) ........................................................ 36
Quality of Intelligent Truck Parking Services (ITPS) ....................................................................... 38
C-ITS Information Quality ............................................................................................................... 38
General reflection on the EU EIP Quality Packages ....................................................................... 39
[page 5]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 5
Annex B: Details about the InQMS framework ................................ ................................ ............ 40
Real world (Content) quality parameters ...................................................................................... 40
Formal quality parameters ............................................................................................................. 40
Technical quality parameters ......................................................................................................... 40
Annex C: Documentation of NAPCORE Quality workshop on March 16th 2022 ............................. 42
List of figures
Figure 1: Example for inconsistent localisation of road work information in different information portals
(Map: ©OpenStreetMap contributors) .................................................................................................. 10
Figure 2: Tabular structure for describing Quality Criteria and Quality Requirements ......................... 10
Figure 3: Formal, Technical and Content evaluation procedures used by InQMS project ..................... 13
Figure 4: “Balancing problem” about EU-wide Quality Frameworks (icon created by Freepik - Flaticon)
................................................................................................................................................................ 14
Figure 5: Evolving from EU EIP Quality Packages to NAPCORE Quality Frameworks ............................ 15
Figure 6: Data categories from Annex of EC Delegated Regulation 2022/670 ...................................... 16
Figure 7: Three dimensions of quality .................................................................................................... 18
Figure 8: TISA Value Chain of Traffic Information .................................................................................. 19
Figure 9: WG 3 Quality workshop Slido mini-survey - Prioritization for Dimension 1: Data Domain .... 20
Figure 10: WG 3 Quality workshop Slido mini -survey - Prioritization by Dimension 2: Value Chain of
Traffic Information ................................................................................................................................. 20
Figure 11: WG 3 Quality workshop Slido mini -survey - Prioritization by Dimension 3: “Objects being
evaluated” .............................................................................................................................................. 20
Figure 12: Results from WG 3-interla mini-questionnaire about prioritised data domains .................. 21
Figure 13: EU EIP questionnaire, question “What is the relevance of the following, potential new quality
topics for your work / your organisation?” ............................................................................................ 22
Figure 14: EU EIP questionnaire, question “For which quality processes do you wish further European
guidance and harmonization?” .............................................................................................................. 22
Figure 15: Basic methodology for the development of the NAPCORE Quality Frameworks.................. 24
Figure 16: Data sources used for data campaign (© Smartparking; INRIX, Inc.; Landesbetrieb
Geoinformation und Vermessung Hamburg; Peter Lubrich) .................................................................. 26
Figure 17: Methodology for the Quality Framework for Floating Car Data .......................................... 31
Figure 18 Number of evaluated catalogue records by the CDQ methodology and resulting grades.... 33
Figure 19: The “Quality Iceberg” in the context of MMTIS Quality (based on VDV, Association of German
Transport Companies) ............................................................................................................................ 37
Figure 20: Example of the metrics processed in the inQMS with respect to delivery and structural
soundness of the data ............................................................................................................................ 41
Figure 20: Example how to attach quality descriptions to the data set offering in a NAP .................... 42
Figure 21: NDW Data Quality Dashboard .............................................................................................. 43
Figure 22: Example for an assessment of formal for a data set ............................................................ 44
Figure 23: Concept of absolute quality (sub-) levels .............................................................................. 44
[page 6]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 6
1. Introduction
Task 3.2 of the NAPCORE project addresses the fourth objective of NAPCORE WG3 as outlined in the
Grant Agreement: “Set a robust framework for and bring into practice the evaluation of European NAP
platforms’ data quality.” This objective is achieved through a se ries of activities aimed at : a)
establishing data quality assessment frameworks, and b) clarify ing the practical application of these
frameworks. These activities are carried out through several work items.
One of these work items is the “Development of Quality Frameworks”. This involves creating generic
Quality Frameworks for various ITS domains, which include agreements and definitions for quality
criteria and (minimum) requirements. These criteria and requirements cover different quality aspects
such as geographic coverage, timeliness, positional accuracy, and error levels. These frameworks build
upon previous quality elaborations, such as those from the EU EIP platform , but expand on these in
terms of concreteness and maturity. Additionally, new frameworks are being established for metadata
and for emerging data categories, such as UVAR.
The process begins with reviewing current achievements in the data quality field and identifying
existing gaps . Initial preparations include the scoping of Quality Frameworks to be established and
identifying and analysing the relevant needs of all actors involved in the ITS value chain, such as public
and private data providers and relevant associations.
The final deliverable from this work item is a set of Quality Frameworks for different data domains and
use cases.
This report compiles the concept s and approaches for establishing these Quality Frameworks and
summarizes the main outcomes.
The specific deliverables and artifacts related to the developed Quality Frameworks are provided in a
“Quality Online Repository” (see section 3.9).
[page 7]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 7
1. The concept of Quality Frameworks
1.1 Why do we need Quality Frameworks in the context of ITS?
The concept of quality has long been essential in the domain of conventional products and services,
where customers have certain quality expectations before purchasing, and manufacturers or service
providers strive to meet these expectations, especially in a competitive environment.
Similarly, the efficiency and acceptance of Intelligent Transport Systems (ITS) services heavily depend
on meeting (minimum) quality expectations from the end-user's perspective, namely the traveller.
These services, in return, rely on accurate and up-to-date data and information, often sourced from
various data providers. Therefore, it is a clear correlation between the quality of an ITS service and the
quality of the underlying data.
Data quality can vary depending on the field of application and time context. Researchers and experts
have different interpretations of data quality . According to Alizamini et al. , data quality is defined as
being appropriate for use or to meet ing user needs1. Another definition is “fitness for use”, implying
that data quality is relative; data quality suitable for one use may be inadequate for another. ISO 25012
defines Data Quality as “the capacity of data to satisfy stated and implied needs when used under
specified conditions”2.
In the ITS data value chain , data quality depends on various actors, from traffic managers and
information providers to end users. From the users’ perspective, the perceived quality depend s not
only on the data content but also on data visibility, description, legal and technical data access, and
conformity to declared structures. Moreover, data quality is context -dependent, often extending
beyond ITS and mobility frameworks.
In theory, data suppliers should monitor data quality, report quality levels and continuously improve
data provision. However, in practice, ITS end-user service providers, who reuse such data, often face
challenges in assessing and aligning data quality, due to undocumented and unharmonised quality
levels.
To address this, the European Commission's ( EC) legal framework s, such as the EC Delegated
Regulations, mandate not only the provision of ITS data, but also the assessment and documentation
of data quality levels across various ITS domains.
For Instance, the revised EC Delegated Regulation 2022/670 for EU-wide real-time traffic information
(RTTI) services3, explicitly requires common definitions of quality , as stated in Section (21) of the
preamble:
“Member States and ITS stakeholders should be encouraged to cooperate to agree on common
definitions of dat a quality with a view to use common data quality indicators throughout the traffic
data value chain, such as the completeness, accuracy and up -to-dateness of the data, the acquisition
method and location referencing method used, as well as quality checks app lied. They should also be
1 F. G. Alizamini, M. M. Pedram, M. Alishahi, and K. Badie, “Data quality improvement using fuzzy
association rules,” in International Conference on Electronics and Information Engineering, 2010, pp.
468–472.
2 International Organization for Standardization, “ISO/IEC 25012:2008, Software engineering –
Software product Quality Requirements and Evaluation (SQuaRE) – Data quality model,” 2008.
Accessed: Jul. 11, 2024. [Online]. Available: https://www.iso.org/standard/35736.html
3 https://eur-lex.europa.eu/eli/reg_del/2022/670/oj
[page 8]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 8
encouraged to work further to establish associated methods of quality measurement and monitoring
of the different data types. Member States should be encouraged to share with each other their
knowledge, experience and best practices in this field in the on-going and future coordination projects”
This stipulation can be seen as a directive for the NAPCORE Quality activity and should be closely
considered. Additionally, quality aspects are mentioned in the Articles that explain data provisioning
and exchange via National Access Points ( NAPs), such as in “Article 4 Accessibility, exchange and re -
use of data on infrastructure”:
“…The data referred to in paragraph 1 and the corresponding metadata including information on the
quality thereof shall be accessible for exchange and re -use by any data user within the Union: …
following minimum quality requirements that Member States shall agree upon in cooperation with
relevant stakeholders…”
These stipulations assume a common understanding of data quality from the perspective of a specific
domain with particular requirements, or from the viewpoint of shared “horizontal” quality concepts.
This is important for the Europe -wide deployment of ITS services and the underlying data provision.
Common quality criteria and requirements, as well as quality assessment methods , are needed when
evaluating ITS data and ITS services against the specified quality criteria and requirements.
EU-funded projects, including the former EU EIP and the current NAPCORE project, aim to define and
agree on quality aspects among European ITS and data stakeholders. These projects focus on
harmonizing the handling of ITS data and information quality , particularly regarding (meta)data
provision on National Access Points (NAPs).
A dedicated quality action in NAPCORE WG3 aims to deepen and expand previous harmonisation
efforts in ITS data and service quality , raise stakeholder awareness about NAP (meta)data quality
aspects, and provide guidance and support in dealing with these aspects. The main output is a set of
Quality Frameworks, detailed in the rest of this report.
1.2 What is a Quality Framework for NAP (meta)data?
A Quality Framework (QF) is a set of definitions and an application guidance for actors dealing with
NAP (meta)data quality. Key elements include quality criteria (sometimes also called quality indicators,
metrics or parameters), quality levels that describe (minimum) requirements to be met for each quality
What to do with Quality of ITS Data?
Once you have established a quality monitoring for your ITS data and services,
maybe based on our Quality Frameworks, you have various oppurtunities how
to benefit:
- You might assess and document spesific quality criteria for internal purposes.
- You might do regular Quality Reports, which find way into, e.g.,
implementation status reports to the EC.
- You might also implement a formal Quality Management System (QMS) within
your organisation, establishing quality monitoring and quality improvement
actions.
[page 9]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 9
criterion by a specific NAP (meta)data service, and recommendations how to assess these criteria and
levels.
A QF is based on research and practical evidence, supported by discussions and a consensus among
various stakeholder s in the data value chain, including both data providers and data re -users. It
influences an organisation’s processes of quality monitoring, assessment, and management. The main
target groups are ITS service operators, data managers and data specialists at data -provider
organisations (e.g., traffic management centres), data users, IT / data specialists, and end-user service
providers, as well as NAP stakeholders dealing with such data.
However, this target group should be expanded to include wider stakeholder communities because
data quality often results from specific processes and structures within a corresponding domain. For
example, in the MMTIS domain, it is crucial to consider the structures of the passenger -transport
information systems. Therefore, stakeholder organisations representing specific domains, in the above
example via Data4PT or UITP, might also be considered as target group of certain QFs.
The focus of QF elaborations at NAPCORE is on ITS data and information exchanged via NAPs, primarily
dealing with data exchange under the Delegated Regulations of the ITS Directive.
NAPCORE aims to provide a set of QFs, each addressing different ITS/NAP (meta)data domains. Each
proposed QFs will include conceptual elaborations of the topics “Quality Criteria “, “Quality
Requirements” and “Quality Assessment Methods”, which are explained next.
Quality Criteria
Quality Criteria are basic parameters used to describe the quality of ITS services and related data. They
are usually categorised into Level of Service (describing the provision of data) and Level of Quality
(describing the data itself).
The data-related criteria are based on previous definitions, such as those from ISO standards4, but are
tailored and adapted to the scope of individual QFs. They relate to temporal and spatial dimensions
(e.g. “Latency”, “Location accuracy”), and the ground -truth correspondence of the data (e.g. “Error
rate”). More generally, they indicate whether and how information from a (virtual) ITS data provision
corresponds with the (physical) environment, identifying any gaps or mismatches between data and
reality.
The example , the Figure 2 shows the relevance of the quality criterion “Location accuracy” in the
context of road work information. The same road work event is represented in two different
information portals differently, with an inconsistent localisation, i.e., the road work has different start
and end points. The analysis of this particular case indicated that data generation and georeferencing
methods play a role here. A consequence of such case may be that a road traveller does not trust a
specific information portal due to inaccurate information. According to a former quality elaboration
by EU EIP (see section 2.1), such phenomenon should be detected and described under the dedicated
quality criterion “location accuracy” , and any quality issues should be addressed and monitored via
the mentioned quality criterion by the responsible actors.
4 ISO/TR 21707:2008, Intelligent transport systems -- Integrated transport information, management
and control -- Data quality in ITS systems
[page 10]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 10
Figure 1: Example for inconsistent localisation of road work information in different information portals
(Map: ©OpenStreetMap contributors)
Quality Requirements
Quality Requirements are understood as (minimum) quality levels that individual ITS services must
meet. According to former quality elaborations by EU EIP (see section 2.1), these requirements specify
the (minimum) level at which the Quality Criteria should be realised by an individual ITS service to meet
certain quality expectations. These quality expectations can be described in levels, such as the threelevel system introduced by EU-EIP:
* Basic level
** Enhanced level
*** Advanced level
Quality Requirements complement the Quality Criteria and are typically compiled in a tabular structure
as shown in Figure 2.
Figure 2: Tabular structure for describing Quality Criteria and Quality Requirements
[page 11]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 11
The Quality Requirements are expressed quantitative ly where possible. Depending on the domain
covered in a specific QF, the requirement values can be derived from evidence (e.g., possible ranges
of quality levels recorded in test settings), or formulated as stipulations (e.g., from (minimum) quality
expectations stated by relevant data consumers). These values cannot be assumed fixed and static,
they are expected to be continuously validated through discussions with relevant stakeholders and
proven in real-life conditions.
Quality Assessment Methods
These are potential methods for quality assurance and assessment. Each QF typically contains a set of
proposed methods, each applicable for different uses and for studying different quality criteria. Typical
methods include the monitoring of equipment performance and availability; reference testing (e.g.
against ground-truth data), and surveys of perceived quality by data users.
Altogether, e ach QF contains chapters on “Quality Criteria”, “Quality Requirements” and “Quality
Assessment Methods. These build upon each other , with “Quality Criteria” act ing as a baseline to
define quality dimensions, which are then quantified via “Quality Requirements”. These two aspects
are eventually put into a practical context via the “Assessment Methods”.
Concrete examples for such Quality Frameworks from the EU EIP project and other projects are
explained in the next sections.
5 6
1.3 Previous Quality Frameworks
EU EIP Quality Packages
A similar approach to defining quality of ITS data and information, as envisioned by NAPCORE, has
been followed by the former EU EIP project (2016-2021). EU EIP sub-activity 4.1 “Determining Quality
of European ITS Se rvices” elaborated a set of quality frameworks for several ITS data and service
5 Wang, R., Strong, D. M. (1996): Beyond Accuracy: What Data Quality Means to Data Consumers,
Journal of Management Information Systems, Vol. 12, No. 4, 1996
6 ISO (2008): ISO/TR 21707:2008 - Intelligent transport systems -- Integrated transport information,
management and control -- Data quality in ITS systems
Quality Frameworks: is it Theory or Practice?
If you ask if we need theoretical concepts or practice-based guidance for ITS
quality, the answer is clearly “both”!
Some previous elaborations did consider theoretical foundations, such as
academic approaches to capture relevant quality aspects from an individual
user perspective (independent of ITS)1, as well as standardisation efforts
proposing generic quality objects and parameters for ITS data exchange2.
However, as our goal is to embed the Quality Frameworks in every-day's
practice of stakeholders, all our definitions are elaborated (and sometimes
even tested) for real-life, practical environments.
[page 12]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 12
domains. These frameworks, called the Quality Packages, add quality aspects to parallel ITS
implementation and pilot projects across Europe.
Each Quality Package contains quality-related definitions and concepts, as proposed and agreed by EU
EIP partners for the use in Europe. The definitions and concepts are based on evidence from conditions
and operating environments in combination with the e xpert knowledge of the public and private
stakeholders involved in the EU EIP quality work.
The target group of the Quality Packages is mainly data managers and data specialists at road operator
organisations, as well as NAP stakeholders dealing with such data. This target group, however, had to
be expanded during the EU EIP project to reflect the perspectives outside the road domain, for example
in the multimodal context, as stated further below.
The scope of the quality definitions is restricted to ITS domains of traveller information, being a
subcategory of ITS in general. These ITS domains also correspond to the priority actions of the EC ITS
Directive, and the respective EC Delegated Regulations. The definitions in the Quality Packages further
relate to certain parts of the so-called Value Chain of Traffic Information. The definitions focus on the
content part of this value chain. The content part, which is typically in the responsibility of a d ata
supplier, covers processes between the detection of a real event or a traffic situation until the provision
of related information in a NAP. At a NAP, the traffic information is (typically) made available to many
service providers via e.g. a data porta l. The service provision, however, is out of scope of the EU EIP
work.
Besides the Quality Packages, some side tasks explored the quality roles and actions in the evolving ITS
ecosystem. One side task defined the relevant stakeholders, value chains, recommended work
processes, when dealing with ITS quality. Another side task “Optimum Quality” examined optimisation
aspects in terms of quality, from the perspective of European road authorities.
All deliverables from this EU EIP activity, including the individual Quality Packages and the
accompanying documents, can be found as an online repository on the EU EIP website7.
Further details and some reflection on the EU EIP Quality Packages can be also found in Annex A.
InQMS
In addition to quality frameworks that are (at least partially) domain or application focused, such as
those in EU EIP, there are also horizontal or cross-domain-oriented works on quality definitions in the
ITS/NAP sector. An important reference in this context is the InQMS project, which is explained next.
The quality framework developed within InQMS8 focuses on different perspectives through which the
quality of provided information could be perceived. Th is framework does not address real-world
quality parameters , such as defined in ISO and EU-EIP, but on the practical aspect s referred to as
“formal quality” and “technical quality”:
• Real world (content) quality parameters: These are standardized (ISO), tested and enhanced
by number of projects, including EU-EIP. These quality parameters are challenging to measure
because evaluators often need ground truth data for comparison.
• Formal quality parameters: These parameters do not relate to the real dynamic content of the
service but rather to how it is described and what metadata are provided.
7 https://www.its-platform.eu/achievement/quality-of-european-its-services-and-their-data/
8 https://inqms.cz
[page 13]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 13
• Technical quality parameters: These parameters focus on structural and distribution quality of
provided traffic information from the perspective of a delivery channel including the service
set up and production.
Further details on these three aspects (including a proposed timeline for their assessment) can be
found in Annex B.
It is important to note that these three aspects are evaluated differently, not per content domain (e.g.,
per EC Delegated Regulation), but rather per delivery channel (e.g. web, RDS-TMC). This is because the
formal, technical and content constraints of each channel are different and lead to varying quality
requirements. Additionally, InQMS promotes a variety of evaluation procedure s, each addressing
different aspects and delivery channels, as illustrated in Figure 3.
Figure 3: Formal, Technical and Content evaluation procedures used by InQMS project
Further details on the background and deployment of InQMS can be also found in two conference
papers 9 10.
Data and information quality in international literature
There is a rich availability of international literature about data and information quality in the domains
of academia, industry and standardisation . Some of the literature address es data in ITS or
transportation, some addresses related domains, such as spatial data, and some addresses generic
concepts, such as business information systems. We did an extensive review of relevant literature
when elaborating the individual NAPCORE QFs. Thus, relevant literature is listed in the individual QF
documentation.
9 Bures, Petr & Langr, Martin. (2018). Implementation of Traffic Service Quality Measures in Czechia:
18th International Conference on Transport System Telematics, TST 2018, Krakow, Poland, March 20-
23, 2018, Selected Papers. 10.1007/978-3-319-97955-7_2.
10 Bures, P. (2017). Approaches to Quality Assessment of Traffic Information Services. In: Mikulski, J.
(eds) Smart Solutions in Today’s Transport. TST 2017. Communications in Computer and Information
Science, vol 715. Springer, Cham. https://doi.org/10.1007/978-3-319-66251-0_7
[page 14]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 14
2. Roadmap to Quality Frameworks by NAPCORE
2.1 Legacy of Quality Packages by EU EIP
The lesson-learnt from the Quality Packages by EU EIP (see section 1.3) is that quality is crucial for any
ITS stakeholder and use case, but has to be carefully interpreted depending on the context. Thus,
different quality aspects apply for the different data domains. Also, the underlying data sources, use
cases and end -user expectations seem to have an impact. On the other hand, the previous Quality
Packages aimed to be a baseline for any actor and application in the wide ITS domain. This resulted in
a “balancing problem”, as illustrated in the next Figure.
Figure 4: “Balancing problem” about EU-wide Quality Frameworks (icon created by Freepik - Flaticon)
This means, that we need to trade off concepts and guidelines with a universal character, while being
context-sensitive, i.e. considering any details and circumstances for individual quality actors and use
cases. This problem will most -likely remain for the NAPCORE activity, but might be resolved by more
granular, or disaggregated approaches, looking at specific quality actors and use cases.
Further, there are certain outcomings from the individual EU EIP Quality Packages that require some
attention in the future NAPCORE works. These outcomings are explained next.
For SRTI and RTTI, it became evident that beyond the current focus on the content part of the
information chain, the end -user perspective should be also considered. This would allow a holistic
quality approach among the entire information chain. Looking at quality criteria, the criterion “data
completeness” seems important to achieve some value of the information towards the user. This
criterion has not been established for SRTI and RTTI so far. Looking into the near -term future, new
technologies such as C-ITS will bring a lot of changes to the quality framework and quality itself. Quality
aspects related to these technologies should be explored, eventually redefining the quality criteria and
requirements (e.g. looking at “latency” in the range of milliseconds) and exploring new quality methods
(e.g. checking the reliability of C-ITS data sources and using C-ITS as an independent ground truth).
For the MMTIS group, the user perspective seems to be relevant again, resulting in a need for
trustworthy data, and for a focus on information rather than only on the underlying data. The
complexity of the many data types should be reflected in the provision of suitable data standards and
formats. Finally, the measuring should look for real -time capabilities of MMTIS, among others, and
take into account non-conventional sources such as social media.
[page 15]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 15
As a general conclusion from the previous EU EIP Quality work, we found that the upcoming NAPCORE
quality work should have a more holistic view on the Value Chain of Traffic Information, looking beyond
the content-side of such Value Chain, at least on a conceptual level.
Also, the target group of potential quality frameworks in NAPCORE likely needs to be expanded. So far,
road operators and NAP stakeholders were the main target groups of EU EIP. However, the range of
possible actors is becoming highly diverse and wide, as alre ady realized in the MMTIS context. Thus,
any quality frameworks should address any actor who is responsible in a certain ITS data domain. This
could be done by supporting the actor’s business processes in terms of data quality aspects, or at least
raise awareness about those aspects. A close collaboration is required with relevant actors throughout
the NAPCORE project. Further, we need to respect that some of the relevant actors may be out of
reach of the NAPCORE project, e.g. private data providers. Here, it is important to proactively engage
and motivate such actors in our processes.
Altogether, we realise there are already four finished and agreed Quality Frameworks by EU EIP. Any
Quality Frameworks by NAPCORE should complement or update such existing Quality Frameworks .
Some of the EU EIP elaborations are considered mature and thus still valid, even in the afterlife of EU
EIP. This is especially true for the Quality Package for Safety-Related and Real-Time Traffic Information
Services (SRTI and RTTI). NAPCORE recommends to consider this Quality Package for current RTTI and
SRTI data p rovision use -cases. However, some specialisations for RTTI/SRTI sub -domains are still
elaborated by NAPCORE, e.g., for the UVAR sub -domain. In contrast, other EU EIP elaborations were
lacking maturity, and have to be revisited by NAPCORE. This is especially true for the Quality Package
for Multimodal Travel Information Services (MMTIS), which is newly released by NAPCORE.
Lastly, any NAPCORE Quality elaborations should not restrict itself on just application areas, but try to
promote also horizontal approaches, assessing common quality features related to the data processing
and data acquisition process by the user.
This means there should be a smooth evolution from previous to future quality works, as indicated in
the next Figure. Thus, the Quality Frameworks from both EU EIP and NAPCORE should serve as a
blueprint and guideline for quality practices for stakeholders responsible for NAP-based data sets.
Figure 5: Evolving from EU EIP Quality Packages to NAPCORE Quality Frameworks
2.2 Evolution of legal frameworks
Some legal frameworks by the EC , as relevant for the NAPCORE QFs , are evolving. The current
developments are explained next.
In 2023, an amendment to the 2010 Directive on Intelligent Transport Systems has been published as
Directive (EU) 2023/266111. The goal is to adopt the current framework for the deployment of ITS, and
to tackle some identified problems, such as the lack of interoperability of applications, systems and
11 https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32023L2661
[page 16]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 16
services; the lack of cooperation among stakeholders; and unresolved issues related to the availability
and sharing of data. It achieves this by expanding the current scope of the Directive to cover new and
emerging challenges, and by allowing essential ITS services to be made mandatory across the EU.
The Revision of RTTI Delegated Regulation 2015/962 has been published in 2022 as Regulation
2022/67012. This revision extends the data provision obligations from the former Regulation ,
considering additional data categories, additional network elements, and additional data standards. It
also introduces a number of levers for implementation, including a stronger consideration of quality
aspects in the course of data provision. There are two implementation dates for the data delivery
obligations: 1/1/2025 for all data in the higher-level network, or "crucial data” in the overall network;
and 1/1/2028 for all data in the entire network.
The data categories covered by the new RTTI Delegated Regulation 2022/670 are shown next.
Figure 6: Data categories from Annex of EC Delegated Regulation 2022/670
The additional data categories introduced in the revision are about locations of recharging and
refuelling points and stations; locations of service areas and rest areas; weight/length/width/height
restrictions; one-way streets; boundaries of restrictions, prohibitions or obligations with zonal validity;
current access status and conditions for circulation in regulated traffic zones; availabilities of refuelling
points and stations for alternative fuel types; and prices of ad hoc recharging/refuelling. Please note
that the “prohibitions or obligations with zonal vali dity” may also contain Urban Vehicle Access
Regulations (UVAR).
Lastly, a revision of MMTIS Delegated Regulation 2017/962 has been published in 2024 as Regulation
2024/49013. One of the major implications is that data provision will be mandatory for dynamic data
12 https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022R0670
13 https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R0490
Del Reg.
2022/670
data on
infrastructure
(a) road network links
(b) road classification
(c) tolling stations
(d) service areas and rest areas;
(e) recharging points for electric
vehicles
(f) compressed natural gas, liquefied
natural gas, liquefied petroleum gas
stations
(g) points and stations for all other fuel
types
(h) location of delivery areas
data on regulations
and restrictions
Crucial:
(a) static and dynamic traffic
regulations
(b) traffic circulation plans
Non-crucial:
(a) traffic signs
(b) static and dynamic traffic
regulations
(c9 tolled roads,
(d) variable road user charges
data on the state
of the network
Crucial:
(a) road closures;
(b) lane closures;
(c) roadworks;
(d) temporary traffic management
measures.
Non-crucial:
(a) bridge closures;
(b) accidents and incidents;
(c) poor road conditions;
(d) weather conditions affecting
road surface and visibility.
data on the realtime use of the
network
(a) traffic volume;
(b) traffic speed;
© traffic queues;
(d) travel times;
(e) waiting time at border
crossings;
(f) delivery areas;
(g) recharging points and stations
for electric vehicles;
(h) refuelling points and stations
for alternative fuel types;
(i) price of ad hoc
recharging/refuelling.
[page 17]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 17
in all member states (up to now, this could be determined individually for each member state).
Furthermore, the data categories in the annex of the Regulation have been revised, and overlaps with
the RTTI Regulation have been cleared up.
All the described revisions imply a reconsideration of affected data domains and categories. In many
cases, the scope of data is extended, which needs to be provided via NAPs. In some cases, also some
political pressures are addressed, e.g. about e-mobility and environmental issues, resulting in a special
focus on certain data categories. For the NAPCORE QFs, we analysed these revisions for additional, or
highly prioritized data domains.
2.3 WG 3 Quality workshop on March 16th 2022
To set the stage for future quality elaborations by WG 3, we organized a dedicated “WG 3 Quality
workshop” online on March 16 th 2022, where we reviewed the former EU EIP Quality Activities; gave
an overview on individual country’s activities for assessing quality ; and discussed the potential scope
for future quality work in WG3 . Altogether, with 7 Presentations and almost 50 participants, the
workshop was a great opportunity to explore individual perspectives on the quality matter, and to find
a first orientation for our future work.
A detailed documentation of this workshop is provided as Annex C.
As a summary, we learned about different approaches to quality, by different stakeholders and by
different states. Even if these approaches might differ in scope and applications, they all rely on a
common and agreed on quality aspects among actors who are exposed to such quality. The
presentations that explicitly focused on NAP data sets, revealed that such common understanding
relates to quality criteria and levels . These criteria and levels need to be described for a data set,
whenever offered on a NAP. This is exactly the concept of the previous EU EIP Quality Packages, as well
as of any future NAPCORE quality elaborations.
Still, the different approach es also imply that there must be some flexibility (or elasticity) when
defining common quality aspects, to address , e.g. different quality actors and different quality
expectations by such actors. This is an important implication for our future Quality Frameworks.
Another implication is the collaboration effort needed to enable a common understanding on quality,
and in the end a consensus on quality definitions. This way, we need to ensure a wide involvement of
stakeholders within and outside the WG 3 quality group.
We have also realised many common and similar points during the presentations. The presented works
provide a valuable baseline for quality elaborations in NAPCORE.
2.4 Three dimensions of quality
To prepare the scoping of future NAPCORE QFs, we define three dimensions which can be used to
classify quality objects or the perspective of such objects within the NAPCORE context. These criteria
are:
• Dimension 1: Data Domain
• Dimension 2: Value Chain of Traffic Information
• Dimension 3: “Objects being evaluated”
[page 18]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 18
These are explained further below. We expect that our NAPCORE elaborations will each cover a subspace in such three -dimensional space, as illustrated below. I.e., they will be related to certain
categories of each of the three dimensions. Each NAPCORE Quality Framework will have a clear
reference to such sub-spaces and categories.
Figure 7: Three dimensions of quality
Dimension 1: Data Domain
The different data domains can be best related to the ITS service categories, as prioritised and classified
by the EC ITS Directive and its corresponding Delegated Regulations. In EU EP, Quality Packages were
elaborated specifically for the domains of Safety -related traffic information (SRTI), Real -time traffic
information (RTTI), Multimodal Travel Information Services (MMTIS) and Intelligent Truck Parking
Services (ITPS).
Based on learnings from EU EIP, it is advised to build future QFs on a more granular level, i.e.,
addressing sub -domains, such as UVAR under RTTI. The reason is that any sub domains consider
specific data ecosystems, use cases etc. Further, some EC legal frameworks are also being updated (see
section 2.2) , and some NAPs also obtain mobility data outside the obligations of the EC legal
frameworks. Altogether, the notion of data domains needs to clearly revisited and newly defined for
the NAPCORE quality work.
Dimension 2: Value Chain of Traffic Information
The Value Chain of Traffic Information by TISA14 describes data and information flows for traveller
information. The definitions from the previous EU EP Quality Packages were limited to the content side
of the Value Chain . Corresponding definitions for the service side were left to Service Providers, i.e.
outside the responsibility of road authorities.
14 TISA (2012). Terms and Definitions for the Traffic and Travel Information Value Chain, Terms and
Definitions EO12013, Traveller Information Services Association (TISA), Brussels
[page 19]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 19
Figure 8: TISA Value Chain of Traffic Information
The question, if a NAPCORE Quality Framework should go beyond and equally address the service-side
of the Value Chain, as previously done for the content-side, cannot be answered quickly. On the one
hand, the EC Delegated Regulations oblige to define quality levels at the point when these data are
provided on the NAP (implying end-user services are not covered). On the other hand, we know from
practice, that service quality aspects are crucial, when we look for end-user acceptance and efficiency.
However, there are so many ways to inform the end user, so this might be a too board task.
For the NAPCORE QFs, the coverage of the Value Chain depends on how far we can reach out to Service
Providers, as these actors are crucial quality stakeholders when looking at the entire Value Chain. In
an ideal case, Service Providers’ perspective will be considered to cover the entire Value Chain.
Dimension 3: “Objects being evaluated”
In the standardisation of Quality Management Systems (QMS), quality is understood as a „degree to
which a set of inherent characteristics of an object fulfils requirements” 15 . The question now is what
an “object” represents in the scope of NAPCORE. On a higher level, relevant quality objects in the ITS
domain can be found in the standardisation work for ITS16 , defining quality dimensions as follows:
• System Quality (e.g. availability of an entire technical system)
• Device Quality (e.g. reliability of devices within a system)
• Functional Quality (e.g. efficiency of an expected function of the system)
• Data Quality (e.g. accuracy of data used for a function)
In the previous EU EIP Quality Packages, the definitions related mainly to “Data Quality”. As the
technical provision of data was also relevant, “System Quality” and “Device Quality” were touched on.
On the other hand, “Functional Quality” is covered elsewhere, e.g. in technical specifications of ITS
services.
For NAPCORE, there might still be a data quality focus, as this is the main asset of NAPs. However, as
we know that such data quality always relies on systems and devices, we might look more deeply
beyond the data level.
2.5 First prioritization by EU EIP and NAPCORE mini-surveys
In our WG 3 Quality workshop on March 16th 2022, we did a first prioritization via a Slido mini-survey,
with 26 participants indicating their priorities on each o f the three dimensions explained above. The
results are shown in the next Figures.
15 ISO 9000:2015(en), Quality management systems — Fundamentals and vocabulary. Geneva:
International Organization for Standardization; 2015.
16 CEN/TC 278 (2019): „Intelligent transport systems—Traffic management systems—Status, fault
and quality requirements“
[page 20]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 20
Figure 9: WG 3 Quality workshop Slido mini-survey - Prioritization for Dimension 1: Data Domain
Figure 10: WG 3 Quality workshop Slido mini-survey - Prioritization by Dimension 2: Value Chain of Traffic Information
Figure 11: WG 3 Quality workshop Slido mini-survey - Prioritization by Dimension 3: “Objects being evaluated”
As a result for “Dimension 1”, there is a preference to focus on the RTTI data domain, followed by
MMTIS. For “Dimension 2”, the content-side from the Value Chain seems most-relevant, however, also
with an indication for a part of the service -side. For “Dimension 3”, the quality object “data quality”
gets most of the votes, followed by “system quality”. Altogether, the main focus points from this minisurvey mainly correspond to the focus points of the former EU EIP Quality Packages, even if there are
some implications to broaden the scope of these former elaborations.
To have a deeper look into potential data domains that are of interest for NAPCORE part ners, we
initiated a WG 3 -internal mini-questionnaire In February 2002 . The question was. “For what data
domain(s) do you wish future elaborations of Quality Frameworks?” . The results are presented in the
next Figure.
[page 21]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 21
Figure 12: Results from WG 3-interla mini-questionnaire about prioritised data domains
As a result, the most -preferred data domain was “ Parking facilities & parking regulations (static &
dynamic)”, followed by “Network typologies & network attributes for vehicles (static) ” and “Fuel and
Charging Stations (static & dynamic) ”. These opinions might be influenced by the current revision by
the RTTI Delegated Regulation (see section 2.2), where network, par king and charging data are also
emphasised.
A first prioritisation of future Quality topics was done at the end of the former EU EIP project via a
questionnaire to the partners of the EU EIP Quality group.
The first question was “What is the relevance of the following, potential new quality topics for your
work / your organisation?”. The next Figure shows the results, as indicated by EU EIP partners.
[page 22]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 22
Figure 13: EU EIP questionnaire, question “What is the relevance of the following, potential new quality
topics for your work / your organisation?”
The results imply that emerging data sources and acquired/3rd party data is of high relevance (see
columns 1 and 4 in the Figure). Surprisingly, also the quality of NAP metadata is of high priority (see
column 5). This is a new issue, as EU EIP quality work so far focused solely on the content data, not
metadata. This topic is addressed by NAPCORE metadata working group (subWG 4.4), however as for
any other subject the data quality methodology shall be elaborated.
The second question was “For which quality processes do you wish further European guidance and
harmonization?”. The next Figure shows the results, as indicated by EU EIP partners.
Figure 14: EU EIP questionnaire, question “For which quality processes do you wish further European
guidance and harmonization?”
The results imply that quality frameworks, as the basic theoretical input, are important (see the first
column in the Figure), but the practical implementation of such frameworks is also relevant (see the
other columns). Thus, we need to support the practi cal implementation of quality aspects in the
responsibility of NAP actors, by providing guidance and best practices for quality assessment. This will
be dedicated work item within the NAPCORE Quality activity.
[page 23]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 23
3. Proposal for new Quality Frameworks by NAPCORE
3.1 Overview and methodology
As explained before, NAPCORE is providing new and enhanc ing previous Quality Frameworks (QFs).
Table 1 shows an overview on the current suite of Quality Frameworks, denoting their titles, the main
baselines/approaches, the connection to a project (either EU EIP or NAPCORE) , and the publication
link.
Table 1 - Overview on Quality Frameworks
Title Baseline/approach Project and publication link
Safety-Related and Real -
Time Traffic Information
Services (SRTI and RTTI)
Workshops, conceptualisation,
validation with real-life data
Published in 2019-202017
Multimodal Travel
Information Services
(MMTIS)
Stakeholder consultation
Intelligent Truck Parking
Services (ITPS)
Workshops, conceptualisation,
validation with real-life data
Cooperative ITS (C-ITS) Pilot projects
On-Street Parking Data Literature, real-life data assessment ,
stakeholder consultation
Published in 202518
Urban Vehicle Access
Regulations (UVAR)
Literature, pilot projects
Alternative Fuels (AF) Literature
Multimodal Travel
Information Services
(MMTIS) - upgrade
Analysis of national approaches,
Stakeholder consultation
Floating Car Data (FCD) Literature, real-life data assessment
Network Topology Pilot projects
A Cross -Domain Quality
(CDQ) methodology for
assessing data and
services
InQMS project , workshops, validation
with real-life data
17 https://www.its-platform.eu/achievement/quality-of-european-its-services-and-their-data/
18 https://napcore.eu/quality
[page 24]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 24
Several working groups were establishe d to wor k on individual QFs. They followed an individual
working mode and working approach, depending on their domain and expertise. However, there were
some commonalities in the methodology for all QFs as indicated in the following Figure and explained
below.
Figure 15: Basic methodology for the development of the NAPCORE Quality Frameworks
• In the Evidence Phase, various sources in the particular domain were analysed. These include
former QFs (e.g. the EU EIP quality elaborations), other literature, research works on quality
aspects, (i f available ) current deployments and pilot projects , and (if available) empirical
studies, where quality implications in real-life data sets were studied.
• In the Phase of Taxonomy Development , main quality definitions were elaborated in a
structured, hierarchical approach. In particular, a concrete set of Quality Criteria and Quality
Metrics was proposed and summarised in a tabular format. Besides definitions, each metric is
annotated with mathematical/theoretical foundations and possible values (or value ranges).
What about all the data categories and domains
without an explicit Quality Framework?
It is unlikely that we can elaborate dedicated Quality Frameworks for all
(sub) categories and use cases of ITS data. The current EC Delegated
Regulations already contain an abundance of data categories, and there
might be even more, when looking beyond those regulations.
However, many of our concepts can be reused and transferred from one
domain to another one. Imagine, we define the qualities of static parking
data, which is in many cases spatial data. Such definitions could be
transferred to other data domains which also contain spatial data.
Altogether, the envisioned set of NAPCORE Quality Frameworks is supposed
to set a baseline for data quality stakeholders. These might concretise our
frameworks for their own use cases, transfer them to to other data
domains, and adopt them to practical environments.
Evidence
Literature
Former Quality
Frameworks
Deployments &
Pilot Projects
Empirical study
on data quality
Taxonomy Development
Quality
Criterion A
Quality
Criterion B
Quality
Criterion n
Quality
Metric A1
Quality
Metric A2
Quality
Metric Am
Quality
Metric B1
Quality
Metric B2
Quality
Metric Bm
Quality
Metric n1
Quality
Metric n2
Quality
Metric nm
Validation
Case study
Stakeholder
Consultation
[page 25]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 25
For the table with Quality Criteria and Quality Metrics, a harmonised format was used among
all QFs, to achieve some consistency and comparability, when using the individual QFs. In some
cases, concrete quality levels for the Quality Metrics were also proposed, maybe starting with
pragmatic (or minimum) levels based on practical experience.
• In the Validation Phase, the quality definitions were validated and backed up via case studies,
i.e., trial quantifications of the proposed Quality Metrics using real-life data, and/or
stakeholder’s feedback. In some cases, the findings from the Validation resulted in a revision
(or improvements) of the proposed Quality Criteria and Metrics.
Please note, that most QFs followed most, but not all the sub-steps mentioned above, depending on
the individual circumstances of the analysed domain, and depending on available resources.
The next section summarizes each elaborated QF by NAPCORE, including the background , goals, the
applied methods and the outcomes.
3.2 A Quality Framework for On-Street Parking Data
Even if parking is a substantial element of the transport system, parking -related data became
prominent in the ITS domain only in the recent years , due to the intensified digitalisation of parking
assets and parking management; due to ongoing standardisation of parking data formats; and, most
specifically, due to the uprise of so -called Smart Parking Systems (SPS) . Analogue to ITS, SPS rely on
emerging technologies, e.g., in terms of sensing and data processing. SPS projects also often generate
data that are under scope of the EC Delegated Acts and National Access Points. However, no alignment
of quality aspects, e.g., across SPS deployments, could be identified so far.
Truck Parking was already covered as a specific Quality Package by EU EIP , addressing Delegated
Regulation 885/2013. This, how ever, had a rather restricted scope, looking at isolated truck parking
lots along motorways. In contrast, general parking in urban settings is far more complex, touching on
different supply segments (private vs. private, off-street vs. on-street, etc.). Further, there are various
regimes of parking management in different cities, considering e.g., parking tariffs, parking restrictions
etc. A more differentiated picture on parking-related data is given by Delegated Regulation 2017/1926
for MMTIS, looking at aspects of parking infrastructure ; access and payment options ; and real-time
availabilities. The Quality Package for this Regulation introduced some Quality Criteria. However, such
definitions were elaborated for a wide range of MMTIS data categories, neglecting the specifics of the
parking domain.
Further, DG MOVE stressed the importance of parking when talking to the NAPCORE Core Alignment
Team on January 25, 2022. There is an expectation to tackle the parking domain more deeply, starting
by harmonising the standardisation work around parking data at CEN level and other aspects of
standardisation. Lastly, NAPCORE partners indicat ed that parking might be of high priority, see the
mini-surveys in section 2.5. Parking data is also part of the “data top 15” in the Netherlands19, which is
a prioritised list of data items for improving data quality . Altogether, we realise there is an evident
need for an own QF for parking-related data, especially when such data is relevant to NAPs.
In the end, NAPCORE partner BASt elaborated a Quality Framework for On -Street Parking Data. This
QF is dealing with on-street parking data in urban setting s. More concretely, this new QF is providing
definitions for static and dynamic data about on -street parking infrastructure, parking regimes and
parking availabilities.
19 https://www.datapedia.nl/datatop15/nodes/datatop15
[page 26]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 26
A starting point were former definitions from the EU EIP Quality Packages and other literature. The QF
is revisiting, concretising, and expanding such previous quality definitions, and putting them in a
practical context of data provision in the on-street parking domain.
Because there might be many data-sourcing opportunities to describe an on-street parking situation
in a given urban scenario (based on SPS or other sources ), a suitable approach must consider a
heterogenous or multi-source data landscape. A suitable method was found in ground-truth and crossreference testing. Such method was concretised and realised by BASt in the city of Hamburg, Germany,
during 2022 as the so-called Data Campaign. The following Figure shows which data sources were used
for this Data Campaign.
Figure 16: Data sources used for data campaign (© Smartparking; INRIX, Inc.; Landesbetrieb Geoinformation und Vermessung
Hamburg; Peter Lubrich)
By analysing and comparing these data sources, various quality implications were identified that were
then translated into generic quality criteria. This findings and analyses from this Data Campaign, as
well as feedback and expertise from parking management staff in Hamburg, were used to define and
validate quality definitions for on -street parking dat a. More concretely , a set of universal quality
criteria for on-street parking was provided.
The methodology and the proposed quality criteria were finally described in detail in a research paper
called “Defining the Quality of Emerging Data: the Showcase of On-Street Parking”.
3.3 A Quality Framework for UVAR Data
Urban Vehicle Access Regulations (UVAR s) have become quite prominent as a means of traffic
management in many European cities and regions. UVARs mostly target road safety and environmental
goals and regulate or restrict the usage of public road network elements based on certain criteria.
These criteria include vehicle types, traveller types and land-use types. The regulations and restrictions
are typically valid for certain areas and (optionally) for certain time periods. In practice, they are
realised as Low Emissions Zones (LEZ), Pedestrian zones (PED), Limited traffic Zones (LTZ), and Parking
Regulations (PARK).
However, there are many types of UVARs across Europe. So, challenges occur to communicate the
applicable regulations/restrictions to drivers, especially when they are not familiar with local rules. In
Ticket Machine
Transactions
Smart Phone Payment
Transactions
Sensor Data
INRIX: Parking API Manual Data Collection City GIS = NAP data set!
[page 27]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 27
terms of a harmonised digitisation and electronic communication of UVARs, the EU project UVARbox20
has provided some baseline, including a common DATEX II profile and some local pilots with UVAR data
provisioning. However, a common approach to define quality of UVAR-related data is still missing.
The QF for UVAR Data is filling this gap, by providing guidance on applicable quality criteria and metrics,
as well as on how to conduct quality assessments.
NAPCORE partner ARMIS was leading the work for t his QF. The method contains both a theoretical
part, via a comprehensive literature review looking at applicable quality dimensions, as well as a
practical part, via defining concrete quality criteria and metrics to be applied for UVAR-related data,
as provided via NAPs.
A major output of this work is a table with a detailed description of applicable Quality Criteria and
Metrics. An accompanying report compiles findings from the literature research, the methodology to
capture the applicable quality criteria and metrics, as well as practical recommendations to conduct
quality assessments in real -life settings. Lastly, the report contains a case study with a concrete
example of how to apply the framework.
3.4 A Quality Framework for Alternative Fuels Data
Alternative fuels are becoming more and more important due to many political and environmental
reasons. Across Europe, there is a lot of investments and activities to provide infrastructures for
electric charging and other alternative fuels. This is accompanied by new legislature to accelerate and
ease the use of alternative fuels. One important legislature is the AFIR Regulation21,
The general goals of such framework are to:
• Facilitate development of charging and alternative fuels infrastructure,
• harmonize user services across countries,
• and support standardization.
More concretely, the AFIR Regulation, together with further Implementing Acts, stipulates data
provision about alternative fuels infrastructure via NAPs, using DATEX II as the data format.
While the necessary data elements are defined by the AFIR Regulation and corresponding DATEX II
profile, the necessary quality definitions are still undefined. The Quality Framework for Alternative
Fuels Data is aiming to fill this gap.
As for the UVAR QF (see above), NAPCORE partner ARMIS was leading the work for t his QF. A lot of
input was given by the Alternative Fuels Ambassadors in NAPCORE. The method is also similar, with a
theoretical part, via a comprehensive literature review looking at applicable quality dimensions, and a
practical part, via defining concrete quality criteria and metrics to be applied for AFIR-related data, as
provided via NAPs.
20 UVAR Box Consortium, “UVAR Box & UVAR Exchange.” Accessed: Jul. 11, 2024. [Online]. Available:
https://uvarbox.eu/
21 European Union, “REGULATION (EU) 2023/1804 OF THE EUROPEAN PARLIAMENT AND OF THE
COUNCIL of 13 September 2023 on the deployment of alternative fuels infrastructure, and repealing
Directive 2014/94/EU,” Sep. 2023. Accessed: Jul. 26, 2024. [Online]. Availabl e: https://eur -
lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32023R1804
[page 28]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 28
A major output of this work is a table with a detailed description of applicable Quality Criteria and
Metrics. An accompanying report compiles findings from the literature research, the methodology to
capture the applicable quality criteria and metrics , as well as practical recommendations to conduct
quality assessments in real-life settings.
3.5 A (renewed) Quality Framework for MMTIS data
The domain of MMTIS data is quite complex as it encompasses all mobility modes and their
interactions, while involves all mobility stakeholders.
The MMTIS Quality Framework created in the framework of EU EIP project (see section 1.3) highlighted
the key challenges to ensure qualitative data and proposed guidelines that potentially can be adopted
by all MS. As one of the most critical challenges is how to consider local/ national condit ions and
specificities in a general quality framework, the EU EIP output was a significant achievement and first
step towards data quality goal. For the existing MMTIS Quality Package by EU EIP, it was, however,
stated that further validation, research, and development efforts are required.
The importance of acquiring and publishing multimodal qualitative, interoperable data, able to be
reused to provide reliable mobility services, both for end users and back-offices operations, led to the
second Programme Support Action from CEF, in 2020; the DATA4PT project 22. In the framework of
DATA4PT, multimodal data quality aspects are also managed with the aim to enable the wide adoption
of EU public transport data standards and support MS to comply with MMTIS regulation. Focusing on
the TRANSMODEL data standard23 and the relevant data exchange formats (NeTEx , SIRI et al.) ,
DATA4PT defines data validation rules, and develops methods and tools with the contribution of MS
and experts . In this framework, valuable feedback has been collected regarding stakeholders’
requirements and expectations regarding MMTIS regulation and data quality, the actual difficulties in
validating data, how validation can be integrated in data production pipeline , etc. Therefore, outputs
from DATA4PT project were used as a main baseline for the further development and enhancement
of the initial EU EIP Quality Framework.
Moreover, the MMTIS quality work at NAPCORE enabled a coordinated involvement of all types of
stakeholders ( representing public transport operators and authorities, providers of micromobility
services, and providers of alternative transport modes services like car sharing , ride sharing, ride
hailing) and all EU MS representatives under the same umbrella. Their feedback was another important
baseline to the update and recognition of the commonly agreed MMTIS Quality Framework.
Finally, the recent update of the EC MMTIS Delegated Regulation24 provided new inputs and aspects
that potentially will influence a corresponding Quality Framework.
The main goals for the renewed Quality Framework are:
• To overcome the interoperability issues. Coordination regarding standardisation work which
is addressed through NAPCORE will also have positive effect to the definition of a “as-muchas-possible” common framework that can be applied to most cases. The conformity of data
22 https://data4pt-project.eu/
23 TRANSMODEL is the CEN standard that concerns multimodal data and currently meets most of
MMTIS Regulation data content requirements.
24 https://eur-lex.europa.eu/eli/reg_del/2024/490/oj
[page 29]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 29
with the EU CEN standards can be one of the basic steps that will ensure a certain level of
quality of published datasets.
• To highlight the reuse of the data available at NAP as the goal. Currently it is not always clear
that this is the goal of the NAP data, so quality is necessary for this goal. If the overall NAP data
goal remains similarly ambiguous, then data providers may find it more expedient to submit
information of poorer quality but with lower a cquisition/collection costs, in a box -ticking
exercise. However, with data reuse as the goal of NAP submissions, providers must comply
with quality frameworks. As such, data p roviders cannot neglect the data quality aspect.
Feedback from DATA4PT, showed that national legislations do not underline the reuse of
published data in a clear way, which might also contribute to a significant tolerance on the
quality.
• To facilitate implementation. A quality framework that defines basic criteria applicable to all
countries enables also NAP implementation. It helps the development of data validation tools
and methods applicable to all EU countries. Especially for countries which lack resources and
expertise, this kind of support is vital if we aim the wide implementation of ITS regulation
across the EU. Potential approach?
The methodology for this QF starts with a review of the former EU EIP MMTIS QF. Criteria from this QF
were reframed and concretised to capture relevant quality aspects. Further, current MMTIS quality
methods and approaches across EU members were reviewed via three online workshops. At these
workshops, national quality approaches for MMTIS data were exposed by NAPCORE partners from
Norway, Switzerland, Austria, France, Italy, and Data4PT.
All these inputs have been considered for an update of the MMTIS QF. A resulting report compiles the
methodological approach, an updated set of MMTIS Quality Criteria and Metrics, and
recommendations for a practical assessment of such Criteria and Metrics
3.6 A Quality Framework for Floating Car Data
Floating car data (FCD), also known as probe vehicle data, is widely regarded as an advanced method
for supporting ITS services . FCD is a dynamic and real -time data collection method that involves
gathering information from GPS -equipped vehicles as they move through a road transport network.
These vehicles, typically comprising a fraction of the entire public or private vehicle fleet, continuously
transmit their location, speed, direction, and sometimes additional parameters, such as acceleration,
deceleration, and engine status, to a centralized data aggregation system (server). In this respect, FCD
serves as a life feed providing a continuous picture of and insights into various facets of the operational
state and status of a road transport network, including traffic flow, travel patterns, level of congestion,
and vehicle -induced emissions. For these reasons, FCD are increasingly u tilized in ITS applications
related to the provision of traveller information, navigation, route planning, and traffic management.
Additionally, FCD is becoming more significant with the advancement of connected and autonomous
vehicles, contributing to the larger framework of smart city initiatives.
Use cases enabled by FCD
[page 30]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 30
FCD supports a wide range of use cases within the digital transportation ecosystem. Cerqueira et al.
(2018)25 classify these into the following categories of mobility applications:
• Digital route and map inference : Reconstructing FCD trajectories to infer the topology and
geometry of road networks, enabling graph-based or detailed digital representations.
• Traffic sensing and prediction : Estimating current or future traffic statuses, including speeds
and travel times on specific segments, based on geolocations of probe vehicles.
• Trajectory mining : Analysing realized routes to study route choice behaviours, identifying
frequently or infrequently used routes, and the user demographics involved.
• O-D matrix estimation: Approximating origin-destination flow matrices to understand mobility
demand between key locations.
Besides such potentials, some challenges and complications are identified, especially when acquiring
FCD from commercial, 3rd parties. It is noted that FCD is not mentioned explicitly as a data category in
the RTTI EC Delegated Regulation 26. However, many data categories are derived from FCD which fall
under the EC Regulations , notably traffic -status related data, such as “traffic speeds”, “travel times”
and “traffic queues”. Very often, traffic management centres acquire commercial FCD to use the
derived traffic-status information for their management or monitoring purposes. The quality aspect is
crucial during this acquisition process. However, besides some academic approaches to FCD quality,
there seems to be no practice-oriented guidance.
To address these challenges, a new QF for FCD, led by NAPCORE partner CERTH, aims to evaluate the
suitability of FCD for various use cases . It is considered an extension of the former QF for “Safety-
Related and Real -Time Traffic Information Services” developed in the context of the EU -EIP project
(see section 1.3). Some concepts from this former QF are revisited and re -interpreted for the FCD
domain. For example, data completeness aspects , as defined in the EU EIP QF, are re -interpreted as
share/penetration rates of vehicles providing FCD, compared to the total number of vehicles, and other
quality aspects.
Dimensions of FCD QF
The FCD Quality Framework evaluates the suitability of floating car data through four key dimensions:
correctness, completeness, timeliness, and hybrid dimensions. Each dimension encompasses specific
quality criteria and metrics tailored to assess different aspects of data quality. Correctness focuses on
the accuracy, bias, classification correctness, and reliability of FCD, using metrics such as Mean
Absolute Percentage Error (MAPE), Root Mean Squared Error (RMSE), and Congestion Classification
Error in Congestion (CCEC). Completeness examines the spatial and network coverage of FCD and the
presence of missing data, with metrics like Grid Coverage (GC), Link Coverage (LC), and Percentage of
Missing Values (PMV). Timeliness evaluates the freshness and latency of data, employing metrics such
as Average Update Frequency (AUF) and Average Time Delay (ATD). Lastly, the Hybrid Dimensions
consider the contextual factors influencing FCD, including granularity, penetration rate, sampling rate,
map-matching accuracy, and fleet composition. These criteria are assessed using diverse metrics, such
as Segmentation Density (SD) and Weighted Link Coverage (WLC), to ensure that the FCD meets the
needs of diverse ITS applications.
The methodology of the FCD QF is shown in the next figure.
25 Cerqueira, V., Moreira -Matias, L., Khiari, J., & van Lint, H. (2018). On evaluating floating car data
quality for knowledge discovery. IEEE Transactions on Intelligent Transportation Systems, 19(11),
3749-3760. https://doi.org/10.1109/TITS.2018.2867834
26 https://eur-lex.europa.eu/eli/reg_del/2022/670/oj
[page 31]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 31
Figure 17: Methodology for the Quality Framework for Floating Car Data
A main input was an analysis of current State of the Art (SoS), including use cases with FCD relevance.
From here, a preliminary set of FCD quality criteria and metrics was proposed. Another important part
of the methodology was a c ase study with real-life FCD in Thessaloniki. Via a “reverse engineering”
sdataset. Quality implications from this comparison were then analysed via GIS analytics and several
python script s assisting the quantification of various quality metrics grouped under the
aforementioned criteria and dimensions . The results of this application provide useful insights into
various facets of FCD quality, which are then translated to implications for FCD providers and/or NAP
operators.
The resulting report compiles the methodology, criteria, and metrics, offering a practical tool for
assessing and improving FCD quality across diverse applications.
3.7 A Quality Framework for Network Topology Information
The topology of a road network refers to the arrangement or structure of the network, including how
roads are connected and the relationships between different segments or nodes within the network.
It encompasses aspects such as the layout of roads, intersections, junctions, and the paths that vehicles
can take to navigate from one point to another.
In the context of road databases, topology and geometry are two fundamental concepts that describe
different aspects of spatial relationships and structures. Thus, it is important to understand their focus.
In essence, while geometry deals with the actual shapes and positions of spatial/road features,
topology is concerned with the relationships and connectivity between these features. Both concepts
are essential in spatial data analysis and geographic information systems (GIS) to accurately represent
and analyse real-world spatial phenomena, such as roads.
This QF aims to establish a common understanding of quality aspects, when dealing with topology
information. It is mentioned that “geometry” is noted as a data category in the RTTI EC Delegated
Regulation27, but “topology” not. However, both concepts are essential for road data bases, from
27 https://eur-lex.europa.eu/eli/reg_del/2022/670/oj
[page 32]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 32
which many data are derived which fall under the EC Regulations. As no previous quality definitions
are found for the domain of Network Topology Information, this QF fills this gap.
NAPCORE partner ERTICO group was leading the work for t his QF. ERTICO is also leading the TN -ITS
working group, which is dealing with network topologies from a data-standard perspective.
The methodology for this QF starts with an analysis on how road databases are usually modelled, on
relevant use cases relying on network topology (in the scope of the RTTI ), and on relevant data
providers. The quality dimensions are then derived from an analysis o f so-called topological checks,
which are usually conducted by road databases. One of such checks is the “Intersection Check”, for
example.
From there, key elements related to road topology are identified that are important in a QF for
Topology information. Finally, a set of Quality Criteria and related Metrics is derived from the previous
findings, allowing for documenting quality levels of topology information.
The Quality Criteria and Metrics are formulated by “rules”. These rules related to the mentioned
topological checks. For example, for the “Intersection Check”, the rule might be “Road Segments Must
Connect at Intersections”. This rule is further assessed via multiple Quality Criteria and Metrics.
A major output of this work is a table with a detailed description of applicable Quality Criteria and
Metrics. An accompanying report compiles findings from the preparatory analyses, the methodology
to capture the applicable quality criteria and metrics, as well as practical recommendations to conduct
quality assessments in real-life settings.
3.8 A Cross-Domain Quality (CDQ) methodology for assessing data and services
The Cross-Domain Quality (CDQ) addresses common quality features related to the data processing
and data acquisition from the data user’s perspective. Specifically, it provides a methodology for
assessing data and services by a data user, building upon the former InQMS project (see section 1.3).
The main motivation for the developing of CDQ is to address current barriers and inefficiencies for data
reuse within the ITS and NAP context. Such inadequacy was also uncovered by participants of the WG3
quality workshop when indicating that that metadata quality is highly relevant.
The ITS directive provides guidance and requirements for various data categories to be provided via
NAPs. It a lso mandates that the related data contents and data services should be adequately
described and facilitated to enable data discovery and sharing.
Data and service descriptions are typically established through metadata. For the metadata creation
on NAPs, s ignificant harmonisation efforts have been made by the former EU EIP C oordinated
Metadata Catalogue and the new NAPCORE mobilityDCAT-AP specification. While some data suppliers
describe their data using these standards, many provide sparse or incorrect metadata.
Various data standardisation groups work to harmonize data content by defining minimum profiles ,
though without recommendations for preferred location mechanism. Best practices for the data
delivery exist but are often not agreed upon by NAP operators and data suppliers.
Research across NAPs reveals that many do not follow harmonization efforts, creating a barrier for
potential data subscribers. Data is rarely described consistently, and metadata is often incomplete,
inaccurate, or data sets are difficult to obtain administratively. There is also a wide variety of data
structures (profiles), which should at least respect some structural definitions or conform to common
requirements.
[page 33]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 33
Today’s data delivery methods vary in terms of security mechanisms and other features . S ome of
descriptions or delivery mechanisms are better than others, while some are obsolete. There are many
options that could better meet the data users’ requirements, such as uniform authorization features
or notifications for changes.
The Cross -Domain Quality (CDQ) methodology aims to provide guidance and best practices for
describing, structur ing and disseminat ing data in a harmonised and efficient manner across NAPs.
Once the data reaches the subscriber, the real-world quality aspects of the data, as defined by domainrelated QFs become relevant.
The goal of the CDQ methodology is to reduce efforts of data users / subscribers when acquiring and
consuming data and to provide a perspective for the data producers. Some NAPs already check formal
aspects of the data, though only automatically.
The CDQ methodology includes various assessment methods for standardized reporting of different
aspects of data/service quality during several phases of the subscription process (planning, staging,
production and ad -hoc) and for different assessment types. The first developed method “Evaluation
of the formal quality of data/service documentation” . This method evaluates metadata of a specific
data set/service against defined criteria, enabling data user s to check the suitability of a data
set/service during the planning phase of data subscription process. This method is operational, with
tools (Excel spreadsheet) and detailed documentation available for individual assessments . This
method has been tested on 39 data sets from 19 NAPs and the results from these tests were presented
during the Mobility Data Days 2024 in Turin.
Figure 18 Number of evaluated catalogue records by the CDQ methodology and resulting grades
Other assessment methods from the CDQ methodology may be developed later.
The set of assessment methods from the CDQ methodology forms a horizontal layer above other
domain-related QFs. This methodology defines agreed upon features of data/service provision that
can be observed and evaluated towards a common goal: providing services uniformly according to
agreed rules and best practices. Following this methodology will also highlight features that need
enhancement in a NAP system update.
19
[page 34]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 34
3.9 Publication of Quality Frameworks: the Quality Online Repository
The NAPCORE Quality Activity has established a n “Quality Online Repository ” on the NAPCORE
website28. This includes background information and various deliverables (downloadable files) by the
NAPCORE quality task. In other words, it acts as single -point-of-access for all quality elaborations by
NAPCORE. A similar repository was provided by EU EIP29.
With such online repository, an incremental approach is possible, i.e., QF documents can be uploaded
or updated over time. The first release hosts a first population of QF documents that were ready at the
time of this report (April 2025). Other QF documents will follow later.
28 https://napcore.eu/quality/
29 https://www.its-platform.eu/achievement/quality-of-european-its-services-and-their-data/
[page 35]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 35
4. Next steps
After establishing the Quality Frameworks, as introduced above, it is important to disseminate the
works among potential stakeholders and user, in particular data managers at various organisations
which provide data on NAPs. Only with a wider outreach, the acceptance and efficiency of the
NAPCORE QFs can be ensured. To do so, the NAPCORE Quality Group is organising outreach actions
and expert involvements, for example via conference contributions (e.g., at the NAPCORE Mobility
Data Days) and articles in professional journals.
The aspect of practical implementation is also covered by another milestone by the NAPCORE Quality
Activity, called “M3.9 Quality Framework application guideline”. This guideline complements the
elaborated set of QFs by adding a practical dimension. Topics are, among other, the various roles and
actors in Quality Assessment, and concrete procedures and tool sets to conduct Quality Assessments.
The mentioned outreach activities and the M3.9 report will be also published at the NAPCORE Quality
Online Repository (see section 3.9).
Future EU activities might include more practical approaches for real -life quality reporting and
assessments, to be conducted by data managers at individual organisations. Concrete tasks might be:
• Practical guidelines for the collection, digitization and exchange of quality metrics and reports,
based on Quality Frameworks from NAPCORE
• Machine-readable representation of quality metrics using the Data Quality Vocabulary30
• Concept study and pilot testing of feedback mechanisms for data quality management (thus,
concretizing the stipulation from the EC RTTI Delegated Regulation)
These future topics are considered at future activities by NAPCORE.
30 https://www.w3.org/TR/vocab-dqv/
[page 36]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 36
Annex A: Details about former EU EIP Quality Frameworks
Quality of Safety-Related and Real-Time Traffic Information Services (SRTI and RTTI)
The Quality Package for the domain of Safety-Related and Real-Time Traffic Information Services (SRTI
and RTTI) was published in May 2019. It aims to support the SRTI and RTTI data provision in accordance
with Commission Delegated Regulations (EU) No 2015/962 and No 886/2013.
This SRTI and RTTI Quality package is considered the most mature product of EU EIP and its predecessor
projects. It has undergone several updates and validations; consultations with NAP, SRTI and RTTI
experts; and even national concretisations by selected road operators. The parallel validations were
based on a series of quality tests with European partners, to evaluate and back up the quality
definitions in the Quality Package.
Resulting from this process, the current version of the SRTI and RTTI Quality Package presents validated
quality definitions, ready to be used in every-day practice by all SRTI and RTTI services and stakeholders
in Europe. There is also an accompanying document “Practical Guidelines” which serves as a compact,
hands-on guidance for quality practitioners, e.g. at Traffic Information Centres (TIC) or a Traffic
Management Centres (TMC). Finally, the validation activities are also documented, providing
references to recent quality tests in real-world conditions.
Altogether, the published set of documents shows the year -long efforts of EU EIP sub -activity 4.1 in
establishing an agreed and validated framework for quality in the field of SRTI and RTTI.
As done for any EU EIP Quality Package, there was an intense involvement of SRTI/RTTI stakeholders,
within and outside the EU EIP activity. The involvement allowed a reflection and (partially) revision of
the quality definitions within the Quality Packages. A major stakeholder contribution came from road
operators during the validation activities, where road operators participated in quality tests with reallife SRT/RTTI data. To do so, they provided sample data, assisted with data processing and helped to
interpret the test results, in accordance with the EU EIP quality definitions.
As further stakeholders, SRTI/RTTI service providers were approached via the Traveller Information
Services Association (TISA). One interesting notation from that group was that future quality
frameworks should look beyond the content part of the information chain, being the current focus of
the EU EIP work. Thus, the end -user perspective should also be considered, allowing a holistic quality
approach among the entire information chain.
The production of the SRTI and RTTI Quality package further revealed some issues and challenges, one
of them being the balance between details and universality. When providing many details and
concretisations, the applicability of the quality definitions u nder different circumstances may be
increased. On the other hand, the understandability of such definitions may be affected this way. For
example, the table of quality criteria for SRTI and RTTI became quite complex during the years,
including many remarks , exceptions and rules. In the end, the EU EIP group revisited these criteria
again, cleaned them out and brought them to a more compact and universal level. This also better
addresses the original goals of the Quality Package: to be a framework with commo n, EU -wide
definitions, which need to be concretised at local institutions, for local circumstances.
Quality of Multimodal Travel Information Services (MMTIS)
The Quality Package for the domain of Multimodal Travel Information Services (MMTIS) was published
in October 2019. It represents a first quality framework related to data and information in MMTIS and
[page 37]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 37
aims to support the MMTIS data provision in accordance with Commission Delegated Regulation (EU)
No 2017/1926.
As a starting point, the complex and multi -layered domain of multi -modal mobility was explored in
terms of data and information quality. This was done via an extensive stakeholder consultation, to
capture the individual insights and perspectives of MMTIS stakeholders. Especially for MMTIS, many
diverse stakeholders are concerned, sometimes organised in branch organisations. The interaction
included two stakeholder workshops and a structured questio nnaire to validate the Quality Package.
During this process, the stakeholders gave valuable feedback for the validation of the proposed MMTIS
quality criteria, quality requirements and assessment methods. Interestingly, all criteria and most of
the levels were agreed by the stakeholders, even if the individual qual ity perspectives and approach
vary from stakeholder to stakeholder. Even more, MMTIS seems to be the area where the perception
of the information quality varies the most from one country to another, considering the users'
expectations and the transport customs of each country. This results in minimum requirements levels
which can be very different between countries.
The stakeholder’s inputs also revealed that there are already some individual quality concepts
(including quality criteria and assessment methods) which could be incorporated in the EU EIP Quality
Package.
However, the main lesson learned from the MMTIS quality activity is that quality assurance and
assessment in MMTIS is far from being harmonised and widely established, certainly when it comes to
door-to-door travel chains. Thus, the EU EIP Quality Package is a first approach for a common
understanding on how to understand and handle MMTIS quality. However, further validation,
research, and development efforts are required.
An essential challenge in this context, as identified in the validation phase, is that MMTIS quality is
quite a complex and evolving working field. Expressed by the “Quality Iceberg” (see Figure 4), it
becomes obvious that the visible part of data and serv ice quality is a product of many underlying
processes. Such underlying processes differ from organisation to organisation, and from data type and
to data type, and are barely able to be harmonised in the form of a Quality Package.
Figure 20: The “Quality Iceberg” in the context of MMTIS Quality (based on VDV, Association of German
Transport Companies)
[page 38]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 38
Altogether, MMTIS quality-related definitions cannot be determined in a complete and deep manner
at this point of time. Consequently, the current MMTIS Quality Package is not considered a formal
guideline, but more an aid or source of information for interested stakeholders.
Quality of Intelligent Truck Parking Services (ITPS)
The Quality Package for the domain of Intelligent Truck Parking Services (ITPS) was published in
October 2019. It represents a first quality framework related to data and information in ITPS and aims
to support the ITPS data provision in accordance with Commission Delegated Regulation (EU) No
885/2013.
Some insights into the applicability of the current ITPS Quality Package could be derived from a
validation phase, with focus on real -life ITPS data in the Netherlands and Germany. Both validations
indicate that the definitions from the ITPS Quality Package are stable. i.e. the criteria can be replicated
in real-life environments, and quality requirements seem to be at reasonable levels.
Again, relevant stakeholders were involved when drafting the ITPS Quality Package. During a
workshop, questions were raised, e.g. whether the EU EIP quality definitions were sufficient for a
common understanding on truck parking information quality. Accord ingly, data quality issues are
important for the stakeholders, in terms of building a solid information base for the individual services.
However, other issues seemed to be also important, such as the business perspectives of truck parking
operators. It wa s stated that costs and benefits for delivering data (according to EC Regulations) do
not always pay off. For the quality work, this means that the data perspective must be put in a wider
context, also reaching out to strategic and business goals of stakeholders in the ITPS domain.
The main lesson learned when defining quality criteria in ITPS is that many definitions from the former
EU EIP quality frameworks could be adopted for the ITPS domain, so there was no need for developing
such definitions from scratch in the ITPS case.
C-ITS Information Quality
The Quality Package for the domain of Cooperative ITS (C -ITS) was published in December 2020. It
represents a draft quality framework related to data and information in C -ITS, and also aims to add
quality aspects to ongoing C-ITS harmonisation approaches in Europe, e.g. via the C-Roads project.
The main lesson learned from the elaboration of this Quality Package is that the variability of data
categories and complexity of data flows in C -ITS deployments make a generic description of C -ITS
quality quite challenging. Also, a pure adaption of the fo rmer Quality Packages, e.g. for SRTI/RTTI,
would not be helpful.
To resolve this issue, the EU EIP activity started with a “zooming -in” approach, looking at selected
communication chains and specific use cases. This way, some preliminary quality definitions were
developed for those specific cases. The resulting Quality Criteria (e.g., “latency”) were then quantified
with (minimum) requirements per use case. As evidence, e.g. from literature and evaluations of
ongoing C-ITS projects, is still quite limited, only a few requirements could be quantified. In addition,
[page 39]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 39
the Quality Criteria were correlated with data elements from ETSI 31 specifications (defining message
contents in C-ITS) as well as evaluation techniques in current C-ITS deployment projects.
Stakeholder inputs, collected in a recent workshop, indicated the need to differentiate the various C -
ITS technologies, communication actors and use cases, when describing and defining Quality Criteria.
For example, the choice of a specific communication t echnology clearly affects the definition and
setting of many Quality Criteria. Such differentiation needs to be considered in future work on the C -
ITS Quality Package.
The C-ITS quality work has been also validated. Questionnaires were sent to C-ITS deployment experts,
asking them to review the preliminary Quality Criteria. In the end, some of the definitions could be
improved and reframed, and some practice -based recommendations were formulated to handle
quality aspects in future C-ITS deployments.
General reflection on the EU EIP Quality Packages
The work on the EU EIP Quality Packages indicate d the value of having a European quality assurance
and assessment framework in the domain of ITS. Besides the production of concrete frameworks,
namely the mentioned Quality Packages, the work facilitated some fruitful discussions with many
European stakeholders and experts on aspects of ITS data and service quality. Such discussions took
place within the EU EIP group as well as with external stakeholders and organisations. During such
discussions, it was ofte n stipulated to apply or set up quality frameworks for the many ITS domains,
e.g., for (multimodal) travel and traffic information services. The details and contents of such
frameworks, however, require intense efforts to analyse the underlying data ecosystems, and to define
and validate applicable quality concepts. These works have been carried out by EU EIP throughout the
recent years and will be taken on by future EU projects.
The main lesson learned from the EU EIP activity is that any quality definition requires a continuous
back-up and validation from stakeholders. For the perspective of traffic m anagers, this means they
must get out of their daily operational environment and to carry out in-depth reflections on the quality
of the provided services. For quality frameworks on a European level, this means that evidence from
conditions and operating environments, as well as expert knowledge of the public and private
stakeholders need to be involved. In EU EIP, such back -up and validation resulted in several updates
of the EU EIP Quality Packages. Thus, the most -recent versions, as published on the EU EIP website,
reflect the current state-of-the-art of evidence and expertise regarding quality definitions for various
ITS domains.
However, the various Quality Packages also reveal different levels of maturity. Whereas the SRTI / RTTI
Quality Package is based on year -long experience and validation, the most -recent C -ITS Quality
Package is fairly new, and thus lacks such maturity. Cons equently, the work for establishing common
ITS quality frameworks is an ongoing task, going beyond the run time of EU EIP.
31 ETSI: European Telecommunications Standards Institute
[page 40]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 40
Annex B: Details about the InQMS framework
Real world (Content) quality parameters
Real world quality parameters assess the message content for precision, completeness, timeliness,
geographical coverage, and accuracy. These parameters must be validated against true value s,
focusing on how to obtain and use ground truth data to validate service content. This type of test is
possible when the service consumption is set up. The InQMS Framework, based on real service
experience, also defines service content related quality measures that can be directly measured from
retrieved data samples suc h as number of incidents, data liveliness (how they are
updated/terminated), and location description problems.
The concept of real world (actual) quality is well defined through EU-EIP quality frameworks.
Formal quality parameters
According to the ITS Directive, all EU member states must establish a NAP. Potential subscribers need
to know several pieces of information about the data and service to assess their usefulness. This
“metadata” is critical from the p erspective of the user. Traffic information providers must provide
certain metadata about their service to the national access point, which can be perceived as the formal
data quality.
The metadata, harmonized by EU -EIP project, sh ould describe all measures needed for assessing
technical aspects of the data. One of the most important metadata elements is the real data sample
and a validation schema. This allows potential subscribers to g ain practical experience with the data
and adapt their systems for data reception. Formal quality also includes general information about the
dataset derived from metadata , such as unique source identification, quality and completeness of
provided documentation, usability of subscription information, availability of clear licencing and
chosen format, location description and delivery mechanism. The evaluation of chosen metrics is done
against best practice.
Assessing formal quality precedes data subscription (planning stage) of a service and includes checking
the metadata for completeness, inspecting provided sample and evaluating the provided information
against predefined criteria. Fulfilling formal quality means that data are well described without any
obvious gaps, making its usage possible.
Any service can later be evaluated against the criteria given in metadata (structure, frequency, access
info, etc.).
Technical quality parameters
Apart from formal requirements and real data content, each service type has different technical quality
aspects that can be evaluated depending on the transformation of the original information and its
delivery to the user. The InQMS framework defines technical quality from structural and delivery
perspectives, executed in staging and production phases of data consumption.
During staging, t he delivery perspective includes manual evaluation of administrative and technical
issues related to subscription. The a dministrative part assesses the ease of subscribing to data
(procedure, legal and time aspect) while technical part focuses on availability of reference data,
compliance with metadata information and delivery channel characteristics such as method of
consumption, level of security (including authorization ), content type, content compression,
conditional request (e-tag), sample envelope, update time and size.
[page 41]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 41
During production, the delivery perspective includes automatic evaluation of data update time,
availability and number and size of received files. There are threshold values for some of the
characteristics but mostly the assessment is qualitative.
During staging, the structural perspective involves manual evaluation of the quality parameters of the
web service, including incorrect use of message attributes, location description, situation description,
matching of the live sample with the schema, real availability of the location data referenced in the
live sample and adherence to good practices.
During production the structural perspective involves automatic evaluation of received files against
schema.
Both delivery and structural perspectives work with information provided via metadata and checks if
information matches with reality.
Figure 21: Example of the metrics processed in the inQMS with respect to delivery and structural soundness of the data
[page 42]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 42
Annex C: Documentation of NAPCORE Quality workshop on March 16th
2022
Workshop agenda:
• Peter Lubrich (DE): Why a Quality Framework for ITS Data and Services?
• Risto Öörni (FI): Overview on EU EIP Quality Frameworks
• Christian von Huth (DK): Quality from a Public Data Provider's View
• Ydo de Vries (NL): Quality from a NAP operator's View
• Damaris Gruber (AT): Quality from a National Body's View
• Petr Bureš (CZ): A Formal and Technical Approach to Quality Assessment of Traffic Information
Services
• Fruzsina Homolka (CH): The Swiss Approach on Quality Assessment
• Common discussion of future NAPCORE Quality Frameworks
The introduction sessions by Peter Lubrich and Risto Öörni explained the context and previous work
on the quality matter. These aspects are already covered by previous sections of this paper. Further,
the impulse presentations in the middle part of the age nda revealed a variety of individual quality
approaches, depending on the presenter’s role and activities. These impulse presentations are
summarised next.
Christian von Huth , speaking for the Danish Road Directorate pointed out the importance of quality
from an end -user perspective. Users in this context may be service providers who acquire the
Directorate’s data sets via the NAP. By making the quality of a data set transpare nt via the
corresponding metadata, the data user might get a better understanding of the suitability and
applicability of the offered data set. A concrete way to do so is to attach downloadable quality
descriptions to the data set offering in the NAP, see the next Figure.
Figure 22: Example how to attach quality descriptions to the data set offering in a NAP
[page 43]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 43
Ydo de Vries represents National Data Warehouse, which also hosts the Dutch NAP. He reported that
a NAP upgrade is planned, which will focus on different “v alue levels” of datasets in the NAP register.
The higher such level, the more intense and more frequent a quality monitoring about one data set is
envisioned. Such monitoring might consider both EU EIP quality definitions and a quality model by
Rijkswaterstaat. There is also an internal “ NDW Data Quality Dashboard ”, which allows the NAP
administrators to monitor e.g., the current compliance of data, as imported into the NDW, see the next
Figure. However, this Dashboard is not opened for NAP data sets yet.
Figure 23: NDW Data Quality Dashboard
Damaris Gruber, representing NAPCORE WG 5 dealing with National Bodies, explained the role of
common quality criteria in the context of “Compliance Assessment”. Such Assessments are used to the
check adherence of data providers to the EC Delegated Regulations. These Regulations often state
“quality keywords”, however without further explanation. For the activities by WG 5, these key words
need to be related to, e.g., quality criteria defined by NAPCORE WG 3. Altogether, the elaborations by
WG 3 are an important input to WG 5, so we will intensify our cooperation.
Petr Bureš presented a previous framework for a “ Formal and Technical Approach to Quality
Assessment of Traffic Information Services”, as proposed by the Czech Technical University in Prague.
This framework looks at different quality aspects of services and the information exchanged herewith.
These aspects need to be assessed at different stages of services, from planning up to production. The
aspects are divided into formal dimensions (relat ing to data d ocumentation via metadata) and
technical dimensions (looking at data d elivery, structure, and content). The formal dimensions are
proposed be assessed in a tabular format, see the next Figure. This framework is targeted the entire
value chain of traffic information, including end-user services, e.g., via RDS-TMC services.
[page 44]
A set of Quality Frameworks for the assessment of NAP (meta)data quality
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 44
Figure 24: Example for an assessment of formal for a data set
Fruzsina Homolka presented the Swiss absolute data quality approach for “Multi -Source Data
Platforms”. This concept assumes a wide variety of quality levels, when integrating various data
sources, hence setting minimum requirements would not reveal potential high-quality data and would
exclude potential lower quality data from a NAP, which may be useful for some applications. Therefore,
the concept says, there is no such a thing as “bad or good data quality, only different quality levels”.
The concept further defines absolute quality levels and/or sub-levels, which are based on multiple data
category specific quality criteria, considering different potential user requirements and potential
applications (see the following Figure). This way, different criterion based absolute quality sub -levels
are defined and can be combined into an overall (but general) absolute quality level, similar to previous
approaches such as QUANTIS. The concept will be tested at the Swiss Traffic Data Platform (TDP).
Figure 25: Concept of absolute quality (sub-) levels
