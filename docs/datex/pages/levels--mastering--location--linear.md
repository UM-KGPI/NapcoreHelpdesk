url: https://docs.datex2.eu/v3.7/levels/mastering/location/linear/
title: Linear referencing (Point and linear location)

## Linear referencing (Point and linear location)
link to the model
This section describes the "Linear referencing" system.
### PointAlongLinearElement
link to the Package
This package supplies classes and attributes to the definition of a point location using different linear referencing methods as specified in EN ISO 19148.
A point defined by a linear reference represent a single point on a linear element, part of the road network. In addition to the linear location definition itself (class “PointAlongLinearElement”), which contains complementary elements like geographic direction, if the point is at-grade or below/above ground level, it shall be realized with two elements:
- The underlying linear element (class “LinearElement”),
- The distance expression between a given point on this linear element and the point itself (abstract class “DistanceAlongLinearElement”).
The distance expression shall be one of the following:
- An absolute distance expression I.e. a curvilinear measurement (in metres) starting from the origin point of the underlying linear element (class “DistanceFromLinearElementStart”);
- A percentage as distance expression I.e. the ratio between the absolute distance of the considered point from the starting point of the underlying linear element and the total length of this linear element (class “PercentageDistanceAlongLinearElement”).
- A relative distance expression I.e. a curvilinear measurement (in metres) starting from an identified point of the considered linear element considered as reference point (class “DistanceFromLinearElementReferent”). This reference point is named “Referent” (class “Referent”);
In case a referent is considered, it can be a distance marker (also named kilopost, kilometre-post or milepost), an area border (e.g. a county border), an intersection, a road node or a landmark. It is defined by a unique identifier. Two referents may be used to frame the considered point (notions of “from” referent and of “towards” referent), which explicitly defines the considered driving direction as going from the “from” referent to the “towards” referent and overrides the implicit direction defined by the underlying linear element direction. A referent may be given geodetic coordinates (see package “PointCoordinates”).
The linear element that underlies the point location is defined by several means:
- A reference (class “LinearElementByCode”), which implies it has previously been defined and exchanged through the ad hoc publication (see Clause 8);
- An ordered sequence of referents including the starting point and the end point of this linear element (class “LinearElementByPoints”). In case the linear element is defined by referents, the sequence order provides the linear element direction.
- A linear geographic feature delineated by a line string (class “LinearElementByLineString” – see package “Gml”).
The linear element shall be given either a road number or a road name depending on what exists. It may be accompanied by other information depending on the road operator and may be typified I.e. defining whether it is a road, a road section or a slip road. In particular, the attribute “linearElementReferenceModel” shall be filled in in case several instances of the class “PointAlongLinearElement” are created.
### LinearWithinLinearElement
link to the Package
This package supplies classes and attributes to the definition of a linear location using different linear referencing methods (LRM) as specified in EN ISO 19148.
A linear location defined by a linear reference represents a linear section on a linear element, part of the road network.
It shall be defined by two points belonging to the same road/street. In addition to the linear location definition itself (class “LinearWithinLinearElement”), which contains complementary elements like geographic direction, information whether the point is at-grade or below/above ground level, it shall be realized with two elements: - the underlying linear element (class “LinearElement”), - two distance expressions between a given point on this linear element and respectively the starting point named “from point” and the ending point named “to point”, framing the linear section (abstract class “DistanceAlongLinearElement”).
These elements are defined according to the rules in "pointAlongLinearElements package" rules.
The following table gives indications on the contents of the various common attributes used by the classes related to the "Linear referencing" location.
LinearReferencing_dataDictionary
Go back to the previous page
