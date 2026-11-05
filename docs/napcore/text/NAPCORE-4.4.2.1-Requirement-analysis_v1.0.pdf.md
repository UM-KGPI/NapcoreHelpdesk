url: https://napcore.eu/wp-content/uploads/2022/08/NAPCORE-4.4.2.1-Requirement-analysis_v1.0.pdf
title: NAPCORE 4.4.2.1 Requirement analysis v1.0

[page 1]
Requirements Analysis for a new Metadata
Specification
A Report by subWG 4.4: NAP Metadata
Status: Final
Version: 1.0
Date: June 14, 2022
Legal disclaimer
The sole responsibility for the content of this document lies with the authors. It does not necessarily
reflect the opinion of the European Union. The European Commission i s not responsible for any use
that may be made of the information contained therein. All images are pro vided by the respective
partners (unless otherwise noted) and are approved for reproduction in this publication.
[page 2]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 2
Document information
Project acronym NAPCORE
Full project title National Access Point Coordination Organisation for Europe
Grant Agreement No. MOVE/B4/SUB/2020-123/SI2.852232
Activity no. and title subWG 4.4. NAP Metadata
Author(s) Petr Bureš, RSD; Peter Lubrich, BASt
Co-author(s) Antonia Azzini / Marco Comerio / Mario Scrocca, Cefriel /
Chrystomonos Mylonas, CERTH
Related to Milestone no. none
External Milestone no
Document history
Version Date created/ modified by Comments
0.1 01.04.2022 Petr Bureš (CZ/RSD) Iteration 1
0.2 22.04.2022 Peter Lubrich (DE/BASt) Iteration 2
0.3 17.05.2022 Petr Bureš (CZ/RSD), Peter
Lubrich (DE/BASt)
Iteration 3
0.4 20.05.2022 Petr Bureš (CZ/RSD), Peter
Lubrich (DE/BASt),
Chrysostomos Mylonas
(GR/CERTH)
Iteration 4
0.5 20.6.2022 Petr Bureš (CZ/RSD) acceptance and reaction to received
comments
1.0 20.6.2022 Petr Bureš (CZ/RSD) final release
Action requested
☐ To be revised by partners involved in the preparation of the document
☐ For review/ approval by the Core Alignment Team
☐ For approval by the NAPCORE Steering Committee
[page 3]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 3
Abstract
The main objective of SWG 4.4 is to develop a “napDCAT-AP” specification, being an RDF-compatible
representation of an agreed, Europe-wide metadata set for NAPs. The present report is a deliverable
by Work Item “4.4.2.1 - Requirements analyses”, being a preparatory work for napDCAT-AP. The goal
is to identify and to prioritise any requirements that need to be addressed by napDCAT-AP. The main
outcome is a consolidated and structured table of requirements that will be considered by follow-up
work of this SWG, namely the preparation and development of the napDCAT-AP data model and
documentation.
Abbreviations
Abbreviation Meaning
EC European Commission
DCAT Data Catalogue Vocabulary
DCAT-AP DCAT Application profile for data portals in Europe
CMC Coordinated Metadata Catalogue
NAP National Access Point
NAPCORE National Access Point Coordination Organisation for Europe
SWG Sub-working Group
[page 4]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 4
Table of contents
1 Introduction ....................................................................................................................................5
2 Methodology ...................................................................................................................................6
2.1 Literature review ...................................................................................................................... 6
2.2 Collection of SWG 4.4 partners’ individual requirements ......................................................... 6
2.3 Collection of inputs from experts ............................................................................................. 8
2.4 Consolidation ........................................................................................................................... 9
3 Requirements analysis .................................................................................................................. 10
3.1 Requirements from the literature review ............................................................................... 10
3.2 Requirements from SWG 4.4. partners ................................................................................... 10
3.3 Requirements from experts' input .......................................................................................... 12
4 Requirements consolidation.......................................................................................................... 14
5 Summary ....................................................................................................................................... 20
Annexes (see separate document)
Annex 1 Individual requirements by SWG 4.4. partners
Annex 2 Structured Literature Review
Annex 3 Experts’ inputs
List of tables
Table 1: Requirements consolidation table ....................................................................................... 15
List of figures
Figure 1: Template for literature review .............................................................................................. 6
Figure 2: Template for individual requirements ................................................................................... 8
Figure 3: Example for a requirement response .................................................................................. 11
Figure 4: List of domain-specific profiles for DCAT-AP (© DCAT-AP) .................................................. 12
Figure 5: Front page of the Coordinated Metadata Catalogue document by EU EIP ........................... 13
[page 5]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 5
1 Introduction
The present report is a deliverable by Work Item “4.4.2.1 - Requirements analyses”, being part of the
NAPCORE sub working-group (SWG) “4.4 - NAP Metadata”.
The main objective of this SWG is to develop a “napDCAT-AP” specification, being an RDF-compatible
representation of an agreed, Europe-wide metadata set for NAPs, based on the Coordinated
Metadata Catalogue (CMC), and parallel DCAT-AP specifications. The CMC is an elaboration for NAP
metadata harmonisation under the former EU EIP project1. DCAT-AP is a well-established metadata
specification in the domain of European Open Data portals, developed by a joint initiative of the EU
organizations DG DIGIT, DG CONNECT and the EU Publications Office2.
Before working on a first napDCAT-AP version, some preparations, i.e., analytical and conceptual
works are needed first. Work Item 4.4.2.1 is one of such preparations. The goal here is to identify and
to prioritise any requirements that need to be addressed by the upcoming napDCAT-AP specification.
The Work Item was executed between November 2021 and May 2022. It was led by NAPCORE
partner RSD (CZ), with contributing partners from BASt (DE) and Cefriel (IT).
The work is mainly based on a literature review, SWG 4.4 partners’ views and external experts'
inputs. For the literature review, we assumed that there are already many references that imply
relevant requirements. These references might be previous research works, policy documents, or
project documentation. Relevant references were collected from SWG members, and then
structurally analysed via a template, containing a brief description of the reference, its purpose and
its relevance for our work. For the SWG 4.4 partners’ views, we collected individual requirements by
looking at different perspectives in the NAP context, again using a template. For the experts' inputs,
we consulted various experts working on the metadata topic, including authors from CMC, the DCAT-
AP developers' group, and selected NAP representatives.
The main outcome is a consolidated and structured table of requirements that will be considered by
follow-up Work Items of this SWG, namely the preparation and development of the napDCAT-AP
data model and documentation. The elicited list of requirements is also a “specification sheet” for
our upcoming work, as it describes expected technical, organisational and functional features of
napDCAT-AP.
1 https://www.its-platform.eu/achievement/monitoring-harmonisation-of-naps/
2 https://joinup.ec.europa.eu/solution/dcat-application-profile-data-portals-europe/about
[page 6]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 6
2 Methodology
The goal of the document is to collect initial requirements for the definition of a metadata profile
supporting the description of datasets published in European NAPs. In order to provide a rich picture,
we have approached the analysis from 3 different viewpoints:
1. Literature review: Analysis of available literature, legislature, projects, and technical
documentation, with a focus on metadata aspects,
2. SWG 4.4 partners’ individual requirements, and
3. unstructured inputs from experts.
2.1 Literature review
For the literature review, we provided a master template and asked SWG 4.4 partners to review
relevant literature, and summarise it using this template. Each reviewer was asked to upload the
reviewed literature in a specific folder, and to describe his/her findings in the master template,
containing:
• Intended audience (all project partners)
• Purpose of the document
• Methodology
• Literature review template itself
The key part of the review was a short commentary on its content and indication of applicability for
the metadata topic. The structure of this template is shown in Figure 1.
Figure 1: Template for literature review
The requirements coming from the literature review were then processed in terms of relevant
sources and contents. These are described later in Chapter 3.1.
2.2 Collection of SWG 4.4 partners’ individual requirements
For the collection of requirements by individual SWG 4.4. partners, we initially defined a procedure
to elicit requirements (presented at one of the SWG 4.4. meetings). The procedure was explained on
an example including:
1. Unstructured question by a stakeholder (e.g., a NAP developer in an implementation phase)
2. Unstructured response to this question, i.e. resolution of the potential problem
3. Formulation of a requirement based on the unstructured “question” -> “answer” pairs.
[page 7]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 7
Important for the requirements collection phase was to cover all stakeholders, therefore SWG 4.4
partners were asked to provide requirements, from their perspective:
• NAP developer: This perspective covers any issues when setting up a metadata catalogue in
an individual NAP system. Such a database is usually built upon a certain data model (data
fields, data types, data relationships etc.), for which our napDCAT-AP model should be a
baseline, for interoperability reasons.
• NAP metadata provider: This perspective covers any needs of persons inserting metadata
into a NAP, e.g., via a GUI. In many cases, the metadata provider is the same as the content
data provider. This person might look for aspects of, e.g., clarity and efficiency when entering
metadata.
• NAP metadata user: This perspective covers any needs of persons (or machines when using
APIs) who read or seek metadata from a NAP. This actor might look for aspects of, e.g.,
expressiveness or usefulness when consuming metadata.
• Metadata standard experts: Lastly, as we build upon existing frameworks of other metadata
specifications, we need to consider the experiences and expectations of experts from such
other metadata specifications. This is particularly true for DCAT-AP, which explicitly provides
guidelines and requirements for the extensions of DCAT-AP. The aspects considered here
mainly focus on interoperability issues.
The initial template was further elaborated into a final requirements template, that contains
additional fields used for classification and qualification of the requirement. The fields in the
template are: (see also Figure 2):
• Identification
o Identification: numeric or numeric with country information i.e., DE-01
o Date and contact information
• Description of the requirement: a short and concise statement including “what” and “why”
• Category of the requirement:
o Functional: requirements related to overall functionalities
o Technical: requirements related to technical aspects such as access, distribution,
vocabularies, etc.
o Other: any additional category classification needed by a stakeholder
• Perspective of the requirement (see above):
o NAP Developer
o Metadata Expert
o NAP metadata provider
o NAP metadata user
o Other: any additional perspective classification needed by a stakeholder
• Source of the requirement:
o Interview: requirement based on experts' interview
o Experience: requirement coming from the experience of the stakeholder when
planning, implementing or maintaining a NAP
o Project result: requirements collected as a result of a project focused on data sharing
and reuse (literature review mostly)
o Study: requirements collected from individual research papers or studies on data
sharing and reuse
o Other: any additional source classification needed by a stakeholder
• Notes: any interesting insight on why the requirement is important.
[page 8]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 8
Figure 2: Template for individual requirements
The requirements coming from the SWG 4.4. partners were then processed in terms of perspectives
and aspects considered. These are described later in Chapter 3.2.
2.3 Collection of inputs from experts
In this requirements collection input the active project members were asked to identify potential
experts from the fields of open data / DCAT community and from projects identified in the literature
review.
The experts should be interviewed by the partner to provide their insight / opinion regarding the
metadata requirements during the partially structured interview or a collaborative workshop. There
were no particular rules for the interview, the topics discussed should cover:
• Current state of the metadata in NAPs, potential improvements
• Practices regarding the metadata creation and governance that should be applied by NAPs
• Lessons to be learned from similar projects, how to involve the NAP community
• Any other aspect deemed important by the experts.
Chapter 3.3 summarizes the results of the interviews. Documents and responses collected during the
interviews shall serve as the input for consolidated requirements in Chapter 4.
[page 9]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 9
2.4 Consolidation
In the consolidation phase, the requirements were shortened and generalized. Similar requirements
coming from different sources were merged. Also, an additional categorization of requirements was
introduced to prioritise the activities of the SubWG 4.4:
• Mandatory requirements: Absolute must, as minimum
• Optional requirements: nice-to-have requirements but not necessary
The consolidation phase resulted in a “requirements consolidation table“, see Chapter 4.
[page 10]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 10
3 Requirements analysis
3.1 Requirements from the literature review
Overall, 50 different resources were analysed from different project members and from different
perspectives; 18 summaries were created with recommendations on usability. Resources were
grouped into 6 categories:
• Open data literature (4 documents)
• Legislature: PSI (1 document), Open Data (1 document), INSPIRE Directive (4 documents) and
data governance act, EU strategy
• DCAT-AP documentation, training webinars, and extensions documentation (several
documents, examples and documentation, presentations)
• EU-EIP metadata documents (several documents including coordinated metadata catalogue,
analyses, napDCAT-AP proposal etc.)
• Metadata standards and interoperability (several documents)
• Project results: SPRINT 3 and LOD project
The individual literature review is provided in Annex 2, Chapter 2.
Useful resources for our metadata work are mainly related to different phases of the metadata
specification, namely the planning, implementation and maintenance. In particular, we identified the
following metadata relevant contents (the chapters in brackets indicate the analysed resource):
• data contents in the transport context together with implementation rules and requirements
(Annex 2, Chapter 2.4)
• FAIR principles for data sharing (Annex 2, Chapter 2.2)
• requirements on development and sharing metadata (Annex 2, Chapter 2.5)
• contents of the catalogue and approaches to metadata (Annex 2, Chapter 2.6, 2.13, 2.15)
• information on how to build extensions (Annex 2, Chapter 2.7)
• metadata challenges and requirements (Annex 2, Chapter 2.10)
• overview of how to store and share metadata (Annex 2, Chapter 2.11)
• mappings between data concepts (Annex 2, Chapter 2.12)
• tools summary and existing ontologies comparison (Annex 2, Chapter 2.14)
• different requirements from national extensions (Annex 2, Chapter 2.16-17)
The information on requirements, coming from the identified, relevant resources, particularly from
the SPRINT project which focused on the analysis of metadata profiles for the transportation domain,
served as input to Chapter 4, i.e., the requirements consolidation.
3.2 Requirements from SWG 4.4. partners
Overall, 53 individual requirements were collected from 6 countries (BE, CY, CZ, DE, GR and IT), using
templates as shown above in Table 2. Even if this is only a small sample of all European countries, the
collected requirements still appear quite extensive, so the overall outcome presents a sufficient view
3 Semantics for PerfoRmant and scalableINteroperability of multimodal Transport (SPRINT) project
http://sprint-transport.eu/
[page 11]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 11
of relevant requirements. Of course, other requirements might arise during the future napDCAT-AP
elaborations, so our first collection might be extended later.
Any similarities between requirements were handled in the consolidation phase, see Chapter 4. An
example response is shown next.
Figure 3: Example for a requirement response
All individual responses are provided in Annex 2, Chapter 1.
The stakeholders classified the requirements into 6 types/categories:
• Content (new class): 18 requirements
• Existing vocabularies (new class): 6 requirements
• Functional: 14 requirements
• General (new class): 9 requirements
• Implementation (new class): 1 requirement
• Technical: 6 requirements
New requirement categories show that there is a need for more detailed classification and that
formerly provided categories (functional, technical) were not sufficient. We focused on
reclassification into relevant categories in the requirements consolidation phase.
With regards to the sources, stakeholders classified requirements accordingly:
• Own experience as NAP operator including implementation: 24 requirements
• Collected within specific projects:
o SPRINT Project: 10 requirements
o EU-EIP Project: 4 requirements
o CMC development (within EU EIP project): 9 requirements
o NAPCORE project (on-going activities): 1
• Experts' consultation: 12 requirements
• Studies: 1 requirement
[page 12]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 12
Most of the requirements were based on the individual experience of stakeholders closely followed
by requirements gathered within specific projects and interviews with experts. This finding is aligned
with the categorisation of requirements according to the stakeholder perspective:
• Metadata experts (developers): 15 requirements
• NAP developer: 14 requirements
• NAP metadata provider: 13 requirements
• NAP metadata user: 15 requirements
• Other perspectives: 5 requirements
With regards to a NAP developer, we assume that various NAP functions are related to a metadata
database, e.g., GUI interactions, administrative tasks for NAP operators, and metadata exchange with
parties outside the NAP system (via APIs or harvesting). Thus, a NAP developer and the NAP operator
might have special needs for the data model, which might be transferred into a requirement for
napDCAT-AP. The collected inputs are mainly based on current NAP developments in BE, CZ and DE.
Further, interesting insights were provided by responders via individual notes associated with a
requirement, where the rationale for the requirement is shortly summarized. This also allowed to
shorten the text of the individual requirement.
3.3 Requirements from experts' input
The main experts’ input came from an interview with the DCAT-AP developers' group. Before this
interview, members of our SWG joined regular meetings of this group, to figure out current concepts
and issues with DCAT-AP development, and to show presence in the DCAT-AP community.
Our envisioned napDCAT-AP specification is already recognised by the DCAT-AP group as a domainspecific profile, and listed in the DCAT-AP set of profiles (see the next figure). Thus, we expect that
napDCAT-AP might be a complementary element to the landscape of DCAT-AP extensions, serving
the needs of NAPs in particular, or of mobility data portals in general. However, we need to have a
closer look at related extensions, such as TransportDCAT-AP, and tackle possible overlaps.
Figure 4: List of domain-specific profiles for DCAT-AP (© DCAT-AP)
[page 13]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 13
We intensified this exchange in a bilateral meeting between the DCAT-AP group and NAPCORE
project partners. The meeting happened online on March 01, 2022. The goals of the meeting were
to:
• get to know the vision of the new DCAT-AP extension under the NAPCORE project
• learn about general requirements for DCAT-AP extensions
• learn how NAPCORE can interact with the DCAT-AP or SEMIC community
The meeting was joined by the authors of this present report, on behalf of NAPCORE, and members
from the Semantic Interoperability Community (SEMIC) team and from EC DG DIGIT, on behalf of
DCAT-AP. Beforehand, the NAPCORE team provided a list of questions to the SEMIC team, about,
e.g., guidelines and details for DCAT-AP extensions. The SEMIC team addressed all these questions,
so we can reuse this feedback for our napDCAT-AP elaborations.
The meeting supported the requirements consolidation phase for napDCAT-AP (see chapter 4) and
the work performed in the Work Item 4.4.2.2 for the definition of a roadmap towards napDCAT-AP.
Overall, the meeting provided interesting and valuable insights into the DCAT-AP framework, and
fostered a closer exchange with our napDCAT-AP development.
The minutes document from this meeting is provided as Annex 3.
Further experts’ inputs were derived from the Coordinated Metadata Catalogue (CMC), being an
antecessor of the metadata harmonisation activity in NAPCORE (see Chapter 1 and Figure 4).
Figure 5: Front page of the Coordinated Metadata Catalogue document by EU EIP
The elaboration of the CMC, as well as feedbacks of CMC users (mainly NAP developers), resulted in
some comments and issues that might be addressed by napDCAT-AP. Such feedback includes the
general wish to move from a proprietary CMC to a standardised DCAT-AP approach. Also, some
questions and proposals were raised about individual metadata elements, as defined by the CMC.
Such inputs were summarized by BASt (DE), being one of the CMC authors, as an own document “EU
EIP Coordinated Metadata Catalogue - A review”. This review is also used for the requirements
consolidation (see chapter 4). The review document is provided as Annex 4.
[page 14]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 14
4 Requirements consolidation
After the collection of requirements, as explained in Chapter 3, we consolidated all the elicited
requirements re-organising the collected inputs (e.g., we handled overlaps and structured by topics),
and producing a “requirements consolidation table”, which is presented below as Table 1.
This table is the main outcome of the requirements analysis, as presented in this report.
The consolidated table shows 40 requirements, divided by the following types:
• General: 8 requirements
• Existing Vocabularies: 5 requirements
• Content: 22 requirements
• Implementation: 5 requirements
Further, the 40 requirements were divided by the following levels of importance:
• Mandatory (the requirement should be addressed by napDCAT-AP from the start): 32
requirements
• Optional (the requirement might be addressed by napDCAT-AP, if found necessary during the
project runtime, and if the project provides enough resources): 8 requirements
The following table compiles all requirements after the process shown above. Some key takeaways
from this consolidation are explained later in Chapter 5 - Summary.
[page 15]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 15
Table 1: Requirements consolidation table
ID Type Requirement Perspective Importance Source Contributor
Req-1 General
napDCAT-AP should address high-level
requirements from literature on metadata
including: expressiveness, richness, adequate data
description, easy data access, context-sensitivity,
modularity, detailed structure, strong typing and
ruling, referential integrity and enable persistent
identifiers.
NAP
metadata
user
Mand
atory
Various
literature4;
SPRINT project
DE, IT
Req-2 General
The napDCAT-AP specification should enable
datasets to be discoverable, searchable and reusable, serve as a baseline for the development of
a metadata database, allow a detailed description
of the registry, its datasets and distributions
and/or data services and allow aggregation and
exchange of metadata.
NAP
metadata
user; NAP
developer
Mand
atory
Meeting with
DCAT-AP
experts; SPRINT
project; EU EIP
activity on NAP
metadata;
experience from
DE NAP
development
DE, IT
Req-3 General
napDCAT-AP-based metadata should be provided
in both human-readable and machine-readable
format.
NAP
metadata
user
Mand
atory SPRINT project IT
Req-4 General napDCAT-AP-based metadata should provide information in multiple languages. NAP metadata user Mandatory SPRINT project IT
Req-5 General napDCAT-AP should adopt a standardised set of vocabularies to ensure semantic interoperability. NAP metadata user Mandatory SPRINT project IT
Req-6 General
napDCAT-AP should adopt a standard
format/serialisation to ensure technological
interoperability and automated access by means
of software agents.
NAP
metadata
user; NAP
developer
Mand
atory
SPRINT project;
EU EIP activity
on NAP
metadata;
experience from
DE NAP
development
DE, IT
Req-7 General
The documentation of napDCAT-AP should be
publicly available on the web without proprietary
licenses. When possible, it should be annotated
digitally, by means of a public repository. .
NAP
developer
Mand
atory
Own experience;
Meeting with
DCAT-AP
experts;
DE, IT
4 Riley, J. (NISO). Understanding Metadata: What Is Metadata, and What Is It For?: A Primer. NISO Primer
Series, 2017.
PwC EU Services. Cost of not having FAIR research data, 2018.
Jeffery, K. G., and A. Asserson. Data Intensive Science: Shades of Grey. No. 33, 2014
Mena-Garcés, E., E. García-Barriocanal, M. A. Sicilia, and S. Sánchez-Alonso. Moving from Dataset Metadata to
Semantics in Ecological Research: A Case in Translating EML to OWL. No. 4, 2011.
Brauburger, N. Datenmarktplätze, Masterarbeit, TU Clausthal. 2021
[page 16]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 16
ID Type Requirement Perspective Importance Source Contributor
Req-8 General
napDCAT-AP should support a maintenance cycle
(issues/discussions/new releases). In particular, it
should define governance processes and a
revision methodology. It should allow for public
commenting on its development and have an
issues and releases planning tool. Issues and
proposals should be discussed and resolved by the
authors, and incorporated into follow-up releases
of napDCAT-AP.
Metadata
standard
experts
Mand
atory
Meeting with
DCAT-AP
experts;
experience from
DE NAP
development;
Good practice
CZ, DE,
IT
Req-9
Existing
Vocabular
ies
napDCAT-AP should consider the DCAT-AP
vocabulary that is the European recommendation
for data catalogues in Europe and is a well-known
vocabulary guaranteeing interoperability also with
data sources from other domains. In particular, it
should reuse DCAT-AP classes and properties,
where possible. Any additional classes and
properties should be added in accordance with
DCAT-AP extension rules.
Metadata
standard
experts
Mand
atory
SPRINT project;
Meeting with
DCAT-AP experts
DE, IT
Req-
10
Existing
Vocabular
ies
napDCAT-AP should follow the ongoing evolution
of DCAT-AP, i.e., consider developments and
revisions of DCAT-AP.
Metadata
standard
experts
Optio
nal
Meeting with
DCAT-AP experts DE
Req-
11
Existing
Vocabular
ies
napDCAT-AP should consider all metadata
elements, as defined by the Coordinated
Metadata Catalogue (CMC) to identify metadata
that better fit the specific requirements of NAPs.
Metadata
standard
experts
Mand
atory
SPRINT project;
EU EIP activity
on NAP
metadata
DE, IT
Req-
12
Existing
Vocabular
ies
A metadata schema for NAPs should consider
existing DCAT-AP extensions (es. geoDCAT-AP for
geo-spatial data) and metadata specifications
from the INSPIRE directive.
Metadata
standard
experts;
NAP
developer
Optio
nal
Meeting with
DCAT-AP
experts;
experience from
CY NAP and BE
NAP
developments
IT, CY,
BE
Req-
13
Existing
Vocabular
ies
When napDCAT-AP defines controlled
vocabularies (or code lists), these should take into
account already existing vocabularies in
operational NAPs, to enable interoperability with
existing solutions
NAP
developer
Optio
nal
Meeting with
DCAT-AP
experts;
experience from
DE NAP
development
DE
Req-
14 Content
napDCAT-AP should provide exhaustive metadata
descriptions for the domain of mobility data,
considering the emerging number and variety of
mobility data sets.
NAP
metadata
user
Mand
atory
EU EIP activity
on NAP
metadata and
experience from
other EU funded
projects related
to mobility data
analysis
DE, GR
[page 17]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 17
ID Type Requirement Perspective Importance Source Contributor
Req-
15 Content
napDCAT-AP should propose essential metadata
elements, which are relevant to any NAP (as a
“minimum set of metadata for European NAPs”).
Besides that, any further metadata elements
should be allowed in individual NAP deployments.
NAP
developer
Mand
atory
Experience from
DE NAP
development
DE
Req-
16 Content
napDCAT-AP should consider the canonical
mappings between DCAT-AP and CMC to identify
information that cannot be currently mapped in
DCAT-AP.
Metadata
standard
experts
NAP
Developer
Mand
atory SPRINT project IT
Req-
17 Content
napDCAT-AP should support the description of
metadata information: last date and time when
the metadata set was created or last modified,
the language in which the metadata is described,
and the responsibility for creation and
maintenance of the metadata.
NAP
metadata
provider/
user
Mand
atory
CMC
specification IT
Req-
18 Content napDCAT-AP should support the description of the conditions of usage of the metadata itself.
NAP
metadata
provider/
user
Mand
atory
Meeting with
DCAT-AP experts IT
Req-
19 Content
napDCAT-AP should support the description of
content information: name, a brief description,
the type of resource (dataset or service), the
dataset type category according to logical
clustering or EC Delegated Regulations, the
service type category listed in EU Delegated
Regulation 2017/1926, the language, and the
georeferencing method applied within the
payload.
NAP
metadata
provider/
user
Mand
atory
CMC
specification,
SPRINT project,
and experience
derived from
ongoing
activities of the
NAPCORE
project
IT, GR
Req-
20 Content
napDCAT-AP should provide an indication of the
Delegated Regulation (MMTIS, RTTI, SRTI, SSTP)
covered by the dataset or service
NAP
developer
Mand
atory
experience from
BE NAP
development
BE
Req-
21 Content
napDCAT-AP should support coordinated
development of a controlled vocabulary to
describe dataset/service content. Controlled
vocabulary could be translated into local
languages to allow for harmonization. It should be
maintained and extendable, and be hosted by
napDCAT-AP.
NAP
metadata
provider/
user
Mand
atory good practice CZ
Req-
22 Content
napDCAT-AP should support the description of
temporal information: the period of time in which
the publication of data does not expire.
NAP
metadata
provider/
user
Mand
atory
CMC
specification,
SPRINT project
IT
Req-
23 Content
napDCAT-AP should support the description of
geographic information: the area covered by a
dataset, the regions in which a dataset is valid and
details on the transport network considered.
(following existing and widely applicable
functional classifications).
NAP
metadata
provider/
user
Mand
atory
CMC
specification,
SPRINT project,
transportDCAT-
AP extension
IT, GR
[page 18]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 18
ID Type Requirement Perspective Importance Source Contributor
Req-
24 Content
napDCAT-AP should support the description of
location referencing methods and CRS used in a
dataset/service.
NAP
metadata
provider/
user
Mand
atory
good practice,
experience from
BE NAP
development
CZ, BE
Req-
25 Content
napDCAT-AP should support the description of
transportation system information: describes the
transportation modes and operators dealt with by
the dataset.
NAP
metadata
provider/
user
Mand
atory
CMC
specification,
SPRINT project,
transportDCAT-
AP extension
IT
Req-
26 Content
napDCAT-AP should support the description of
information on responsibilities: who publishes
and owns the datasets.
NAP
metadata
provider/
user
Mand
atory
CMC
specification,
SPRINT project
IT
Req-
27 Content
napDCAT-AP should support the description of
conditions for use: if there is a “License” or
“Contract”, and any other condition to use the
data.
NAP
metadata
provider/
user
Mand
atory
CMC
specification,
SPRINT project
IT
Req-
28 Content
napDCAT-AP should support the description of
access information for data: encoding, syntax,
grammar and data model.
NAP
metadata
provider/
user
Mand
atory
CMC
specification,
SPRINT project
IT
Req-
29 Content
napDCAT-AP should support the description of
data schema and data samples, so the user can
evaluate data before setting up consumption.
NAP
metadata
provider/
user
Mand
atory
experience from
CZ NAP
development
CZ
Req-
30 Content
napDCAT-AP should support the precise
description of the data model adopted by a
dataset, i.e., DATEX II version, publication type,
extension, to allow better searching.
NAP
metadata
provider/
user
Mand
atory
experience from
CZ NAP
development
CZ
Req-
31 Content
napDCAT-AP should support the description of
quality information: the update rate, the quality
criteria of the data set, the history and status of
procedures to assess the compliance of the
Delegated Regulations regarding the provisioning
of data via a NAP.
NAP
metadata
provider/
user
Mand
atory
CMC
specification IT, GR
Req-
32 Content
napDCAT-AP should specify the cardinalities and
obligations for each metadata element
(mandatory, recommended, optional). For such
cardinalities, clear rules need to be established for
NAP deployments (e.g. implications for database
setups, GUI designs and API/harvesting
mechanisms). Also, existing rules from DCAT-AP
regarding such cardinalities need to be
considered.
Metadata
standard
experts;
NAP
developer
Mand
atory
Meeting with
DCAT-AP
experts; EU EIP
activity on NAP
metadata
DE, IT,
GR
Req-
33 Content napDCAT-AP should define guidelines for identifiers. Metadata standard experts Optional Meeting with DCAT-AP experts IT
[page 19]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 19
ID Type Requirement Perspective Importance Source Contributor
Req-
34 Content
napDCAT-AP should define expected value ranges
for each metadata element (e.g. by the usage of
controlled vocabularies)
Metadata
standard
experts
Mand
atory
Meeting with
DCAT-AP experts IT
Req-
35 Content napDCAT-AP should be able to track changes and different versions of metadata records on a NAP. NAP metadata provider Mandatory SPRINT project IT
Req-
36
Implementation
napDCAT-AP should support the (automatic)
validation of metadata adopting it.
Metadata
standard
experts
Optio
nal
Meeting with
DCAT-AP experts IT
Req-
37
Implementation
napDCAT-AP should provide usage rules in
addition to the metadata definitions, including
explanations of the semantics of each metadata
element, advice how to relate these elements into
NAP processes
and other.
NAP
developer
Mand
atory
experience from
DE NAP
development
DE
Req-
38
Implementation
napDCAT-AP should provide guidelines for cases
with multiple resources for one dataset/service,
i.e., provide guidelines and solutions to divide the
metadata between the dataset and the resource.
NAP
developer
Optio
nal
experience from
BE NAP
development
BE
Req-
39
Implemen
tation
napDCAT-AP should provide guidelines on how to
make NAP-specific metadata interoperable with
other data portals (e.g., outside the mobility
domain). This may include the handling of
napDCAT-AP extensions when harvesting from
other portals.
NAP
developer
Optio
nal
EU EIP activity
on NAP
metadata
DE
Req-
40
Implemen
tation
napDCAT should provide guidelines for a quality
assurance process to check the quality of
metadata collected on a NAP
NAP
metadata
user
Optio
nal SPRINT project IT
[page 20]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 20
5 Summary
The “Requirements Consolidation Table”, as presented in Chapter 4, presents a comprehensive
catalogue of advice and assignments, to be considered by follow-up activities of NAPCORE SWG 4.4.
There are some up-front, general requirements, looking at, e.g., high-level requirements for a new
metadata specification (see “Req-1” in the Table), including aspects of:
• Expressiveness,
• Richness,
• adequate description of the real data,
• easy access to the real data,
• context-sensitivity,
• modularity,
• detailed structure (=distinct metadata categories which are captured in form of specified
metadata elements),
• strong typing and ruling,
• “referential integrity” (= a clear allocation of an identity to metadata elements in an
unambiguous way), and
• enable persistent identifiers for data, datasets and metadata.
Further general advice looks at certain functionalities to be fulfilled by the napDCAT-AP specification
(see “Req-2” in the Table):
• to make datasets, when offered on a NAP, discoverable, searchable and re-usable for
national and international data consumers,
• to ensure a common understanding of the metadata content,
• to serve as a baseline for the development of a metadata database in an individual NAP,
• to allow for a detailed description of a NAP dataset registry, the datasets offered by such
registry, and distributions or data services related to such data sets, and
• to allow for aggregation and exchange of metadata.
All of the above aspects, some of which we reflected by particular requirements, need to be kept in
mind when developing and maintaining the envisioned napDCAT-AP model.
The remaining general requirements (see “Req-3” to “Req-8” in the Table) impose further technical
and organisational prerequisites for napDCAT-AP.
There is also a series of requirements regarding existing vocabularies (see “Req-9” to “Req-13” in the
Table), implying that we should build napDCAT-AP upon existing metadata definitions, where
possible, instead of building a stand-alone approach. This would foster interoperability and
acceptance with existing metadata domains and legacy systems.
The majority of the requirements is about metadata contents (see “Req-14” to “Req-35” in the
Table). These correspond to information items which are seen as necessary to be covered by the
napDCAT-AP model. Many of these requirements here can be translated into specific metadata
elements, that might be modelled as classes or properties under the napDCAT-AP data model.
Finally, there are some requirements about implementation (see “Req-36” to “Req-40” in the Table),
implicating approaches and methods to apply and host the envisioned napDCAT-AP specification in a
real-life context.
[page 21]
Requirements Analysis for a new Metadata Specification
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 21
We propose that all these requirements will be handled within NAPCORE SWG 4.4. as follows:
• General requirements are of interest for any upcoming work item of NAPCORE SWG 4.4.
• Requirements about existing vocabularies and metadata contents are of interest for the
upcoming Work Item 4.4.2.3 Conceptual model and Work Item 4.4.2.4 Draft specification
• Requirements about implementation are of interest for any upcoming work under the Task
4.4.3 “nap DCAT-AP back office”
In summary, the consolidated table of requirements will be considered by follow-up Work Items of
this SWG, during the preparation and development of the napDCAT-AP data model and
documentation. This way, such requirements list is also a sort of a “specification sheet” for our
upcoming work, as it describes expected technical, organisational, and functional features of
napDCAT-AP.
The content of this report is integrated by the outcomes of the Work Item 4.4.2.2 “Approach towards
napDCAT-AP specification” that, considering also the identified requirements, defines a roadmap
based on guidelines and best practices for the definition, implementation and publication of
napDCAT-AP as a DCAT-AP extension.
[page 22]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 2
Annex 1: Individual requirements by SWG 4.4. partners
1.1. Germany
Rq. No.: DE-00
The requirement: The “NAPCORE Metadata Catalogue” should serve as a baseline for
the development of a metadata database in a NAP.
Category Functional
The perspective: NAP developer
The source: Own experience
Your name: Peter Lubrich
Date: 2022/01/31
Notes: Based on current re-development of DE NAP
Rq. No.: DE-01
The requirement:
(a short and clear
statement)
The harmonized metadata scheme should address some high-level
requirements from literature on metadata:
• expressiveness
• adequate description of the real data
• easy access to the real data
• context-sensitivity
• modularity
• detailed structure (=distinct metadata categories which are
captured in form of specified metadata elements)
• strong typing and ruling
• “Referential integrity” (= a clear allocation of an identity to
metadata elements in an unambiguous way)
• enable persistent identifiers for data, datasets and metadata
Category Technical
The perspective: Metadata standard experts
The source: Outcome from study / paper:
• Riley, J. (NISO). Understanding Metadata: What Is Metadata,
and What Is It For?: A Primer. NISO Primer Series, 2017.
• PwC EU Services. Cost of not having FAIR research data, 2018.
• Jeffery, K. G., and A. Asserson. Data Intensive Science: Shades
of Grey. No. 33, 2014
• Mena-Garcés, E., E. García-Barriocanal, M. A. Sicilia, and S.
Sánchez-Alonso. Moving from Dataset Metadata to Semantics
in Ecological Research: A Case in Translating EML to OWL. No.
4, 2011.
• Brauburger, N. Datenmarktplätze, Masterarbeit, TU Clausthal.
2021
Your name: Peter Lubrich
Date: 2022/03/17
[page 23]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 3
Notes:
Rq. No.: DE-02
The requirement:
(a short and clear
statement)
The harmonized metadata scheme should:
• help to make data available and searchable for pan-European
service providers,
• ensure Metadata to be machine-readable, and
• ensure a common understanding of the metadata content.
Category Functional
The perspective: Other: Author of EU EIP Coordinated Metadata Catalogue
The source: Outcome from project: EU EIP
Your name: Peter Lubrich
Date: 2022/03/17
Notes:
Rq. No.: DE-03
The requirement:
(a short and clear
statement)
The harmonization activity should provide exhaustive metadata
descriptions for the domain of mobility data.
This means we need to make mobility data sets more distinguishable
and better findable, considering the emerging number and variety of
mobility data sets.
Category Functional
The perspective: Other: Author of EU EIP Coordinated Metadata Catalogue
The source:
Outcome from project: EU EIP
Your name: Peter Lubrich
Date: 2022/03/17
Notes:
Rq. No.: DE-04
The requirement:
(a short and clear
statement)
The harmonization activity should allow for mobility-related
metadata descriptions, which still need to be interoperable with
other data portals, outside the mobility domain.
Mechanisms for interoperability need to be described.
(For example, if you harvest your NAP metadata to an Open Data
portal, a metadatum like "TRANSPORTATION MODES" may be
transmitted, even if it will be likely ignored).
Category Functional
The perspective: Other: Author of EU EIP Coordinated Metadata Catalogue
The source: Outcome from project: EU EIP
Your name: Peter Lubrich
Date: 2022/03/17
Notes:
Rq. No.: DE-05
The requirement:
(a short and clear
statement)
When we describe harmonized metadata, we need to have a clear
understanding of “mandatory”, “recommended” and “optional”
[page 24]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 4
metadata elements, and compare this understanding to DCAT-AP
rules.
For example, a “mandatory” element may mean the following:
• the NAP system can save such element within its database,
• and/or such element can be entered by a manual metadata
GUI in the NAP
• and/or such element can be imported via an API/harvester to
the NAP database
• and/or such element can be exported via an API/harvester
from the NAP database
Category Functional
The perspective: Other: Author of EU EIP Coordinated Metadata Catalogue
The source: Outcome from project: EU EIP
Your name: Peter Lubrich
Date: 2022/03/17
Notes:
Rq. No.: DE-06
The requirement:
(a short and clear
statement)
The “NAPCORE Metadata Catalogue” should serve as a baseline for
the development of a metadata database in a NAP.
Category Functional
The perspective: NAP developer
The source: Own experience
Your name: Peter Lubrich
Date: 2022/01/31
Notes: Based on current re-development of DE NAP
Rq. No.: DE-07
The requirement:
(a short and clear
statement)
The harmonization activity should only apply for essential Metadata
elements, which are relevant to any NAP. We should follow the
paradigm of the former Coordinated Metadata Catalogue to be a
“minimum set of Metadata for NAPs”.
Saying so, we should allow to add further, country-specific Metadata
fields in individual NAP deployments.
Category Content
The perspective: NAP developer
The source: Own experience
Your name: Peter Lubrich
Date: 2022/01/31
Notes: Based on current re-development of DE NAP
Rq. No.: DE-08
The requirement:
(a short and clear
statement)
The harmonized metadata scheme should be provided in an RDF-
compatible format.
[page 25]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 5
Category Technical
The perspective: NAP developer
The source: Own experience
Your name: Peter Lubrich
Date: 2022/01/31
Notes: Based on current re-development of DE NAP
Rq. No.: DE-09
The requirement:
(a short and clear
statement)
Analogous to DCAT-AP, which serves certain functionalities, we need
to define the functionalities of “napDCAT-AP”. Options are:
• Description of catalogues, datasets/distributions and data
services
• Aggregation and exchange of metadata
• Expression of access rights and licences
• Enabling faceted search through common data themes
• Description of details of data to allow for automated
processing
Category Functional
The perspective: Metadata standard experts
The source: Other: Meeting with DCAT-AP experts on 1st March 22
Your name: Peter Lubrich
Date: 2022/03/17
Notes:
Rq. No.: DE-10
The requirement:
(a short and clear
statement)
“napDCAT-AP” should reuse DCAT-AP classes and properties, where
possible. Further classes and properties should be added in
accordance to DCAT-AP extension rules.
Category Content / Existing Vocabularies
The perspective: NAP developer
The source: Own experience
Your name: Peter Lubrich
Date: 2022/01/31
Notes: Based on current re-development of DE NAP
Rq. No.: DE-11
The requirement:
(a short and clear
statement)
“napDCAT-AP” should provide usage rules in addition to the
Metadata definitions, including:
• explanations of the semantics of each metadata element,
• advice how to relate these elements into NAP processes
• and other.
These rules should be laid down verbally and downloadable for
users.
Category Functional
The perspective: NAP developer
[page 26]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 6
The source: Own experience
Your name: Peter Lubrich
Date: 2022/01/31
Notes: Based on current re-development of DE NAP
Rq. No.: DE-12
The requirement:
(a short and clear
statement)
“napDCAT-AP” should be governed and revisionable. Issues and
proposals should be discussed and resolved by the authors, and
maybe incorporated into follow-up versions of “napDCAT-AP”.
Category Functional
The perspective: NAP developer
The source: Own experience
Your name: Peter Lubrich
Date: 2022/01/31
Notes: Based on current re-development of DE NAP
Rq. No.: DE-13
The requirement:
(a short and clear
statement)
When “napDCAT-AP” defines controlled vocabularies, these should
account for already existing vocabularies (or code lists) in
operational NAPs.
If the harmonized vs. national vocabularies are different, we should
ensure interoperability of such multiple vocabularies. (use the “sub
property” concept of RDF, and the mapping expressions used in
SKOS)
Category Technical / Existing Vocabularies
The perspective: NAP developer
The source:
Own experience AND Other: Meeting with DCAT-AP experts on 1st
March 22
Your name: Peter Lubrich
Date: 2022/03/17
Notes: Based on current re-development of DE NAP
Rq. No.: DE-14
The requirement:
(a short and clear
statement)
The production of “napDCAT-AP” should follow the official DCAT-AP
extension rules:
https://joinup.ec.europa.eu/release/dcat-ap-how-extend-dcat-ap
Category Technical
The perspective: Metadata standard experts
The source: Other: Meeting with DCAT-AP experts on 1st March 22
Your name: Peter Lubrich
Date: 2022/03/17
Notes:
Rq. No.: DE-15
The requirement:
(a short and clear
statement)
The documentation of “napDCAT-AP” should be annotated digitally,
maybe as a HMTL site similar to:
https://semiceu.github.io/GeoDCAT-AP/releases/
Category Technical
[page 27]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 7
The perspective: Metadata standard experts
The source: Other: Meeting with DCAT-AP experts on 1st March 22
Your name: Peter Lubrich
Date: 2022/03/17
Notes:
Rq. No.: DE-16
The requirement:
(a short and clear
statement)
“napDCAT-AP” should follow the ongoing evolution of DCAT-AP, i.e.
consider developments and revisions of DCAT-AP.
Category Functional
The perspective: Metadata standard experts
The source: Other: Meeting with DCAT-AP experts on 1st March 22
Your name: Peter Lubrich
Date: 2022/03/17
Notes:
1.2. Belgium
Rq. No.: BE-01
The requirement: Review an approach for cases with multiple resources for one
dataset/service:
A) multiple uploads of a dataset/service with (almost) identical
metadata information
B) division of metadata on the level of a dataset and metadata on
the level of the resource, where a dataset can have multiple
resources.
In BE we chose option B, as this is inherent to the database approach
used in the open source CKAN software. In the metadata we did not
find any guidelines to divide the metadata between the dataset and
the resource.
Category Functional
The perspective: Metadata standard experts
The source: Own experience
Your name: Jasper Beernaerts
Date: 03/03/2022
Notes: BE NAP operator
Rq. No.: BE-02
The requirement: Include a (mandatory, multiple choice) metadatafield indicating the
type of NAP (MMTIS, RTTI, SRTI, SSTP) a dataset or service is
registered for.
Category Functional
The perspective: NAP developer
The source: Interview AND Own experience
[page 28]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 8
Your name: Jasper Beernaerts
Date: 03/03/2022
Notes: BE Nap operator
Rq. No.: BE-03
The requirement: Definition of napDCAT-AP should be accompanied by mappings from
other standards e.g. INSPIRE
Category Technical
The perspective: NAP developer AND Metadata standard experts
The source: Own experience AND Outcome from project: Belgium project for
mapping DCAT-AP & INSPIRE (in progress)
Your name: Jasper Beernaerts
Date: 03/03/2022
Notes: NAP Operator BE. Currently we are in progress of defining a mapping
for DCAT-AP and INSPIRE data for our portal geo.be . In our opinion,
development of napDCAT-AP could benefit from standardized
mapping tables with for example INSPIRE to avoid that every country
will do this independently (less efficient).
Rq. No.: BE-04
The requirement: Include more exhaustive values for metadatafield ‘georeferencing’.
Current options are too limited and leads to data owners indicating
‘other’ in too many cases.
Category Functional
The perspective: NAP developer AND NAP metadata provider (=person who enters
metadata) AND NAP metadata user (=person who reads/seeks
metadata)
The source: Own experience AND Other: colleagues from the maps department
generating
Your name: Jasper Beernaerts
Date: 03/03/2022
Notes: NAP Operator BE
1.3. Cyprus
Rq. No.: CY-01
The requirement: The need to convert/harmonize an INSPIRE metadata schema into a Cypriot
profile of DCAT-AP. The requirement is to take into consideration the
INSPIRE directives when creating the napDCAT-AP
Category Technical
The perspective: Metadata standard experts
The source: Outcome from project: New Cyprus NAP (in progress)
Your name: Rodolfo Da Silva (Cyprus)
Date: 8/3/2022
Notes: Based on a major upgrade of CY NAP (in progress)
[page 29]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 9
1.4. Czechia
Rq. No.: CZ 01
The requirement: The metadata catalogue shall contain information fields for schema
(XSD, RGN, SHACL, …) and samples, so the user has possibility to
evaluate data before setting up consumption.
Category Content
The perspective: Other: data consumer / contents
The source: Own experience
Your name: Petr Bureš
Date: 2022/04/05
Notes: Based on current re-development of CZ NAP
https://registr.dopravniinfo.cz/en/, before setting up subscription to
the data users could “peek” inside the data contents to know what to
expect and prepare their systems.
Rq. No.: CZ 02
The requirement: The metadata catalogue shall contain information fields for model of
the used data source, I.e., version, publication, extension, to allow
better searching.
Category Content
The perspective: NAP metadata user (=person who reads/seeks metadata)
The source: Own experience
Your name: Petr Bureš
Date: 2022/04/05
Notes: Based on current re-development of CZ NAP
https://registr.dopravniinfo.cz/en/, to allow better searching
possibility, data model information shall go beyond saying “just”
DATEX II is used it shall further specify version and ideally or indicate if
it was extended.
Example:
Model: DATEX II
model version used: v3.3
Model specific publication SituationPublication
Extended: true
It could be put together like DATEX II v3.3/SituationPublication
Rq. No.: CZ 03
The requirement: Metadata catalogue shall allow for public commenting of its
development, having issues and releases planning tool.
Category Functional
The perspective: NAP metadata user (=person who reads/seeks metadata)
[page 30]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 10
The source: Own experience
Your name: Petr Bureš
Date: 2022/04/05
Notes: Good practice, I.e. use github.com for development and keeping track
of comments and issues and releases.
Rq. No.: CZ 04
The
requirement:
Metadata catalogue shall allow description of used location
referencing methods (more) and used CRS.
Category Content
The perspective: NAP metadata user (=person who reads/seeks metadata) AND Other:
data consumer
The source: Own experience
Your name: Petr Bureš
Date: 2022/04/05
Notes: Good practice, data could be described by many location referencing
methods = we can use DATEX II as for basic set of methods, + it can be
described in supplementary information (roadname, area) or general
comment can be used for that as well. Also some of the providers
might choose to provide also information in different CRS then
ETRS89.
Example:
Reference methods:
- OpenLRpoint, OpenLRLinear, PointAlongLinear,
WGSCoordinate, etc.
Rq. No.: CZ 05
The requirement: Metadata catalogue shall allow coordinated development of satellite
ontologies used to describe data
Category Technical / vocabularies
The perspective: NAP metadata user (=person who reads/seeks metadata)
The source: Own experience
Your name: Petr Bureš
Date: 2022/04/05
Notes: Good practice, data are now described by 2 layer of hierarchical
ontology, this ontology (vocabulary), shall maintained and extendable
and shall be hosted by NAPCORE.
The ontology shall serve as support structure for data description
allowing translations to many languages.
Relates to data categories specified by CMC and delegated
regulations but is not limited by it.
[page 31]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 11
Such vocabularies are then used in metadata description and instead
of just being a literal it is an identifier.
1.5. Italy
ID Type Requirement Perspective Source
Req-
1 General Rich metadata are needed to make data discoverable and re-usable
NAP metadata user
(=person who
reads/seeks
metadata)
SPRINT project
Req-
2 General
Metadata should be provided in both
human-readable and machinereadable format
NAP metadata user
(=person who
reads/seeks
metadata)
SPRINT project
Req-
3 General Metadata should provide information in multiple languages.
NAP metadata user
(=person who
reads/seeks
metadata)
SPRINT project
Req-
4 General
Metadata should adopt a
standardised set of vocabularies to
ensure semantic interoperability
NAP metadata user
(=person who
reads/seeks
metadata)
SPRINT project
Req-
5 General
Metadata should adopt a standard
format/serialisation to ensure
technological interoperability and
automated access by means of
software agents
NAP metadata user
(=person who
reads/seeks
metadata)
SPRINT project
Req-
6 General
Metadata should be collected
defining a quality assurance process
to check their quality
NAP metadata user
(=person who
reads/seeks
metadata)
SPRINT project
Req-
7 General Changes and different versions of metadata should be handled
NAP metadata
provider (=person
who enters
metadata)
SPRINT project
Req-
8 General
Metadata schema specifications
should be publicly available on the
web without proprietary licenses
NAP Developer Own experience
Req-
9 General
Metadata schema specifications
should support a maintenance cycle
(issues/discussions/new releases)
Metadata standard
experts
Meeting with
DCAT-AP
experts
Req-
10
Existing
Vocabular
ies
A metadata schema for NAPs should
consider the DCAT-AP vocabulary
that is the European
recommendation for data calogues in
Europe and is a well-known
vocabulary guaranteeing
interoperability also with data
sources from other domains
Metadata standard
experts SPRINT project
[page 32]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 12
Req-
11
Existing
Vocabular
ies
A metadata schema for NAPs should
consider the Coordinated Metadata
Catalogue (CMC) to identify
metadata that better fit the specific
requirements of NAPs
Metadata standard
experts SPRINT project
Req-
12
Existing
Vocabular
ies
A metadata schema for NAPs should
consider existing DCAT-AP extensions
(es. geoDCAT-AP for geo-spatial data)
and the INSPIRE directives
Metadata standard
experts
Meeting with
DCAT-AP
experts
Req-
13 Content
napDCAT-AP should consider the
canonical mappings between DCAT-
AP and CMC to identify information
that can not be currently mapped in
DCAT-AP
Metadata standard
experts
NAP Developer
SPRINT project
Req-
14 Content
napDCAT-AP should support the
description of metadata information:
last date and time when the
metadata set was created or last
modified, the language in which the
metadata is described, and the
responsibility for creation and
maintenance of the metadata.
NAP metadata
provider/user
CMC
specification
Req-
15 Content
napDCAT-AP should support the
description of the conditions of usage
of the metadata itself
NAP metadata
provider/user
Meeting with
DCAT-AP
experts
Req-
16 Content
napDCAT-AP should support the
description of content information:
name, a brief description, the type of
resource (dataset or service), the
dataset type category according to
logical clustering or EC Delegated
Regulations, the service type
category listed in EU Delegated
Regulation 2017/1926, the language,
and the georeferencing method
applied within the payload.
NAP metadata
provider/user
CMC
specification,
SPRINT project
Req-
17 Content
napDCAT-AP should support the
description of temporal information:
the period of time in which the
publication of data does not expire.
NAP metadata
provider/user
CMC CMC
specification,
SPRINT project
Req-
18 Content
napDCAT-AP should support the
description of geographic
information: the area covered by a
dataset, the regions in which a
dataset is valid and details on the
transport network considered.
NAP metadata
provider/user
CMC
specification,
SPRINT project,
transportDCAT-
AP extension
Req-
19 Content
napDCAT-AP should support the
description of transportation system
information: describes the
transportation modes and operators
dealt with by the dataset.
NAP metadata
provider/user
CMC
specification,
SPRINT project,
transportDCAT-
AP extension
[page 33]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 13
Req-
20 Content
napDCAT-AP should support the
description of information on
responsibilities: who publishes and
owns the datasets.
NAP metadata
provider/user
CMC
specification,
SPRINT project
Req-
21 Content
napDCAT-AP should support the
description of conditions for use: if
there is a “License” or “Contract”,
and any other condition to use the
data.
NAP metadata
provider/user
CMC
specification,
SPRINT project
Req-
22 Content
napDCAT-AP should support the
description of access information for
data: encoding, syntax, grammar and
data model.
NAP metadata
provider/user
CMC
specification,
SPRINT project
Req-
23 Content
napDCAT-AP should support the
description of quality information:
the update rate, the quality criteria
of the data set, the history and status
of procedures to assess the
compliance of the Delegated
Regulations regarding the
provisioning of data via a NAP.
NAP metadata
provider/user
CMC
specification
Req-
24 Content
napDCAT-AP should specify the
cardinalities and obligation for
metadata (mandatory,
recommended, optional).
Metadata standard
experts
Meeting with
DCAT-AP
experts
Req-
25 Content napDCAT-AP should try to define recommendations for identifiers. Metadata standard experts Meeting with DCAT-AP experts
Req-
26 Content
napDCAT-AP should define expected
ranges for each metadata property
(e.g. recommend the usage of
controlled vocabularies for values)
Metadata standard
experts
Meeting with
DCAT-AP
experts
Req-
27
Implemen
tation
napDCAT-AP may define SHACL
shapes to facilitate the validation of
metadata adopting it
Metadata standard
experts
Meeting with
DCAT-AP
experts
1.6. Greece
Rq. No.: GR-01
The requirement:
(a short and clear
statement)
The Coordinated Metadata Catalogue should include an el ement
facilitating the association of a dataset with one or more (if strictly
needed) Delegated Regulations supplementing the ITS Directive.
The perspective: NAP metadata user (=person who reads/seeks metadata)
The source: Own experience
Outcome from project: NAPCORE (WG3 – Task 3.1/3.3)
Your name: Chrysostomos Mylonas (Greece)
Date: 16/5/2022
[page 34]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 14
Notes: Based on experiences derived from the conduction of a survey
targeting the monitoring of NAP data availability and data
collection about utilized licenses per Delegated Regulation.
Rq. No.: GR-02
The requirement:
(a short and clear
statement)
The network coverage element of the Coordinated Metadata
Catalogue grouped under the network coverage category s hould
consider existing and widely applicable functional classifications of
urban and interurban roadways and other elements of a
multimodal transport network (e.g., the one suggested by the
FHWA).
The perspective: NAP metadata user (=person who reads/seeks metadata)
The source: Own experience
Your name: Chrysostomos Mylonas (Greece)
Date: 16/5/2022
Notes: Based on own experience (specifically in the conduction of a study
targeting the assessment of climate change impacts on the national
transportation network)
Rq. No.: GR-03
The requirement:
(a short and clear
statement)
Distinguish “mandatory” and “nice to have” metadata elements
and reflect this distinction on the “napDCAT-AP” extension.
The perspective: NAP developer
The source: Own experience
Your name: Chrysostomos Mylonas (Greece)
Date: 16/5/2022
Notes: Own experience while taking part in the development of the Greek
NAP and the preparation of a document facilitating the adoption of
the Coordinated Metadata Catalogue by data providers in Greece.
Rq. No.: GR-04
The requirement:
(a short and clear
statement)
The Coordinated Metadata Catalogue should help NAP users and
potential data consumers easily understand the content of
mobility-related datasets included in NAPs and associated (or not)
with the Delegated Regulation 1926/2017, given the heterogeneity
of mobility services and relevant data thereof.
The perspective: NAP metadata provider (=person who enters metadata)
NAP metadata user (=person who reads/seeks metadata)
The source: Own experience
Your name: Chrysostomos Mylonas (Greece)
Date: 16/5/2022
Notes: Own experience triggered by an exercise oriented to map MM TIS
data categories.
Rq. No.: GR-05
The requirement:
(a short and clear
statement)
For shared mobility-related datasets, the Coordinated Metadata
Catalogue should provide information about the sharing model to
which a shared-mobility service complies (e.g., station -based
versus free-floating).
[page 35]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 15
The perspective: NAP metadata user (=person who reads/seeks metadata)
The source: Own experience
Your name: Chrysostomos Mylonas (Greece)
Date: 16/5/2022
Notes: Based on own experience especially in tasks related to the analysis
of shared mobility-related data.
Rq. No.: GR-06
The requirement:
(a short and clear
statement)
The Coordinated Metadata Catalogue should be enriched with
elements related to ITS data quality parameters (e.g., avail ability,
timeliness, latency, error rate, location accuracy, event cove rage,
etc.)
The perspective: NAP metadata provider (=person who enters metadata)
NAP metadata user (=person who reads/seeks metadata)
The source: Own experience
Your name: Chrysostomos Mylonas (Greece)
Date: 16/5/2022
Notes: Own experience triggered by the provision of support to th e
operation of the Greek NAP.
[page 36]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 16
2. Annex 2: Input to consolidated requirements from literature
This appendix contains a summary of the reviewed literature, as explained in Chaper 2.1
2.1 Methodology:
Upload document to its respective folder and here put some description of it containing:
• Name of the document (link to that document / or folder)
• Who added / when added
• Purpose: why this document is important to us (1 sentence to 1 paragraph)
New documents should be put first. For common documents like policy there is probably no need for
description. Updating this document is sole responsibility of the uploading party. The document does
not reflect 1:1 contents of the reference folder
Template
Ref short name of the reference group and number
Name of the document: title of filename (hyperlinked)
Folder: hyperlink to the sharepoint folder)
Date: upload date, WHO uploaded
Purpose: Short description of the document with context. Why it is useful to us, what exact parts and
how we use it.
2.2 TURNING FAIR INTO REALITY
Name of the document: TURNING FAIR INTO REALITY: Final Report and Action Plan from the European
Commission Expert Group on FAIR Data
Folder: Literature on Open Data; Date: 28/02/2022, RSD CR
Purpose: 2018, 76 pages. The federation of data infrastructure and application of standards will enable
the discovery and interoperability of data. Data reuse. Defines steps how to implement FAIR principles
to be findable, accessible, interoperable and reusable (page 19). Defines FAIR data in Open Data
context. Defines 27 recommendations for implementation, mainly focused on stakeholders actions
Useful for us: FAIR guiding principles could be used in transport related data sharing here,
recommendations might be useful
2.3 Ref PSI
Name of the document : DIRECTIVE (EU) 2019/1024 OF THE EUROPEAN PARLIAMENT AND OF THE
COUNCIL of 20 June 2019 on open data and the re-use of public sector information
Folder: PSI Directive; Date: 28/02/2022, RSD CR
Purpose: Directive establishes a set of minimum rules governing the re-use and th e practical
arrangements for facilitating the re-use of open data and stimulate innovati on in products and
services. Specify transport (mobility) as one of the high value data sets. Specify data and services to
which it applies, sets grounds for delegated regulations. Sets licences and how the high value datasets
shall be provided. Furter specifies complementarity with ITS Directive!
[page 37]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 17
Usability: inspiration only more relevant information in implementing coming decision
2.4 Ref INSPIRE
Name of the document: folder with INSPIRE Related documents
Folder: INSPIRE; Date: 28/02/2022, RSD CR
Document: DIRECTIVE 2007/2/EC OF THE EUROPEAN PARLIAMENT AND OF THE COUNCILof 14 March
2007establishing an Infrastructure for Spatial Information in the European Community (INSPIRE)
Purpose: INSPIRE Directive, metadata implementing regulation and technical guidelines. The Directive
establishes rules for the Infrastructure for Spatial Information. Specifies that spatial data (or services)
shall be shared by MS and defines which metadata shall be set up. Defines search criteria (article 11.2),
sets up data theme names and themes => important for metadata and data organizat ion. Directive
not focused on transport.
Usability: inspiration only more relevant information in implementing decision
---
Document: COMMISSION REGULATION (EC) No 1205/2008 of 3 December 2008 i mplementing
Directive 2007/2/EC of the European Parliament and of the Council as regards metadata
Purpose: Sets up rules for metadata! Defines metadata elements, definitions, multipl icity, domains
and topics, metadata for services complex family of metadata is defined.
Usability: some metadata elements are useful in transport context, a lot of them similar: title, abstract,
temporal and geographical reference, conditions of access and use, service description => all metadata
to be comparted with NAP needs and DCAT-AP
---
Document: INSPIRE Metadata Implementing Rules: Technical Guidelines based on EN ISO 19115 and
EN ISO 19119
Purpose: revised version from 2013, 99 pages, to define how the requirements of the Implementing
Rules for Metadata can be implemented using EN ISO 19115 and EN ISO 19119. Covers services,
provides mapping to the standard 19115/19119 (xpath). Defines metadata, sets requirements on
metadata and conformity, I.e., for metadata structure and encoding, textual value encoding,
licences, data access, geographical bounding box, data quality, provides examples.
Usability: defines requirements for specific transport relevant metadata and defines conformance
assessment services => inspiration for our metadata conformance.
---
Document: Technical Guidance for the implementation of INSPIRE dataset and service metadata
based on ISO/TS 19139:2007
Purpose: Revised version from 2017, 157 pages, implementing rules describe metadata,
harmonisation, measures and coordination. Describes how to Integrate metadata for Spatial Data
Services, for interoperability, theme-specific metadata etc. Defines Requirements on metadata and
conformity, I.e., for metadata structure and encoding, textual value encoding, licences, data access,
geographical bounding box, data quality, provides examples.
[page 38]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 18
Usability: defines requirements for specific transport relevant metadata and defines conformance
assessment services => inspiration for our metadata conformance.
2.5 DCAT-AP release 2.0.0
Name of the document: Documentation of the DCAT-AP release 2.0.0 // newer version available! 2.1.0
Folder: DCAT-AP release 2.0.0; Date: 28/02/2022, RSDCR
Official link: https://joinup.ec.europa.eu/collection/semantic-interoperability-communitysemic/solution/dcat-application-profile-data-portals-europe/release/200
Purpose: DCAT-AP description in RDF format also EAP file and documentation in docx and PDF. Version
2.0.0 is obsolete (2019) version 2.1.0 is actual now (02/2022). Documentations sets up terminology
and ontology / vocabulary references. Defines mandatory and optional classes to be used to describe
a dataset. Sets up requirements for data compatibility. Defines how to address mul ti-linguality. DCAT
AP available in GITHUB.
Useful for us: as a general resource to base our extension on, documentation examples, githu b with
issues etc.
2.6 Metadata harmonisation activities in EU EIP (ended in 2021)
Name of the document: Three deliverables:
• Coordinated Metadata Catalogue (CMC), Version 2019
• Metadata Guideline, Version 2018
• EU EIP NAP Annual Report 2020
Folder: EU EIP; Date: 31/01/2022, BASt
Official link: https://www.its-platform.eu/achievement/monitoring-harmonisation-of-naps/
Purpose:
Document: Coordinated Metadata Catalogue (CMC), Version 2019
Purpose: blueprint for Metadata structures at each individual NAP in Europe. I t defines a common,
minimum Metadata set, in particular 32 Metadata elements, including t heir description, types and
obligation levels.
--
Document: Metadata Guideline, Version 2018
Purpose: for NAP deployers, discussing alternative Metadata approaches for individu al NAP
environments, taking into account higher-level considerations.
--
Document: EU EIP NAP Annual Report 2020
Purpose: describes the deployment status of NAPs in Europe as well as harmonising work on NAPs;
summarises findings and discussion of Metadata structures at NAPs in 2020, explaining harmonisation
needs and harmonisation bottlenecks
--
[page 39]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 19
Useful for us:
Mostly relevant: the latest CMC version: each of the 32 metadata elements from the CMC needs to be
represented by RDF classes/properties, either compliant to existing classes/properties in DCAT-AP, or
as new classes/properties proposed by subWG4.4
Peter Lubrich has written a review of the CMC, discussing the benefits and some practical issues related
to its use. See the document “4.4.1.1 CMC review_220131.docx“ in the same Sharepoint folder.
2.7 DCAT and DCAT-AP training webinars 2021
Name of the document: Documentation of the DCAT and DCAT-AP training webinars 202 1, provided
by the EU Open Data Portal
Folder: DCAT and DCAT-AP training webinars 2021; Date: 31/01/2022, BASt
Official link: https://academy.europa.eu/courses/dcat-and-dcat-ap-training-advanced-user
Purpose:
Webinar No 1: The learning objective is to understand what metadata is and how it relates to DCAT;
Learn about the history and objectives of DCAT and DCAT-AP.
Webinar No 2: The learning objective is to understand the vocabularies used in DCAT and DCAT-AP and
how they are used; Understand the way DCAT-AP defines mandatory, recommended and optional
classes and properties; Understand the use of controlled vocabularies in DCAT-AP
Webinar No 3: The learning objective is to understand extensions of DCA T-AP and how they retain
conformance.
Useful for us:
Webinar No 1: Basis knowledge - I expect everyone in subWG4.4 is aware of these basics!
Webinar No 2: This Important for us, as we apply the same building blocks in our DCAT-AP extension.
Should be considered by Work Item 4.4.2.4 “Draft specification”
Webinar No 3: This Important for us as we build an own DCAT-AP extension. Should be considered by
Work Item 4.4.2.2 “Approach towards DCAT-AP specification”.
2.8 EU Data Governance Act
Name of the document : REGULATION OF THE EUROPEAN PARLIAMENT AND OF THE COUN CIL ON
EUROPEAN DATA GOVERNANCE (Data Governance Act) (Proposed EC Regulation)
Folder: Data Governance Act; Date: 31/01/2022, BASt
Official link: https://eur-lex.europa.eu/legalcontent/EN/TXT/PDF/?uri=CELEX:52020PC0767&from=EN
Purpose: The Regulation will facilitate data sharing across the EU and between sectors to create wealth
for society, increase control and trust of both citizens and companies reg arding their data, and offer
an alternative European model to data handling practice of major tech pl atforms. In particular, to
create new EU rules on neutrality to allow novel data intermediaries to fu nction as trustworthy
organisers of data sharing.
Useful for us: The term “Metadata” is only used in the regulation regarding data sharing services for
DGPR-related data. As this is not in the scope of NAP (at least, yet), this regulation is not relevant!
[page 40]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 20
2.9 EU European Data Strategy
Name of the document: A European strategy for data (EC Communication)
Folder: European Data Strategy, Date: 31/01/2022, BASt
Official link: https://ec.europa.eu/info/strategy/priorities-2019-2024/europe-fit-digitalage/european-data-strategy_en
Purpose: The Communication on a European strategy for data aims to create a single market for data
that will boost Europe’s global competitiveness and data laws. It is c oncretised via the Data
Governance Act (see above).
Useful for us: The term “Metadata” is not mentioned, thus this is not relevant!
2.10 Cost of not having FAIR research data
Name of the document: Cost of not having FAIR research data (EC, 2018)
Folder: Literature on Open Data; Date: 31/01/2022, BASt
Purpose: Estimating the cost of not having FAIR research data for the EU dat a market and EU data
economy.
Useful for us: Reference to FAIR principles – a minimal set of guiding principles and practices, which
enable both machines and humans to find, access, interoperate and re-use research data and
metadata. Very generic elaboration:
• Metadata challenges (“lack of persistent identifiers for data, datasets and metadata”,
“unstructured or incomplete metadata.”
• Metadata requirements (“single point of access, where you could query for metadata whi ch
would instantly point to the layer where the data are located, thus reducing considerably time
to access (meta)data.”, “Quality and richness of the available metadata.”, “Metadata following
international recognised standards such as DataCite, DCAT- AP Dublin Core, DDI, or SDMX.”,
“Machine-readability of metadata”)
2.11 Ref Riley and Baca
Name of the documents: Riley, J. (NISO). Understanding Metadata: What Is Metadata, and What Is It
For?: A Primer. NISO Primer Series, 2017. and Baca, M., Pardo, P.E., Berg , S.U., Zozom, E., 2008.
Introduction to Metadata. Getty Research Institute, 2008.
Folder: Literature on Metadata standards and interoperability; Date: 19/01/2022, BASt
Purpose: some literature to get familiar with the topic of Metadata standards an d interoperability.
These two reports give you a good overview how to store and share metadata, based on the concepts
of the Resource Description Framework (RDF), Linked Data and Semantic Web, as well as on domainspecific Metadata standards.
2.12 Ref SPRINT 1
Name of the document: Enabling Cross-Border Travel Offers Through National Access Point
Federation via Metadata Harmonisation (paper and slides)
Folder: SPRINT project; Date: 11/2021, Cefriel (IT)
[page 41]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 21
Purpose: Paper and slides describing the work done within the Shift2Rail IP4 SPRI NT project on a
prototype harmonizing metadata from different NAPs (Belgium, Netherlands, and France) and
enabling the defined cross-border scenario.
Useful for us: it investigates conceptual mappings between different NAP metadata schema, the CMC
and DCAT-AP; it describes a working prototype to harmonise metadata from different NAPs using
DCAT-AP.
2.13 Ref SPRINT 2
Name of the document: D2.3 Requirements for an IF architectural design F-REL
Folder: SPRINT project; Date: 1/2022, Cefriel (IT)
Purpose: Deliverable of the Shift2Rail IP4 SPRINT project analysing different NAPs an d the CMC to
gather requirements for the IP4 Asset Manager, i.e., a catalogue of digital artifacts for transport service
providers.
Useful for us: Analysis of the CMC, elicited requirements (e.g., competency questions for NAP
metadata).
2.14 Ref DATEX-LOD-1
Name of the document: Analysis and revision of the models used for road traffic and travel
information in Europe
Folder: DATEX-LOD Project; Date: 11/01/2022, ŘSD ČR (CZ)
Purpose: Report of the CEF project LOD-RoadTran18, aimed at increased visibility o f road traffic data
across open data portals. This report focuses on review of existing models used for traffic description.
Useful for us is Annex C analysing different traffic ontologies including vocab.d atex and summary of
tools used for work with metadata and ontologies.
2.15 Ref DATEX-LOD-2
Name of the document: Analysis of the implementation of the PSI and ITS Directives
Folder: DATEX-LOD Project; Date: 11/01/2022, ŘSD ČR (CZ)
Purpose: Report of the CEF project LOD-RoadTran18, aimed at increased visibility o f road traffic data
across open data portals. This report focuses on analysis of ITS and PSI di rective implementation.
Useful for us is Annex D-F Analysing metadata approaches in ITS and Open Data contexts across the
EU, Spain and Czechia. Used to point out traffic extensions to DCA T-AP and software for harvesting
and converting metadata.
2.16 Ref DCAT-AP other extensions
Name of the documents: geoDCAT-AP, DCAT-AP_IT/DK/NO/SE, ISA and Aporta analysis of DCAT-AP
extensions
Folder: DCAT-AP\DCAT-AP other extensions; Date: 11/2021-01/2022, BASt, Cefriel (IT)
Purpose: Specifications and analysis of different extensions of DCAT-AP (national profiles and domain
specific profiles).
[page 42]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 22
Useful for us: to define the napDCAT-AP roadmap it is useful to investigate what artefacts are delivered
for each extension, and how the specifications of the extensions are structured. Moreover, the analysis
for ISA reports guidelines for the definition of DCAT-AP extensions.
2.17 Ref DCAT-AP other extensions - transport DCAT AP
Name of the document: O1.2 TransportDCAT-AP and Controlled Vocs.pdf
Folder: DCAT-AP\DCAT-AP other extensions\transportDCAT-AP; Date: 01/2022, Cefriel (IT)
Purpose: Document describing TransportDCAT-AP, a profile of the European stand ard for the
representation of metadata in open data portals, created in the context of the CEF-OASIS project with
a focus on the representation of metadata about open public transport data.
Useful for us: review of current metadata models and their features; extract requirements considering
an extension addressing the same domain (pag. 7); provides an example of how t o describe a DCAT-
AP extension.
2.18 Ref Get Ready for Data Tool
Name of the document: Get ready for data! (paper long and compact version)
Folder: Literature on Open Data; Date: 01/2022, BASt
Purpose: Paper and its compact version are describing the Get Ready for Data Tool. I t is designed for
city officials and early-child development practitioners who collect, sha re, and use data. The tool
reports a set of questions to make considerations in planning a data-in formed project or policy. The
three main themes considered are: strategy, data collection and use, and ethics and engagement.
Useful for us: some of the question reported could help us in collecting requirements for the metadata
profile.
[page 43]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 23
3. Appendix 3 Input to consolidated requirements from expert interviews
3.1. Meeting Minutes – Discussion 01/03/2022 DCAT-AP and extensions
Project
Action 2016-07
Promoting semantic interoperability
amongst the EU Member States
Meeting
Date/Time
01/03/2022
09:00-10:30 AM
(GMT+1)
Meeting Type Discussion Meeting Location Microsoft Teams
Meeting Coordinator Makx Dekkers Issue Date 02/03/2022
Meeting Agenda
1. Opening, welcome, agenda, objectives
2. Short presentations by participants
3. Vision of the new DCAT-AP extension in Napcore project
4. General requirements for DCAT-AP extensions
5. Discussion
6. Wrap up
Presentation and meeting details:
Attendee Name Organisation/Country
Antonia Azzini AA Napcore
Bert Van Nuffelen BVN TenForce -- SEMIC team
Charline Alexandre CA PwC -- SEMIC team
Makx Dekkers MD Independent consultant -- SEMIC team
Marco Comerio MC Napcore
Marco Scrocca MS Napcore
Pavlina Fragkou PF European Commission
Petr Bures PB Napcore
Peter Lubrich PL Napcore
Summary of the meeting
Opening, welcome, agenda, objectives
[page 44]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 24
• Peter Lubrich presented the objectives of today’s discussion on the DCAT-AP extension in
NAPCORE project, as well as the agenda of this meeting
Short presentations by participants
● Makx Dekkers reminded that he was the editor of DCAT-AP 1.0 and is currently looking at how
DCAT-AP can help data spaces. He also remembered that he is a member of the working group
at W3C that developes and maintains DCAT.
● Bert Van Nuffelen mentioned that he is the editor of DCAT-AP and is also supporting the Flemish
Government in their metadata and their local DCAT-AP profiles.
● Antonia Azzini (IT) is working on the knowledge technology practice at Cefriel in Milan. She is
working on the requirement definitions for the Napcore project.
● Marco Comerio (IT) is part of the research group Cefriel in Milan.
● Mario Scrocca (IT) added that he has been involved in the SPRINT project where he worked on
asset management for an ecosystem of transport stakeholders.
● Petr Bures (CZ) is an independent expert in the Napcore project. His background is traffic
information and creating a description of the data feed.
● Peter Lubrich (GE) is working for the Federal Highway Research Institute. He also operates the
National Access Point and is the leader of the activity group in Napcore.
Vision of the new DCAT-AP extension in Napcore project
● Peter Lubrich presented the Napcore project which has a European dimension. He explained the
NAP acronym standing for National Access Point. Technically, t here are data portals for the
mobility sector installed by the Member States of the EU. When looking at those portals, they
look like open data portals with specific mobility data and metadata. T here are data categories
that are mobility related.
● PL explained that they are driven by the European Delegated Regulations, regulati ons about
mobility data. Those regulations clarify that mobility data have to be on NAP. When looking at
the details of those regulations, it is stated that appropriate metadata should be used. They also
mention metadata catalogues, meaning that the European Commission is aware that metadata
harmonization and alignment is needed.
[page 45]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 25
● PL presented what they did in the previous years when working with other NAPs about
Coordinated Metadata Catalogue. They set up many specifications for metadata in European
NAPs.
● PL explained the feedback they had on the Catalogue. It has been widely accepted, many people
around the continent are aware of this and some use it. The EC likes i t and recommends it for
implementation. However, they faced some scepticism because of the prop rietary approach,
they did not use DCAT-AP. The compatibility is a big issue and there is a wish of making the
catalogue compatible with DCAT-AP.
● PL added that now they have the idea to convert the catalogue into a proper DCAT-AP extension,
called napDCAT-AP. They have the motivation of Linked Open Data.
[page 46]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 26
● PL presented what they are doing these days. They are doing requirement analysis; conceptual
modelling and they try to do some mapping of DCAT-AP elements.
● Petr Bures commented that countries developing their NAPs would like to use catalogue as the
backbone of those portals.
● Bert van Nuffelen wondered if there was a European access point, a portal aggregating
everything.
● Peter Lubrich clarified that this was the long-term goal. Once they have their metadata
harmonized, they could establish a consolidation of the metadata and there will be already some
demonstrators in their Napcore project.
● BVN also asked how many of the data is not public and is not open data.
● Peter Lubrich stated that in Germany it is more than a half of data.
● Petr Burse added that they did some research in the NAPs and more than half is hidden by APIs
and you need to log in or sign some license terms.
General requirements for DCAT-AP extensions
• Makx Dekkers explained that SEMIC is building vocabularies and applicati on profiles based on
semantic web technologies. There is a focus on governance and the appro ach is based on cocreation with working groups involving people from Member States helping to build those
standards with engagement. They are also toolchains for the implementation.
[page 47]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 27
• MD presented DCAT-AP and the new version that was recently published (v2.1.0) based on W3C
recommendation DCAT version 2.
• https://joinup.ec.europa.eu/collection/semantic-interoperability-communitysemic/solution/dcat-application-profile-data-portals-europe/release/210
• https://www.w3.org/TR/2020/REC-vocab-dcat-2-20200204/
• https://data.europa.eu/en
• MD presented the DCAT-AP maintenance, the co-creation process as well as the GitHub
repository. MD mentioned that W3C is currently working on a version 3 of DCAT which has
functionalities on versioning and data series that they are trying to bui ld in the new version of
DCAT-AP as well.
• https://github.com/SEMICeu/DCAT-AP
• https://joinup.ec.europa.eu/collection/semantic-interoperability-communitysemic/document/process-and-methodology-developing-semantic-agreements
• https://joinup.ec.europa.eu/collection/semantic-interoperability-communitysemic/solution/dcat-application-profile-data-portals-europe/document/change-and-releasemanagement-policy-dcat-ap
• MD presented the main functionalities of DCAT-AP.
• Petr Bures wondered if there is a harmonization with INSPIRE.
• MD clarified that there is a mapping from Inspire to GeoDCAT-AP but t hat does not map all of
INSPIRE.
[page 48]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 28
• BVN added that every Member States has its own INSPIRE rules. There is also mandato ry
information required. Most of INSPIRE data could be mapped to the DCAT space but there are
some differences. ISO sometimes put information at the level of datasets while DC AT puts it at
the distribution or data service level.
Questions from NAPCORE
• MD explained that there are guidelines which are pretty basic and explain how to extend DCAT-
AP. It is allowed to add classes and properties but not something to o similar to what is already
there. The cardinalities for properties can also be changed.
• https://joinup.ec.europa.eu/release/dcat-ap-how-extend-dcat-ap
• MD clarified that it is needed to use the controlled vocabularies specified for DCAT-AP. Others
may be used in addition.
• Peter Lubrich wondered if there is only one controlled vocabulary allowed per property.
• BVN clarifies that technically, there can be multiple. The problem is with the designers of portals
for whom sub properties are handy.
• Peter asked about the portals that already exist. For example, the Belgian and the German portal
have their own vocabularies talking about the same properties. He wonders if it is possible to do
a mapping between 2 vocabularies.
• BVN clarified that for code lists, it is easy.
• MD explained that GeoDCAT-AP is an example of good practices.
• https://semiceu.github.io/GeoDCAT-AP/drafts/latest/
[page 49]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 29
• MD mentioned that anybody working on this topic is welcome to be a member of the DCAT-AP
working group.
• Peter Lubrich asked about how to become an official member.
• MD clarified that it is only important to subscribe.
• https://github.com/SEMICeu/DCAT-AP
• https://joinup.ec.europa.eu/collection/semantic-interoperability-communitysemic/event/dcat-ap-webinar-10th-march-1000-cet
• MD presented the tools for hosting and publishing. At SEMIC, we like GitHub a lot.
• Peter Bures wondered if the vocabularies are also published on GitHub.
• BVN clarified that this is the case. Most of the vocabularies that are used by SEMIC are the ones
of the Publication Office. They have a website where they publish the vocabularies as SKOS
concept schemes.
• MD explained that the governance is the responsibility of NAPCORE. SEMIC has a public approach
and a policy for releases. The only thing he recommends is to write their own rules down.
• https://joinup.ec.europa.eu/collection/semantic-interoperability-communitysemic/solution/dcat-application-profile-implementation-guidelines/about
[page 50]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 30
• MD mentioned that the deliverables to be produced depends on what the implementers expect.
For DCAT-AP, we have a pdf, word, RDF…
• https://data.vlaanderen.be/doc/applicatieprofiel/DCAT-AP-VL/
• https://joinup.ec.europa.eu/collection/access-base-registries/solution/abr-bregdcataptools/norway-implementation-dcat-ap-no
• https://semiceu.github.io/GeoDCAT-AP/
• Peter Lubrich wondered if the UML model is something SEMIC would like to publish.
• BVN clarifies that we always have a UML diagram because people would like to see a picture of
what is happening. They are careful with it because there are a lot of debates on the meaning of
the picture. It is important to well describe what is on the picture and what is not.
• Peter Lubrich explained that the German have already implemented a version of DC AT-AP and
they marked what has been changed / extended.
• Petr Bures wondered what the main document for development is.
• BVN explained that examples, side information have to be added to a templating, this is not put
in the enterprise architecture.
Discussion
• Makx Dekkers asked about the possibility to have a European portal for nation al access point
data.
• Peter Lubrich clarified that this is the long-term goal. What they do in NAPCORE is that there will
be a demonstrator where they take 3 NAPs as a beginning. Most likely, thi s will be portals that
already have RDFs representations.
• Makx wonders if NAPCORE will look at the automated processing of data in the context of DCAT-
AP.
• Petr Bures is not sure about that as NAPCORE is a harmonization project and they are in the
working group for metadata with one of the goals being to have a portal which groups together
several of the portals by way of metadata.
Wrap up
● Peter Lubrich thanked the participants for their contribution.
[page 51]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 31
4. Appendix 4 EU EIP Coordinated Metadata Catalogue (CMC): A review
(Peter Lubrich, BAST, 22/01/31)
4.1. Background
Metadata describes the administration, organisation, and content of a dataset and of a data service.
Metadata datasets are therefore crucial elements to make NAPs accessible and searchable. The EU
EIP harmonisation task examined the usage of metadata in NAPs and worked towards harmonization.
The most visible Metadata representation are the dataset descriptions in NAP portals. Metadata are
also a recurring element of Delegated Regulations of the ITS Directive. Metadata have been
mentioned to date for Delegated Regulation (EU) 2015/962 for RTTI and for Delegated Regulation
(EU) 2017/1926 for MMTIS. However, Metadata should also have the same relevance for all other
Delegated Regulations.
EU EIP recognised there is a need to harmonise Metadata descriptions and structures for the
following reasons:
• to help to make data available and searchable for pan-European service providers,
• to ensure Metadata to be machine-readable in a later stage, and
• to ensure a common understanding of the listed data content.
Consequently, EU EIP provided recommendations in terms of how to implement Metadata in existing
and upcoming NAPs across Europe. The activities were based on:
• results from the former projects EIP and EIP+, in particular the “Coordinated Metadata
Catalogue” (2015) as a proposal for a harmonised set of Metadata,
• evaluation of Metadata approaches in the MS so far, and
• identification of needs and requirements in order to further develop a recommended,
harmonised Metadata approach across Europe.
4.2. EU EIP activities
EU EIP reviewed and evaluated the current practice and experiences of individual NAPs in terms of
Metadata approaches.
This review indicated a quite heterogeneous Metadata landscape across all reviewed NAPs. In 2020,
the CMC is a reference in about half of the analysed NAPs. It is noted that this Catalogue was
updated in 2019, and we assume the latest version is only applied in a few instances, e.g. in
Germany. However, in some other cases alternative Metadata approaches are chosen, or no
information on the Metadata approach is given at all. Reasons for this heterogeneity have been
discussed many times: individual system architectures, individual IT / Open Data frameworks, and
individual NAPs “maturity levels”.
EU EIP has been working on the harmonisation issue for many years. A major product is the
“Coordinated Metadata Catalogue” (CMC), as a blueprint for Metadata structures at each individual
NAP in Europe; defining a common, minimum Metadata set; and considering all data and information
domains of the EU Directive and the respective Delegated Regulations.
The CMC was updated in 2019, with additional coverage of multi-modal travel data and services,
according to Delegated Regulation (EU) 2017/1926 for MMTIS.
[page 52]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 32
4.3. CMC feedback from NAP operators and NAP deployers
We received some generic observations by NAP operators and NAP deployers on the CMC usage.
One of them is about the level of obligation, i.e. the definition of obligatory and optional metadata
elements, and the of the extent of CMC, i.e. the number of defined metadata elements. (Please
remember that the CMC was considered a “minimum set of Metadata for NAPs”!)
The general question is what the general trend is in the European NAP community: should we
simplify the NAP and its processes by only harmonizing the essential metadata, or try to be
exhaustive by collecting also all the optional metadata?
There are in fact two trends:
1. to have exhaustive metadata -> to make transportation data sets more distinguishable and
better findable, considering the emerging number and variety of transportation data sets.
2. To have limited metadata -> to be interoperable with other data portals, outside the
transportation domain. (For example, if you harvest your NAP metadata to an Open Data
portal, a metadatum like "TRANSPORTATION MODES" will be likely ignored).
For the NAPCORE work, we should discuss this, and find a way how we understand the “mandatory”
and “optional” settings. We might explain that some few “essential” data MUST be provided by any
NAP, and further propose a set of optional metadata, that CAN be provided by individual NAP
deployments, depending on use cases, data providers and data users addressed by a NAP.
NAP operators and deployers also provided some concrete feedback and questions on individual
metadata elements from the CMC. They are noted below, together with proposals how to resolve
them in the NAPCORE follow-up work.
Metadata element “TRANSPORTATION MODE”:
• Comment: The CMC defines this as mandatory metadata, with multiple selection possible. In
some NAPs, we might expect that some datasets cannot be related to concrete
transportation modes. For example, in the German NAP, weather observations are offered,
without relation to a transportation mode.
• Solution for NAPCORE: allowing a 0...n cardinality (instead of 1…n) for “TRANSPORTATION
MODE”.
Metadata element “DATASET TYPE CATEGORY”:
• Comment: The CMC defines this as mandatory metadata, with only one selection possible.
The question is that for instance a GTFS or NETEX group of files have themselves more than
one those categories. They could belong at the same time to “Public transport operational
information” and also to “Public transport: fare and purchase information”, as those files
have information about Fares too.
• Solution for NAPCORE: allowing a 1...n cardinality (instead of 1) for “DATASET TYPE
CATEGORY”.
Metadata element “NETWORK COVERAGE”:
• Comment: The options for this element cover all possibilities for infrastructure networks, but
if we are talking about transport services (for instance bus), do we have to set the option
that describes the infrastructure the bus lines are using?
• Solution for NAPCORE: We need to better explain the semantics of this element. Further, we
might implement some logical relations between the entries for "NETWORK COVERAGE" and
[page 53]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 33
"TRANSPORTATION MODES". For example: if a user enters "bus" for "TRANSPORTATION
MODES", only the options "motorway", "arterial road network etc. will be selectable for
"NETWORK COVERAGE".
Metadata element “VALID FROM” / ”VALID TO”:
• Comment: This element can be understood in two ways: (1) time interval when the data feed
is delivered technically via the NAP; (2) the time reference of the delivered information (e.g.
validity time of a public transport time table.)
• Solution for NAPCORE: We need to better explain the semantics of this element. We also
might separate this element into two new elements: e.g. “START/END OF DATA FEED” +
“START/END OF TIME REFERENCE OF DATA”, or similar.
Metadata element “UPDATE FREQUENCY”:
• Comment: This element can be understood in two ways: (1) The update intervals at the data
provider side (i.e., transport service providers update their data when their data are
changed, on occurrence or in constant time intervals). (2) The update intervals at the NAP
data interface (the NAP connects to these transport service providers, take their data, and
then shares those data in the NAP in a differing interval)
• Solution for NAPCORE: We need to better explain the semantics of this element. Proposal:
“UPDATE FREQUENCY” is meant to tell a person who finds this dataset on the NAP, how
often it is updated on NAP, so this person might install a regular data access to the NAP, to
have an up-do-date picture anytime. So, we would use the semantic (2) from above.
However, we could propose a new metadata element for the semantic (1), for example
"UPDATE FREQUENCE OF ORIGINAL SOURCE" or something similar.
Metadata element “CONTRACT OR LICENCE”:
• Comment: This element allows the following options:
o No licence – No contract
o Licence and Free of charge
o Licence and Fee
o Contract and Free of charge
o Contract and Fee
o Not relevant
o The above list is not expressive enough to represent commonly used licences, e.g.
“Creative Commons” etc. Further, the above list sometimes cannot be semantically
mapped to such common licences.
• Solution for NAPCORE: Repair the above list of options for ““CONTRACT OR LICENCE”. Maybe
use the following list:
o royalty-free
o Licence, free use/open data
o Licence, restricted use, free of charge
o Licence, restricted use, fee
o Other contractual arrangement
o Further, add a new metadata element for standard licenses, as "STANDARD LICENSE"
or similar.
4.4. Handover to NAPCORE
[page 54]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 34
As Metadata are more and more recognised as a key factor to ensure interoperability between
different data catalogues, the Metadata perspective has to be widened beyond NAPs, also looking at
Open Data Portals, Government Data platforms, commercial data platforms in the hands of e.g. IT big
players. This way, any Metadata harmonization activities need to expand to wider data ecosystems.
Some stakeholders stated to advance with the CMC in the direction of Metadata interoperability. In
particular, there was the idea to bring together the Catalogue with DCAT-AP, a well-established
metadata specification in the domain of European Open Data portals, developed by a joint initiative
of the EU organizations DG DIGIT, DG CONNECT and the EU Publications Office.
An envisioned product is a “napDCAT-AP” extension, i.e. an adaptation of the DCAT-AP data model to
meet the specific demands of NAPs, e.g. by adding NAP-specific model elements. “napDCAT-AP” will
eventually foster interoperability of NAP metadata with, e.g. open data portals, and eventually allow
findability of NAP data sets outside the NAP portals.
“napDCAT-AP” is expected as a promising step towards efficient and harmonised Metadata usage
across European NAPs. However, the current elaboration is still in a premature status. Many experts
and references related to DCAT-AP have been consulted, and a first iteration to set up a stable
specification of “napDCAT-AP” has been accomplished. However, a viability and acceptance of this
concept will be only possible with wider stakeholder engagement and additional maintenance
structures to handle this specification.
Ideas to do so were discussed and concretised within the NAPCORE project. A dedicated work
package will deal with progressing of “napDCAT-AP”. Many experts and stakeholders from the
previous EU EIP Metadata activities are part of this. Further, under this new activity, additional
liaising is planned with other European Groups, such as the Semantic Interoperability Community
(SEMIC), to ensure a wider perspective on Metadata beyond the NAP domain.
[page 55]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 35
5. SPRINT project on Metadata Harmonisation [Summary “Cefriel project
on Metadata Harmonisation”]
The focus of the NAP regulations is to promote the usage of a specific set of standards, based on
Transmodel, across all Europe to improve transport data interoperability. The data published on a
National Access Point are not easily discoverable and/or reusable if insufficient information is
provided through metadata. Data publishers are encouraged to provide human-readable information
in multiple languages. Metadata for both human data consumers and computer applications provide
even greater benefit.
Even though the role of the NAP as a dataset catalogue is clear in the regulation, each member state
is then free to implement it according to its design. Such principle led to the appearance of different
metadata vocabularies, and the need for interoperability between different metadata sets offered by
different NAPs.
An effort towards the harmonisation of metadata by NAPs is needed to support easy data exchange
and to avoid errors in data exchange between catalogues. For example, if an international user
accesses the NAPs of several EU Member States, there should be no difference in wording and
meaning between the metadata provided, even in different languages. In this context, Semantic Web
technologies can offer a valid solution to encode the semantic of metadata also in an interoperable
machine-readable format.
The Shift2Rail IP4 SPRINT project (http://sprint-transport.eu/) designed and evaluated an automated
solution, based on Semantic Web technologies, for the ingestion and harmonisation of metadata
from different NAPs (Carenini et al., 2021). An RDF representation, adopting a standardised set of
vocabularies for NAP metadata, can also enable software agents to access and explore data
contained in different NAPs.
Besides the need of defining a conceptual mapping between different metadata schema, the
implementation of a prototype adopting the described approach highlighted two important
recommendations for the integration of multiple remote data providers, such as the NAPs: (i) to
consider a quality assurance process for data and metadata, (ii) to handle changes and different
versions of data and metadata.
In the project, the conceptual mappings between different NAP metadata schema (Belgium,
Netherland, and France) and DCAT-AP were defined also leveraging the canonical Coordinated
Metadata Catalogue to DCAT-AP mappings defined by EU EIP. The project highlights the following
considerations: (i) DCAT-AP leverages a standardised vocabulary facilitating the encoding of specific
semantics for each metadata property, moreover, the vocabulary is well-known also outside the
mobility domain and can be easily used by users working with generic data catalogues, (ii) CMC
defines a broader set of metadata that better fit the requirements for National Access Points, (iii)
DCAT-AP should be extended to support domain-specific metadata, such as the ones related to
transportation modes and network coverage and defined in CMC, that currently cannot be
represented using DCAT-AP.
Alessio Carenini, Andrea Fiano, Mario Scrocca, Marco Comerio, and Irene Celino. Enabling Cross-
Border Travel Offers Through National Access Point Federation via Metadata Harmonisation.
Sem4Tra@SEMANTICS 2021, http://ceur-ws.org/Vol-2939/paper6.pdf
[page 56]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 36
5.1. Coordinated Metadata Catalogue [Summary of information modelled by
CMC extracted from SPRINT deliverables]
A specific effort of EU EIP WG NAP is the harmonization in the field of Metadata of European NAPs. A
first agreement was found in the form of the “Coordinated Metadata Catalogue”. It allows the
description and discovery of the most relevant features of NAP datasets. It is worth noting that the
“Coordinated Metadata Catalogue” already contains a mapping with standard vocabularies as EU-
EIP, DCAT-AP and INSPIRE.
According to Coordinated Metadata Catalogue, Metadata describes both datasets and services. A
dataset contains the traffic or travel data, and specific services for multi-modal travel are listed by EU
Regulation 2017/1926 lists. An example of a specific service is “location search” on a data set
describing address identifiers.
A Publication is the combination of a dataset and how the data are published and made accessible. A
Publisher is the one who publishes a dataset. A Contact Point is the one that registers the dataset at
the NAP. A Data Owner is the one who owns or produces data.
A Metadata Set is the collection of different information represented as metadata elements:
• The metadata information on the last date and time when the metadata set was created or
last modified, the language in which the metadata is described, and the responsibility for
creation and maintenance of the metadata.
• The content information describes the dataset defining its name, a brief description, the type
of resource (dataset or service), the dataset type category according to logical clustering or
EC Delegated Regulations, the service type category listed in EU Delegated Regulation
2017/1926, the language, and the georeferencing method applied within the payload.
• The temporal information presents the period of time in which the publication of data does
not expire.
• The geographic information describes the area covered by a dataset, the regions in which a
dataset is valid and details on the transport network considered.
• The transportation system information describes the transportation modes dealt with by the
dataset.
• The information on responsibilities defines who publishes and owns the datasets.
• The conditions for use specify if there is a “License” or “Contract”, and any other condition to
use the data.
• The access information includes four layers: Encoding, Syntax, Grammar and Data Model.
• The quality information defines the update rate, the quality criteria of the data set, the
history and status of procedures to assess the compliance of the Delegated Regulations
regarding the provisioning of data via a NAP.
5.2. Competency Questions for NAP Metadata [Extracted from SPRINT D2.3]
Competency Questions (CQs) play an important role in the ontology development lifecycle, as they
represent the ontology requirements. CQs consist of a set of questions stated in natural language
that the data represented using the ontology structure must be able to answer. They play an
important role in the ontology development life cycle, as they represent the ontology requirements.
The same technique can be used to identify a minimum set of required metadata for NAPs. Below we
provide some examples of competency questions that are specific to the metadata harmonised by
NAP:
[page 57]
Requirements Analysis for a new Metadata Specification - ANNEXES
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 37
• Which are the publishers (transport data providers) of the datasets including information on
different means of public transport?
• Which is the list of owners of the datasets containing information on the different means of
public transport?
• Which are the datasets containing operational information such as vehicle details (i.e. A-
1.1.d.viii and A-1.2.c.ii as codes according to EC Delegated Regulation)?
• Which are the datasets containing Special Fare Products (i.e. A-1.3.a.iii as the code according
to EC Delegated Regulation)?
• Which are the names of the datasets published by the Consorcio Regional de Transportes de
Madrid (CRTM)?
• What are the datasets related to the region of Madrid that also deal with buses?
• Which is the list of publishers of the datasets ordered by the publishers’ websites?
• What is the metadata data and National body assessment status of a specific dataset?
• What are the starting time and the ending time from which a specific dataset is valid?
• What is the transportation mode covered by a given dataset?
• What is the license agreed on to use a given dataset?
• In which data format can a particular dataset be accessed?
5.3. Summary of requirements considered in the definition of the
TransportDCAT-AP extension
TranportDCAT-AP is a profile of the DCAT-AP ontology focused on the public transport domain. This
profile extends DCAT-AP to improve the representation of metadata in this domain.
The profile considers that the nature of the public transport data is geospatial, thus defining as
mandatory the set of metadata related to this type of information. In addition, a specific set of
admissible keywords is defined to standardise the range of metadata properties (i.e., the values that
can be associated with property) and enable domain-related queries, e.g., considering specific
transportation modes.
5.4. Additional requirements [Cefriel]
• Adoption of well-known and interoperable vocabularies to define metadata
• Enable the definition of conditions to access the assets
• Spatial and Temporal granularity of data
