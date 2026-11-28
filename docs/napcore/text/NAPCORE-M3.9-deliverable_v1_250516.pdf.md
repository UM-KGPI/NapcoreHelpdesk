url: https://napcore.eu/wp-content/uploads/2025/07/NAPCORE-M3.9-deliverable_v1_250516.pdf
title: NAPCORE M3.9 deliverable v1 250516

[page 1]
Quality Framework Application Guideline
Report by Task 3.2: European NAPs data quality
Status: final
Version: 1.0
Date: 16 May 2025
Legal disclaimer
The sole responsibility for the content of this document lies with the authors. It does not necessarily
reflect the opinion of the European Union. The European Commission is not responsible for any use
that may be made of the information contained therein. All images are provided by the respective
partners (unless otherwise noted) and are approved for reproduction in this publication.
[page 2]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 2
Document information
Project acronym NAPCORE
Full project title National Access Point Coordination Organisation for Europe
Grant Agreement No. MOVE/B4/SUB/2020-123/SI2.852232
Activity no. and title WG 3 NAP content and accessibility
Author(s) Peter Lubrich, BASt
Co-author(s) David Ariño-Montoya, ITxPT
Anastasia Founta, ITxPT,
Chrysostomos Mylonas, CERTH
Related to Milestone no. M3.9
External Milestone yes
Document history
Version Date created/ modified by Comments
0.1 18.02.2025 Peter Lubrich, BASt First draft
0.2 27.02.2025 David Ariño-Montoya, ITxPT Method additions
0.3 06.03.2025 Chrysostomos Mylonas,
CERTH
Anastasia Founta, ITxPT
Method additions
0.4 20.03.25 Call with author group Added actor roles, reformatting of actor
roles
0.5 22.04.2025 Peter Lubrich, BASt Cleaned out and comple ted methods
chapter, added conclusions chapter
0.6 24.04.2025 Maria Stavara, CERTH Methods checked
1.0 16.05.2025 Peter Lubrich, BASt Group-internal review, finalisation
Action requested
☐ To be revised by partners involved in the preparation of the document
☐ For review/ approval by the Core Alignment Team
☒ For approval by the NAPCORE Steering Committee
Abstract
This deliverable by NAPCORE WG3 summarizes basic concepts and methods for operational Quality
Assessments to be undertaken at responsible organisations , as a complement to the Quality
Frameworks published previously by WG3.
Abbreviations
Abbreviation Meaning
EC European Commission
ITPS Intelligent Truck Parking Services
ITS Intelligent Transport Systems
MMTIS Multimodal Travel Information Services
NAP National Access Point
NAPCORE National Access Point Coordination Organisation for Europe
RTTI Real-Time Traffic Information Services
SRTI Safety-Related Information Services
WG Working Group
[page 3]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 3
Table of contents
1. Introduction................................ ................................ ................................ .......................... 4
2. Context ................................ ................................ ................................ ................................ . 5
3. The actors and roles in Quality Assessment ................................ ................................ ........... 6
3.1 NAP operators .......................................................................................................................... 6
3.2 Data providers .......................................................................................................................... 6
3.3 Data consumers........................................................................................................................ 7
3.4 National Bodies ........................................................................................................................ 7
3.5 Other neutral organisations ..................................................................................................... 8
4. Basic principles for Quality Assessment ................................ ................................ ................. 9
4.1 Perform quality assessment in different stages of data provision chain/process................... 9
4.2 Establish different types of errors and relevant errors management ..................................... 9
4.3 Define what exactly is being assessed ................................................................................... 10
4.4 Provide proper and sufficient documentation....................................................................... 11
5. Overview of assessment methods ................................ ................................ ....................... 13
Method 1: Cross-check or reference-check analysis ......................................................................... 14
Method 2: Logical and syntactic validation ....................................................................................... 15
Method 3: Visual check ...................................................................................................................... 16
Method 4: Data user/consumer feedback ......................................................................................... 17
Method 5: In-Depth Metadata Evaluation ......................................................................................... 18
Method 6: Self Evaluation .................................................................................................................. 19
Method 7: Contextual use of an additional data source ................................................................... 20
6. Conclusions and next steps................................ ................................ ................................ .. 21
[page 4]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 4
1. Introduction
Task 3.2 of the NAPCORE project is addressing the fourth objective of NAPCORE WG3 according to the
Grant Agreement: “Set a robust framework for and bring into practice the evaluation of European NAP
platforms’ data quality.” This is achieved by a sequence of work items oriented: a) to set up data quality
assessment frameworks, and b) to clarify how these frameworks can be practically applied.
The first work item, the elaboration of Quality Frameworks, was concluded in a previous Milestone
M3.8, represented by a set of Quality Frameworks for the assessment of NAP (meta)data quality and
published at an Online Repository1.
This report addresses the second work item, the practical application of the Quality Frameworks. It
serves as a complementing Milestone M3.9.
The main goal of this work item is to explore efficient and practical ways to assess individual NAP
(meta)data. So far, t here has been a lack of experience and common understanding on how to do
Quality Assessments in the NAP context, e.g., based on the above-mentioned Quality Frameworks.
To fill this gap, this report called “Quality Framework Application Guideline” summarizes basic
concepts and methods for operational Quality Assessments to be undertaken at responsible
organisations. It involves best -practice research and practitioners’ expertise. This guideline also
accounts for various constellations regarding (meta)data provision and organisational setups . The
assessment objects in this context are (meta)datasets , as provided on NAPs or other mobility data
portals.
The guideline is mainly based on pilot Quality Assessments as realised in the former M3.8 elaborations.
In such pilots, selected NAP (meta)data sets were assessed via dedicated methods. This way, specific
Quality Assessments were demonstrated in real-life environments. Other methods were derived from
previous research and works on the quality matter, and from expertise of NAPCORE stakeholders.
Other inputs for this work are gathered from parallel NAPCORE activities, such as the NAP Reference
Architecture work and DATA4PT guidelines.
1 https://napcore.eu/quality/
[page 5]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 5
2. Context
The contents of potential Quality Assessments in the NAP domain have been defined by Quality
Framework (QFs) by NAPCORE. These QFs represent a set of definitions for actors dealing with NAP
(meta)data quality. In each QF, individual quality criteria and quality levels are defined, but also
recommendations and showcases how those criteria and quality levels can be assessed. The
expectation behind these QFs is that Quality Assessments are conducted by responsible data managers
at organisation s which provide ( meta)data on NAPs, and that results from these assessments are
exposed to potential data consumers.
Any Quality Assessments (in the mobility domain and elsewhere) usually rely on concrete data-driven
methods. Examples for such methods include the monitoring of equipment performance and
availability; reference testing (e.g. against ground-truth data), and surveys of perceived quality by data
users.
Any assessment method can be applicable for different uses and for studying different quality criteria.
Further, each method involves different prerequisites and resources ( e.g., staff and IT tools), is
addressed to different target groups (e.g., internal quality managers, or external data users) and has
different set-ups (e.g., embedded in regular data -processing workflows, or outsourced in occasional
quality audits).
For a practitioner, it might be difficult to set up a procedure for a concrete Quality Assessment, i.e.,
identify applicable roles, approaches and methods for a concrete assessment setting. Thus, this
guideline compiles relevant application guidance, as cited in the QFs by NAPCORE, or presented in
other sources, in one central document.
It presents relevant actors and roles in Quality Assessment (chapter 3), basic principles (chapter 4) and
concrete methods (chapter 5). Altogether, it s erves as hands -on guidance for practitioners of data
quality management in the NAP and mobility domain.
[page 6]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 6
3. The actors and roles in Quality Assessment
In this chapter, we have compiled the most relevant actors and their recommended roles in Quality
Assessment. As actors, we have defined: NAP operators, data providers, data consumers , National
Bodies and other neutral organisations . As roles, we have defined recommended actions with two
obligation levels: “should” and “may”.
This compilation is based on experience and common practice at the NAP actor community, as
represented by NAPCORE. The main input here are the NAP Reference Architecture 2, guidance
documents by DATA4PT3 and NAPCORE guidance for National Bodies4.
3.1 NAP operators
- Should incentivise data producers to provide correct data: complete, quality -assured, and
valid on syntactic and semantic levels.
- Should provide instructions to data providers. In particular, a unified understanding of what
to publish and a unified way to verify the quality of the dataset should be defined.
- NAP operators often do not have the responsibility of content data provided on a NAP, or they
cannot give full instructions. However, they should indicate to data providers what should be
reported as metadata elements. In this case, the quality is focused on data structure (schema,
profiles,…) and metadata population, not on content.
- Should allow for cross-referencing of datasets to relevant other datasets that are temporal or
spatial in nature. E.g., this might be t he timetable of the upcoming year, the timetable of a
neighbouring region, or an adjacent data theme. This way, datasets can be compared and
complemented by data users.
- Should give guidance on the management of relevant ID s (i.e., IDs of data entiti es or the
dataset itself) and management of metadata
- Should provide a feedback channel (e.g., a GUI button or an e-mail address) for
questions/issues about (a) the NAP in general or (b) individual datasets . For (b): contact
information to the data provider must be saved per dataset (optimally, as part of the
metadata).
- May provide an issue tracker (to report a problem and track the solution) or a user forum
(enabling a user discussion) for investigations of quality issues.
- May provide own quality checking processes, e.g., as the French NAP does for GTFS data
feeds. For such cases, data providers should have access to the results of the quality process.
- May allow for an upstream communication about quality issues towards data providers. This
can be do via an issue tracker and/or user forum (see above), and/or be forwarding specific
problems towards the responsible data provider.
3.2 Data providers
- Should consult guidelines or best-practices on data quality (such as the NAPCORE Quality
Frameworks5 or the TISA 5-Star-Rating6) before publishing data.
2 NAPCORE, 2025: “Harmonized EU NAP architecture”, Milestone 2.11 report
3 https://data4pt.org/w/index.php?title=National_Access-Points
4 https://napcore.eu/activity-wg5-national-bodies-and-compliance-assessment/
5 https://napcore.eu/quality/
6 https://tisa.org/successful-rtti-5-star-rating-evaluation-methodology-workshop
[page 7]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 7
- Should publish relevant information about data/services (e.g., metadata) and information on
the data quality at the NAP.
- Should analyse and validate data quality before sharing it with the NAP. May repeat s uch
quality analyses and validations on a regular basis.
- For dynamic data: should ensure that data is updated at the appropriate and recommended
time intervals.
- For dynamic data: should report current/planned quality integrity issues (due to, e.g.,
temporary maintenance) in time to data consumers.
- Should publish data in a prescribed format, as defined in the EC Delegated Regulations.
- Should ensure that published data is updated at the appropriate and recommended time
intervals.
- Should be able to contact the data consumer and to respond to consumers’ feedback.
- Should p ublish content based on requirements from the Delegated Regulations under the
FRAND conditions, fulfilling implicit requirements like completeness and timeliness.
- Should assist the N ational Bodies/Compliance Assessments when performing a compliance
assessment and correct any issues found promptly.
3.3 Data consumers
- Should check quality descriptions before consuming data
- Should ensure timely and accurate integration of the subscribed content to their products
and services.
- Should provide feedback on data quality issues found , using the NAP features for user
communication (see section 3.1), including:
o Communicating proposals to solve issues.
o Telling reasons to data providers when datasets are rejected/or without value
o providing insights from own (cross-) validation, e.g., from end users
- May express specific user requirements through relevant fora, e.g., via NAPCORE stakeholder
activities
3.4 National Bodies
- Should evaluate whether reported data quality matches with actual data quality.
- Should randomly and regularly check the compliance of CPs and the NO with the Delegated
Regulations (i.e., data and metadata are compliant and processes of sharing the data and
reporting are compliant with the rules set up by Delegated Regulations).
- Should use NAPCORE quality frameworks7 for dedicated (meta)data and service assessments
- Should follow up on non-compliant results, and report results to the MS and NO.
- Should collaborate with CP to reach a successful Compliance Assessment.
- Should identify and contact entities obliged to publish (meta)data to the NAP
7 https://napcore.eu/quality/
[page 8]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 8
3.5 Other neutral organisations
- May facilitate stakeholder fora and platforms to discuss and define quality criteria and levels
for specific data domains, such as the NAPCORE Quality Group or the TISA 5-Star-Rating
activity.
- May provide tools for quality checks and quality reports, such as the online validator tools
available for multimodal data formats8.
- May execute independent assessment checks or regulatory actions towards data providers,
such as French authority responsible for the assessment of implementation of the MMTIS
Regulation (L’Autorité de régulation des transports (ART)9).
8 see the NAPCORE MMTIS Quality Framework at https://napcore.eu/quality/
9 https://www.autorite-transports.fr/
[page 9]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 9
4. Basic principles for Quality Assessment
This chapter presents some basic principles for Quality Assessment . These are rules and approaches
defined above the level of concrete assessment methods, which are defined in the subsequent
chapter.
4.1 Perform quality assessment in different stages of data provision chain/process
The provision of data to NAPs is one of the last stages of the data production and provision chain.
Previous stages concern the production and collection of the data from the source, the processing
(aggregation or other actions) and the final supply to the end user/consumer or the entity which may
evaluate the implementation of the NAP. Different actors can be involved and depending on the
country the NAP operator might have several roles in this chain.
The best practice is to perform quality checks in different stages to capture errors and inconsistencies
early enough to be able to correct them efficiently. At each stage different quality criteria are assessed
via different methods.
For example, this practice is adopted by Austrian Mobility Database, see the next table The NAP in this
case is involved in the stage 3 of checks “during data supply and provision”.
Table 1 Quality assessment in different stages of data collection and provision chain - the approach from Austria.
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
This principle is discussed in the NAPCORE MMTIS Quality Framework, including further examples10.
4.2 Establish different types of errors and relevant errors management
There are different types of errors that can appear during the data quality process. Some of those are
critical and some are not so critical. Depending on the significance of the errors, a different quality
management is required. For example, for some errors, the harvesting of dataset might stop, while for
some other errors, the dataset might be adopted.
10 see the NAPCORE MMTIS Quality Framework, section 6.2.1., available at https://napcore.eu/quality/
[page 10]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 10
The exemplary approach of Austria indicates three types of errors: a) critical error, b) error, c) warning.
If a critical error is detected, it stops the harvesting of the complete data set while when an error is not
critical (generating a warning) the data can be published.
This principle is discussed in the NAPCORE MMTIS Quality Framework, including further examples11.
4.3 Define what exactly is being assessed
When assessing quality in the context of NAP data (or, in general, of mobility data), some confusion
might arise about what exactly is being assessed. Thus, a clear and exact definition of the assessment
object(s) is necessary.
Depending on the assessment setting, different assessment objects are possible.
The following figure shows exemplary assessment objects in the scenario where parking data is
exchanged via a data portal. In such scenario, multiple elements are involved: real-life entities (e.g., a
parking facility), data elements related to one facility (e.g., “name”), groups of entities combined under
one dataset, and additional metadata (e.g., “license”).
Figure 1 Data exchange scenario for parking data (based on Lubrich, 202112)
In such scenario, a quality assessment could be executed for one or more objects:
Figure 2 Potential assessment objects in the above scenario
11 see the NAPCORE MMTIS Quality Framework, section 6.2.2., available at https://napcore.eu/quality/
12 https://doi.org/10.1177/03611981211031878
B
A
C
D
[page 11]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 11
• Assessment object A: One unique data element across multiple entities (e.g., are the “names”
of all reported parking facilities correct?)
• Assessment object B: All data elements for one entit y (e.g., are all elements for one parking
facility complete?)
• Assessment object C: The entire data set (e.g., do all entities and their data elements comply
with a given data scheme?)
• Assessment object D: The corresponding metadata (e.g., is the metadata complete and
correct?)
• Or variants or combinations of the above
Such definition is usually done by the assessor before the actual assessment. The chosen assessment
object(s) affect the scope and also the explanatory power of the assessment. In any case, the definition
of the assessments object(s) must be clearly documented.
4.4 Provide proper and sufficient documentation
When documenting the assessment, not only the pure assessment results should be reported but also
any context and background information. This might include a detailed description of the applied data
sources, the calculation methods and other circumstances during the calculations.
Such comprehensive documentation will enable the data consumer to interpret the assessment results
correctly, detect any biase s or other implicat ions, and utilize the findings for a (potential) data
consumption.
In practice, we recommend a “Quality Statement” should be provided as an attachment to each
individual dataset. Such “Quality Statement” should include the following items:
• Author of the Quality Statement
• Date of the Quality Statement
• Definition of the assessment object(s) (see the previous section)
• Quality Criteria and Metrics being calculated, each with:
o Concrete definitions (ideally, referring back to the NAPCORE Quality Frameworks)
o Calculation methods
o Temporal and spatial scope of calculation
o Calculation results, including statistical measures such as averages or deviations
• Any auxiliary information (e.g., identified outliers)
• Feedback/contact channel to the author
This Quality Statement should be published as part of the metadata of the dataset being assessed. This
might be a downloadable PDF report or a free -text metadata, but should be accessible to any
interested data consumer.
The mobilityDCAT-AP data model, being a metadata specification for NAPs and mobility data portals,
provides a dedicated metadata field “Quality Description”13 where the Quality Statement can be saved
under.
The following figure shows how the field “Quality Description” can be populated at a GUI of a real data
platform, here at the NAP in Germany.
13 https://mobilitydcat-ap.github.io/mobilityDCAT-AP/releases/index.html#dataset-quality-description
[page 12]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 12
Figure 3 Example of Quality Information as part of the GUI at the German NAP
[page 13]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 13
5. Overview of assessment methods
In the following tables, relevant assessment methods are presented in a structured way, i.e., describing
the following aspects per method:
• Method Description
• Data requirements
• Examples
• Applicability
• Usage
• Recommendation
• References
Please note that several references are made to NAPCORE Quality Frameworks (QFs), which are all
available at the NAPCORE Quality Online Repository 14. These QFs provide more details and examples
on the methods presented below.
14 https://napcore.eu/quality/
[page 14]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 14
Method 1: Cross-check or reference-check analysis
Method
Description
A comparative analysis of multiple independent data sources describing the
same object(s) in the mobility system.
Data
Requirements
At least two independent data sources about the same information with the
same temporal and spatial context.
Examples Static and dynamic on-street parking data for a district of Hamburg, Germany,
were analysed via a comparison of six data sources.
Static data about a Low Emission Zone in Lisbon, Portugal, was cross-checked
between a DATEX II dataset form the UVAR Box Tool and the Traffic
Regulation Order from the Municipality.
Delays and disruptions are compared via two data sources: road perspective
(DATEX II) and public transport view (SIRI).
Applicability Scope: Quality assessment
Type of data: Status or event data
Type of process: Offline and online
Parts of value chain: Content detection + Content processing
Covered quality criteria: All mentioned in the UVAR and Parking Quality
Frameworks, e.g., location accuracy and Completeness
Usage Objective: Check the consistency of information given in multiple data
sources, in case of inconsistencies: analyse gaps and deltas and derive quality
problems.
Stage: Operation + problem resolution / diagnosis
Rate of use: Single or spot check in case of problems
Example: Data sources used for cross-check analysis of parking data in Hamburg, Germany
Recommendation: The cross-check method allows for unambiguous quality metrics about a tested
dataset derived from comparisons with alternative datasets. It results in unambiguous metrics such
as error rates. Many of the required calculations are mathematically straight -forward and can be
easily replicated. Special caution needs to be paid to finding a trustful reference dataset. External
data sources might need to be tested first (e.g., commercial FCD). Further, it is not always evident
which data source can be considered ground -truth. Even a manual survey might have errors. Thus,
special care needs to be taken during analysis and interpretation.
Transaction data from parking
meters
Transaction data from
mobile phone applications
Sensor data
Parking API
Geoportal Hamburg
Manual survey
[page 15]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 15
Method 2: Logical and syntactic validation
Method Description Validation tools have capabilities to validate the dataset against the
relevant standards and their profiles. The most basic check is to
confirm that the XML schema and the format of the dataset is correct
and there are no syntactic errors. Additional rules can be applied to
verify specific requirements (e.g., if compared with national profiles)
and to check logical precision (e.g., “distance between stops is very
small/very big depending on the transport mode”, “PT vehicles arrive
at final stop before leaving previous stop” etc.).
Data Requirements All type of data depending on the validator.
Examples Validators for public-transport data are used in several countries:
Finland, Norway, Austria, France, etc. Examples are given by
DATA4PT15. An XML validator to verify the compatibility of a LEZ
dataset from the Municipality of Lisbon with the recommended UVAR
DATEX II profile from the DATEXII standard.
Applicability Scope: Quality assessment
Type of data: Static and dynamic data, depending on the validation
rules and tool.
Type of process: Offline and online (depending on the tool capabilities
and NAP approach)
Parts of value chain: Content detection / Content processing / Service
provision/ Service presentation
Covered quality criteria: Compatibility checks; Completeness (if
compared against the relevant national or EU profile); Logical Precision
correctness (see MMTIS QF)
Usage Objective: To ensure that the data is interoperable and accurate
Stage: Acceptance test/ operation/ problem / diagnosis
Rate of use: Depending on the validation tool, but most of them
periodic and/or continuous use
Example: validator GUI at the French NAP
Recommendation: Validation tools allow for automated and continuous checks about schema
conformity and other pre-defined rules. Many open-source tool environments are available. NAP
operators are advised to check and adopt existing validation tools available at other NAPs.
15https://data4pt.org/w/index.php?title=NeTEX#Software_&_tools_%F0%9F%A7%B0,
https://data4pt.org/w/index.php?title=SIRI#Software_&_tools_%F0%9F%A7%B0
• Producers shall complete a declaration
regarding regulatory requirements
(declaration of compliance)
• Data published are automatically
checked by validation tools
and documentation on standards and
national profiles are available for
producers.
• the GTFS datasets provided are
automatically converted in NeTEx by
the NAP.
• Producers mainly use the odbl licence
or NAP open licence.
NAP in France
[page 16]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 16
Method 3: Visual check
Method Description The visualisation maps enable the assessment of data in a manual way.
They are meant to detect obvious inconsistencies or abnormal
situations in the circulation of the vehicles and the network elements
(like stops, stations etc.). Major errors regarding stop points, or journey
patterns might be detected visually.
Data Requirements Any geo referenced data, i.e., datasets containing coordinates or other
locations (stop places, stations, points of interest etc.).
Examples Norway: New modes visualization map (floating vehicles and docking
stations)16 ; Scheduled-modes vehicles visualization map17
Applicability Scope: Quality assurance of data where meaningful for human user
visualisation can be developed
Type of data: Location related (stop points for example) and traffic
related (actual vehicle position etc.)
Type of process: Offline and online (depending on the tool capabilities
and NAP approach)
Parts of value chain: Content processing, service provision, service
presentation
Covered quality criteria: Logical Precision / Correctness (see MMTIS QF)
Usage Objective: To detect major errors regarding position related data.
Stage: Problem diagnosis
Rate of use: Depending on the tool and the nature of data. For real
time data: continuous; for static data: periodic (every time a change is
indicated).
Example: screenshot from the Norwegian vehicles visualization map
Recommendation: Visualisation tools are effective ways for manual inspection of geo-referenced
data. As some NAPs have already deployed such tools , NAP operators are advised to check and
adopt existing visualisation tools available at other NAPs.
16 https://mobility-map.entur.org/
17 https://vehicle-map.entur.org/
[page 17]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 17
Method 4: Data user/consumer feedback
Method Description This method is based on the data user’s experience when utilising the
data. Any relevant feedback can contribute to the improvement of data
quality, once communicated back to the data provider. To facilitate
this, technical feedback channels, issue trackers or user fora can be
installed at a NAP platform, see section 3.1. The NAP itself might also
be the consumer of the provided data and thus generate its own
feedback. Feedback can be either generated by data users (e.g., when
they encounter quality issues) or collected proactively by the data
provider or the NAP operator (e.g., via questionnaires).
Data Requirements Data and metadata, as it can retrieved from a NAP
Examples The proFund project18 provides an online tool “Roadwork Check” to
collect users’ feedback on the correctness of individual roadwork
messages published on the German NAP.
A NAP monitors that some published NeTEx datasets are not consumed
at all. It also detects that these datasets non-valid XML files. The NAP
will contact the responsible data provider and inform about the
prevailing non-conformity.
Norway (ENTUR) and Austria collect user’s feedback with questions
such as: To what extent has the data you have accessed been useful?
How satisfied are you with the services NAP provides regarding data
quality assessment?
Applicability Scope: Quality assurance
Type of data: Any
Type of process: Offline and online
Parts of value chain: Service provision, service presentation
Covered quality criteria: Any
Usage Objective: To derive quality issues from data user’s experience
Stage: Problem diagnosis
Rate of use: Occasionally or regularly (for questionnaires)
Example: screenshot from the proFund Roadwork Check
Recommendation: Collection of direct user feedback can support he quality assessment of a n
operating service. It is a relatively easy way as actual users are the main source of quality
information. Because the method provides only isolated and ex-post quality insights, the quality
management should be complemented with other methods, in particular, more continuous and
ex-ante methods.
18https://bmdv.bund.de/SharedDocs/DE/Artikel/DG/mfund-projekte/meldungsqualitaet-baustellenprofund.html
[page 18]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 18
Method 5: In-Depth Metadata Evaluation
Method Description This corresponds to the evaluation method [web/manual/doc/formal],
as defined by the Cross-Domain Quality (CDQ) QF. It is a manual check
on how well the data is described on a NAP, looking at the metadata
population of the assessed data set.
Data Requirements Metadata of an assessed data set, as published on a NAP.
Examples NAPCORE partner CERTH has evaluated 39 catalogue records (sample
NAP metadata sets), using the CDQ methodology. The results are
published in tabular format at the 'NAP Browser'.
Applicability Scope: Quality assessment
Type of data: Metadata
Type of process: Offline and online
Parts covered: Content detection + Content processing
Covered quality criteria: Availability, completeness, and usability of the
metadata.
Usage Objective: Manual assessment of all parameters against the evaluation
criteria, using the CDQ framework.
Stage: Operation + problem resolution / diagnosis
Rate of use: Single or spot check in case of problems.
Screenshot of the evaluation sheet of the Evaluation Form in the CDQ methodology
Recommendation: This is an efficient method with the goal to learn about the usability and
applicability of data sets and data services, BEFORE such data and services are acquired by a data
consumer, thus ensuring transparency and ex -ante quality. The tooling is ready to use, see the
CDQ framework for documentation and spreadsheets. The outputs, using a scoring system, give a
clear and neut ral indication on the expected quality. Results are stored centrally and may be
published online.
[page 19]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 19
Method 6: Self Evaluation
Method Description This assesses the quality of a dataset using its own internal
characteristics rather than external validation sources. It is a direct
approach that examines key quality dimensions and criteria such as
completeness (temporal and content completeness), timeliness,
granularity, and sampling rate. This method may prove particularly
useful for particular quality dimensions and criteria in case that
external ground truth data is unavailable or difficult to integrate.
Data Requirements The dataset being evaluated. No additional data needed.
Examples Assessing the temporal completeness of a dynamic traffic information
service by verifying gaps (missing values) in time-series data.
Evaluating the completeness of an Urban Vehicle Access Regulation
(UVAR) dataset by comparing its structure to the required information
set.
Evaluating the number and types of events covered by an SRTI/RTTI
data source.
Applicability Scope: Quality assurance and quality assessment
Type of data: Dynamic datasets, in particular datasets with continuous
updates, such as real-time traffic data, geospatial information, or
sensor-based measurements.
Type of process: Offline and online
Parts covered: Content processing
Covered quality criteria: Completeness, Timeliness, Granularity,
Sampling rate
Usage Objective: To understand some aspects of the data source that shape
its applicability in specific use cases.
Stage: Operations
Rate of use: Continuous or periodic, depending on the level of required
quality inspections.
Example: missing records analysis from the FCD QF
Recommendation: Self-evaluation is useful for data providers to internally assess the quality of
their datasets before making them available. The benefit is that data providers can proactively
identify data gaps, inconsistencies, or anomalies, to reduce the risk of delivering low -quality
datasets. It is further a cost-effective and efficient approach, especially when external reference
or benchmark datasets are unavailable, such as traffic sensor data, GIS layers, or statistical records.
In such cases, self-evaluation ensures that at least the internal consistency and structural integrity
of the dataset are verified without requiring external validation sources.
[page 20]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 20
Method 7: Contextual use of an additional data source
Method Description This method involves using an additional data source to obtain
essential contextual information required for quantifying specific
quality metrics that cannot be directly derived from the primary
(evaluated) dataset. Rather than serving as a benchmarking tool for
comparison (see Method 1), the additional data source provides
complementary data necessary for evaluating aspects such as
penetration rate, spatial coverage, network coverage, and fleet
representativeness. For example, in the case of FCD, it is impossible to
determine the penetration rate without an independent reference
such as loop detector counts or aggregate vehicle flow data. Similarly,
when assessing the completeness of geospatial datasets, an
authoritative road network dataset may be required to establish
whether all relevant infrastructure is covered.
Data Requirements At least one external dataset other than the evaluated one depending
on the context.
Examples Using inductive loop detector data to quantify the penetration rate of
FCD-based travel time data.
Using geospatial data to estimate the network coverage of traffic
information service.
Applicability Scope: Quality assurance and quality assessment
Type of data: Static and dynamic traffic data, including spatial datasets.
Type of process: Typically used in offline validation tasks
Parts covered: Content detection
Covered quality criteria: Spatial coverage, network coverage,
penetration rate, fleet composition (see FCD QF)
Usage Objective: To gain insight into the coverage of a data source and the
extent to which is representative of the real-world conditions.
Stage: Acceptance testing, operational monitoring, diagnosing data
issues.
Rate of use: Can be used periodically (e.g., during audits or
performance evaluations) or continuously (e.g., real-time fusion with
external datasets).
Example: penetration rate analysis from the FCD QF
Recommendation: This method is especially relevant for data providers responsible for
monitoring the quality of ITS -related data at a national level. It provides a stronger validation
approach than self -evaluation by incorporating an additional data source to support the
quantification of additional quality metrics that cannot be derived directly from the evaluated
dataset itself.
[page 21]
Quality Framework Application Guideline
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 21
6. Conclusions and next steps
The NAPCORE project has provided a wide range of guidance, references, and tools with the goal to
assess and ensure the quality of (meta)data, as provided on NAPs. The work done is based on extensive
stakeholder engagement, evidence from data usage in real -world environments, and knowledge
collected from literature and other projects.
The more tangible products of NAPCORE’s quality activity are a set of Quality Frameworks and this
Application Guideline. All products are made available to the public via a dedicated Online
Repository19. These outputs represent the current state of quality management for ITS and mobility
data. They also fill some knowledge gaps, represent the current consensus among relevant
stakeholders, and provide orientation to actors dealing with the quality topic.
It is evident that the quality issue will remain one o f the most relevant enablers ( and bottlenecks) in
the creation of efficient ITS and mobility data ecosystems in Europe, also following the various legal
frameworks set out by the EC.
Many ongoing trends will give further momentum but will also provide new challenges for the quality
topic. These trends include artificial intelligence, emerging data sources and new data use cases, as
well a constantly converging data ecosystem with a broad and heterogenous stakeholder landscape.
To this end, discussions, collaboration, and concrete actions on the quality matter will be continued in
the upcoming NAPCORE -X phase. Specific quality topics noted in the proposal for the NAPCORE -X
project include:
- Discussing quality aspects at the strategical and tactical level among stakeholders in road &
traffic information and management sector.
- Continue working on a sustainable and coherent data quality framework for the full scope of
the EU Delegated Regulations.
- Embedding the quality perspective in the development of (meta)data standards and digital
tools assisting in the value chain
- Defining best practices for quality management
- Aligning with the sectoral data quality standards such as the TISA 5 -star rating model and
comparable actions done in the RTTI-taskforce and emerging EU projects like TISGRADE
Future actions and results by the NAPCORE Quality Activity will be regularly reported via the NAPCORE
website and social media channels.
19 https://napcore.eu/quality/
