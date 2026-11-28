url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-670/4-sn-d-temporary-traffic-management-measures/
title: Temporary traffic management measures

## Temporary traffic management measures
### DATEX II packages addressed by the RRP The crucial types of data on the state of the network
This RRP tailors the following DATEX II model packages:
- Common – commonly used DATEX II data elements used by the tailored packages below (CEN/EN 16157-7:2018)
- LocationReferencing – the location references, tailored for Temporary Trafficmanagement Measures (CEN/EN 161578-2: 2019)
- Situation – the DATEX II general traffic event packages tailored for Temporary Trafficmanagement Measures (CEN/EN 16157-3:2018)
The Situation package is used for publishing event-type information for Temporary Trafficmanagement Measures as a SituationPublication. Note that this RRP is overlapping with other RRP's
Specialisations of OperatorAction -> NetworkManagement -> can be:
- ReroutingManagement
- GeneralNetworkManagement
- WinterDrivingManagement
- RoadOrCarriagewayOrLaneManagement
- SpeedManagement
see Figure 1.
Figure 1 NetworkManagement
The available ReroutingManagementTypes in this RRP are:
- doNotFollowDiversionSigns
- doNotUseEntry
- doNotUseExit
- doNotUseIntersectionOrJunction
- followDiversionSigns
- followLocalDiversion
- followSpecialMarkers
- useEntry
- useExit
- useIntersectionOrJunction
The available GeneralNetworkManagementTypes in this RRP are:
- bridgeSwingInOperation
- convoyService
- obstacleSignalling
- other
- rampMeteringInOperation
- temporaryTrafficLights
- tollGatesOpen
- trafficBeingManuallyDirected
- trafficHeld
- restrictedAreasAccessInOperation
- tollingInOperation
- tollingNotInOperation
The available WinterDrivingManagementTypes in this RRP are:
- doNotUseStudTyres
- other
- useSnowChains
- useSnowChainsOrTyres
- useSnowTyres
- winterEquipmentOnBoardRequired
The available RoadOrCarriagewayOrLaneManagementTypes in this RRP are:
- carPoolLaneInOperation
- carriagewayClosures
- clearALaneForEmergencyVehicles
- clearALaneForSnowploughsAndGrittingVehicles
- closedPermanentlyForTheWinter
- contraflow
- doNotUseSpecifiedLanesOrCarriageways
- hardShoulderRunningInOperation
- hardShoulderRunningNotInOperation
- heightRestrictionInOperation
- intermittentShortTermClosures
- keepToTheLeft
- keepToTheRight
- laneClosures
- lanesDeviated
- narrowLanes
- newRoadworksLayout
- other
- overnightClosures
- roadCleared
- roadClosed
- rollingRoadBlock
- rushHourLaneInOperation
- singleAlternateLineTraffic
- tidalFlowLaneInOperation
- turnAroundInOperation
- useOfSpecifiedLanesOrCarriagewaysAllowed
- useSpecifiedLanesOrCarriageways
- vehicleStorageInOperation
- weightRestrictionInOperation
The available SpeedManagementTypes in this RRP are:
- activeSpeedControlInOperation
- doNotSlowdownUnnecessarily
- observeSpeedLimit
- other
- policeSpeedChecksInOperation
- reduceYourSpeed
- speedRestrictionInOperation
### LocationReference profile
This RRP does not specify the locationreferencing methods to use. The applied method for location referencing is the choice of the specific user implementing this profile. In this RRP alternative routes in case of reroutingmanagement is supported. Make sure the required locationreferencing profiles to suppport Area's and points for destinations and at least one linear method if you want to make use of the alternative route.
This RRP does limit the use of SupplementaryPositionalDescription to identifying the affected lane(s), and the carriageway on which they are positioned. laneUsage and laneNumber shall be used jointly to characterise lanes that are have a non generic usage.
Figure 2 supplementary positional description
### Validity profile
The time validity profile includes the overallPeriod and validPeriod concepts. In case of long-term measures or because of scheduled traffic management actions, the following concepts are available as well:
- recurringTimeperiodOfDay
- recurringDayWeekMonthPeriod
### PayloadPublication and SituationPublication profile
The general ‘wrapper’ classes for conveying event information are the following classes:
- PayloadPublication: The generic base class for all DATEX II publications. The optional attributes of the class PayloadPublication have all been kept in the RRP, since they are very generic by nature may be useful
- SituationPublication: This is a container class and has no extra attributes
### Situation profile
Traffic Situations are in DATEX II modelled as a container class (Situation) that contains SituationRecords, the basic elements to describe an event of a certain nature. The following profile applies:
- Situation: The optional attributes and associated components of the class Situation have all been kept in the RRP, since they are very generic by nature;
- From the generic data concepts supported by any kind of SituationRecord, the following have been deselected since they are not strictly required to provide the information in this data-category:
- cause
- informationManagerOverride
- confidentialityOverride
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
