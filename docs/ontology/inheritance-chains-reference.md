# XSD Inheritance Chains Reference
**Complete Parent → Child Relationships for NAPCORE Standards**

---

## NeTEx Core Inheritance Chains

### Service & Network Hierarchy

```
VersionedChildStructure
└─ DataManagedObject_VersionStructure
   └─ GroupOfEntities_VersionStructure
      ├─ Network_VersionStructure
      │   ├─ NetworkRef / NetworkRefStructure
      │   └─ Used in: serviceFrame, networkFrame
      │
      ├─ Service_VersionStructure
      │   ├─ Describes grouping of lines
      │   ├─ References lines, journeys
      │   └─ Collections: allServices_RelStructure, services_RelStructure
      │
      └─ GroupOfLines_VersionStructure
          ├─ Named line grouping
          └─ Collections: groupsOfLines_RelStructure

Service_VersionStructure (abstract)
├─ FlexibleLine_VersionStructure
│   ├─ Flexible route service
│   ├─ DeviatedRoute: true/false
│   └─ Collections: flexibleLines_RelStructure
│
├─ Line_VersionStructure
│   ├─ Standard public transport line
│   ├─ Routes, directions, journeys
│   ├─ Inherits: name, id, version
│   ├─ Collections: lines_RelStructure
│   └─ References: LineRef (extends VersionedRefStructure)
│
└─ Network_VersionStructure
    ├─ Network of services/lines
    ├─ Contains multiple services/lines
    └─ Collections: networks_RelStructure

Line_VersionStructure
├─ Attributes:
│   ├─ id (LineIdType)
│   ├─ name (MultilingualString)
│   ├─ lineNumber (String)
│   ├─ transportMode (AllModesEnum)
│   ├─ ticketMachineServiceCode (String)
│   └─ version (String)
│
├─ Child Collections:
│   ├─ routes_RelStructure → contains RouteRef
│   ├─ journeyPatterns_RelStructure → contains JourneyPatternRef
│   └─ serviceJourneys_RelStructure → contains ServiceJourneyRef
│
└─ Related References:
    ├─ ResponsibilityRoleRef
    ├─ OperatorRef
    └─ GroupsOfLineRefs
```

### Journey & Timetable Hierarchy

```
VersionedChildStructure
└─ LinkSequence_VersionStructure
   └─ Journey_VersionStructure (abstract)
      ├─ ServiceJourney_VersionStructure
      │   ├─ Passenger-carrying journey
      │   ├─ For specific DayType
      │   ├─ Based on ServiceJourneyPattern
      │   ├─ Inherits: id, version, name
      │   ├─ Attributes:
      │   │   ├─ dayTypeRef (DayTypeRef)
      │   │   ├─ journeyPatternRef (JourneyPatternRef)
      │   │   ├─ operatorRef (OperatorRef)
      │   │   ├─ lineRef (LineRef)
      │   │   ├─ routeRef (RouteRef)
      │   │   └─ timingPattern references
      │   └─ Collections:
      │       ├─ passingTimes_RelStructure
      │       ├─ calls_RelStructure
      │       └─ timingLinks_RelStructure
      │
      ├─ DeadRun_VersionStructure
      │   ├─ Non-passenger journey
      │   ├─ Vehicle operational movement
      │   └─ Same structure as ServiceJourney
      │
      └─ TrainNumberJourney_VersionStructure
          └─ Train service identification

VehicleJourney_VersionStructure (abstract)
├─ Operates over LinkSequence
├─ Timing linked via TimingLinks
└─ Subdivided:
    ├─ ServiceJourney_VersionStructure
    ├─ DeadRun_VersionStructure
    └─ SpecialService_VersionStructure

JourneyPattern_VersionStructure (abstract)
├─ ServiceJourneyPattern_VersionStructure
│   ├─ Sequence of RoutePoints
│   ├─ Timetable pattern
│   ├─ Collections:
│   │   └─ pointsInPattern_RelStructure
│   └─ References:
│       ├─ routeRef (RouteRef)
│       └─ lineRef (LineRef)
│
└─ TimingPattern_VersionStructure
    ├─ Run & wait times
    ├─ No actual stops
    └─ Collections:
        └─ timingLinks_RelStructure

Call_VersionStructure (abstract)
├─ ScheduledStopPoint-based call
├─ Arrival/Departure timings
└─ Variants:
    ├─ TimetabledPassingTime_VersionStructure
    │   ├─ Planned call time
    │   ├─ arrivalTime (TimeOfDay)
    │   ├─ departureTime (TimeOfDay)
    │   ├─ Attributes:
    │   │   ├─ waitTime (Duration)
    │   │   ├─ aitingTime (Duration)
    │   │   └─ elapsedTime (Duration)
    │   └─ References: scheduledStopPointRef
    │
    ├─ PassingTime_VersionStructure
    │   ├─ Actual/observed passing
    │   └─ actualArrivalTime, actualDepartureTime
    │
    ├─ TargetPassingTime_VersionStructure
    │   ├─ Target/expected time
    │   └─ targetArrivalTime, targetDepartureTime
    │
    └─ DatedCallStructure
        └─ Call for dated journey
```

### Stop & Place Hierarchy

```
VersionedChildStructure
└─ Place_VersionStructure (abstract)
   ├─ TopographicPlace_VersionStructure
   │   ├─ Geographic/administrative place
   │   ├─ country, principalityRef, etc.
   │   ├─ Collections:
   │   │   └─ topographicPlaces_RelStructure
   │   └─ References:
   │       ├─ TopographicPlaceRef
   │       └─ AdministrativeAreaRef
   │
   ├─ PointOfInterest_VersionStructure
   │   ├─ Named point of interest
   │   ├─ Potentially stops at POI
   │   ├─ Collections:
   │   │   └─ pointsOfInterest_RelStructure
   │   └─ References: PointOfInterestRef
   │
   └─ StopPlace_VersionStructure
       ├─ Public transport access point
       ├─ Collections:
       │   ├─ quays_RelStructure
       │   │   └─ Contains Quay_VersionStructure
       │   ├─ platforms_RelStructure
       │   │   └─ Contains Platform_VersionStructure
       │   ├─ entrances_RelStructure
       │   │   └─ Contains StopPlaceEntrance_VersionStructure
       │   ├─ stopPlaceAreas_RelStructure
       │   │   └─ Contains StopArea_VersionStructure
       │   └─ accessibilityAssessment_RelStructure
       │
       ├─ References:
       │   ├─ StopPlaceRef / StopPlaceRefStructure
       │   ├─ QuayRef / QuayRefStructure
       │   ├─ PlatformRef / PlatformRefStructure
       │   └─ StopPlaceEntranceRef / StopPlaceEntranceRefStructure
       │
       └─ Attributes:
           ├─ StopPlaceType (busStation, railStation, airport, etc.)
           ├─ placeEquipment_RelStructure
           ├─ suitabilities_RelStructure
           └─ accessibility_RelStructure

Quay_VersionStructure
├─ Boarding/alighting area at StopPlace
├─ Directly serves vehicles
├─ Attributes:
│   ├─ quayType (BusStop, RailPlatform, etc.)
│   ├─ compass_bearing (Integer)
│   ├─ pedestrianAccessible (Boolean)
│   └─ wheelChairAccessible (Boolean)
├─ Collections:
│   └─ equipment_RelStructure
└─ Parent: StopPlace

ScheduledStopPoint_VersionStructure
├─ Stop definition for timetables
├─ Distinct from StopPlace (facility)
├─ Used in:
│   ├─ JourneyPatterns
│   ├─ Calls
│   └─ Timing information
├─ Attributes:
│   ├─ timing pattern inclusion
│   ├─ forAlighting (Boolean)
│   ├─ forBoarding (Boolean)
│   └─ stopSeqNo (Integer)
└─ References:
    ├─ ScheduledStopPointRef
    └─ Links to StopPlace via stopPlaceRef
```

### Fare & Pricing Hierarchy

```
VersionedChildStructure
└─ FareProduct_VersionStructure (abstract)
   ├─ PreAssignedFareProduct_VersionStructure
   │   ├─ Fare_VersionStructure
   │   │   ├─ Traditional fare product
   │   │   ├─ Inherits: name, description, id
   │   │   ├─ Collections:
   │   │   │   ├─ validableElements_RelStructure
   │   │   │   ├─ usageParameters_RelStructure
   │   │   │   └─ fareElementPrices_RelStructure
   │   │   └─ References: FareRef
   │   │
   │   ├─ Concession_VersionStructure
   │   │   ├─ Discounted fare
   │   │   ├─ Same structure as Fare
   │   │   └─ Collections: same as Fare
   │   │
   │   └─ FareSpec_VersionStructure
   │       └─ Specification of fare characteristics
   │
   ├─ SalesOfferPackage_VersionStructure
   │   ├─ Bundled fare package
   │   ├─ Group of products
   │   ├─ Collections:
   │   │   ├─ includedFareProducts_RelStructure
   │   │   ├─ prices_RelStructure
   │   │   └─ usage parameters
   │   └─ References: SalesOfferPackageRef
   │
   └─ FarePart_VersionStructure
       └─ Component of fare structure

FareStructureElement_VersionStructure (abstract)
├─ Component of fare calculation
├─ Variants:
│   ├─ ValidableElement_VersionStructure
│   │   ├─ AccessRightParameter_VersionStructure
│   │   │   ├─ Eligibility for access right
│   │   │   └─ Collections: accessRightParameterPrices_RelStructure
│   │   │
│   │   ├─ UsageParameterEligibility_VersionStructure
│   │   │   ├─ Who can use this fare
│   │   │   └─ Age, disability, residency constraints
│   │   │
│   │   ├─ UsageParameterEntitlement_VersionStructure
│   │   │   ├─ What services included
│   │   │   ├─ Trip count, time validity
│   │   │   └─ Collections: usageParameterEntitlementPrices_RelStructure
│   │   │
│   │   └─ UsageParameterAfterSales_VersionStructure
│   │       ├─ Post-purchase rules
│   │       ├─ Refund, exchange, upgrade
│   │       └─ Collections: usageParameterAfterSalesPrices_RelStructure
│   │
│   └─ TimeStructureFactor_VersionStructure
│       ├─ Time-based pricing component
│       ├─ timeInterval (Start/End)
│       └─ Collections: timeStructureFactorPrices_RelStructure

FarePrice_VersionStructure (abstract)
├─ Pricing data
├─ Variants:
│   ├─ FarePriceWithMethod_VersionStructure
│   │   ├─ Calculation method
│   │   ├─ Collections: fareElementPrices_RelStructure
│   │   └─ pricingMethod (distance, zone, flat, etc.)
│   │
│   ├─ FarePriceWithRoundingRules_VersionStructure
│   │   ├─ Rounding strategies
│   │   ├─ Collections: roundingSteps_RelStructure
│   │   └─ roundingRule (up, down, standard)
│   │
│   └─ FarePriceDailyModifier_VersionStructure
│       └─ Daily/temporal price modifications

DistanceStructureFactor_VersionStructure
├─ Distance-based pricing
├─ Start/end stop distances
├─ Collections: distanceStructureFactorPrices_RelStructure
└─ numbersOfUnitsInDistance

GeographicStructureFactor_VersionStructure
├─ Zone/geographic pricing
├─ Zone identification
├─ Collections: geographicStructureFactorPrices_RelStructure
└─ numberOfZonesInDistance

QualityStructureFactor_VersionStructure
├─ Service quality pricing
├─ Quality level definition
├─ Collections: qualityStructureFactorPrices_RelStructure
└─ qualityLevel
```

### Equipment & Accessibility

```
VersionedChildStructure
└─ Vehicle_VersionStructure
   ├─ Attributes: id, registration, type
   ├─ Collections:
   │   └─ vehicleEquipment_RelStructure
   │       └─ Contains VehicleEquipment_VersionStructure
   └─ References: VehicleRef

VehicleEquipment_VersionStructure (abstract)
├─ AccessibilityEquipment_VersionStructure
│   ├─ Lift_VersionStructure
│   ├─ Ramp_VersionStructure
│   ├─ Handholds_VersionStructure
│   ├─ Tactile_VersionStructure
│   └─ Wheelchair_VersionStructure
│
├─ GeneralEquipment_VersionStructure
│   ├─ Seating_VersionStructure
│   ├─ Luggage_VersionStructure
│   ├─ Bicycle_VersionStructure
│   ├─ RetractableStep_VersionStructure
│   └─ Platform_VersionStructure
│
├─ PassengerEquipment_VersionStructure
│   ├─ Toilet_VersionStructure
│   ├─ ClimateControl_VersionStructure
│   ├─ Lighting_VersionStructure
│   ├─ FirstAidKit_VersionStructure
│   └─ SmokerAreas_VersionStructure
│
└─ VehicleServiceEquipment_VersionStructure
    ├─ CommunicationEquipment_VersionStructure
    ├─ OnBoardComfort_VersionStructure
    └─ RealTimeInformation_VersionStructure

AccessibilityAssessment_VersionStructure
├─ Wheelchair accessible: true/false
├─ Audio feedback: true/false
├─ Visual display: true/false
├─ Collections:
│   ├─ accessibilityLimitations_RelStructure
│   └─ accessibilityFeatures_RelStructure
└─ globalOptions_RelStructure
```

---

## SIRI Inheritance Chains

### Service Request/Delivery Hierarchy

```
AbstractRequestStructure (root)
├─ AbstractServiceRequestStructure (extends AbstractRequestStructure)
│   ├─ AbstractFunctionalServiceRequestStructure
│   │   ├─ EstimatedTimetableRequestStructure
│   │   ├─ StopMonitoringRequestStructure
│   │   ├─ VehicleMonitoringRequestStructure
│   │   ├─ StopTimetableRequestStructure
│   │   ├─ ProductionTimetableRequestStructure
│   │   ├─ ConnectionMonitoringRequestStructure
│   │   ├─ ConnectionTimetableRequestStructure
│   │   ├─ GeneralMessageRequestStructure
│   │   ├─ SituationExchangeRequestStructure
│   │   ├─ FacilityMonitoringRequestStructure
│   │   └─ ControlActionRequestStructure
│   │
│   └─ ServiceCapabilitiesRequestStructure
│
├─ AuthenticatedRequestStructure
│   ├─ AbstractDiscoveryRequestStructure
│   │   ├─ StopPointsDiscoveryRequestStructure
│   │   ├─ LinesDiscoveryRequestStructure
│   │   ├─ ProductCategoriesDiscoveryRequestStructure
│   │   ├─ ServiceFeaturesDiscoveryRequestStructure
│   │   ├─ VehicleFeaturesRequestStructure
│   │   ├─ ConnectionLinksDiscoveryRequestStructure
│   │   ├─ InfoChannelDiscoveryRequestStructure
│   │   └─ FacilityRequestStructure
│   │
│   ├─ RequestStructure
│   │   ├─ AbstractSubscriptionRequestStructure
│   │   │   └─ SubscriptionRequestStructure
│   │   │       ├─ [Service-specific subscriptions]
│   │   │       ├─ EstimatedTimetableSubscriptionStructure
│   │   │       ├─ StopMonitoringSubscriptionStructure
│   │   │       ├─ VehicleMonitoringSubscriptionStructure
│   │   │       └─ ... [others]
│   │   │
│   │   ├─ CapabilitiesRequestStructure
│   │   └─ CheckStatusRequestStructure
│   │
│   └─ TerminateSubscriptionRequestStructure

AbstractServiceDeliveryStructure (root)
├─ EstimatedTimetableDeliveryStructure
│   ├─ Status information
│   └─ Collections:
│       └─ estimatedCalls_RelStructure
│
├─ StopTimetableDeliveryStructure
│   ├─ Stop-based scheduled times
│   └─ Collections:
│       └─ scheduledStopVisits_RelStructure
│
├─ StopMonitoringDeliveryStructure
│   ├─ Real-time stop information
│   ├─ Collections:
│   │   └─ monitoredStopVisits_RelStructure
│   └─ References service requests
│
├─ VehicleMonitoringDeliveryStructure
│   ├─ Real-time vehicle positions
│   ├─ Collections:
│   │   └─ vehicleActivities_RelStructure
│   └─ UpdateInterval, ValidUntil, etc.
│
├─ ConnectionMonitoringDeliveryStructure
│   └─ Interchange monitoring
│
├─ SituationExchangeDeliveryStructure
│   ├─ Disruption information
│   ├─ Collections:
│   │   └─ situations_RelStructure
│   │       ├─ PtSituationElementStructure
│   │       └─ RoadSituationElementStructure
│   └─ ValidUntil, Status
│
├─ GeneralMessageDeliveryStructure
│   └─ General information messages
│
├─ FacilityMonitoringDeliveryStructure
│   └─ Facility status
│
├─ ProductionTimetableDeliveryStructure
│   └─ Static schedule reference
│
└─ ConnectionTimetableDeliveryStructure
    └─ Scheduled connections
```

### Item Hierarchy

```
AbstractItemStructure (root)
├─ AbstractIdentifiedItemStructure (extends AbstractItemStructure)
│   ├─ VehicleActivityStructure
│   │   ├─ Extends: AbstractIdentifiedItemStructure
│   │   ├─ RecordedAtTime (TimeStamp)
│   │   ├─ MonitoredVehicleJourney_StructureGroup
│   │   │   ├─ LineRef
│   │   │   ├─ DirectionRef
│   │   │   ├─ FramedVehicleJourneyRef
│   │   │   ├─ JourneyName
│   │   │   ├─ Occupancy (empty, very light, light, moderate, heavy, very heavy, impossible)
│   │   │   ├─ Bearing (degrees 0-359)
│   │   │   ├─ Speed (km/h)
│   │   │   ├─ Odometer (meters)
│   │   │   ├─ OperatorRef
│   │   │   ├─ OperatorName
│   │   │   ├─ MonitoredCall (current stop)
│   │   │   ├─ OnwardCalls (future stops)
│   │   │   └─ Previous Calls (past stops)
│   │   │
│   │   ├─ References:
│   │   │   ├─ VehicleRef
│   │   │   └─ VehicleJourneyRef
│   │   │
│   │   └─ Position information:
│   │       ├─ Location (GPS)
│   │       ├─ LinkRef (road/link)
│   │       └─ OrderedStopVisitRef
│   │
│   ├─ MonitoredStopVisitStructure
│   │   ├─ Extends: AbstractIdentifiedItemStructure
│   │   ├─ RecordedAtTime
│   │   ├─ MonitoredCall (current vehicle)
│   │   ├─ OnwardCalls (future arrivals)
│   │   ├─ PreviousCalls (past departures)
│   │   ├─ StopPointRef
│   │   ├─ StopPointName
│   │   ├─ VisitNumber (sequence at stop)
│   │   └─ Passenger information
│   │
│   ├─ TimetabledStopVisitStructure
│   │   ├─ Scheduled (not real-time) stop info
│   │   ├─ StopPointRef
│   │   ├─ ScheduledStopVisitCall
│   │   │   ├─ ExpectedArrivalTime
│   │   │   ├─ ExpectedDepartureTime
│   │   │   ├─ ServiceJourneyRef
│   │   │   └─ CallNumber
│   │   └─ LineRef
│   │
│   ├─ DriverMessageStructure
│   │   └─ Messages for drivers
│   │
│   ├─ InfoMessageStructure
│   │   └─ Passenger information messages
│   │
│   └─ StopLineNoticeStructure
│       └─ Notices about line/stop
│
├─ AbstractReferencingItemStructure (extends AbstractItemStructure)
│   ├─ VehicleActivityCancellationStructure
│   │   └─ Cancellation of vehicle activity
│   │
│   ├─ MonitoredStopVisitCancellationStructure
│   │   └─ Cancellation of monitored stop visit
│   │
│   ├─ TimetabledStopVisitCancellationStructure
│   │   └─ Cancellation of timetabled visit
│   │
│   ├─ StopLineNoticeCancellationStructure
│   │   └─ Cancellation of notice
│   │
│   └─ InfoMessageCancellationStructure
│       └─ Cancellation of info message
│
└─ DatedTimetableVersionFrameStructure
    └─ Container for dated timetable data
```

### Call Hierarchy

```
AbstractCallStructure (root)
├─ RelatedCallStructure
│   ├─ Reference to call
│   ├─ Used in disruptions
│   └─ CallRef with offset
│
└─ AbstractMonitoredCallStructure (root for monitored calls)
    ├─ MonitoredCallStructure
    │   ├─ Current/next vehicle at stop
    │   ├─ StopPointRef
    │   ├─ StopPointName
    │   ├─ ArrivalTime (planned)
    │   ├─ ExpectedArrivalTime (estimated)
    │   ├─ DepartureTime (planned)
    │   ├─ ExpectedDepartureTime (estimated)
    │   ├─ ArrivalStatus (onTime, early, delayed, cancelled, missed)
    │   ├─ DepartureStatus
    │   ├─ Delay (duration)
    │   ├─ CallNumber (stop sequence)
    │   ├─ BoardingAlighting (true/false)
    │   ├─ DestinationDisplay
    │   └─ Order (stop sequence number)
    │
    ├─ OnwardCallStructure
    │   ├─ Upcoming stop (not yet reached)
    │   ├─ StopPointRef
    │   ├─ ExpectedArrivalTime
    │   ├─ ExpectedDepartureTime
    │   ├─ BoardingAlighting
    │   └─ Order (sequence at stop)
    │
    └─ PreviousCallStructure
        ├─ Already served stop
        ├─ StopPointRef
        ├─ ArrivalTime (actual or expected)
        ├─ DepartureTime (actual or expected)
        └─ Order (sequence)
```

### Situation Hierarchy

```
AbstractSituationElementStructure (root)
├─ SituationElementStructure
│   ├─ Generic situation/disruption
│   ├─ Description
│   ├─ Severity (VerySerious, Serious, Minor, Unknown)
│   ├─ CreationTime
│   ├─ StartTime
│   ├─ EndTime
│   ├─ Advice
│   └─ PublicityChannel
│
├─ PtSituationElementStructure (extends SituationElementStructure)
│   ├─ Public transport specific disruption
│   ├─ AffectedLines_RelStructure
│   │   └─ AffectedLineStructure
│   │       ├─ LineRef
│   │       ├─ AffectedStops_RelStructure
│   │       │   └─ AffectStopPoint
│   │       ├─ AffectedRoutes_RelStructure
│   │       └─ Consequences_RelStructure
│   │
│   ├─ AffectedStops_RelStructure
│   │   └─ Directly affected stops
│   │
│   ├─ AffectedOperators_RelStructure
│   │   └─ OperatorRef
│   │
│   ├─ AffectedJourneys_RelStructure
│   │   └─ Specific journeys affected
│   │
│   ├─ Consequence_VersionStructure
│   │   ├─ Effect of disruption
│   │   ├─ Severity
│   │   ├─ Condition
│   │   └─ Advice
│   │
│   ├─ Severity levels:
│   │   ├─ VerySerious (major impact)
│   │   ├─ Serious (significant impact)
│   │   ├─ Minor (small impact)
│   │   └─ Unknown
│   │
│   └─ Reason types:
│       ├─ Accident
│       ├─ AbnormalTraffic
│       ├─ Crowding
│       ├─ DisruptedService
│       ├─ RoadWorks
│       ├─ Strike
│       ├─ TrafficAccident
│       ├─ WeatherRelated
│       └─ ... [20+ more]
│
└─ RoadSituationElementStructure (extends SituationElementStructure)
    └─ Road/infrastructure disruption
```

### Permission Hierarchy

```
AbstractPermissionStructure (root)
├─ ConnectionServicePermissionStructure
├─ ControlActionServicePermissionStructure
├─ FacilityMonitoringServicePermissionStructure
├─ GeneralMessageServicePermissionStructure
├─ SituationExchangeServicePermissionStructure
├─ StopMonitoringServicePermissionStructure
├─ StopTimetableServicePermissionStructure
└─ VehicleMonitoringServicePermissionStructure

AbstractTopicPermissionStructure (root)
├─ ConnectionLinkPermissionStructure
├─ InfoChannelPermissionStructure
├─ LinePermissionStructure
├─ OperatorPermissionStructure
├─ StopMonitorPermissionStructure
└─ VehicleMonitorPermissionStructure
```

---

## OpRa Inheritance Chains

### Indicator Hierarchy

```
AbstractIndicators_RelStructure (root)
├─ AbstractCapacities_RelStructure (extends AbstractIndicators_RelStructure)
│   ├─ ActualCapacities_RelStructure
│   │   ├─ ActualCapacityRefStructure
│   │   └─ Contains: ActualCapacity_VersionStructure
│   │
│   ├─ PlannedCapacities_RelStructure
│   │   └─ Contains: PlannedCapacity_VersionStructure
│   │
│   └─ VehicleTypeCapacities_RelStructure
│       ├─ VehicleTypeCapacity_RefStructure
│       └─ Contains: VehicleTypeCapacityStructure
│
├─ AbstractServiceIntensities_RelStructure
│   ├─ ActualServiceIntensities_RelStructure
│   │   ├─ ActualServiceIntensityRefStructure
│   │   └─ Contains: service intensity metrics
│   │
│   ├─ ExpectedServiceIntensities_RelStructure
│   │   ├─ ExpectedServiceIntensityRefStructure
│   │   └─ Contains: forecasted intensity
│   │
│   └─ PlannedServiceIntensities_RelStructure
│       └─ Contains: planned values
│
├─ AbstractFleetDimensions_RelStructure
│   ├─ ActualFleetIDimensions_RelStructure
│   │   ├─ ActualFleetIDimensionsRefStructure
│   │   └─ Fleet size, composition metrics
│   │
│   ├─ PlannedFleetDimensions_RelStructure
│   │   ├─ PlannedFleetDimensionsRefStructure
│   │   └─ Planned fleet composition
│   │
│   └─ ActualFleetIDimensions_RelStructure
│
├─ AbstractServiceDimensions_RelStructure
│   ├─ ActualServiceIDimensions_RelStructure
│   │   ├─ ActualServiceIDimensionsRefStructure
│   │   └─ Service coverage, frequency metrics
│   │
│   └─ PlannedServiceDimensions_RelStructure
│       └─ Planned service dimensions
│
└─ AbstractPassengerCounts_RelStructure
    ├─ ExpectedPassengerCounts_RelStructure
    │   ├─ ExpectedPassengerCountRefStructure
    │   └─ Forecasted counts
    │
    ├─ OnboardDeviceBasedPassengerCounts_RelStructure
    │   ├─ OnboardDeviceBasedPassengerCountRefStructure
    │   └─ From on-board counters
    │
    ├─ TicketingBasedPassengerCounts_RelStructure
    │   ├─ TicketingBasedPassengerCountRefStructure
    │   └─ From ticketing system
    │
    ├─ ExternalPassengerCounts_RelStructure
    │   ├─ ExternalPassengerCountRefStructure
    │   └─ From external sources
    │
    └─ Aggregated variants:
        ├─ AggregatedOnboardDeviceBasedPassengerCounts_RelStructure
        └─ AggregatedTicketingBasedPassengerCounts_RelStructure
```

### Journey & Delay Tracking

```
AbstractDatedVehicleJourney_RelStructure (root)
├─ CancelledDatedVehicleJourneyCounts_RelStructure
│   ├─ CancelledDatedVehicleJourneyCountRefStructure
│   ├─ Contains: CancelledDatedVehicleJourneyCount_VersionStructure
│   ├─ Contains: CancelledDatedVehicleJourneyEntries_RelStructure
│   │   └─ CancelledDatedVehicleJourneyEntry_Structure
│   │       ├─ DatedVehicleJourneyRef
│   │       ├─ ServiceJourneyRef
│   │       ├─ CancelReason
│   │       └─ LastUpdateTime
│   └─ Aggregate cancelled journeys
│
└─ LateDatedVehicleJourneyCounts_RelStructure
    ├─ LateDatedVehicleJourneyCountRefStructure
    ├─ Contains: LateDatedVehicleJourneyCount_VersionStructure
    ├─ Contains: LateDatedVehicleJourneyEntries_RelStructure
    │   └─ LateDatedVehicleJourneyEntry_Structure
    │       ├─ DatedVehicleJourneyRef
    │       ├─ ServiceJourneyRef
    │       ├─ DelayMinutes (Duration)
    │       ├─ DelayReason
    │       └─ LastUpdateTime
    └─ Track late/delayed journeys
```

### Log & Audit

```
AbstractLogEntries_RelStructure (root)
├─ GeneralLogEntries_RelStructure
│   ├─ GeneralLogEntry_VersionStructure
│   ├─ Collections:
│   │   ├─ logEntryValues_RelStructure
│   │   │   └─ LogEntryValue_VersionStructure
│   │   │       ├─ Metric value
│   │   │       ├─ Timestamp
│   │   │       └─ Status
│   │   │
│   │   └─ contextualIndicators_RelStructure
│   │       └─ CtxIndicator
│   │           ├─ Supporting context
│   │           └─ Referenced facts
│   │
│   └─ Logging general events
│
└─ ValidationEntries_RelStructure
    ├─ ValidationEntry_VersionStructure
    ├─ ValidationEntryRefs_RelStructure
    └─ Validation/quality checks
```

---

## Summary Statistics

| Standard | Root Types | Max Depth | Collections | References |
|----------|-----------|-----------|-------------|-----------|
| **NeTEx** | 400+ | 7 | ~800 | ~200 |
| **OpRa** | 51 | 3 | ~40 | ~20 |
| **SIRI** | 488 | 5 | ~100 | ~150 |

**Key Patterns:**
- **Collection Pattern** (_RelStructure): Used for aggregations of entities
- **Reference Pattern** (RefStructure, *Ref): Used for external references
- **Version Pattern** (_VersionStructure): Used for versioned entities
- **Service Pattern**: SIRI uses parallel service-specific types
- **Abstract Base Pattern**: All standards use abstract bases for polymorphism
