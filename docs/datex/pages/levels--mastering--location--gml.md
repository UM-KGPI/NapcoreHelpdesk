url: https://docs.datex2.eu/v3.7/levels/mastering/location/gml/
title: GML (Linear and area location)

## GML (Linear and area location)
link to the model
This section describes the "GML" referencing system.
### GML Package
This package includes 4 classes with their attributes for the definition of a linear location which specializes a location of a traffic object. This method complies with EN ISO 19136.
#### “GmlLineString” class
The class “GmlLineString” instantiates a GML line string and has 3 attributes:
- the “posList” attribute which contains the ordered list of the two-or three-dimensional point coordinates according to EN ISO 19136 (corresponding GML attribute: gml:posList);
- the “srsName” attribute which specifies the Coordinate Reference System (CRS) used to interpret the corresponding coordinates in this GmlLineString. This attribute is defined according to the same standard. Unlike GML where it is mandatory, when this attribute is not filled in the corresponding CRS is “ETRS89-LatLonh”;
- the “srsDimension” which provides the number of coordinates for each point belonging to the LineString. This value is either 2 or 3. If it is not provided, the default value is “2”.
The order of coordinates is defined according to the CRS chosen. Generally, the sequence is “latitude” then “longitude”.
The order of the points forming the line string provides the direction of the geographic feature.
Example
In case the postList attribute contains a set of six coordinate values, it will represent a line defined by two points when the dimension is “3”. In the other cases, the line will be defined by three points in the same plan.
#### “GmlPolygon” and “GmlMultiPolygon” classes
The class *“GmlMultiPolygon”** instantiates a case of GML_MultiSurface where all the surfaces belonging to the set are polygons (class “GmlPolygon”). When this area is defined by several polygons (and not only one), each of them may be associated with a name (attribute “gmlAreaName”) to distinguish them. Each polygon is defined by an exterior linear ring and zero to several interior linear rings that define interior patches.
#### “GmlLinearRing” class
The class “GmlLinearRing” (equivalent to GM_LinearRing) is a specific linear ring, not self-intersecting closed curve derived from a line string, I.e. where the last tuple is identical to the first one. Such linear ring is composed of at least four positions. This linear ring is not self-intersecting to avoid creating fragmented (non-compact) areas since several exteriors can be attached to an instance of the “GmlMultiPolygon” class.
The following table gives indications on the contents of the various common attributes used by the classes related to the GML location.
GML_dataDictionary
Go back to the previous page
