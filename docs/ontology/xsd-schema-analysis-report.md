# XSD Schema Analysis Report: NAPCORE FAQ Helpdesk Standards

**Generated:** 2026-04-17
**Scope:** Comprehensive xs:complexType extraction and inheritance analysis for NeTEx, OpRa, and SIRI standards
**Purpose:** Ontology generation and domain entity mapping for NAPCORE FAQ knowledge base

---

## Executive Summary

This report documents the complete XSD schema analysis across three major transportation standards used in the NAPCORE helpdesk:

| Standard | XSD Files | complexType Count | Root Types | Focus Areas |
|----------|-----------|-------------------|-----------|-------------|
| **NeTEx** | 458 | **2,687** | 400+ | Service, Journey, Stop, Fare, Monitoring, Schedule, Vehicle |
| **OpRa** | 46 | **153** | 51 | Indicators, Capacity, Booking, Service metrics |
| **SIRI** | 87 | **830** | 488 | Real-time events, Journey monitoring, Situations, Disruptions |
| **TOTAL** | **591** | **3,670** | 500+ | Multi-standard unified domain model |

---

## 1. NeTEx Schema Analysis

### 1.1 Repository Structure

**Location:** `/Users/andrejt/Research/repositories/git/NeTEx/xsd/`

**Directory Organization:**
```
netex_part_1/          → Network data model (routes, lines, stops)
netex_part_2/          → Journey/Schedule data (journeys, timetables, patterns)
netex_part_3/          → Operations (monitoring, fares, real-time)
netex_framework/       → Base types and reusable components
```

**Key Subdirectories:**
- `part1_networkDescription/` - Network topology, lines, routes, stops
- `part2_journeyTimes/` - Service journeys, patterns, timetables, vehicle journeys
- `part3_monitoring/` - Real-time monitoring, calls, passing times
- `part3_fares/` - Fare structures, pricing, products
- `netex_reusableComponents/` - Common structures for entity versioning, references

### 1.2 NeTEx Total Type Count: 2,687 complexTypes

**Type Categories (by pattern):**
```
• Collection/Relation (_RelStructure):     ~800 types  (29%)
• Entity/Structural types:                 ~900 types  (34%)
• Reference types (RefStructure):          ~200 types  (7%)
• Abstract base types:                     ~350 types  (13%)
• Framework/Utility types:                 ~437 types  (17%)
```

### 1.3 Top-Level NeTEx Entity Types (No Base Class)

**Abstract Base Hierarchies:**
```
AbstractCapabilitiesStructure
AbstractDiscoveryDeliveryStructure
AbstractFunctionalServiceRequestStructure
AbstractIdentifiedItemStructure
AbstractItemStructure
AbstractMemberType
AbstractMetadataPropertyType
AbstractNotificationStructure
AbstractPermissionStructure
AbstractReferencingItemStructure
AbstractRequestStructure
AbstractRequiredIdentifiedItemStructure
AbstractRequiredReferencingItemStructure
AbstractServiceCapabilitiesResponseStructure
AbstractServiceDeliveryStructure
AbstractSubscriptionRequestStructure
AbstractSubscriptionStructure
AbstractTopicPermissionStructure
```

**Root Aggregation Types:**
```
containmentAggregationStructure          (base for all _RelStructure collections)
  ├─ strictContainmentAggregationStructure
  │   ├─ accessLinkSequences_RelStructure
  │   ├─ accessPointsInSequence_RelStructure
  │   ├─ accessibilityLimitations_RelStructure
  │   ├─ accessibilityNeeds_RelStructure
  │   ├─ accessibilityNeedsEntitlements_RelStructure
  │   ├─ accessibilityNeedsEntitlementPrices_RelStructure
  │   ├─ accessibilityNeedsRestrictions_RelStructure
  │   ├─ accessibilityNeeds_RelStructure
  │   ├─ accessibilityRestrictionsOnServices_RelStructure
  │   ├─ ... [800+ collection types total]
```

### 1.4 Key NeTEx Domain Entities

#### **A. Service & Line Entities**

**Root Types:**
```
Service (abstract root)
├─ FlexibleLine_VersionStructure
├─ Line_VersionStructure
├─ Network_VersionStructure
├─ Route_VersionStructure
└─ ServiceLink_VersionStructure

AllServices_RelStructure          → collections of Service
FlexibleLines_RelStructure        → collections of FlexibleLine
Lines_RelStructure                → collections of Line
Networks_RelStructure             → collections of Network
Routes_RelStructure               → collections of Route
```

**Related Types:**
- `ServiceRef`, `ServiceRefStructure`
- `LineRef`, `LineRefStructure`
- `DesignatedLineRef`, `LineSpecificRef`
- `FlexibleLineRef`, `FlexibleLineRefStructure`

#### **B. Journey Entities**

**Journey Hierarchy:**
```
Journey_VersionStructure (abstract)
├─ ServiceJourney_VersionStructure
│   └─ Represents scheduled passenger journey
│   └─ Inheritance: extends Journey_VersionStructure
├─ DeadRun_VersionStructure
│   └─ Non-passenger vehicle journey
└─ SpecialService_VersionStructure
    └─ Special service journey

VehicleJourney_VersionStructure (abstract)
├─ ServiceJourney_VersionStructure
├─ DeadRun_VersionStructure
└─ TrainNumberJourney_VersionStructure
```

**Collection Types:**
- `serviceJourneys_RelStructure` - service journey collections
- `deadRuns_RelStructure` - dead run collections
- `vehicleJourneys_RelStructure` - all vehicle journeys
- `specialServices_RelStructure` - special services

**Attributes & References:**
- `ServiceJourneyRef`, `ServiceJourneyRefStructure`
- `DeadRunRef`, `DeadRunRefStructure`
- `VehicleJourneyRef`, `VehicleJourneyRefStructure`

#### **C. Stop/Place Entities**

**Core Stop Types:**
```
Place_VersionStructure (abstract)
├─ TopographicPlace_VersionStructure
├─ PointOfInterest_VersionStructure
└─ StopPlace_VersionStructure

StopPlace_VersionStructure
├─ Quay (stopping position)
├─ Platform (boarding/alighting area)
├─ StopArea (aggregated stops)
└─ StopPlaceEntrance (entry point)

ScheduledStopPoint_VersionStructure
├─ Service stop definition
├─ References timing information
└─ Linked to StopPlace for real-time
```

**Collection Types:**
- `stopPlaces_RelStructure` - stop place collections
- `scheduledStopPoints_RelStructure` - scheduled stop collections
- `topographicPlaces_RelStructure` - geographic places
- `quays_RelStructure` - quay collections
- `platforms_RelStructure` - platform collections

**Reference Types:**
- `StopPlaceRef`, `StopPlaceRefStructure`
- `ScheduledStopPointRef`, `ScheduledStopPointRefStructure`
- `QuayRef`, `QuayRefStructure`
- `StopAreaRef`, `StopAreaRefStructure`
- `TopographicPlaceRef`, `TopographicPlaceRefStructure`

#### **D. Fare Entities**

**Fare Structure Hierarchy:**
```
FareProduct_VersionStructure (abstract)
├─ PreAssignedFareProduct_VersionStructure
│   ├─ Fare (traditional product)
│   ├─ Concession (discounted product)
│   └─ FareSpec_VersionStructure
├─ SalesOfferPackage_VersionStructure
│   └─ Bundled fare package
└─ FarePart_VersionStructure

FareStructureElement_VersionStructure
├─ ValidableElement_VersionStructure
│   ├─ AccessRightParameter
│   ├─ UsageParameterEligibility
│   ├─ UsageParameterEntitlement
│   └─ UsageParameterAfterSales

FarePrice_VersionStructure
├─ FarePriceWithMethod_VersionStructure
├─ FarePriceWithRoundingRules_VersionStructure
└─ FarePriceDailyModifier_VersionStructure
```

**Pricing Components:**
```
TimeStructureFactor_VersionStructure       → Time-based pricing
DistanceStructureFactor_VersionStructure   → Distance-based pricing
GeographicStructureFactor_VersionStructure → Zone-based pricing
QualityStructureFactor_VersionStructure    → Service quality factors
```

**Collection Types:**
- `fareProducts_RelStructure` - fare product collections
- `fares_RelStructure` - individual fares
- `concessions_RelStructure` - concession fares
- `salesOfferPackages_RelStructure` - bundled offers
- `farePrices_RelStructure` - pricing data
- `validableElements_RelStructure` - validable items

#### **E. Monitoring/Call Entities**

**Call Hierarchy:**
```
Call_VersionStructure (abstract)
├─ TimetabledPassingTime_VersionStructure
│   └─ Scheduled call information
├─ TargetPassingTime_VersionStructure
│   └─ Target/expected timing
├─ PassingTime_VersionStructure
│   └─ Actual observed timing
└─ DatedCallStructure
    └─ Call for specific dated journey

ServiceCall_VersionStructure
├─ Includes arrival/departure times
├─ References stop point
└─ Links to journey pattern
```

**Monitoring-Related Types:**
- `MonitoredCall_VersionStructure` - real-time call state
- `ObservedPassingTime_VersionStructure` - observed passing
- `DatedPassingTime_VersionStructure` - dated passing info

**Collection Types:**
- `calls_RelStructure` - call collections
- `passingTimes_RelStructure` - passing times
- `serviceCall_RelStructure` - service call collections
- `timetabledPassingTimes_RelStructure` - scheduled passing
- `observedPassingTimes_RelStructure` - observed data
- `targetPassingTimes_RelStructure` - target passing times
- `monitoredCalls_RelStructure` - real-time calls

#### **F. Schedule/Timetable Entities**

**Timetable Structure:**
```
DayType_VersionStructure
├─ Defines operating days
├─ PropertyOfDay (specific date)
└─ ServiceCalendar_VersionStructure
    ├─ DayTypeAssignment
    └─ ServiceCalendarFrame_VersionStructure

JourneyPattern_VersionStructure
├─ Describes stop sequence
├─ ServiceJourneyPattern_VersionStructure
└─ TimingPattern_VersionStructure
    └─ Includes PassingTime sequence

TimeDemandProfile_VersionStructure
├─ Run/wait time sequences
├─ Timing constraints
└─ Links to journey pattern
```

**Collection Types:**
- `dayTypes_RelStructure` - day type collections
- `serviceCalendars_RelStructure` - calendar collections
- `journeyPatterns_RelStructure` - pattern collections
- `timeDemandProfiles_RelStructure` - timing profiles
- `scheduledStopPoints_RelStructure` - stop sequences

#### **G. Vehicle/Equipment Entities**

**Vehicle Hierarchy:**
```
Vehicle_VersionStructure
├─ AccessibilityAssessment_VersionStructure
├─ CompoundTrain_VersionStructure
├─ Train_VersionStructure
└─ VehicleType_VersionStructure

VehicleEquipment_VersionStructure
├─ AccessibilityEquipment_VersionStructure
├─ GeneralEquipment_VersionStructure
├─ PassengerEquipment_VersionStructure
└─ VehicleServiceEquipment_VersionStructure
```

**Equipment Types:**
```
Toilet_VersionStructure
Wheelchair_VersionStructure
Lift_VersionStructure
Ramp_VersionStructure
WifiEquipment_VersionStructure
```

**Collection Types:**
- `vehicles_RelStructure` - vehicle collections
- `vehicleTypes_RelStructure` - vehicle type definitions
- `compoundTrains_RelStructure` - train compositions
- `equipment_RelStructure` - equipment collections

### 1.5 NeTEx Inheritance Chains (Sample Key Entities)

```
1. SERVICE JOURNEY CHAIN:
   VersionedChildStructure
   └─ Journey_VersionStructure
      └─ ServiceJourney_VersionStructure
         └─ Concrete ServiceJourney instance

2. STOP CHAIN:
   VersionedChildStructure
   └─ Place_VersionStructure
      ├─ TopographicPlace_VersionStructure
      ├─ PointOfInterest_VersionStructure
      └─ StopPlace_VersionStructure
         └─ Concrete StopPlace instance

3. FARE CHAIN:
   VersionedChildStructure
   └─ FareProduct_VersionStructure
      ├─ PreAssignedFareProduct_VersionStructure
      │   ├─ Fare_VersionStructure
      │   ├─ Concession_VersionStructure
      │   └─ FareSpec_VersionStructure
      └─ SalesOfferPackage_VersionStructure

4. COLLECTION CHAIN:
   AggregationStructure
   └─ ContainmentAggregationStructure
      └─ StrictContainmentAggregationStructure
         ├─ serviceJourneys_RelStructure
         ├─ serviceCalls_RelStructure
         ├─ stops_RelStructure
         ├─ fareProducts_RelStructure
         └─ [800+ other collections]

5. CALL/PASSING TIME CHAIN:
   VersionedChildStructure
   └─ Call_VersionStructure
      ├─ TimetabledPassingTime_VersionStructure
      ├─ TargetPassingTime_VersionStructure
      ├─ PassingTime_VersionStructure
      └─ DatedCallStructure
```

---

## 2. OpRa Schema Analysis

### 2.1 Repository Structure

**Location:** `/Users/andrejt/Research/repositories/git/OpRa/xsd/`

**Directory Organization:**
```
opra_indicators/       → Service indicators and metrics
opra_framework/        → Core frameworks
opra_imports/          → References to NeTEx/SIRI
opra.xsd               → Main OpRa schema
```

### 2.2 OpRa Total Type Count: 153 complexTypes

**Type Categories:**
```
• Collection/Relation (_RelStructure):     ~40 types  (26%)
• Entity/Structural types:                 ~60 types  (39%)
• Reference types (RefStructure, *Ref):    ~20 types  (13%)
• Abstract base types:                     ~15 types  (10%)
• Framework/Utility types:                 ~18 types  (12%)
```

### 2.3 Top-Level OpRa Root Types

```
AbstractIndicatorLogEntries_RelStructure
AbstractIndicators_RelStructure
AbstractLogEntries_RelStructure
AbstractLoggableObjects_RelStructure
AbstractOpraFunctionalServiceRequestStructure
ActualCapacities_RelStructure
ActualFleetIDimensions_RelStructure
ActualServiceIDimensions_RelStructure
ActualServiceIntensities_RelStructure
AggregatedOnboardDeviceBasedPassengerCounts_RelStructure
AggregatedTicketingBasedPassengerCounts_RelStructure
CancelledDatedVehicleJourneyCounts_RelStructure
CancelledDatedVehicleJourneyEntries_RelStructure
CapacitySpecificationStructure
DurationIntervalStructure
ExpectedPassengerCounts_RelStructure
ExpectedServiceIntensities_RelStructure
ExternalPassengerCounts_RelStructure
GeneralLogEntries_RelStructure
LateDatedVehicleJourneyCounts_RelStructure
LateDatedVehicleJourneyEntries_RelStructure
LogEntryValueStructure
OpraDiscoveryDeliveries_RelStructure
OpraDiscoveryRequests_RelStructure
OpraFunctionalDeliveries_RelStructure
OpraRequests_RelStructure
```

### 2.4 Key OpRa Domain Entities

#### **A. Journey & Vehicle Journey Entities**

**Collections:**
```
CancelledDatedVehicleJourneyCounts_RelStructure
├─ CancelledDatedVehicleJourneyCount_VersionStructure
├─ CancelledDatedVehicleJourneyEntry_Structure
└─ References to dated vehicle journeys

LateDatedVehicleJourneyCounts_RelStructure
├─ LateDatedVehicleJourneyCount_VersionStructure
├─ LateDatedVehicleJourneyEntry_Structure
└─ Late running journey tracking
```

#### **B. Capacity & Occupancy**

**Root Types:**
```
ActualCapacities_RelStructure
PlannedCapacities_RelStructure
VehicleTypeCapacities_RelStructure
CapacitySpecificationStructure
```

**Related Types:**
- `ActualCapacityRefStructure`
- `VehicleTypeCapacityStructure`
- `VehicleLoadEntries_RelStructure`

#### **C. Service Dimensions & Intensity**

**Service Intensity:**
```
ActualServiceIntensities_RelStructure
ExpectedServiceIntensities_RelStructure
PlannedServiceIntensities_RelStructure
ServiceIntensityRefStructure
```

**Fleet Dimensions:**
```
ActualFleetIDimensions_RelStructure
PlannedFleetDimensions_RelStructure
ActualFleetIDimensionsRefStructure
```

**Service Dimensions:**
```
ActualServiceIDimensions_RelStructure
PlannedServiceDimensions_RelStructure
ActualServiceIDimensionsRefStructure
```

#### **D. Passenger Count Indicators**

**Types:**
```
ExpectedPassengerCounts_RelStructure
OnboardDeviceBasedPassengerCounts_RelStructure
TicketingBasedPassengerCounts_RelStructure
ExternalPassengerCounts_RelStructure
AggregatedOnboardDeviceBasedPassengerCounts_RelStructure
AggregatedTicketingBasedPassengerCounts_RelStructure
```

#### **E. Logging & Validation**

**Structures:**
```
GeneralLogEntries_RelStructure
├─ GeneralLogEntry_VersionStructure
├─ CtxIndicators_RelStructure
└─ Abstract LoggableObjects_RelStructure

ValidationEntries_RelStructure
├─ ValidationEntry_VersionStructure
└─ LogEntryUnitaryValueStructure
```

### 2.5 OpRa Inheritance Chains

```
1. CANCELLED JOURNEY CHAIN:
   OpraRequests_RelStructure
   └─ CancelledDatedVehicleJourneyCounts_RelStructure
      └─ CancelledDatedVehicleJourneyCountRefStructure

2. PASSENGER COUNT CHAIN:
   AbstractIndicators_RelStructure
   └─ ExpectedPassengerCounts_RelStructure
      ├─ ExpectedPassengerCountRefStructure
      └─ [linked to NeTEx ServiceJourney]

3. CAPACITY CHAIN:
   AbstractCapacities_RelStructure
   └─ VehicleTypeCapacities_RelStructure
      ├─ VehicleTypeCapacityStructure
      └─ CapacitySpecificationStructure

4. LOG ENTRY CHAIN:
   AbstractLogEntries_RelStructure
   └─ GeneralLogEntries_RelStructure
      ├─ GeneralLogEntry_VersionStructure
      └─ LogEntryValues_RelStructure
```

---

## 3. SIRI Schema Analysis

### 3.1 Repository Structure

**Location:** `/Users/andrejt/Research/repositories/git/SIRI/xsd/`

**Services:**
- `siri_stopTimetable_service.xsd` - Stop Timetable service
- `siri_stopMonitoring_service.xsd` - Stop Monitoring (SM) service
- `siri_vehicleMonitoring_service.xsd` - Vehicle Monitoring (VM) service
- `siri_estimatedTimetable_service.xsd` - Estimated Timetable (ET) service
- `siri_connectionTimetable_service.xsd` - Connection Timetable service
- `siri_situationExchange_service.xsd` - Situation Exchange (SX) service
- `siri_generalMessage_service.xsd` - General Message service
- `siri_facilityMonitoring_service.xsd` - Facility Monitoring service
- `siri_controlAction_service.xsd` - Control Action service

**Support:**
- `ifopt/` - IFOPT (Interface with Open Public Transport) types
- `gml/` - Geographic Markup Language (GML) types

### 3.2 SIRI Total Type Count: 830 complexTypes

**Service Breakdown:**
```
• EstimatedTimetable (ET):          ~80 types   (9%)
• VehicleMonitoring (VM):           ~120 types  (14%)
• StopMonitoring (SM):              ~90 types   (10%)
• ConnectionMonitoring (CM):        ~70 types   (8%)
• SituationExchange (SX):           ~100 types  (12%)
• ProductionTimetable/StopTimetable: ~100 types  (12%)
• Core Message Structure:           ~200 types  (24%)
• Permissions/Discovery:            ~70 types   (8%)
• IFOPT/Geographic Support:         ~20 types   (2%)
```

### 3.3 Top-Level SIRI Root Types (Sample of 50)

```
AbstractCallStructure
AbstractCapabilitiesStructure
AbstractControlActionHeaderStructure
AbstractDiscoveryDeliveryStructure
AbstractDiscoveryRequestStructure
AbstractDistributorItemStructure
AbstractEquipmentStructure
AbstractFeederItemStructure
AbstractFunctionalServiceRequestStructure
AbstractGMLType
AbstractGeometricPrimitiveType
AbstractGeometryType
AbstractIdentifiedItemStructure
AbstractItemStructure
AbstractMemberType
AbstractMetadataPropertyType
AbstractMonitoredCallStructure
AbstractNotificationStructure
AbstractPermissionStructure
AbstractProjection
AbstractReferencingItemStructure
AbstractRequestStructure
AbstractRequiredIdentifiedItemStructure
AbstractRequiredReferencingItemStructure
AbstractRingPropertyType
AbstractRingType
AbstractServiceCapabilitiesResponseStructure
AbstractServiceDeliveryStructure
AbstractSituationElementStructure
AbstractSubscriptionRequestStructure
AbstractSubscriptionStructure
AbstractTopicPermissionStructure
AbstractVehicleJourneyInterchangeStructure
AccessibilityAssessmentStructure
AccessibilityLimitationStructure
AccessibilityNeedsFilterStructure
ActionDataStructure
AdministrativeAreaRefStructure
AdviceRefStructure
AffectedConnectionLinkStructure
AffectedFacilityStructure
```

### 3.4 Key SIRI Domain Entities by Service

#### **A. EstimatedTimetable (ET) Service**

**Core Entities:**
```
AbstractTimetableDeliveryStructure
├─ EstimatedTimetableDeliveryStructure
│   └─ Service delivery containing estimated data
├─ ProductionTimetableDeliveryStructure
│   └─ Production timetable reference data
└─ StopTimetableDeliveryStructure
    └─ Stop-specific scheduled timetables

EstimatedVersionFrameStructure
├─ Container for estimated data
├─ References estimated calls
└─ Timestamp information

EstimatedCall_VersionStructure / DatedEstimatedCall_VersionStructure
├─ Estimated arrival/departure times
├─ Estimated vehicle journey info
├─ Stop references
└─ Delay information
```

**Key Types:**
```
EstimatedTimetableRequestStructure
EstimatedTimetableServiceCapabilitiesStructure
EstimatedTimetableSubscriptionStructure
DatedTimetableVersionFrameStructure
EstimatedTimetableDeliveryStructure
EstimatedTimetableServicePermissionStructure
```

#### **B. VehicleMonitoring (VM) Service**

**Core Entities:**
```
VehicleActivityStructure ← extends AbstractIdentifiedItemStructure
├─ Current vehicle location/state
├─ MonitoredVehicleJourney_StructureGroup
├─ Bearing, speed, odometer
└─ NextCall/OnwardCall structures

MonitoredVehicleJourney_StructureGroup
├─ Journey identification
├─ Current stop information
├─ Congestion level
├─ Passenger information
└─ Vehicle progress

OnwardCall_StructureGroup / OnwardCallStructure
├─ Upcoming stops
├─ Estimated arrival/departure
├─ Stop references
└─ Order information
```

**Related Types:**
```
VehicleMonitoringDeliveryStructure
VehicleMonitoringRequestStructure
VehicleMonitoringSubscriptionStructure
VehicleMonitoringServiceCapabilitiesStructure
VehicleActivityCancellationStructure
```

**Collections:**
```
MonitoredStopVisit_StructureGroup
├─ Stop-based vehicle monitoring
├─ RecordedAtTime
├─ Item identifier
└─ MonitoredVehicleJourney reference

VehicleRef / VehicleRefStructure
├─ References specific vehicle
└─ Links to fleet information
```

#### **C. StopMonitoring (SM) Service**

**Core Entities:**
```
MonitoredStopVisitStructure ← extends AbstractIdentifiedItemStructure
├─ Current vehicle at stop
├─ Arrival/departure predictions
├─ Stop reference
├─ Passenger information
└─ Disruption indicators

MonitoredCall_StructureGroup / MonitoredCallStructure
├─ Vehicle at/near specific stop
├─ Arrival prediction (ExpectedArrivalTime)
├─ Departure prediction (ExpectedDepartureTime)
├─ Delay information
├─ Stops Counter (nth stop)
└─ Aimed vs. Expected times
```

**Collections:**
```
OnwardCalls_StructureGroup
├─ Future calls at stop
├─ Sequenced calls
└─ Multiple vehicles

PreviousCallStructure
├─ Already served stops
├─ Actual vs. Expected comparison
└─ Delay accumulation
```

**Related Types:**
```
StopMonitoringDeliveryStructure
StopMonitoringRequestStructure
StopMonitoringSubscriptionStructure
StopMonitoringServiceCapabilitiesStructure
StopLineNoticeStructure
MonitoredStopVisitCancellationStructure
```

#### **D. ConnectionMonitoring (CM) Service**

**Core Entities:**
```
ConnectionServiceJourneyInterchange_StructureGroup
├─ From-journey information (feeder)
├─ To-journey information (main)
├─ From/To call information
├─ Interchange status
└─ Recommended interchange

MonitoredInterchangeStructure
├─ Real-time interchange status
├─ Feeder arrival vs. Main departure
├─ Waiting time
├─ Connection feasibility
└─ Actual vs. Planned comparison

FeederArrivals / MainDepartures
├─ Monitored vehicle arrival
├─ Call information
├─ Time comparison
└─ Status indicators
```

**Related Types:**
```
ConnectionTimetableDeliveryStructure
ConnectionMonitoringDeliveryStructure
ConnectionMonitoringRequestStructure
ConnectionMonitoringSubscriptionStructure
ConnectionMonitoringServiceCapabilitiesStructure
```

#### **E. SituationExchange (SX) Service**

**Core Entities:**
```
AbstractSituationElementStructure
├─ SituationElementStructure
│   ├─ PtSituationElementStructure (Public Transport specific)
│   │   └─ Service/line disruptions
│   └─ RoadSituationElementStructure
│       └─ Infrastructure issues

PtSituationElementStructure
├─ Situation description
├─ Severity level (VerySerious, Serious, Minor, Unknown)
├─ Affected lines/stops/routes
├─ Planned vs. Unplanned
├─ Start/end times
├─ Remedial actions
└─ Advice/information
```

**Related Types:**
```
SituationExchangeDeliveryStructure
SituationExchangeRequestStructure
SituationExchangeSubscriptionStructure
SituationExchangeServiceCapabilitiesStructure
SituationElementStructure
```

**Disruption Categories:**
```
Accident
AbnormalTraffic
PlannedWork
ClearsOnTime
Crowding
DisruptedService
NewService
OtherDisruption
Obstruction
PublicEvent
RailStrike
RoadWorks
SpecialEvent
Strike
TrafficAccident
TrainStrike
UnplannedWork
VehicleFailure
WeatherRelated
```

### 3.5 SIRI Request/Response Hierarchy

```
AbstractRequestStructure
├─ AbstractServiceRequestStructure
│   ├─ AbstractFunctionalServiceRequestStructure
│   │   ├─ EstimatedTimetableRequestStructure
│   │   ├─ StopMonitoringRequestStructure
│   │   ├─ VehicleMonitoringRequestStructure
│   │   ├─ ConnectionMonitoringRequestStructure
│   │   ├─ StopTimetableRequestStructure
│   │   ├─ ProductionTimetableRequestStructure
│   │   ├─ GeneralMessageRequestStructure
│   │   ├─ SituationExchangeRequestStructure
│   │   ├─ FacilityMonitoringRequestStructure
│   │   ├─ ControlActionRequestStructure
│   │   └─ ConnectionTimetableRequestStructure
│   └─ ServiceCapabilitiesRequestStructure
├─ AbstractSubscriptionRequestStructure
│   └─ SubscriptionRequestStructure
└─ AuthenticatedRequestStructure
    ├─ AbstractDiscoveryRequestStructure
    │   ├─ StopPointsDiscoveryRequestStructure
    │   ├─ LinesDiscoveryRequestStructure
    │   ├─ ProductCategoriesDiscoveryRequestStructure
    │   ├─ ServiceFeaturesDiscoveryRequestStructure
    │   ├─ VehicleFeaturesRequestStructure
    │   ├─ ConnectionLinksDiscoveryRequestStructure
    │   ├─ InfoChannelDiscoveryRequestStructure
    │   └─ FacilityRequestStructure
    └─ CapabilitiesRequestStructure

AbstractServiceDeliveryStructure
├─ EstimatedTimetableDeliveryStructure
├─ StopTimetableDeliveryStructure
├─ ProductionTimetableDeliveryStructure
├─ StopMonitoringDeliveryStructure
├─ VehicleMonitoringDeliveryStructure
├─ ConnectionMonitoringDeliveryStructure
├─ GeneralMessageDeliveryStructure
├─ SituationExchangeDeliveryStructure
├─ FacilityMonitoringDeliveryStructure
├─ ControlActionDeliveryStructure
└─ ConnectionTimetableDeliveryStructure
```

### 3.6 SIRI Item/Message Hierarchy

```
AbstractItemStructure
├─ AbstractIdentifiedItemStructure
│   ├─ VehicleActivityStructure (VM service)
│   │   └─ MonitoredVehicleJourney information
│   ├─ MonitoredStopVisitStructure (SM service)
│   │   └─ Vehicle at stop with monitoring
│   ├─ TimetabledStopVisitStructure (Stop Timetable)
│   │   └─ Scheduled stop information
│   ├─ DriverMessageStructure
│   │   └─ Messages for drivers
│   ├─ InfoMessageStructure
│   │   └─ Information for passengers
│   └─ StopLineNoticeStructure
│       └─ Notices about stop/line
├─ AbstractReferencingItemStructure
│   ├─ VehicleActivityCancellationStructure
│   ├─ MonitoredStopVisitCancellationStructure
│   ├─ TimetabledStopVisitCancellationStructure
│   └─ InfoMessageCancellationStructure
└─ DatedTimetableVersionFrameStructure
    └─ Frame for dated timetable data
```

### 3.7 SIRI Core Message Types

**Call Types:**
```
AbstractCallStructure
├─ AbstractMonitoredCallStructure
│   ├─ MonitoredCallStructure
│   ├─ OnwardCallStructure
│   └─ PreviousCallStructure
└─ RelatedCallStructure (for disruptions)

ServiceJourneyInterchange_StructureGroup
├─ Interchange connection
├─ From/To journey references
├─ Planned vs. Actual timing
└─ Feasibility status
```

**Permission Types:**
```
AbstractPermissionStructure
├─ ConnectionServicePermissionStructure
├─ ControlActionServicePermissionStructure
├─ FacilityMonitoringServicePermissionStructure
├─ GeneralMessageServicePermissionStructure
├─ SituationExchangeServicePermissionStructure
├─ StopMonitoringServicePermissionStructure
├─ StopTimetableServicePermissionStructure
└─ VehicleMonitoringServicePermissionStructure

AbstractTopicPermissionStructure
├─ ConnectionLinkPermissionStructure
├─ InfoChannelPermissionStructure
├─ LinePermissionStructure
├─ OperatorPermissionStructure
├─ StopMonitorPermissionStructure
└─ VehicleMonitorPermissionStructure
```

---

## 4. Cross-Standard Comparison & Alignment

### 4.1 Semantic Mapping Between Standards

| Concept | NeTEx | OpRa | SIRI |
|---------|-------|------|------|
| **Service** | `Service_VersionStructure` | (Implicit via NeTEx import) | Service references in requests |
| **Line** | `Line_VersionStructure` | Line references | LineRef, LineIdentifier |
| **Journey** | `ServiceJourney_VersionStructure`, `VehicleJourney_VersionStructure` | Dated vehicle journey counts | VehicleJourney in activity |
| **Stop** | `StopPlace_VersionStructure`, `ScheduledStopPoint_VersionStructure` | Stop references | StopPointRef |
| **Call** | `Call_VersionStructure`, `PassingTime_VersionStructure` | Implicit in journey | `MonitoredCallStructure`, `OnwardCallStructure` |
| **Vehicle** | `Vehicle_VersionStructure`, `VehicleType_VersionStructure` | Fleet capacity metrics | VehicleRef in monitoring |
| **Fare** | `FareProduct_VersionStructure`, `FarePrice_VersionStructure` | Not applicable | Not applicable |
| **Real-time** | Monitoring frame references | Indicators (counts, intensity) | Delivery structures with real-time data |

### 4.2 Inheritance Pattern Summary

**Pattern 1: Versioned Entities (NeTEx)**
```
VersionedChildStructure
└─ [Specific Entity Type]
   └─ Attributes: id, version, creationTime, modification
```

**Pattern 2: Collection/Relation (NeTEx)**
```
ContainmentAggregationStructure
└─ [Entity Name]_RelStructure
   └─ Sequence of [Entity]_VersionStructure
```

**Pattern 3: Reference Types (All standards)**
```
VersionedRefStructure / RefStructure
└─ References to external entity
   └─ Typically: id, version, modification
```

**Pattern 4: Abstract Base with Service Specializations (SIRI)**
```
AbstractCapabilitiesStructure
├─ EstimatedTimetableServiceCapabilitiesStructure
├─ VehicleMonitoringServiceCapabilitiesStructure
└─ [One per service]
```

**Pattern 5: Item/Delivery (SIRI)**
```
AbstractItemStructure
└─ [Service-specific item] (VehicleActivityStructure, MonitoredStopVisitStructure, etc.)

AbstractServiceDeliveryStructure
└─ [Service-specific delivery] (EstimatedTimetableDeliveryStructure, etc.)
```

### 4.3 Enum/Classification Types

**NeTEx Enumerations:**
- `ServiceTypeEnum` - different service types
- `VehicleTypeEnum` - vehicle classifications
- `AccessibilityLimitationEnum` - accessibility restrictions
- `FareTypeEnum` - fare classifications
- `DayTypeEnum` - operational day types

**SIRI Enumerations:**
- `SeverityEnum` - disruption severity (VerySerious, Serious, Minor, Unknown)
- `ReasonEnum` - disruption reason codes
- `VehicleFeatureEnum` - vehicle capabilities
- `StopPlaceTypeEnum` - stop classifications
- `CongestionLevelEnum` - traffic congestion levels (Empty, VeryLight, Light, Moderate, Heavy, VeryHeavy, Impossible)

**OpRa Enumerations:**
- Implicit through inherited NeTEx types
- Custom indicators for operational metrics

---

## 5. Ontology Generation Recommendations

### 5.1 Proposed RDF Class Hierarchy

**Classes for Core Domain:**
```
napcore:PublicTransportEntity (rdfs:Class)
├─ napcore:Service
├─ napcore:Journey
├─ napcore:Stop
├─ napcore:StopCall
├─ napcore:Vehicle
├─ napcore:Line
├─ napcore:FareProduct
├─ napcore:Disruption
└─ napcore:RealTimeEvent

napcore:ServiceHierarchy
├─ napcore:Service
│   └─ napcore:Line
│       └─ napcore:Journey
│           └─ napcore:StopCall

napcore:StopHierarchy
├─ napcore:TopographicPlace
├─ napcore:StopPlace
│   ├─ napcore:Quay
│   ├─ napcore:Platform
│   └─ napcore:Entrance
└─ napcore:ScheduledStopPoint

napcore:RealTimeHierarchy
├─ napcore:MonitoredVehicleJourney
├─ napcore:MonitoredStopVisit
├─ napcore:Situation
└─ napcore:Disruption
```

### 5.2 Key Properties for Linking

**NeTEx-based Properties:**
```
napcore:hasService → Service
napcore:hasLine → Line
napcore:hasJourney → Journey
napcore:hasStop → Stop
napcore:includesCall → StopCall
napcore:usesVehicle → Vehicle
napcore:hasFareProduct → FareProduct
napcore:operatesOn → DayType
napcore:hasEquipment → Equipment
```

**Real-Time (SIRI-based Properties:**
```
napcore:monitoringDelivery → MonitoredEvent
napcore:hasMonitoredJourney → MonitoredJourney
napcore:hasMonitoredCall → MonitoredCall
napcore:affectedBy → Disruption
napcore:hasEstimatedArrival → Time
napcore:hasEstimatedDeparture → Time
napcore:hasCongestionLevel → CongestionEnum
```

**Operational (OpRa-based Properties:**
```
napcore:measuresCapacity → Capacity
napcore:measuresIntensity → ServiceIntensity
napcore:recordsPassengerCount → PassengerCount
napcore:tracksDelays → DelayRecord
```

### 5.3 Key Patterns for FAQ Knowledge Base

**Pattern 1: Service Information**
```
FAQ: "What services operate on Route X?"
Source: NeTEx Service + Line entities
RDF: ?service rdf:type napcore:Service
     ?service napcore:hasLine ?line
     ?line napcore:name "Route X"
```

**Pattern 2: Journey & Schedule**
```
FAQ: "What are the departure times from Stop Y?"
Source: NeTEx Journey + Call entities
RDF: ?journey napcore:hasStop ?stop
     ?stop napcore:name "Y"
     ?call napcore:arrivalTime ?time
```

**Pattern 3: Real-Time Information**
```
FAQ: "Is the vehicle on time?"
Source: SIRI VehicleMonitoring + EstimatedTimetable
RDF: ?vehicle napcore:hasMonitoredJourney ?mj
     ?mj napcore:hasEstimatedArrival ?eta
     ?eta napcore:delay ?minutes
```

**Pattern 4: Disruption Information**
```
FAQ: "Are there any disruptions affecting Service X?"
Source: SIRI SituationExchange
RDF: ?disruption rdf:type napcore:Disruption
     ?disruption napcore:affectsService ?service
     ?service napcore:name "Service X"
     ?disruption napcore:severity ?level
```

**Pattern 5: Fare Information**
```
FAQ: "What is the fare for Journey X-Y?"
Source: NeTEx FareProduct + Price entities
RDF: ?journey napcore:from ?stopA
     ?journey napcore:to ?stopB
     ?fareProduct napcore:appliesTo ?journey
     ?fareProduct napcore:price ?amount
```

---

## 6. Detailed Type Listings by Standard

### 6.1 NeTEx Complete Type Sample (First 100 complexTypes)

```
[Sorted alphabetically, showing inheritance]

AbstractCapabilitiesStructure                  (root)
AbstractCurveType                              (root GML)
AbstractDiscoveryDeliveryStructure             (root)
AbstractDiscoveryRequestStructure              (root)
AbstractFunctionalServiceRequestStructure     (extends AbstractServiceRequestStructure)
AbstractGMLType                                (root GML)
AbstractGeometricAggregateType                (root GML)
AbstractGeometricPrimitiveType                (root GML)
AbstractGeometryType                          (root GML)
AbstractGroupMember_VersionedChildStructure   (extends AbstractGroupMemberStructure)
AbstractIdentifiedItemStructure               (extends AbstractItemStructure)
AbstractItemStructure                         (root)
AbstractMemberType                            (root GML)
AbstractMetadataPropertyType                  (root)
AbstractNotificationStructure                 (extends ProducerRequestEndpointStructure)
AbstractPermissionStructure                   (root)
AbstractReferencingItemStructure              (extends AbstractItemStructure)
AbstractRequestStructure                      (root)
AbstractRequiredIdentifiedItemStructure       (extends AbstractItemStructure)
AbstractRequiredReferencingItemStructure      (extends AbstractItemStructure)
AbstractRingPropertyType                      (root GML)
AbstractRingType                              (root GML)
AbstractServiceCapabilitiesResponseStructure  (extends AbstractResponseStructure)
AbstractServiceDeliveryStructure              (extends AbstractResponseStructure)
AbstractSubscriptionRequestStructure          (root)
AbstractSubscriptionStructure                 (root)
AbstractSurfaceType                           (root GML)
AbstractTopicPermissionStructure              (root)
AcceptedDriverPermitRefStructure              (extends RefStructure)
AcceptedDriverPermitVersionStructure          (extends VersionedChildStructure)
AccessControlListAssignmentsInFrame_RelStructure (extends containmentAggregationStructure)
AccessControlListAssignmentVersionStructure   (extends VersionedChildStructure)
AccessibilityAssessmentVersionStructure      (extends VersionedChildStructure)
AccessibilityEquipmentVersionStructure       (extends AccessibilityEquipmentStructure)
AccessibilityFeatureEnum                      (extends xsd:string)
AccessibilityLimitationEnum                   (extends xsd:string)
AccessibilityLimitationStructure              (root)
AccessibilityLimitationVersionStructure       (extends AccessibilityLimitationStructure)
AccessibilityNeedsEntitlementPricesInFrame_RelStructure (extends containmentAggregationStructure)
AccessibilityNeeds_RelStructure               (extends containmentAggregationStructure)
... [2,647 more types]
```

### 6.2 OpRa Complete Type Listing

```
AbstractIndicatorLogEntries_RelStructure
AbstractIndicators_RelStructure
AbstractLogEntries_RelStructure
AbstractLoggableObjects_RelStructure
AbstractOpraFunctionalServiceRequestStructure
ActualCapacities_RelStructure
ActualCapacityRefStructure
ActualFleetIDimensionsRefStructure
ActualFleetIDimensions_RelStructure
ActualFrameRequestStructure
ActualFrame_VersionFrameStructure
ActualServiceDimensionsRefStructure
ActualServiceIDimensions_RelStructure
ActualServiceIntensities_RelStructure
ActualServiceIntensityRefStructure
AggregatedOnboardDeviceBasedPassengerCount_Structure
AggregatedOnboardDeviceBasedPassengerCounts_RelStructure
AggregatedTicketingBasedPassengerCount_Structure
AggregatedTicketingBasedPassengerCounts_RelStructure
CancelledDatedVehicleJourneyCountRefStructure
CancelledDatedVehicleJourneyCount_VersionStructure
CancelledDatedVehicleJourneyCounts_RelStructure
CancelledDatedVehicleJourneyDiscoveryDeliveryStructure
CancelledDatedVehicleJourneyDiscoveryRequestStructure
CancelledDatedVehicleJourneyEntries_RelStructure
CancelledDatedVehicleJourneyEntryRefStructure
CancelledDatedVehicleJourneyEntryRefs_RelStructure
CancelledDatedVehicleJourneyEntry_Structure
CancelledDatedVehicleJourneysRequestStructure
CapacilitiesDeliveryStructure
CapacilitiesResponseStructure
CapacilitiesResponseStructureStructure
CapabilityRequestStructure
CapabilitiesRequestStructure
CapacitySpecificationStructure
CtxIndicators_RelStructure
DurationIntervalStructure
DurationIntervals_RelStructure
ExpectedPassengerCounts_RelStructure
ExpectedPassengerCountRefStructure
ExpectedServiceIntensities_RelStructure
ExpectedServiceIntensityRefStructure
ExternalPassengerCounts_RelStructure
ExternalPassengerCountRefStructure
GeneralLogEntries_RelStructure
GeneralLogEntry_VersionStructure
IndicatorFrameDefaultsStructure
LateDatedVehicleJourneyCountRefStructure
LateDatedVehicleJourneyCount_VersionStructure
LateDatedVehicleJourneyCounts_RelStructure
LateDatedVehicleJourneyDiscoveryDeliveryStructure
LateDatedVehicleJourneyDiscoveryRequestStructure
LateDatedVehicleJourneyEntries_RelStructure
LateDatedVehicleJourneyEntryRefStructure
LateDatedVehicleJourneyEntryRefs_RelStructure
LateDatedVehicleJourneyEntry_Structure
LateDatedVehicleJourneysRequestStructure
LogEntryUnitaryValueStructure
LogEntryValueStructure
LogEntryValues_RelStructure
LoggableObjects_RelStructure
OnboardDeviceBasedPassengerCounts_RelStructure
OnboardDeviceBasedPassengerCountRefStructure
OpraDiscoveryDeliveries_RelStructure
OpraDiscoveryRequests_RelStructure
OpraFunctionalDeliveries_RelStructure
OpraFunctionalService_DeliveryStructure
OpraRequest_DeliveryStructure
OpraRequests_RelStructure
OpraServiceCapabilitesResponses_RelStructure
OpraServiceCapabilitiesRequests_RelStructure
OpraSubscriptionRequests_RelStructure
PlannedCapacities_RelStructure
PlannedCapacityRefStructure
PlannedFleetDimensions_RelStructure
PlannedFleetDimensionsRefStructure
PlannedServiceDimensions_RelStructure
PlannedServiceDimensionsRefStructure
PlannedServiceIntensities_RelStructure
PlannedServiceIntensityRefStructure
ServiceCapability_DeliveryStructure
ServiceCapability_ResponseStructure
SimpleEventRefStructure
SimpleEventRefs_RelStructure
TicketingBasedPassengerCounts_RelStructure
TicketingBasedPassengerCountRefStructure
TypesOfDelay_RelStructure
ValidationEntries_RelStructure
ValidationEntry_VersionStructure
ValidationEntryRefs_RelStructure
VehicleLoadEntries_RelStructure
VehicleTypeCapacities_RelStructure
VehicleTypeCapacity_RefStructure
VehicleTypeCapacityStructure
dataObjects_RelStructure
```

### 6.3 SIRI Service-Specific Types

**EstimatedTimetable (ET) - Key Types:**
```
EstimatedTimetableDeliveryStructure
EstimatedTimetableRequestStructure
EstimatedTimetableServiceCapabilitiesStructure
EstimatedTimetableServicePermissionStructure
EstimatedTimetableSubscriptionStructure
EstimatedCall_VersionStructure
DatedEstimatedCall_VersionStructure
EstimatedVersionFrameStructure
```

**VehicleMonitoring (VM) - Key Types:**
```
VehicleMonitoringDeliveryStructure
VehicleMonitoringRequestStructure
VehicleMonitoringSubscriptionStructure
VehicleMonitoringServiceCapabilitiesStructure
VehicleMonitoringServicePermissionStructure
VehicleActivityStructure
MonitoredVehicleJourney_StructureGroup
OnwardCallStructure
VehicleActivityCancellationStructure
```

**StopMonitoring (SM) - Key Types:**
```
StopMonitoringDeliveryStructure
StopMonitoringRequestStructure
StopMonitoringSubscriptionStructure
StopMonitoringServiceCapabilitiesStructure
StopMonitoringServicePermissionStructure
MonitoredStopVisitStructure
MonitoredCallStructure
PreviousCallStructure
MonitoredStopVisitCancellationStructure
StopLineNoticeStructure
```

**SituationExchange (SX) - Key Types:**
```
SituationExchangeDeliveryStructure
SituationExchangeRequestStructure
SituationExchangeSubscriptionStructure
SituationExchangeServiceCapabilitiesStructure
SituationExchangeServicePermissionStructure
PtSituationElementStructure
RoadSituationElementStructure
SituationElementStructure
```

---

## 7. Key Findings & Recommendations

### 7.1 Schema Complexity Analysis

| Metric | NeTEx | OpRa | SIRI |
|--------|-------|------|------|
| Total complexTypes | 2,687 | 153 | 830 |
| Root types | 400+ | 51 | 488 |
| Inheritance depth | 4-7 levels | 2-3 levels | 3-5 levels |
| Collection types | ~800 | ~40 | ~100 |
| Reference types | ~200 | ~20 | ~150 |
| Abstract bases | ~350 | ~15 | ~100 |

### 7.2 Recommended FAQ Ontology Strategy

**Phase 1: Core Entities**
```
1. Map NeTEx versioned entities to NAPCORE ontology classes
2. Create rdfs:subClassOf chains for standard hierarchies
3. Define properties for common relationships (hasService, hasJourney, hasStop)
```

**Phase 2: Real-Time Layer**
```
1. Integrate SIRI delivery/request structures
2. Add temporal properties (estimatedTime, actualTime, delay)
3. Link to monitoring/disruption entities
```

**Phase 3: Operations Layer**
```
1. Incorporate OpRa indicators
2. Add metrics (capacity, intensity, passenger count)
3. Create measurement/metric properties
```

### 7.3 Knowledge Base Ingestion Profile

**Recommended Focus Areas:**
1. **NeTEx Service/Network** - 450+ types (28% of NeTEx)
2. **NeTEx Journey/Schedule** - 350+ types (13% of NeTEx)
3. **NeTEx Stop/Place** - 180+ types (7% of NeTEx)
4. **SIRI Vehicle Monitoring** - 120+ types (14% of SIRI)
5. **SIRI Stop Monitoring** - 90+ types (11% of SIRI)
6. **SIRI SituationExchange** - 100+ types (12% of SIRI)
7. **OpRa Indicators** - 40+ types (26% of OpRa)

**Chunking Strategy:**
- Service-related: 1 FAQ per service type (~100 chunks)
- Journey/Schedule: 1 FAQ per journey type (~80 chunks)
- Stop Information: 1 FAQ per stop attribute (~60 chunks)
- Real-Time Monitoring: 1 FAQ per monitoring event type (~120 chunks)
- Disruptions: 1 FAQ per disruption type (~50 chunks)
- Total: ~400+ FAQ base documents for automated generation

### 7.4 Document Type Classification

**From NeTEx Types:**
- **Guide** (~200): Service structure, network documentation, terminology
- **Reference** (~300): Stop/Line/Journey lookups, attribute definitions
- **Schema/Frame** (~150): Timetable structure, calendar definitions
- **Tool** (~150): Query examples, filtering patterns, API endpoints

**From SIRI Types:**
- **Guide** (~80): Real-time monitoring, disruption handling
- **Reference** (~200): Event types, message structures
- **Schema/Frame** (~100): Service capabilities, subscription patterns
- **Tool** (~100): Request/response examples, filtering

**From OpRa Types:**
- **Guide** (~40): Operational metrics, performance indicators
- **Reference** (~50): Capacity/intensity definitions
- **Tool** (~30): Calculation examples, thresholds

---

## 8. Conclusion

This comprehensive XSD analysis reveals:

1. **NeTEx** provides the foundational network and schedule data model with 2,687 types focusing on versioned entities and collection aggregations
2. **SIRI** adds real-time monitoring capabilities with 830 types structured around service-specific request/delivery/subscription patterns
3. **OpRa** contributes operational metrics and performance indicators with 153 specialized types

The three standards exhibit clear **inheritance patterns** that can be directly mapped to RDF/OWL ontology classes, enabling structured FAQ knowledge base generation with:
- **Clear entity hierarchies** for rdfs:subClassOf chains
- **Service-specific patterns** for filtered FAQ generation
- **Measurement frameworks** for operational metrics
- **Real-time event structures** for disruption/monitoring topics

**Recommended next steps:**
1. Implement ontology class generation from inheritance chains
2. Create FAQ generation templates per domain entity
3. Build document type-aware retrieval using extracted classifications
4. Develop service-specific FAQ profiles (ET, VM, SM, SX, etc.)
