url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/mmtis/ls3-future-predicted-road-link-travel-times/
title: DATEX&nbsp;II packages addressed by the RRP Future Predicted Road Link traveltimes simple

## DATEX II packages addressed by the RRP Future Predicted Road Link traveltimes simple
This RRP tailors the following DATEX II model packages:
- Common – commonly used DATEX II data elements used by the tailored packages below (CEN/EN 16157-7:2018)
- LocationReferencing – the location references, tailored for traveltime data (CEN/EN 161578-2: 2019)
- RoadTrafficData – the DATEX II package for sensor data, tailored for traveltime data (CEN/EN 16157-5:2020)
Note 1: this profile is identical to the RRP for Future predicted road link traveltime in this section, except the usage of the attributes indicating that the data provided is a forecast. These are mandatory in this profile. Note 2: this profile is identical to the RRP for Travel times in the RTTI section. Except that this is limited to Road Links where the RTTI can also be applied to itineraries.
The RoadTrafficData is used for publishing information on traveltimes at roadlinks.
The profile supports one prediction per road link. In case multiple predictions in time per road link are available it is recommended to use RRP Future Predicted Road Link traveltimes Enhanced.
See Figure 1 for the ElaboratedDataPublication
It shall be used as:
- an ElaboratedDataPublication, is used for simple traveltime data provision, including the future predicted road link travel time
### ElaboratedData profile
The RoadTrafficData package is used to provide traveltime in ElaboratedDataPublication as a PhysicalQuantity -> SinglePhysicalQuantity specialising as TrafficData -> TravelTime , having averageVehicleSpeed
Instances of ElaboratedDataPublication contain one or more PhysicalQuantities (one per measurement per pertinentlocation), see Figure 2.
Figure 1 PhysicalQuantity in an elaborated data publication
The relevant time information stating the measurementtime and its meaning is provided in MeasurementOrCalculationTime by the attributes: - timeMeaning - timeValue
In case the traveltime represents an average, measured over a certain time interval, which is valid for all traveltimes provided in the publication, the length of the interval is provided in the periodDefault of ElaboratedDataPublication In case a measurementtime is valid for all traveltimes provided in the publication, this time is provided in the timeDefault of ElaboratedDataPublication. In that case timeValue as described above is omitted.
This RRP uses the TravelTimeData specialisation of BasicData. Here the travelTimeType can be provided, and the travelTime shall be provided in seconds in the attrribute:
- duration
### LocationReference profile
This RRP does not specify the locationreferencing methods to use. The applied method for location referencing is the choice of the specific user implementing this profile. The location of a measurement site for traveltime is a road link, an uninterrupted linear section of a road between two succeeding points where one can enter or leave that section.
This RRP does limit the use of SupplementaryPositionalDescription to identifying the affected carriageways and lanes on which the provided traveltime is valid.
Where relevant the lane identification and its use is provided as specificLane in the supplementaryPositionalDescription of the location.
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
