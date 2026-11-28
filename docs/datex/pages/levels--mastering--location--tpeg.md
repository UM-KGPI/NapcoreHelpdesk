url: https://docs.datex2.eu/v3.7/levels/mastering/location/tpeg/
title: TPEG-Loc (Point, linear and area location)

## TPEG-Loc (Point, linear and area location)
Transport Protocol Expert Group
This section describes the TPEG-Loc referencing system.
link to the model
### TpegDescriptor Package
link to the package
The package “TpegDescriptor” supplies classes and attributes to the definition of a descriptor in TPEG which delineates the descriptive part of a TPEG location besides geodetic coordinates.
A descriptor is a TPEG-originated word representing any textual description and shall be composed of a descriptor type, a text string and a language code. The latter two elements shall be embedded in a “MultingualString” structure.
### TpegPointLocation Package
link to the package
This package supplies classes and attributes to the definition of a point location using the methods specified in CEN ISO/TS 18234-6 and CEN ISO/TS 24530-2.
A TPEG point represents a single point on the road network defined by a TPEG-Loc structure and shall have a direction of traffic flow.
It shall be realized as:
- a simple point (class “TpegSimplePoint”) I.e. a point on the road network not bounded by any other points on the road network, or
- a framed point (class “TpegFramedPoint”) I.e. represents a point on the road network framed (or bracketed) between two other points on the same road. It can be used when the location is not at a junction and is a point without a predefined name. The two points at either side are used to frame the location with known points;
Points of one type or of the other have the common characteristics of all of TPEG points (class “TpegPoint”). They can be either located at a road junction (class “TpegJunction”) or located outside any road junction (class “TpegNonJunctionPoint”). They also include a geodetic coordinate pair as already defined above.
When a TPEG point is at a junction it shall be defined with one to three ILOC descriptors (class “TpegIlcPointDescriptor”). It may also be described with a junction descriptor (class “TpegJunctionPointDescriptor”) and/or with other point descriptors (class “TpegOtherPointDescriptor”). Regarding ILOC descriptor the different values of this descriptor shall be mutually exclusive.
When a TPEG point is not at a junction it shall be defined with at least one point descriptor (the class “TpegOtherPointDescriptor”). One of these descriptors shall identify the road or street on which the TPEG point is located. The corresponding descriptor type shall have either the value ‘linkName’ or the value ‘localLinkName’.
A TPEG framed point shall be defined by three TPEG points. In addition to the framed point that is not on a junction, it shall define other two points that frame the framed point.
The different descriptors are described above.
### TpegLinearLocation Package
link to the package
This package supplies classes and attributes to the definition of a linear location using methods specified in CEN ISO/TS 18234-6 and CEN ISO/TS 24530-2.
A TPEG linear location represents a linear section on the road network defined by TPEG-Loc structures (class “TpegLinearLocation”). It shall have a direction of traffic flow. This linear section shall be bounded by a “from” point and a “to” point. Both points are defined by a TPEG point location as already defined in class “TpegPointLocation” above.
### TpegAreaLocation Package
link to the package
This package supplies classes and attributes to the definition of an area-typed location locating a traffic object e.g. a situation record in a situation publication.
A TPEG area represents a geographic or geometric area defined by a TPEG-Loc structure which may include height information for additional geospatial discrimination.
It shall be realized as:
- an area defined using a simple geometric shape (class “TpegGeometricArea”) I.e. a circle defined by a given point (centre) (through a coordinate pair) and its radius in metres. It may also be described by one or several area descriptors;
- an area without any geometric depiction defined by its only name (class “TpegNamedOnlyArea”) through one or several area descriptors.
These descriptors are described in "TpegDescriptor Package" section.
The following tables give indications on the contents of the various common attributes used by the classes related to the TPEG location.
TpegDescriptor
TpegPointLocation
TpegLinearLocation
TpegAreaLocation
Go back to the previous page
