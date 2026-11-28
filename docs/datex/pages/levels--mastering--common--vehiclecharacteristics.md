url: https://docs.datex2.eu/v3.7/levels/mastering/common/vehiclecharacteristics/
title: VehicleCharacteristics package

## VehicleCharacteristics package
The package “VehicleCharacteristics” shall comprise a sub-model for defining the characteristics of vehicles (see the following figure).
### Semantics of the VehicleCharacteristics package
The information that is modelled in the “VehicleCharacteristics” package shall identify a set of vehicle characteristics, some of whose values can be specified using comparative operators (e.g. greater than ‘x’ but less than ‘y’).
#### VehicleCharacteristics class
An instance of the “VehicleCharacteristics” class shall allow a supplier to identify a base set of vehicle characteristics.
#### Emissions class
The "Emissions" class may be used to specify a vehicle emission level either by Euro-norm, by selfdefined emission categories or by a low emission level flag.
#### GrossWeightCharacteristics class
The “GrossWeightCharacteristics” class may be used to allow a supplier to identify the actual gross weight of a vehicle. By providing two instances of this class a supplier can specify the gross weight as being between a lower and upper limit.
#### HeightCharacteristic class
The “HeightCharacteristic” class may be used to allow a supplier to identify the actual height of a vehicle. By providing two instances of this class a supplier can specify the height as being between a lower and upper limit.
#### LengthCharacteristic class
The “LengthCharacteristic” class may be used to allow a supplier to identify the actual length of a vehicle. By providing two instances of this class a supplier can specify the length as being between a lower and upper limit.
#### WidthCharacteristic class
The “WidthCharacteristic” class may be used to allow a supplier to identify the actual width of a vehicle. By providing two instances of this class a supplier can specify the width as being between a lower and upper limit.
#### HeaviestAxleWeightCharacteristic class
The “HeaviestAxleWeightCharacteristic” class may be used to allow a supplier to identify the actual heaviest axle weight of a vehicle. By providing two instances of this class a supplier can specify the heaviest axle weight as being between a lower and upper limit.
#### NumberOfAxlesCharacteristic class
The “NumberOfAxlesCharacteristic” class may be used to allow a supplier to identify the actual number of axles on a vehicle. By providing two instances of this class a supplier can specify the number of axles as being between a lower and upper limit.
Go back to the previous page
