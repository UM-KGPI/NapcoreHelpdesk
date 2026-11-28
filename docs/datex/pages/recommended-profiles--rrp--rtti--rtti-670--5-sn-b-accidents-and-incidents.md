url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-670/5-sn-b-accidents-and-incidents/
title: Accidents and incidents

## Accidents and incidents
### DATEX II packages addressed by the RRP Other types of data on the state of the network
This RRP tailors the following DATEX II model packages:
- Common – commonly used DATEX II data elements used by the tailored packages below (CEN/EN 16157-7:2018)
- LocationReferencing – the location references, tailored for information on accidents and incidents (CEN/EN 161578-2: 2019)
- Situation – the DATEX II general traffic event packages tailored for for information on accidents and incidents (CEN/EN 16157-3:2018)
The Situation package is used for publishing event-type information for Accidents and incidents as a SituationPublication. Instances of TrafficElement -> Accidents -> ConstructionWorks contain accidentType and if relevant CollissionType. It may contain the involved vehicles, see Figure 1.
Figure 1a Accidents
The available accidenttypes in this RRP are:
- accident
- accidentInvolvingHazardousMaterials
- accidentInvolvingHeavyLorries
- accidentInvolvingMassTransitVehicle
- accidentInvolvingPublicTransport
- accidentInvolvingRadioactiveMaterial
- accidentInvolvingTrain
- collision
- multipleVehicleAccident
- other
- secondaryAccident
- seriousInjuryOrFatalAccident
The available collisiontypes in this RRP are:
- collisionWithAnimal
- collisionWithObstacle
- collisionWithPerson
- headOnCollision
- headOnOrSideCollision
- multipleVehicleCollision
- rearCollision
- sideCollision
Instances of TrafficElement -> Obstruction contains the following incidents as obstructions: animalPrecense, EnvironmentalObstructions, InfrastructureDamageObstructions, VehicleObstructions and GeneralObstructions see Figure 2.
Figure 1b obstructions
The available animal precense types are:
- animalsOnTheRoad
- herdOfAnimalsOnTheRoad
- largeAnimalsOnTheRoad
- smallAnimalsOnTheRoad
The available Environmental obstructiontypes are:
- avalanches
- earthquakeDamage
- fallenTrees
- fallingIce
- fallingLightIceOrSnow
- flashFloods
- flooding
- forestFire
- grassFire
- landslips
- mudSlide
- other
- rockfalls
- seriousFire
- sewerOverflow
- smokeOrFumes
- stormDamage
- subsidence
The available Infrastructure Damage Obstructiontypes are:
- burstPipe
- burstWaterMain
- collapsedSewer
- damagedBridge
- damagedCrashBarrier
- damagedFlyover
- damagedGallery
- damagedGantry
- damagedRoadSurface
- damagedTunnel
- damagedViaduct
- fallenPowerCables
- gasLeak
- other
- weakBridge
The available Obstructiontypes are:
- airCrash
- childrenOnRoadway
- clearanceWork
- craneOperating
- cyclistsOnRoadway
- debris
- explosion
- explosionHazard
- hazardsOnTheRoad
- incident
- industrialAccident
- objectOnTheRoad
- objectsFallingFromMovingVehicle
- obstructionOnTheRoad
- other
- peopleOnRoadway
- railCrash
- rescueAndRecoveryWork
- severeFrostDamagedRoadway
- shedLoad
- snowAndIceDebris
- spillageOccurringFromMovingVehicle
- spillageOnTheRoad
- unprotectedAccidentArea
The available Vehicle Obstructiontypes are:
- abandonedVehicle
- abnormalLoad
- brokenDownVehicle
- convoy
- damagedVehicle
- dangerousSlowMovingVehicle
- emergencyVehicle
- highSpeedChase
- highSpeedEmergencyVehicle
- longLoad
- medicalEmergency
- militaryConvoy
- other
- overheightVehicle
- prohibitedVehicleOnTheRoad
- recklessDriver
- slowVehicle
- specialPermitTransport
- trackedVehicle
- unlitVehicleOnTheRoad
- vehicleCarryingHazardousMaterials
- vehicleInDifficulty
- vehicleOnFire
- vehicleOnWrongCarriageway
- vehicleStuck
- vehicleWithOverheightLoad
- vehicleWithOverwideLoad
- winterMaintetanceVehicleInTransfer
### LocationReference profile
This RRP does not specify the locationreferencing methods to use. The applied method for location referencing is the choice of the specific user implementing this profile.
This RRP does limit the use of SupplementaryPositionalDescription to identifying the affected lane(s), and the carriageway on which they are positioned. laneUsage and laneNumber shall be used jointly to characterise lanes that are affected.
Figure 2 supplementary positional description
### Validity profile
The validityStatus shall be used to distinct between planned and active roadworks, or the time validity profile is used to provide the planned timeschedule of the roadworks.
The time validity profile includes the overallPeriod and validPeriod concepts. In case of long-term closures or because of traffic management purposes, controlled accessibility the following concepts are available as well:
- recurringTimeperiodOfDay
- recurringDayWeekMonthPeriod
Figure 3 validity
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
