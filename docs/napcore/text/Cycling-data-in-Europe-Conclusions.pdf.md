url: https://napcore.eu/wp-content/uploads/2026/06/Cycling-data-in-Europe-Conclusions.pdf
title: Cycling data in Europe Conclusions

[page 1]
1 of 16
NAPCORE cycling data – Workshops conclusions
Recommendations to the EC DG MOVE
Cycling ambassadors and taskforce
Report
Version v5 (03/04/2025)
Legal disclaimer
The sole responsibility for the content of this document lies with the authors. It does not necessarily
reflect the opinion of the European Union. The European Commission is not responsible for any use
that may be made of the information contained therein. All images are provided by the respective
partners (unless otherwise noted) and are approved for reproduction in this publication.
[page 2]
2 of 16
Document information
Project acronym NAPCORE
Full project title National Access Point Coordination Organisation for Europe
Grant Agreement No. MOVE/B4/SUB/2020-123/SI2.852232
Activity no. and title Cycling data ambassadors and Taskforce
Ambassadors for
cycling data, pilots
Cristina BURAGA (CEREMA)
Mirelle PETERS (NTM)
Taskforce, authors Samuel PIERCE (CIE)
Jørgen WANSCHER (HIT)
Tu-Tho THAI (AFNOR)
Aleksander BUCZYNSKI (ECF)
Holger HAUBOLD (ECF)
David ARINO-MONTOYA (ITxPT)
Stephen TSIOBBEL (ERTICO)
Jon HARROD-BOOTH (EPA)
Contributors Yves AMSLER (UITP)
Abstract
This is a report for EC DG MOVE with recommendations issues from the workshops driven by cycling
data ambassadors and the taskforce associated.
Based on work carried out interactively with the cycling community the conclusions allowed to select
priority use cases and the recommended actions to take for the identified categories as:
- Infrastructure data
- Parking data
- Counting data
- Real-time information for cyclists
Abbreviations
Abbreviation Meaning
DG MOVE Directorate-General for Mobility and Transport
EC European Commission
EU European Union
ITS Intelligent Traffic Systems
NAP National Access Point
NAPCORE National Access Point Coordination Organisation for Europe
WG Working Group
[page 3]
3 of 16
Table of contents
1. Foreword .................................................................................................................................................... 4
1.1. General introduction ......................................................................................................................... 4
1.2. Objectives ........................................................................................................................................... 4
2. Relations with existing EU regulations ................................................................................................... 5
2.1. Cycling data and multimodal travel information ........................................................................ 5
2.2. Cycling and trans-European transport network ........................................................................... 6
2.3. Cycling and active mobility in the Social Climate Fund ............................................................. 7
2.4. Cycling for candidate countries to the EU .................................................................................... 7
3. The four pillars of cycling data .............................................................................................................. 8
3.1. Infrastructure ...................................................................................................................................... 8
Priority use cases ....................................................................................................................................... 8
Recommended actions .............................................................................................................................. 8
3.2. Parking ................................................................................................................................................ 9
Priority use cases ....................................................................................................................................... 9
State of the art & Differences with existing standards ..................................................................... 9
Recommended actions ........................................................................................................................... 10
3.3. Counting ........................................................................................................................................... 10
Priority use cases .................................................................................................................................... 10
State of the art & Differences with existing standards .................................................................. 11
Recommended actions ........................................................................................................................... 11
3.4. Real-time data ................................................................................................................................ 11
Priority use cases .................................................................................................................................... 11
State of the art & differences with existing standards ................................................................... 11
Recommended actions ........................................................................................................................... 11
4. Conclusions – Actions to take ............................................................................................................... 12
4.1. Preamble .......................................................................................................................................... 12
4.2. General recommendations to the European Commission ........................................................ 12
4.3. Low hanging fruits .......................................................................................................................... 13
4.4. Funding opportunities .................................................................................................................... 13
5. Annex - consistent definition of user categories and uses .............................................................. 14
6. REFERENCES ............................................................................................................................................ 16
[page 4]
4 of 16
CYCLING DATA IN EUROPE
1. FOREWORD
1.1. GENERAL INTRODUCTION
Cycling data collection from automatic counters, smartphone applications, infrastructure databases,
parking providers, bike share operators etc. has developed very dynamically. These data are vital
for planners, for example to monitor real-life cyclist flows and evaluate projects. But also for
developers of route planners helping to make cycling more attractive, for example, by combining
precise and up-to-date geodata on cycling infrastructure, including parking, that is compatible
across Europe with real-time information on road closures, congestion or availability of cycle
parking. Currently, this is complicated by the lack of common standards for data collection and
provision for infrastructure data, counting data and all other data types.
Some progress has been made towards establishing coordinated methodologies and standards for
collecting, storing and disseminating data in Europe. The ITS Directive (2010/40/EU) requires that
EU Member States must establish National Access Points (NAP) for mobility data, while Delegated
Regulation 2017/1926 on EU-wide multimodal travel information services includes specifications on
cycling data categories to be published on these NAPs.
1.2. OBJECTIVES
To coordinate the work of NAPs, which originally were quite different in their setup, and to develop
common data formats and standards for use across Europe, the National Access Point Coordination
Organisation for Europe (NAPCORE) project was started. Within NAPCORE, a taskforce on cycling
data is currently producing recommendations on cycling data standards in four main fields: counting,
infrastructure, parking, and real-time. So far, the taskforce has identified relevant data types for
cycling, but also standards that already exist and could be adapted/extended to cycling, leading
to a technical and strategic prioritisation of the cycling data standardisation roadmap for Europe.
In this document, the taskforce on cycling data presents a summary of the results gathered during
the year 2024 and the conclusions made.
[page 5]
5 of 16
2. RELATIONS WITH EXISTING EU REGULATIONS
The below section resurfaces and condenses where cycling and its data has been made relevant in
the existing EU regulations. One can note that cycling is a transversal subject, which explains why it
is mentioned in several texts to the contrary of conventional public transport.
All of the below are strongly related to the political intention of the European Commission that is
materialised in the European Declaration on Cycling (C/2024/2377) [1] contains a commitment to
enable the continuous measurement of progress on the use of cycling in the EU by establishing an
EU-wide baseline, including the length, network density, quality and accessibility of cycling
infrastructure and services for several user types, the share of cycling in total transport and mobility
activity, and the number of serious injuries and fatalities among cyclists (commitment 34).
2.1. CYCLING DATA AND MULTIMODAL TRAVEL INFORMATION
Delegated Regulation (EU) 2024/490 [2] amending DR(EU) 2017/1926 [3] regarding the
provision of EU-wide multimodal travel information services lists the following travel and traffic data
categories relevant for cycling, that should be accessible through the National Access Points (NAP):
TYPES OF THE STATIC, HISTORIC AND OBSERVED TRAVEL AND TRAFFIC DATA
Level of service 1
(e) trip plan computation: (ii) cycle network (cycle tracks, cycle lanes, bus-and-cycle lanes, on-road
shared with vehicles, on-path shared with pedestrians);
Level of service 2
(a) location search – for transport on demand and personal transport: (iv) bike-sharing stations;
(vi) secure bike parking (such as locked bike garage);
(c) auxiliary information – for scheduled transport and transport on demand where relevant:
(ii) vehicle facilities, including classes of carriage, on-board Wi-Fi, capacity and access conditions
for bicycles.
Level of service 3
(c) trip plans: (i) detailed cycle network attributes (surface quality, side-by-side cycling, shared
surface, on/off road, scenic route, ‘walk only’, turn or access restrictions, e.g. against flow of traffic);
(d) trip plan computation: estimated travel times by day type and time-band by
transport mode/combination of transport modes.
[page 6]
6 of 16
TYPES OF THE DYNAMIC TRAVEL AND TRAFFIC DATA
Level of service 2
(b) availability check and location – for transport on demand and personal transport where relevant:
(i) car-sharing availability and location, bike-sharing availability and location, scooter-sharing
availability and location, and other vehicle-sharing availability and location;
According to Article 4 and 5 of the Delegated Regulation; data holders shall provide static, historic
and observed travel and traffic data via the national access point (if that data exist in a readable
machine format) with the following timetable (table only for relevant cycling data types):
Data Type TEN-T network deadline Other parts of the Union
transport network
1.1.e.ii 1 December 2019 1 December 2023
1.2.a.iv 1 December 2020 1 December 2023
1.2.a.vi 1 December 2020 1 December 2023
1.2.c.ii 1 December 2024 1 December 2024
1.3.c.i 1 December 2021 1 December 2023
1.3.d 1 December 2021 1 December 2023
2.2.b.i 1 December 2026 1 December 2028
2.2. CYCLING AND TRANS-EUROPEAN TRANSPORT NETWORK
Regulation (EU) 2024/1679 on Union guidelines for the development of the trans-European
transport network requires in article 40 the collection and submission to the Commission of urban
mobility data per urban node in the fields of sustainability, safety and accessibility. The Commission
shall adopt, no later than July 2025 (one year after the entry into force of the TEN-T regulation),
an implementing act defining the indicators to be used, establishing a methodology for the collection
and submission of data pursuant to that paragraph, and specifying individual deadlines for
submitting such data. While the work on defining the Sustainable Urban Mobility Indicators (SUMI)
is already ongoing, their calculation and updating would be much easier if their underlying data
was collected and represented in a harmonised way.
Additionally, for the EU cofinanced investments, Regulation (EU) 2021/1058 on the European
Regional Development Fund and on the Cohesion Fund lists among the common output and result
indicators:
 RCO 58 - Dedicated cycling infrastructure supported: According to the Staff Working
Document on Performance, monitoring and evaluation of the European Regional
Development Fund, the Cohesion Fund and the Just Transition Fund in 2021-2027 (SWD
2021/198), this is defined as the “length of dedicated cycling infrastructure newly built or
significantly upgraded by projects supported. Dedicated cycling infrastructure includes cycling
facilities separated from roads for vehicular traffic or other parts of the same road by structural
means (kerbs, barriers), cycling streets, cycling tunnels, etc. For cycling infrastructure with
separated oneway lanes (ex: on each side of a road), the length is measured as lane length”.
[page 7]
7 of 16
 RCR 64 - Annual users of dedicated cycling infrastructure:
o SWD 2021/198 states that “the baseline of the indicator is estimated as the annual
number of users of the infrastructure for the year before the intervention starts, and it
is zero for new infrastructure. The achieved values are estimated ex-post in terms of the
number of users using the infrastructure for the year after the physical completion of
the intervention”.
o The document “Methodological support for ERDF and Cohesion Fund result indicators
in the field of transport post 2020” gives detailed guidance on how to collect data
for this indicator and names field surveys (manual counts or temporary automatic
counts) or permanent counters as the main data sources.
2.3. CYCLING AND ACTIVE MOBILITY IN THE SOCIAL CLIMATE FUND
Regulation (EU) 2023/955 establishing a Social Climate Fund stipulates that national plans under
the regulation can provide support in developing and providing active mobility options. Annex IV
of the regulation contains Indicator 28 on d edicated cycling infrastructure supported, which is
defined in accordance with common output indicator RCO58 under regional/structural funding as
the “length of dedicated cycling infrastructure newly built or significantly upgraded by projects
supported under the Fund. Dedicated cycling infrastructure includes cycling facilities separated from
roads for vehicular traffic or other parts of the same road by structural means (such as kerbs and
barriers), cycling streets, cycling tunnels, etc. For cycling infrastructure with separated one-way lanes
(e.g. on each side of a road), the length is measured as lane length.”
2.4. CYCLING FOR CANDIDATE COUNTRIES TO THE EU
In EU accession candidate countries, cycling infrastructure can be financed through Regulation (EU)
2021/1529 of the European Parliament and of the Council establishing an Instrument for Preaccession Assistance (IPA III). Commission Staff Working Document SWD 2022/455 lists indicator
IPA III RF 3.2.4.4: Length of new or upgraded dedicated cycling infrastructure (Km). According to
the accompanying methodological note, this indicator must be further disaggregated:
- by new or upgraded dedicated cycling infrastructure;
- by cycle track or cycle lane or other;
- by urban or rural.
[page 8]
8 of 16
3. THE FOUR PILLARS OF CYCLING DATA
Based on interactive workshops with the cycling community, 4 structuring themes have been identified
for the cycling data, concerning: infrastructure, parking, counting and real-time data.
3.1. INFRASTRUCTURE
Priority use cases
Having precise, correct, up-to-date and comparable digital data on cycling infrastructure
available is important for a wide number of stakeholders:
- Cyclists/users of infrastructure, especially for routing applications: knowing where which type
of cycling infrastructure is located, and what its parameters are (safety, comfort,
time/physical effort needed, accessibility for different users/cycle types, etc.)
- Infrastructure managers: evaluating infrastructure safety and performance (link to counting
+ survey data), identifying and prioritising maintenance + investment needs
- Policy makers and funding institutions: knowing where and how much cycling infrastructure is
available needed, how much it will cost to build comprehensive networks and where
investments should be prioritised (state of the art & differences with existing standards)
Only a few EU Member States developed a national standard for representing cycle infrastructure
data based on INSPIRE Directive [5]. Good practices include Austria, France, Germany. In most cases
data is either not shared through the NAP or not harmonised between different data producers
(different municipalities, regional authorities etc.). Many cities are missing, sometimes the only data
linked from the NAP is for example a PDF with a map of the city. Different authorities have different
definitions of basic terms and use different parameters to describe the infrastructure, which
generates misunderstandings and variable applications of regulations. Such incomplete and
fragmented data is not useful for most of supralocal wider integration use cases.
Therefore, many data consumers – from routing apps to scientists analysing route choices, distribution
or impact of cycle infrastructure – use crowdsourced OpenStreetMap (OSM) as the source of data.
Currently, this is the only internationally relevant source. Limitations include: governance (no single
responsible for the data) and varying quality of coverage across different areas.
Recommended actions
Common standards on infrastructure should be developed as a priority on road safety by CycleRAP
[6], and include at the very minimum the type of infrastructure, its surface and width; the final report
[7] of the UNECE Group of Experts on cycling infrastructure can be used as a basis for the typology
of cycling infrastructure. There should also be support for the development of tools to convert
between cycling infrastructure data collected according to relevant national standards where they
exist already and the future common standards, as well as a conversion method between the
common standard and OpenStreetMap [8] representation of the cycling infrastructure.
[page 9]
9 of 16
This can be used in several ways:
 Consider the EuroVelo network as a harmonisation basis for long-distance routes [9];
 Stop gap provision of infrastructure data where official data is not available or not yet
converted to the common standard;
 Additional quality check for official data in the areas where it is already available;
 Better representation of cycling infrastructure in OpenStreetMap in the areas where
official data is already available.
Providing geolocated data (instead of statistical summaries) in the common standard about the
infrastructure built and its usage should be obligatory for EU cofinanced projects.
3.2. PARKING
Priority use cases
The overarching theme of uses cases related to parking data for cycling is sustainable mode shift:
- Cyclists want to make sure they can do part of their multimodal journeys cycling, mostly for
the first and last mile part;
- Transport planners want to make sure that modal shift includes cycling and it can be fully
part of everyone’s journeys;
- Transport operators want to have cyclists as customers.
Within this theme, we have identified three main uses cases or functional domains for which parking
data for cycling is the most relevant:
 Location and overall description of the parking (e.g., number of available spaces, types of
cycles that can be parked, parking distance from people's residence or work etc.);
 Safety details for both the vehicles and the cyclists (e.g., is the parking guarded?);
 Pricing and additional services (e.g., pricing schema, cleaning supplies, etc.).
State of the art & Differences with existing standards
To address these uses-cases, we found out that:
- Existing data standards such as NeTEx 1 or APDS2 can be used for the static description of
parking and its related components;
- Local specifications have been developed and shared openly, mostly in projects led by local
authorities (e.g., Velopark used by the city of Antwerp);
- Some of the data exists in collaborative maps such as OpenStreetMap, though it is uncertain
how such data can be extracted to be shared with other trip planning applications.
1 https://www.netex-cen.eu/
2 APDS (ISO TS 5206-1:2023) is very closely related to the Part of the DATEX II Standard relating to parking (CEN
TS 16157-6:2022)
[page 10]
10 of 16
However, none of these solutions are comprehensive enough to be adopted at the EU-level for
cycling. The three main hurdles are:
- Standards such as NeTEx or APDS are not specific enough to cycling (e.g., more granular
description of the vehicles’ types, dedicated services, etc.);
- Local specifications cannot always apply more broadly (e.g., administrative representation
of an address);
- The data extracted from OpenStreetMap still convey uncertainty about the data sharing
licence that should be applied, especially when used by commercial third parties.
Recommended actions
Based on the fact that at least 2 recognised standards exist to describe parking locations, services
and facilities, we consider that parking data for cycling could be the easiest to move forward with.
It could also be seen as a natural extension of the MMTIS domain to cycling. For this, we would
recommend:
- The identification of what is missing in NeTEx and APDS to cater to cycling;
- Extend NeTEx and APDS, relying on their usual standardisation processes;
- Collect some data to serve as illustrations;
- Share the data with NAPs and data consumers to get their feedback.
3.3. COUNTING
Priority use cases
Counting has several uses-cases that could be seen as complementary to the two pillars abovementioned. It supports making decisions on the dimensions of infrastructure investment, for example.
Knowing how many cyclists any city/region/Member State has, is key to invest further.
- Modal split and modal share: is one of the basic needs for cities and regions to know, but
not only between modals such as car and bicycle, but also within cyclists (different propulsion,
types of cycles, differences in cyclists etc);
- Planning, infrastructure and investments : this is for example necessary to determine
popular cycling routes and the use of routes, but also to increase safety and finding potential
(new) routes and optimizing routes;
- Monitoring and evaluation: for all projects and policy goals it is necessary to monitor the
effect of changes and the effect of policy goals. Not only is this a need in cities and regions,
but also nationally and on European level.
[page 11]
11 of 16
State of the art & Differences with existing standards
Counting is one of the basic data being collected in all countries and there are already standards
in several countries such as: France, Flanders and the Netherlands. It still differs a lot from motor
vehicle data and especially there is a wish to know more about the differences in the types of cycles
and cyclists, which is still a bit difficult to collect.
Recommended actions
When the European Commission wants to focus more on cycling in and between Member States,
there is a need for uniformity in counting data and their definitions, so trends can be monitored.
The needs for monitoring and the information needed can form a basis for a standard to be
developed.
Onwards we can also make sure that other use cases can be answered with the information that can
be collected in the data standard.
3.4. REAL-TIME DATA
Priority use cases
Real-time data is the fourth pillar that adds information to all other pillars, which can be seen as
static or planned data. Real-time data covers:
- Real time route/path availability based on road works/incidents;
- Seasonal maintenance (de-icing, sweeping, water hazards);
- Parking availability.
State of the art & differences with existing standards
The primary challenge in this topic is that very little comparable standard work has been done.
Furthermore, the application of most information in this category is dependent on at least one of the
other categories. Real-time route planning or seasonal maintenance information is practically
irrelevant without generic standardised infrastructural information. Similarly, real-time parking
availability is dependent on a fairly precise parking capacity estimate. The clear behavioural
differences from automotive queue building to cyclists much freer traversing of the infrastructure
makes many assumptions for existing standards void. As an example, the average travelling speed
of an automotive vehicle is fairly representative of any vehicle travelling in the same lane at
approximately the same time. This is not the case for cyclists were overtaking and individuals
traveling at different speeds are much more common.
Recommended actions
It is the recommendation that cycling in general is promoted to a higher level of both investment and
focus. The specific real-time topic should be addressed in order of prioritised use cases and then
evolved consequently as the three other bicycling topics mentioned here evolves to a stronger level
enabling even further real-time relevant use case support.
[page 12]
12 of 16
4. CONCLUSIONS – ACTIONS TO TAKE
4.1. PREAMBLE
As a prerequisite, the European Commission could give impetus to the approach of the Member
States in order to agree on definitions of the different types of cycling users and related
infrastructures, as detailed in Annex - consistent definition of user categories and uses. These types
of cycling and conditions of use are regulated under different functional and technical requirements,
which raise harmonization issues at EU level.
4.2. GENERAL RECOMMENDATIONS TO THE EUROPEAN COMMISSION
The below are general recommendations in regards to the European legal framework and middleto-long terms actions to be taken.
1. Develop new or amend existing standards for representing:
a. cycling infrastructure data, including as the very minimum the type of infrastructure, its
surface and width; the final report of the UNECE Group of Experts on cycling
infrastructure can be used as a basis for the typology of cycling infrastructure;
b. cycle counting data, including information on the location of counters (geodata), type
of infrastructure, modes counted (vehicles and users), direction, temporary/permanent
counters, start/end of counting, number of passages counted;
c. cycling parking options and their services, to be included in trip planning and multimodal
journeys for all cyclists;
d. real-time information for cyclists that complement the data pillars mentioned above,
e. Cyclist behaviour data, including immediate turn choices, short and long route choices,
O/D information, travel speed, waiting times, etc.
2. Encourage countries that have not yet made a significant progress in establishing relevant
national standards to adopt the common standards as listed in point 1;
3. Where relevant national standards exist already, support development of tools to convert
between them and the common standards;
4. Make providing geolocated data (instead of statistical summaries) in the common standard
about the infrastructure built and its usage obligatory for EU cofinanced projects;
5. Develop or adapt an existing conversion method between the common standards and
OpenStreetMap representation of the cycling infrastructure. This can be used in several
ways:
a. Stop gap provision of infrastructure data where official data is not available or not
yet converted to the common standard;
b. Additional quality check for official data in the areas where it is already available;
c. Better representation of cycling infrastructure in OpenStreetMap in the areas where
official data is already available;
6. Whenever there is work on static data for cycling, to always add the real-time component
to it. It could be done taking inspiration from the MMTIS DR, RTTI DR, SRTI DR, etc. or simply
with how traffic management has fully incorporated real-time data.
[page 13]
13 of 16
4.3. LOW HANGING FRUITS
Based on the above, we have identified some low hanging fruits that seem to be the easiest to
support in a short-to-middle term.
1. Parking data for cycling based on the extension of existing European standards;
2. Cross Member States body focusing on cycling infrastructure standard work already
ongoing in many states working towards a generic common standard, or at least
compatibility between existing national standards;
3. Make providing geolocated data (instead of statistical summaries) in the common standard
about the infrastructure built and its usage obligatory for EU cofinanced projects;
4. Whenever there is work on static data for cycling, to always add the real-time component
to it.
4.4. FUNDING OPPORTUNITIES
The below is not an exhaustive list: it represents the projects that the cycling task force of NAPCORE
has identified as potential funding opportunities to implement the above-mentioned low-hanging
fruits:
1. NAPCORE-X, mostly in its work on Multimodal standards (related to the implementation of
the revised MMTIS DR);
2. The follow-up of European projects dedicated to cycling data, such as MEGABITS,
MERIDIAN… for example;
3. The inclusion of data in infrastructure-led projects, such as the extension of the EuroVelo
network.
In any case, we strongly advocate for a better coordination between all projects related to cycling,
by signing cooperation agreements to relaunch the provision of cycling data to NAPs. As of today,
it sometimes feels that either cycling is funded as a silo or as an after-thought in bigger scale projects
whereas the European Cycling Declaration covered all aspects of cycling and its industries. Such
coordination role could be found within NAPCORE and NAPCORE-X, probably with some Member
States taking a stronger lead in supporting the cycling task force and all other European-supported
activities and projects dedicated to cycling and its data.
[page 14]
14 of 16
5. ANNEX - CONSISTENT DEFINITION OF USER CATEGORIES AND USES
Similar to motorized traffic, it is necessary to identify the different types of cycles (vehicles and
users) and their different conditions of use (infrastructure and situations). This includes cycle ownership
(by cycle category) also covering the rider and their ability to use a given cycle, as well as the
public transport infrastructure/services associated with each cycle category.
1. Running infrastructure (road lane, cycle lane, pedestrian lane)
There are big differences in terms of use of running infrastructure:
• between a bike and a scooter: cycle lanes are usually not allowed for scooters.
• between a bike and an e-bike: the speed of some e-bikes using cycle lanes needs to be
limited for safety reasons, so different categories of e-bikes should be defined (and
standardized).
• between a scooter and an e-scooter: a scooter (driven by a child or an adult) may use
a pedestrian walkway, while an e-scooter most usually must use a general traffic road
lane. The speed of e-scooters may also need to be limited for safety reason.
2. Ownership of cycle (bike, e-bike, scooter and e-scooter)
There are big differences between private cycles and shared cycles (fleets). The latter only are
public transport means of transport - PT cycles. Private cycles and PT cycles follow different
regulations/data categorizations for what regards:
• the characteristics of the cycle (registration, technical regulation) [bike, e-bike, scooter
and e-scooter]
• the attributes of the driver (insurance, age, equipment like helmet…) [bike, e-bike,
scooter and e-scooter]
3. Parking
There are big differences for what regards parking conditions between private cycle and PT cycle
(also depending of the category of cycle [bike, e-bike, scooter and e-scooter]) in terms of:
• public parking areas for private cycles - location, management, pricing, security (locked
or not, guarded or not), battery charging possibilities and conditions, additional services
(maintenance, cleaning…), online and off-line information…
• public parking areas for PT cycles in terms of location, management, pricing, battery
charging possibilities and conditions, additional services (maintenance, cleaning…),
online and off-line information…
The public parking itself might be owned by a public or a private entity.
The cycle parking can be used by a traveller performing (or intending to perform) a monomodal
(cycle) trip or a multimodal (cycle + conventional PT) trip.
Focus of MMTIS should be on parking used by travellers performing a multimodal trip.
[page 15]
15 of 16
4. Conventional (scheduled or on-demand) PT means of transport (road- or rail-borne: bus, tram,
metro, non-SERA train, SERA train, possibly coach; possibly air-borne mode or waterborne mode)
There are big differences regarding the complementarity between cycle (private or PT) and
conventional PT means of transport:
• MMTIS use case(s) type 1: Customer using a conventional PT mean of transport with the
cycle left at a public parking area. Associated cycle parking pricing is usually associated
with the pricing of the connecting conventional PT service (multimodal fare and ticketing
policy).
• MMTIS Use case(s) type 2: Customer boarding its cycle (usually private bike, e-bike,
scooter and e-scooter) on-board a collective PT mean of transport. In such cases the
conditions of use differ according to the PT mode and service, and to the category of
cycle [bike, e-bike, scooter and e-scooter]. Conditions of use (including pricing) may
relate to the physical characteristics of the cycle and/or to the access to the service
(registration or not, reservation of a place or not, number of cycles allowed on-board,
safety (battery) requirements…).
5. Alternative PT means of transport (shuttle bus, shuttle ferry, dial-a-ride service, taxi, carsharing, car-pooling, car-hire, ride-sharing)
In this case of complementarity between cycling and alternative PT services the cycle is treated as
a luggage if boarded on the PT mean of transport.
6. Categories of operators
The PT service operators may have - collectively or individually - differents policies (and therefore
data management and data harmonization needs) regarding the accommodation/complementarity
with cycle:
• collective public transport services operators (e.g. PTAs, PTOs, airlines, mainline rail
companies, coach companies like Flixbus, Blablacar Bus, Alsa, Marino bus)
• taxis or other services with a driver (e.g. Uber, Bolt) or without driver (e.g. bike-sharing,
scooter-sharing)
• car rental companies or carsharing companies etc.
• travel agencies, mainly organisers and most often not operators
• digital mobility services providers (MaaS)
For this reason, future use cases should take into account the opinion of these stakeholders.
[page 16]
16 of 16
6. REFERENCES
1. European Declaration on cycling (April 2024):
https://transport.ec.europa.eu/system/files/2023-1/European_Declaration_on_Cycling_en_0.pdf
2. Delegated Regulation revised (EU) 2024/490 on the provision of EU-wide MMTIS:
https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202400490
3. Delegated Regulation (EU) 2017/1926 on the provision of EU-wide multimodal travel
information services:
https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32017R1926&rid=6
4. Delegated Regulation (EU) 2022/670 on the provision of EU-wide real-time traffic
information services:
https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32022R0670&from=en
5. INSPIRE European Directive: https://inspire.ec.europa.eu/
https://knowledge-base.inspire.ec.europa.eu/
6. iRAP: standardised safety ratings based on globally data including cycling
www.irap.org/cyclerap
7. UNECE Agreed definitions for types of cycling infrastructure:
https://unece.org/transport/documents/2023/01/working-documents/agreed-definitions-typescycling-infrastructure
8. Open Street Map cooperative map under free license:
https://wiki.openstreetmap.org/wiki/Bicycle
9. European Certification Standard for Eurovelo network:
https://pro.eurovelo.com/projects/european-certification-standard
https://eurovelo.com/download/document/ECS-Manual-2021_online.pdf
