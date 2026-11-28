url: https://docs.datex2.eu/v3.7/levels/mastering/location/openlr/
title: OpenLR™ (Point, linear and area location)

## OpenLR™ (Point, linear and area location)
link to the model
This section describes the "OpenLR" referencing system.
### "OpenlrPoint" Package
This package supplies classes and attributes to the definition of a point location using the OpenLR™ method as specified in ISO/TS 21219-22.
An OpenLR™ point (class “OpenlrPointLocationReference”) represents a single point that can be either on the road network or defined by a simple pair of geodetic coordinates (class “OpenlrGeoCoordinate”).
Being on a road network it can be defined either as a point of interest (POI) with an access point on a linear path (class “OpenlrPoiWithAccessPoint”) or a point along a linear representing a road element (class “OpenlrPointAlongLine”).
Both classes representing points on a road network inherit of the “OpenlrBasePointLocation” class which defines a linear element, its orientation, the side of road where the located point lies and a positive offset that represents the distance in meters between the node starting the linear path carrying the point and the point itself.
The linear path is expressed by two points realized by respectively the classes “OpenlrLocationReferencePoint” and “OpenlrLastLocationReferencePoint”.
These latter classes inherit from the “OpenlrBaseReferencePoint" class which is linked to geodetic coordinates (“PointCoordinates” class) and to attributes like bearing, form-of-way and functional road class through the class “OpenlrLineAttributes”.
### “OpenlrLinear” Package
This package supplies classes and attributes to the definition of a linear location using the method specified in ISO/TS 21219-22.
An OpenLR™ linear location reference (class “OpenlrLinear”) can represent up to two linear sections of a road, corresponding respectively to the aligned direction (“firstDirection” relationship role) and to the opposite direction (“oppositeDirection” relationship role).
Each linear section is defined (using the “OpenlrLineLocationReference” class) by a sequence of instances of the “OpenlrLocationReferencePoint” class and finishing by one instance of the “OpenlrLastLocationReferencePoint” class.
These classes and their related ones are defined in OpenlrPoint Package.
Each instance of the “OpenlrLineLocationReference” may be accompanied by a positive offset, respectively a negative offset, along the line of the location using the “OpenlrOffsets” class, when the start point, respectively the end point, of the location does not coincide with the node starting, respectively ending, the location reference path.
### “OpenlrArea” Package
The package “OpenlrArea” supplies classes and attributes to the definition of an area-typed location using the OpenLR™ area location.
An OpenLR™ area (class “OpenlrAreaLocationReference”) represents an area that can be defined by several ways:
- by a circle (class “OpenlrCircleLocationReference”), which consists in providing the point coordinates of the centre and the radius;
- by a rectangle (class “OpenlrRectangleLocationReference”) defined by the geodetic coordinates of the two ends of its diagonal from northwest to southeast (the rectangle having two sides that are parallel to lines of latitude);
- by a grid (class “OpenlrGridLocationReference”) which consists in defining this area as a set of connected rectangular boxes (defined through the class “OpenlrRectangle”) repeated according to the defined number of rows and columns;
- by a polygon (class “OpenlrPolygonLocationReference”) which consists in providing the geodetic coordinates of at least three points corresponding to the polygon vertices (this implies to have straight line between two consequent vertices);
- by a closed line (class “OpenlrClosedLineLocationReference”) which is defined by a closed path (I.e. a circuit) in the road network. The boundary always consists of road segment. This definition is similar to the one of the “OpenlrLineLocationReference” class. It allows having curve contours.
The following table gives indications on the contents of the various common attributes used by the classes related to the OpenLR location.
OpenLR_dataDictionary
Go back to the previous page
