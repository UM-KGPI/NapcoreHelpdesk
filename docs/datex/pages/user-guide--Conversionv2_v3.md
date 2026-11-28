url: https://docs.datex2.eu/v3.7/user-guide/Conversionv2_v3/
title: Conversion of DATEX II version 2.3 to DATEX II version 3

## Conversion of DATEX II version 2.3 to DATEX II version 3
#### Some preliminary remarks
The basis for the mapping described here are the following versions:
- DATEX II v2.3
- DATEX II v3.6
In DATEX II version 3, in contrast to DATEX II version 2.3, multiple namespaces are used. In this documentation, namespaces are not explicitly named, because this is at the expense of the readability of the text. If, when applying this documentation, it turns out in practice that not mentioning namespaces is a major omission, then a practical way to include this information can, of course, be investigated.
#### Functional requirements
- The converted result should not contain self-closing tags in places where they are not present in the input.
- If an XML node occurs multiple times in the input, all corresponding XML nodes in the output must be generated (iterating).
### Reusable elements
#### VehicleCharacteristics maps to VehicleCharacteristics
In version 3 of the European DATEX II Model, the mandatory element typeOfWeight has been added to this complexType. If the mandatory element typeOfWeight is present in the version 3 target profile, it must be filled with 'actual'.
Source
Target
VehicleCharacteristics (V2.3) | VehicleCharacteristics (V3) | Remark
fuelType | fuelType
loadType | loadType
vehicleEquipment | vehicleEquipment
vehicleType | vehicleType
vehicleUsage | vehicleUsage
grossWeightCharacteristic | grossWeightCharacteristic
grossWeightCharacteristic.comparisonOperator | grossWeightCharacteristic.comparisonOperator
grossWeightCharacteristic.grossVehicleWeight | grossWeightCharacteristic.grossVehicleWeight
grossWeightCharacteristic.typeOfWeight | In version 3, the mandatory element typeOfWeight has been added. Default value = 'actual'.
heightCharacteristic | heightCharacteristic
heightCharacteristic.comparisonOperator | heightCharacteristic.comparisonOperator
heightCharacteristic.vehicleHeight | heightCharacteristic.vehicleHeight
lengthCharacteristic | lengthCharacteristic
lengthCharacteristic.comparisonOperator | lengthCharacteristic.comparisonOperator
lengthCharacteristic.vehicleLength | lengthCharacteristic.vehicleLength
widthCharacteristic | widthCharacteristic
widthCharacteristic.comparisonOperator | widthCharacteristic.comparisonOperator
widthCharacteristic.vehicleWidth | widthCharacteristic.vehicleWidth
#### lane maps to lane>laneNumber and lane>laneUsage
Source
Target 1
Target 2
LaneEnum (V2.3) | LaneEnum (V3) | laneNumber (V3) | Remark
allLanesCompleteCarriageway | allLanesCompleteCarriageway
busLane | busLane
busStop | busStop
carPoolLane | carPoolLane
centralReservation | centralReservation
crawlerLane | crawlerLane
emergencyLane | emergencyLane
escapeLane | escapeLane
expressLane | expressLane
hardShoulder | hardShoulder
heavyVehicleLane | heavyVehicleLane
lane1 | 1
lane2 | 2
lane3 | 3
lane4 | 4
lane5 | 5
lane6 | 6
lane7 | 7
lane8 | 8
lane9 | 9
layBy | layBy
leftHandTurningLane | leftHandTurningLane
leftLane | leftLane
localTrafficLane | localTrafficLane
middleLane | middleLane
opposingLanes | Not possible to map, element is not available in version 3
overtakingLane | overtakingLane
rightHandTurningLane | rightHandTurningLane
rightLane | rightLane
rushHourLane | rushHourLane
setDownArea | setDownArea
slowVehicleLane | slowVehicleLane
throughTrafficLane | throughTrafficLane
tidalFlowLane | tidalFlowLane
turningLane | turningLane
verge | verge
cycleLane | Does not exist in v2.3, nothing to convert
#### GroupOfLocations maps to LocationReference
#### Reusable elements GroupOfLocations
#### SupplementaryPositionalDescription and originalNumberOfLanes map to SupplementaryPositionalDescription
Input class
Source
Target
v2.3 | v2.3 | supplementaryPositionalDescription (V3) | Remark
SupplementaryPositionalDescription. | locationDescriptor | infrastructureDescriptor | With use of enumeration mapping
SupplementaryPositionalDescription. | affectedCarriagewayAndLanes.lengthAffected | lengthAffected
SupplementaryPositionalDescription. | locationDescriptor | positionOnCarriageway | With use of enumeration mapping
SupplementaryPositionalDescription. | affectedCarriagewayAndLanes.carriageway | carriageway.carriageway
Impact. | originalNumberOfLanes | carriageway.originalNumberOfLanes
SupplementaryPositionalDescription. | affectedCarriagewayAndLanes.lane | carriageway.lane.laneNumber | With use of enumeration mapping
SupplementaryPositionalDescription. | affectedCarriagewayAndLanes.lane | carriageway.lane.laneUsage | With use of enumeration mapping
#### LocationDescriptor maps to InfrastructureDescriptor and PositionOnCarriageway
Source
Target 1
Target 2
LocationDescriptor (V2.3) | InfrastructureDescriptor (V3) | PositionOnCarriageway (V3)
atMotorwayInterchange | atMotorwayInterchange
atRestArea | atRestArea
atServiceArea | atServiceArea
atTollPlaza | atTollPlaza
atTunnelEntryOrExit | atTunnelEntryOrExit
inGallery | inGallery
inTunnel | inTunnel
onBridge | onBridge
onConnector | onConnector
onElevatedSection | onElevatedSection
onFlyover | onFlyover
onIceRoad | onIceRoad
onLevelCrossing | onLevelCrossing
onLinkRoad | onLinkRoad
onRoundabout | onRoundabout
onTheRoadway | onTheRoadway
onUndergroundSection | onUndergroundSection
onUnderpass | onUnderpass
withinJunction | withinJunction
onTheLeft | onTheLeft
onTheRight | onTheRight
inTheCentre | inTheCentre
#### openlrFunctionalRoadClassEnum maps to openlrFunctionalRoadClassEnum
Source
Target
openlrFunctionalRoadClassEnum (V2.3) | openlrFunctionalRoadClassEnum (V3)
FRC0 | frc0
FRC1 | frc1
FRC2 | frc2
FRC3 | frc3
FRC4 | frc4
FRC5 | frc5
FRC6 | frc6
FRC7 | frc7
#### alertCDirectionEnum maps to alertCDirectionEnum
Source
Target
AlertCDirectionEnum (V2.3) | alertCDirectionEnum (V3)
both
negative | negative
positive | positive
unknown
Definitions:
- Version 2.3 definition alertCDirectionEnum = "The direction of traffic flow concerned by a situation or traffic data. In ALERT-C the positive (resp. negative) direction corresponds to the positive offset direction within the RDS location table."
- Version 3 definition alertCDirectionEnum = "Direction used to reach the primary location from the secondary location in ALERT-C location table, as defined in CEN ISO 14819-1"
#### Linear maps to SingleRoadLinearLocation or to LinearLocation
- If in a version 2.3 Linear both AlertCLinear type AlertCMethod2Linear and AlertCLinear type AlertCMethod4Linear are not included, and openLrExtendedLinear is included, then the entire content of Linear must be mapped to version 3 LinearLocation
- If a version 2.3 Linear contains at least one of AlertCLinear type AlertCMethod2Linear or AlertCLinear type AlertCMethod4Linear, then the entire content of Linear must be mapped to version 3 SingleRoadLinearLocation
#### locationForDisplay maps to coordinatesForDisplay
- locationForDisplay.latitude maps to coordinatesForDisplay.latitude
- locationForDisplay.longitude maps to coordinatesForDisplay.longitude
#### SupplementaryPositionalDescription maps to SupplementaryPositionalDescription
Click here for the mapping to version 3 SupplementaryPositionalDescription.
#### AlertCLinear type AlertCMethod2Linear maps to AlertCLinear type AlertCMethod2Linear
The elements of AlertCLinear type AlertCMethod2Linear map 1-to-1 from version 2.3 to version 3 AlertCLinear type AlertCMethod2Linear.
#### AlertCLinear type AlertCMethod4Linear maps to AlertCLinear type AlertCMethod4Linear
The elements of AlertCLinear type AlertCMethod4Linear, map 1-to-1 from version 2.3 to version 3 AlertCLinear type AlertCMethod4Linear.
#### LinearExtension
#### openLrExtendedLinear maps to element openLrLinear
openLrExtendedLinear maps, with one exceptions, see below, to openLrLinear. The exception is:
- Version 2.3 element openlrCoordinate maps to version 3 element openlrCoordinates
#### Point maps to PointLocation
#### locationForDisplay maps to coordinatesForDisplay
- locationForDisplay.latitude maps to coordinatesForDisplay.latitude
- locationForDisplay.longitude maps to coordinatesForDisplay.longitude
#### SupplementaryPositionalDescription maps to SupplementaryPositionalDescription
Click here for the mapping to version 3 SupplementaryPositionalDescription.
#### alertCPoint type AlertCMethod2Point maps to alertCPoint type AlertCMethod2Point
The elements of alertCPoint type AlertCMethod2Point map 1-to-1 from version 2.3 to version 3 alertCPoint type AlertCMethod2Point.
#### alertCPoint type AlertCMethod4Point maps to alertCPoint type AlertCMethod4Point
The elements of alertCPoint type AlertCMethod4Point map 1-to-1 from version 2.3 to version 3 alertCPoint type AlertCMethod4Point.
#### openlrPointAlongLine maps to openlrPointLocationReference type OpenlrPointAlongLine
Example
Version 2.3Version 3
<openlrPointAlongLine> <openlrSideOfRoad>onRoadOrUnknown</openlrSideOfRoad> <openlrOrientation>noOrientationOrUnknown</openlrOrientation> <openlrPositiveOffset>184</openlrPositiveOffset> <openlrLocationReferencePoint> <openlrCoordinate> <latitude>52.0115128</latitude> <longitude>4.45868063</longitude> </openlrCoordinate> <openlrLineAttributes> <openlrFunctionalRoadClass>FRC3</openlrFunctionalRoadClass> <openlrFormOfWay>multipleCarriageway</openlrFormOfWay> <openlrBearing>223</openlrBearing> </openlrLineAttributes> <openlrPathAttributes> <openlrLowestFRCToNextLRPoint>FRC3</openlrLowestFRCToNextLRPoint> <openlrDistanceToNextLRPoint>1302</openlrDistanceToNextLRPoint> </openlrPathAttributes> </openlrLocationReferencePoint> <openlrLastLocationReferencePoint> <openlrCoordinate> <latitude>52.001442</latitude> <longitude>4.45368862</longitude> </openlrCoordinate> <openlrLineAttributes> <openlrFunctionalRoadClass>FRC3</openlrFunctionalRoadClass> <openlrFormOfWay>multipleCarriageway</openlrFormOfWay> <openlrBearing>59</openlrBearing> </openlrLineAttributes> </openlrLastLocationReferencePoint> </openlrPointAlongLine>
<loc:openlrPointLocationReference xmlns="http://datex2.eu/schema/3/locationReferencing" xsi:type="loc:OpenlrPointAlongLine"> <loc:openlrSideOfRoad>onRoadOrUnknown</loc:openlrSideOfRoad> <loc:openlrOrientation>noOrientationOrUnknown</loc:openlrOrientation> <loc:openlrLocationReferencePoint> <loc:openlrCoordinates> <loc:latitude>52.01151</loc:latitude> <loc:longitude>4.458681</loc:longitude> </loc:openlrCoordinates> <loc:openlrLineAttributes> <loc:openlrFunctionalRoadClass>frc3</loc:openlrFunctionalRoadClass> <loc:openlrFormOfWay>multipleCarriageway</loc:openlrFormOfWay> <loc:openlrBearing>223</loc:openlrBearing> </loc:openlrLineAttributes> <loc:openlrPathAttributes> <loc:openlrLowestFrcToNextLRPoint>frc3</loc:openlrLowestFrcToNextLRPoint> <loc:openlrDistanceToNextLRPoint>1302</loc:openlrDistanceToNextLRPoint> </loc:openlrPathAttributes> </loc:openlrLocationReferencePoint> <loc:openlrLastLocationReferencePoint> <loc:openlrCoordinates> <loc:latitude>52.00144</loc:latitude> <loc:longitude>4.453689</loc:longitude> </loc:openlrCoordinates> <loc:openlrLineAttributes> <loc:openlrFunctionalRoadClass>frc3</loc:openlrFunctionalRoadClass> <loc:openlrFormOfWay>multipleCarriageway</loc:openlrFormOfWay> <loc:openlrBearing>59</loc:openlrBearing> </loc:openlrLineAttributes> </loc:openlrLastLocationReferencePoint> <loc:openlrOffsets> <loc:openlrPositiveOffset>184</loc:openlrPositiveOffset> </loc:openlrOffsets> </loc:openlrPointLocationReference>
#### pointByCoordinates maps to pointByCoordinates
The version 2.3 element tree pointByCoordinates maps 1-to-1 to version 3 element tree pointByCoordinates.
#### pointExtension>openLrExtendedPoint>openLrPointAlongLine maps to openLrPointLocationReference type OpenlrPointAlongLine
openLrPointAlongLine maps, with two exceptions, see below, to openLrPointLocationReference type OpenlrPointAlongLine. The next two points should be mapped as follows:
- Version 2.3 openlrCoordinate maps to version 3 openlrCoordinates
- Version 2.3 openlrFunctionalRoadClass and openlrLowestFRCToNextLRPoint map 1-op-1 to the same element in version 3 if the enumeration literals are converted from upper case to lower case. See the enumeration mapping over here.
#### NonOrderedLocationGroupByList maps to LocationGroupByList
Both version 2.3 NonOrderedLocationGroupByList and version 3 LocationGroupByList contain the locationContainedInGroup element. The type of locationContainedInGroup is chosen depending on the application.
- Version 2.3 Linear maps to version 3 LinearLocation or SingleRoadLinearLocation; see here for more detail.
- Version 2.3 Point maps to version 3 PointLocation; see here for more detail.
#### Area maps to AreaLocation
#### locationForDisplay maps to coordinatesForDisplay
- locationForDisplay.latitude maps to coordinatesForDisplay.latitude
- locationForDisplay.longitude maps to coordinatesForDisplay.longitude
#### alertCArea maps to alertCArea
The elements of alertCArea map 1-to-1 from version 2.3 to version 3 alertCArea.
#### ItineraryByIndexedLocations maps to ItineraryByIndexedLocations
The mapping from version 2.3 ItineraryByIndexedLocations maps to version 3 ItineraryByIndexedLocations as described below. References to necessary sub-mappings are included.
- Version 2.3 routeDestination type AreaDestination maps to version 3 routeDestination type AreaDestination
- Area maps to AreaLocation, see here
- Version 2.3 routeDestination type PointDestination maps to version 3 routeDestination type PointDestination
- Point maps to PointLocation, see here
- Version 2.3 locationContainedInItinerary maps to version 3 locationContainedInItinerary
- Area maps to AreaLocation, see here
- Linear maps to LinearLocation or SingleRoadLinearLocation, see here
- Point maps to PointLocation, see here
### SituationPublication maps to SituationPublication
Source
Target
payloadPublication xsi:type="SituationPublication" (V2.3) | payload xsi:type="sit:SituationPublication" (V3) | Remark
lang | lang
modelBaseVersion | Fill this required element for version 3 with the value 3
publicationTime | publicationTime
publicationCreator | publicationCreator
publicationCreator.country | publicationCreator.country
publicationCreator.nationalIdentifier | publicationCreator.nationalIdentifier
Example
Version 2.3Version 3
<payloadPublication xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="SituationPublication" lang="nl"> <publicationTime>2022-11-22T17:07:41.507Z</publicationTime> <publicationCreator> <country>nl</country> <nationalIdentifier>NLNDW</nationalIdentifier> </publicationCreator> ... here situation(s)... </payloadPublication>
<payload xsi:type="sit:SituationPublication" lang="nl" modelBaseVersion="3"> <com:publicationTime>2022-11-22T17:07:41.507Z</com:publicationTime> <com:publicationCreator> <com:country>nl</com:country> <com:nationalIdentifier>NLNDW</com:nationalIdentifier> </com:publicationCreator> ... here situation(s)... </payload>
### Situation maps to Situation
Source
Target
situation (V2.3) | situation (V3) | Remark
situation.id | situation.id
situation.version | In version 3, situation.version does not exist, so it cannot be mapped.
overallSeverity | overallSeverity
relatedSituation | relatedSituation | In version 3, the reference is implemented differently. In version 3, a relatedSituation must be created with an objectReference in it
relatedSituation | objectReference
relatedSituation.id | objectReference.id
relatedSituation.version | In version 3, situation.version does not exist, so it cannot be mapped.
targetClass | targetClass | The targetClass in version 3 must be provided with the correct namespace prefix. If "sit" is the prefix of the SituationPublication namespace from V3, "sit:" must be inserted before the value of the targetClass as it is included in V2.3
situationVersionTime | situationVersionTime
headerInformation | headerInformation
headerInformation.confidentiality | headerInformation.confidentiality
headerInformation.informationStatus | headerInformation.informationStatus
Example
Version 2.3Version 3
<situation id="RWS01_SP448064_D2" version="18"> <overallSeverity>medium</overallSeverity> <relatedSituation targetClass="Situation" id="RWS01_SM811801_D2" version="15"/> <situationVersionTime>2022-09-08T13:03:00Z</situationVersionTime> <headerInformation> <confidentiality>noRestriction</confidentiality> <informationStatus>real</informationStatus> </headerInformation> ... here situationRecord(s)... </situation>
<sit:situation id="RWS01_SM811801_D2"> <sit:overallSeverity xmlns="http://datex2.eu/schema/3/situation">medium</sit:overallSeverity> <sit:situationVersionTime xmlns="http://datex2.eu/schema/3/situation">2022-11-16T09:12:10Z</sit:situationVersionTime> <sit:headerInformation xmlns="http://datex2.eu/schema/3/situation"> <com:confidentiality>noRestriction</com:confidentiality> <com:informationStatus>real</com:informationStatus> </sit:headerInformation> ... here situationRecord(s)... <sit:relatedSituation xmlns=“http://datex2.eu/schema/3/situation”> <sit:objectReference id=“RWS01_SP448064_D2” targetClass=“sit:Situation”/> </sit:relatedSituation> </sit:situation>
### SituationRecord (base type) maps to SituationRecord (base type)
#### Elements
The following elements map 1-to-1.
Source
Target
situationRecord (V2.3) | situationRecord (V3)
situationRecord.id | situationRecord.id
situationRecord.version | situationRecord.version
situationRecordCreationTime | situationRecordCreationTime
situationRecordFirstSupplierVersionTime | situationRecordFirstSupplierVersionTime
situationRecordObservationTime | situationRecordObservationTime
situationRecordVersionTime | situationRecordVersionTime
situationRecordCreationReference | situationRecordCreationReference
probabilityOfOccurrence | probabilityOfOccurrence
SituationRecordExtension >
SituationRecordExtendedApproved >
safetyRelatedMessage | safetyRelatedMessage
#### Source maps to Source
The structure of the Source element tree is analogous for version 2.3 and version 3. All elements must be mapped 1-to-1.
#### Validity maps to Validity
Source
Target
validity (V2.3) | validity (V3) | Remark
validityStatus | validityStatus
overrunning | overrunning
validityTimeSpecification.overallStartTime | validityTimeSpecification.overallStartTime
validityTimeSpecification.overallEndTime | validityTimeSpecification.overallEndTime
validityTimeSpecification.validPeriod.startOfPeriod | validityTimeSpecification.validPeriod.startOfPeriod
validityTimeSpecification.validPeriod.endOfPeriod | validityTimeSpecification.validPeriod.endOfPeriod
validityTimeSpecification.validPeriod.periodName | validityTimeSpecification.validPeriod.periodName
validityTimeSpecification.validPeriod.recurringTimePeriodOfDay.startTimeOfPeriod | validityTimeSpecification.validPeriod.recurringTimePeriodOfDay.startTimeOfPeriod | version 2.3: recurringTimePeriodOfDay = recurringTimePeriodOfDay xsi-type="TimePeriodByHour"
validityTimeSpecification.validPeriod.recurringTimePeriodOfDay.endTimeOfPeriod | validityTimeSpecification.validPeriod.recurringTimePeriodOfDay.endTimeOfPeriod | version 2.3: recurringTimePeriodOfDay = recurringTimePeriodOfDay xsi-type="TimePeriodByHour"
validityTimeSpecification.validPeriod.recurringDayWeekMonthPeriod.applicableDay | validityTimeSpecification.validPeriod.recurringDayWeekMonthPeriod.applicableDay
validityTimeSpecification.validPeriod.recurringDayWeekMonthPeriod.applicableWeek | In version 3, situation.version does not exist, so it cannot be mapped.
validityTimeSpecification.validPeriod.recurringDayWeekMonthPeriod.applicableMonth | validityTimeSpecification.validPeriod.recurringDayWeekMonthPeriod.applicableMonth
validityTimeSpecification.exceptionPeriod.startOfPeriod | validityTimeSpecification.exceptionPeriod.startOfPeriod
validityTimeSpecification.exceptionPeriod.endOfPeriod | validityTimeSpecification.exceptionPeriod.endOfPeriod
validityTimeSpecification.exceptionPeriod.periodName | validityTimeSpecification.exceptionPeriod.periodName
validityTimeSpecification.exceptionPeriod.recurringTimePeriodOfDay.startTimeOfPeriod | validityTimeSpecification.exceptionPeriod.recurringTimePeriodOfDay.startTimeOfPeriod | version 2.3: recurringTimePeriodOfDay = recurringTimePeriodOfDay xsi-type="TimePeriodByHour"
validityTimeSpecification.exceptionPeriod.recurringTimePeriodOfDay.endTimeOfPeriod | validityTimeSpecification.exceptionPeriod.recurringTimePeriodOfDay.endTimeOfPeriod | version 2.3: recurringTimePeriodOfDay = recurringTimePeriodOfDay xsi-type="TimePeriodByHour"
validityTimeSpecification.exceptionPeriod.recurringDayWeekMonthPeriod.applicableDay | validityTimeSpecification.exceptionPeriod.recurringDayWeekMonthPeriod.applicableDay
validityTimeSpecification.exceptionPeriod.recurringDayWeekMonthPeriod.applicableWeek | In version 3, situation.version does not exist, so it cannot be mapped.
validityTimeSpecification.exceptionPeriod.recurringDayWeekMonthPeriod.applicableMonth | validityTimeSpecification.exceptionPeriod.recurringDayWeekMonthPeriod.applicableMonth
#### Impact maps to Impact, SupplementaryPositionalDescription and TrafficElement
Source
Target
Impact (V2.3) | Impact (V3) | Remark
capacityRemaining | capacityRemaining
numberOfLanesRestricted | numberOfLanesRestricted
numberOfOperationalLanes | numberOfOperationalLanes
orignalNumberOfLanes | SupplementaryPositionalDescription.Carriageway.originalNumberOfLanes | Element moved in version 3
residualRoadWidth | residualRoadWidth
trafficConstrictionType | TrafficElement.trafficConstrictionType | Element moved in version 3
delays.delayBand | delays.delayBand
delays.delaysType | delays.delaysType
delays.delayTimeValue | delays.delayTimeValue
Click here for more context for the mapping of Impact.originalNumberOfLanes to version 3 SupplementaryPositionalDescription.carriageway.originalNumberOfLanes.
Notes:
- Definition of:
- Version 2.3 trafficConstrictionType = "The type of constriction to which traffic is subjected as a result of an event or operator action."
- Version 3 TrafficElement.trafficConstrictionType = "The type of constriction to which traffic is subjected as a result of an unplanned event"
- Definition of:
- Version 2.3 originalNumberOfLanes = "The normal number of usable lanes in the specified direction that the carriageway has before reduction due to roadworks or traffic events."
- Version 3 SupplementaryPositionalDescription.Carriageway.originalNumberOfLanes = "Normal number of lanes, potentially available for moving traffic, before reduction due to situations. Hard shoulder should not be counted unless it is sometimes used operationally for moving traffic."
#### Cause maps to Cause
Source
Target
cause xsi:type="NonManagedCause" (V2.3) | cause (V3)
causeDescription | causeDescription
causeType | causeType
Source
Target
cause xsi:type="ManagedCause" (V2.3) | cause.managedCause (V3) | Remark
managedCause | cause.managedCause.objectReference
managedCause.id | cause.managedCause.objectReference.id
managedCause.version | cause.managedCause.objectReference.version
managedCause.targetClass | cause.managedCause.objectReference.targetClass | The targetClass in version 3 must be provided with the correct namespace prefix. If "sit" is the prefix of the SituationPulication namespace from version 3, "sit:" must be inserted before the value of the targetClass as included in version 2.3
#### generalPublicComment maps to generalPublicComment
The structure of the element tree generalPublicComment is analogous for version 2.3 and version 3. All elements map 1-to-1.
#### UrlLink maps to UrlLink
The structure of the element tree UrlLink is analogous for version 2.3 and version 3. All elements map 1-to-1.
#### GroupOfLocations maps to LocationReference
### NonRoadEventInformation (abstract) maps to ServiceInformation (abstract)
The abstract class NonRoadEventInformation contains no elements that have to be mapped.
#### TransitInformation maps to TransitInformation
Elements transitServiceInformation and transitServiceType map 1-to-1 from version 2.3 to version 3.
#### RoadsideServiceDisruption maps to ServiceDisruption
Version 2.3 element roadsideServiceDisruptionType maps to version 3 element ServiceDisruptionType.
#### CarParks maps to ServiceDisruption
Note
The DATEX II version 2.3 specialization NonRoadEventInformation>Carparks no longer exists in DATEX II version 3. This section describes a limited mapping to version 3 ServiceDisruption.
CarParks can be mapped to Service Information>Service Disruption with ServiceDisruptionType = noParkingAvailability.
This must be done for the enumerations of CarParkStatusEnum as described in the table below.
Source
Target
CarParkStatusEnum (V2.3) | ServiceDisruptionTypeEnum (V3)
carParkClosed | noParkingAvailability
allCarParksFull | noParkingAvailability
carParkFull | noParkingAvailability
noMoreParkingSpacesAvailable | noParkingAvailability
Not mapped in this mapping | Not used in this mapping
carParkFacilityFaulty | barClosed
carParkStatusUnknown | dieselShortage
enoughSpacesAvailable | fuelShortage
multiStoryCarParksFull | lpgShortage
noParkAndRideInformation | methaneShortage
noParkingAllowed | noDieselForHeavyVehicles
noParkingInformationAvailable | noDieselForLightVehicles
normalParkingRestrictionsLifted | noPublicTelephones
onlyAFewSpacesAvailable | noToiletFacilities
parkAndRideServiceNotOperating | noVehicleRepairFacilities
parkAndRideServiceOperating | petrolShortage
specialParkingRestrictionsInForce | restAreaBusy
restAreaClosed
restAreaOvercrowdedDriveToAnotherRestArea
serviceAreaBusy
serviceAreaClosed
serviceAreaFuelStationClosed
serviceAreaOvercrowdedDriveToAnotherServiceArea
serviceAreaRestaurantClosed
someCommercialServicesClosed
waterShortage
Note:
- Version 2.3 element carParkIdentity is not mapped, if desired, it could be mapped, for example, to a generalPublicComment.
### TrafficElement (abstract) maps to TrafficElement (abstract)
Pay attention
The version 2.3 element Impact>trafficConstrictionType maps to version 3 element TrafficElement>trafficConstrictionType.
#### Conditions maps to Conditions
Element drivingConditionType maps 1-to-1 from version 2.3 to version 3.
#### PoorEnvironmentConditions maps to PoorEnvironmentConditions
Element PoorEnvironmentType maps 1-to-1 from version 2.3 to version 3.
The element tree Visibility maps to the element tree Visibility.
#### RoadConditions (abstract) maps to RoadSurfaceConditions (abstract)
The abstract class RoadConditions contains no elements that have to be mapped.
#### NonWeatherRelatedRoadConditions maps to NonWeatherRelatedRoadConditions
Element nonWeatherRelatedRoadConditionType maps 1-to-1 from version 2.3 to version 3.
#### WeatherRelatedRoadConditions maps to WeatherRelatedRoadConditions
The version 2.3 values/enumeration literals of WeatherRelatedRoadConditionType/WeatherRelatedRoadConditionTypeEnum are, with exception of one, one 1-to-1 mappable to the corresponding version 3 literals. The exception WeatherRelatedRoadConditionTypeEnum literal 'slipperyRoad' should be recoded to 'slippery'.
#### AbnormalTraffic maps to AbnormalTraffic
Elements abnormalTrafficType, queueLength, relativeTrafficFlow, trafficFlowCharacteristics and trafficTrendType map 1-to-1 from version 2.3 to version 3.
#### EquipmentOrSystemFault maps to EquipmentOrSystemFault
Elements equipmentOrSystemFaultType and faultyEquipmentOrSystemType map 1-to-1 from version 2.3 to version 3.
#### Accident maps to Accident
#### accidentType maps to accidentType and collisionType
Source
Target 1
Target 2
AccidentTypeEnum (V2.3) | AccidentTypeEnum (V3) | CollisionTypeEnum (V3)
accident | accident
accidentInvolvingBicycles | accident
accidentInvolvingBuses | accident
accidentInvolvingHazardousMaterials | accidentInvolvingHazardousMaterials
accidentInvolvingHeavyLorries | accidentInvolvingHeavyLorries
accidentInvolvingMassTransitVehicle | accidentInvolvingMassTransitVehicle
accidentInvolvingMopeds | accident
accidentInvolvingMotorcycles | accident
accidentInvolvingRadioactiveMaterial | accidentInvolvingRadioactiveMaterial
accidentInvolvingTrain | accidentInvolvingTrain
chemicalSpillageAccident | accident
collision | collision
collisionWithAnimal | collision | collisionWithAnimal
collisionWithObstruction | collision | collisionWithObstacle
collisionWithPerson | collision | collisionWithPerson
earlierAccident | accident
fuelSpillageAccident | accident
headOnCollision | collision | headOnCollision
headOnOrSideCollision | collision | headOnOrSideCollision
jackknifedArticulatedLorry | accident
jackknifedCaravan | accident
jackknifedTrailer | accident
multipleVehicleCollision | collision | multipleVehicleCollision
multivehicleAccident | multipleVehicleAccident
oilSpillageAccident | accident
overturnedHeavyLorry | accident
overturnedTrailer | accident
overturnedVehicle | accident
rearCollision | collision | rearCollision
secondaryAccident | secondaryAccident
seriousAccident | accident
sideCollision | collision | sideCollision
vehicleOffRoad | accident
vehicleSpunAround | accident
other | other
Does not exist in v2.3, nothing to convert | accidentInvolvingPublicTransport
Does not exist in v2.3, nothing to convert | seriousInjuryOrFatalAccident
Does not exist in v2.3, nothing to convert | vehicleStuckUnderBridge
#### Obstruction (abstract) maps to Obstruction (abstract)
The abstract class Obstruction contains no elements that have to be mapped.
#### mobilityOfObstruction
Version 2.3 element tree mobilityOfObstruction maps to the version 3 element tree mobilityOfObstruction.
#### AnimalPresenceObstruction maps to AnimalPresenceObstruction
Elements alive and animalPresenceType map 1-to-1 from version 2.3 to version 3.
#### EnvironmentalObstruction maps to EnvironmentalObstruction
Element environmentalObstructionType maps 1-to-1 from version 2.3 to version 3.
#### InfrastructureDamageObstruction maps to InfrastructureDamageObstruction
Element infrastructureDamageType maps 1-to-1 from version 2.3 to version 3.
#### GeneralObstruction maps to GeneralObstruction
Element ObstructionType must be mapped from version 2.3 to version 3.
The version 2.3 values/enumeration literals of obstructionType/ObstructionTypeEnum are mostly mappable 1-to-1 to the corresponding version 3 literals.
The ObstructionTypeEnum literals highSpeedChase, houseFire and recklessDriver, no longer exist in version 3 and should be mapped to 'other'.
#### VehicleObstruction maps to VehicleObstruction
Element vehicleObstructionType must be mapped from version 2.3 to version 3 according to a conversion table.
#### vehicleObstructionType maps to vehicleObstructionType
Source
Target
VehicleObstructionTypeEnum (V2.3) | VehicleObstructionTypeEnum (V3)
abandonedVehicle | abandonedVehicle
abnormalLoad | abnormalLoad
brokenDownBus | brokenDownVehicle
brokenDownHeavyLorry | brokenDownVehicle
brokenDownVehicle | brokenDownVehicle
convoy | convoy
damagedVehicle | damagedVehicle
dangerousSlowMovingVehicle | dangerousSlowMovingVehicle
emergencyVehicle | emergencyVehicle
highSpeedEmergencyVehicle | highSpeedEmergencyVehicle
longLoad | longLoad
militaryConvoy | militaryConvoy
overheightVehicle | overheightVehicle
prohibitedVehicleOnTheRoadway | prohibitedVehicleOnTheRoad
slowMovingMaintenanceVehicle | slowVehicle
slowVehicle | slowVehicle
trackLayingVehicle | trackedVehicle
unlitVehicleOnTheRoad | unlitVehicleOnTheRoad
vehicleOnFire | vehicleOnFire
vehicleCarryingHazardousMaterials | vehicleCarryingHazardousMaterials
vehicleInDifficulty | vehicleInDifficulty
vehicleOnWrongCarriageway | vehicleOnWrongCarriageway
vehicleStuck | vehicleStuck
vehicleStuckUnderBridge | vehicleStuck
vehicleWithOverheightLoad | vehicleWithOverheightLoad
vehicleWithOverwideLoad | vehicleWithOverwideLoad
other | other
saltingOrGrittingVehicleInUse | other
snowplough | other
Does not exist in v2.3, nothing to convert | highSpeedChase
Does not exist in v2.3, nothing to convert | medicalEmergency
Does not exist in v2.3, nothing to convert | recklessDriver
Does not exist in v2.3, nothing to convert | winterMaintetanceVehicleInTransfer
Does not exist in v2.3, nothing to convert | specialPermitTransport
#### Activity (abstract) maps to Activity (abstract)
The abstract class Activity contains no elements that have to be mapped.
#### AuthorityOperation maps to AuthorityOperation
Element authorityOperationType maps 1-to-1 from version 2.3 to version 3.
#### PublicEvent maps to PublicEvent
Element publicEventType maps 1-to-1 from version 2.3 to version 3.
#### DisturbanceActivity
Element disturbanceActivityType maps 1-to-1 from version 2.3 to version 3.
### OperatorAction (abstract) maps to OperatorAction (abstract)
Element operatorActionStatus maps 1-to-1 from version 2.3 to version 3.
#### RoadsideAssistance maps to RoadsideAssistance
Element roadsideAssistanceType maps 1-to-1 from version 2.3 to version 3.
#### NetworkManagement (abstract) maps to NetworkManagement (abstract)
Elements applicableForTrafficDirection and complianceOption map 1-to-1 from version 2.3 to version 3.
The element tree forVehiclesWithCharateristicsOf maps to the element tree forVehiclesWithCharateristicsOf.
#### ReroutingManagement maps to ReroutingManagement
Elements reroutingManagementType, reroutingItineraryDescription and signedRerouting map 1-to-1 from version 2.3 to version 3.
The element tree alternative Route maps to the element tree alternative Route.
#### SpeedManagement maps to SpeedManagement
Elements speedManagementType and temporarySpeedLimit map 1-to-1 from version 2.3 to version 3.
#### RoadOrCarriagewayOrLaneManagement maps to RoadOrCarriagewayOrLaneManagement
Element roadOrCarriagewayOrLaneManagementType maps 1-to-1 from version 2.3 to version 3.
#### GeneralInstructionOrMessageToRoadUsers maps to GeneralInstructionOrMessageToRoadUsers
Elements generalInstructionToRoadUsersType and generalMessageToRoadUsers map 1-to-1 from version 2.3 to version 3.
#### GeneralNetworkManagement maps to GeneralNetworkManagement
Elements generalNetworkManagementType and trafficManuallyDirectedBy map 1-to-1 from version 2.3 to version 3.
#### RoadWorks (abstract) maps to RoadWorks (abstract)
Source
Target
RoadWorks (V2.3) | RoadWorks (V3) | Remark
roadworksDuration | roadworksDurationClassification | Element has a different name in version 3, enumeration literals have remained the same.
roadworksScale | roadworksScale
urgentRoadWorks | urgentRoadWorks
Mobility | Mobility
mobility.mobilityType | mobility.mobilityType
#### Subjects maps to Subjects
Element Subjects.subjectTypeOfWorks maps 1-to-1 from version 2.3 to version 3.
#### ConstructionWorks maps to ConstructionWorks
Element constructionWorkType maps 1-to-1 from version 2.3 to version 3.
#### MaintenanceWorks maps to MaintenanceWorks
Element roadMaintenanceType maps 1-to-1 from version 2.3 to version 3.
### MeasurementSiteTablePublication maps to MeasurementSiteTablePublication
Source
Target
payloadPublication xsi:type="MeasurementSiteTablePublication" (V2.3) | payload xsi:type="roa:MeasurementSiteTablePublication" (V3) | Remark
lang | lang
modelBaseVersion | Fill this required element for version 3 with the value 3
publicationTime | publicationTime
publicationCreator | publicationCreator
publicationCreator.country | publicationCreator.country
publicationCreator.nationalIdentifier | publicationCreator.nationalIdentifier
headerInformation.confidentiality | headerInformation.confidentiality
headerInformation.informationStatus | headerInformation.informationStatus
MeasurementSiteTable.id | MeasurementSiteTable.id
MeasurementSiteTable.version | MeasurementSiteTable.version
---.MeasurementSiteRecord.id | ---.MeasurementSite.id | MeasurementSiteRecord has been renamed to MeasurementSite in version 3
---.MeasurementSiteRecord.version | ---.MeasurementSite.version
---.MeasurementSiteRecord.measurementSiteRecordVersionTime | ---.MeasurementSite.MeasurementSiteVersionTime
---.MeasurementSiteRecord.computationMethod | ---.MeasurementSite.measurementSpecificCharacteristics.computationMethod | Element moved in version 3
---.MeasurementSiteRecord.measurementEquipmentReference | ---.MeasurementSite.measurementEquipmentReference
---.MeasurementSiteRecord.measurementEquipmentTypeUsed | ---.MeasurementSite.measurementEquipmentTypeUsed
---.MeasurementSiteRecord.measurementSiteName | ---.MeasurementSite.measurementSiteName
---.MeasurementSiteRecord.measurementSiteNumberOfLanes | ---.MeasurementSite.measurementSiteNumberOfLanes
---.MeasurementSiteRecord.measurementSide | ---.MeasurementSite.measurementSpecificCharacteristics.measurementSide | Element moved in version 3
---.---.measurementSpecificCharacteristics.index | ---.---.measurementSpecificCharacteristics.index
---.---.measurementSpecificCharacteristics.accuracy | ---.---.measurementSpecificCharacteristics.accuracy
---.---.measurementSpecificCharacteristics.period | ---.---.measurementSpecificCharacteristics.period
---.---.measurementSpecificCharacteristics.smoothingFactor | ---.---.measurementSpecificCharacteristics.smoothingFactor
---.---.measurementSpecificCharacteristics.specificLane | ---.---.measurementSpecificCharacteristics.specificLane.laneNumber | Using enumeration mapping
---.---.measurementSpecificCharacteristics.specificLane | ---.---.measurementSpecificCharacteristics.specificLane.laneUsage | Using enumeration mapping
---.---.measurementSpecificCharacteristics.specificMeasurementValueType | ---.---.measurementSpecificCharacteristics.specificMeasurementValueType
---.---.---.specificVehicleCharacteristics.vehicleType | ---.---.---.specificVehicleCharacteristics.vehicleType
---.---.---.---.lengthCharacteristic.comparisonOperator | ---.---.---.---.lengthCharacteristic.comparisonOperator
---.---.---.---.lengthCharacteristic.vehicleLength | ---.---.---.---.lengthCharacteristic.vehicleLength
---.---.measurementSiteLocation xsi:type="ItineraryByIndexedLocations" | ---.---.measurementSiteLocation xsi:type="ItineraryByIndexedLocations" | Using this mapping
---.---.measurementSiteLocation xsi:type="Point" | ---.---.measurementSiteLocation xsi:type="PointLocation" | Using this mapping
### MeasuredDataPublication maps to MeasuredDataPublication
Source
Target
payloadPublication xsi:type="MeasuredDataPublication" (V2.3) | payload xsi:type="roa:MeasuredDataPublication" (V3) | Remark
lang | lang
modelBaseVersion | Fill this required element for version 3 with the value 3
publicationTime | publicationTime
publicationCreator | publicationCreator
publicationCreator.country | publicationCreator.country
publicationCreator.nationalIdentifier | publicationCreator.nationalIdentifier
measurementSiteTableReference.id | measurementSiteTableReference.id
measurementSiteTableReference.version | measurementSiteTableReference.version
The targetClass in version 3 must be provided with the correct namespace prefix. If "roa" is the prefix of the MeasuredDataPublication namespace from V3, "roa:" must be inserted before the value of the targetClass as it is included in V2.3.
measurementSiteTableReference.targetClass | measurementSiteTableReference.targetClass | Example: roa:MeasurementSiteTable
headerInformation | headerInformation
headerInformation.confidentiality | headerInformation.confidentiality
headerInformation.informationStatus | headerInformation.informationStatus
SiteMeasurements | SiteMeasurements
---.measurementSiteReference.id | ---.measurementSiteReference.id
---.measurementSiteReference.version | ---.measurementSiteReference.version
The targetClass in version 3 must be provided with the correct namespace prefix. If "roa" is the prefix of the MeasuredDataPublication namespace from V3, "roa:" must be inserted before the value of the targetClass as it is included in V2.3. In this case, the version 2.3 suffix "-Record" must also be removed
---.measurementSiteReference.targetClass | ---.measurementSiteReference.targetClass | Example: roa:MeasurementSite
---.measurementTimeDefault | measurementTimeDefault.timeValue
#### measuredValue maps to physicalQuantity
Source
Target
measuredValue (V2.3) | physicalQuantity (V3)
measuredValue.index | physicalQuantity.index
measuredValue.measuredValue | physicalQuantity xsi:type="SinglePhysicalQuantity"
---.---.measurementEquipmentTypeUsed | ---.measurementEquipmentTypeUsed
#### basicData maps to basicData
#### basicData type TrafficFlow maps to basicData type TrafficFlow
Source
Target
basicData xsi:type ="TrafficFlow" (V2.3) | basicData xsi:type="TrafficFlow" (V3) | Remark
measurementOrCalculationPeriod | TBD | Elaborate mapping (later) if necessary
measurementOrCalculationTime | TBD | Elaborate mapping (later) if necessary
vehicleFlow | vehicleFlow
vehicleFlow.accuracy | vehicleFlow.accuracy
vehicleFlow.computationalMethod | vehicleFlow.computationalMethod
vehicleFlow.numberOfIncompleteInputs | vehicleFlow.numberOfIncompleteInputs
vehicleFlow.numberOfInputValuesUsed | vehicleFlow.numberOfInputValuesUsed
vehicleFlow.smoothingFactor | vehicleFlow.smoothingFactor
vehicleFlow.standardDeviation | vehicleFlow.standardDeviation
vehicleFlow.supplierCalculatedDataQuality | vehicleFlow.supplierCalculatedDataQuality
vehicleFlow.dataError | vehicleFlow.dataError
vehicleFlow.reasonForDataError | vehicleFlow.reasonForDataError
vehicleFlow.vehicleFlowRate | vehicleFlow.vehicleFlowRate
#### basicData type TrafficSpeed maps to basicData type TrafficSpeed
Source
Target
basicData xsi:type ="TrafficSpeed" (V2.3) | basicData xsi:type="TrafficSpeed" (V3) | Remark
measurementOrCalculationPeriod | TBD | Elaborate mapping (later) if necessary
measurementOrCalculationTime | TBD | Elaborate mapping (later) if necessary
averageVehicleSpeed | averageVehicleSpeed
averageVehicleSpeed.accuracy | averageVehicleSpeed.accuracy
averageVehicleSpeed.computationalMethod | averageVehicleSpeed.computationalMethod
averageVehicleSpeed.numberOfIncompleteInputs | averageVehicleSpeed.numberOfIncompleteInputs
averageVehicleSpeed.numberOfInputValuesUsed | averageVehicleSpeed.numberOfInputValuesUsed
averageVehicleSpeed.smoothingFactor | averageVehicleSpeed.smoothingFactor
averageVehicleSpeed.standardDeviation | averageVehicleSpeed.standardDeviation
averageVehicleSpeed.supplierCalculatedDataQuality | averageVehicleSpeed.supplierCalculatedDataQuality
averageVehicleSpeed.dataError | averageVehicleSpeed.dataError
averageVehicleSpeed.reasonForDataError | averageVehicleSpeed.reasonForDataError
averageVehicleSpeed.speed | averageVehicleSpeed.speed
#### basicData type TravelTimeData maps to basicData type TravelTimeData
Source
Target
basicData xsi:type ="TravelTimeData" (V2.3) | basicData xsi:type="TravelTimeData" (V3) | Remark
measurementOrCalculationPeriod | TBD | Elaborate mapping (later) if necessary
measurementOrCalculationTime | TBD | Elaborate mapping (later) if necessary
travelTimeType | travelTimeType
travelTime | travelTime
travelTime.accuracy | travelTime.accuracy
travelTime.computationalMethod | travelTime.computationalMethod
travelTime.numberOfIncompleteInputs | travelTime.numberOfIncompleteInputs
travelTime.numberOfInputValuesUsed | travelTime.numberOfInputValuesUsed
travelTime.smoothingFactor | travelTime.smoothingFactor
travelTime.standardDeviation | travelTime.standardDeviation
travelTime.supplierCalculatedDataQuality | travelTime.supplierCalculatedDataQuality
travelTime.dataError | travelTime.dataError
travelTime.reasonForDataError | travelTime.reasonForDataError
travelTime.duration | travelTime.duration
### VmsTablePublication maps to VmsTablePublication
A mapping for a limited number of elements of the DATEX II European Model is given below.
Source
Target
payloadPublication xsi:type="VmsTablePublication" (V2.3) | payload xsi:type="vms:VmsTablePublication" (V3) | Remark
lang | lang
modelBaseVersion | Fill this required element for version 3 with the value 3
publicationTime | publicationTime
publicationCreator | publicationCreator
publicationCreator.country | publicationCreator.country
publicationCreator.nationalIdentifier | publicationCreator.nationalIdentifier
headerInformation.confidentiality | headerInformation.confidentiality
headerInformation.informationStatus | headerInformation.informationStatus
vmsUnitTable | vmsControllerTable
vmsUnitTable.id | vmsControllerTable.id
vmsUnitTable.version | vmsControllerTable.version
---.VmsUnitRecord | ---.vmsController
---.VmsUnitRecord.id | ---.vmsController.id
---.VmsUnitRecord.version | ---.vmsController.version
---.VmsUnitRecord.numberOfVms | ---.vmsController.numberOfVms
---.VmsUnitRecord.vmsRecord | ---.vmsController.vms
---.---.vmsRecord.vmsIndex | ---.---.vms.vmsIndex
---.---.---.vmsRecord | ---.---.---.vms
---.---.---.vmsRecord.vmsDescription | ---.---.---.vms.description
---.---.---.vmsRecord.vmsPhysicalMounting | ---.---.---.vms.physicalSupport
---.---.---.vmsRecord.vmsType | ---.---.---.vms.vmsType
---.---.---.vms.vmsConfiguration | New in version 3
---.---.---.---.---.DisplayArea | New in version 3
---.---.---.---.---.DisplayArea.displayAreaIndex | New in version 3, fill this required element with the value 1
---.---.---.vmsRecord.vmsTextDisplayCharacteristics | ---.---.---.---.---.DisplayArea xsi:type="TextDisplayArea" | Unlike version 2.3, version 3 works with specializations.
---.---.---.---.textDisplayHeight | ---.---.---.---.---.---.displayGeometry.displayHeight
---.---.---.---.textDisplayWidth | ---.---.---.---.---.---.displayGeometry.displayWidth
---.---.---.---.maxNumberOfCharacters | ---.---.---.---.---.---.maxNumberOfCharacters
---.---.---.---.maxNumberOfRows | ---.---.---.---.---.---.maxNumberOfRows
---.---.---.vmsRecord.vmsLocation xsi:type="Point" | ---.---.---.vmsRecord.vmsLocation xsi:type="PointLocation" | Using this mapping
### VmsPublication maps to VmsPublication
A mapping for a limited number of elements of the DATEX II European Model is given below.
Source
Target
payloadPublication xsi:type="VmsPublication" (V2.3) | payload xsi:type="vms:VmsPublication" (V3) | Remark
lang | lang
modelBaseVersion | Fill this required element for version 3 with the value 3
publicationTime | publicationTime
publicationCreator | publicationCreator
publicationCreator.country | publicationCreator.country
publicationCreator.nationalIdentifier | publicationCreator.nationalIdentifier
headerInformation.confidentiality | headerInformation.confidentiality
headerInformation.informationStatus | headerInformation.informationStatus
vmsUnit | VmsControllerStatus
---.vmsUnitTableReference | ---.vmsControllerTableReference
---.vmsUnitTableReference.id | ---.vmsControllerTableReference.id
---.vmsUnitTableReference.version | ---.vmsControllerTableReference.version
---.vmsUnitTableReference.targetClass | ---.vmsControllerTableReference.targetClass | In version 3 fill this element with "vms:VmsControllerTable"
---.vmsUnitReference | ---.vmsControllerReference
---.vmsUnitReference.id | ---.vmsControllerReference.id
---.vmsUnitReference.version | ---.vmsControllerReference.version
---.vmsUnitReference.targetClass | ---.vmsControllerReference.targetClass | In version 3 fill this element with "vms:VmsController"
---.vms | ---.vmsStatus
---.vms.vmsIndex | ---.vmsStatus.vmsIndex
---.---.vms | ---.---.vmsStatus
If vmsWorking=true, then workingStatus=working
---.---.---.vmsWorking | ---.---.---.workingStatus | If vmsWorking=false, then workingStatus=notWorking
---.---.---.vmsMessage | ---.---.---.vmsMessage
---.---.---.vmsMessage.messageIndex | ---.---.---.vmsMessage.messageIndex
---.---.---.---.timeLastSet | ---.---.---.---.timeLastSet
---.---.---.---.---.DisplayAreaSettings | New (intermediate) layer in xml tree in version 3
---.---.---.---.---.DisplayAreaSettings.displayAreaIndex | New in version 3, fill this element with the value 1
---.---.---.---.---.DisplayAreaSettings xsi:type="MultiPageDisplay"
---.---.---.---.textPage | ---.---.---.---.---.---.DisplayAreaSettings
---.---.---.---.textPage.pageNumber | ---.---.---.---.---.---.DisplayAreaSettings.pageNumber
---.---.---.---.---.vmsText | ---.---.---.---.---.---.DisplayAreaSettings xsi:type="TextDisplay"
---.---.---.---.---.---.vmsTextLine | ---.---.---.---.---.---.---.textLine
---.---.---.---.---.---.vmsTextLine.lineIndex | ---.---.---.---.---.---.---.textLine.lineIndex
---.---.---.---.---.---.---.vmsTextLine | ---.---.---.---.---.---.---.---.textLine
---.---.---.---.---.---.---.---.vmsTextLine | ---.---.---.---.---.---.---.---.---.textLine
Go back to the previous page
