url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-962/td-5-waiting-time-at-borders-with-non-eu-MS/
title: DATEX&nbsp;II packages addressed by the RRP Waiting time at borders with non-eu MS

## DATEX II packages addressed by the RRP Waiting time at borders with non-eu MS
The way waiting times at borders with non-EU Member States are interpreted by the different member states having such a border, require further engineering and most probably extensions of the DATEX II standard. THis will be carried out in 2022. Meanhwile this RRP is able to carry the minimum required information known to date.
This RRP tailors the following DATEX II model packages:
- Common – commonly used DATEX II data elements used by the tailored packages below (CEN/EN 16157-7:2018)
- LocationReferencing – the location references, tailored for traffic status data (CEN/EN 161578-2: 2019)
- Situation – the DATEX II package for traffic situations, tailored for waiting time at borders with non-eu MS (CEN/EN 16157-5:2020)
The Situation package is used for publishing event driven information on Waiting times as a SituationPublication. After the initial report, an update is sent when a change in length or treshold change of waiting time is observed/detected. Also when the waiting time is dimished to 0, an update is sent in order to inform the consumer about that observation.
A waiting time at the border is considered to be the delay a new arriving vehicle at the (queue tail) of those vehicles waiting to pass the border. Two characteristics are provided: the waiting time (could be vehicletype specific) and the length of the queue of waiting vehicles.
Instances of Situation -> SituationRecord -> TrafficElement -> Activity-> AuthorityOperation contain AuthorityOperation populated with:
- customsOperation
, see Figure 1.
Figure 1 SituationRecord
The delay is provided in SituationRecord -> Impact -> Delays -> delayTimeValue The length of the queue of waiting vehicles can be provided by the attribute lenthAffected in SupplementaryPositionalDescription in LocationReference When distinction is made for waiting times for busses and/or heavy vehicles, the way to express this is by using the laneUsage attribute in SupplementaryPositionalDescription -> Carriageway -> Lane. If no distinction is made, this can be omitted. As a consequence for each type of vehicle for which the waiting time is provided, a situation record has to be provided and updated.
### LocationReference profile
This RRP does not specify the locationreferencing methods to use. The applied method for location referencing is the choice of the specific user implementing this profile. The location of the waiting time could either be a point refering the exact location of the border, or it could be a linear section of road covering the stretch of road where the waiting vehicles are queing. In order to explicitly express that the location is at the border the geoGraphicDescriptor attribute in SupplementaryPositionalDescription of location shall be used, populated with the value onBorder.
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
