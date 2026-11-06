url: https://docs.datex2.eu/v3.7/levels/mastering/common/datavalue/
title: DataValue package

## DataValue package
This package describes data values of something that can be measured or calculated - see the following figure.
Click image to zoom
### Semantics of the DataValue package
This package contains types for data values (see following subclauses) and adds additional quality and error information to these types.
#### DataValue class
The “DataValue” class is an abstract class i.e. shall be specialised by other classes such as those given in this package. It provides the following quality and error information for each specialised data value:
- Information on data error and reason for it
- Accuracy and computation method
- Number of input values used and number of incomplete inputs
- Smoothing factor and standard deviation
- Information on supplier calculated data quality (in percent)
#### ApplicationRateValue class
A measured or calculated value of the application rate of a substance.
#### DirectionBearingValue class
A measured or calculated value of direction as a bearing.
#### DirectionCompassValue class
A measured or calculated value of direction as a point of the compass.
#### FloatingPointMetreDistanceValue class
A measured or calculated value of distance in metres in a floating point format.
#### FrictionValue class
A measured or calculated value of road surface friction.
#### IntegerMetreDistanceValue class
A measured or calculated value of distance in whole metres.
#### KilogramsConcentrationValue class
A measured or calculated value of concentration of a substance in kilograms per unit volume.
#### MicrogramsConcentrationValue class
A measured or calculated value of concentration of a substance in micrograms per unit volume.
#### PercentageValue class
A measured or calculated value expressed as a percentage.
#### PrecipitationIntensityValue class
A measured or calculated value of the accumulation rate of precipitation.
#### PressureValue class
A measured or calculated value of atmospheric pressure.
#### SpeedValue class
A measured or calculated value of speed.
#### TemperatureValue class
A measured or calculated value of temperature.
#### VehicleFlowValue class
A measured or calculated value of the flow rate of vehicles.
#### WindSpeedValue class
A measured or calculated value of wind speed.
Go back to the previous page
