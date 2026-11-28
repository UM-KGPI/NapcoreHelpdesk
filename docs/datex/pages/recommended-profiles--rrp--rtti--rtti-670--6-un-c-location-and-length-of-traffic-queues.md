url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-670/6-un-c-location-and-length-of-traffic-queues/
title: Location and length of traffic queues

## Location and length of traffic queues
### DATEX II packages addressed by the RRP The types of data on the real-time use of the network
This RRP tailors the following DATEX II model packages:
- Common – commonly used DATEX II data elements used by the tailored packages below (CEN/EN 16157-7:2018)
- LocationReferencing – the location references, tailored for traffic status data (CEN/EN 161578-2: 2019)
- Situation – the DATEX II package for traffic situations, tailored for traffic queue data (CEN/EN 16157-5:2020)
- RoadTrafficData – the DATEX II package for sensor data, tailored for traffic status data (CEN/EN 16157-5:2020)
The Situation package is used for publishing event driven information on traffic queues as a SituationPublication. After the initial report, an update is sent when a change in location, length or type of congestion is observed/detected. Also when a congestion has ceased to exist, an update is sent in order to inform the consumer about that observation.
Instances of Situation -> SituationRecord -> TrafficElement -> AbnormalTraffic contain abnormalTrafficType and queueLength, see Figure 1.
Figure 1 SituationRecord
The available abnormalTrafficType litterals in this RRP are:
- stationaryTraffic
- queueingTraffic
- slowTraffic
The RoadTrafficData package is used for publishing on an regular interval basis (e.g. once every 5 minutes) information on traffic status, providing a full update of the traffic status on the roadsegments on which data is available. The roadsegments are published in a MeasurementSiteTablePublication. With a MeasuredDataPublication the cyclic update of the actual trafficStatus on the roadsegments is published.
### MeasuredData and measurementSiteTable profile
The actual measured datavalues are published with a measuredDataPublication, referring to a measurementsite or an index of the site related to a specific vehiclecharacteristic, in the MeasurementSiteTablePublication.
### MeasuredData profile
This is the package for the real-time traffic status per roadsegment.
The RoadTrafficData package is used to provide traffic status in MeasuredDataPublication as SiteMeasurements -> PhysicalQuantity. specialising as TrafficData -> TrafficStatus , having TrafficStatusValue.
Figure 2 SiteMeasurements in a Measureddata publication
This RRP uses the following attribute:
- trafficStatus
### MeasurementSiteTablePublication profile
For the MeasurementSiteTablePublication, the profile supports a measurementSiteLocation for each physical location where a traffic status is provided. See figure 4.
Figure 3 MeasurementSiteTablePublication
a repetition of indexed instances of MeasurementSpecificCharacteristics is provided.
Within this RRP the following value of specificMeasurementValue is availabele:
- trafficStatus
In case of grouping of distincted measurement for either:
- lanes
- vehicle characteristics
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
