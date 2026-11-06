url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-962/td-1-traffic-volume/
title: DATEX&nbsp;II packages addressed by the RRP traffic volume

## DATEX II packages addressed by the RRP traffic volume
This RRP tailors the following DATEX II model packages:
- Common – commonly used DATEX II data elements used by the tailored packages below (CEN/EN 16157-7:2018)
- LocationReferencing – the location references, tailored for traffic volume data (CEN/EN 161578-2: 2019)
- RoadTrafficData – the DATEX II package for sensor data, tailored for traffic volume data (CEN/EN 16157-5:2020)
The RoadTrafficData is used for publishing sensor data information on traffic volume.
It can be use either as:
- an ElaboratedDataPublication, for simple measurements, or small sets of sensors and/or per vehicletype.
- a MeasurementSiteTablePublication in combination with a MeasuredDataPublication in the use case of larger sets of sensors, or distincted measurements on a variety of vehicle characteristics, like length catogories or vehicle type.
### ElaboratedData profile
The RoadTrafficData package is used to provide sensor measurements in ElaboratedDataPublication as a PhysicalQuantity -> SinglePhysicalQuantity specialising as TrafficData -> TrafficFlow , having vehicleFlow
Instances of ElaboratedDataPublication contain one or more PhysicalQuantities (one per measurement per location), see Figure 1.
Figure 1 PhysicalQuantity in an elaborated data publication
This RRP uses the following attribute:
- vehicleFlowRate
### MeasuredData and measurementSiteTable profile
In case of more complex or large sets of sensors, the MeasurementSiteTablePublication in combination with a MeasuredDataPublication should be used in order to reduce the size of the recurring data publication.
The actual measured datavalues are published with a measuredDataPublication, referring to a measurementsite or an index of the site related to a specific vehiclecharacteristic, in the MeasurementSiteTablePublication.
### MeasuredData profile
This is the package for the real-time flow of measurement results.
The RoadTrafficData package is used to provide sensor measurements in MeasuredDataPublication as SiteMeasurements -> PhysicalQuantity see Figure 2.
Figure 2 SiteMeasurements in a Measureddata publication
specialising as TrafficData -> TrafficFlow , having vehicleFlow
Instances of MeasuredDataPublication contain one or more PhysicalQuantities (one per measurement per index), see Figure 3.
Figure 3 PhysicalQuantity in a maesured data publication
This RRP uses the following attribute: - vehicleFlowRate
### MeasurementSiteTablePublication profile
For the MeasurementSiteTablePublication, the profile supports a measurementSiteLocation for each physical location where flow is measured. See figure 4.
Figure 4 MeasurementSiteTablePublication
a repetition of indexed instances of MeasurementSpecificCharacteristics is provided.
Within this RRP the following value of specificMeasurementValue is availabele: - trafficFlow
In case of grouping of distincted measurement for either: - lanes - vehicle characteristics
Where relevant the lane identification and its use is provided as specificLane in the MeasurementSpecificCharacteristics. So for each lane an indexed instance of MeasurementSpecificCharacteristics is in the MeasurementSite
laneUsage and laneNumber shall be used jointly to characterise lanes that are affected.
### LocationReference profile
This RRP does not specify the locationreferencing methods to use. The applied method for location referencing is the choice of the specific user implementing this profile. The location of a measurement site for traffic volume is usually a point, but it may also be a linear section of road or an area.
This RRP does limit the use of SupplementaryPositionalDescription to identifying the affected carriageway on which the measurementSiteLocations are positioned.
Where relevant the lane identification and its use is provided as specificLane in the MeasurementSpecificCharacteristics.
laneUsage and laneNumber shall be used jointly to characterise lanes that are affected.
#### Application of the RRP
The RRP can be selected in the schema creation wizard at DATEX II webtool.
- If you want to implement the RRP “as-is”, you simply click through the wizard starting with the default selection of the package in the first step.
You skip Step 2
Choose the respective RRP in Step 3.
In step 4 you select the locationreferencing method you are going to implement.
Then you skip the subsequent steps and choose which type of output (XML Schema or JSON Schema) you want to produce in Step 6.
These schemas will then be used by the implementer of you RRP to create the interface software, e.g. by application of data binding.
If you service manages more data elements which have not been selected in the RRP, it is possible to extend the profile in Step 5 by selecting further elements.
Go back to the previous page
