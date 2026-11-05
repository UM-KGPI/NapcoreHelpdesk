url: https://docs.datex2.eu/v3.7/levels/mastering/location/pointcoordinates/
title: PointCoordinates (Point location)

## PointCoordinates (Point location)
link to the model
This section describes the "PointCoordinates" referencing system.
### "PointCoordinates" Package
This package supplies classes and attributes to the definition of a point location by coordinates including three-dimension definition and the corresponding confidence parameters.
In this package, a point is defined by geodetic coordinates (in term of geodetic longitude and latitude) through the class *“PointCoordinates”*.
Geodetic coordinates are defined according to the European Terrestrial Reference System of 1989 (ETRS89) which was coincident with the International Terrestrial Reference System (ITRS) in 1989. This is the European implementation of ITRS, but unlike ITRS it is fixed to the stable part of the Eurasian Plate. The coordinates and maps in Europe based on ETRS89 are not subject to change due to the continental drift. ETRS89 is the EU-recommended frame of reference for geodetic data in Europe.
In the case of three-dimension definition the third coordinate is added through the class “HeightCoordinate”.
Three variants of height are proposed:
- by default, it is the ellipsoidal height (measured relatively to the IERS ellipsoid).
- Other possibilities are gravity-related height (defined by a value measured along direction of gravity above the reference geoid I.e. equipotential surface of the Earth's gravity field which globally approximates mean sea level – often inaccurately named “altitude”)
- and relative height defined relatively to the ground level.
In addition, the classes *“PositionConfidenceEllipse”** and “AltitudeConfidence” can be used to defined the accuracy of the geographical position through a confidence ellipse and its height according to the specifications of ETSI/TS 102 894-2.
This accuracy is based on a confidence level of 95 % (see ETSI/TS 102 894-2 V1.2.1 (2014-09), A.119 and A.8).
The class “PositionAccuracy” is defined according to EN 16803-1.
The following table gives indications on the contents of the various common attributes used by the classes related to the GML location.
PointCoordinates_dataDictionary
Go back to the previous page
