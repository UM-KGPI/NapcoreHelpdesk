# NETEX Alignment Gap Report

Standard ontology: `netex.ttl`
Alignment file: `nits-netex-align.ttl`

| Metric | Count |
|--------|-------|
| Total classes in netex.ttl | 871 |
| Already aligned | 62 |
| **Unaligned (gap)** | **831** |

---

## Proposed additions by NITS category

> Copy the TTL block for a category into `nits-netex-align.ttl` after review.
> Delete or comment out lines you want to skip.

### Skip candidates (94 classes)

These are enumeration types, list containers, or abstract base classes.
They are typically not useful retrieval targets.
You may bulk-align them all as `nits:DataArtifact` or leave them unaligned.

```
netex:AbstractGroupMember  # Abstract base class — derives from parent alignment
netex:AccessFacilityList  # XSD list container — not a retrieval target
netex:AccessibilityInfoFacilityList  # XSD list container — not a retrieval target
netex:AccessibilityToolList  # XSD list container — not a retrieval target
netex:AccommodationAccessList  # XSD list container — not a retrieval target
netex:AccommodationFacilityList  # XSD list container — not a retrieval target
netex:AssistanceFacilityList  # XSD list container — not a retrieval target
netex:BookingProcessFacilityList  # XSD list container — not a retrieval target
netex:CarServiceFacilityList  # XSD list container — not a retrieval target
netex:CateringFacilityList  # XSD list container — not a retrieval target
netex:ClimateControlList  # XSD list container — not a retrieval target
netex:CouchetteFacilityList  # XSD list container — not a retrieval target
netex:EmergencyServiceList  # XSD list container — not a retrieval target
netex:FamilyFacilityList  # XSD list container — not a retrieval target
netex:LightingControlFacilityList  # XSD list container — not a retrieval target
netex:LuggageCarriageFacilityList  # XSD list container — not a retrieval target
netex:LuggageLockerFacilityList  # XSD list container — not a retrieval target
netex:LuggageServiceFacilityList  # XSD list container — not a retrieval target
netex:MedicalFacilityList  # XSD list container — not a retrieval target
netex:MobilityFacilityList  # XSD list container — not a retrieval target
netex:NuisanceFacilityList  # XSD list container — not a retrieval target
netex:ParkingFacilityList  # XSD list container — not a retrieval target
netex:PassengerCommsFacilityList  # XSD list container — not a retrieval target
netex:PassengerInformationFacilityList  # XSD list container — not a retrieval target
netex:ReservedSpaceFacilityList  # XSD list container — not a retrieval target
netex:RetailFacilityList  # XSD list container — not a retrieval target
netex:SafetyFacilityList  # XSD list container — not a retrieval target
netex:SanitaryFacilityList  # XSD list container — not a retrieval target
netex:SecurityList  # XSD list container — not a retrieval target
netex:ServiceReservationFacilityList  # XSD list container — not a retrieval target
netex:TicketingFacilityList  # XSD list container — not a retrieval target
netex:TicketingServiceFacilityList  # XSD list container — not a retrieval target
netex:TypeOfAccessRightAssignment  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfActivation  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfBatteryChemistry  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfConcession  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfCongestion  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfCustomerAccount  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfDeckEntrance  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfDeckEntranceUsage  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfDeckSpace  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfDeliveryVariant  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfDriverPermit  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfEntity  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfEquipment  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfFacility  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfFareContract  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfFareContractEntry  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfFareProduct  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfFareStructureElement  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfFareStructureFactor  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfFleet  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfFlexibleService  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfFrame  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfJourneyPattern  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfLine  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfLink  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfLinkSequence  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfLocatableSpot  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfMachineReadability  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfMediumAccessDevice  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfMobilityService  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfModeOfOperation  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfNotice  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfOperation  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfOrganisation  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfOrganisationPart  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfParking  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfPassengerInformationEquipment  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfPaymentMethod  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfPlace  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfPlug  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfPoint  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfPricingRule  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfProductCategory  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfProjection  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfProof  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfRetailDevice  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfRollingStock  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfSalesOfferPackage  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfSecurityList  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfService  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfServiceFeature  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfTariff  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfTransfer  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfTravelDocument  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfUsageParameter  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfValidity  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfValue  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfVersion  # Enumeration/classifier type — bulk-align or skip
netex:TypeOfWheelchair  # Enumeration/classifier type — bulk-align or skip
netex:UicProductCharacteristicList  # XSD list container — not a retrieval target
netex:VehicleAccessFacilityList  # XSD list container — not a retrieval target
netex:keyList  # XSD list container — not a retrieval target
```

### nits:DataArtifact (552 classes)

Suggested alignment: `rdfs:subClassOf nits:DataArtifact`

```turtle
# NETEX → nits:DataArtifact
netex:AcceptedDriverPermit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Access
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccessFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccessMode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccessRightInProduct
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccessRightParameterAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccessSummary
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccessVehicleEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccessibilityInfoFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccessibilityLimitation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccessibilityTool
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Accommodation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccommodationAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccommodationFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AccountableElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ActivatedEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ActivationAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ActualVehicleEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AdditionalDriverOption
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AllVehicleModes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AllowedLineDirection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AlternativeModeOfOperation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AlternativeQuayDescriptor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AmountOfPriceUnitProduct
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Assignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AssistanceBookingService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AssistanceFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AssistanceService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AudibleSignalsAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:AvailabilityCondition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:BatteryEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:BedEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:BerthFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Blacklist
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Block
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:BoardingPermission
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:BoardingPosition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:BookingArrangement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:BookingDebit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:BookingPolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:BookingProcessFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Branding
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Call
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Cancelling
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CappedDiscountRight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CappingRule
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CappingRulePrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CarModelProfile
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CarPoolingService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CarServiceFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CateringFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CateringService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Cell
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ChargingMoment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ChargingPolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ChauffeuredVehicleService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CheckConstraint
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CheckConstraintDelay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CheckConstraintThroughput
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ClassOfUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ClimateControl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CoachSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CommercialProfile
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CommercialProfileEligibility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CommonFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CommonSectionPointMember
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CommonVehicleService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CommunicationService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CompanionProfile
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ComplaintsService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ComplexFeature
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ComplexFeatureProjection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CompositeFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CompoundBlock
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CompoundTrain
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ConditionSummary
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Connection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Contact
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Contract
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ControlCentre
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ControllableElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ControllableElementInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ControllableElementPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ConventionalModeOfOperation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CouchetteFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Country
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CrewBase
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CrossingEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Customer
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerAccount
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerAccountSecurityListing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerAccountStatus
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerEligibility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerPaymentMeans
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerPurchasePackage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerPurchasePackageElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerPurchasePackageElementAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerPurchasePackagePrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerPurchaseParameterAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerSecurityListing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CustomerService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CycleModelProfile
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:CycleStorageEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DataManagedObject
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DataObjectCapabilitiesRequest
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DataObjectCapabilitiesResponse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DataObjectDelivery
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DataObjectPermissions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DataObjectRequest
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DataObjectServiceCapabilities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DataObjectSubscriptionRequest
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DataSource
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DatedSpecialService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Deck
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DeckComponent
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DeckLevel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DeckPlaceInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DeckPlan
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DeckPlanAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DeckSpaceCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DeckWindow
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DefaultConnection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DefaultDeadRunRunTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DefaultInterchange
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DeliveryVariant
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Delta
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DeltaValue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Department
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DestinationDisplay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DestinationDisplayVariant
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Direction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DiscountingRule
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DisplayAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DistanceMatrixElementPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DistributionAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DistributionChannel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DriverScheduleFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DriverTrip
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DriverTripTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Duty
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DutyPart
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DynamicDistanceMatrixElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DynamicStopAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:DynamicVehicleMeetingPointAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:EligibilityChangePolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:EmergencyService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:EmvCard
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:EntitlementGiven
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:EntitlementProduct
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:EntitlementRequired
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Entity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:EntityInVersion
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Equipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:EquipmentPosition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:EscalatorEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:EscalatorFreeAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Exchanging
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Extensions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FacilityRequirement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FacilitySet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FamilyFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareClass
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareContract
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareContractEntry
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareContractSecurityListing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareDebit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareDemandFactor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareElementInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareInterval
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FarePrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FarePriceFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareProductPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareProductSaleDebit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareQuotaFactor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareStructureElementInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareStructureElementPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareStructureFactor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareTableColumn
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareTableInContext
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareTableRow
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FareUnit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Fleet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FlexibleLine
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FlexibleLinkProperties
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FlexibleOperation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FlexiblePointProperties
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FlexibleServiceProperties
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FlexibleStopAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FrequencyOfUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FulfilmentMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FulfilmentMethodPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:FunicularSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Garage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GenderLimitation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GeneralFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GeneralFrameMember
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GeneralGroupOfEntities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GeneralSign
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GenericParameterAssignmentInContext
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GeographicalIntervalPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GeographicalStructureFactor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GeographicalUnit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GeographicalUnitPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupBookingFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupConstraintMember
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupMember
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupOfDistanceMatrixElements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupOfDistributionChannels
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupOfEntities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupOfLines
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupOfLinkSequences
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupOfPlaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupOfSalesOfferPackages
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupOfServices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupOfSites
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupOfTimebands
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupOfTimingLinks
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GroupTicket
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:GuideDogAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:HeadingSign
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:HelpPointEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:HireFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:HireService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:IndividualPassengerInfo
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:IndividualTraveller
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:InfrastructureFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:InfrastructureLinkRestriction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:InstalledEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Interchange
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:InterchangeRule
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:InterchangeRuleFilter
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:InterchangeRuleTiming
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Interchanging
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Layer
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LeftLuggageService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Level
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LevelAccessIntoVehicle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LiftCallEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LiftEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LiftFreeAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LightingControlFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LimitingRule
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LimitingRuleInContext
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LinkInLinkSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LinkProjection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LinkSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LinkSequenceProjection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LocalService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Locale
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LocatableSpot
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Log
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LogEntry
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LogicalDisplay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LostPropertyService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LuggageAllowance
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LuggageCarriageFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LuggageLockerEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LuggageLockerFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LuggageService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LuggageServiceFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LuggageSpot
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:LuggageSpotEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ManagementAgent
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MealFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MedicalFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MediumAccessDevice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MediumAccessDeviceSecurityListing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MediumApplicationInstance
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MeetingPointService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MeetingRestriction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MetroSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MinimumStay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MobileDevice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MobilityFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MobilityService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MobilityServiceFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ModeOfOperation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ModeRestrictionAssessment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MoneyFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MoneyService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:MonthValidityOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Notice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:NoticeAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:NuisanceFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:OffenceDebit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:OfferedTravelSpecification
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:OnboardStay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:OnlineService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:OpenTransportMode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:OperatingDay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:OperatingDepartment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:OperationalContext
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:OtherDebit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:OtherPlaceEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:OvertakingPossibility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Parking
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ParkingBay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ParkingBayCondition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ParkingBayStatus
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ParkingChargeBand
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ParkingComponent
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ParkingFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ParkingPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ParkingTariff
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerAccessibilityNeeds
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerAtStopTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerBeaconEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerBoardingPositionAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerCarryingRequirement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerCommsFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerInformationEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerInformationFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerSafetyEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerSpot
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerSpotAllocation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerStopAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerVehicleCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PassengerVehicleSpot
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PenaltyPolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PersonalModeOfOperation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PointInLinkSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PointOfInterest
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PointOfInterestClassification
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PointOfInterestClassificationHierarchy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PointOfInterestComponent
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PointProjection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PoolOfVehicles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PostalAddress
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PoweredTrain
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PreviousCall
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PriceUnit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PriceableObject
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PricingParameterSet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PricingService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Projection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PropertyOfDay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PurchaseWindow
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PurposeOfEquipmentProfile
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:PurposeOfGrouping
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:QualityStructureFactor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:QualityStructureFactorPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:QueueingEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RailSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RailwayElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RailwayJunction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RampEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RampFreeAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RechargingBay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RechargingEquipmentProfile
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RechargingPlan
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RechargingPointAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RechargingStation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RechargingStep
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ReliefOpportunity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RentalAvailability
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RentalOption
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RentalPenaltyPolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Replacing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RequestedTravelSpecification
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Reselling
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ReservedSpaceFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Reserving
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ResidentialQualification
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ResidentialQualificationEligibility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ResourceFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ResponsibilitySet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RestrictedManoeuvre
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RestrictedServiceFacilitySet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RetailConsortium
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RetailDevice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RetailDeviceSecurityListing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RetailFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RetailService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Review
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RoadAddress
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RoadElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RoadJunction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RoadVehicleMode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RollingStockInventory
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RollingStockItem
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RoughSurface
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RoundTrip
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Rounding
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RoundingStep
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RouteInstruction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Routing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:RubbishDisposalEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SafetyFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SaleDiscountRight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SalesNoticeAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SalesOfferPackageEntitlementGiven
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SalesOfferPackageEntitlementRequired
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SalesOfferPackagePrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SalesOfferPackageSubstitution
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SalesTransaction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SalesTransactionFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SanitaryEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SanitaryFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ScheduledOperation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SchematicMap
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ScopeOfTicket
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SeatEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SeatingEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SecurityListing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SelfDriveSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SensorEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SensorInSpot
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SeriesConstraint
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SeriesConstraintPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ShelterEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SignEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SimpleAvailabilityCondition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SimpleFeature
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SimpleValidityCondition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Site
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SiteComponent
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SiteConnection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SiteElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SiteEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SiteFacilitySet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SiteFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Smartcard
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SpecialService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SpecificParameterAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SpotAffinity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SpotColumn
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SpotEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SpotRow
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SpotSensor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SrsName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Staffing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:StairEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:StairFlight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:StairFreeAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:StaircaseEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:StandardFareTable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:StepFreeAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:StepLimit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Submode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Subscribing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Suitability
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:SupplementProduct
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Suspending
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TactileGuidanceAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TaxiRank
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TaxiService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TaxiServicePlaceAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TaxiStand
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TelecabinSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ThirdPartyProduct
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TicketValidatorEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TicketingEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TicketingFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TicketingService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TicketingServiceFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TimeDemandProfileMember
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TimeDemandTypeAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TimeIntervalPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TimeStructureFactor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TimeUnit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TimeUnitPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Timeband
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TopographicProjection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Trace
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TractiveRollingStockItem
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TrailingRollingStockItem
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Train
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TrainBlock
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TrainBlockPart
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TrainComponent
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TrainComponentLabelAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TrainComponentStopAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TrainElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TrainNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TrainSize
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TrainStopAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Transfer
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TransferDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TransferRestriction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Transferability
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TransportSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TravelAgent
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TravelDocument
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TravelDocumentSecurityListing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TravelSpecification
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TravelatorEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TripDebit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TrolleyStandEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:TurnaroundTimeLimitTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:UicProductCharacteristic
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:UicTrainRate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:UnpoweredTrain
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:UsageDiscountRight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:UsageParameter
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:UsageParameterPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:UserNeed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:UserProfileEligibility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ValidBetween
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ValidDuring
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ValidableElementPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ValidityCondition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ValidityParameterAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ValidityRuleParameter
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ValidityTrigger
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ValueSet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleAccessCredentialsAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleAccessFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleChargingEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleEquipmentProfile
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleEquipmentProfileMember
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleManoeuvringRequirement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleMeetingPointAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleMode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleModel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleModelProfile
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehiclePoolerProfile
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehiclePooling
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehiclePoolingDriverInfo
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehiclePoolingParkingBay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehiclePoolingPlaceAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehiclePoolingService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehiclePositionAlignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleQuayAlignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleReleaseEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleRental
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleRentalService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleScheduleFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleServicePart
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleServicePlaceAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleSharing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleSharingParkingBay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleSharingPlaceAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleSharingService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleStoppingPosition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleTypePreference
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VehicleTypeStopAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Version
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VersionFrame
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VersionedChild
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:VisualSignsAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:WaitingEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:WaitingRoomEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:WaterSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:WheelchairAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:WheelchairVehicleEquipment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:Whitelist
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:WireElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:WireJunction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:appliesOnOperatingDay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:onLine
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
```

### nits:Journey (52 classes)

Suggested alignment: `rdfs:subClassOf nits:Journey`

```turtle
# NETEX → nits:Journey
netex:CoupledJourney
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:CourseOfJourneys
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:DatedServiceJourney
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:DatedVehicleJourney
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:DeadRunJourneyPattern
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:DefaultServiceJourneyRunTime
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:FarePointInPattern
    rdfs:subClassOf nits:Journey .  # Ends with 'Pattern' (journey/service pattern)
netex:FlexibleRoute
    rdfs:subClassOf nits:Journey .  # Ends with 'Route'
netex:GroupOfSingleJourneys
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyAccounting
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyDesignator
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyHeadway
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyLayover
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyMeeting
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyPart
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyPartCouple
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyPartPosition
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyPatternHeadway
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyPatternLayover
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyPatternRunTime
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyPatternWaitTime
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyRunTime
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyTiming
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:JourneyWaitTime
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:LinkInJourneyPattern
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:MobilityJourneyFrame
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:NormalDatedVehicleJourney
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:PointInJourneyPattern
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:PointOnRoute
    rdfs:subClassOf nits:Journey .  # Ends with 'Route'
netex:PurposeOfJourneyPartition
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:ServiceJourneyInterchange
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:ServiceJourneyPatternInterchange
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:ServiceLinkInJourneyPattern
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:ServicePattern
    rdfs:subClassOf nits:Journey .  # Ends with 'Pattern' (journey/service pattern)
netex:SingleJourney
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:StopPointInJourneyPattern
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:TemplateServiceJourney
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:TemplateVehicleJourney
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:TimingLinkInJourneyPattern
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:TimingPattern
    rdfs:subClassOf nits:Journey .  # Ends with 'Pattern' (journey/service pattern)
netex:TimingPointInJourneyPattern
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:VehicleJourney
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:VehicleJourneyHeadway
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:VehicleJourneyLayover
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:VehicleJourneyRunTime
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:VehicleJourneySpotAllocation
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:VehicleJourneyStopAssignment
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:VehicleJourneyWaitTime
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:hasJourneyPattern
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:hasPointInJourneyPattern
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:hasServiceJourney
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:usesRoute
    rdfs:subClassOf nits:Journey .  # Ends with 'Route'
```

### nits:Line (2 classes)

Suggested alignment: `rdfs:subClassOf nits:Line`

```turtle
# NETEX → nits:Line
netex:LineSectionPointMember
    rdfs:subClassOf nits:Line .  # Starts with 'Line'
netex:LineShape
    rdfs:subClassOf nits:Line .  # Starts with 'Line'
```

### nits:Network (3 classes)

Suggested alignment: `rdfs:subClassOf nits:Network`

```turtle
# NETEX → nits:Network
netex:LineNetwork
    rdfs:subClassOf nits:Network .  # Contains 'Network'
netex:NetworkFrameTopic
    rdfs:subClassOf nits:Network .  # Contains 'Network'
netex:NetworkRestriction
    rdfs:subClassOf nits:Network .  # Contains 'Network'
```

### nits:Organisation (8 classes)

Suggested alignment: `rdfs:subClassOf nits:Organisation`

```turtle
# NETEX → nits:Organisation
netex:GeneralOrganisation
    rdfs:subClassOf nits:Organisation .  # Contains 'Organisation'
netex:OnlineServiceOperator
    rdfs:subClassOf nits:Organisation .  # Contains 'Operator'
netex:OrganisationPart
    rdfs:subClassOf nits:Organisation .  # Contains 'Organisation'
netex:OrganisationalUnit
    rdfs:subClassOf nits:Organisation .  # Contains 'Organisation'
netex:OtherOrganisation
    rdfs:subClassOf nits:Organisation .  # Contains 'Organisation'
netex:RelatedOrganisation
    rdfs:subClassOf nits:Organisation .  # Contains 'Organisation'
netex:ServicedOrganisation
    rdfs:subClassOf nits:Organisation .  # Contains 'Organisation'
netex:TransportOrganisation
    rdfs:subClassOf nits:Organisation .  # Contains 'Organisation'
```

### nits:RealTimeInformation (2 classes)

Suggested alignment: `rdfs:subClassOf nits:RealTimeInformation`

```turtle
# NETEX → nits:RealTimeInformation
netex:MonitoredCall
    rdfs:subClassOf nits:RealTimeInformation .  # Contains 'Monitored'
netex:MonitoredVehicleSharingParkingBay
    rdfs:subClassOf nits:RealTimeInformation .  # Contains 'Monitored'
```

### nits:Service (8 classes)

Suggested alignment: `rdfs:subClassOf nits:Service`

```turtle
# NETEX → nits:Service
netex:ServiceAccessRight
    rdfs:subClassOf nits:Service .  # Starts with 'Service'
netex:ServiceBookingArrangement
    rdfs:subClassOf nits:Service .  # Starts with 'Service'
netex:ServiceDesignator
    rdfs:subClassOf nits:Service .  # Starts with 'Service'
netex:ServiceExclusion
    rdfs:subClassOf nits:Service .  # Starts with 'Service'
netex:ServiceFacilitySet
    rdfs:subClassOf nits:Service .  # Starts with 'Service'
netex:ServiceFrame
    rdfs:subClassOf nits:Service .  # Starts with 'Service'
netex:ServiceReservationFacility
    rdfs:subClassOf nits:Service .  # Starts with 'Service'
netex:ServiceSite
    rdfs:subClassOf nits:Service .  # Starts with 'Service'
```

### nits:SpatialEntity (101 classes)

Suggested alignment: `rdfs:subClassOf nits:SpatialEntity`

```turtle
# NETEX → nits:SpatialEntity
netex:AccessSpace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Space'
netex:AccessZone
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:ActivationLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:ActivationPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:AddressablePlace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Place'
netex:AdministrativeZone
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:BeaconPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:CommonSection
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Section'
netex:DeckEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:DeckEntranceAssignment
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:DeckEntranceCouple
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:DeckEntranceUsage
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:DeckNavigationPath
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:DeckPathJunction
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:DeckPathLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:DeckSpace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Space'
netex:DeckVehicleEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:Entrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:EntranceEquipment
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:EntranceSensor
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:EquipmentPlace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Place'
netex:FareScheduledStopPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:FlexibleArea
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:FlexibleStopPlace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Place'
netex:GaragePoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:GeneralSection
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Section'
netex:GeneralZone
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:GenericNavigationPath
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:GenericPathJunction
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:GenericPathLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:HailAndRideArea
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:InfoLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:InfrastructureLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:InfrastructurePoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:LineSection
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Section'
netex:Link
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:MobilityServiceConstraintZone
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:NavigationPath
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:NavigationPathAssignment
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:OffSitePathLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:OnboardSpace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Space'
netex:OtherDeckEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:OtherDeckSpace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Space'
netex:ParkingEntranceForVehicles
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:ParkingPassengerEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:ParkingPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:PassengerEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:PassengerSpace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Space'
netex:PathInstruction
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:PathJunction
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:PathLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:PathLinkInSequence
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:Place
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Place'
netex:PlaceEquipment
    rdfs:subClassOf nits:SpatialEntity .  # Starts with 'Place'
netex:PlaceInSequence
    rdfs:subClassOf nits:SpatialEntity .  # Starts with 'Place'
netex:PlaceLighting
    rdfs:subClassOf nits:SpatialEntity .  # Starts with 'Place'
netex:PlaceSign
    rdfs:subClassOf nits:SpatialEntity .  # Starts with 'Place'
netex:Point
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:PointOfInterestEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:PointOfInterestSpace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Space'
netex:PointOfInterestVehicleEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:PointOnLineSection
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Section'
netex:PointOnLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:PointOnSection
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Section'
netex:ReliefPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:RouteLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:RoutePoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:RoutingConstraintZone
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:Section
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Section'
netex:SensorInEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:ServiceLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:SingleJourneyPath
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:SiteNavigationPath
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:SitePathJunction
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:SitePathLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:StartTimeAtStopPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:StopPlaceEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:StopPlaceSpace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Space'
netex:StopPlaceVehicleEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:TaxiParkingArea
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:TimingLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:TimingPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:TopographicPlace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Place'
netex:TrafficControlPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:TransportAdministrativeZone
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:VehicleEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:VehicleMeetingLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:VehicleMeetingPlace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Place'
netex:VehicleMeetingPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:VehicleMeetingPointInPath
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:VehiclePoolingMeetingPlace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Place'
netex:VehiclePoolingParkingArea
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:VehicleSharingParkingArea
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:VehicleStoppingPlace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Place'
netex:VehicleTypeAtPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:VehicleTypeZoneRestriction
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:Zone
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:ZoneInSeries
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:ZoneProjection
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:inStopPlace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Place'
netex:servesScheduledStopPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
```

### nits:Stop (3 classes)

Suggested alignment: `rdfs:subClassOf nits:Stop`

```turtle
# NETEX → nits:Stop
netex:FlexibleQuay
    rdfs:subClassOf nits:Stop .  # Ends with 'Quay'
netex:StopAssignment
    rdfs:subClassOf nits:Stop .  # Starts with 'Stop'
netex:StopPlaceComponent
    rdfs:subClassOf nits:Stop .  # Starts with 'Stop'
```

### nits:TemporalEntity (3 classes)

Suggested alignment: `rdfs:subClassOf nits:TemporalEntity`

```turtle
# NETEX → nits:TemporalEntity
netex:DayTypeAssignment
    rdfs:subClassOf nits:TemporalEntity .  # DayType scheduling concept
netex:ServiceCalendarFrame
    rdfs:subClassOf nits:TemporalEntity .  # Contains 'Calendar'
netex:hasDayTypeAssignment
    rdfs:subClassOf nits:TemporalEntity .  # DayType scheduling concept
```

### nits:Timetable (3 classes)

Suggested alignment: `rdfs:subClassOf nits:Timetable`

```turtle
# NETEX → nits:Timetable
netex:TimetableFrame
    rdfs:subClassOf nits:Timetable .  # Contains 'Timetable'
netex:TimetabledPassingTime
    rdfs:subClassOf nits:Timetable .  # Contains 'Timetable'
netex:hasTimetabledPassingTime
    rdfs:subClassOf nits:Timetable .  # Contains 'Timetable'
```

---

## Full proposed TTL block (all non-skip classes)

```turtle
# nits:DataArtifact
netex:AcceptedDriverPermit
    rdfs:subClassOf nits:DataArtifact .

netex:Access
    rdfs:subClassOf nits:DataArtifact .

netex:AccessFacility
    rdfs:subClassOf nits:DataArtifact .

netex:AccessMode
    rdfs:subClassOf nits:DataArtifact .

netex:AccessRightInProduct
    rdfs:subClassOf nits:DataArtifact .

netex:AccessRightParameterAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:AccessSummary
    rdfs:subClassOf nits:DataArtifact .

netex:AccessVehicleEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:AccessibilityInfoFacility
    rdfs:subClassOf nits:DataArtifact .

netex:AccessibilityLimitation
    rdfs:subClassOf nits:DataArtifact .

netex:AccessibilityTool
    rdfs:subClassOf nits:DataArtifact .

netex:Accommodation
    rdfs:subClassOf nits:DataArtifact .

netex:AccommodationAccess
    rdfs:subClassOf nits:DataArtifact .

netex:AccommodationFacility
    rdfs:subClassOf nits:DataArtifact .

netex:AccountableElement
    rdfs:subClassOf nits:DataArtifact .

netex:ActivatedEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:ActivationAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:ActualVehicleEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:AdditionalDriverOption
    rdfs:subClassOf nits:DataArtifact .

netex:AllVehicleModes
    rdfs:subClassOf nits:DataArtifact .

netex:AllowedLineDirection
    rdfs:subClassOf nits:DataArtifact .

netex:AlternativeModeOfOperation
    rdfs:subClassOf nits:DataArtifact .

netex:AlternativeQuayDescriptor
    rdfs:subClassOf nits:DataArtifact .

netex:AmountOfPriceUnitProduct
    rdfs:subClassOf nits:DataArtifact .

netex:Assignment
    rdfs:subClassOf nits:DataArtifact .

netex:AssistanceBookingService
    rdfs:subClassOf nits:DataArtifact .

netex:AssistanceFacility
    rdfs:subClassOf nits:DataArtifact .

netex:AssistanceService
    rdfs:subClassOf nits:DataArtifact .

netex:AudibleSignalsAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:AvailabilityCondition
    rdfs:subClassOf nits:DataArtifact .

netex:BatteryEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:BedEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:BerthFacility
    rdfs:subClassOf nits:DataArtifact .

netex:Blacklist
    rdfs:subClassOf nits:DataArtifact .

netex:Block
    rdfs:subClassOf nits:DataArtifact .

netex:BoardingPermission
    rdfs:subClassOf nits:DataArtifact .

netex:BoardingPosition
    rdfs:subClassOf nits:DataArtifact .

netex:BookingArrangement
    rdfs:subClassOf nits:DataArtifact .

netex:BookingDebit
    rdfs:subClassOf nits:DataArtifact .

netex:BookingPolicy
    rdfs:subClassOf nits:DataArtifact .

netex:BookingProcessFacility
    rdfs:subClassOf nits:DataArtifact .

netex:Branding
    rdfs:subClassOf nits:DataArtifact .

netex:Call
    rdfs:subClassOf nits:DataArtifact .

netex:Cancelling
    rdfs:subClassOf nits:DataArtifact .

netex:CappedDiscountRight
    rdfs:subClassOf nits:DataArtifact .

netex:CappingRule
    rdfs:subClassOf nits:DataArtifact .

netex:CappingRulePrice
    rdfs:subClassOf nits:DataArtifact .

netex:CarModelProfile
    rdfs:subClassOf nits:DataArtifact .

netex:CarPoolingService
    rdfs:subClassOf nits:DataArtifact .

netex:CarServiceFacility
    rdfs:subClassOf nits:DataArtifact .

netex:CateringFacility
    rdfs:subClassOf nits:DataArtifact .

netex:CateringService
    rdfs:subClassOf nits:DataArtifact .

netex:Cell
    rdfs:subClassOf nits:DataArtifact .

netex:ChargingMoment
    rdfs:subClassOf nits:DataArtifact .

netex:ChargingPolicy
    rdfs:subClassOf nits:DataArtifact .

netex:ChauffeuredVehicleService
    rdfs:subClassOf nits:DataArtifact .

netex:CheckConstraint
    rdfs:subClassOf nits:DataArtifact .

netex:CheckConstraintDelay
    rdfs:subClassOf nits:DataArtifact .

netex:CheckConstraintThroughput
    rdfs:subClassOf nits:DataArtifact .

netex:ClassOfUse
    rdfs:subClassOf nits:DataArtifact .

netex:ClimateControl
    rdfs:subClassOf nits:DataArtifact .

netex:CoachSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:CommercialProfile
    rdfs:subClassOf nits:DataArtifact .

netex:CommercialProfileEligibility
    rdfs:subClassOf nits:DataArtifact .

netex:CommonFrame
    rdfs:subClassOf nits:DataArtifact .

netex:CommonSectionPointMember
    rdfs:subClassOf nits:DataArtifact .

netex:CommonVehicleService
    rdfs:subClassOf nits:DataArtifact .

netex:CommunicationService
    rdfs:subClassOf nits:DataArtifact .

netex:CompanionProfile
    rdfs:subClassOf nits:DataArtifact .

netex:ComplaintsService
    rdfs:subClassOf nits:DataArtifact .

netex:ComplexFeature
    rdfs:subClassOf nits:DataArtifact .

netex:ComplexFeatureProjection
    rdfs:subClassOf nits:DataArtifact .

netex:CompositeFrame
    rdfs:subClassOf nits:DataArtifact .

netex:CompoundBlock
    rdfs:subClassOf nits:DataArtifact .

netex:CompoundTrain
    rdfs:subClassOf nits:DataArtifact .

netex:ConditionSummary
    rdfs:subClassOf nits:DataArtifact .

netex:Connection
    rdfs:subClassOf nits:DataArtifact .

netex:Contact
    rdfs:subClassOf nits:DataArtifact .

netex:Contract
    rdfs:subClassOf nits:DataArtifact .

netex:ControlCentre
    rdfs:subClassOf nits:DataArtifact .

netex:ControllableElement
    rdfs:subClassOf nits:DataArtifact .

netex:ControllableElementInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:ControllableElementPrice
    rdfs:subClassOf nits:DataArtifact .

netex:ConventionalModeOfOperation
    rdfs:subClassOf nits:DataArtifact .

netex:CouchetteFacility
    rdfs:subClassOf nits:DataArtifact .

netex:Country
    rdfs:subClassOf nits:DataArtifact .

netex:CrewBase
    rdfs:subClassOf nits:DataArtifact .

netex:CrossingEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:Customer
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerAccount
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerAccountSecurityListing
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerAccountStatus
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerEligibility
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerPaymentMeans
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerPurchasePackage
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerPurchasePackageElement
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerPurchasePackageElementAccess
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerPurchasePackagePrice
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerPurchaseParameterAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerSecurityListing
    rdfs:subClassOf nits:DataArtifact .

netex:CustomerService
    rdfs:subClassOf nits:DataArtifact .

netex:CycleModelProfile
    rdfs:subClassOf nits:DataArtifact .

netex:CycleStorageEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:DataManagedObject
    rdfs:subClassOf nits:DataArtifact .

netex:DataObjectCapabilitiesRequest
    rdfs:subClassOf nits:DataArtifact .

netex:DataObjectCapabilitiesResponse
    rdfs:subClassOf nits:DataArtifact .

netex:DataObjectDelivery
    rdfs:subClassOf nits:DataArtifact .

netex:DataObjectPermissions
    rdfs:subClassOf nits:DataArtifact .

netex:DataObjectRequest
    rdfs:subClassOf nits:DataArtifact .

netex:DataObjectServiceCapabilities
    rdfs:subClassOf nits:DataArtifact .

netex:DataObjectSubscriptionRequest
    rdfs:subClassOf nits:DataArtifact .

netex:DataSource
    rdfs:subClassOf nits:DataArtifact .

netex:DatedSpecialService
    rdfs:subClassOf nits:DataArtifact .

netex:Deck
    rdfs:subClassOf nits:DataArtifact .

netex:DeckComponent
    rdfs:subClassOf nits:DataArtifact .

netex:DeckLevel
    rdfs:subClassOf nits:DataArtifact .

netex:DeckPlaceInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:DeckPlan
    rdfs:subClassOf nits:DataArtifact .

netex:DeckPlanAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:DeckSpaceCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:DeckWindow
    rdfs:subClassOf nits:DataArtifact .

netex:DefaultConnection
    rdfs:subClassOf nits:DataArtifact .

netex:DefaultDeadRunRunTime
    rdfs:subClassOf nits:DataArtifact .

netex:DefaultInterchange
    rdfs:subClassOf nits:DataArtifact .

netex:DeliveryVariant
    rdfs:subClassOf nits:DataArtifact .

netex:Delta
    rdfs:subClassOf nits:DataArtifact .

netex:DeltaValue
    rdfs:subClassOf nits:DataArtifact .

netex:Department
    rdfs:subClassOf nits:DataArtifact .

netex:DestinationDisplay
    rdfs:subClassOf nits:DataArtifact .

netex:DestinationDisplayVariant
    rdfs:subClassOf nits:DataArtifact .

netex:Direction
    rdfs:subClassOf nits:DataArtifact .

netex:DiscountingRule
    rdfs:subClassOf nits:DataArtifact .

netex:DisplayAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:DistanceMatrixElementPrice
    rdfs:subClassOf nits:DataArtifact .

netex:DistributionAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:DistributionChannel
    rdfs:subClassOf nits:DataArtifact .

netex:DriverScheduleFrame
    rdfs:subClassOf nits:DataArtifact .

netex:DriverTrip
    rdfs:subClassOf nits:DataArtifact .

netex:DriverTripTime
    rdfs:subClassOf nits:DataArtifact .

netex:Duty
    rdfs:subClassOf nits:DataArtifact .

netex:DutyPart
    rdfs:subClassOf nits:DataArtifact .

netex:DynamicDistanceMatrixElement
    rdfs:subClassOf nits:DataArtifact .

netex:DynamicStopAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:DynamicVehicleMeetingPointAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:EligibilityChangePolicy
    rdfs:subClassOf nits:DataArtifact .

netex:EmergencyService
    rdfs:subClassOf nits:DataArtifact .

netex:EmvCard
    rdfs:subClassOf nits:DataArtifact .

netex:EntitlementGiven
    rdfs:subClassOf nits:DataArtifact .

netex:EntitlementProduct
    rdfs:subClassOf nits:DataArtifact .

netex:EntitlementRequired
    rdfs:subClassOf nits:DataArtifact .

netex:Entity
    rdfs:subClassOf nits:DataArtifact .

netex:EntityInVersion
    rdfs:subClassOf nits:DataArtifact .

netex:Equipment
    rdfs:subClassOf nits:DataArtifact .

netex:EquipmentPosition
    rdfs:subClassOf nits:DataArtifact .

netex:EscalatorEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:EscalatorFreeAccess
    rdfs:subClassOf nits:DataArtifact .

netex:Exchanging
    rdfs:subClassOf nits:DataArtifact .

netex:Extensions
    rdfs:subClassOf nits:DataArtifact .

netex:FacilityRequirement
    rdfs:subClassOf nits:DataArtifact .

netex:FacilitySet
    rdfs:subClassOf nits:DataArtifact .

netex:FamilyFacility
    rdfs:subClassOf nits:DataArtifact .

netex:FareClass
    rdfs:subClassOf nits:DataArtifact .

netex:FareContract
    rdfs:subClassOf nits:DataArtifact .

netex:FareContractEntry
    rdfs:subClassOf nits:DataArtifact .

netex:FareContractSecurityListing
    rdfs:subClassOf nits:DataArtifact .

netex:FareDebit
    rdfs:subClassOf nits:DataArtifact .

netex:FareDemandFactor
    rdfs:subClassOf nits:DataArtifact .

netex:FareElementInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:FareInterval
    rdfs:subClassOf nits:DataArtifact .

netex:FarePrice
    rdfs:subClassOf nits:DataArtifact .

netex:FarePriceFrame
    rdfs:subClassOf nits:DataArtifact .

netex:FareProductPrice
    rdfs:subClassOf nits:DataArtifact .

netex:FareProductSaleDebit
    rdfs:subClassOf nits:DataArtifact .

netex:FareQuotaFactor
    rdfs:subClassOf nits:DataArtifact .

netex:FareStructureElementInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:FareStructureElementPrice
    rdfs:subClassOf nits:DataArtifact .

netex:FareStructureFactor
    rdfs:subClassOf nits:DataArtifact .

netex:FareTableColumn
    rdfs:subClassOf nits:DataArtifact .

netex:FareTableInContext
    rdfs:subClassOf nits:DataArtifact .

netex:FareTableRow
    rdfs:subClassOf nits:DataArtifact .

netex:FareUnit
    rdfs:subClassOf nits:DataArtifact .

netex:Fleet
    rdfs:subClassOf nits:DataArtifact .

netex:FlexibleLine
    rdfs:subClassOf nits:DataArtifact .

netex:FlexibleLinkProperties
    rdfs:subClassOf nits:DataArtifact .

netex:FlexibleOperation
    rdfs:subClassOf nits:DataArtifact .

netex:FlexiblePointProperties
    rdfs:subClassOf nits:DataArtifact .

netex:FlexibleServiceProperties
    rdfs:subClassOf nits:DataArtifact .

netex:FlexibleStopAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:FrequencyOfUse
    rdfs:subClassOf nits:DataArtifact .

netex:FulfilmentMethod
    rdfs:subClassOf nits:DataArtifact .

netex:FulfilmentMethodPrice
    rdfs:subClassOf nits:DataArtifact .

netex:FunicularSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:Garage
    rdfs:subClassOf nits:DataArtifact .

netex:GenderLimitation
    rdfs:subClassOf nits:DataArtifact .

netex:GeneralFrame
    rdfs:subClassOf nits:DataArtifact .

netex:GeneralFrameMember
    rdfs:subClassOf nits:DataArtifact .

netex:GeneralGroupOfEntities
    rdfs:subClassOf nits:DataArtifact .

netex:GeneralSign
    rdfs:subClassOf nits:DataArtifact .

netex:GenericParameterAssignmentInContext
    rdfs:subClassOf nits:DataArtifact .

netex:GeographicalIntervalPrice
    rdfs:subClassOf nits:DataArtifact .

netex:GeographicalStructureFactor
    rdfs:subClassOf nits:DataArtifact .

netex:GeographicalUnit
    rdfs:subClassOf nits:DataArtifact .

netex:GeographicalUnitPrice
    rdfs:subClassOf nits:DataArtifact .

netex:GroupBookingFacility
    rdfs:subClassOf nits:DataArtifact .

netex:GroupConstraintMember
    rdfs:subClassOf nits:DataArtifact .

netex:GroupMember
    rdfs:subClassOf nits:DataArtifact .

netex:GroupOfDistanceMatrixElements
    rdfs:subClassOf nits:DataArtifact .

netex:GroupOfDistributionChannels
    rdfs:subClassOf nits:DataArtifact .

netex:GroupOfEntities
    rdfs:subClassOf nits:DataArtifact .

netex:GroupOfLines
    rdfs:subClassOf nits:DataArtifact .

netex:GroupOfLinkSequences
    rdfs:subClassOf nits:DataArtifact .

netex:GroupOfPlaces
    rdfs:subClassOf nits:DataArtifact .

netex:GroupOfSalesOfferPackages
    rdfs:subClassOf nits:DataArtifact .

netex:GroupOfServices
    rdfs:subClassOf nits:DataArtifact .

netex:GroupOfSites
    rdfs:subClassOf nits:DataArtifact .

netex:GroupOfTimebands
    rdfs:subClassOf nits:DataArtifact .

netex:GroupOfTimingLinks
    rdfs:subClassOf nits:DataArtifact .

netex:GroupTicket
    rdfs:subClassOf nits:DataArtifact .

netex:GuideDogAccess
    rdfs:subClassOf nits:DataArtifact .

netex:HeadingSign
    rdfs:subClassOf nits:DataArtifact .

netex:HelpPointEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:HireFacility
    rdfs:subClassOf nits:DataArtifact .

netex:HireService
    rdfs:subClassOf nits:DataArtifact .

netex:IndividualPassengerInfo
    rdfs:subClassOf nits:DataArtifact .

netex:IndividualTraveller
    rdfs:subClassOf nits:DataArtifact .

netex:InfrastructureFrame
    rdfs:subClassOf nits:DataArtifact .

netex:InfrastructureLinkRestriction
    rdfs:subClassOf nits:DataArtifact .

netex:InstalledEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:Interchange
    rdfs:subClassOf nits:DataArtifact .

netex:InterchangeRule
    rdfs:subClassOf nits:DataArtifact .

netex:InterchangeRuleFilter
    rdfs:subClassOf nits:DataArtifact .

netex:InterchangeRuleTiming
    rdfs:subClassOf nits:DataArtifact .

netex:Interchanging
    rdfs:subClassOf nits:DataArtifact .

netex:Layer
    rdfs:subClassOf nits:DataArtifact .

netex:LeftLuggageService
    rdfs:subClassOf nits:DataArtifact .

netex:Level
    rdfs:subClassOf nits:DataArtifact .

netex:LevelAccessIntoVehicle
    rdfs:subClassOf nits:DataArtifact .

netex:LiftCallEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:LiftEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:LiftFreeAccess
    rdfs:subClassOf nits:DataArtifact .

netex:LightingControlFacility
    rdfs:subClassOf nits:DataArtifact .

netex:LimitingRule
    rdfs:subClassOf nits:DataArtifact .

netex:LimitingRuleInContext
    rdfs:subClassOf nits:DataArtifact .

netex:LinkInLinkSequence
    rdfs:subClassOf nits:DataArtifact .

netex:LinkProjection
    rdfs:subClassOf nits:DataArtifact .

netex:LinkSequence
    rdfs:subClassOf nits:DataArtifact .

netex:LinkSequenceProjection
    rdfs:subClassOf nits:DataArtifact .

netex:LocalService
    rdfs:subClassOf nits:DataArtifact .

netex:Locale
    rdfs:subClassOf nits:DataArtifact .

netex:LocatableSpot
    rdfs:subClassOf nits:DataArtifact .

netex:Log
    rdfs:subClassOf nits:DataArtifact .

netex:LogEntry
    rdfs:subClassOf nits:DataArtifact .

netex:LogicalDisplay
    rdfs:subClassOf nits:DataArtifact .

netex:LostPropertyService
    rdfs:subClassOf nits:DataArtifact .

netex:LuggageAllowance
    rdfs:subClassOf nits:DataArtifact .

netex:LuggageCarriageFacility
    rdfs:subClassOf nits:DataArtifact .

netex:LuggageLockerEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:LuggageLockerFacility
    rdfs:subClassOf nits:DataArtifact .

netex:LuggageService
    rdfs:subClassOf nits:DataArtifact .

netex:LuggageServiceFacility
    rdfs:subClassOf nits:DataArtifact .

netex:LuggageSpot
    rdfs:subClassOf nits:DataArtifact .

netex:LuggageSpotEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:ManagementAgent
    rdfs:subClassOf nits:DataArtifact .

netex:MealFacility
    rdfs:subClassOf nits:DataArtifact .

netex:MedicalFacility
    rdfs:subClassOf nits:DataArtifact .

netex:MediumAccessDevice
    rdfs:subClassOf nits:DataArtifact .

netex:MediumAccessDeviceSecurityListing
    rdfs:subClassOf nits:DataArtifact .

netex:MediumApplicationInstance
    rdfs:subClassOf nits:DataArtifact .

netex:MeetingPointService
    rdfs:subClassOf nits:DataArtifact .

netex:MeetingRestriction
    rdfs:subClassOf nits:DataArtifact .

netex:MetroSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:MinimumStay
    rdfs:subClassOf nits:DataArtifact .

netex:MobileDevice
    rdfs:subClassOf nits:DataArtifact .

netex:MobilityFacility
    rdfs:subClassOf nits:DataArtifact .

netex:MobilityService
    rdfs:subClassOf nits:DataArtifact .

netex:MobilityServiceFrame
    rdfs:subClassOf nits:DataArtifact .

netex:ModeOfOperation
    rdfs:subClassOf nits:DataArtifact .

netex:ModeRestrictionAssessment
    rdfs:subClassOf nits:DataArtifact .

netex:MoneyFacility
    rdfs:subClassOf nits:DataArtifact .

netex:MoneyService
    rdfs:subClassOf nits:DataArtifact .

netex:MonthValidityOffset
    rdfs:subClassOf nits:DataArtifact .

netex:Notice
    rdfs:subClassOf nits:DataArtifact .

netex:NoticeAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:NuisanceFacility
    rdfs:subClassOf nits:DataArtifact .

netex:OffenceDebit
    rdfs:subClassOf nits:DataArtifact .

netex:OfferedTravelSpecification
    rdfs:subClassOf nits:DataArtifact .

netex:OnboardStay
    rdfs:subClassOf nits:DataArtifact .

netex:OnlineService
    rdfs:subClassOf nits:DataArtifact .

netex:OpenTransportMode
    rdfs:subClassOf nits:DataArtifact .

netex:OperatingDay
    rdfs:subClassOf nits:DataArtifact .

netex:OperatingDepartment
    rdfs:subClassOf nits:DataArtifact .

netex:OperationalContext
    rdfs:subClassOf nits:DataArtifact .

netex:OtherDebit
    rdfs:subClassOf nits:DataArtifact .

netex:OtherPlaceEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:OvertakingPossibility
    rdfs:subClassOf nits:DataArtifact .

netex:Parking
    rdfs:subClassOf nits:DataArtifact .

netex:ParkingBay
    rdfs:subClassOf nits:DataArtifact .

netex:ParkingBayCondition
    rdfs:subClassOf nits:DataArtifact .

netex:ParkingBayStatus
    rdfs:subClassOf nits:DataArtifact .

netex:ParkingChargeBand
    rdfs:subClassOf nits:DataArtifact .

netex:ParkingComponent
    rdfs:subClassOf nits:DataArtifact .

netex:ParkingFacility
    rdfs:subClassOf nits:DataArtifact .

netex:ParkingPrice
    rdfs:subClassOf nits:DataArtifact .

netex:ParkingTariff
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerAccessibilityNeeds
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerAtStopTime
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerBeaconEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerBoardingPositionAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerCarryingRequirement
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerCommsFacility
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerInformationEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerInformationFacility
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerSafetyEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerSpot
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerSpotAllocation
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerStopAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerVehicleCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:PassengerVehicleSpot
    rdfs:subClassOf nits:DataArtifact .

netex:PenaltyPolicy
    rdfs:subClassOf nits:DataArtifact .

netex:PersonalModeOfOperation
    rdfs:subClassOf nits:DataArtifact .

netex:PointInLinkSequence
    rdfs:subClassOf nits:DataArtifact .

netex:PointOfInterest
    rdfs:subClassOf nits:DataArtifact .

netex:PointOfInterestClassification
    rdfs:subClassOf nits:DataArtifact .

netex:PointOfInterestClassificationHierarchy
    rdfs:subClassOf nits:DataArtifact .

netex:PointOfInterestComponent
    rdfs:subClassOf nits:DataArtifact .

netex:PointProjection
    rdfs:subClassOf nits:DataArtifact .

netex:PoolOfVehicles
    rdfs:subClassOf nits:DataArtifact .

netex:PostalAddress
    rdfs:subClassOf nits:DataArtifact .

netex:PoweredTrain
    rdfs:subClassOf nits:DataArtifact .

netex:PreviousCall
    rdfs:subClassOf nits:DataArtifact .

netex:PriceUnit
    rdfs:subClassOf nits:DataArtifact .

netex:PriceableObject
    rdfs:subClassOf nits:DataArtifact .

netex:PricingParameterSet
    rdfs:subClassOf nits:DataArtifact .

netex:PricingService
    rdfs:subClassOf nits:DataArtifact .

netex:Projection
    rdfs:subClassOf nits:DataArtifact .

netex:PropertyOfDay
    rdfs:subClassOf nits:DataArtifact .

netex:PurchaseWindow
    rdfs:subClassOf nits:DataArtifact .

netex:PurposeOfEquipmentProfile
    rdfs:subClassOf nits:DataArtifact .

netex:PurposeOfGrouping
    rdfs:subClassOf nits:DataArtifact .

netex:QualityStructureFactor
    rdfs:subClassOf nits:DataArtifact .

netex:QualityStructureFactorPrice
    rdfs:subClassOf nits:DataArtifact .

netex:QueueingEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:RailSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:RailwayElement
    rdfs:subClassOf nits:DataArtifact .

netex:RailwayJunction
    rdfs:subClassOf nits:DataArtifact .

netex:RampEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:RampFreeAccess
    rdfs:subClassOf nits:DataArtifact .

netex:RechargingBay
    rdfs:subClassOf nits:DataArtifact .

netex:RechargingEquipmentProfile
    rdfs:subClassOf nits:DataArtifact .

netex:RechargingPlan
    rdfs:subClassOf nits:DataArtifact .

netex:RechargingPointAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:RechargingStation
    rdfs:subClassOf nits:DataArtifact .

netex:RechargingStep
    rdfs:subClassOf nits:DataArtifact .

netex:ReliefOpportunity
    rdfs:subClassOf nits:DataArtifact .

netex:RentalAvailability
    rdfs:subClassOf nits:DataArtifact .

netex:RentalOption
    rdfs:subClassOf nits:DataArtifact .

netex:RentalPenaltyPolicy
    rdfs:subClassOf nits:DataArtifact .

netex:Replacing
    rdfs:subClassOf nits:DataArtifact .

netex:RequestedTravelSpecification
    rdfs:subClassOf nits:DataArtifact .

netex:Reselling
    rdfs:subClassOf nits:DataArtifact .

netex:ReservedSpaceFacility
    rdfs:subClassOf nits:DataArtifact .

netex:Reserving
    rdfs:subClassOf nits:DataArtifact .

netex:ResidentialQualification
    rdfs:subClassOf nits:DataArtifact .

netex:ResidentialQualificationEligibility
    rdfs:subClassOf nits:DataArtifact .

netex:ResourceFrame
    rdfs:subClassOf nits:DataArtifact .

netex:ResponsibilitySet
    rdfs:subClassOf nits:DataArtifact .

netex:RestrictedManoeuvre
    rdfs:subClassOf nits:DataArtifact .

netex:RestrictedServiceFacilitySet
    rdfs:subClassOf nits:DataArtifact .

netex:RetailConsortium
    rdfs:subClassOf nits:DataArtifact .

netex:RetailDevice
    rdfs:subClassOf nits:DataArtifact .

netex:RetailDeviceSecurityListing
    rdfs:subClassOf nits:DataArtifact .

netex:RetailFacility
    rdfs:subClassOf nits:DataArtifact .

netex:RetailService
    rdfs:subClassOf nits:DataArtifact .

netex:Review
    rdfs:subClassOf nits:DataArtifact .

netex:RoadAddress
    rdfs:subClassOf nits:DataArtifact .

netex:RoadElement
    rdfs:subClassOf nits:DataArtifact .

netex:RoadJunction
    rdfs:subClassOf nits:DataArtifact .

netex:RoadVehicleMode
    rdfs:subClassOf nits:DataArtifact .

netex:RollingStockInventory
    rdfs:subClassOf nits:DataArtifact .

netex:RollingStockItem
    rdfs:subClassOf nits:DataArtifact .

netex:RoughSurface
    rdfs:subClassOf nits:DataArtifact .

netex:RoundTrip
    rdfs:subClassOf nits:DataArtifact .

netex:Rounding
    rdfs:subClassOf nits:DataArtifact .

netex:RoundingStep
    rdfs:subClassOf nits:DataArtifact .

netex:RouteInstruction
    rdfs:subClassOf nits:DataArtifact .

netex:Routing
    rdfs:subClassOf nits:DataArtifact .

netex:RubbishDisposalEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:SafetyFacility
    rdfs:subClassOf nits:DataArtifact .

netex:SaleDiscountRight
    rdfs:subClassOf nits:DataArtifact .

netex:SalesNoticeAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:SalesOfferPackageEntitlementGiven
    rdfs:subClassOf nits:DataArtifact .

netex:SalesOfferPackageEntitlementRequired
    rdfs:subClassOf nits:DataArtifact .

netex:SalesOfferPackagePrice
    rdfs:subClassOf nits:DataArtifact .

netex:SalesOfferPackageSubstitution
    rdfs:subClassOf nits:DataArtifact .

netex:SalesTransaction
    rdfs:subClassOf nits:DataArtifact .

netex:SalesTransactionFrame
    rdfs:subClassOf nits:DataArtifact .

netex:SanitaryEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:SanitaryFacility
    rdfs:subClassOf nits:DataArtifact .

netex:ScheduledOperation
    rdfs:subClassOf nits:DataArtifact .

netex:SchematicMap
    rdfs:subClassOf nits:DataArtifact .

netex:ScopeOfTicket
    rdfs:subClassOf nits:DataArtifact .

netex:SeatEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:SeatingEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:SecurityListing
    rdfs:subClassOf nits:DataArtifact .

netex:SelfDriveSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:SensorEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:SensorInSpot
    rdfs:subClassOf nits:DataArtifact .

netex:SeriesConstraint
    rdfs:subClassOf nits:DataArtifact .

netex:SeriesConstraintPrice
    rdfs:subClassOf nits:DataArtifact .

netex:ShelterEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:SignEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:SimpleAvailabilityCondition
    rdfs:subClassOf nits:DataArtifact .

netex:SimpleFeature
    rdfs:subClassOf nits:DataArtifact .

netex:SimpleValidityCondition
    rdfs:subClassOf nits:DataArtifact .

netex:Site
    rdfs:subClassOf nits:DataArtifact .

netex:SiteComponent
    rdfs:subClassOf nits:DataArtifact .

netex:SiteConnection
    rdfs:subClassOf nits:DataArtifact .

netex:SiteElement
    rdfs:subClassOf nits:DataArtifact .

netex:SiteEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:SiteFacilitySet
    rdfs:subClassOf nits:DataArtifact .

netex:SiteFrame
    rdfs:subClassOf nits:DataArtifact .

netex:Smartcard
    rdfs:subClassOf nits:DataArtifact .

netex:SpecialService
    rdfs:subClassOf nits:DataArtifact .

netex:SpecificParameterAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:SpotAffinity
    rdfs:subClassOf nits:DataArtifact .

netex:SpotColumn
    rdfs:subClassOf nits:DataArtifact .

netex:SpotEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:SpotRow
    rdfs:subClassOf nits:DataArtifact .

netex:SpotSensor
    rdfs:subClassOf nits:DataArtifact .

netex:SrsName
    rdfs:subClassOf nits:DataArtifact .

netex:Staffing
    rdfs:subClassOf nits:DataArtifact .

netex:StairEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:StairFlight
    rdfs:subClassOf nits:DataArtifact .

netex:StairFreeAccess
    rdfs:subClassOf nits:DataArtifact .

netex:StaircaseEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:StandardFareTable
    rdfs:subClassOf nits:DataArtifact .

netex:StepFreeAccess
    rdfs:subClassOf nits:DataArtifact .

netex:StepLimit
    rdfs:subClassOf nits:DataArtifact .

netex:Submode
    rdfs:subClassOf nits:DataArtifact .

netex:Subscribing
    rdfs:subClassOf nits:DataArtifact .

netex:Suitability
    rdfs:subClassOf nits:DataArtifact .

netex:SupplementProduct
    rdfs:subClassOf nits:DataArtifact .

netex:Suspending
    rdfs:subClassOf nits:DataArtifact .

netex:TactileGuidanceAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:TaxiRank
    rdfs:subClassOf nits:DataArtifact .

netex:TaxiService
    rdfs:subClassOf nits:DataArtifact .

netex:TaxiServicePlaceAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:TaxiStand
    rdfs:subClassOf nits:DataArtifact .

netex:TelecabinSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:ThirdPartyProduct
    rdfs:subClassOf nits:DataArtifact .

netex:TicketValidatorEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:TicketingEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:TicketingFacility
    rdfs:subClassOf nits:DataArtifact .

netex:TicketingService
    rdfs:subClassOf nits:DataArtifact .

netex:TicketingServiceFacility
    rdfs:subClassOf nits:DataArtifact .

netex:TimeDemandProfileMember
    rdfs:subClassOf nits:DataArtifact .

netex:TimeDemandTypeAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:TimeIntervalPrice
    rdfs:subClassOf nits:DataArtifact .

netex:TimeStructureFactor
    rdfs:subClassOf nits:DataArtifact .

netex:TimeUnit
    rdfs:subClassOf nits:DataArtifact .

netex:TimeUnitPrice
    rdfs:subClassOf nits:DataArtifact .

netex:Timeband
    rdfs:subClassOf nits:DataArtifact .

netex:TopographicProjection
    rdfs:subClassOf nits:DataArtifact .

netex:Trace
    rdfs:subClassOf nits:DataArtifact .

netex:TractiveRollingStockItem
    rdfs:subClassOf nits:DataArtifact .

netex:TrailingRollingStockItem
    rdfs:subClassOf nits:DataArtifact .

netex:Train
    rdfs:subClassOf nits:DataArtifact .

netex:TrainBlock
    rdfs:subClassOf nits:DataArtifact .

netex:TrainBlockPart
    rdfs:subClassOf nits:DataArtifact .

netex:TrainComponent
    rdfs:subClassOf nits:DataArtifact .

netex:TrainComponentLabelAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:TrainComponentStopAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:TrainElement
    rdfs:subClassOf nits:DataArtifact .

netex:TrainNumber
    rdfs:subClassOf nits:DataArtifact .

netex:TrainSize
    rdfs:subClassOf nits:DataArtifact .

netex:TrainStopAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:Transfer
    rdfs:subClassOf nits:DataArtifact .

netex:TransferDuration
    rdfs:subClassOf nits:DataArtifact .

netex:TransferRestriction
    rdfs:subClassOf nits:DataArtifact .

netex:Transferability
    rdfs:subClassOf nits:DataArtifact .

netex:TransportSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:TravelAgent
    rdfs:subClassOf nits:DataArtifact .

netex:TravelDocument
    rdfs:subClassOf nits:DataArtifact .

netex:TravelDocumentSecurityListing
    rdfs:subClassOf nits:DataArtifact .

netex:TravelSpecification
    rdfs:subClassOf nits:DataArtifact .

netex:TravelatorEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:TripDebit
    rdfs:subClassOf nits:DataArtifact .

netex:TrolleyStandEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:TurnaroundTimeLimitTime
    rdfs:subClassOf nits:DataArtifact .

netex:UicProductCharacteristic
    rdfs:subClassOf nits:DataArtifact .

netex:UicTrainRate
    rdfs:subClassOf nits:DataArtifact .

netex:UnpoweredTrain
    rdfs:subClassOf nits:DataArtifact .

netex:UsageDiscountRight
    rdfs:subClassOf nits:DataArtifact .

netex:UsageParameter
    rdfs:subClassOf nits:DataArtifact .

netex:UsageParameterPrice
    rdfs:subClassOf nits:DataArtifact .

netex:UserNeed
    rdfs:subClassOf nits:DataArtifact .

netex:UserProfileEligibility
    rdfs:subClassOf nits:DataArtifact .

netex:ValidBetween
    rdfs:subClassOf nits:DataArtifact .

netex:ValidDuring
    rdfs:subClassOf nits:DataArtifact .

netex:ValidableElementPrice
    rdfs:subClassOf nits:DataArtifact .

netex:ValidityCondition
    rdfs:subClassOf nits:DataArtifact .

netex:ValidityParameterAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:ValidityRuleParameter
    rdfs:subClassOf nits:DataArtifact .

netex:ValidityTrigger
    rdfs:subClassOf nits:DataArtifact .

netex:ValueSet
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleAccessCredentialsAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleAccessFacility
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleChargingEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleEquipmentProfile
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleEquipmentProfileMember
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleManoeuvringRequirement
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleMeetingPointAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleMode
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleModel
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleModelProfile
    rdfs:subClassOf nits:DataArtifact .

netex:VehiclePoolerProfile
    rdfs:subClassOf nits:DataArtifact .

netex:VehiclePooling
    rdfs:subClassOf nits:DataArtifact .

netex:VehiclePoolingDriverInfo
    rdfs:subClassOf nits:DataArtifact .

netex:VehiclePoolingParkingBay
    rdfs:subClassOf nits:DataArtifact .

netex:VehiclePoolingPlaceAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:VehiclePoolingService
    rdfs:subClassOf nits:DataArtifact .

netex:VehiclePositionAlignment
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleQuayAlignment
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleReleaseEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleRental
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleRentalService
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleScheduleFrame
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleService
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleServicePart
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleServicePlaceAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleSharing
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleSharingParkingBay
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleSharingPlaceAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleSharingService
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleStoppingPosition
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleTypePreference
    rdfs:subClassOf nits:DataArtifact .

netex:VehicleTypeStopAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:Version
    rdfs:subClassOf nits:DataArtifact .

netex:VersionFrame
    rdfs:subClassOf nits:DataArtifact .

netex:VersionedChild
    rdfs:subClassOf nits:DataArtifact .

netex:VisualSignsAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:WaitingEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:WaitingRoomEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:WaterSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:WheelchairAccess
    rdfs:subClassOf nits:DataArtifact .

netex:WheelchairVehicleEquipment
    rdfs:subClassOf nits:DataArtifact .

netex:Whitelist
    rdfs:subClassOf nits:DataArtifact .

netex:WireElement
    rdfs:subClassOf nits:DataArtifact .

netex:WireJunction
    rdfs:subClassOf nits:DataArtifact .

netex:appliesOnOperatingDay
    rdfs:subClassOf nits:DataArtifact .

netex:onLine
    rdfs:subClassOf nits:DataArtifact .

# nits:Journey
netex:CoupledJourney
    rdfs:subClassOf nits:Journey .

netex:CourseOfJourneys
    rdfs:subClassOf nits:Journey .

netex:DatedServiceJourney
    rdfs:subClassOf nits:Journey .

netex:DatedVehicleJourney
    rdfs:subClassOf nits:Journey .

netex:DeadRunJourneyPattern
    rdfs:subClassOf nits:Journey .

netex:DefaultServiceJourneyRunTime
    rdfs:subClassOf nits:Journey .

netex:FarePointInPattern
    rdfs:subClassOf nits:Journey .

netex:FlexibleRoute
    rdfs:subClassOf nits:Journey .

netex:GroupOfSingleJourneys
    rdfs:subClassOf nits:Journey .

netex:JourneyAccounting
    rdfs:subClassOf nits:Journey .

netex:JourneyDesignator
    rdfs:subClassOf nits:Journey .

netex:JourneyHeadway
    rdfs:subClassOf nits:Journey .

netex:JourneyLayover
    rdfs:subClassOf nits:Journey .

netex:JourneyMeeting
    rdfs:subClassOf nits:Journey .

netex:JourneyPart
    rdfs:subClassOf nits:Journey .

netex:JourneyPartCouple
    rdfs:subClassOf nits:Journey .

netex:JourneyPartPosition
    rdfs:subClassOf nits:Journey .

netex:JourneyPatternHeadway
    rdfs:subClassOf nits:Journey .

netex:JourneyPatternLayover
    rdfs:subClassOf nits:Journey .

netex:JourneyPatternRunTime
    rdfs:subClassOf nits:Journey .

netex:JourneyPatternWaitTime
    rdfs:subClassOf nits:Journey .

netex:JourneyRunTime
    rdfs:subClassOf nits:Journey .

netex:JourneyTiming
    rdfs:subClassOf nits:Journey .

netex:JourneyWaitTime
    rdfs:subClassOf nits:Journey .

netex:LinkInJourneyPattern
    rdfs:subClassOf nits:Journey .

netex:MobilityJourneyFrame
    rdfs:subClassOf nits:Journey .

netex:NormalDatedVehicleJourney
    rdfs:subClassOf nits:Journey .

netex:PointInJourneyPattern
    rdfs:subClassOf nits:Journey .

netex:PointOnRoute
    rdfs:subClassOf nits:Journey .

netex:PurposeOfJourneyPartition
    rdfs:subClassOf nits:Journey .

netex:ServiceJourneyInterchange
    rdfs:subClassOf nits:Journey .

netex:ServiceJourneyPatternInterchange
    rdfs:subClassOf nits:Journey .

netex:ServiceLinkInJourneyPattern
    rdfs:subClassOf nits:Journey .

netex:ServicePattern
    rdfs:subClassOf nits:Journey .

netex:SingleJourney
    rdfs:subClassOf nits:Journey .

netex:StopPointInJourneyPattern
    rdfs:subClassOf nits:Journey .

netex:TemplateServiceJourney
    rdfs:subClassOf nits:Journey .

netex:TemplateVehicleJourney
    rdfs:subClassOf nits:Journey .

netex:TimingLinkInJourneyPattern
    rdfs:subClassOf nits:Journey .

netex:TimingPattern
    rdfs:subClassOf nits:Journey .

netex:TimingPointInJourneyPattern
    rdfs:subClassOf nits:Journey .

netex:VehicleJourney
    rdfs:subClassOf nits:Journey .

netex:VehicleJourneyHeadway
    rdfs:subClassOf nits:Journey .

netex:VehicleJourneyLayover
    rdfs:subClassOf nits:Journey .

netex:VehicleJourneyRunTime
    rdfs:subClassOf nits:Journey .

netex:VehicleJourneySpotAllocation
    rdfs:subClassOf nits:Journey .

netex:VehicleJourneyStopAssignment
    rdfs:subClassOf nits:Journey .

netex:VehicleJourneyWaitTime
    rdfs:subClassOf nits:Journey .

netex:hasJourneyPattern
    rdfs:subClassOf nits:Journey .

netex:hasPointInJourneyPattern
    rdfs:subClassOf nits:Journey .

netex:hasServiceJourney
    rdfs:subClassOf nits:Journey .

netex:usesRoute
    rdfs:subClassOf nits:Journey .

# nits:Line
netex:LineSectionPointMember
    rdfs:subClassOf nits:Line .

netex:LineShape
    rdfs:subClassOf nits:Line .

# nits:Network
netex:LineNetwork
    rdfs:subClassOf nits:Network .

netex:NetworkFrameTopic
    rdfs:subClassOf nits:Network .

netex:NetworkRestriction
    rdfs:subClassOf nits:Network .

# nits:Organisation
netex:GeneralOrganisation
    rdfs:subClassOf nits:Organisation .

netex:OnlineServiceOperator
    rdfs:subClassOf nits:Organisation .

netex:OrganisationPart
    rdfs:subClassOf nits:Organisation .

netex:OrganisationalUnit
    rdfs:subClassOf nits:Organisation .

netex:OtherOrganisation
    rdfs:subClassOf nits:Organisation .

netex:RelatedOrganisation
    rdfs:subClassOf nits:Organisation .

netex:ServicedOrganisation
    rdfs:subClassOf nits:Organisation .

netex:TransportOrganisation
    rdfs:subClassOf nits:Organisation .

# nits:RealTimeInformation
netex:MonitoredCall
    rdfs:subClassOf nits:RealTimeInformation .

netex:MonitoredVehicleSharingParkingBay
    rdfs:subClassOf nits:RealTimeInformation .

# nits:Service
netex:ServiceAccessRight
    rdfs:subClassOf nits:Service .

netex:ServiceBookingArrangement
    rdfs:subClassOf nits:Service .

netex:ServiceDesignator
    rdfs:subClassOf nits:Service .

netex:ServiceExclusion
    rdfs:subClassOf nits:Service .

netex:ServiceFacilitySet
    rdfs:subClassOf nits:Service .

netex:ServiceFrame
    rdfs:subClassOf nits:Service .

netex:ServiceReservationFacility
    rdfs:subClassOf nits:Service .

netex:ServiceSite
    rdfs:subClassOf nits:Service .

# nits:SpatialEntity
netex:AccessSpace
    rdfs:subClassOf nits:SpatialEntity .

netex:AccessZone
    rdfs:subClassOf nits:SpatialEntity .

netex:ActivationLink
    rdfs:subClassOf nits:SpatialEntity .

netex:ActivationPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:AddressablePlace
    rdfs:subClassOf nits:SpatialEntity .

netex:AdministrativeZone
    rdfs:subClassOf nits:SpatialEntity .

netex:BeaconPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:CommonSection
    rdfs:subClassOf nits:SpatialEntity .

netex:DeckEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:DeckEntranceAssignment
    rdfs:subClassOf nits:SpatialEntity .

netex:DeckEntranceCouple
    rdfs:subClassOf nits:SpatialEntity .

netex:DeckEntranceUsage
    rdfs:subClassOf nits:SpatialEntity .

netex:DeckNavigationPath
    rdfs:subClassOf nits:SpatialEntity .

netex:DeckPathJunction
    rdfs:subClassOf nits:SpatialEntity .

netex:DeckPathLink
    rdfs:subClassOf nits:SpatialEntity .

netex:DeckSpace
    rdfs:subClassOf nits:SpatialEntity .

netex:DeckVehicleEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:Entrance
    rdfs:subClassOf nits:SpatialEntity .

netex:EntranceEquipment
    rdfs:subClassOf nits:SpatialEntity .

netex:EntranceSensor
    rdfs:subClassOf nits:SpatialEntity .

netex:EquipmentPlace
    rdfs:subClassOf nits:SpatialEntity .

netex:FareScheduledStopPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:FlexibleArea
    rdfs:subClassOf nits:SpatialEntity .

netex:FlexibleStopPlace
    rdfs:subClassOf nits:SpatialEntity .

netex:GaragePoint
    rdfs:subClassOf nits:SpatialEntity .

netex:GeneralSection
    rdfs:subClassOf nits:SpatialEntity .

netex:GeneralZone
    rdfs:subClassOf nits:SpatialEntity .

netex:GenericNavigationPath
    rdfs:subClassOf nits:SpatialEntity .

netex:GenericPathJunction
    rdfs:subClassOf nits:SpatialEntity .

netex:GenericPathLink
    rdfs:subClassOf nits:SpatialEntity .

netex:HailAndRideArea
    rdfs:subClassOf nits:SpatialEntity .

netex:InfoLink
    rdfs:subClassOf nits:SpatialEntity .

netex:InfrastructureLink
    rdfs:subClassOf nits:SpatialEntity .

netex:InfrastructurePoint
    rdfs:subClassOf nits:SpatialEntity .

netex:LineSection
    rdfs:subClassOf nits:SpatialEntity .

netex:Link
    rdfs:subClassOf nits:SpatialEntity .

netex:MobilityServiceConstraintZone
    rdfs:subClassOf nits:SpatialEntity .

netex:NavigationPath
    rdfs:subClassOf nits:SpatialEntity .

netex:NavigationPathAssignment
    rdfs:subClassOf nits:SpatialEntity .

netex:OffSitePathLink
    rdfs:subClassOf nits:SpatialEntity .

netex:OnboardSpace
    rdfs:subClassOf nits:SpatialEntity .

netex:OtherDeckEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:OtherDeckSpace
    rdfs:subClassOf nits:SpatialEntity .

netex:ParkingEntranceForVehicles
    rdfs:subClassOf nits:SpatialEntity .

netex:ParkingPassengerEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:ParkingPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:PassengerEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:PassengerSpace
    rdfs:subClassOf nits:SpatialEntity .

netex:PathInstruction
    rdfs:subClassOf nits:SpatialEntity .

netex:PathJunction
    rdfs:subClassOf nits:SpatialEntity .

netex:PathLink
    rdfs:subClassOf nits:SpatialEntity .

netex:PathLinkInSequence
    rdfs:subClassOf nits:SpatialEntity .

netex:Place
    rdfs:subClassOf nits:SpatialEntity .

netex:PlaceEquipment
    rdfs:subClassOf nits:SpatialEntity .

netex:PlaceInSequence
    rdfs:subClassOf nits:SpatialEntity .

netex:PlaceLighting
    rdfs:subClassOf nits:SpatialEntity .

netex:PlaceSign
    rdfs:subClassOf nits:SpatialEntity .

netex:Point
    rdfs:subClassOf nits:SpatialEntity .

netex:PointOfInterestEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:PointOfInterestSpace
    rdfs:subClassOf nits:SpatialEntity .

netex:PointOfInterestVehicleEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:PointOnLineSection
    rdfs:subClassOf nits:SpatialEntity .

netex:PointOnLink
    rdfs:subClassOf nits:SpatialEntity .

netex:PointOnSection
    rdfs:subClassOf nits:SpatialEntity .

netex:ReliefPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:RouteLink
    rdfs:subClassOf nits:SpatialEntity .

netex:RoutePoint
    rdfs:subClassOf nits:SpatialEntity .

netex:RoutingConstraintZone
    rdfs:subClassOf nits:SpatialEntity .

netex:Section
    rdfs:subClassOf nits:SpatialEntity .

netex:SensorInEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:ServiceLink
    rdfs:subClassOf nits:SpatialEntity .

netex:SingleJourneyPath
    rdfs:subClassOf nits:SpatialEntity .

netex:SiteNavigationPath
    rdfs:subClassOf nits:SpatialEntity .

netex:SitePathJunction
    rdfs:subClassOf nits:SpatialEntity .

netex:SitePathLink
    rdfs:subClassOf nits:SpatialEntity .

netex:StartTimeAtStopPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:StopPlaceEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:StopPlaceSpace
    rdfs:subClassOf nits:SpatialEntity .

netex:StopPlaceVehicleEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:TaxiParkingArea
    rdfs:subClassOf nits:SpatialEntity .

netex:TimingLink
    rdfs:subClassOf nits:SpatialEntity .

netex:TimingPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:TopographicPlace
    rdfs:subClassOf nits:SpatialEntity .

netex:TrafficControlPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:TransportAdministrativeZone
    rdfs:subClassOf nits:SpatialEntity .

netex:VehicleEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:VehicleMeetingLink
    rdfs:subClassOf nits:SpatialEntity .

netex:VehicleMeetingPlace
    rdfs:subClassOf nits:SpatialEntity .

netex:VehicleMeetingPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:VehicleMeetingPointInPath
    rdfs:subClassOf nits:SpatialEntity .

netex:VehiclePoolingMeetingPlace
    rdfs:subClassOf nits:SpatialEntity .

netex:VehiclePoolingParkingArea
    rdfs:subClassOf nits:SpatialEntity .

netex:VehicleSharingParkingArea
    rdfs:subClassOf nits:SpatialEntity .

netex:VehicleStoppingPlace
    rdfs:subClassOf nits:SpatialEntity .

netex:VehicleTypeAtPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:VehicleTypeZoneRestriction
    rdfs:subClassOf nits:SpatialEntity .

netex:Zone
    rdfs:subClassOf nits:SpatialEntity .

netex:ZoneInSeries
    rdfs:subClassOf nits:SpatialEntity .

netex:ZoneProjection
    rdfs:subClassOf nits:SpatialEntity .

netex:inStopPlace
    rdfs:subClassOf nits:SpatialEntity .

netex:servesScheduledStopPoint
    rdfs:subClassOf nits:SpatialEntity .

# nits:Stop
netex:FlexibleQuay
    rdfs:subClassOf nits:Stop .

netex:StopAssignment
    rdfs:subClassOf nits:Stop .

netex:StopPlaceComponent
    rdfs:subClassOf nits:Stop .

# nits:TemporalEntity
netex:DayTypeAssignment
    rdfs:subClassOf nits:TemporalEntity .

netex:ServiceCalendarFrame
    rdfs:subClassOf nits:TemporalEntity .

netex:hasDayTypeAssignment
    rdfs:subClassOf nits:TemporalEntity .

# nits:Timetable
netex:TimetableFrame
    rdfs:subClassOf nits:Timetable .

netex:TimetabledPassingTime
    rdfs:subClassOf nits:Timetable .

netex:hasTimetabledPassingTime
    rdfs:subClassOf nits:Timetable .

```

---

## Next steps

1. Review the proposed TTL block above
2. Copy approved lines into `nits-netex-align.ttl`
3. Bump `owl:versionInfo` in the alignment file
4. Run `make graphdb-load`
5. Re-run this command to confirm gap is closed
