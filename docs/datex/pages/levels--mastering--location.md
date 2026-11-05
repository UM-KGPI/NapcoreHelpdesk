url: https://docs.datex2.eu/v3.7/levels/mastering/location/
title: LocationReferencing

## LocationReferencing
### The basics
The "LocationReferencing" package is composed of 4 packages :
- "LocationReference",
- "PredefinedLocationsPublication",
- "DataTypes",
- "Enumerations".
#### Location Reference
The location reference is a collection of information related to specifying locations within a road network; Such a location reference is a set of one or several locations and is depicted by the abstract class “LocationReference” that is the main entry point of the corresponding package to carry the corresponding locations.
This location reference can be either used as a set of locations that can be seen as :
- a single location (depicted by the class “Location”), which is the atomic locating unit.
- or an itinerary (or route) (class “Itinerary”) → In this case, the different sections shall be defined following a specific order or linkage.
- or independently one from another and without any order (class “LocationGroup”)
Note
A group of non-ordered locations as well as an itinerary have at least two locations.
A location can be represents as :
a Road Network Element (class “NetworkLocation”), which can be either :
1. a Point location (class “PointLocation”) > It represents a single geospatial point on a road. It shall be referenced using at least one of the following methods:
- the ALERT-C location referencing methods (see package “AlertCPoint”); Click here
- the TPEG-Loc location referencing method (see package “TpegPointLocation”); Click here
- the linear referencing method (see package “PointAlongLinearElement"); Click here
- the OpenLR™ location referencing method (see package “OpenlrPoint”); Click here
- A geographic point defined with geodetic coordinates. (see package “PointCoordinates”). Click here
2. or a Linear Location (class LinearLocation”) > it is a part of the road network defined between two points on the same road. It may include an indication of direction. It shall be referenced using at least one of the following methods:
the ALERT-C location referencing methods (see package "AlertCLinear"); Click here
the GML-based linear definition method (see package “Gml”); Click here
the TPEG-Loc location referencing method (see package “TpegLinearLocation”); Click here
the linear location referencing method (see package “LinearWithinLinearElement”); Click here
the OpenLR™ location referencing method (see package “OpenlrLinear”). Click here
When a linear location is defined using different methods it is assumed to represent the same geographic location. As well, a linear location defined by the linear referencing method or an ALERT-C location method may be associated to different instances, each one associated to a reference model but representing the same geographic feature. Some location referencing methods like OpenLR™ or GML allow defining linear locations that belong to several roads whereas some others not (like ALERT-C, TPEG or linear referencing). These latter linear locations are composed to the “SingleRoadLinearLocation” class, which is inherited from the “LinearLocation” class.
Supplementary information may be added to a road network element (package “SupplementaryPositionalDescription”).
or an Area Location (class “AreaLocation”). > It can be either a geographic or a geometric two-dimensioned feature. It may be qualified by height information to provide additional geospatial discrimination (e.g. for snow in an area but only above a certain height). It shall be referenced using one of the following methods without being exclusive:
- the Alert-C location referencing method (see package “AlertCArea”); Click here
- the TPEG-Loc location referencing method (see package “TpegAreaLocation”); Click here
- the OpenLR™ location referencing method (see package “OpenlrArea”); Click here
- as a named area (see package “NamedArea”); Click here
- as an area defined as a multipolygon (see package “Gml”). Click here
In case of an itinerary destination(s) may be added to it through occurrence(s) of the class “Destination”. A destination can be delineated either as a point on the road network (class “PointDestination” defined from the class “PointLocation”) or as an area (class “AreaDestination” defined from the class “AreaLocation”).
To help the location to be displayed on a map, geodetic coordinates (in term of geodetic longitude and geodetic latitude) may be added as “coordinatesForDisplay” (package “PointCoordinates”).
External references may be added to locations if there is a need to add a reference to an external/other referencing system (class “ExternalReferencing”). The given reference code provided shall be accompanied with the name of the external referencing system in use. For example, this feature may be used to extend the present model accordingly to EN 16157-1.
For more details,
- "LocationReference" package class model : Click Here
- "PointLocation" package class model : Click Here
- "LinearLocation" package class model : Click Here
- "AreaLocation" package class model : Click Here
And find the data dictionary for the various common attributes and enumerations used in the LocationReference Package in the files below:
Download here: LocationReference Data Dictionary Attributes
Download here: LocationReference Data Dictionary Enumerations
#### Predefined locations publication
A Predefined locations publication deals with collections of data providing definitions of particular defined groups of network sections.
Any location reference can be predefined (i.e. previously defined, identified and exchanged) and then be used through its reference.
This publication is used to predefine (sets of) locations which can then be referred to in any of the other publications by means of a single versioned reference attribute. This allows great simplification of those publications where repeating static or quasi-static locations are used
A set of locations defined may contain one location or can be characterised as an Itinerary (ordered set of locations) or as a non-ordered group of locations. Each predefined location may be of any type, i.e. point, linear or area. Each set of predefined locations and each individual predefined location have its own unique versioned identifier and can be referenced in other publications. The main utilisation is when publications are sent periodically and always concern the same locations, which are mostly itineraries or elementary linear locations (for instance, elaborated data and traffic views publications).
The utilisation mechanism is as follows:
- Step 1: the DATEX II client gets a predefined location publication with the locations identifiers and definitions,
- Step 2: when the DATEX II Supplier delivers publications to this client, it only uses the predefined location identifiers and the client is able to look up the identifier and obtain the real location details.
The advantage of this mechanism is to reduce the publication size. When a predefined location set is modified, the DATEX II Supplier has to inform the concerned DATEX II Clients.
With this publication, attributes can be given in the "InformationHeader" which provide clients with information management details (area of interest, confidentiality, information status, urgency) relating to this publication. The predefined location container (abstract) shall be derived into :
- a predefined location, (and class “LocationByReference”)
- a predefined itinerary, (class “ItineraryByReference”),
- a predefined group of non-ordered locations (class “LocationGroupByReference”).
All three have a unique versioned identifier and may have a name. Itinerary and group of non-ordered locations are made up of predefined locations; each location has its own unique versioned identifier and may have its own name. The definition of each predefined location uses the same location definition as the other publications (refer paragraph: “Location”). When predefining these locations, usage of other references is not allowed when it infers circular references.
For more details, "PredefinedLocationPublication" package class model: Click Here
#### DataTypes
This package is a collection of data types that are specific to location referencing.
For more details, "DataTypes" package class model : Click Here
#### Enumerations
This package is a collection of enumerations that are used in the LocationReferencing package of the DATEX II model.
For more details, "Enumerations" package class model : Click Here
### The Location Reference Methods
#### Alert-C
→ Allows Point, linear and area location. See more...
#### TPEG-Loc
→ Allows Point, linear and area location. See more...
#### Linear referencing
→ Allows Point and linear location. See more...
#### OpenLR™
→ Allows Point, linear and area location. See more...
#### PointCoordinates
→ Allows Point location. See more...
#### GML
→ Allows linear and area location. See more...
#### NamedArea
→ Allows area location. See more...
#### SupplementaryPositionalDescription
→ Allows supplementary positional description (lane, carriageway, etc.). See more...
Go back to the previous page
