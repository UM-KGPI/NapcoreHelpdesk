url: https://docs.datex2.eu/v3.7/levels/mastering/common/vehicle/
title: Vehicle package

## Vehicle package
The package “Vehicle” shall comprise a sub-model for defining information about an individual vehicle (see the following figure).
### Semantics of the Vehicle package
The information that is modelled in the “Vehicle” package shall identify details of an individual vehicle and the load which it may be carrying.
#### Vehicle class
An instance of the “Vehicle” class shall allow a supplier to identify the specific details relating to a single individual vehicle and its load.
#### AxleSpacing class
The “AxleSpacing” class may be used to allow a supplier to identify the spacing between adjacent sets of axles on a specific vehicle, indexed from the front of the vehicle.
Attribute “axleSpacingSequenceIdentifier” shall identify which axle spacing is being specified, e.g. a value of ‘1’ indicates that the “axleSpacing” value relates to the distance between the front axle and the next axle from the front of the vehicle.
#### AxleWeight class
The “AxleWeight” class may be used to allow a supplier to identify the actual weight and the maximum permitted weight on a specified axle on a specific vehicle.
Attribute “axlePositionIdentifier” shall identify to which axle the specified weight values relate, e.g. a value of ‘1’ indicates that it is the front axle weight that is being specified.
Go back to the previous page
