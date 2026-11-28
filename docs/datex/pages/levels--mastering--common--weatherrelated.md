url: https://docs.datex2.eu/v3.7/levels/mastering/common/weatherrelated/
title: WeatherRelated package

## WeatherRelated package
The package “WeatherRelated” shall comprise a collection of classes used to specify road weather related measurements.
### Semantics
The aspects of weather or pollution measurements modelled in this package relate to humidity, temperature, visibility, wind, pollution, precipitation and road surface conditions.
#### Humidity class
The "Humidity” class shall allow relative humidity measurements to be specified (see figure below).
Relative humidity measurements shall be expressed as a percentage. Note that each instance of a measurement may be accompanied by information about the measurement via the PercentageValue class which inherits a number of metadata attributes from the DataValue class.
#### Temperature class
The “Temperature” class shall allow a number of different atmospheric temperature measurements to be specified (see figure below).
Individual measurements of air temperature, dew point temperature, maximum temperature and minimum temperature may be specified. Note that each instance of a measurement may be accompanied by information about the measurement via the TemperatureValue class which inherits a number of metadata attributes from the DataValue class.
#### Visibility class
The “Visibility” class shall allow minimum visibility distance measurements to be specified (see figure below).
Minimum visibility distance measurements shall be given in integer metres. Note that each instance of a measurement may be accompanied by information about the measurement via the IntegerMetreDistanceValue class which inherits a number of metadata attributes from the DataValue class.
#### Wind class
The "Wind" class shall allow a number of different measurements relating to wind to be specified (see figure below).
Individual measurements of wind speed, maximum wind speed, wind direction and direction of maximum wind (both bearing and compass) may be specified. Note that each instance of a measurement may be accompanied by information about the measurement via the WindSpeedValue, DirectionBearingValue and DirectionCompassValue classes which inherit a number of metadata attributes from the DataValue class.
#### Pollution class
The “Pollution” class shall allow pollution concentration measurements to be specified (see figure below).
Pollution concentration measurements shall be given in micrograms per cubic metre. Note that each instance of a measurement may be accompanied by information about the measurement via the MicrogramsConcentrationValue class which inherits a number of metadata attributes from the DataValue class.
#### Pressure class
The “Pressure” class shall allow atmospheric pressure measurements to be specified (see figure below).
Pressure measurements shall be given in hectopascal. Note that each instance of a measurement may be accompanied by information about the measurement via the PressureValue class which inherits a number of metadata attributes from the DataValue class.
#### PrecipitationDetail class
The “PrecipitationDetail” class shall allow measurements relating to precipitation to be specified (see figure below).
Information on the precipitation type and its intensity may be provided by using the enumerations "PrecipitationTypeEnum" and "PrecipitationIntensityEnum" (see data dictionary). Individual measurements of intensity and depth of precipitation may be specified. Note that each instance of a measurement may be accompanied by information about the measurement via the PrecipitationIntensityValue and FloatingPointMetreDistanceValue classes which inherit a number of metadata attributes from the DataValue class.
#### RoadSurfaceConditionMeasurements and TemperatureAboveOrBelowRoadSurface class
The “RoadSurfaceConditionMeasurements” class shall allow road surface condition measurements which are related specifically to the weather to be specified (see Figure 10).
Individual measurements of road surface temperature, road surface protection temperature, de-icing application rate, de-icing concentration, depth of snow, ice layer thickness and percentage, water film thickness and friction may be specified.
By using the "TemperatureAboveOrBelowRoadSurface" class, it is possible to specify temperatures for individual measurement heights above or below the road surface.
Note that each instance of a measurement may be accompanied by information about the measurement via the TemperatureValue, ApplicationRateValue, KilogramsConcentrationValue, FloatingPointMetreDistanceValue, FrictionValue and PercentageValue classes which inherit a number of metadata attributes from the DataValue class.
Go back to the previous page
