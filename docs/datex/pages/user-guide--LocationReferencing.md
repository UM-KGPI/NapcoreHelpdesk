url: https://docs.datex2.eu/v3.7/user-guide/LocationReferencing/
title: Important features about locations in Datex II

## Important features about locations in Datex II
- Information can be located with one location reference containing different locations which must be physically different.
- A location reference can be an itinerary (i.e. an ordered set of locations), a group of non-ordered locations or a single location.
- Each individual location can be defined with several location referencing systems (ALERT-C, linear referencing, TPEG-Loc, …): for interoperability, the Supplier and its Clients MUST use at least one common location referencing system which is a result of an interchange agreement (refer paragraph to Interchange agreement) .
- The location references and each location can be expressed by references defined in the Predefined Locations Publication.
- A location can correspond to a road network element (point or linear) or to an area,
- An itinerary can relate to one or several destinations, each being a point or an area, It is also true for a road network location.
- When the location is on the network, supplementary positional description information can be given (e.g. characteristics at the carriageway and/or at the lane level, …).
Note
More information is provided about the different location referencing systems in the section Use of ALERT-C location referencing system
## Location Reference by types
In the UML model, two different walkthroughs lead to information about location.
In the diagrams, the classes are presented by types:
- Point
- Linear
- Area
In the packages, the classes are gathered by packages:
- AlertC
- Gml
- LinearReferencing
- OpenLR
- PointCoordinates
- SupplementaryPositionalDescription
- TpegLoc
- NamedArea
### Point location
Several location referencing systems can be used. At least one must be present:
- Point by coordinates (ETRS89): latitude, longitude plus optional bearing
- Warning: Coordinates are defined according to the European Terrestrial Reference System 1989 (ETRS89) which was coincident with ITRS in 1989. This is the European implementation of ITRS, but unlike ITRS and WGS84 it is centred on Europe. ETRS89 is the EU-recommended frame of reference for geodata in Europe.
- Point along linear element:
- linear referencing system based on referents, distances to referents all of them being along a linear element (road element). Details (road name, direction, height, …) may also be added.
- TPEG Point Location: a TPEG point location has direction (e.g. northbound, eastbound, clockwise …) and is either specified as:
- a simple point on the road network either at a junction or not, or
- a framed point on the road network between two other points (i.e. framing points) on the road network.
Warning
Each point (simple point, framed point or framing point) is defined by its latitude and longitude (ETRS89) which may be at a junction or between junctions. Each is further elaborated by one or more textual descriptors of prescribed type (i.e. names like junction names, point names, railways station name…).
- ALERT-C Point : country code, table number and version, plus:
- Mandatory code and ALERT-C direction and optional name (Method 2); or
- Same elements plus offset distance (Method 4)
- OpenLR Point
### Linear Referencing
Several linear location referencing systems can be used. At least one must be present:
- Single Road linear element
- Linear within linear element location: besides details common with the point along linear element, it includes:
- A linearly referenced point identifying the "from" point and another linearly referenced point identifying the "to" point, where the "to" point is downstream from the "from" point according to the direction provided by the underlying linear road element
- ALERT-C linear : country code, table number and version, plus:
- Mandatory linear location code and ALERT-C direction and optional name (method linear by code) or
- Mandatory primary code, secondary code and ALERT-C direction and optional names (Method 2), plus offset distances (Method 4)
- TPEG Linear Location
- A TPEG point location identifying the "from" point and another TPEG point location identifying the "to" point, where the "to" point is downstream from the from" point according to the direction of traffic flow.
- A direction (e.g. northbound, eastbound, clockwise …)
- OpenLR Linear
- GmlLineString
Any Linear Location must have an instance of at least one of these classes. If using multiple instances, producers must take care to ensure they represent the same location.
Moreover, supplementary descriptions can be added to the linear location: length, position on the carriageway, position descriptor (at rest area, in tunnel…), etc.
### Area location
Several location referencing systems can be used. At least one must be present:
- ALERT-C area: country code, table number and version, plus:
- Mandatory area location code and optional name
- TPEG Area Location, a TPEG area has a type of either "largeArea" or "other" and optional height information and height type (e.g. above sea level…). It is further specified either as:
- A "named only" area (i.e. by a name and a descriptor type, e.g. county name, town name…) or
- A geometric area comprising a centre point (defined by ETRS89 latitude and longitude), a radius and an optional "named area".
- namedArea
- GmlMultiPoygon
- OpenLR Area
At least one of these aggregated classes must be present. If using multiple instances, producers must take care to ensure they represent the same location.
## Location Reference by packages
In the UML model, two different walkthroughs lead to information about location.
In the diagrams, the classes are presented by types:
- Point
- Linear
- Area
In the packages, the classes are gathered by packages:
- AlertC
- Gml
- LinearReferencing
- OpenLR
- PointCoordinates
- SupplementaryPositionalDescription
- TpegLoc
- NamedArea
### ALERT-C location referencing system
This section describes the ALERT-C referencing system and gives details of the contents of ALERT-C tables. Since this version of the DATEX II specification does not include the exchange of ALERT-C Location tables this is provided as general support information.
Note
Reminder: An ALERT-C localisation is a tabular address defining a locating element belonging to this table.
Only the reference is transmitted between the Supplier and the Client. It is up to the client to look it up in the table for the descriptive elements corresponding to the referenced location using the ALERT-C code. To have a unique ALERT-C coding at the European level, the reference must comprise three elements (triplet):
- Country Code,
- Table number,
- Location number
Two distinct locations at the European level cannot have the same triplet.
Warning
Caution: currently certain codes for country table references were not allotted; they are thus invalid.
It is the European standard EN ISO 14819-3 that defines the rules of constitution of the ALERT-C location tables.
The following table gives indications on the contents of the various common attributes used by the classes related to the ALERT-C location.
Code | Definition | Possible values
F (France)1 (Germany)
1 (Germany)
E (Spain)
5 (Italy) etc…
etc…
alertCLocationCountryCode | Country code defined by RDS (IEC 62106). It uses only 15 values (1 hexadecimal digit: 1 to 9 and A to F). It doesn’t identify a specific country because values are shared by several countries.
17 to 32 (France)
17 to 24 (Spain)
1 to 16 (Italy)
5 (Italy) etc…
etc…
alertCLocationTableNumber | Number allowed for a country CountryCode + TableNumber fully identifies the table
alertCLocationTableVersion | Version number of the ALERT-C location table in a country.
both
negative
positive
unknown
alertCDirectionCoded | It is the concerned direction. Positive direction corresponds to the direction used when following positive linkage in the table
alertCDirectionNamed | String for the direction name
true (ALERT-C positive direction)
false (ALERT-C negative direction)
alertCDirectionSense | Indicates for circular routes (i.e. valid only for ring roads) the sense in which navigation should be made from the primary location to the secondary location, to avoid ambiguity. The value TRUE indicates the positive RDS direction, i.e. direction of coding of road.
alertCLocationName | Location name (redundant because already in the table)
offsetDistance | The non-negative offset distance from the ALERT-C referenced point to the actual point.
specificLocation | Unique code within the ALERT-C location table which identifies the specific point, linear or area location. | Number between 1 and 63487
Examples can be found here.
#### Alert-C Point location
A point will be used to locate certain phenomena where dimension length is negligible such as for example accidents, incidents (broken down vehicles), obstacles, …. DATEX II proposes two methods of localization for the points, called method 2 and method 4 (the previous DATEX method 1 and method 3 have been abandoned):
- In method 2, the point is defined by the tabular address of the ALERT-C point;
- In method 4, the point is defined by the tabular address of the ALERT-C point, supplemented by the distance between this ALERT-C point and the point to be located.
In an ALERT-C location table an ALERT-C point includes a type and a point name as well as the name of intersecting roads at the point. Moreover, a reference towards the road (or the segment of road which carries it) is systematically added to the point and makes it possible to attach the name/number of road to this point. Consequently, all points are attached to a road (and only one).
#### Alert-C Linear location
Linear will be used to locate certain phenomena or operator actions where dimension length is relevant, such as for abnormal traffic flow (queues, …), the bad condition of roads (e.g. road surface), …
DATEX II proposes three methods of localization for linear:
- In method 2, the linear one is defined by two points (primary location and secondary location), each point being defined only by the tabular address of the corresponding ALERT-C point;
- In method 4, the linear one is defined by two points (primary location and secondary location), each point being defined by the tabular address of the corresponding ALERT-C point, supplemented by the distance between this ALERT-C point and the end of the linear location.
- In method "linear by code", the linear is defined only by the tabular address of the corresponding linear ALERT-C location (road, street or segment).
The primary location is the nearest defined downstream point (for methods 2 or 4). In an ALERT-C location table an ALERT-C linear location includes a type, the names of the origin and end of linear section as well as the associated road number/name.
#### Alert-C Area location
In an ALERT-C location table an area location includes a name and its type can be found starting from the contents of the location table.
It can be used to locate certain surface phenomena like weather phenomena. It can also be used to provide an indication of the destination (when it corresponds to a city for example).
### Gml
The package "Gml" includes four class with their attributes for the definition of a linear location which specializes a location of a traffic object. This method complies with EN ISO 19136.
#### GmlLinear
The class "GmlLineString" instantiates a GML line string and has three attributes:
- "posList" which contains the ordered list of the two- or three-dimensional point coordinates,
- "srsName" which specifies the Coordinate Reference System (CRS) used to interpret the coordinates
- "srsDimension" which provides the number of coordinates for each point belonging to the LineString. This value is either 2 or 3. If it is not provided, the default value is "2".
Generally, the sequence in the coordinates is "latitude" then "longitude".
The order of the points forming the line string provides the direction of the geographic feature.
#### GMLArea
The class "GmlMultiPolygon" instantiates a case of GML_MultiSurface where all the surfaces belonging to the set are polygons (class "GmlPolygon"). When this area is defined by several polygons (and not only one), each of them may be associated with a name (attribute "gmlAreaName") to distinguish them.
Each polygon is defined by an exterior linear ring and zero to several interior linear rings that define interior patches. A linear ring (class "GmlLinearRing" equivalent to GM_LinearRing) is a specific, not self-intersecting closed curve derived from a line string, i.e. where the last tuple is identical to the first one. Such linear ring is composed of at least four positions. This linear ring is not self-intersecting to avoid creating fragmented (non-compact) areas since several exteriors can be attached to an instance of the "GmlMultiPolygon" class.
### Linear referencing system of locations
This section describes the linear referencing system used by DATEX II. It accommodates all the actual linear referencing systems adopted by road operators in Europe. It can be used for systems based on a distance measured from the linear element origin: kilometre point or its US equivalent mile point or true mileage as well as for the UK system named "chainage", hectometre-points, or link offset. It also accommodates systems where there exist intermediate points from which the distance is measured: systems based on kilometre-post, milepost, reference post as well as cross-streets or control sections. It is fully compliant with a draft CEN ISO standard on the same topic (EN ISO 19148) being adopted, with the two following restrictions:
- Distances are only expressed in metres according to the DATEX II principle on units, unlike the draft standard where it is permissible to express them with different units.
- The lateral/vertical offset features are not implemented
Reminder: This system is based on predefined elements that need to exchanged and agreed by the Supplier and the Client before being used in a DATEX II exchange. Only the reference is transmitted between the Supplier and the Client. It is up to the client to look up the descriptive elements corresponding to the referenced location using the provided elements.
Such a linear referencing system includes three elements:
- general information on the location itself:
- administrative area including the location,
- geographic direction: e.g.: northbound, westbound, clockwise, …
- relative traffic flow direction of the considered location regarding the underlying
- referenced linear element direction: aligned, opposite, both, unknown
- height grade of linear section: above grade, at-grade, below grade
- Expression of distance of the referenced point: this expression of distance can be absolute (expressed from the origin of the road element), relative to an upstream intermediate point named "from referent", or interpolative (expressed by a percentage along the linear element and calculated from the linear element origin).
In case of relative method, the "from referent" may also be associated with a "toward referent" (downstream), both bracketing the considered point.
In case the considered point is bracketed by two referents, the direction defined as going from the "from referent" to the "toward referent" overrides the general direction of the linear element (see below). The location direction is thus compared to this direction.
A referent is typified: boundary, intersection, reference marker, landmark, road node.
Finally, each referent may be associated with ETRS89 geographic coordinates (latitude, longitude).
- The linear element underlying the location. It includes several attributes:
- road number,
- road name, one of the two attributes shall be provided,
- linear element nature (optional): road, road section, slip-road, other
- reference model which identifies the road network reference model which segments the road network according to specific business rules. It may be e.g. a graph describing the considered road network.
- reference model version: version of the referenced road network model
This underlying linear element is defined either with an identifier string (e.g. looking up in a map database) or as an ordered sequence of points with one at each extremity. These points are defined as referent. In this latter case, the sequence order provides the reference linear element direction.
#### Point along a linear element
A point will be used to locate certain phenomena where dimension length is negligible such as for example accidents, incidents (broken down vehicles), obstacles, …. In case of a point referencing, the general information is provided by the class "PointAlongLinearElement".
#### Linear within a linear element
Linear will be used to locate certain phenomena or operator actions where dimension length is relevant, such as for abnormal traffic flow (queues, …), the bad condition of roads (e.g. road surface), …
This linear is defined by its two extremities: "from" point and "to" point. Unlike some other referencing based on points like ALERT-C, the order between "from" point and "to" point is only defined downstream by considering the underlying linear element direction. If the impacted traffic direction is aligned, the attribute "directionRelativeOnLinearSection" is used. The general information is provided by the class "LinearWithinLinearElement".
#### No area referencing
This referencing system cannot be used for referencing areas.
### OpenLR
OpenLR whitepaper version 1.5
OpenLR point location references are defined in more detail in the .
#### OpenLR Line Location Reference
An OpenLR line reference is defined as a sequence of OpenLR base Location Reference points forming a route/itinerary on a road network.
Be aware that OpenLR lines can comprise more than one linear in terms of the DATEX II definitions of a linear. It would harm the basic concepts of on-the-fly location referencing as supported by OpenLR when an implementation is made by splitting the openLR lines up according to the DATEX II definition of a linear.
Therefore, it is recommended to include only one OpenLR linear from the beginning to the end of a trajectory.
OpenLR Area Location reference which
OpenLR Area Location reference is a set of ordered X,Y coordinates (ETRS89) together forming a geometric area, which has to be one of the following types:
- circle location reference: defined by a centre point in coordinates, with a radius of the circle
- rectangle location reference: defined by the coordinates of the lower left (south-west) and upper right (north east) corners of the rectangle
- grid location reference: defined by a rectangles and the number of columns and rows that form the grid within this rectangle
- polygon location reference: defined by the coordinates of at least 3 corners of the polygon.
- closed line location reference: an area framed by road segments. This area is defined by openLR lines
### PointCoordinates
### SupplementaryPositionalDescription
### TpegLoc
### NamedArea
The above content is missing, but will be added as soon as possible.
## PredefinedLocationsPublication
### Objectives and utilisation mechanisms
This publication is used to predefine (sets of) locations which can then be referred to in any of the other publications by means of a single versioned reference attribute. This allows great simplification of those publications where repeating static or quasi-static locations are used.
A set of locations defined as a container may contain one location or can be characterised as an Itinerary (ordered set of locations) or as a group of non-ordered locations. Predefined itineraries as well as a group of non-ordered locations contain several predefined locations. Each predefined location may be of any type, i.e. point, linear or area. Obviously an itinerary cannot include area-typed locations. Each set of predefined locations and each individual predefined location have its own unique versioned identifier and can be referenced in other publications.
The main utilisation is when publications are sent periodically and always concern the same locations, which are mostly itineraries or elementary linear locations (for instance, elaborated data and traffic views publications).
The utilisation mechanism is as follows:
- Step 1: the DATEX II client gets a predefined location publication with the locations identifiers and definitions,
- Step 2: when the DATEX II Supplier delivers publications to this client, it only uses the predefined location identifiers and the client is able to look up the identifier and obtain the real location details.
The advantage of this mechanism is to reduce the publication size.
When a predefined location set is modified, the DATEX II Supplier has to inform the concerned DATEX II Clients.
### Content
With this publication, attributes can be given in the InformationHeader which provide clients with information management details (area of interest, confidentiality, information status, urgency) relating to this publication.
The predefined location container (abstract) shall be derived into a predefined itinerary, a predefined group of non-ordered locations or simply a predefined location. All three have a unique versioned identifier and may have a name.
Itinerary and group of non-ordered locations are made up of predefined locations; each location has its own unique versioned identifier and may have its own name.
The definition of each predefined location uses the same location definition as the other publications. When predefining these locations, usage of other references is not allowed when it infers circular references.
Go back to the previous page
