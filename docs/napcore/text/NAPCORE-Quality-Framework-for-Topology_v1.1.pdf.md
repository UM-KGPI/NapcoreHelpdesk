url: https://napcore.eu/wp-content/uploads/2025/06/NAPCORE-Quality-Framework-for-Topology_v1.1.pdf
title: NAPCORE Quality Framework for Topology v1.1

[page 1]
A Quality Framework
for Road Network Topology
Report by Task 3.2: European NAPs data quality
Status: final
Version: 1.1
Date: 05- 06 -2025
Legal disclaimer
The sole responsibility for the content of this document lies with the authors. It does not necessarily reflect the
opinion of the European Union. The European Commission is not responsible for any use that may be made of
the information contained therein. All images are provided by the respective partn ers (unless otherwise noted)
and are approved for reproduction in this publication.
[page 2]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 2
Document information
Project acronym NAPCORE
Full project title National Access Point Coordination Organisation for Europe
Grant Agreement No. MOVE/B4/SUB/2020-123/SI2.852232
Activity no. and title WG 3 NAP content and accessibility
Author(s) Stephen T’Siobbel, Frank Daems (ERTICO-TN-ITS innovation platform)
Co-author(s) Michelle Fransen (NDW NL), Rodolfo Gomes Da Silva (Kios CY), Nele Dedene
(MOW Flanders)
Related to Milestone no. M3.8
External Milestone Yes (inputs to)
Document history
Version Date created/ modified by Comments
0.1 01/06/2024 Stephen T’Siobbel First draft
0.5 06-02-2025 Stephen T’Siobbel; ir Frank
Daems
Draft for final review
0.7 19-03-2025 Frank Daems Update during the on line meeting
0.8 01-05-2025 Stephen T’Siobbel General updates
1.0 07-05-2025 Frank Daems Finalisation
1.1 05-06-2025 Peter Lubrich Activity Leader Review
Action requested
☐ To be revised by partners involved in the preparation of the document
☐ For review/ approval by the Core Alignment Team
☐ For approval by the NAPCORE Steering Committee
Abbreviations
Abbreviation Meaning
EC European Commission
FCD Floating Car Data
GDF Geographic Data File
INSPIRE Infrastructure for Spatial Information in the European Community
GIS Geographic Information System
ITPS Intelligent Truck Parking Services
MMTIS Multimodal Travel Information Services
NAP National Access Point
NAPCORE National Access Point Coordination Organisation for Europe
[page 3]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 3
OGC Open GIS Consortium
OSM Open Street Map
RTTI Real-Time Traffic Information Services
SDBMS Spatial Database Management Systems
SRTI Safety-Related Information Services
TN-ITS Transport Network ITS
WG Working Group
UVAR Urban Vehicle Access Regulation
[page 4]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 4
Table of contents
1. INTRODUCTION ................................................................................................................................ 5
1.1 BACKGROUND OF THIS DOCUMENT ......................................................................................................... 5
1.2 METHODOLOGY .................................................................................................................................. 5
2. SCOPING ........................................................................................................................................... 7
2.1 WHAT IS TOPOLOGY DATA? ................................................................................................................... 7
2.2 ROAD (SPECIFIC) TOPOLOGY AS THE BASIS FOR SIMPLE AND COMPLEX ROAD FEATURES ................................... 8
2.3 EXAMPLES OF TOPOLOGICAL ELEMENTS OF A ROAD NETWORK .................................................................. 10
2.4 EXAMPLES OF ROAD TOPOLOGY RULES (CHECKS) .................................................................................... 12
2.5 DATA SOURCES FOR ROAD NETWORK TOPOLOGY .................................................................................... 13
3. RELEVANT USE CASES ..................................................................................................................... 14
4. RELEVANT DATA TYPES IMPACTING ROAD NETWORK TOPOLOGY ............................................... 15
5. RELEVANT DATA PROVIDERS.......................................................................................................... 19
6. APPLIED QUALITY DEFINITIONS ..................................................................................................... 20
6.1 REFERENCE TO THE NAPCORE QUALITY FRAMEWORKS .......................................................................... 20
6.2 IDENTIFICATION OF RELEVANT RULES .................................................................................................... 21
6.3 EXEMPLARY DEFINITION OF QUALITY DIMENSIONS, CRITERIA AND METRICS .................................................. 24
6.4 ASSESSMENT OF THE EXEMPLARY DEFINITION OF QUALITY DIMENSIONS, CRITERIA AND METRICS ..................... 31
7. FURTHER EVALUATIONS NEEDED ...................................................................................................... 32
7.1 GENERATED INSIGHT .......................................................................................................................... 32
7.2 FUTURE HANDLING THE DATA QUALITY ISSUE IN THE CONTEXT OF ROAD NETWORK TOPOLOGY ....................... 32
8. CONCLUSIONS .................................................................................................................................... 33
REFERENCES ........................................................................................................................................... 34
[page 5]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 5
1. Introduction
1.1 Background of this document
The objective of this document is to inform the reader about the definition, scope and criteria for a
quality framework related to data related to road network topology. It will als o guide the reader on
the methodology applied to come to this quality framework description. The document reflects the
work and conclusions of participants in the NAPCORE task 3.2, representing experts from
governmental agencies and map and service providers , as well as members of the TN -ITS ERTICO
innovation platform1.
The basic concepts behind the NAPCORE quality elaborations, including questions like “ Why do we
need a Quality Framework for ITS Services and ITS Data? ” and “What is a Quality Framework for ITS
Services and ITS Data?” have been explained in a generic report by NAPCORE Task 3.22.
This presented quality framework for data related to road topology aims to enable the quality
assessment of topological features in digital maps , enabling use cases and connectivity functions to
support, e.g., route planning, navigation, spatial queries etcetera . It leads to a b etter and common
understanding of the quality related topics related to topology and its underlying data.
1.2 Methodology
The task followed a structured methodology to develop this quality framework for road network
topology. The process began with an initial planning phase in which participants were introduced, and
the overall approach was established. Early discussions focused on the significance of topology within
the quality framework and the relevance of existing standards such as GDF , INSPIRE and TN -ITS
(chapter 2). The team also identified key use cases (chapter 3) and created a priority list to ensure that
efforts were directed toward the most critical aspects of road network topology quality.
Following this initial phase, the focus shifted toward clarifying definitions and developing use cases.
Presentations and discussions helped refine key terminology, while a list of use cases was identified
and prioritized for inclusion in the quality framework.
The next stage involved technical discussions and data exploration (chapter 4). The team evaluated
existing topological checks available in commercial GIS tools and investigated their applicability to the
framework. There was also an effort to study other NAPCORE Task 3.2 quality frameworks such as the
FCD, UVAR, etc (as published on the NAPCORE Quality Repository3), and the NAPCORE data dictionary4.
Further discussions explored data source identification and validation methodologies to strengthen
the reliability of the framework. During this period, industry stakeholders, including HERE and
TomTom, were engaged to provide input on essential aspects of road network topology, ensuring that
both public and private sector perspectives were incorporated. Industry representatives provided
1 https://tn-its.eu/
2 https://napcore.eu/wp-content/uploads/2025/03/1_NAPCORE-M3.8-deliverable_v1_250317.pdf
3 https://napcore.eu/quality/
4 https://napcore.eu/its-mobility-data-dictionary/
[page 6]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 6
input to identify the top five topology -related quality rules, which formed a key component of the
framework.
As the project progressed, the focus shifted toward developing concrete quality criteria and validation
rules (chapter 5) . Iterative reviews of the draft milestone report allowed for the refinement of
methodology and ensured that applicable data standards were incorporated. This iterative process
continued throughout the latter half of the process for this quality framework , culminating in a
structured and well-evaluated approach to road network topology quality assessment.
The final phase involved the consolidation and reporting of findings (chapter 6). The team conducted
a recap of previous actions and set a plan for finalizing the framework. Internal reviews helped refine
the deliverable, and preparations were made for upcoming meetings to ensure that the milestone
report was fully aligned with regulatory requirements and practical industry applications.
Throughout this process, a broad range of stakeholders contributed to the discussions, including public
authorities from various European countries and private sector representatives. A combination of
online meetings and in -person discussions facilitated e ffective collaboration, ensuring that both
theoretical and practical perspectives were considered. The project was structured with clear
objectives, and each meeting concluded with actionable next steps to maintain progress. The iterative
nature of the dis cussions and the continuous refinement of deliverables helped ensure that the final
report addressed all critical aspects of road network topology quality. The engagement of relevant
stakeholders and the structured evaluation of findings indicate a well -managed and comprehensive
approach to the development of the quality framework.
[page 7]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 7
2. Scoping
2.1 What is topology data?
The current report targets the development of a Quality Framework (QF) for Road Network Topology
and its underlying data. The topology of a road network refers to the arrangement or structure of the
network, including how roads are connected and the relationships between different segments or
nodes within the network. It encompasses aspects such as the layout of roads, intersections, junctions,
and the paths that vehicles can take to navigate from one point to another.
In the context of road databases, topology and geometry are two fundamental concepts that describe
different aspects of spatial relationships and structures, and it is important to understand their focus.
The definitions presented below reflect s those which can be concluded from the most relevant
international standards as GDF (ISO/FDIS 20542-1:2019), OCG and INSPIRE, starting with Geometry:
Geometry
• Definition: Geometry refers to the actual geometric shapes and coordinates that define the basic
road features, such as (shape) points, lines, and polygons.
• Focus: It primarily deals with the spatial location and arrangement of individual geometric
elements of a road.
• Example: In a map, geometry describes the specific coordinates of a point, the shape of a line, or
the boundary of a polygon.
Turning to the main topic of this report:
Topology
• Definition: Topology describes the spatial relationships and connectivity between different
geometric elements of a road.
• Focus: It is concerned with how features are related to each other, including adjacency,
containment, and connectivity.
• Example: Topology would describe whether two lines representing roads intersect, whether a
point is inside a polygon (area), or how polygons share common boundaries.
In essence, while geometry deals with the actual shapes and positions of spatial/road features,
topology is concerned with the relationships and connectivity between these features. Both concepts
are essential in spatial data analysis and geographic information systems (GIS) to accurately represent
and analyse real-world spatial phenomena, such as roads. Also, both concepts support the use of digital
maps for planning ( vehicle routing), driving ( vehicle navigation), and tactical purposes (vehicle
overtaking, merging, etc.)
Understanding the topology of a road network is crucial for urban planning, traffic management, and
optimizing transportation systems for efficiency, safety, and convenience (e.g., Routing and Navigation
ADAS and Automated Driving). A subsequent chapter in this document addresses use cases within the
scope of RTTI.
The following figure concludes the relationship between topology and geometry.
[page 8]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 8
TOPOLOGY ≠ GEOMETRY
Figure 1 – Relationship between topology and geometry
2.2 Road (specific) topology as the basis for simple and complex road features
This chapter looks into the definitions of road topology in some main representations such as GDF and
OSM. It also elaborates on why these levels are identified and their applications.
Having described the difference between geometry and topology in the previous chapter, it helps to
understand how road databases are modelled by looking into a reference of geographic data
modelling: GDF (ISO/FDIS 20542-1:2019).
In GDF, and its derived descriptions, three levels of (cartographic) representation are defined:
• Level 0 (Topology): This level contains elementary GIS topology components. No features overlap
in any way, and neighbouring relationships are known. Everything is described by cartographic
primitives as Nodes, Edges and Faces.
• Level 1 (Features): Level 1 contains simple features like road elements, rivers, boundaries, and
signposts. Features can have attributes that are specific to the feature (for example, one way,
width of the road, number of lanes). Features can also have rel ations, which are very important
for car navigation systems. For example, relations can include “forbidden turn from road element
1 to road element 2” or “road element 1 has priority over road element 2.”
• Level 2 (Complex Features): At this level, the level 1 “simple features” are aggregated to a higherlevel feature. For example, at level 1, all road elements of an intersection are represented. At level
2, the intersection may only be represented with a single point.
While OSM does not explicitly define "road topology" as a separate layer (as in GDF), the way its data
is structured aligns with the Level 0 and Level 1 definitions from GDF:
• Level 0 (Topology): Represented by the node and way connectivity in OSM's raw data.
• Level 1 (Features): Achieved through tagging that defines roads, intersections, and other features
with attributes.
Note that OSM data is used by many tools (e.g., routing engines ) to build topological models of road
networks for navigation, urban planning, and analysis.
[page 9]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 9
The definition of these different representation levels serves several key purposes in geographic data
modelling and practical applications. These purposes address the complexity, abstraction, and utility
of the data for various use cases:
Abstraction and Simplification
Each level represents a higher level of abstraction:
Level 0 (Topology) is the most granular, dealing with raw geometric and topological primitives (nodes,
edges, and faces) that serve as the building blocks of the map.
Level 1 (Features) abstracts these primitives into recognizable, real -world entities like roads or rivers,
along with attributes and relationships.
Level 2 (Complex Features) further simplifies and aggregates detailed features into larger,
conceptualized entities, like entire intersections or regions. This abstraction allows users to choose the
level of detail appropriate for their needs. For example: a traffic simulation might require Level 0 or
Level 1 data for detailed movement modelling . Or, a high-level navigation system might rely on Level
2 data for simplified route planning.
Data Usability and Flexibility
The levels enable the same data to serve different applications and audiences:
Technical experts (e.g., GIS analysts) might work with Level 0 data for detailed spatial analysis and
engineering tasks. Mapmakers might use Level 1 data to create user-friendly visualizations. Navigation
systems might focus on Level 2 data for efficient route calculation, where granular details like
individual road segments or turns aren't required.
Data Optimization and Performance
Higher levels of abstraction reduce the volume of data that needs to be processed, which improves
performance in systems where detailed topology isn’t necessary. For instance, navigation systems use
aggregated Level 2 features to quickly calculate routes without dealing with the computational
complexity of individual road segments and their connections.
Standardization and Interoperability
For example, the GDF framework ensures a standard structure for geographic data, making it easier to
share, integrate, and interpret data across different systems and applications. Defining these levels
help clarify how the data is structured and at what level of abstraction it can be accessed or utilized.
Scalability for Different Use Cases
Different applications may require different scales or levels of detail: Level 0 is essential for precision
tasks like urban planning or micro -level simulations. Level 1 strikes a balance between detail and
usability for most mapping and navigation purposes. Level 2 works best for high -level planning, such
as logistics or long-distance navigation, where fine details may not matter.
Examples of Purpose in Practice
Urban Planning: A city planner might use Level 0 data to analy se the connectivity of a road network
and design infrastructure improvements. Car Navigation Systems: These systems primarily rely on
Level 1 data (road elements and attributes) for routing and Level 2 data for simplified navigation and
[page 10]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 10
user display. Cartographic Representation: When producing maps at different scales, Level 1 and Level
2 provide suitable abstractions for creating legible visualizations without cluttering the map with
excessive detail.
Conclusion: related to this document subject level O and level 1 (road) are both considered in the road
network topology framework
2.3 Examples of topological elements of a road network
This chapter gives some examples of road network topological elements.
Direction of travel (level 1)
The direction of travel on a road is a crucial aspect of road network topology. It determines the flow
of traffic and influences how routes are planned and navigated within the network. In some road
network representations, the direction of travel is explicitly indicated, such as one -way streets or
highways with divided lanes. This information helps drivers and navigation systems determine the
correct route to take to reach their destination efficiently. Additionally, understanding the direction of
travel is essential for traffic management, including implementing traffic signals, signage, and lane
markings to regulate the flow of vehicles and prevent accidents or congestion. So, while the physical
layout of roads and their connections forms the backbone of road network topology, the directionality
of travel plays a significant role in how the network operates and is organized.
Junctions (level 1)
The presence of a junction is indeed a fundamental topological element in a road network. A junction
is where two or more roads intersect or meet, forming a node in the network. Junctions can vary in
complexity, from simple T-intersections to complex multi-lane intersections or roundabouts. Junctions
play a crucial role in determining the connectivity and structure of the road network. They define how
different segments of roads are connected and how traffic can flow between them. The configuration
and design of junctions influence factors such as traffic flow, safety, and efficiency within the network.
In road network analysis and modelling, junctions are often represented as nodes, and the roads
connecting them are represented as edges or links. Understanding the distribution and characteristics
of junctions helps transportation planners and engineers assess the performance of the network,
identify congestion hotspots, optimize traffic signal timings, and plan infrastructure improvements.
Therefore, the presence and characteristics of junctions are integral to the topology and functioning
of a road network.
Manoeuvres at intersections (level 2-out of scope of this document)
Manoeuvres at intersections are indeed a crucial aspect of road network topology. An intersection is
a key point where multiple roads meet, and manoeuvres at these intersections include actions such as
turning left, turning right, going straight through, or making U -turns. The design and layout of
intersections greatly impact traffic flow, safety, and efficiency within the road network. Different types
of intersections, such as roundabouts, T-intersections, four-way intersections, and complex multi-lane
intersections, require different types of manoeuvres and have specific rules governing right -of-way
and traffic flow. Understanding intersection manoeuvres is essential for drivers to navigate
intersections safely and efficiently. It also influences urban planning decisions, such as the placement
of traffic signals, signage, lane markings, and pedestrian crossings, to manage traffic and prioritize
various mo des of transportation. Moreover, modern transportation systems and navigation
technologies often consider intersec tion manoeuvres when providing route guidance to drivers,
[page 11]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 11
helping them choose the most appropriate path based on their destination and current traffic
conditions. Therefore, manoeuvres at intersections are an integral part of road network topology and
transportation planning.
Lane information (level 1)
Lane information in a road network can be considered an important element of road topology,
especially in modern road networks and transportation systems. While traditional road network
topology primarily focuses on the connectivity and layout of roads and intersections, lane information
adds another layer of detail that influences traffic flow, routing decisions, and overall network
performance. Here's how lane information contributes to road network topology:
• Lane Configuration: The number and type of lanes on a road (e.g., travel lanes, turning lanes, bus
lanes, bike lanes) affect how traffic moves within the network. Lane configurations at intersections
and along road segments determine permissible manoeuvres, such as turning left, turning right,
or going straight through.
• Lane Assignments: Lane information can specify which lanes are designated for specific types of
vehicles or movements. For example, some lanes may be reserved for buses, bicycles, or high -
occupancy vehicles (HOV), while others are for general traffic or specific turning movements.
• Lane Connectivity : Lane information also includes how lanes merge, split, or transition at
intersections and along road segments. This aspect influences the continuity of travel paths and
the complexity of manoeuvres required at junctions.
• Lane Markings and Signs: Lane information encompasses lane markings, signage, and signals that
provide guidance to drivers regarding lane usage, lane changes, and manoeuvring at intersections.
This information is crucial for ensuring safety and efficient traffic flow within the network.
• Lane-Based Routing : In advanced transportation systems and navigation technologies, lane
information is used for lane -based routing, where drivers are guided to specific lanes based on
their destination, the type of manoeuvre required, and current traffic conditions. This enhances
route accuracy and helps optimize traffic distribution across lanes.
Overall, lane information complements traditional road network topology by providing detailed
insights into how traffic moves within the network and how lanes are utilized for different purposes
and manoeuvres. Therefore, it can be considered an essential element of road network topology,
particularly in the context of modern transportation planning and management.
Priority Regulations (level 1)
Priority regulations, such as right-of-way rules and traffic control mechanisms, are indeed an integral
aspect of road network topology. While they may not be physical features like roads or intersections,
they govern the behaviour of vehicles within the network and influence its structure and functioning.
Here's how priority regulations contribute to road network topology:
• Intersection Control: Priority regulations determine which vehicles have the right -of-way at
intersections, affecting how traffic flows through junctions. For example, traffic signals, stop signs,
yield signs, and roundabouts allocate priority to different streams of traffic, shaping the dynamics
of movement within the network.
• Lane Assignment: Priority regulations often dictate lane assignments based on specific conditions
or vehicle types. For instance, lanes may be designated for buses, bicycles, or turning movements,
with corresponding right-of-way rules to manage interactions between different types of traffic.
[page 12]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 12
• Traffic Flow: Priority regulations help regulate the flow of traffic within the network by establishing
rules for merging, yielding, overtaking, and other manoeuvres. These regulations contribute to
safety, efficiency, and predictability in traffic movements.
• Pedestrian Crossings: Priority regulations also apply to pedestrian crossings, determining when
and where pedestrians have the right -of-way to cross roads. Features like crosswalks, pedestrian
signals, and traffic calming measures influence pedestrian movement within the network.
• Special Circumstances: Priority regulations may include provisions for special circumstances such
as emergency vehicles, construction zones, school zones, and temporary traffic controls. These
regulations ensure that priority is given to critical activitie s while maintaining the overall
functionality of the network.
In summary, priority regulations are essential components of road network topology as they govern
the interaction between vehicles, pedestrians, and other users within the network. By establishing
rules for right-of-way and traffic control, priority regula tions shape the behaviour of participants and
contribute to the overall structure and efficiency of the road network.
2.4 Examples of Road Topology rules (checks)
Topological checks in road databases are important for ensuring the consistency and integrity of spatial
data. These checks help verify the relationships and connectivity between geometric elements. Some
common topological checks that can be made in spatial databases . For each rule, an example of
importance in a road network is given.
Intersection Check:
• Verify that geometries do not intersect inappropriately, based on the data model's rules.
• Ensure that lines do not cross unless there is a proper node or intersection point.
• Prevents unrealistic crossings without connections (e.g., bridges vs intersections).
Containment Check:
• Ensure that polygons do not improperly contain other polygons. For example, a country boundary
should not contain another country's boundary.
• Ensures spatial correctness, such as jurisdiction-based routing.
Adjacency Check:
• Verify the adjacency relationships between spatial features. For instance, check if polygons share
common boundaries where they are expected to.
• Important for lane-level modelling or adjacent zones.
Connectivity Check:
• Ensure that network-based spatial data (such as road networks) is properly connected. Check for
gaps or isolated segments that could affect routing.
• Crucial for routing algorithms; avoids disconnected roads.
Node and Edge Checks:
[page 13]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 13
• Verify the correctness of nodes and edges in network data. Ensure that nodes connect to the
correct edges, and edges do not have unexpected intersections.
• Prevents logical errors in graph representation.
Directionality Check:
• In cases where the direction of features matters (e.g., one -way streets), verify that features have
the correct orientation.
• Essential for turn-by-turn navigation and legal movement.
Overlap Check:
• Ensure that polygons do not overlap unless they are meant to, such as in the case of administrative
boundaries.
• Prevents errors in map rendering and routing (e.g. overlapping roads).
Boundary Consistency Check:
• Verify that boundaries of adjacent features align correctly. This is crucial for maintaining
consistency in spatial relationships.
• Important for spatial queries and jurisdictional reporting.
Cyclic Dependency Check:
• Ensure that there are no cyclic dependencies in network data, which could lead to infinite loops in
network traversals.
• Useful in network modelling and preventing infinite loops in algorithms.
Dimensionality Check:
• Verify that the dimensionality of spatial objects is consistent. For example, a point should not be
represented as a polygon.
• Ensures correct elevation modelling or bridge/tunnel representation.
Planar vs. Non-planar Geometry Check:
• Ensure that geometric objects are appropriately planar or non -planar based on the spatial model
being used.
• Supports realistic modelling of grade-separated roads (bridges, tunnels).
Implementing these checks can help ensure the accuracy and reliability of spatial data in databases.
Many Spatial Database Management Systems (SDBMS) provide tools and functions for performing
these topological checks. In the context of NAPCORE: these checks are typically done by the DBMS at
the side of the road authority before the data is shared with 3rd parties.
2.5 Data sources for road network topology
Sources for such data as mentioned in previous section are manual or automated insertion in the
digital map representation based upon pdf, arial picture, traffic regulation orders, floating car data
(FCD), mobile mapping data (e.g., street view data), etc.
[page 14]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 14
3. Relevant use cases
Digital maps have become integral to the operation and enhancement of transport services, driving
innovation and improving user experiences across the globe. Within the scope of this document the
topological aspects enables a number of use cases . A selection of use cases are (Non exhaustive):
• Route planning: Digital maps provide up-to-date road geometry and topology, turn
restrictions, and traffic rules, allowing navigation systems to calculate the fastest or most
efficient routes.
• Traffic management (alternative routes): Real-time map data, including congestion and
incidents, enables traffic control centres and apps to suggest alternative routes to balance
traffic loads and reduce delays.
• Emergency service: Accurate, routable maps help emergency responders reach incidents
faster by identifying the quickest paths and considering temporary changes like closures or
one-way streets.
• ISA (Intelligent Speed Assistance): Digital maps supply precise speed limit data that onboard
systems use to warn drivers or limit vehicle speed, enhancing road safety and regulatory
compliance.
• Road works and road blocks: Map updates reflecting temporary changes in road accessibility
ensure drivers and systems are aware of closures or detours, reducing confusion and
improving safety.
• Powertrain management for trucks: Digital maps with elevation, curvature, and traffic data
enable energy-efficient route selection and adaptive engine/transmission control to reduce
fuel consumption and emissions.
The relevance of topological data is depending on the use case; hence the quality rating of the
topological data depends on the use case.
E.g. for the topological element ‘direction of travel’ with the value: ‘one way street’, the relevance is
related to the use cases: route planning, traffic management, emergency service , … The project team
carried out a more in depth study, unfortunately no consensus was reached. This result illustrates the
difficulty how to approach the topic of quality related to topology data.
[page 15]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 15
4. Relevant data types impacting road network topology
Road topology itself is not directly coded in data, but it is the result of processed data in a digital map.
Therefore, we look to the actual types of data that impact road topology.
In a first instance the most relevant sources are th ose mandated by the Delegated Regulations in the
context of the ITS Directive 2010/40/EU5. The following tables presents the data types described in the
various Delegated Regulations. For these mandated data types, priorities have been set by the
commission. In the below table, the priority for availability on 1 -1-2025 is put in yellow (first left
column). For each mandated data type, the related Delegated Regulation has been mentioned.
Obviously, not all mandated data is relevant to road topology. The last column indicates this relevance.
Some discussions are possible. Therefore, the following color code has been applied, according to the
specifications of topology, previously mentioned in this document.
• Green: It is relevant for road topology
• Yellow: discussion is possible, relevance is not clear
• Red: this data has no relevance for road topology.
5 https://eur-lex.europa.eu/eli/dir/2010/40/oj/eng
[page 16]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 16
Table 1 - Data types in the Delegated Regulations and their relevance to road network topology
[page 17]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 17
[page 18]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 18
[page 19]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 19
5. Relevant data providers
The current report , being an output of the NAPCORE project, is naturally focused on data provided
through National Access Points (NAPs) – or may be provided in the future – and their data providers.
In general , digital maps describing road networks are available from authoritative sources across
Europe from:
• Mapping Agencies
• Road Authorities
These digital maps may be their own produce and/or may reflect maps, or elements of them, obtained
from different sources, such as:
• Commercial map providers
• Community maps, e.g. OSM, Overture
[page 20]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 20
6. Applied Quality Definitions
6.1 Reference to the NAPCORE Quality Frameworks
The Quality Frameworks (QFs) by NAPCORE Task 3.2 usually apply a certain nomenclature.
First, there are quality dimensions that group several quality criteria. Each quality criterium can be
assessed with metrics. The acceptance of data needs to meet a certain value of each of the metrics.
An example for the usage of the nomenclature, as applied for the Quality framework for floating car
data (FCD), is presented in below picture:
Figure 2 – Example for the nomenclature from the Quality Framework for Floating Car Data
In the QF for FCD, the applied quality dimensions are: “Correctness, Completeness, Timeliness,
Reliability, Usability”
As an example, the quality criteria for the quality dimension “Correctness” are: Accuracy, Bias rate,
Classification correctness, Granularity, see the following table.
Table 2 – Overview of quality dimensions and quality criteria from the FCD QF
For each of the criteria one or more metrics can be defined.
In this FCD QF the possible metrics for Accuracy (error rate) can be:
• Pearson Correlation Index (CI)
• Mean Absolute Percentage Error (MAPE)
• Root Mean Squared Error (RMSE)
• Per Mile Absolute Time Error
[page 21]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 21
The FCD QF and other NAPCORE QFs can be found at the NAPCORE Quality Repository6.
6.2 Identification of relevant Rules
Before defining quality dimensions, criteria and metrics for the topology topic, we defined relevant
‘rules’ to be applied for individual topological data, which can be applied as road network topology
elements.
As an exercise, since we cannot address all related road network topology data, the team looked at
selected topological data.
We consider the following exemplary topological data:
• Polygon layers (level 0 in the topology)
• Line layers (level 0 in the topology)
• Road segments (level1 in the topology)
Next, we asked digital map service providers via a small survey launched in the task, what the most
relevant rules are in the process of creating topological maps. The following lists compile the top 5
rules per topological data.
Top 5 rules on the topological data “Polygon Layers” (level 0):
1. No Gaps allowed Between Polygons
Rule: Ensure that there are no gaps between adjacent polygons.
Importance: This is essential for maintaining continuous coverage of areas, such as land use or zoning
maps, ensuring every part of the region is accounted for.
2. No Overlaps allowed Between Polygons
Rule: Adjacent polygons should not overlap.
Importance: Overlapping polygons can lead to inaccuracies in area calculations and
misrepresentations of spatial relationships.
3. Polygons Must Be Closed
Rule: Polygons must form closed loops, meaning the start and end points of the boundary should
coincide.
Importance: Open or unclosed polygons can cause errors in spatial analysis and render the data
unusable.
4. Polygons Must Not Self-Intersect
6 https://napcore.eu/quality/
[page 22]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 22
Rule: A single polygon should not cross over itself.
Importance: Self-intersecting polygons can create invalid geometry, leading to errors in spatial
operations like buffering and overlay.
5. Must Be Single Part
Rule: Each polygon feature should be a single, contiguous part without disjoint segments.
Importance: Multi-part features can complicate spatial operations and analysis, leading to errors in
data interpretation.
The metrics for these requirements is the number of infringements in a certain digital topological
map
Top 5 rules for Line Layers (level 0):
1. Lines Must Not Self-Intersect
Rule: A single line feature should not cross over itself.
Importance: Preventing self-intersections ensures the accuracy of network analyses, such as
determining the shortest path or flow within networks.
2. Lines Must Not Have Dangles
Rule: Lines should not have dangling ends unless they are supposed to represent a dead-end.
Importance: Dangles can indicate incomplete data or errors in digitization, leading to inaccuracies in
network connectivity analysis.
3. Lines Must Be Properly Snapped
Rule: Line endpoints must be properly snapped to the endpoints of adjacent lines or to vertices of
polygons when necessary.
Importance: Ensuring proper snapping prevents gaps or overshoots, which is crucial for maintaining
connectivity in network analyses.
4. Lines Must Not Overlap
Rule: Line features representing the same network element should not overlap each other.
Importance: Overlapping lines can cause redundancy and inaccuracies in length calculations and
network analysis.
5. Lines Must Be Single Part
Rule: Each line feature should be a single, contiguous part without disjoint segments.
[page 23]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 23
Importance: Multi-part line features can complicate spatial operations and analyses, leading to errors
in data interpretation.
Top 5 rules for Road Transport Networks in GIS (level1):
1. Road Segments Must Connect at Intersections
Rule: Road segments must connect at intersections, meaning the endpoints of road segments should
meet precisely at junctions.
Importance: Ensuring proper connections at intersections is crucial for accurate routing and
navigation. This prevents gaps or misalignments that can disrupt network continuity and affect travel
time calculations.
2. No Overlapping Road Segments
Rule: Road segments representing the same stretch of road should not overlap each other.
Importance: Overlapping road segments can lead to redundancy and inaccuracies in distance and
travel time calculations. Avoiding overlaps ensures a clean and accurate representation of the road
network.
3. Road Segments Must Not Have Dangles (Unless Dead-Ends)
Rule: Road segments should not have dangling ends unless they are supposed to represent a deadend or cul-de-sac.
Importance: Dangling ends can indicate incomplete or incorrect data, affecting the network's
connectivity. Properly terminated road segments ensure accurate routing and network analysis.
4. Road Segments Must Be Properly Snapped
Rule: The endpoints of road segments must be snapped to the endpoints of adjacent segments or to
intersection nodes.
Importance: Ensuring that road segments are properly snapped prevents gaps or overshoots,
maintaining the network's integrity and ensuring accurate analysis of connectivity and traffic flow.
5. Road Segments Must Have Correct Directionality
Rule: Road segments must have the correct directionality, reflecting one-way streets and the proper
flow of traffic.
Importance: Correct directionality is essential for accurate routing and navigation. Incorrect
directionality can lead to routing errors and inaccurate travel time predictions, affecting traffic
management and navigation systems.
[page 24]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 24
6.3 Exemplary definition of quality dimensions, criteria and metrics
As the next step, we provided exemplary definitions of quality dimensions, criteria and metrics for
the above-mentioned quality rule nr 4 for Road Transport Networks in GIS (level 1): ‘Road Segments
must Be Properly Snapped‘.
The following table compiles a preliminary set of such definitions, including the semantics,
mathematical formulations and value ranges.
[page 25]
Table 3 – Definition of quality dimensions, criteria and metrics for the rule ‘Road Segments must Be Properly Snapped‘
Quality
dimension
Quality
criterion
Criterion description Metrics
(Dimension
Sub-element)
Metric description Mathematical formulation Possible values
Correctness Geometry
correctness
(Position
accuracy)
Topology QF - Precise
geometry (road
segments and of
intersection) to ensure
that the real-world is
correctly represented
(reflect the reality of
the physical world).
Coordinate
Precision
Geographic coordinates of road segments endpoints are
accurate and precise with the physical world
All road segment endpoints coordinates
must be the same at the intersection.
To achieve this, user should apply
snapping techniques (e.g. ‘enable
snapping’) during digitization or editing,
to ensure that the endpoint will
automatically snap precisely to the
junction, avoiding any digitization errors
and ensuring that the coordinates of the
endpoints and the junctions are identical.
Snapping Tolerance: distance tolerance
between the pointer and the geometric
element. If the pointer is within this
distance, the snap will automatically align
the pointer with the element.
Possible Snapping type:
Vertex Snap – This will move
the pointer to the closest vertex
of a polyline or polygon
feature, based on the snapping
tolerance.
Snapping on Intersection – This
will enable snapping to the
intersections, even if there are
no vertices at the intersection.
16.3. Editing — QGIS Documentation
documentation
Use snapping—ArcGIS Pro |
Documentation
Logical
consistency
To ensure that the
data follows the
structure and rules
established
Topological
consistency
Quality measure: Number of Errors or Error rate (undershoots
and overshoots, above a specified connectivity tolerance.)
For example, 10 out of 1000 road links show an error, resulting
in an error rate of 1% for topological consistency.
Undershoot:
Topological consistency ensures that
features in the dataset (i.e. road
segments, intersections) conform to
topological rules. In this context, it would
check whether road segments meet at
intersections without overshoots or
undershoots.
[page 26]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 26
Overshoot:
This quality criteria calculates the number
of road segments in the dataset with
connection discrepancies due to
undershoots, and overshoots that exceed
the specified connectivity tolerance
parameter.
* INSPIRE Data Specification on Transport
Networks - Technical guidelines uses the
concept of connectivity tolerance parameter
which defines the acceptable threshold distance
for features to be considered connected.
(Mentioned in Inspire technical guide and
Commission Regulation No 1089/2010 - Annex
II. Section 7.9.6)
Example:
Two road links should meet at
a four-way intersection, but
one road ends in a distance
away than the connectivity
tolerance from the intersection
point. This is a topological
error due to missing
connectivity (undershoot).
Two road links should meet at
a four-way intersection, but
one road ends overlapping the
intersection point and the
other road links. This is a
topological error due to
overlap connectivity
(overshoot).
Note: QGIS has in-built topology checker
mechanism, ArcGIS can validate topology with
Error inspector
Reference : ISO 19157
Conceptual
Consistency
Error Count
(count of all records in the dataset that are not aligned with the
conceptual schema)
The total number of records in the dataset
that do not comply with the rules of the
[page 27]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 27
conceptual schema (example of inspire
conceptual schema). Conceptual
consistency ensures that the data follows
the rules of the conceptual schema (i.e.,
the model that describes how the data
should behave and be structured). This
conceptual schema is usually built upon a
common conceptual schema language (i.e.
UML) and specifies requirements on the
properties of each spatial object.
Example:
If the transport network
conceptual schema the
showing that the "A" roads
must connect to "A” roads or
"B” roads at intersections, and
the "C" roads only allowed to
connect to the "B” roads at
intersections (not directly to
the "A” roads), and in the
dataset there is a "C” road that
is incorrectly connected to a
"A" road at intersection, then
this is a conceptual consistency
violation.
If in the transport network
conceptual schema, the roads
are classified based on their
function (e.g., highway, “A”
road, "B” road) and on the
dataset the road is incorrectly
classified (e.g., "B” road
classified as highway) this
would be a conceptual
inconsistency.
Reference: ISO 19157
Geometry correctness (Intersection Information)
Include accurate information about the
number of lanes, lane types (e.g., bus
lanes) to correspond to an intersection (if
it connects correctly with the road
segments).
Connectivity index
Calculate the number of road
segments connected at each
node.
Geometry correctness (Intersection Information – Traffic
Rules)
In relation to the route planning and
travel time maybe it’s important to have
accurate information of the traffic rules
Attribute matching
accuracy
[page 28]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 28
on the intersection (e.g no left turn,
entering highway)
Calculate the percentage of
matching attributes (e.g., road
type, lane count) between
connected segments
Domain
Consistency
Error Count
The total number of records in the
dataset that do not comply with their
defined value domain (e.g. domain value
should be consistent as per domain of
valid values in the application schemas
properties requirements of the spatial
object). Domain consistency ensures that
attribute values fall within the predefined
valid range or domain for each attribute.
Example:
If the transport network
schema defines that speed
limits should be within a
specific range (e.g., 30 to 120
km/h for roads), and a road
segment has a speed limit
value outside of this range
(e.g., 250 km/h), this would be
a domain inconsistency. The
data must follow the defined
domain of acceptable speed
limits.
Another example could be in
the case of road length, if in
the schema defines that the
maximum length of secondary
road is 10 km and the dataset
showing a secondary road with
a length of 12 km then this is a
domain consistency violation.
Verify that roads are classified
correctly based on their
functional characteristics, such
as residential, commercial, or
industrial zones.
Reference: ISO 19157
[page 29]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 29
Format
Consistency
Error Rate
The number of records in the dataset
stored, in conflict with the required
format (e.g., GML or XML).
Example:
If the dataset is supposed to be
in a specific format (like GML),
but is instead provided in a
shapefile format, this would
violate format consistency.
Or if a road network dataset is
missing an attribute such as
road type that according to the
schema should be present, or if
extra columns are added
outside the specification, then
this is also a violation of format
consistency
Reference: ISO 19157
Compatibility Extent to which the provided information
is provided in the desired format and in
line with common standards (incl. location
referencing). (pdf? Updates TN-ITS?)
whole network
Completeness
(not sure if
this is
relevant. This
is a generic
criteria for all
use cases)
Excess
Records
Percentage of records
in the dataset that are
in excess to the
number of records that
should have been
present in reality
Commission Error Rate
Duplicated
Records
Number of records
that are duplicated
with the features in
the dataset
Commission Number of Error The total number of records in the dataset was
created erroneously with a duplicate geometry.
Missing
Records
Percentage of missing
records (geometry
representation).
Omission Error Rate
Hybrid
(correctness &
completeness)
Granularity Level of detail of the
information provided
Alignment
Score (AS)
Evaluates the extent to which FCD segmentation aligns with network topology.
[page 30]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 30
for each road segment
and intersection.
(Road segments
connecting at an
intersection should
have consistent
attributes, such as road
type, lane count, and
speed limits,
Discrepancy
Index (DI)
Difference
Analysis?
Quantify discrepancies in key attributes.
Timeliness
(Unless there
are major road
works,
intersections
don't really
change, also
for road
segments
intersecting,
timeliness is
not relevant)
Freshness Extent to which
information derived
from FCD is updated in
a frequent basis
Average
Update
Frequency
(AUF)
Measures the average time difference between consecutive FCD time aggregation
intervals.
Latency Time delay or lag
between the update of
an FCD record and the
moment this record is
made available for use
through a data
exchange system or
platform.
Average Time
Delay (ATD)
Measures the average time difference between all FCD time aggregation intervals
and the moment at which the respective information is accessible to FCD users.
[page 31]
6.4 Assessment of the exemplary definition of quality dimensions, criteria and metrics
Within the available time and assignment, it was impossible to work out dimensions,
criteria and metrics for other mentioned road network topological data, mentioned in
this document. The reader will understand that making a complete quality framework
for all topological data is quite a further effort to go.
One can question if the metrics can be applied and if we can come to agreements of
acceptance of the topological data quality based upon these metrics and ground ‘truth’
(e.g., derived from Satellite data (raster), other map data (vector), Floating Car Data…)
As a potential alternative approach to quality assessment in the topology context, we
propose to look at the data that underly the creation of topological maps.
Road network topological maps and their data are the result of processing more ‘raw
map’ data. Road network topological maps data are also considered to be more ‘static
data’. So, it might be obvious to look at the ‘static’ ‘raw data’ sources that lie on t he
basis of the topological process.
The following table identifies such ‘static’ ‘raw data’ from the data type inventory in
the former table 1.
Table 4 – Identification of ‘static’ ‘raw data’ that underly the topological process.
[page 32]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 32
7. Further evaluations needed
7.1 Generated insight
Based on the experience with the exemplary definitions of quality dimensions,
criteria and metrics, based on pre-defined rules in the process of creating topological
maps, we propose to establish a quality framework for ‘static’ ‘raw data’ sources that
underly the topological process. Such sources include node data etc. and are listed in
Table 4.
This means that the definition work for quality dimensions (e.g., correctness,
completeness, …) and related criteria and metrics needs to be rather related to such
‘static’ ‘raw data’.
Looking to the above table of relevant required data that defines the road network
topological representation in digital maps, the insight is that many of those data is
again derived from the available traffic regulations and corresponding road signs. The
identification and changes of those, are subject of the data exchange standard TN-ITS
(becoming in the future DATEX II part 14), as referenced in the RTTI Delegated
Regulation.
Quality aspects regarding traffic regulations and road signage information relate to
questions such as “Are they available?”, “What is the coverage?” etc. However,
quality aspects about traffic regulations and road signage data were not in scope in
this QF for road network topology, but should be covered in future elaborations of
NAPCORE or other activities.
7.2 Future handling the data quality issue in the context of road network topology
The findings from the presented work imply two actions:
• A further study the map versus topology data relationships, maybe focussed
to priority use cases as navigation.
• A focused quality elaboration on the data that build the source for the
topological process, such as data related to traffic regulations and road
signage.
We recommend taking on these works in the quality activity in upcoming phase of
NAPCORE (starting in July 2025).
It is noted that traffic regulations and road signage data are part of the RTTI
framework. A parallel approach to evaluating RTTI related data quality is the current
5-star-rating initiative from TISA7. This initiative aims to agree between service
providers and authorities on data quality and acceptance levels. However, this
process is likely to take some time, and the current scope is limited to priority data
sets: speed limits, roadblocks, road closures.
7 https://tisa.org/wp-content/uploads/Draft-Proposal-Minimum-Quality-RTTI-Requirements-
SL_RW_RC.pdf
[page 33]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 33
We thus recommend to extend the work of TISA towards the relevant data types for
the road network topology. In any case, the quality work in the upcoming NAPCORE
phase should cooperate with the TISA initiative.
8. Conclusions
This QF for road network topology provided some basic concepts for a quality approach in the
roadwork topology context. This includes an analysis on how road databases are usually modelled,
on relevant use cases relying on network topology (in the scope of the RTTI), on relevant data
providers, and on typical topological checks or rules in the map creation process.
However, this QF did not result in a complete finalised framework of defined and agree quality
definitions (dimensions/criteria/metrics) that can be implemented right away.
The original idea of the presented Quality Framework was to create Quality Definitions Criteria and
Metrics from “rules” related to typical topological checks. For example, one rule was ‘Road Segments
must Be Properly Snapped‘. We did define a preliminary set of definitions for this one exemplary
rule, but it turned out that a comprehensive (and agreed) definition work for any kind of rules is too
complex and time consuming.
In this process, it became clear that the road network data topology topic is complex in nature and in
scope. The required data quality levels will depend on the envisioned use cases. But the topology is a
result of a processed map. If the map data is wrong the topology data will be wrong.
The insight generated is that the quality aspect moves to the relevant data sets that define the digital
maps. Thus, we identified two concrete follow-up actions:
• The relationship between the relevant map data and the resulting topology data needs to be
further identified.
• Quality definitions (dimensions/criteria/metrics) have to be provided for the data that the
underly the topological process. (We identified such data as of ‘static’ ‘raw data’ and listed
them in Table 4.)
Further actions on that matter are recommended for the upcoming phase of NAPCORE.
[page 34]
A Quality Framework for road network topology
This project has received funding from the European Commission’s Directorate General for
Transport and Mobility under Grant Agreement no. MOVE/B4/SUB/2020-123/SI2.85223 34
References
GDF, ISO 20524-1:2020 Intelligent transport systems — Geographic Data Files (GDF) GDF5.1Part 1: Application
independent map data shared between multiple sources. https://www.iso.org/standard/68244.html
GDF, ISO 20524-2:2020 Intelligent transport systems — Geographic Data Files (GDF) GDF5.1Part 2: Map data
used in automated driving systems, Cooperative ITS, and multi-modal transport
https://www.iso.org/standard/72494.html
INSPIRE Data Specification on Transport Networks – Technical Guidelines. INSPIRE Infrastructure for Spatial
Information in Europe D2.8.I.7 Data Specification on Transport Networks – https://knowledgebase.inspire.ec.europa.eu/publications/inspire-data-specification-transport-networks-technical-guidelines_en
Open Geospatial Consortium (OGC), Simple Features Specification: a standard that outlines how topology can
be maintained in spatial datasets. URL: https://www.ogc.org/standards/sfa
Other NAPCORE Quality framework milestones
