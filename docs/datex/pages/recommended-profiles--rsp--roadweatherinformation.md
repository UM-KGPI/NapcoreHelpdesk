url: https://docs.datex2.eu/v3.7/recommended-profiles/rsp/roadweatherinformation/
title: DATEX&nbsp;II packages addressed by the Road Weather Information RSP

## DATEX II packages addressed by the Road Weather Information RSP
This RSP tailors the following DATEX II model packages:
- Common – commonly used DATEX II data elements used by the tailored packages below (CEN/EN 16157-7:2018)
- LocationReferencing – the location references, tailored for road weather information (CEN/EN 161578-2: 2019)
- Situation – the DATEX II general traffic event packages tailored for road weather information (CEN/EN 16157-3:2018)
- RoadTrafficData – the DATEX II package for sensor data publications (currently balloted to be published as CEN/EN 16157-5:2020)
The Situation package is used for publishing event-type information for weather related road conditions as a SituationPublication. Instances of WeatherRelatedRoadConditions may contain RoadSurfaceConditionMeasurements, see Figure 1.
Figure 1 Weather related road conditions
The RoadTrafficData package is used to provide sensor measurements in MeasuredDataPublication either as one of the WeatherData specialisations
- Humidity
- PollutionInformation
- PrecipitationInformation
- PressureInformation
- TemperaturInformation
- VisibilityInformation
- WindInformation
or as RoadSurfaceConditionInformation, which also contains RoadSurfaceConditionMeasurements.
The RoadSurfaceConditionMeasurements model allows for a variety of measured values (Figure 2).
Figure 2 Road surface conditions measurements
Organisations that want to publish this data will have to decide which type of publication they want to use, a pure publication of measurements or an event-driven publication, where they can include supporting measurement values.
Organisations that want to publish measurements will have to provide a second publication describing the measurement equipment (including the location) called MeasurementSiteTablePublication.
An RSP is provided for all three publications and described in the corresponding section.
### Situation Package
To describe a traffic situation with road weather related content, a profile of the DATEX II Situation package has been created with the following features:
#### RRPs
The profile is based on and complies with the following Recommended Reference Profiles (RRPs):
Regarding Delegated Regulation (EU) 886/2013:
- Category a) temporary slippery road
- Category e) reduced visibility
- Category h) exceptional weather conditions
Regarding Delegated Regulation (EU) 2015/962
- Category p) weather conditions affecting road surface and visibility
#### LocationReference profile
The profile includes all options for single Location instances as well as LocationGroup instances.
It does not contain Itinerary.
The profile has all location referencing systems enabled for all types of location, but the geography (coordinate) based location referencing systems have been made mandatory in order to support harmonisation of feeds. This comprises
- GmlMultiPolygon for area locations
- GmlLineString for linear locations
- PointByCoordinates for point locations
#### Validity profile
The time validity profile includes the overallPeriod, validPeriod and exceptionPeriod concepts, as governed by the respective RRPs. It does not contain the following concepts, which are typically used for time schedules:
- recurringTimeperiodOfDay
- recurringDayWeekMonthPeriod
- recurringSpecialDay
#### PayloadPublication and SituationPublication profile
The general ‘wrapper’ classes for conveying road weather related event information are the following classes:
PayloadPublication: The generic base class for all DATEX II publications
: The optional attributes of the class PayloadPublication have all been kept in the RSP, since they are very generic by nature may be useful for Road Weather Information as well
SituationPublication: This is a container class and has no extra attributes
#### Situation profile
Traffic Situations are in DATEX II modelled as a container class (Situation) that contains SituationRecords, the basic elements to describe an event of a certain nature like weather related road conditions, poor environment conditions, etc. The following profile applies:
Situation: The optional attributes and associated components of the class Situation have all been kept in the RSP, since they are very generic by nature may be useful for Road Weather Information as well; the one exception de-selected is situationSummary, since this additional SituationRecord is typically used for complex scenarios like long-term roadworks and does not seem applicable in this RSP
From the generic data concepts supported by any kind of SituationRecord, the following have been deselected since they were not seen as useful in the context of road weather information services:
- cause
- informationManagerOverride
- confidentialityOverride
All other optional attributes and associated components of SituationRecord are very generic by nature and therefore included in the RSP, since they may be useful for Road Weather Information
The profile selects four concrete types of SituationRecord specialisations relevant for Road Weather Information, which are:
- WeatherRelatedRoadConditions
- PoorEnvironmentConditions
- NonWeatherRelatedRoadConditions
- EnvironmentalObstruction
The first three are specialisations of the Conditions class for which the optional drivingConditionType attribute has been included in the profile.
The EnvironmentalObstruction class is a specialisation of the Obstruction class for which the optional numberOfObstructions attribute has been included in the profile. The optional associated mobilityOfObstruction component has not been included since it does not seem to apply to Road Weather Information.
#### WeatherRelatedRoadConditions profile
The WeatherRelatedRoadConditions class and the complete component for RoadSurefaceConditionsMeasurements are included in the profile. The enumeration types of the mandatory weatherRelatedRoadConditionType attribute is profiled in the sense that the following kerbside related literals have been de-selected for the profile:
- freezingPavements
- normalWinterConditionsForPedestrians
- snowOnPavement
Note
These literals are part of some of the selected RRPs. Nevertheless, they are in principle not seen as relevant for a Road Weather Information Service and have been de-selected in this RSP. Publishers that would nevertheless want to publish this information as well should include them in their publication profile as described in section Application of the RSPs.
#### PoorEnvironmentConditions profile
The PoorEnvironmentConditions class and all associated components to describe weather related phenomena have been included in the profile, see Figure 3. This includes (from top-right to lower-left):
- Pressure
- Humidity
- Wind
- Temperature
- Pollution
- Visibility
- Precipitation Detail
Figure 3 Poor environment conditions
#### NonWeatherRelatedRoadConditions profile
NonWeatherRelatedRoadConditions are by definition not directly related to weather and therefore not on the focus of Road Weather Information Services. Nevertheless, weather effects can lead to situation like mud on the road or similar situations. Therefore, this class has been included in the RSP with the following literals of the NonWeatherRelatedRoadConditionsTypeEnum:
- mudOnRoad
- slipperyRoads
- other
#### EnvironmentalObstruction profile
For the EnvironmentalObstruction class, the optional depth attribute has been included in the profile, and the following weather-related enumeration literals have been selected for the environmentalObstructionType attribute:
- fallingIce
- fallingLight IceOrSnow
- flashFloods
- flooding
- landSlips
- mudSlide
- severOverflow
- stormDamage
- subsidence
- other
Note
The other literals are also part of some of the selected RRPs. Nevertheless, they are in principle not seen as relevant for a Road Weather Information Service and have been de-selected in this RSP. Publishers that want to publish this information as well should include them in their publication profile as described in section Application of the RSPs.
### RoadTrafficData Package
The RoadTrafficData package has to two publication types and for each a dedicated RSP is provided.
#### PayloadPublication profile (applicable to both RSPs)
The general ‘wrapper’ classes for conveying road weather related event information is PayloadPublication, the generic base class for all DATEX II publications. The optional attributes of the class PayloadPublication have all been kept in the RSP, since they are very generic by nature may be useful for Road Weather Information as well
#### MeasuredDataPublication profile
This is the package for the real-time flow of measurement results. The optional elements in the HeaderInformation class are all applicable in case of Road Weather Information and kept in the RSP.
Since all classes and attributes in the basic framework of this model are in general applicable to Road Weather Information as well, they have in principle been included in the RSP with the following exception: for the specialisations of the BasicData class, only WeatherData is included and the following sub-models were de-selected:
- TrafficStatus
- TravelTimeData
- TrafficData
Furthermore, for the pertinentLocation association, a similar profile as described in the Situation profile has been chosen for LocationReference, i.e. the profile includes all options for single Location instances and It does not contain Itenary. A difference here is that it also does not contain LocationGroup instances.
The profile has all location referencing systems enabled for all types of location, but the geography (coordinate) based location referencing systems have been made mandatory in order to support harmonisation of feeds. This comprises
- GmlMultiPolygon for area locations
- GmlLineString for linear locations
- PointByCoordinates for point locations
#### MeasurementSiteTablePublication profile
For the MeasurementSiteTablePublication, almost the full model is included in the RSP except for the following:
- The LocationReference attached as measurementSiteLocation is tailored in the same way as for the MeasuredDataPublication profile above
- The axleCharacteristics and specificVehicleCharacteristics associations have been deselected
- The literals for the specificMeasurementValueType have been restricted to the following weather-related values:
- humidityInformation
- pollutionInformation
- precipitationInformation
- pressureInformation
- roadSurfaceConditionInformation
- temperatureInformation
- visibilityInformation
- windInformation
### Application of the RSPs
(to be included in the handbook and include a reference to the specific profile documentation, specific profiling guidance etc.
: Generic section to introduce the recommended service profiles. What needs to be done with this RSP to make it usable and implementable. Guidance how to produce datadictionary)
In the profile section reference to the handbook:
The RSPs can be selected in the schema creation wizard at . If you want to implement the RSP “as-is”, you simply click through the wizard starting with the corresponding selection of the package in the first step (“SituationPublication without selection” or “RoadTrafficData” without selection). You skip Step 2 and choose the respective RSP in Step 3. Then you skip the subsequent steps and choose which type of output (XML Schema or JSON Schema) you want to produce in Step 5.
These schemas will then be used by the implementer of you Road Weather Information Service to create the interface software, e.g. by application of data binding.
If you service manages more data elements which have not been selected in the RSP, it is possible to extend the profile in Step 4 by selecting further elements.
https://webtool.datex2.eu/wizard
Go back to the previous page
