# NETEX Alignment Gap Report

Standard ontology: `netex.ttl`
Alignment file: `nits-netex-align.ttl`

| Metric | Count |
|--------|-------|
| Total classes in netex.ttl | 2939 |
| Already aligned | 824 |
| **Unaligned (gap)** | **2115** |

---

## Proposed additions by NITS category

> Copy the TTL block for a category into `nits-netex-align.ttl` after review.
> Delete or comment out lines you want to skip.

### Skip candidates (533 classes)

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
netex:MealFacilityList  # XSD list container — not a retrieval target
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
netex:TypeOfFareTable  # Enumeration/classifier type — bulk-align or skip
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
netex:TypeOfZone  # Enumeration/classifier type — bulk-align or skip
netex:UicProductCharacteristicList  # XSD list container — not a retrieval target
netex:VehicleAccessFacilityList  # XSD list container — not a retrieval target
netex:accessFacilityList  # XSD list container — not a retrieval target
netex:accessFeatureList  # XSD list container — not a retrieval target
netex:accessibilityAssessmentRef  # XSD reference element — not a standalone concept
netex:accessibilityInfoFacilityList  # XSD list container — not a retrieval target
netex:accessibilityToolList  # XSD list container — not a retrieval target
netex:accommodationAccessList  # XSD list container — not a retrieval target
netex:accommodationFacilityList  # XSD list container — not a retrieval target
netex:accountingStopPointRef  # XSD reference element — not a standalone concept
netex:addressablePlaceRef  # XSD reference element — not a standalone concept
netex:adjacentPointRef  # XSD reference element — not a standalone concept
netex:adjacentStopPlaceRef  # XSD reference element — not a standalone concept
netex:adjacentStopPointRef  # XSD reference element — not a standalone concept
netex:administrativeZoneRef  # XSD reference element — not a standalone concept
netex:againstVehicleTypeRef  # XSD reference element — not a standalone concept
netex:alternativeJourneyRef  # XSD reference element — not a standalone concept
netex:assistanceFacilityList  # XSD list container — not a retrieval target
netex:atStopPointRef  # XSD reference element — not a standalone concept
netex:authorityRef  # XSD reference element — not a standalone concept
netex:availabilityConditionRef  # XSD reference element — not a standalone concept
netex:baseUserProfileRef  # XSD reference element — not a standalone concept
netex:baselineVersionFrameRef  # XSD reference element — not a standalone concept
netex:blockPartRef  # XSD reference element — not a standalone concept
netex:blockRef  # XSD reference element — not a standalone concept
netex:boardingPositionRef  # XSD reference element — not a standalone concept
netex:bookingProcessFacilityList  # XSD list container — not a retrieval target
netex:borderPointRef  # XSD reference element — not a standalone concept
netex:brandingRef  # XSD reference element — not a standalone concept
netex:cappedDiscountRightRef  # XSD reference element — not a standalone concept
netex:cappingRuleRef  # XSD reference element — not a standalone concept
netex:carServiceFacilityList  # XSD list container — not a retrieval target
netex:cateringFacilityList  # XSD list container — not a retrieval target
netex:chargingMomentRef  # XSD reference element — not a standalone concept
netex:checkConstraintRef  # XSD reference element — not a standalone concept
netex:classOfUseRef  # XSD reference element — not a standalone concept
netex:classifiedAsRef  # XSD reference element — not a standalone concept
netex:climateControlList  # XSD list container — not a retrieval target
netex:codespaceRef  # XSD reference element — not a standalone concept
netex:collectionPointRef  # XSD reference element — not a standalone concept
netex:columnRef  # XSD reference element — not a standalone concept
netex:commercialProfileRef  # XSD reference element — not a standalone concept
netex:commonVehicleServiceRef  # XSD reference element — not a standalone concept
netex:complexFeatureRef  # XSD reference element — not a standalone concept
netex:compoundBlockRef  # XSD reference element — not a standalone concept
netex:compoundTrainRef  # XSD reference element — not a standalone concept
netex:connectingStopPointRef  # XSD reference element — not a standalone concept
netex:connectionRef  # XSD reference element — not a standalone concept
netex:connectionZoneRef  # XSD reference element — not a standalone concept
netex:contactRef  # XSD reference element — not a standalone concept
netex:controlCentreRef  # XSD reference element — not a standalone concept
netex:controllableElementRef  # XSD reference element — not a standalone concept
netex:couchetteFacilityList  # XSD list container — not a retrieval target
netex:countryRef  # XSD reference element — not a standalone concept
netex:courseOfJourneysRef  # XSD reference element — not a standalone concept
netex:crewBaseRef  # XSD reference element — not a standalone concept
netex:customerAccountRef  # XSD reference element — not a standalone concept
netex:customerAccountStatusRef  # XSD reference element — not a standalone concept
netex:customerPaymentMeansRef  # XSD reference element — not a standalone concept
netex:customerPurchasePackageElementRef  # XSD reference element — not a standalone concept
netex:customerPurchasePackageRef  # XSD reference element — not a standalone concept
netex:customerRef  # XSD reference element — not a standalone concept
netex:datedJourneyPatternRef  # XSD reference element — not a standalone concept
netex:datedVehicleJourneyRef  # XSD reference element — not a standalone concept
netex:dayTypeRef  # XSD reference element — not a standalone concept
netex:deadRunRef  # XSD reference element — not a standalone concept
netex:deckEntranceRef  # XSD reference element — not a standalone concept
netex:deckLevelRef  # XSD reference element — not a standalone concept
netex:deckPlanRef  # XSD reference element — not a standalone concept
netex:deckRef  # XSD reference element — not a standalone concept
netex:deckSpaceRef  # XSD reference element — not a standalone concept
netex:deltaRef  # XSD reference element — not a standalone concept
netex:departmentRef  # XSD reference element — not a standalone concept
netex:derivedFromVersionRef  # XSD reference element — not a standalone concept
netex:destinationDisplayRef  # XSD reference element — not a standalone concept
netex:directionRef  # XSD reference element — not a standalone concept
netex:distanceMatrixElementRef  # XSD reference element — not a standalone concept
netex:distributionAssignmentRef  # XSD reference element — not a standalone concept
netex:distributionChannelRef  # XSD reference element — not a standalone concept
netex:driverTripRef  # XSD reference element — not a standalone concept
netex:dutyRef  # XSD reference element — not a standalone concept
netex:emergencyServiceList  # XSD list container — not a retrieval target
netex:endMeetingPointRef  # XSD reference element — not a standalone concept
netex:endPointOnLinkRef  # XSD reference element — not a standalone concept
netex:endPointRef  # XSD reference element — not a standalone concept
netex:endStopPointRef  # XSD reference element — not a standalone concept
netex:endTariffZoneRef  # XSD reference element — not a standalone concept
netex:entranceSensorRef  # XSD reference element — not a standalone concept
netex:equipmentPlaceRef  # XSD reference element — not a standalone concept
netex:equipmentRef  # XSD reference element — not a standalone concept
netex:exchangableFromIntervalRef  # XSD reference element — not a standalone concept
netex:exchangableUntilIntervalRef  # XSD reference element — not a standalone concept
netex:excludingJourneyPatternRef  # XSD reference element — not a standalone concept
netex:facilitySetRef  # XSD reference element — not a standalone concept
netex:familyFacilityList  # XSD list container — not a retrieval target
netex:fareContractRef  # XSD reference element — not a standalone concept
netex:fareDemandFactorRef  # XSD reference element — not a standalone concept
netex:fareElementInSequenceRef  # XSD reference element — not a standalone concept
netex:farePriceRef  # XSD reference element — not a standalone concept
netex:fareProductRef  # XSD reference element — not a standalone concept
netex:fareSectionRef  # XSD reference element — not a standalone concept
netex:fareStructureElementInSequenceRef  # XSD reference element — not a standalone concept
netex:fareStructureElementRef  # XSD reference element — not a standalone concept
netex:fareTableRef  # XSD reference element — not a standalone concept
netex:flexibleQuayRef  # XSD reference element — not a standalone concept
netex:flexibleServicePropertiesRef  # XSD reference element — not a standalone concept
netex:flexibleStopPlaceRef  # XSD reference element — not a standalone concept
netex:forVehicleTypeRef  # XSD reference element — not a standalone concept
netex:fromConnectionRef  # XSD reference element — not a standalone concept
netex:fromDeckEntranceRef  # XSD reference element — not a standalone concept
netex:fromFarePointInPatternRef  # XSD reference element — not a standalone concept
netex:fromFareSectionRef  # XSD reference element — not a standalone concept
netex:fromJourneyPatternRef  # XSD reference element — not a standalone concept
netex:fromJourneyRef  # XSD reference element — not a standalone concept
netex:fromLinkRef  # XSD reference element — not a standalone concept
netex:fromOperatingDayRef  # XSD reference element — not a standalone concept
netex:fromPointInJourneyPatternRef  # XSD reference element — not a standalone concept
netex:fromPointInPatternRef  # XSD reference element — not a standalone concept
netex:fromPointRef  # XSD reference element — not a standalone concept
netex:fromServiceJourneyPatternRef  # XSD reference element — not a standalone concept
netex:fromServiceJourneyRef  # XSD reference element — not a standalone concept
netex:fromStopPointInJourneyPatternRef  # XSD reference element — not a standalone concept
netex:fromStopPointRef  # XSD reference element — not a standalone concept
netex:fulfilmentMethodRef  # XSD reference element — not a standalone concept
netex:generalGroupOfEntitiesRef  # XSD reference element — not a standalone concept
netex:generalOrganisationRef  # XSD reference element — not a standalone concept
netex:genericPathLinkRef  # XSD reference element — not a standalone concept
netex:geographicalIntervalRef  # XSD reference element — not a standalone concept
netex:geographicalStructureFactorRef  # XSD reference element — not a standalone concept
netex:geographicalUnitRef  # XSD reference element — not a standalone concept
netex:gisFeatureRef  # XSD reference element — not a standalone concept
netex:groupOfDistanceMatrixElementsRef  # XSD reference element — not a standalone concept
netex:groupOfDistributionChannelsRef  # XSD reference element — not a standalone concept
netex:groupOfEntitiesRef  # XSD reference element — not a standalone concept
netex:groupOfLinesRef  # XSD reference element — not a standalone concept
netex:groupOfNoticesRef  # XSD reference element — not a standalone concept
netex:groupOfOperatorsRef  # XSD reference element — not a standalone concept
netex:groupOfSalesOfferPackagesRef  # XSD reference element — not a standalone concept
netex:groupOfServicesRef  # XSD reference element — not a standalone concept
netex:groupOfSingleJourneysRef  # XSD reference element — not a standalone concept
netex:groupOfTimingLinksRef  # XSD reference element — not a standalone concept
netex:hostUserProfileRef  # XSD reference element — not a standalone concept
netex:identityDocumentRef  # XSD reference element — not a standalone concept
netex:individualTravellerRef  # XSD reference element — not a standalone concept
netex:infrastructureLinkRef  # XSD reference element — not a standalone concept
netex:infrastructurePointRef  # XSD reference element — not a standalone concept
netex:inverseRouteRef  # XSD reference element — not a standalone concept
netex:journeyFrequencyGroupRef  # XSD reference element — not a standalone concept
netex:journeyPartCoupleRef  # XSD reference element — not a standalone concept
netex:journeyPartRef  # XSD reference element — not a standalone concept
netex:journeyPatternRef  # XSD reference element — not a standalone concept
netex:journeyRef  # XSD reference element — not a standalone concept
netex:keyList  # XSD list container — not a retrieval target
netex:layerRef  # XSD reference element — not a standalone concept
netex:levelRef  # XSD reference element — not a standalone concept
netex:lightingControlFacilityList  # XSD list container — not a retrieval target
netex:lineRef  # XSD reference element — not a standalone concept
netex:linkRef  # XSD reference element — not a standalone concept
netex:linkSequenceProjectionRef  # XSD reference element — not a standalone concept
netex:linkSequenceRef  # XSD reference element — not a standalone concept
netex:localServiceRef  # XSD reference element — not a standalone concept
netex:locatableSpotRef  # XSD reference element — not a standalone concept
netex:locatingSystemRef  # XSD reference element — not a standalone concept
netex:logicalDisplayRef  # XSD reference element — not a standalone concept
netex:luggageCarriageFacilityList  # XSD list container — not a retrieval target
netex:luggageLockerFacilityList  # XSD list container — not a retrieval target
netex:luggageServiceFacilityList  # XSD list container — not a retrieval target
netex:mainLineRef  # XSD reference element — not a standalone concept
netex:mainPartRef  # XSD reference element — not a standalone concept
netex:mainPlaceRef  # XSD reference element — not a standalone concept
netex:maximumPeriodIntervalRef  # XSD reference element — not a standalone concept
netex:mealFacilityList  # XSD list container — not a retrieval target
netex:medicalFacilityList  # XSD list container — not a retrieval target
netex:mediumAccessDeviceRef  # XSD reference element — not a standalone concept
netex:mediumApplicationInstanceRef  # XSD reference element — not a standalone concept
netex:memberTypeOfValueRef  # XSD reference element — not a standalone concept
netex:minimumPeriodIntervalRef  # XSD reference element — not a standalone concept
netex:mobilityFacilityList  # XSD list container — not a retrieval target
netex:mobilityServiceConstraintZoneRef  # XSD reference element — not a standalone concept
netex:mobilityServiceRef  # XSD reference element — not a standalone concept
netex:modeOfOperationRef  # XSD reference element — not a standalone concept
netex:navigationPathRef  # XSD reference element — not a standalone concept
netex:noticeRef  # XSD reference element — not a standalone concept
netex:nuisanceFacilityList  # XSD list container — not a retrieval target
netex:onboardSpaceRef  # XSD reference element — not a standalone concept
netex:ontoFeatureRef  # XSD reference element — not a standalone concept
netex:onwardRouteLinkRef  # XSD reference element — not a standalone concept
netex:onwardServiceLinkRef  # XSD reference element — not a standalone concept
netex:onwardTimingLinkRef  # XSD reference element — not a standalone concept
netex:operatingDayRef  # XSD reference element — not a standalone concept
netex:operatingPeriodRef  # XSD reference element — not a standalone concept
netex:operationalContextRef  # XSD reference element — not a standalone concept
netex:operatorRef  # XSD reference element — not a standalone concept
netex:oppositeDirectionRef  # XSD reference element — not a standalone concept
netex:organisationPartRef  # XSD reference element — not a standalone concept
netex:organisationalUnitRef  # XSD reference element — not a standalone concept
netex:overtakenVehicleTypeRef  # XSD reference element — not a standalone concept
netex:overtakingAtPointRef  # XSD reference element — not a standalone concept
netex:overtakingOnLinkRef  # XSD reference element — not a standalone concept
netex:overtakingVehicleTypeRef  # XSD reference element — not a standalone concept
netex:parentAccessSpaceRef  # XSD reference element — not a standalone concept
netex:parentDeckSpaceRef  # XSD reference element — not a standalone concept
netex:parentFareZoneRef  # XSD reference element — not a standalone concept
netex:parentJourneyPartRef  # XSD reference element — not a standalone concept
netex:parentJourneyRef  # XSD reference element — not a standalone concept
netex:parentPointOfInterestSpaceRef  # XSD reference element — not a standalone concept
netex:parentQuayRef  # XSD reference element — not a standalone concept
netex:parentRef  # XSD reference element — not a standalone concept
netex:parentStopAreaRef  # XSD reference element — not a standalone concept
netex:parentTopographicPlaceRef  # XSD reference element — not a standalone concept
netex:parentZoneRef  # XSD reference element — not a standalone concept
netex:parkingAreaRef  # XSD reference element — not a standalone concept
netex:parkingBayRef  # XSD reference element — not a standalone concept
netex:parkingBayStatusRef  # XSD reference element — not a standalone concept
netex:parkingFacilityList  # XSD list container — not a retrieval target
netex:parkingPropertiesRef  # XSD reference element — not a standalone concept
netex:parkingRef  # XSD reference element — not a standalone concept
netex:parkingStayList  # XSD list container — not a retrieval target
netex:parkingTariffRef  # XSD reference element — not a standalone concept
netex:passengerCarryingRequirementRef  # XSD reference element — not a standalone concept
netex:passengerCommsFacilityList  # XSD list container — not a retrieval target
netex:passengerInformationEquipmentList  # XSD list container — not a retrieval target
netex:passengerInformationFacilityList  # XSD list container — not a retrieval target
netex:passengerStopAssignmentRef  # XSD reference element — not a standalone concept
netex:placeRef  # XSD reference element — not a standalone concept
netex:pointInJourneyPatternRef  # XSD reference element — not a standalone concept
netex:pointOnRouteRef  # XSD reference element — not a standalone concept
netex:pointRef  # XSD reference element — not a standalone concept
netex:preassignedFareProductRef  # XSD reference element — not a standalone concept
netex:priceGroupRef  # XSD reference element — not a standalone concept
netex:priceUnitRef  # XSD reference element — not a standalone concept
netex:priceableObjectRef  # XSD reference element — not a standalone concept
netex:pricingRuleRef  # XSD reference element — not a standalone concept
netex:pricingServiceRef  # XSD reference element — not a standalone concept
netex:projectToLinkRef  # XSD reference element — not a standalone concept
netex:projectToPointRef  # XSD reference element — not a standalone concept
netex:projectToZoneRef  # XSD reference element — not a standalone concept
netex:projectedFeatureRef  # XSD reference element — not a standalone concept
netex:projectedLinkRef  # XSD reference element — not a standalone concept
netex:projectedLinkSequenceRef  # XSD reference element — not a standalone concept
netex:projectedPointRef  # XSD reference element — not a standalone concept
netex:projectedZoneRef  # XSD reference element — not a standalone concept
netex:providedByRef  # XSD reference element — not a standalone concept
netex:purposeOfEquipmentProfileRef  # XSD reference element — not a standalone concept
netex:purposeOfGroupingRef  # XSD reference element — not a standalone concept
netex:purposeOfJourneyPartitionRef  # XSD reference element — not a standalone concept
netex:qualityStructureFactorRef  # XSD reference element — not a standalone concept
netex:quayRef  # XSD reference element — not a standalone concept
netex:rechargingEquipmentProfileRef  # XSD reference element — not a standalone concept
netex:referencePointRef  # XSD reference element — not a standalone concept
netex:reliefPointRef  # XSD reference element — not a standalone concept
netex:representedByGroupRef  # XSD reference element — not a standalone concept
netex:residentialQualificationRef  # XSD reference element — not a standalone concept
netex:responsibilityRoleRef  # XSD reference element — not a standalone concept
netex:responsibilitySetRef  # XSD reference element — not a standalone concept
netex:responsibleAreaRef  # XSD reference element — not a standalone concept
netex:responsibleOrganisationRef  # XSD reference element — not a standalone concept
netex:responsiblePartRef  # XSD reference element — not a standalone concept
netex:retailDeviceRef  # XSD reference element — not a standalone concept
netex:retailFacilityList  # XSD list container — not a retrieval target
netex:retailingOrganizationRef  # XSD reference element — not a standalone concept
netex:roadAddressRef  # XSD reference element — not a standalone concept
netex:roundingRef  # XSD reference element — not a standalone concept
netex:roundingStepRef  # XSD reference element — not a standalone concept
netex:routePointRef  # XSD reference element — not a standalone concept
netex:routeRef  # XSD reference element — not a standalone concept
netex:rowRef  # XSD reference element — not a standalone concept
netex:safetyFacilityList  # XSD list container — not a retrieval target
netex:salesOfferPackageElementRef  # XSD reference element — not a standalone concept
netex:salesOfferPackageRef  # XSD reference element — not a standalone concept
netex:salesTransactionRef  # XSD reference element — not a standalone concept
netex:sanitaryFacilityList  # XSD list container — not a retrieval target
netex:scheduledStopPointRef  # XSD reference element — not a standalone concept
netex:sectionRef  # XSD reference element — not a standalone concept
netex:securityListRef  # XSD reference element — not a standalone concept
netex:seriesConstraintRef  # XSD reference element — not a standalone concept
netex:serviceAccessCodeRef  # XSD reference element — not a standalone concept
netex:serviceAccessRightRef  # XSD reference element — not a standalone concept
netex:serviceCalendarRef  # XSD reference element — not a standalone concept
netex:serviceFacilitySetRef  # XSD reference element — not a standalone concept
netex:serviceJourneyPatternInterchangeRef  # XSD reference element — not a standalone concept
netex:serviceJourneyRef  # XSD reference element — not a standalone concept
netex:serviceLinkRef  # XSD reference element — not a standalone concept
netex:serviceList  # XSD list container — not a retrieval target
netex:serviceReservationFacilityList  # XSD list container — not a retrieval target
netex:simpleFeatureRef  # XSD reference element — not a standalone concept
netex:singleJourneyPathRef  # XSD reference element — not a standalone concept
netex:singleJourneyRef  # XSD reference element — not a standalone concept
netex:siteComponentRef  # XSD reference element — not a standalone concept
netex:siteElementRef  # XSD reference element — not a standalone concept
netex:siteFacilitySetRef  # XSD reference element — not a standalone concept
netex:siteNavigationPathRef  # XSD reference element — not a standalone concept
netex:siteRef  # XSD reference element — not a standalone concept
netex:spatialFeatureRef  # XSD reference element — not a standalone concept
netex:spotColumnRef  # XSD reference element — not a standalone concept
netex:spotRowRef  # XSD reference element — not a standalone concept
netex:spotSensorRef  # XSD reference element — not a standalone concept
netex:startMeetingPointRef  # XSD reference element — not a standalone concept
netex:startPointOnLinkRef  # XSD reference element — not a standalone concept
netex:startPointRef  # XSD reference element — not a standalone concept
netex:startStopPointRef  # XSD reference element — not a standalone concept
netex:startTariffZoneRef  # XSD reference element — not a standalone concept
netex:stopAreaRef  # XSD reference element — not a standalone concept
netex:stopPlaceEntranceRef  # XSD reference element — not a standalone concept
netex:stopPlaceRef  # XSD reference element — not a standalone concept
netex:submodeRef  # XSD reference element — not a standalone concept
netex:supplementToFareProductRef  # XSD reference element — not a standalone concept
netex:tariffRef  # XSD reference element — not a standalone concept
netex:tariffZoneRef  # XSD reference element — not a standalone concept
netex:taxiParkingAreaRef  # XSD reference element — not a standalone concept
netex:taxiServiceRef  # XSD reference element — not a standalone concept
netex:taxiStandRef  # XSD reference element — not a standalone concept
netex:ticketTypeList  # XSD list container — not a retrieval target
netex:ticketingFacilityList  # XSD list container — not a retrieval target
netex:ticketingServiceFacilityList  # XSD list container — not a retrieval target
netex:ticketingServiceList  # XSD list container — not a retrieval target
netex:timeDemandTypeRef  # XSD reference element — not a standalone concept
netex:timeIntervalRef  # XSD reference element — not a standalone concept
netex:timeStructureFactorRef  # XSD reference element — not a standalone concept
netex:timeUnitRef  # XSD reference element — not a standalone concept
netex:timebandRef  # XSD reference element — not a standalone concept
netex:timetableFrameRef  # XSD reference element — not a standalone concept
netex:timingAlgorithmTypeRef  # XSD reference element — not a standalone concept
netex:timingLinkRef  # XSD reference element — not a standalone concept
netex:timingPatternRef  # XSD reference element — not a standalone concept
netex:timingPointInJourneyPatternRef  # XSD reference element — not a standalone concept
netex:timingPointRef  # XSD reference element — not a standalone concept
netex:toClassOfUseRef  # XSD reference element — not a standalone concept
netex:toConnectionRef  # XSD reference element — not a standalone concept
netex:toDeckEntranceRef  # XSD reference element — not a standalone concept
netex:toFarePointInPatternRef  # XSD reference element — not a standalone concept
netex:toFareSectionRef  # XSD reference element — not a standalone concept
netex:toJourneyPatternRef  # XSD reference element — not a standalone concept
netex:toJourneyRef  # XSD reference element — not a standalone concept
netex:toLinkRef  # XSD reference element — not a standalone concept
netex:toOperatingDayRef  # XSD reference element — not a standalone concept
netex:toPointInJourneyPatternRef  # XSD reference element — not a standalone concept
netex:toPointInPatternRef  # XSD reference element — not a standalone concept
netex:toPointRef  # XSD reference element — not a standalone concept
netex:toServiceJourneyPatternRef  # XSD reference element — not a standalone concept
netex:toServiceJourneyRef  # XSD reference element — not a standalone concept
netex:toStopPointInJourneyPatternRef  # XSD reference element — not a standalone concept
netex:toStopPointRef  # XSD reference element — not a standalone concept
netex:topographicPlaceRef  # XSD reference element — not a standalone concept
netex:tractiveElementTypeRef  # XSD reference element — not a standalone concept
netex:trafficControlPointRef  # XSD reference element — not a standalone concept
netex:trailingElementTypeRef  # XSD reference element — not a standalone concept
netex:trainBlockRef  # XSD reference element — not a standalone concept
netex:trainComponentRef  # XSD reference element — not a standalone concept
netex:trainElementRef  # XSD reference element — not a standalone concept
netex:trainElementTypeRef  # XSD reference element — not a standalone concept
netex:trainNumberRef  # XSD reference element — not a standalone concept
netex:trainRef  # XSD reference element — not a standalone concept
netex:transportOrganisationRef  # XSD reference element — not a standalone concept
netex:transportTypeRef  # XSD reference element — not a standalone concept
netex:travelDocumentRef  # XSD reference element — not a standalone concept
netex:typeOfAccessRightAssignmentRef  # XSD reference element — not a standalone concept
netex:typeOfActivationRef  # XSD reference element — not a standalone concept
netex:typeOfBatteryChemistryRef  # XSD reference element — not a standalone concept
netex:typeOfConcessionRef  # XSD reference element — not a standalone concept
netex:typeOfCongestionRef  # XSD reference element — not a standalone concept
netex:typeOfCustomerAccountRef  # XSD reference element — not a standalone concept
netex:typeOfDeckEntranceUsageRef  # XSD reference element — not a standalone concept
netex:typeOfDeckSpaceRef  # XSD reference element — not a standalone concept
netex:typeOfDeliveryVariantRef  # XSD reference element — not a standalone concept
netex:typeOfDriverPermitRef  # XSD reference element — not a standalone concept
netex:typeOfEquipmentRef  # XSD reference element — not a standalone concept
netex:typeOfFacilityRef  # XSD reference element — not a standalone concept
netex:typeOfFareContractEntryRef  # XSD reference element — not a standalone concept
netex:typeOfFareContractRef  # XSD reference element — not a standalone concept
netex:typeOfFareProductRef  # XSD reference element — not a standalone concept
netex:typeOfFareStructureElementRef  # XSD reference element — not a standalone concept
netex:typeOfFareStructureFactorRef  # XSD reference element — not a standalone concept
netex:typeOfFareTableRef  # XSD reference element — not a standalone concept
netex:typeOfFleetRef  # XSD reference element — not a standalone concept
netex:typeOfFlexibleServiceRef  # XSD reference element — not a standalone concept
netex:typeOfFrameRef  # XSD reference element — not a standalone concept
netex:typeOfJourneyPatternRef  # XSD reference element — not a standalone concept
netex:typeOfLineRef  # XSD reference element — not a standalone concept
netex:typeOfLocatableSpotRef  # XSD reference element — not a standalone concept
netex:typeOfMachineReadabilityRef  # XSD reference element — not a standalone concept
netex:typeOfMediumAccessDeviceRef  # XSD reference element — not a standalone concept
netex:typeOfModeOfOperationRef  # XSD reference element — not a standalone concept
netex:typeOfNoticeRef  # XSD reference element — not a standalone concept
netex:typeOfOperationRef  # XSD reference element — not a standalone concept
netex:typeOfOrganisationPartRef  # XSD reference element — not a standalone concept
netex:typeOfParkingRef  # XSD reference element — not a standalone concept
netex:typeOfPassengerInformationEquipmentRef  # XSD reference element — not a standalone concept
netex:typeOfPaymentMethodRef  # XSD reference element — not a standalone concept
netex:typeOfPlugRef  # XSD reference element — not a standalone concept
netex:typeOfPricingRuleRef  # XSD reference element — not a standalone concept
netex:typeOfProductCategoryRef  # XSD reference element — not a standalone concept
netex:typeOfProjectionRef  # XSD reference element — not a standalone concept
netex:typeOfRetailDeviceRef  # XSD reference element — not a standalone concept
netex:typeOfRollingStockRef  # XSD reference element — not a standalone concept
netex:typeOfSalesOfferPackageRef  # XSD reference element — not a standalone concept
netex:typeOfSecurityListRef  # XSD reference element — not a standalone concept
netex:typeOfServiceRef  # XSD reference element — not a standalone concept
netex:typeOfTariffRef  # XSD reference element — not a standalone concept
netex:typeOfTransferRef  # XSD reference element — not a standalone concept
netex:typeOfTravelDocumentRef  # XSD reference element — not a standalone concept
netex:typeOfUsageParameterRef  # XSD reference element — not a standalone concept
netex:typeOfValidityRef  # XSD reference element — not a standalone concept
netex:typeOfVersionRef  # XSD reference element — not a standalone concept
netex:typesOfPaymentMethodRef  # XSD reference element — not a standalone concept
netex:typesOfProofAcceptedRef  # XSD reference element — not a standalone concept
netex:typesOfProofRequiredRef  # XSD reference element — not a standalone concept
netex:uicProductCharacteristicList  # XSD list container — not a retrieval target
netex:usageParameterRef  # XSD reference element — not a standalone concept
netex:userProfileRef  # XSD reference element — not a standalone concept
netex:validableElementRef  # XSD reference element — not a standalone concept
netex:vehicleAccessCredentialsAssignmentRef  # XSD reference element — not a standalone concept
netex:vehicleAccessFacilityList  # XSD list container — not a retrieval target
netex:vehicleChargingEquipmentRef  # XSD reference element — not a standalone concept
netex:vehicleEquipmentProfileRef  # XSD reference element — not a standalone concept
netex:vehicleJourneyRef  # XSD reference element — not a standalone concept
netex:vehicleMeetingPlaceRef  # XSD reference element — not a standalone concept
netex:vehicleMeetingPointAssignmentRef  # XSD reference element — not a standalone concept
netex:vehicleMeetingPointRef  # XSD reference element — not a standalone concept
netex:vehicleModelProfileRef  # XSD reference element — not a standalone concept
netex:vehicleModelRef  # XSD reference element — not a standalone concept
netex:vehiclePoolingDriverInfoRef  # XSD reference element — not a standalone concept
netex:vehiclePoolingMeetingPlaceRef  # XSD reference element — not a standalone concept
netex:vehiclePoolingParkingAreaRef  # XSD reference element — not a standalone concept
netex:vehiclePoolingRef  # XSD reference element — not a standalone concept
netex:vehiclePoolingServiceRef  # XSD reference element — not a standalone concept
netex:vehicleRef  # XSD reference element — not a standalone concept
netex:vehicleRentalRef  # XSD reference element — not a standalone concept
netex:vehicleServicePartRef  # XSD reference element — not a standalone concept
netex:vehicleServiceRef  # XSD reference element — not a standalone concept
netex:vehicleSharingParkingAreaRef  # XSD reference element — not a standalone concept
netex:vehicleSharingRef  # XSD reference element — not a standalone concept
netex:vehicleStoppingPlaceRef  # XSD reference element — not a standalone concept
netex:vehicleStoppingPositionRef  # XSD reference element — not a standalone concept
netex:vehicleTypeRef  # XSD reference element — not a standalone concept
netex:versionFrameRef  # XSD reference element — not a standalone concept
netex:withConditionRef  # XSD reference element — not a standalone concept
netex:withSalesOfferPackageRef  # XSD reference element — not a standalone concept
netex:zoneRef  # XSD reference element — not a standalone concept
```

### nits:DataArtifact (1494 classes)

Suggested alignment: `rdfs:subClassOf nits:DataArtifact`

```turtle
# NETEX → nits:DataArtifact
netex:abbreviation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:abridgementRanking
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:acceptedDriverPermits
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accessCode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accessFeatureType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accessModes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accessNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accessNumberIsLimited
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accessRightsInProduct
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accessSpaceType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accessSpaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accesses
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accessibilityAssessment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accessibilityTrainedStaff
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accommodationFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accommodations
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accompaniedByCarer
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accountingCode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accountingFactor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accountingTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accountingType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:accousticAnnouncements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:acousticAnnouncements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:acousticCrossingAids
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:acousticDeviceSensors
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:acousticSensor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:activationPointNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:actualVehicleEquipments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:additionalDriver
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:additionalTax
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:address
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:addressLine1
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:addressLine2
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:addresses
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:adjacentPlaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:adjustmentUnits
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:advertised
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:aimedArrivalTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:aimedDepartureTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:aimedNonstopPassingTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:aimedWaitingTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:airConditioned
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:airConditioning
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:airSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:airlock
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:alarmButton
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:alightingRequestMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:alightingSideInDirectionOfTravel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:alightingUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:allLines
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:allowAdditionalDiscounts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:allowCompanionDiscounts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:allowCumulativeDiscounts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:allowed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:allowedDirections
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:allowedForWaitTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:allowedInChannel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:allowedInCountry
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:allowedUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:alternativeDescriptors
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:alternativeNames
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:alternativeTexts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:alwaysLit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:amount
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:amountFactor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:amountOfPriceUnits
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:applicationInstances
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:appliesTo
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:areas
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:armRest
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:arrivalDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:arrivalTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:arrivesForwards
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:arrivesFromLeft
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:asBraille
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:assignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:assistanceAvailability
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:assistanceNeeded
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:assistedBoardingLocation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:associatedContract
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:atCentre
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:attendant
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:attributeName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:attributeValue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:audibleSignalsAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:audioAnnouncementType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:audioAnnouncements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:audioAnnouncementsTrigger
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:audioInterfaceAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:audioOrVideoIntercom
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:audioPassthroughIndicator
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:audioTriggerMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:audioValidationFeedback
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:authorityTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:automatedUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:automatic
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:automaticDoor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:automaticDoors
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:availableDocks
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:availableOnSubscription
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:availableVehicles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:averageDelay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:averagePassengers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:back
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:backRest
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:baggageType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:baggageUseType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:barrier
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:basket
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:battery
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:batteryCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:batteryUsableCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bayGeometry
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bays
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:beaconBackendUrl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:beaconDirection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:beaconProtocol
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:beaconType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bearing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bearingCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bearingCompass
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bearingDegrees
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bedLength
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bedType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:berthFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bicycleRackCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:billingPolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:blacklistRefs
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:blacklists
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:blindAccessible
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:blockParts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:blockRefs
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:blocked
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:boardingHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:boardingPermission
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:boardingPosition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:boardingPositionType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:boardingPositions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:boardingRequestMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:boardingSideInDirectionOfTravel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:boardingUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bollardCrossing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bookWhen
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bookingAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bookingArrangements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bookingChargeType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bookingContact
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bookingDepositRefundable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bookingMethods
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bookingNote
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bookingRequired
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bookingUrl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:borderCrossing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:borderPoints
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bothWays
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:brailleButtons
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:branchLevel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:brandGraphic
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:broadType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:buildDate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:buildingName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:bumpCrossing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:busSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:buttonsHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:buyWhen
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:calendarDate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:callButtonAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:callButtonHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:calls
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:canBeAdvertised
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:canBeCumulative
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:canBeOpened
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:canCarry
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:canChangeClass
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:canInterchange
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:canManoeuvre
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:canRotate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:canTransfer
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cancellationAllowed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cancellationPossible
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:capacities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:capacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cappingRules
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cardNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cardsAccepted
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cctv
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cellPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cells
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:centroid
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:chains
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:changeAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:changeOfDestinationDisplay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:changeOfServiceRequirements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:changeOfTimePossible
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:changedAt
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:changedBy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:changedSince
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:charge
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:chargeEnergy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:chargingBasis
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:chargingDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:chargingMomentType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:chargingVoltage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:chassisNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:checkConstraintDelays
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:checkConstraintProcess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:checkConstraintThroughputs
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:checkConstraints
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:checkDirection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:checkProcess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:checkService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:childSeat
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:classifications
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:client
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:coachSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:codePrefix
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:codespace
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:codespaceAssignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:codespaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:collectionNote
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:columns
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:comment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:commentsAbout
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:communicationMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:companionProfiles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:companionRelationshipType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:companionSeat
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:companyNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:compassBearing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:compassOctant
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:compatibleWith
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:components
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:conditionSummary
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:configurationConditions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:congestion
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:connectingStopPointName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:connectingVehicleModes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:connectionCertainty
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:consumptionAmount
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:consumptionUnits
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:contactDetails
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:contacts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:containedIn
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:content
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:contentValidityConditions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:continuousHandrail
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:contractGoverningLaw
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:contractType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:contracts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:contrast
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:controlCentreCode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:controlCentreNotifyThreshold
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:controlCentres
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:controllableElements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:controllableElementsInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:controlled
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:controlledLocking
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:convertible
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:couchetteFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:count
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:counterService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:countries
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:countryName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:covered
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:creditPolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:crewBases
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:crossBorder
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:crossRoad
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:crowding
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cruiseControl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:currenciesAccepted
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:currency
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:current
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:currentAt
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:currentType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:customerAccountEntries
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:customerAccountStatusType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:customerAccounts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:customerPurchasePackageElements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:customerPurchasePackageEntries
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:customerPurchasePackageStatus
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:customerPurchasePackages
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:customerServiceContactDetails
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:customers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cycleRack
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:cycleStorageType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dataLicenceUrl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dataObjectPermissions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dataObjectRequest
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dataObjectServiceCapabilities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dataRoleType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dataSources
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:date
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dateOfBirth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:datedCalls
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:datedPassingTimes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dayEvent
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dayLength
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dayNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dayOfMonth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dayOfYear
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dayOffsetRelativeToMainPart
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dayTypeAssignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dayTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:daysOfWeek
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:deadRunType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:deckLevels
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:deckNavigationType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:deckPlacesInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:deckPlans
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:deckSpaceCapacities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:deckSpaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:deckWindowType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:deckWindows
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:decks
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:defaultCurrency
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:defaultDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:defaultLanguage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:delegatedResponsibilitySets
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:deliveryVariantMediaType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:delta
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:deltaValues
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:departments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:departsForwards
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:departsToRight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:departureDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:departureTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:depositPolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:depositRequired
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:depth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:description
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:descriptor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:destinationDisplayContext
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:destinationDisplayVariantMediaType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:destinationDisplays
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:destinations
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:detourAccepted
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:directionButtonHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:directionName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:directionOfUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:directionType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:disabledDocks
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:disabledPriority
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:disabledVehicles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:disbarring
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:discountAsPercentage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:discountAsValue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:discountBasis
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:discountOnlyForFirstPerson
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:discountRights
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:discrete
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:displayAsIcon
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:displayAssignmentType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:displayAssignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:displayPriority
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:distance
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:distanceFromFront
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:distanceFromNearestKerb
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:distanceFromStart
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:distanceMatrixElements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:distributionAssignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:distributionChannelType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:distributionChannels
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:distributionPoints
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:distributionRights
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:documentLinks
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dogsMustBeCarried
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:door
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:doorControlElementHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:doorHandleInside
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:doorHandleOutside
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:doorOrientation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:doorType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:doors
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:doorstepMark
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:doubleSingleFare
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:drinkingWater
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:driverAccessDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:driverDisplayText
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:driverFeeBasis
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:driverReturnDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:drivingLicenceVerified
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:drivingStyle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dropKerbOutside
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:droppedKerb
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:duration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dutyParts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dynamic
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:dynamicDistanceMatrixElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:earliestDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:earliestDepartureDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:earliestDepartureTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:earliestTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:earliestTimeDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:edgeToTrackCenterDistance
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:effectiveFrom
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:elementAccesses
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:email
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:emailVerified
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:embargoUntil
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:enclosed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:encumbranceNeed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:endDate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:endDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:endEvent
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:endGeographicalValue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:endOfValidity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:endTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:endTimeDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:endValue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:energySaving
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:entitlementType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:entranceAttention
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:entranceRequiresPassport
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:entranceRequiresStaffing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:entranceRequiresTicket
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:entranceSetting
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:entranceToVehicle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:entranceUsageType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:entrances
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:equipmentLength
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:equipmentPlaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:equipmentPositions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:equipmentProfiles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:equipmentWidth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:equipments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:escalatorFreeAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:escalatorWithLanding
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:euroClass
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:exchangableFromAnyTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:exchangableFromDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:exchangableFromPercentUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:exchangableTo
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:exchangableUntilAnyTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:exchangableUntilDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:exchangableUntilPercentUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:exclude
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:excluded
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:expiryDate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:extensions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:externalFloorSelection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:facilities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:facilitySets
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:factor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareBasis
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareClass
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareClasses
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareContractEntries
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareContracts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareDemandType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareElementsInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareScheduledStopPoints
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareSections
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareStructureElements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareStructureElementsInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareStructureType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fareTables
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:featureMembers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:features
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:feeBasis
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:feePerBag
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:finalCarrier
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:finalisationDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:finishingDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:firstArrivalTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:firstAxleHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:firstClassDistance
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:firstClassReturn
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:firstClassSingle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:firstDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:firstDepartureTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:firstName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fixed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fleets
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:flexibleLineType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:flexibleLinkType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:flexiblePointProperties
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:flexibleRouteType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:flexibleServiceProperties
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:flexibleServiceType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:flexibleStopPlaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:flights
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:floatingVehicles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:flooringStatus
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:flooringType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fontSize
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:forAdvertisement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:forAlighting
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:forBoarding
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:forProduction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:formula
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:forwardsOnly
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:freeParkingOutOfHours
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:freeRecharging
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:freeToUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:frequencyGroups
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:frequencyInterval
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:frequencyOfUseType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:frequentTravellerDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fromCall
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fromDate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fromMode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fromVisitNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:frontText
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fuelType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fuelTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fulfilmentMethodType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fulfilmentMethods
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:fullCharge
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:funicularSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:gapToPlatform
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:garagePoints
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:garages
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:gated
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:gearTypeDescriotion
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:gender
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:genderLimitation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:generalGroupOfEntities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:genericParameterAssignment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:genericParameterAssignmentInContext
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:geographicalIntervals
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:geographicalStructureFactors
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:geographicalUnits
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:givesEntitlement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:glassDoor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:goesOnCard
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:gradient
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:gradientType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:gridVoltage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groundMarkAlignedWithButton
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupBookingFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupOfDistanceMatrixElements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupOfLinesType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupOfTimebands
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupSizeChanges
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupsOfDistanceMatrixElements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupsOfDistributionChannels
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupsOfEntities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupsOfLines
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupsOfSaleOfferPackages
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupsOfSalesOfferPackages
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupsOfServices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:groupsOfSites
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:guaranteed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:guideDogAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:guideDogsAllowed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:handWashing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:handrailHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:handrailType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasArmrest
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasBlind
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasDiscountedFares
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasDoor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasDynamicPricing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasExchangeFee
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasFee
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasFreeConnectingReservations
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasHoist
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasLiftOrRamp
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasMinimumPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasNotices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasPhoto
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasPower
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasPowerSupply
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasPurchaseConditions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasQuota
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasReservationFee
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasRouteRestrictions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasTransferFee
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasTravelTimeRestrictions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasUsbPowerSocket
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hasWheelchairSpaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:heading
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:headroom
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:headroomForLuggage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:headwayDisplay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:headways
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:heated
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:height
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:heightFromFloor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:heightFromGround
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:heightOfLowCounter
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:heightOfMachineInterface
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:heightOfSosPanel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:helmet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hide
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:highFloor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hoist
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:hoistOperatingRadius
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:holidayType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:holidayTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:houseNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:identityToken
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:identityVerified
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:image
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:imageUri
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:immobilisation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:includedIn
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:includes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:includesGroupingType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:individualPassengerInfos
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:inductionLoop
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:inductionLoopSign
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:inductionLoops
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:infoLinks
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:infoUrl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:initialCarrier
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:installmentPaymentMethods
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:installmentTypesOfPaymentMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:instruction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:insuranceVerified
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:integratesAnEscalatorPart
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:interchangeAllowed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:internalHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:internalWidth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:intervalType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:inverseAllowed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isAcceptingReturns
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isAccessibleOnVoyage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isAllowed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isAutomatic
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isBetweenSeats
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isByAisle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isByWindow
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isCard
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isDirect
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isEmergencyExit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isExchangable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isFacingAisle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isFacingWindow
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isFareStage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isFeeRefundable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isFirstInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isFoldup
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isForbidden
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isInEndRow
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isInFrontRow
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isLastInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isLockable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isObligatory
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isOperational
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isPersonal
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isPortable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isReclining
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isRefundable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isRenting
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isRequired
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isRestricted
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isReversible
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isSmartCard
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isStowable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isSupplement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isValid
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:isoCode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:itinerary
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:jointCheckIn
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:journeyAccountings
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:journeyDesignator
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:journeyDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:journeyPartPositions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:journeyParts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:journeyPatternRunTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:journeyPatterns
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:journeys
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:keptOpen
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:keyScheme
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:label
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lamps
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:landmark
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lang
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:languages
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lastArrivalTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lastDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lastDepartureTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lastTripDate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lastUpdated
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lastVerifiedDate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:latestArrivalDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:latestArrivalTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:latestBookingTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:latestDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:latestTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:latestTimeDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:layers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:layover
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:layovers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:leftSideBorder
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:legalName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:legalStatus
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:length
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:levelAccessIntoVehicle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:liftFreeAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lighting
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lightingOnMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:likeForLikeRefuelling
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:limitationGroupingType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:limitationSetSelectionType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:limitations
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:limitedUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lineDirections
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lineMap
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lineName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lineSectionPointType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lineType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lines
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:linesInDirectionRefs
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:link
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:linkSequenceProjection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:links
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:linksInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:localControl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:localResident
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:localServices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:locale
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:locatableSpotType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:locationSystem
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lock
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lockedAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:locker
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lockerDepth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lockerFee
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lockerHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lockerType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lockerWidth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lockingMechanism
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lockingType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:logEntries
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:logInRequired
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lowCounterAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lowFloor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:lowerHandrailHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:luggageAllowanceType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:luggageAllowed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:luggageChargingBasis
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:luggageMaximalWeigth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:luggageSpotType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:luggageSpots
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:luggageTrolleys
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:machineReadable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:magneticInductionLoop
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mainTerminusForPlaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mandatoryProduct
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:manufacturer
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mark
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:markUrl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:markedAs
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:markingStatus
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximalFrequency
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumAge
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumAutomaticWaitTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumBagDepth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumBagHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumBagWeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumBagWidth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumBookingDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumChargingPower
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumDistance
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumFlowPerMinute
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumHeadwayInterval
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumInterchangeWindow
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumLength
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumLikelyDelay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumLimitPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumLimitPriceAsPercentage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumLoad
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumNumberItems
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumNumberOfBerths
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumNumberOfFailToCheckOutEvents
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumNumberOfInterchanges
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumNumberOfNamedTransferees
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumNumberOfNightsAway
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumNumberOfPersons
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumNumberOfSteps
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumNumberOfSuspensionsPerTerm
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumNumberOfTrips
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumNumberToReserve
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumPassengers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumPeriodBeforeDeparture
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumPersonsDiscounted
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumPersonsFree
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumPower
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumPowerAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumPriceAsMultiple
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumPriceAsPercentage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumRange
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumRecline
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumSpeed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumSpots
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumStandingDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumStay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumTimeToMakeATransfer
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumTransferTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumVelocity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumWaitTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumWeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:maximumWidth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mayBeSkipped
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mediaType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mediumAccessDevices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:meetingPointAssignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:meetingPointServiceType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:members
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:method
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:methodName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:metroSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimalFrequency
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumAge
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumBookingDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumHeadwayInterval
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumLength
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumLikelyDelay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumLimitPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumLimitPriceAsPercentage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumNumberOfCardHolders
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumNumberOfNightsAway
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumNumberOfPassengers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumNumberOfPersons
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumNumberOfSteps
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumNumberToReserve
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumOvertakingWidth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumPeriodBeforeDeparture
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumPrice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumPriceAsMultiple
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumPriceAsPercentage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumStayType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumTimeBeforeReentry
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumTransferTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumTurningCircle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumUnits
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:minimumWidth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mirrorOnOppositeSide
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mobileDeviceTickets
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mobilePhoneCoverage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mobilityImpairedAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mobilityNeed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mobilityRestrictedTravellerDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:modeRestrictionAssessments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:modification
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:modificationSet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:monitored
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:monitoredBays
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:monitoringRemoteControl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:month
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:monthDayOnWhichAgeApplies
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:monthOfYear
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:monthValidityOffsets
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mustCarry
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mustReserveWholeCompartment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mustReside
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:mustReturnToSameBay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:name
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:nameOfClass
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:nameOnRouting
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:nameSuffix
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:nameType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:nature
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:navigationType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:nearTopographicPlaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:necessaryForceToOpen
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:needRanking
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:neighbours
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:newValue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:nightTrain
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:noCashPayment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:nominalVoltage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:note
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:notice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:notices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:number
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOFDrivers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfBaysWithRecharging
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfCars
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfExchangesAllowed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfFlights
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfFreeConnectingReservations
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfGates
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfGears
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfLockers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfMachines
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfParkingLevels
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfProposedTrips
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfServers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfSpaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfSteps
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfTills
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfToilets
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfTravellersCarried
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberOfUnits
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberingFromFront
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:numberingFromLeft
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:occasionalTravellerDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:oldValue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:onBecomingEligiblePolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:onCeasingToBeEligiblePolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:onboardStays
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:oneForNPersons
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:onlinePurchaseForCollection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:onlinePurchaseForETicket
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:onlinePurchaseForSelfPrintTicket
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:onlineServices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:onlyAtCertainDistributionPoints
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:onwardCalls
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:onwardLinks
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:operatingDays
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:operatingPeriods
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:operationalContexts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:operationalNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:operationalOrientation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:operatorActivities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:operators
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:organisationRoleType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:organisationType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:orientation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:otherCountries
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:otherFacilities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:otherModes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:otherTransportModes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:outOfService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:overnightParkingPermitted
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:overtakingWidth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ownResponsibilitySets
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:panicButton
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingChargeBand
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingChargeBands
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingComponents
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingLayout
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingPaymentCode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingPaymentProcess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingProperties
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingReservation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingStayType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingUserType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingUserTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingVehicleType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingVehicleTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parkingVisibility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:partial
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:parts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:passageType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:passengerAtStopTimes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:passengerCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:passengerSpaceType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:passengerSpotAllocations
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:passengerSpots
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:passengerVehicleSpots
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:passengersPerMinute
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:passingThrough
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:passingTimeDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:passingTimes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pathHeading
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pathInstructions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pathJunctions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pathLinks
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pathLinksInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:paymentMeans
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:paymentMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:paymentMethods
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pedestal
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pedestrianLights
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:penaltyFee
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:penaltyIfWithoutTicket
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:penaltyPolicyType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:period
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:periodicity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:personCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:personalOperationType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:petsAllowed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:phone
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:phoneVerified
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:photo
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:placeCentre
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:placeEquipments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:placeName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:placeTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:placement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:placesInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:planned
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:plateCode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:platformHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:plugType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:point
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pointNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pointOfInterestClassificationHierarchies
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pointOfInterestSpaceType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:points
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pointsInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pointsOfInterest
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:poolingPolicyUrl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:poolsOfVehicles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:positionInTrain
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:positionOfTrainElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:possibleInstallmenttIntervals
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:postCode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:postCodeExtension
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:postalAddress
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:postalRegion
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:powerCouplingType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pramPlaceCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:precision
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:preparationDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:prerequisites
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:presentationPosition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:previousCalls
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:priceGroups
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:priceUnits
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:prices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pricesFor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pricingBasis
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pricingParameterSet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pricingServices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:primaryMode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:primaryOrientation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:principalCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:print
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:priority
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:privateCode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:privateContactDetails
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:productType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:prohibitedForHazardousMaterials
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:projection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:projections
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:proofRequired
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:properties
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:propertyKeptForDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:proposedByServices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:proposingServices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:propulsionType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:propulsionTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:providesCard
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:province
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:psychosensoryNeed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:public
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:publicUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:publicityChannel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pump
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:purchaseAction
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:purchaseMoment
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:purchaseWhen
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:pushchairCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:qualificationPercent
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:qualifierName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:qualityStructureFactors
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:quay
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:quayAlignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:quayType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:quays
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:queueManagement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:queuingSeatedPossible
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:railSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:railedQueue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:raisedButtons
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ramp
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rampDoorbell
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rampFreeAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:range
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rangeBetweenRefuelling
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rank
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ranking
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reachedFloorAnnouncement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:realTimeOccupancyAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reason
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rechargingAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rechargingPointAssignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rechargingProcessType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rechargingSteps
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:recognizable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:recycling
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:refundBasis
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:registrationDate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:registrationNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:registrationRequired
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:relationToVehicle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:relativeLevelOrder
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:relativeRanking
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:relativeWeighting
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reliefOpportunities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:remarks
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:remoteControl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rentalPenaltyPolicyType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rentalPolicyUrl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:replaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requestMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requestMethodType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requestStop
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresAccount
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresBookingReference
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresCard
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresDeposit
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresEmailAddress
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresEntitlement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresNightsAway
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresPhoto
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresPositiveBalance
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresRegistration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresReservation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:requiresValidation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:resellWhen
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reservationChargeType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reservationRequired
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reservationUrl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reservingRequirements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:residenceType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:residencyType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:resides
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:responsibilities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:responsibilityRoles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:responsibilitySets
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:restStopDistance
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:restricted
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:restrictedLine
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:restrictedToChannel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:restrictionType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:retailConsortiums
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:retailDevices
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:returnFareTwiceSingle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:returnRouteIdentical
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:returnTripsOnly
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reverse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reverseMembers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reversedOrientation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reversible
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reversingDirection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:reviews
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:revolvingDoor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rightSideBorder
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:roadAddress
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:roadName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:roadNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:roles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rollingStockInventories
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rollingStockItems
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rollingStockType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:roofRack
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:roundIfGreaterThan
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:roundTo
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:roundingMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:roundingModulus
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:roundingSteps
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:roundings
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:routeInstructions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:routes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:routingType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:rows
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ruleApplicability
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ruleStepResults
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:runTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:runTimes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:safeForGuideDog
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:safetyEdge
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:salesOfferPackageElements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:salesOfferPackageSubstitutions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:salesOfferPackages
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:salesTransactions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sameStationRentryPolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sanitary
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:satNav
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:satisfiesFacilityRequirements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:scheduledHeadwayInterval
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:schematicMaps
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:scopeOfTicketsAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:scopingMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:season
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:seasons
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:seatAllocationMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:seatBackHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:seatDepth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:seatHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:seatingCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:seats
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:secondClassDistance
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:secondClassReturn
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:secondClassSingle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sectionType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sections
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sectionsInSequence
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:secure
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:secureParking
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:selfDriveSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:selfPropelled
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:selfServiceLockers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sensorsInSpot
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sequenceFromFront
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:seriesConstraints
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:seriesType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:servedPlaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:servedScheduledStopPoints
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:serviceAlteration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:serviceAlterationType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:serviceBookingArrangements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:serviceDesignator
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:serviceFacilitySets
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:services
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sharedUsage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sharingPolicyUrl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sharpsDisposal
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:shortCode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:shortName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:shortStopCode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:shortTrip
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:showAsAccessible
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:showerFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sideText
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:signContentType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:signGraphic
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:signageToLift
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:siteFacilitySet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:siteFacilitySets
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:skiRack
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:smoker
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:smokingAllowed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:snowAndIceSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:sosPanel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:spaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:specialPlaceCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:specificParameterAssignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:speed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:spiralStair
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:spotAffinities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:spotAffinityType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:spotAllocations
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:spotAvailabilityStatus
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:spotColumns
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:spotRows
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:staffing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stairFreeAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stairRamp
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stakeholderRoleType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:standardTransferTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:standardWaitTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:standingAllowed
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:standingCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:startDate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:startEvent
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:startGeographicalValue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:startOfValidity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:startTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:startTimeDayOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:startTimeInBlock
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:startTimesAtStopPoints
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:startValue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:status
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:staySeated
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stepColourContrast
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stepCondition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stepFree
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stepFreeAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stepHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stepLength
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stopPlaceType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stopPlaceWeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stopPlaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stopRequestButton
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stopRequestTimeout
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stopType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stopUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:stopUseConstraint
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:street
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:structureFactors
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:submodes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:subscriptionRenewalPolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:subscriptionTermType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:suburb
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:subzones
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:suitabilities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:suitable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:suitableFor
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:suitableForCycles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:summaries
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:supplementProductType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:supplementTo
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:supportBarHeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:surfaceType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:surname
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:suspension
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:suspensionPolicy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tableType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tactileActuators
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tactileGroundFloorButton
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tactileGuidanceAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tactileGuidanceStrips
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tactileGuidingStrip
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tactileGuidingStripStatus
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tactileInterfaceAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tactileValidationFeedback
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tactileWarningStrip
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tactileWarningStripContrast
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tactileWriting
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:talkative
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:targetEnergy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tariffBasis
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tariffs
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:taxCategory
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:taxiRanks
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:taxiStands
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:taxiSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:telecabinSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:temporary
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:text
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:thirdPartyProducts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:throughLoader
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ticketCounter
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ticketCounterService
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ticketMachines
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ticketOffice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ticketTypesAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ticketValidatorType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ticketedQueue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:ticketing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tides
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tiltAngle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tiltType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:time
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:timeDemandTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:timeIntervals
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:timeStructureFactors
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:timeUnits
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:timebands
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:timingPointStatus
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:timings
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:title
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:toCall
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:toDate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:toFareClass
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:toMode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:toVisitNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:toiletFacility
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:toiletsType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:topographicPlaceType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:topographicPlaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:totalCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:totalChargeEnergy
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:totalPower
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:totalWeight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:towards
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:town
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:traces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tradingName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:trailerHitch
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:trainComponentLabelAssignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:trainElement
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:trainElementType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:trainElementTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:trainElements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:trainNumbers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:trainRestrictions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:trainSize
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:trainSizeType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tramSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transferDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transferMode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transferModes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transferOnly
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transfers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transitCarrier
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transmission
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transportMode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transportModes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transportSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:transportTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:travelDocuments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:travelSpecifications
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:travellingWithPet
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tripTimes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:tripType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:turningSpacePosition
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:type
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typeOfCoupling
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typeOfEntity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typeOfFuel
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typeOfName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:types
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typesOfEntity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typesOfFareProduct
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typesOfMachineReadabilities
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typesOfPaymentMethod
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typesOfRetailDevice
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typesOfServiceFeature
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typesOfTravelDocument
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typesOfTravelDocuments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:typesOfValue
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:uicCode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:uicTrainRate
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:units
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:unlimitedMileage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:unlocalisedEquipments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:unusedTicketsOnly
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:url
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:usage
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:usbPowerSockets
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:useToExclude
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:usedIn
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:userAcronym
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:userTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vATNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:validBetween
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:validDayBits
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:validableElements
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:validationGuidance
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:validityConditions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:validityParameterAssignmentType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:validityParameterAssignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:validityParameterGroupingType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:validityParameterSetSelectionType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:value
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:valueName
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:values
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:variantText
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:variants
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleCategories
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleCollection
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleEquipmentProfileMembers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleEquipmentProfiles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleMeetingLinks
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleMeetingPlaceAssignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleMeetingPointAssignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleMeetingPoints
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleMode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleModelProfiles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleModels
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleModes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleOrientation
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehiclePoolingDriverInfos
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehiclePositionAlignments
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehiclePreferences
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleRestrictions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleServiceParts
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleSide
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleStoppingPlaces
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleStoppingPositions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicleTypes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vehicles
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:versionFrames
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:versionType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:versions
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:viaFlag
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:viaType
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vias
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:vibratingCrossingAids
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:visitNumber
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:visualContrast
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:visualGuidanceBands
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:visualObstacle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:visualSignsAvailable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:visualValidationFeedback
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:waitTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:waitTimes
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:waitingTime
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:walkTransferDuration
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:waterSubmode
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:weeksOfMonth
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:weight
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:weighting
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:wheelchairAccepted
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:wheelchairAccess
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:wheelchairBookingRequired
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:wheelchairLuggageTrolleys
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:wheelchairPassable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:wheelchairPassengers
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:wheelchairPlaceCapacity
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:wheelchairSuitable
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:wheelchairTurningCircle
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:wheelchairUnaided
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:whitelistRefs
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:whitelists
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:width
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:winterTyres
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:withoutRiser
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:womenOnly
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:x
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:xOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:xmlns
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:xmlnsUrl
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:y
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:yOffset
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:zebraCrossing
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:zoneContainingStops
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:zoneTopology
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:zoneUse
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:zones
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
netex:zonesInSeries
    rdfs:subClassOf nits:DataArtifact .  # Default: treat as DataArtifact
```

### nits:Journey (19 classes)

Suggested alignment: `rdfs:subClassOf nits:Journey`

```turtle
# NETEX → nits:Journey
netex:canBreakJourney
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:coupledJourneys
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:courseOfJourneysNumber
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:coursesOfJourneys
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:excludedJourneyPatternRefs
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:farePointsInPattern
    rdfs:subClassOf nits:Journey .  # Ends with 'Pattern' (journey/service pattern)
netex:fromStopPointInJourneyPattern
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:journeyPattern
    rdfs:subClassOf nits:Journey .  # Ends with 'Pattern' (journey/service pattern)
netex:numberOfJourneysToShow
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:onMainRoute
    rdfs:subClassOf nits:Journey .  # Ends with 'Route'
netex:pointsInPattern
    rdfs:subClassOf nits:Journey .  # Ends with 'Pattern' (journey/service pattern)
netex:registerBreakOfJourney
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:replacedJourneys
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:serviceJourneyPatternType
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:symbolMarkingUsualRoute
    rdfs:subClassOf nits:Journey .  # Ends with 'Route'
netex:templateVehicleJourneyType
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:toStopPointInJourneyPattern
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:vehicleJourneySpotAllocations
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
netex:vehicleJourneyStopAssignments
    rdfs:subClassOf nits:Journey .  # Contains 'Journey'
```

### nits:Organisation (8 classes)

Suggested alignment: `rdfs:subClassOf nits:Organisation`

```turtle
# NETEX → nits:Organisation
netex:additionalOperators
    rdfs:subClassOf nits:Organisation .  # Contains 'Operator'
netex:comparisonOperator
    rdfs:subClassOf nits:Organisation .  # Contains 'Operator'
netex:groupOfOperators
    rdfs:subClassOf nits:Organisation .  # Contains 'Operator'
netex:groupsOfOperators
    rdfs:subClassOf nits:Organisation .  # Contains 'Operator'
netex:hasOperatorRestrictions
    rdfs:subClassOf nits:Organisation .  # Contains 'Operator'
netex:relatedOrganisations
    rdfs:subClassOf nits:Organisation .  # Contains 'Organisation'
netex:servicedOrganisationType
    rdfs:subClassOf nits:Organisation .  # Contains 'Organisation'
netex:typesOfOrganisation
    rdfs:subClassOf nits:Organisation .  # Contains 'Organisation'
```

### nits:SpatialEntity (42 classes)

Suggested alignment: `rdfs:subClassOf nits:SpatialEntity`

```turtle
# NETEX → nits:SpatialEntity
netex:administrativeZones
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:allAreasWheelchairAccessible
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:boardingPositionEntrances
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:deckEntranceAssignments
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:deckEntranceCouples
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:deckEntranceType
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:deckEntranceUsages
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:deckEntrances
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:deckNavigationPaths
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:deckPathJunction
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:deckPathJunctions
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:deckPathLinks
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:fareZones
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:groupsOfTariffZones
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:hasZoneRestrictions
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:heightOfAccessArea
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:infoLink
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Link' (path/access link)
netex:isWaitPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:legSpace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Space'
netex:lengthOfAccessArea
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:linksOnSection
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Section'
netex:mobilityServiceConstraintZones
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:navigationPaths
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:numberOfWheelchairAreas
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:parkingAreas
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:pointStandingForAZone
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:pointsOnSection
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Section'
netex:reversePointsOnSection
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Section'
netex:scheduledStopPoint
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Point'
netex:sensorsInEntrance
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:stopAreas
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:stopPlace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Place'
netex:summerTimeZone
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:summerTimeZoneOffset
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:timeZone
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:timeZoneOffset
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Zone'
netex:turningSpace
    rdfs:subClassOf nits:SpatialEntity .  # Ends with 'Space'
netex:unscheduledPath
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Path'
netex:vehicleEntrances
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Entrance'
netex:wheelchairAreaLength
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:wheelchairAreaWidth
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
netex:widthOfAccessArea
    rdfs:subClassOf nits:SpatialEntity .  # Contains 'Area'
```

### nits:TemporalEntity (19 classes)

Suggested alignment: `rdfs:subClassOf nits:TemporalEntity`

```turtle
# NETEX → nits:TemporalEntity
netex:cappingPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:expireAfterPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:maximumBookingPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:maximumRentalPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:maximumSharingPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:maximumSubscriptionPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:maximumSuspensionPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:minimumBookingPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:minimumQualificationPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:minimumRentalPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:minimumSharingPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:minimumSubscriptionPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:minimumSuspensionPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:notificationPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:paymentGracePeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:qualificationPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:reservationExpiryPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
netex:serviceCalendar
    rdfs:subClassOf nits:TemporalEntity .  # Contains 'Calendar'
netex:uicOperatingPeriod
    rdfs:subClassOf nits:TemporalEntity .  # Ends with 'Period'
```

---

## Full proposed TTL block (all non-skip classes)

```turtle
# nits:DataArtifact
netex:abbreviation
    rdfs:subClassOf nits:DataArtifact .

netex:abridgementRanking
    rdfs:subClassOf nits:DataArtifact .

netex:acceptedDriverPermits
    rdfs:subClassOf nits:DataArtifact .

netex:accessCode
    rdfs:subClassOf nits:DataArtifact .

netex:accessFeatureType
    rdfs:subClassOf nits:DataArtifact .

netex:accessModes
    rdfs:subClassOf nits:DataArtifact .

netex:accessNumber
    rdfs:subClassOf nits:DataArtifact .

netex:accessNumberIsLimited
    rdfs:subClassOf nits:DataArtifact .

netex:accessRightsInProduct
    rdfs:subClassOf nits:DataArtifact .

netex:accessSpaceType
    rdfs:subClassOf nits:DataArtifact .

netex:accessSpaces
    rdfs:subClassOf nits:DataArtifact .

netex:accesses
    rdfs:subClassOf nits:DataArtifact .

netex:accessibilityAssessment
    rdfs:subClassOf nits:DataArtifact .

netex:accessibilityTrainedStaff
    rdfs:subClassOf nits:DataArtifact .

netex:accommodationFacility
    rdfs:subClassOf nits:DataArtifact .

netex:accommodations
    rdfs:subClassOf nits:DataArtifact .

netex:accompaniedByCarer
    rdfs:subClassOf nits:DataArtifact .

netex:accountingCode
    rdfs:subClassOf nits:DataArtifact .

netex:accountingFactor
    rdfs:subClassOf nits:DataArtifact .

netex:accountingTime
    rdfs:subClassOf nits:DataArtifact .

netex:accountingType
    rdfs:subClassOf nits:DataArtifact .

netex:accousticAnnouncements
    rdfs:subClassOf nits:DataArtifact .

netex:acousticAnnouncements
    rdfs:subClassOf nits:DataArtifact .

netex:acousticCrossingAids
    rdfs:subClassOf nits:DataArtifact .

netex:acousticDeviceSensors
    rdfs:subClassOf nits:DataArtifact .

netex:acousticSensor
    rdfs:subClassOf nits:DataArtifact .

netex:activationPointNumber
    rdfs:subClassOf nits:DataArtifact .

netex:actualVehicleEquipments
    rdfs:subClassOf nits:DataArtifact .

netex:additionalDriver
    rdfs:subClassOf nits:DataArtifact .

netex:additionalTax
    rdfs:subClassOf nits:DataArtifact .

netex:address
    rdfs:subClassOf nits:DataArtifact .

netex:addressLine1
    rdfs:subClassOf nits:DataArtifact .

netex:addressLine2
    rdfs:subClassOf nits:DataArtifact .

netex:addresses
    rdfs:subClassOf nits:DataArtifact .

netex:adjacentPlaces
    rdfs:subClassOf nits:DataArtifact .

netex:adjustmentUnits
    rdfs:subClassOf nits:DataArtifact .

netex:advertised
    rdfs:subClassOf nits:DataArtifact .

netex:aimedArrivalTime
    rdfs:subClassOf nits:DataArtifact .

netex:aimedDepartureTime
    rdfs:subClassOf nits:DataArtifact .

netex:aimedNonstopPassingTime
    rdfs:subClassOf nits:DataArtifact .

netex:aimedWaitingTime
    rdfs:subClassOf nits:DataArtifact .

netex:airConditioned
    rdfs:subClassOf nits:DataArtifact .

netex:airConditioning
    rdfs:subClassOf nits:DataArtifact .

netex:airSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:airlock
    rdfs:subClassOf nits:DataArtifact .

netex:alarmButton
    rdfs:subClassOf nits:DataArtifact .

netex:alightingRequestMethod
    rdfs:subClassOf nits:DataArtifact .

netex:alightingSideInDirectionOfTravel
    rdfs:subClassOf nits:DataArtifact .

netex:alightingUse
    rdfs:subClassOf nits:DataArtifact .

netex:allLines
    rdfs:subClassOf nits:DataArtifact .

netex:allowAdditionalDiscounts
    rdfs:subClassOf nits:DataArtifact .

netex:allowCompanionDiscounts
    rdfs:subClassOf nits:DataArtifact .

netex:allowCumulativeDiscounts
    rdfs:subClassOf nits:DataArtifact .

netex:allowed
    rdfs:subClassOf nits:DataArtifact .

netex:allowedDirections
    rdfs:subClassOf nits:DataArtifact .

netex:allowedForWaitTime
    rdfs:subClassOf nits:DataArtifact .

netex:allowedInChannel
    rdfs:subClassOf nits:DataArtifact .

netex:allowedInCountry
    rdfs:subClassOf nits:DataArtifact .

netex:allowedUse
    rdfs:subClassOf nits:DataArtifact .

netex:alternativeDescriptors
    rdfs:subClassOf nits:DataArtifact .

netex:alternativeNames
    rdfs:subClassOf nits:DataArtifact .

netex:alternativeTexts
    rdfs:subClassOf nits:DataArtifact .

netex:alwaysLit
    rdfs:subClassOf nits:DataArtifact .

netex:amount
    rdfs:subClassOf nits:DataArtifact .

netex:amountFactor
    rdfs:subClassOf nits:DataArtifact .

netex:amountOfPriceUnits
    rdfs:subClassOf nits:DataArtifact .

netex:applicationInstances
    rdfs:subClassOf nits:DataArtifact .

netex:appliesTo
    rdfs:subClassOf nits:DataArtifact .

netex:areas
    rdfs:subClassOf nits:DataArtifact .

netex:armRest
    rdfs:subClassOf nits:DataArtifact .

netex:arrivalDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:arrivalTime
    rdfs:subClassOf nits:DataArtifact .

netex:arrivesForwards
    rdfs:subClassOf nits:DataArtifact .

netex:arrivesFromLeft
    rdfs:subClassOf nits:DataArtifact .

netex:asBraille
    rdfs:subClassOf nits:DataArtifact .

netex:assignments
    rdfs:subClassOf nits:DataArtifact .

netex:assistanceAvailability
    rdfs:subClassOf nits:DataArtifact .

netex:assistanceNeeded
    rdfs:subClassOf nits:DataArtifact .

netex:assistedBoardingLocation
    rdfs:subClassOf nits:DataArtifact .

netex:associatedContract
    rdfs:subClassOf nits:DataArtifact .

netex:atCentre
    rdfs:subClassOf nits:DataArtifact .

netex:attendant
    rdfs:subClassOf nits:DataArtifact .

netex:attributeName
    rdfs:subClassOf nits:DataArtifact .

netex:attributeValue
    rdfs:subClassOf nits:DataArtifact .

netex:audibleSignalsAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:audioAnnouncementType
    rdfs:subClassOf nits:DataArtifact .

netex:audioAnnouncements
    rdfs:subClassOf nits:DataArtifact .

netex:audioAnnouncementsTrigger
    rdfs:subClassOf nits:DataArtifact .

netex:audioInterfaceAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:audioOrVideoIntercom
    rdfs:subClassOf nits:DataArtifact .

netex:audioPassthroughIndicator
    rdfs:subClassOf nits:DataArtifact .

netex:audioTriggerMethod
    rdfs:subClassOf nits:DataArtifact .

netex:audioValidationFeedback
    rdfs:subClassOf nits:DataArtifact .

netex:authorityTypes
    rdfs:subClassOf nits:DataArtifact .

netex:automatedUse
    rdfs:subClassOf nits:DataArtifact .

netex:automatic
    rdfs:subClassOf nits:DataArtifact .

netex:automaticDoor
    rdfs:subClassOf nits:DataArtifact .

netex:automaticDoors
    rdfs:subClassOf nits:DataArtifact .

netex:availableDocks
    rdfs:subClassOf nits:DataArtifact .

netex:availableOnSubscription
    rdfs:subClassOf nits:DataArtifact .

netex:availableVehicles
    rdfs:subClassOf nits:DataArtifact .

netex:averageDelay
    rdfs:subClassOf nits:DataArtifact .

netex:averagePassengers
    rdfs:subClassOf nits:DataArtifact .

netex:back
    rdfs:subClassOf nits:DataArtifact .

netex:backRest
    rdfs:subClassOf nits:DataArtifact .

netex:baggageType
    rdfs:subClassOf nits:DataArtifact .

netex:baggageUseType
    rdfs:subClassOf nits:DataArtifact .

netex:barrier
    rdfs:subClassOf nits:DataArtifact .

netex:basket
    rdfs:subClassOf nits:DataArtifact .

netex:battery
    rdfs:subClassOf nits:DataArtifact .

netex:batteryCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:batteryUsableCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:bayGeometry
    rdfs:subClassOf nits:DataArtifact .

netex:bays
    rdfs:subClassOf nits:DataArtifact .

netex:beaconBackendUrl
    rdfs:subClassOf nits:DataArtifact .

netex:beaconDirection
    rdfs:subClassOf nits:DataArtifact .

netex:beaconProtocol
    rdfs:subClassOf nits:DataArtifact .

netex:beaconType
    rdfs:subClassOf nits:DataArtifact .

netex:bearing
    rdfs:subClassOf nits:DataArtifact .

netex:bearingCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:bearingCompass
    rdfs:subClassOf nits:DataArtifact .

netex:bearingDegrees
    rdfs:subClassOf nits:DataArtifact .

netex:bedLength
    rdfs:subClassOf nits:DataArtifact .

netex:bedType
    rdfs:subClassOf nits:DataArtifact .

netex:berthFacility
    rdfs:subClassOf nits:DataArtifact .

netex:bicycleRackCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:billingPolicy
    rdfs:subClassOf nits:DataArtifact .

netex:blacklistRefs
    rdfs:subClassOf nits:DataArtifact .

netex:blacklists
    rdfs:subClassOf nits:DataArtifact .

netex:blindAccessible
    rdfs:subClassOf nits:DataArtifact .

netex:blockParts
    rdfs:subClassOf nits:DataArtifact .

netex:blockRefs
    rdfs:subClassOf nits:DataArtifact .

netex:blocked
    rdfs:subClassOf nits:DataArtifact .

netex:boardingHeight
    rdfs:subClassOf nits:DataArtifact .

netex:boardingPermission
    rdfs:subClassOf nits:DataArtifact .

netex:boardingPosition
    rdfs:subClassOf nits:DataArtifact .

netex:boardingPositionType
    rdfs:subClassOf nits:DataArtifact .

netex:boardingPositions
    rdfs:subClassOf nits:DataArtifact .

netex:boardingRequestMethod
    rdfs:subClassOf nits:DataArtifact .

netex:boardingSideInDirectionOfTravel
    rdfs:subClassOf nits:DataArtifact .

netex:boardingUse
    rdfs:subClassOf nits:DataArtifact .

netex:bollardCrossing
    rdfs:subClassOf nits:DataArtifact .

netex:bookWhen
    rdfs:subClassOf nits:DataArtifact .

netex:bookingAccess
    rdfs:subClassOf nits:DataArtifact .

netex:bookingArrangements
    rdfs:subClassOf nits:DataArtifact .

netex:bookingChargeType
    rdfs:subClassOf nits:DataArtifact .

netex:bookingContact
    rdfs:subClassOf nits:DataArtifact .

netex:bookingDepositRefundable
    rdfs:subClassOf nits:DataArtifact .

netex:bookingMethods
    rdfs:subClassOf nits:DataArtifact .

netex:bookingNote
    rdfs:subClassOf nits:DataArtifact .

netex:bookingRequired
    rdfs:subClassOf nits:DataArtifact .

netex:bookingUrl
    rdfs:subClassOf nits:DataArtifact .

netex:borderCrossing
    rdfs:subClassOf nits:DataArtifact .

netex:borderPoints
    rdfs:subClassOf nits:DataArtifact .

netex:bothWays
    rdfs:subClassOf nits:DataArtifact .

netex:brailleButtons
    rdfs:subClassOf nits:DataArtifact .

netex:branchLevel
    rdfs:subClassOf nits:DataArtifact .

netex:brandGraphic
    rdfs:subClassOf nits:DataArtifact .

netex:broadType
    rdfs:subClassOf nits:DataArtifact .

netex:buildDate
    rdfs:subClassOf nits:DataArtifact .

netex:buildingName
    rdfs:subClassOf nits:DataArtifact .

netex:bumpCrossing
    rdfs:subClassOf nits:DataArtifact .

netex:busSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:buttonsHeight
    rdfs:subClassOf nits:DataArtifact .

netex:buyWhen
    rdfs:subClassOf nits:DataArtifact .

netex:cage
    rdfs:subClassOf nits:DataArtifact .

netex:calendarDate
    rdfs:subClassOf nits:DataArtifact .

netex:callButtonAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:callButtonHeight
    rdfs:subClassOf nits:DataArtifact .

netex:calls
    rdfs:subClassOf nits:DataArtifact .

netex:canBeAdvertised
    rdfs:subClassOf nits:DataArtifact .

netex:canBeCumulative
    rdfs:subClassOf nits:DataArtifact .

netex:canBeOpened
    rdfs:subClassOf nits:DataArtifact .

netex:canCarry
    rdfs:subClassOf nits:DataArtifact .

netex:canChangeClass
    rdfs:subClassOf nits:DataArtifact .

netex:canInterchange
    rdfs:subClassOf nits:DataArtifact .

netex:canManoeuvre
    rdfs:subClassOf nits:DataArtifact .

netex:canRotate
    rdfs:subClassOf nits:DataArtifact .

netex:canTransfer
    rdfs:subClassOf nits:DataArtifact .

netex:cancellationAllowed
    rdfs:subClassOf nits:DataArtifact .

netex:cancellationPossible
    rdfs:subClassOf nits:DataArtifact .

netex:capacities
    rdfs:subClassOf nits:DataArtifact .

netex:capacity
    rdfs:subClassOf nits:DataArtifact .

netex:cappingRules
    rdfs:subClassOf nits:DataArtifact .

netex:cardNumber
    rdfs:subClassOf nits:DataArtifact .

netex:cardsAccepted
    rdfs:subClassOf nits:DataArtifact .

netex:cctv
    rdfs:subClassOf nits:DataArtifact .

netex:cellPrice
    rdfs:subClassOf nits:DataArtifact .

netex:cells
    rdfs:subClassOf nits:DataArtifact .

netex:centroid
    rdfs:subClassOf nits:DataArtifact .

netex:chains
    rdfs:subClassOf nits:DataArtifact .

netex:changeAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:changeOfDestinationDisplay
    rdfs:subClassOf nits:DataArtifact .

netex:changeOfServiceRequirements
    rdfs:subClassOf nits:DataArtifact .

netex:changeOfTimePossible
    rdfs:subClassOf nits:DataArtifact .

netex:changedAt
    rdfs:subClassOf nits:DataArtifact .

netex:changedBy
    rdfs:subClassOf nits:DataArtifact .

netex:changedSince
    rdfs:subClassOf nits:DataArtifact .

netex:charge
    rdfs:subClassOf nits:DataArtifact .

netex:chargeEnergy
    rdfs:subClassOf nits:DataArtifact .

netex:chargingBasis
    rdfs:subClassOf nits:DataArtifact .

netex:chargingDuration
    rdfs:subClassOf nits:DataArtifact .

netex:chargingMomentType
    rdfs:subClassOf nits:DataArtifact .

netex:chargingVoltage
    rdfs:subClassOf nits:DataArtifact .

netex:chassisNumber
    rdfs:subClassOf nits:DataArtifact .

netex:checkConstraintDelays
    rdfs:subClassOf nits:DataArtifact .

netex:checkConstraintProcess
    rdfs:subClassOf nits:DataArtifact .

netex:checkConstraintThroughputs
    rdfs:subClassOf nits:DataArtifact .

netex:checkConstraints
    rdfs:subClassOf nits:DataArtifact .

netex:checkDirection
    rdfs:subClassOf nits:DataArtifact .

netex:checkProcess
    rdfs:subClassOf nits:DataArtifact .

netex:checkService
    rdfs:subClassOf nits:DataArtifact .

netex:childSeat
    rdfs:subClassOf nits:DataArtifact .

netex:classifications
    rdfs:subClassOf nits:DataArtifact .

netex:client
    rdfs:subClassOf nits:DataArtifact .

netex:coachSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:codePrefix
    rdfs:subClassOf nits:DataArtifact .

netex:codespace
    rdfs:subClassOf nits:DataArtifact .

netex:codespaceAssignments
    rdfs:subClassOf nits:DataArtifact .

netex:codespaces
    rdfs:subClassOf nits:DataArtifact .

netex:collectionNote
    rdfs:subClassOf nits:DataArtifact .

netex:columns
    rdfs:subClassOf nits:DataArtifact .

netex:comment
    rdfs:subClassOf nits:DataArtifact .

netex:commentsAbout
    rdfs:subClassOf nits:DataArtifact .

netex:communicationMethod
    rdfs:subClassOf nits:DataArtifact .

netex:companionProfiles
    rdfs:subClassOf nits:DataArtifact .

netex:companionRelationshipType
    rdfs:subClassOf nits:DataArtifact .

netex:companionSeat
    rdfs:subClassOf nits:DataArtifact .

netex:companyNumber
    rdfs:subClassOf nits:DataArtifact .

netex:compassBearing
    rdfs:subClassOf nits:DataArtifact .

netex:compassOctant
    rdfs:subClassOf nits:DataArtifact .

netex:compatibleWith
    rdfs:subClassOf nits:DataArtifact .

netex:components
    rdfs:subClassOf nits:DataArtifact .

netex:conditionSummary
    rdfs:subClassOf nits:DataArtifact .

netex:configurationConditions
    rdfs:subClassOf nits:DataArtifact .

netex:congestion
    rdfs:subClassOf nits:DataArtifact .

netex:connectingStopPointName
    rdfs:subClassOf nits:DataArtifact .

netex:connectingVehicleModes
    rdfs:subClassOf nits:DataArtifact .

netex:connectionCertainty
    rdfs:subClassOf nits:DataArtifact .

netex:consumptionAmount
    rdfs:subClassOf nits:DataArtifact .

netex:consumptionUnits
    rdfs:subClassOf nits:DataArtifact .

netex:contactDetails
    rdfs:subClassOf nits:DataArtifact .

netex:contacts
    rdfs:subClassOf nits:DataArtifact .

netex:containedIn
    rdfs:subClassOf nits:DataArtifact .

netex:content
    rdfs:subClassOf nits:DataArtifact .

netex:contentValidityConditions
    rdfs:subClassOf nits:DataArtifact .

netex:continuousHandrail
    rdfs:subClassOf nits:DataArtifact .

netex:contractGoverningLaw
    rdfs:subClassOf nits:DataArtifact .

netex:contractType
    rdfs:subClassOf nits:DataArtifact .

netex:contracts
    rdfs:subClassOf nits:DataArtifact .

netex:contrast
    rdfs:subClassOf nits:DataArtifact .

netex:controlCentreCode
    rdfs:subClassOf nits:DataArtifact .

netex:controlCentreNotifyThreshold
    rdfs:subClassOf nits:DataArtifact .

netex:controlCentres
    rdfs:subClassOf nits:DataArtifact .

netex:controllableElements
    rdfs:subClassOf nits:DataArtifact .

netex:controllableElementsInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:controlled
    rdfs:subClassOf nits:DataArtifact .

netex:controlledLocking
    rdfs:subClassOf nits:DataArtifact .

netex:convertible
    rdfs:subClassOf nits:DataArtifact .

netex:couchetteFacility
    rdfs:subClassOf nits:DataArtifact .

netex:count
    rdfs:subClassOf nits:DataArtifact .

netex:counterService
    rdfs:subClassOf nits:DataArtifact .

netex:countries
    rdfs:subClassOf nits:DataArtifact .

netex:countryName
    rdfs:subClassOf nits:DataArtifact .

netex:covered
    rdfs:subClassOf nits:DataArtifact .

netex:creditPolicy
    rdfs:subClassOf nits:DataArtifact .

netex:crewBases
    rdfs:subClassOf nits:DataArtifact .

netex:crossBorder
    rdfs:subClassOf nits:DataArtifact .

netex:crossRoad
    rdfs:subClassOf nits:DataArtifact .

netex:crowding
    rdfs:subClassOf nits:DataArtifact .

netex:cruiseControl
    rdfs:subClassOf nits:DataArtifact .

netex:currenciesAccepted
    rdfs:subClassOf nits:DataArtifact .

netex:currency
    rdfs:subClassOf nits:DataArtifact .

netex:current
    rdfs:subClassOf nits:DataArtifact .

netex:currentAt
    rdfs:subClassOf nits:DataArtifact .

netex:currentType
    rdfs:subClassOf nits:DataArtifact .

netex:customerAccountEntries
    rdfs:subClassOf nits:DataArtifact .

netex:customerAccountStatusType
    rdfs:subClassOf nits:DataArtifact .

netex:customerAccounts
    rdfs:subClassOf nits:DataArtifact .

netex:customerPurchasePackageElements
    rdfs:subClassOf nits:DataArtifact .

netex:customerPurchasePackageEntries
    rdfs:subClassOf nits:DataArtifact .

netex:customerPurchasePackageStatus
    rdfs:subClassOf nits:DataArtifact .

netex:customerPurchasePackages
    rdfs:subClassOf nits:DataArtifact .

netex:customerServiceContactDetails
    rdfs:subClassOf nits:DataArtifact .

netex:customers
    rdfs:subClassOf nits:DataArtifact .

netex:cycleRack
    rdfs:subClassOf nits:DataArtifact .

netex:cycleStorageType
    rdfs:subClassOf nits:DataArtifact .

netex:dataLicenceUrl
    rdfs:subClassOf nits:DataArtifact .

netex:dataObjectPermissions
    rdfs:subClassOf nits:DataArtifact .

netex:dataObjectRequest
    rdfs:subClassOf nits:DataArtifact .

netex:dataObjectServiceCapabilities
    rdfs:subClassOf nits:DataArtifact .

netex:dataRoleType
    rdfs:subClassOf nits:DataArtifact .

netex:dataSources
    rdfs:subClassOf nits:DataArtifact .

netex:date
    rdfs:subClassOf nits:DataArtifact .

netex:dateOfBirth
    rdfs:subClassOf nits:DataArtifact .

netex:datedCalls
    rdfs:subClassOf nits:DataArtifact .

netex:datedPassingTimes
    rdfs:subClassOf nits:DataArtifact .

netex:dayEvent
    rdfs:subClassOf nits:DataArtifact .

netex:dayLength
    rdfs:subClassOf nits:DataArtifact .

netex:dayNumber
    rdfs:subClassOf nits:DataArtifact .

netex:dayOfMonth
    rdfs:subClassOf nits:DataArtifact .

netex:dayOfYear
    rdfs:subClassOf nits:DataArtifact .

netex:dayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:dayOffsetRelativeToMainPart
    rdfs:subClassOf nits:DataArtifact .

netex:dayTypeAssignments
    rdfs:subClassOf nits:DataArtifact .

netex:dayTypes
    rdfs:subClassOf nits:DataArtifact .

netex:daysOfWeek
    rdfs:subClassOf nits:DataArtifact .

netex:deadRunType
    rdfs:subClassOf nits:DataArtifact .

netex:deckLevels
    rdfs:subClassOf nits:DataArtifact .

netex:deckNavigationType
    rdfs:subClassOf nits:DataArtifact .

netex:deckPlacesInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:deckPlans
    rdfs:subClassOf nits:DataArtifact .

netex:deckSpaceCapacities
    rdfs:subClassOf nits:DataArtifact .

netex:deckSpaces
    rdfs:subClassOf nits:DataArtifact .

netex:deckWindowType
    rdfs:subClassOf nits:DataArtifact .

netex:deckWindows
    rdfs:subClassOf nits:DataArtifact .

netex:decks
    rdfs:subClassOf nits:DataArtifact .

netex:defaultCurrency
    rdfs:subClassOf nits:DataArtifact .

netex:defaultDuration
    rdfs:subClassOf nits:DataArtifact .

netex:defaultLanguage
    rdfs:subClassOf nits:DataArtifact .

netex:delegatedResponsibilitySets
    rdfs:subClassOf nits:DataArtifact .

netex:deliveryVariantMediaType
    rdfs:subClassOf nits:DataArtifact .

netex:delta
    rdfs:subClassOf nits:DataArtifact .

netex:deltaValues
    rdfs:subClassOf nits:DataArtifact .

netex:departments
    rdfs:subClassOf nits:DataArtifact .

netex:departsForwards
    rdfs:subClassOf nits:DataArtifact .

netex:departsToRight
    rdfs:subClassOf nits:DataArtifact .

netex:departureDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:departureTime
    rdfs:subClassOf nits:DataArtifact .

netex:depositPolicy
    rdfs:subClassOf nits:DataArtifact .

netex:depositRequired
    rdfs:subClassOf nits:DataArtifact .

netex:depth
    rdfs:subClassOf nits:DataArtifact .

netex:description
    rdfs:subClassOf nits:DataArtifact .

netex:descriptor
    rdfs:subClassOf nits:DataArtifact .

netex:destinationDisplayContext
    rdfs:subClassOf nits:DataArtifact .

netex:destinationDisplayVariantMediaType
    rdfs:subClassOf nits:DataArtifact .

netex:destinationDisplays
    rdfs:subClassOf nits:DataArtifact .

netex:destinations
    rdfs:subClassOf nits:DataArtifact .

netex:detourAccepted
    rdfs:subClassOf nits:DataArtifact .

netex:directionButtonHeight
    rdfs:subClassOf nits:DataArtifact .

netex:directionName
    rdfs:subClassOf nits:DataArtifact .

netex:directionOfUse
    rdfs:subClassOf nits:DataArtifact .

netex:directionType
    rdfs:subClassOf nits:DataArtifact .

netex:disabledDocks
    rdfs:subClassOf nits:DataArtifact .

netex:disabledPriority
    rdfs:subClassOf nits:DataArtifact .

netex:disabledVehicles
    rdfs:subClassOf nits:DataArtifact .

netex:disbarring
    rdfs:subClassOf nits:DataArtifact .

netex:discountAsPercentage
    rdfs:subClassOf nits:DataArtifact .

netex:discountAsValue
    rdfs:subClassOf nits:DataArtifact .

netex:discountBasis
    rdfs:subClassOf nits:DataArtifact .

netex:discountOnlyForFirstPerson
    rdfs:subClassOf nits:DataArtifact .

netex:discountRights
    rdfs:subClassOf nits:DataArtifact .

netex:discrete
    rdfs:subClassOf nits:DataArtifact .

netex:displayAsIcon
    rdfs:subClassOf nits:DataArtifact .

netex:displayAssignmentType
    rdfs:subClassOf nits:DataArtifact .

netex:displayAssignments
    rdfs:subClassOf nits:DataArtifact .

netex:displayPriority
    rdfs:subClassOf nits:DataArtifact .

netex:distance
    rdfs:subClassOf nits:DataArtifact .

netex:distanceFromFront
    rdfs:subClassOf nits:DataArtifact .

netex:distanceFromNearestKerb
    rdfs:subClassOf nits:DataArtifact .

netex:distanceFromStart
    rdfs:subClassOf nits:DataArtifact .

netex:distanceMatrixElements
    rdfs:subClassOf nits:DataArtifact .

netex:distributionAssignments
    rdfs:subClassOf nits:DataArtifact .

netex:distributionChannelType
    rdfs:subClassOf nits:DataArtifact .

netex:distributionChannels
    rdfs:subClassOf nits:DataArtifact .

netex:distributionPoints
    rdfs:subClassOf nits:DataArtifact .

netex:distributionRights
    rdfs:subClassOf nits:DataArtifact .

netex:documentLinks
    rdfs:subClassOf nits:DataArtifact .

netex:dogsMustBeCarried
    rdfs:subClassOf nits:DataArtifact .

netex:door
    rdfs:subClassOf nits:DataArtifact .

netex:doorControlElementHeight
    rdfs:subClassOf nits:DataArtifact .

netex:doorHandleInside
    rdfs:subClassOf nits:DataArtifact .

netex:doorHandleOutside
    rdfs:subClassOf nits:DataArtifact .

netex:doorOrientation
    rdfs:subClassOf nits:DataArtifact .

netex:doorType
    rdfs:subClassOf nits:DataArtifact .

netex:doors
    rdfs:subClassOf nits:DataArtifact .

netex:doorstepMark
    rdfs:subClassOf nits:DataArtifact .

netex:doubleSingleFare
    rdfs:subClassOf nits:DataArtifact .

netex:drinkingWater
    rdfs:subClassOf nits:DataArtifact .

netex:driverAccessDuration
    rdfs:subClassOf nits:DataArtifact .

netex:driverDisplayText
    rdfs:subClassOf nits:DataArtifact .

netex:driverFeeBasis
    rdfs:subClassOf nits:DataArtifact .

netex:driverReturnDuration
    rdfs:subClassOf nits:DataArtifact .

netex:drivingLicenceVerified
    rdfs:subClassOf nits:DataArtifact .

netex:drivingStyle
    rdfs:subClassOf nits:DataArtifact .

netex:dropKerbOutside
    rdfs:subClassOf nits:DataArtifact .

netex:droppedKerb
    rdfs:subClassOf nits:DataArtifact .

netex:duration
    rdfs:subClassOf nits:DataArtifact .

netex:dutyParts
    rdfs:subClassOf nits:DataArtifact .

netex:dynamic
    rdfs:subClassOf nits:DataArtifact .

netex:dynamicDistanceMatrixElement
    rdfs:subClassOf nits:DataArtifact .

netex:earliestDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:earliestDepartureDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:earliestDepartureTime
    rdfs:subClassOf nits:DataArtifact .

netex:earliestTime
    rdfs:subClassOf nits:DataArtifact .

netex:earliestTimeDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:edgeToTrackCenterDistance
    rdfs:subClassOf nits:DataArtifact .

netex:effectiveFrom
    rdfs:subClassOf nits:DataArtifact .

netex:elementAccesses
    rdfs:subClassOf nits:DataArtifact .

netex:email
    rdfs:subClassOf nits:DataArtifact .

netex:emailVerified
    rdfs:subClassOf nits:DataArtifact .

netex:embargoUntil
    rdfs:subClassOf nits:DataArtifact .

netex:enclosed
    rdfs:subClassOf nits:DataArtifact .

netex:encumbranceNeed
    rdfs:subClassOf nits:DataArtifact .

netex:endDate
    rdfs:subClassOf nits:DataArtifact .

netex:endDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:endEvent
    rdfs:subClassOf nits:DataArtifact .

netex:endGeographicalValue
    rdfs:subClassOf nits:DataArtifact .

netex:endOfValidity
    rdfs:subClassOf nits:DataArtifact .

netex:endTime
    rdfs:subClassOf nits:DataArtifact .

netex:endTimeDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:endValue
    rdfs:subClassOf nits:DataArtifact .

netex:energySaving
    rdfs:subClassOf nits:DataArtifact .

netex:entitlementType
    rdfs:subClassOf nits:DataArtifact .

netex:entranceAttention
    rdfs:subClassOf nits:DataArtifact .

netex:entranceRequiresPassport
    rdfs:subClassOf nits:DataArtifact .

netex:entranceRequiresStaffing
    rdfs:subClassOf nits:DataArtifact .

netex:entranceRequiresTicket
    rdfs:subClassOf nits:DataArtifact .

netex:entranceSetting
    rdfs:subClassOf nits:DataArtifact .

netex:entranceToVehicle
    rdfs:subClassOf nits:DataArtifact .

netex:entranceUsageType
    rdfs:subClassOf nits:DataArtifact .

netex:entrances
    rdfs:subClassOf nits:DataArtifact .

netex:equipmentLength
    rdfs:subClassOf nits:DataArtifact .

netex:equipmentPlaces
    rdfs:subClassOf nits:DataArtifact .

netex:equipmentPositions
    rdfs:subClassOf nits:DataArtifact .

netex:equipmentProfiles
    rdfs:subClassOf nits:DataArtifact .

netex:equipmentWidth
    rdfs:subClassOf nits:DataArtifact .

netex:equipments
    rdfs:subClassOf nits:DataArtifact .

netex:escalatorFreeAccess
    rdfs:subClassOf nits:DataArtifact .

netex:escalatorWithLanding
    rdfs:subClassOf nits:DataArtifact .

netex:euroClass
    rdfs:subClassOf nits:DataArtifact .

netex:exchangableFromAnyTime
    rdfs:subClassOf nits:DataArtifact .

netex:exchangableFromDuration
    rdfs:subClassOf nits:DataArtifact .

netex:exchangableFromPercentUse
    rdfs:subClassOf nits:DataArtifact .

netex:exchangableTo
    rdfs:subClassOf nits:DataArtifact .

netex:exchangableUntilAnyTime
    rdfs:subClassOf nits:DataArtifact .

netex:exchangableUntilDuration
    rdfs:subClassOf nits:DataArtifact .

netex:exchangableUntilPercentUse
    rdfs:subClassOf nits:DataArtifact .

netex:exclude
    rdfs:subClassOf nits:DataArtifact .

netex:excluded
    rdfs:subClassOf nits:DataArtifact .

netex:expiryDate
    rdfs:subClassOf nits:DataArtifact .

netex:extensions
    rdfs:subClassOf nits:DataArtifact .

netex:externalFloorSelection
    rdfs:subClassOf nits:DataArtifact .

netex:facilities
    rdfs:subClassOf nits:DataArtifact .

netex:facilitySets
    rdfs:subClassOf nits:DataArtifact .

netex:factor
    rdfs:subClassOf nits:DataArtifact .

netex:fareBasis
    rdfs:subClassOf nits:DataArtifact .

netex:fareClass
    rdfs:subClassOf nits:DataArtifact .

netex:fareClasses
    rdfs:subClassOf nits:DataArtifact .

netex:fareContractEntries
    rdfs:subClassOf nits:DataArtifact .

netex:fareContracts
    rdfs:subClassOf nits:DataArtifact .

netex:fareDemandType
    rdfs:subClassOf nits:DataArtifact .

netex:fareElementsInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:fareScheduledStopPoints
    rdfs:subClassOf nits:DataArtifact .

netex:fareSections
    rdfs:subClassOf nits:DataArtifact .

netex:fareStructureElements
    rdfs:subClassOf nits:DataArtifact .

netex:fareStructureElementsInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:fareStructureType
    rdfs:subClassOf nits:DataArtifact .

netex:fareTables
    rdfs:subClassOf nits:DataArtifact .

netex:featureMembers
    rdfs:subClassOf nits:DataArtifact .

netex:features
    rdfs:subClassOf nits:DataArtifact .

netex:feeBasis
    rdfs:subClassOf nits:DataArtifact .

netex:feePerBag
    rdfs:subClassOf nits:DataArtifact .

netex:finalCarrier
    rdfs:subClassOf nits:DataArtifact .

netex:finalisationDuration
    rdfs:subClassOf nits:DataArtifact .

netex:finishingDuration
    rdfs:subClassOf nits:DataArtifact .

netex:firstArrivalTime
    rdfs:subClassOf nits:DataArtifact .

netex:firstAxleHeight
    rdfs:subClassOf nits:DataArtifact .

netex:firstClassDistance
    rdfs:subClassOf nits:DataArtifact .

netex:firstClassReturn
    rdfs:subClassOf nits:DataArtifact .

netex:firstClassSingle
    rdfs:subClassOf nits:DataArtifact .

netex:firstDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:firstDepartureTime
    rdfs:subClassOf nits:DataArtifact .

netex:firstName
    rdfs:subClassOf nits:DataArtifact .

netex:fixed
    rdfs:subClassOf nits:DataArtifact .

netex:fleets
    rdfs:subClassOf nits:DataArtifact .

netex:flexibleLineType
    rdfs:subClassOf nits:DataArtifact .

netex:flexibleLinkType
    rdfs:subClassOf nits:DataArtifact .

netex:flexiblePointProperties
    rdfs:subClassOf nits:DataArtifact .

netex:flexibleRouteType
    rdfs:subClassOf nits:DataArtifact .

netex:flexibleServiceProperties
    rdfs:subClassOf nits:DataArtifact .

netex:flexibleServiceType
    rdfs:subClassOf nits:DataArtifact .

netex:flexibleStopPlaces
    rdfs:subClassOf nits:DataArtifact .

netex:flights
    rdfs:subClassOf nits:DataArtifact .

netex:floatingVehicles
    rdfs:subClassOf nits:DataArtifact .

netex:flooringStatus
    rdfs:subClassOf nits:DataArtifact .

netex:flooringType
    rdfs:subClassOf nits:DataArtifact .

netex:fontSize
    rdfs:subClassOf nits:DataArtifact .

netex:forAdvertisement
    rdfs:subClassOf nits:DataArtifact .

netex:forAlighting
    rdfs:subClassOf nits:DataArtifact .

netex:forBoarding
    rdfs:subClassOf nits:DataArtifact .

netex:forProduction
    rdfs:subClassOf nits:DataArtifact .

netex:formula
    rdfs:subClassOf nits:DataArtifact .

netex:forwardsOnly
    rdfs:subClassOf nits:DataArtifact .

netex:freeParkingOutOfHours
    rdfs:subClassOf nits:DataArtifact .

netex:freeRecharging
    rdfs:subClassOf nits:DataArtifact .

netex:freeToUse
    rdfs:subClassOf nits:DataArtifact .

netex:frequencyGroups
    rdfs:subClassOf nits:DataArtifact .

netex:frequencyInterval
    rdfs:subClassOf nits:DataArtifact .

netex:frequencyOfUseType
    rdfs:subClassOf nits:DataArtifact .

netex:frequentTravellerDuration
    rdfs:subClassOf nits:DataArtifact .

netex:fromCall
    rdfs:subClassOf nits:DataArtifact .

netex:fromDate
    rdfs:subClassOf nits:DataArtifact .

netex:fromMode
    rdfs:subClassOf nits:DataArtifact .

netex:fromVisitNumber
    rdfs:subClassOf nits:DataArtifact .

netex:frontText
    rdfs:subClassOf nits:DataArtifact .

netex:fuelType
    rdfs:subClassOf nits:DataArtifact .

netex:fuelTypes
    rdfs:subClassOf nits:DataArtifact .

netex:fulfilmentMethodType
    rdfs:subClassOf nits:DataArtifact .

netex:fulfilmentMethods
    rdfs:subClassOf nits:DataArtifact .

netex:fullCharge
    rdfs:subClassOf nits:DataArtifact .

netex:funicularSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:gapToPlatform
    rdfs:subClassOf nits:DataArtifact .

netex:garagePoints
    rdfs:subClassOf nits:DataArtifact .

netex:garages
    rdfs:subClassOf nits:DataArtifact .

netex:gated
    rdfs:subClassOf nits:DataArtifact .

netex:gearTypeDescriotion
    rdfs:subClassOf nits:DataArtifact .

netex:gender
    rdfs:subClassOf nits:DataArtifact .

netex:genderLimitation
    rdfs:subClassOf nits:DataArtifact .

netex:generalGroupOfEntities
    rdfs:subClassOf nits:DataArtifact .

netex:genericParameterAssignment
    rdfs:subClassOf nits:DataArtifact .

netex:genericParameterAssignmentInContext
    rdfs:subClassOf nits:DataArtifact .

netex:geographicalIntervals
    rdfs:subClassOf nits:DataArtifact .

netex:geographicalStructureFactors
    rdfs:subClassOf nits:DataArtifact .

netex:geographicalUnits
    rdfs:subClassOf nits:DataArtifact .

netex:givesEntitlement
    rdfs:subClassOf nits:DataArtifact .

netex:glassDoor
    rdfs:subClassOf nits:DataArtifact .

netex:goesOnCard
    rdfs:subClassOf nits:DataArtifact .

netex:gradient
    rdfs:subClassOf nits:DataArtifact .

netex:gradientType
    rdfs:subClassOf nits:DataArtifact .

netex:gridVoltage
    rdfs:subClassOf nits:DataArtifact .

netex:groundMarkAlignedWithButton
    rdfs:subClassOf nits:DataArtifact .

netex:groupBookingFacility
    rdfs:subClassOf nits:DataArtifact .

netex:groupOfDistanceMatrixElements
    rdfs:subClassOf nits:DataArtifact .

netex:groupOfLinesType
    rdfs:subClassOf nits:DataArtifact .

netex:groupOfTimebands
    rdfs:subClassOf nits:DataArtifact .

netex:groupSizeChanges
    rdfs:subClassOf nits:DataArtifact .

netex:groupsOfDistanceMatrixElements
    rdfs:subClassOf nits:DataArtifact .

netex:groupsOfDistributionChannels
    rdfs:subClassOf nits:DataArtifact .

netex:groupsOfEntities
    rdfs:subClassOf nits:DataArtifact .

netex:groupsOfLines
    rdfs:subClassOf nits:DataArtifact .

netex:groupsOfSaleOfferPackages
    rdfs:subClassOf nits:DataArtifact .

netex:groupsOfSalesOfferPackages
    rdfs:subClassOf nits:DataArtifact .

netex:groupsOfServices
    rdfs:subClassOf nits:DataArtifact .

netex:groupsOfSites
    rdfs:subClassOf nits:DataArtifact .

netex:guaranteed
    rdfs:subClassOf nits:DataArtifact .

netex:guideDogAccess
    rdfs:subClassOf nits:DataArtifact .

netex:guideDogsAllowed
    rdfs:subClassOf nits:DataArtifact .

netex:handWashing
    rdfs:subClassOf nits:DataArtifact .

netex:handrailHeight
    rdfs:subClassOf nits:DataArtifact .

netex:handrailType
    rdfs:subClassOf nits:DataArtifact .

netex:hasArmrest
    rdfs:subClassOf nits:DataArtifact .

netex:hasBlind
    rdfs:subClassOf nits:DataArtifact .

netex:hasDiscountedFares
    rdfs:subClassOf nits:DataArtifact .

netex:hasDoor
    rdfs:subClassOf nits:DataArtifact .

netex:hasDynamicPricing
    rdfs:subClassOf nits:DataArtifact .

netex:hasExchangeFee
    rdfs:subClassOf nits:DataArtifact .

netex:hasFee
    rdfs:subClassOf nits:DataArtifact .

netex:hasFreeConnectingReservations
    rdfs:subClassOf nits:DataArtifact .

netex:hasHoist
    rdfs:subClassOf nits:DataArtifact .

netex:hasLiftOrRamp
    rdfs:subClassOf nits:DataArtifact .

netex:hasMinimumPrice
    rdfs:subClassOf nits:DataArtifact .

netex:hasNotices
    rdfs:subClassOf nits:DataArtifact .

netex:hasPhoto
    rdfs:subClassOf nits:DataArtifact .

netex:hasPower
    rdfs:subClassOf nits:DataArtifact .

netex:hasPowerSupply
    rdfs:subClassOf nits:DataArtifact .

netex:hasPurchaseConditions
    rdfs:subClassOf nits:DataArtifact .

netex:hasQuota
    rdfs:subClassOf nits:DataArtifact .

netex:hasReservationFee
    rdfs:subClassOf nits:DataArtifact .

netex:hasRouteRestrictions
    rdfs:subClassOf nits:DataArtifact .

netex:hasTransferFee
    rdfs:subClassOf nits:DataArtifact .

netex:hasTravelTimeRestrictions
    rdfs:subClassOf nits:DataArtifact .

netex:hasUsbPowerSocket
    rdfs:subClassOf nits:DataArtifact .

netex:hasWheelchairSpaces
    rdfs:subClassOf nits:DataArtifact .

netex:heading
    rdfs:subClassOf nits:DataArtifact .

netex:headroom
    rdfs:subClassOf nits:DataArtifact .

netex:headroomForLuggage
    rdfs:subClassOf nits:DataArtifact .

netex:headwayDisplay
    rdfs:subClassOf nits:DataArtifact .

netex:headways
    rdfs:subClassOf nits:DataArtifact .

netex:heated
    rdfs:subClassOf nits:DataArtifact .

netex:height
    rdfs:subClassOf nits:DataArtifact .

netex:heightFromFloor
    rdfs:subClassOf nits:DataArtifact .

netex:heightFromGround
    rdfs:subClassOf nits:DataArtifact .

netex:heightOfLowCounter
    rdfs:subClassOf nits:DataArtifact .

netex:heightOfMachineInterface
    rdfs:subClassOf nits:DataArtifact .

netex:heightOfSosPanel
    rdfs:subClassOf nits:DataArtifact .

netex:helmet
    rdfs:subClassOf nits:DataArtifact .

netex:hide
    rdfs:subClassOf nits:DataArtifact .

netex:highFloor
    rdfs:subClassOf nits:DataArtifact .

netex:hoist
    rdfs:subClassOf nits:DataArtifact .

netex:hoistOperatingRadius
    rdfs:subClassOf nits:DataArtifact .

netex:holidayType
    rdfs:subClassOf nits:DataArtifact .

netex:holidayTypes
    rdfs:subClassOf nits:DataArtifact .

netex:houseNumber
    rdfs:subClassOf nits:DataArtifact .

netex:identityToken
    rdfs:subClassOf nits:DataArtifact .

netex:identityVerified
    rdfs:subClassOf nits:DataArtifact .

netex:image
    rdfs:subClassOf nits:DataArtifact .

netex:imageUri
    rdfs:subClassOf nits:DataArtifact .

netex:immobilisation
    rdfs:subClassOf nits:DataArtifact .

netex:includedIn
    rdfs:subClassOf nits:DataArtifact .

netex:includes
    rdfs:subClassOf nits:DataArtifact .

netex:includesGroupingType
    rdfs:subClassOf nits:DataArtifact .

netex:individualPassengerInfos
    rdfs:subClassOf nits:DataArtifact .

netex:inductionLoop
    rdfs:subClassOf nits:DataArtifact .

netex:inductionLoopSign
    rdfs:subClassOf nits:DataArtifact .

netex:inductionLoops
    rdfs:subClassOf nits:DataArtifact .

netex:infoLinks
    rdfs:subClassOf nits:DataArtifact .

netex:infoUrl
    rdfs:subClassOf nits:DataArtifact .

netex:initialCarrier
    rdfs:subClassOf nits:DataArtifact .

netex:installmentPaymentMethods
    rdfs:subClassOf nits:DataArtifact .

netex:installmentTypesOfPaymentMethod
    rdfs:subClassOf nits:DataArtifact .

netex:instruction
    rdfs:subClassOf nits:DataArtifact .

netex:insuranceVerified
    rdfs:subClassOf nits:DataArtifact .

netex:integratesAnEscalatorPart
    rdfs:subClassOf nits:DataArtifact .

netex:interchangeAllowed
    rdfs:subClassOf nits:DataArtifact .

netex:internalHeight
    rdfs:subClassOf nits:DataArtifact .

netex:internalWidth
    rdfs:subClassOf nits:DataArtifact .

netex:intervalType
    rdfs:subClassOf nits:DataArtifact .

netex:inverseAllowed
    rdfs:subClassOf nits:DataArtifact .

netex:isAcceptingReturns
    rdfs:subClassOf nits:DataArtifact .

netex:isAccessibleOnVoyage
    rdfs:subClassOf nits:DataArtifact .

netex:isAllowed
    rdfs:subClassOf nits:DataArtifact .

netex:isAutomatic
    rdfs:subClassOf nits:DataArtifact .

netex:isAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:isBetweenSeats
    rdfs:subClassOf nits:DataArtifact .

netex:isByAisle
    rdfs:subClassOf nits:DataArtifact .

netex:isByWindow
    rdfs:subClassOf nits:DataArtifact .

netex:isCard
    rdfs:subClassOf nits:DataArtifact .

netex:isDirect
    rdfs:subClassOf nits:DataArtifact .

netex:isEmergencyExit
    rdfs:subClassOf nits:DataArtifact .

netex:isExchangable
    rdfs:subClassOf nits:DataArtifact .

netex:isFacingAisle
    rdfs:subClassOf nits:DataArtifact .

netex:isFacingWindow
    rdfs:subClassOf nits:DataArtifact .

netex:isFareStage
    rdfs:subClassOf nits:DataArtifact .

netex:isFeeRefundable
    rdfs:subClassOf nits:DataArtifact .

netex:isFirstInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:isFoldup
    rdfs:subClassOf nits:DataArtifact .

netex:isForbidden
    rdfs:subClassOf nits:DataArtifact .

netex:isInEndRow
    rdfs:subClassOf nits:DataArtifact .

netex:isInFrontRow
    rdfs:subClassOf nits:DataArtifact .

netex:isLastInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:isLockable
    rdfs:subClassOf nits:DataArtifact .

netex:isObligatory
    rdfs:subClassOf nits:DataArtifact .

netex:isOperational
    rdfs:subClassOf nits:DataArtifact .

netex:isPersonal
    rdfs:subClassOf nits:DataArtifact .

netex:isPortable
    rdfs:subClassOf nits:DataArtifact .

netex:isReclining
    rdfs:subClassOf nits:DataArtifact .

netex:isRefundable
    rdfs:subClassOf nits:DataArtifact .

netex:isRenting
    rdfs:subClassOf nits:DataArtifact .

netex:isRequired
    rdfs:subClassOf nits:DataArtifact .

netex:isRestricted
    rdfs:subClassOf nits:DataArtifact .

netex:isReversible
    rdfs:subClassOf nits:DataArtifact .

netex:isSmartCard
    rdfs:subClassOf nits:DataArtifact .

netex:isStowable
    rdfs:subClassOf nits:DataArtifact .

netex:isSupplement
    rdfs:subClassOf nits:DataArtifact .

netex:isValid
    rdfs:subClassOf nits:DataArtifact .

netex:isoCode
    rdfs:subClassOf nits:DataArtifact .

netex:itinerary
    rdfs:subClassOf nits:DataArtifact .

netex:jointCheckIn
    rdfs:subClassOf nits:DataArtifact .

netex:journeyAccountings
    rdfs:subClassOf nits:DataArtifact .

netex:journeyDesignator
    rdfs:subClassOf nits:DataArtifact .

netex:journeyDuration
    rdfs:subClassOf nits:DataArtifact .

netex:journeyPartPositions
    rdfs:subClassOf nits:DataArtifact .

netex:journeyParts
    rdfs:subClassOf nits:DataArtifact .

netex:journeyPatternRunTime
    rdfs:subClassOf nits:DataArtifact .

netex:journeyPatterns
    rdfs:subClassOf nits:DataArtifact .

netex:journeys
    rdfs:subClassOf nits:DataArtifact .

netex:keptOpen
    rdfs:subClassOf nits:DataArtifact .

netex:keyScheme
    rdfs:subClassOf nits:DataArtifact .

netex:label
    rdfs:subClassOf nits:DataArtifact .

netex:lamps
    rdfs:subClassOf nits:DataArtifact .

netex:landmark
    rdfs:subClassOf nits:DataArtifact .

netex:lang
    rdfs:subClassOf nits:DataArtifact .

netex:languages
    rdfs:subClassOf nits:DataArtifact .

netex:lastArrivalTime
    rdfs:subClassOf nits:DataArtifact .

netex:lastDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:lastDepartureTime
    rdfs:subClassOf nits:DataArtifact .

netex:lastTripDate
    rdfs:subClassOf nits:DataArtifact .

netex:lastUpdated
    rdfs:subClassOf nits:DataArtifact .

netex:lastVerifiedDate
    rdfs:subClassOf nits:DataArtifact .

netex:latestArrivalDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:latestArrivalTime
    rdfs:subClassOf nits:DataArtifact .

netex:latestBookingTime
    rdfs:subClassOf nits:DataArtifact .

netex:latestDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:latestTime
    rdfs:subClassOf nits:DataArtifact .

netex:latestTimeDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:layers
    rdfs:subClassOf nits:DataArtifact .

netex:layover
    rdfs:subClassOf nits:DataArtifact .

netex:layovers
    rdfs:subClassOf nits:DataArtifact .

netex:leftSideBorder
    rdfs:subClassOf nits:DataArtifact .

netex:legalName
    rdfs:subClassOf nits:DataArtifact .

netex:legalStatus
    rdfs:subClassOf nits:DataArtifact .

netex:length
    rdfs:subClassOf nits:DataArtifact .

netex:levelAccessIntoVehicle
    rdfs:subClassOf nits:DataArtifact .

netex:liftFreeAccess
    rdfs:subClassOf nits:DataArtifact .

netex:lighting
    rdfs:subClassOf nits:DataArtifact .

netex:lightingOnMethod
    rdfs:subClassOf nits:DataArtifact .

netex:likeForLikeRefuelling
    rdfs:subClassOf nits:DataArtifact .

netex:limitationGroupingType
    rdfs:subClassOf nits:DataArtifact .

netex:limitationSetSelectionType
    rdfs:subClassOf nits:DataArtifact .

netex:limitations
    rdfs:subClassOf nits:DataArtifact .

netex:limitedUse
    rdfs:subClassOf nits:DataArtifact .

netex:lineDirections
    rdfs:subClassOf nits:DataArtifact .

netex:lineMap
    rdfs:subClassOf nits:DataArtifact .

netex:lineName
    rdfs:subClassOf nits:DataArtifact .

netex:lineSectionPointType
    rdfs:subClassOf nits:DataArtifact .

netex:lineType
    rdfs:subClassOf nits:DataArtifact .

netex:lines
    rdfs:subClassOf nits:DataArtifact .

netex:linesInDirectionRefs
    rdfs:subClassOf nits:DataArtifact .

netex:link
    rdfs:subClassOf nits:DataArtifact .

netex:linkSequenceProjection
    rdfs:subClassOf nits:DataArtifact .

netex:links
    rdfs:subClassOf nits:DataArtifact .

netex:linksInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:localControl
    rdfs:subClassOf nits:DataArtifact .

netex:localResident
    rdfs:subClassOf nits:DataArtifact .

netex:localServices
    rdfs:subClassOf nits:DataArtifact .

netex:locale
    rdfs:subClassOf nits:DataArtifact .

netex:locatableSpotType
    rdfs:subClassOf nits:DataArtifact .

netex:locationSystem
    rdfs:subClassOf nits:DataArtifact .

netex:lock
    rdfs:subClassOf nits:DataArtifact .

netex:lockedAccess
    rdfs:subClassOf nits:DataArtifact .

netex:locker
    rdfs:subClassOf nits:DataArtifact .

netex:lockerDepth
    rdfs:subClassOf nits:DataArtifact .

netex:lockerFee
    rdfs:subClassOf nits:DataArtifact .

netex:lockerHeight
    rdfs:subClassOf nits:DataArtifact .

netex:lockerType
    rdfs:subClassOf nits:DataArtifact .

netex:lockerWidth
    rdfs:subClassOf nits:DataArtifact .

netex:lockingMechanism
    rdfs:subClassOf nits:DataArtifact .

netex:lockingType
    rdfs:subClassOf nits:DataArtifact .

netex:logEntries
    rdfs:subClassOf nits:DataArtifact .

netex:logInRequired
    rdfs:subClassOf nits:DataArtifact .

netex:lowCounterAccess
    rdfs:subClassOf nits:DataArtifact .

netex:lowFloor
    rdfs:subClassOf nits:DataArtifact .

netex:lowerHandrailHeight
    rdfs:subClassOf nits:DataArtifact .

netex:luggageAllowanceType
    rdfs:subClassOf nits:DataArtifact .

netex:luggageAllowed
    rdfs:subClassOf nits:DataArtifact .

netex:luggageChargingBasis
    rdfs:subClassOf nits:DataArtifact .

netex:luggageMaximalWeigth
    rdfs:subClassOf nits:DataArtifact .

netex:luggageSpotType
    rdfs:subClassOf nits:DataArtifact .

netex:luggageSpots
    rdfs:subClassOf nits:DataArtifact .

netex:luggageTrolleys
    rdfs:subClassOf nits:DataArtifact .

netex:machineReadable
    rdfs:subClassOf nits:DataArtifact .

netex:magneticInductionLoop
    rdfs:subClassOf nits:DataArtifact .

netex:mainTerminusForPlaces
    rdfs:subClassOf nits:DataArtifact .

netex:mandatoryProduct
    rdfs:subClassOf nits:DataArtifact .

netex:manufacturer
    rdfs:subClassOf nits:DataArtifact .

netex:mark
    rdfs:subClassOf nits:DataArtifact .

netex:markUrl
    rdfs:subClassOf nits:DataArtifact .

netex:markedAs
    rdfs:subClassOf nits:DataArtifact .

netex:markingStatus
    rdfs:subClassOf nits:DataArtifact .

netex:maximalFrequency
    rdfs:subClassOf nits:DataArtifact .

netex:maximumAccess
    rdfs:subClassOf nits:DataArtifact .

netex:maximumAge
    rdfs:subClassOf nits:DataArtifact .

netex:maximumAutomaticWaitTime
    rdfs:subClassOf nits:DataArtifact .

netex:maximumBagDepth
    rdfs:subClassOf nits:DataArtifact .

netex:maximumBagHeight
    rdfs:subClassOf nits:DataArtifact .

netex:maximumBagWeight
    rdfs:subClassOf nits:DataArtifact .

netex:maximumBagWidth
    rdfs:subClassOf nits:DataArtifact .

netex:maximumBookingDuration
    rdfs:subClassOf nits:DataArtifact .

netex:maximumChargingPower
    rdfs:subClassOf nits:DataArtifact .

netex:maximumDistance
    rdfs:subClassOf nits:DataArtifact .

netex:maximumDuration
    rdfs:subClassOf nits:DataArtifact .

netex:maximumFlowPerMinute
    rdfs:subClassOf nits:DataArtifact .

netex:maximumHeadwayInterval
    rdfs:subClassOf nits:DataArtifact .

netex:maximumHeight
    rdfs:subClassOf nits:DataArtifact .

netex:maximumInterchangeWindow
    rdfs:subClassOf nits:DataArtifact .

netex:maximumLength
    rdfs:subClassOf nits:DataArtifact .

netex:maximumLikelyDelay
    rdfs:subClassOf nits:DataArtifact .

netex:maximumLimitPrice
    rdfs:subClassOf nits:DataArtifact .

netex:maximumLimitPriceAsPercentage
    rdfs:subClassOf nits:DataArtifact .

netex:maximumLoad
    rdfs:subClassOf nits:DataArtifact .

netex:maximumNumberItems
    rdfs:subClassOf nits:DataArtifact .

netex:maximumNumberOfBerths
    rdfs:subClassOf nits:DataArtifact .

netex:maximumNumberOfFailToCheckOutEvents
    rdfs:subClassOf nits:DataArtifact .

netex:maximumNumberOfInterchanges
    rdfs:subClassOf nits:DataArtifact .

netex:maximumNumberOfNamedTransferees
    rdfs:subClassOf nits:DataArtifact .

netex:maximumNumberOfNightsAway
    rdfs:subClassOf nits:DataArtifact .

netex:maximumNumberOfPersons
    rdfs:subClassOf nits:DataArtifact .

netex:maximumNumberOfSteps
    rdfs:subClassOf nits:DataArtifact .

netex:maximumNumberOfSuspensionsPerTerm
    rdfs:subClassOf nits:DataArtifact .

netex:maximumNumberOfTrips
    rdfs:subClassOf nits:DataArtifact .

netex:maximumNumberToReserve
    rdfs:subClassOf nits:DataArtifact .

netex:maximumPassengers
    rdfs:subClassOf nits:DataArtifact .

netex:maximumPeriodBeforeDeparture
    rdfs:subClassOf nits:DataArtifact .

netex:maximumPersonsDiscounted
    rdfs:subClassOf nits:DataArtifact .

netex:maximumPersonsFree
    rdfs:subClassOf nits:DataArtifact .

netex:maximumPower
    rdfs:subClassOf nits:DataArtifact .

netex:maximumPowerAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:maximumPrice
    rdfs:subClassOf nits:DataArtifact .

netex:maximumPriceAsMultiple
    rdfs:subClassOf nits:DataArtifact .

netex:maximumPriceAsPercentage
    rdfs:subClassOf nits:DataArtifact .

netex:maximumRange
    rdfs:subClassOf nits:DataArtifact .

netex:maximumRecline
    rdfs:subClassOf nits:DataArtifact .

netex:maximumSpeed
    rdfs:subClassOf nits:DataArtifact .

netex:maximumSpots
    rdfs:subClassOf nits:DataArtifact .

netex:maximumStandingDuration
    rdfs:subClassOf nits:DataArtifact .

netex:maximumStay
    rdfs:subClassOf nits:DataArtifact .

netex:maximumTimeToMakeATransfer
    rdfs:subClassOf nits:DataArtifact .

netex:maximumTransferTime
    rdfs:subClassOf nits:DataArtifact .

netex:maximumVelocity
    rdfs:subClassOf nits:DataArtifact .

netex:maximumWaitTime
    rdfs:subClassOf nits:DataArtifact .

netex:maximumWeight
    rdfs:subClassOf nits:DataArtifact .

netex:maximumWidth
    rdfs:subClassOf nits:DataArtifact .

netex:mayBeSkipped
    rdfs:subClassOf nits:DataArtifact .

netex:mediaType
    rdfs:subClassOf nits:DataArtifact .

netex:mediumAccessDevices
    rdfs:subClassOf nits:DataArtifact .

netex:meetingPointAssignments
    rdfs:subClassOf nits:DataArtifact .

netex:meetingPointServiceType
    rdfs:subClassOf nits:DataArtifact .

netex:members
    rdfs:subClassOf nits:DataArtifact .

netex:method
    rdfs:subClassOf nits:DataArtifact .

netex:methodName
    rdfs:subClassOf nits:DataArtifact .

netex:metroSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:minimalFrequency
    rdfs:subClassOf nits:DataArtifact .

netex:minimumAccess
    rdfs:subClassOf nits:DataArtifact .

netex:minimumAge
    rdfs:subClassOf nits:DataArtifact .

netex:minimumBookingDuration
    rdfs:subClassOf nits:DataArtifact .

netex:minimumDuration
    rdfs:subClassOf nits:DataArtifact .

netex:minimumHeadwayInterval
    rdfs:subClassOf nits:DataArtifact .

netex:minimumHeight
    rdfs:subClassOf nits:DataArtifact .

netex:minimumLength
    rdfs:subClassOf nits:DataArtifact .

netex:minimumLikelyDelay
    rdfs:subClassOf nits:DataArtifact .

netex:minimumLimitPrice
    rdfs:subClassOf nits:DataArtifact .

netex:minimumLimitPriceAsPercentage
    rdfs:subClassOf nits:DataArtifact .

netex:minimumNumberOfCardHolders
    rdfs:subClassOf nits:DataArtifact .

netex:minimumNumberOfNightsAway
    rdfs:subClassOf nits:DataArtifact .

netex:minimumNumberOfPassengers
    rdfs:subClassOf nits:DataArtifact .

netex:minimumNumberOfPersons
    rdfs:subClassOf nits:DataArtifact .

netex:minimumNumberOfSteps
    rdfs:subClassOf nits:DataArtifact .

netex:minimumNumberToReserve
    rdfs:subClassOf nits:DataArtifact .

netex:minimumOvertakingWidth
    rdfs:subClassOf nits:DataArtifact .

netex:minimumPeriodBeforeDeparture
    rdfs:subClassOf nits:DataArtifact .

netex:minimumPrice
    rdfs:subClassOf nits:DataArtifact .

netex:minimumPriceAsMultiple
    rdfs:subClassOf nits:DataArtifact .

netex:minimumPriceAsPercentage
    rdfs:subClassOf nits:DataArtifact .

netex:minimumStayType
    rdfs:subClassOf nits:DataArtifact .

netex:minimumTimeBeforeReentry
    rdfs:subClassOf nits:DataArtifact .

netex:minimumTransferTime
    rdfs:subClassOf nits:DataArtifact .

netex:minimumTurningCircle
    rdfs:subClassOf nits:DataArtifact .

netex:minimumUnits
    rdfs:subClassOf nits:DataArtifact .

netex:minimumWidth
    rdfs:subClassOf nits:DataArtifact .

netex:mirrorOnOppositeSide
    rdfs:subClassOf nits:DataArtifact .

netex:mobileDeviceTickets
    rdfs:subClassOf nits:DataArtifact .

netex:mobilePhoneCoverage
    rdfs:subClassOf nits:DataArtifact .

netex:mobilityImpairedAccess
    rdfs:subClassOf nits:DataArtifact .

netex:mobilityNeed
    rdfs:subClassOf nits:DataArtifact .

netex:mobilityRestrictedTravellerDuration
    rdfs:subClassOf nits:DataArtifact .

netex:mode
    rdfs:subClassOf nits:DataArtifact .

netex:modeRestrictionAssessments
    rdfs:subClassOf nits:DataArtifact .

netex:modification
    rdfs:subClassOf nits:DataArtifact .

netex:modificationSet
    rdfs:subClassOf nits:DataArtifact .

netex:monitored
    rdfs:subClassOf nits:DataArtifact .

netex:monitoredBays
    rdfs:subClassOf nits:DataArtifact .

netex:monitoringRemoteControl
    rdfs:subClassOf nits:DataArtifact .

netex:month
    rdfs:subClassOf nits:DataArtifact .

netex:monthDayOnWhichAgeApplies
    rdfs:subClassOf nits:DataArtifact .

netex:monthOfYear
    rdfs:subClassOf nits:DataArtifact .

netex:monthValidityOffsets
    rdfs:subClassOf nits:DataArtifact .

netex:mustCarry
    rdfs:subClassOf nits:DataArtifact .

netex:mustReserveWholeCompartment
    rdfs:subClassOf nits:DataArtifact .

netex:mustReside
    rdfs:subClassOf nits:DataArtifact .

netex:mustReturnToSameBay
    rdfs:subClassOf nits:DataArtifact .

netex:name
    rdfs:subClassOf nits:DataArtifact .

netex:nameOfClass
    rdfs:subClassOf nits:DataArtifact .

netex:nameOnRouting
    rdfs:subClassOf nits:DataArtifact .

netex:nameSuffix
    rdfs:subClassOf nits:DataArtifact .

netex:nameType
    rdfs:subClassOf nits:DataArtifact .

netex:nature
    rdfs:subClassOf nits:DataArtifact .

netex:navigationType
    rdfs:subClassOf nits:DataArtifact .

netex:nearTopographicPlaces
    rdfs:subClassOf nits:DataArtifact .

netex:necessaryForceToOpen
    rdfs:subClassOf nits:DataArtifact .

netex:needRanking
    rdfs:subClassOf nits:DataArtifact .

netex:neighbours
    rdfs:subClassOf nits:DataArtifact .

netex:newValue
    rdfs:subClassOf nits:DataArtifact .

netex:nightTrain
    rdfs:subClassOf nits:DataArtifact .

netex:noCashPayment
    rdfs:subClassOf nits:DataArtifact .

netex:nominalVoltage
    rdfs:subClassOf nits:DataArtifact .

netex:note
    rdfs:subClassOf nits:DataArtifact .

netex:notice
    rdfs:subClassOf nits:DataArtifact .

netex:notices
    rdfs:subClassOf nits:DataArtifact .

netex:number
    rdfs:subClassOf nits:DataArtifact .

netex:numberOFDrivers
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfBaysWithRecharging
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfCars
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfExchangesAllowed
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfFlights
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfFreeConnectingReservations
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfGates
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfGears
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfLockers
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfMachines
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfParkingLevels
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfProposedTrips
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfServers
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfSpaces
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfSteps
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfTills
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfToilets
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfTravellersCarried
    rdfs:subClassOf nits:DataArtifact .

netex:numberOfUnits
    rdfs:subClassOf nits:DataArtifact .

netex:numberingFromFront
    rdfs:subClassOf nits:DataArtifact .

netex:numberingFromLeft
    rdfs:subClassOf nits:DataArtifact .

netex:occasionalTravellerDuration
    rdfs:subClassOf nits:DataArtifact .

netex:oldValue
    rdfs:subClassOf nits:DataArtifact .

netex:onBecomingEligiblePolicy
    rdfs:subClassOf nits:DataArtifact .

netex:onCeasingToBeEligiblePolicy
    rdfs:subClassOf nits:DataArtifact .

netex:onboardStays
    rdfs:subClassOf nits:DataArtifact .

netex:oneForNPersons
    rdfs:subClassOf nits:DataArtifact .

netex:onlinePurchaseForCollection
    rdfs:subClassOf nits:DataArtifact .

netex:onlinePurchaseForETicket
    rdfs:subClassOf nits:DataArtifact .

netex:onlinePurchaseForSelfPrintTicket
    rdfs:subClassOf nits:DataArtifact .

netex:onlineServices
    rdfs:subClassOf nits:DataArtifact .

netex:onlyAtCertainDistributionPoints
    rdfs:subClassOf nits:DataArtifact .

netex:onwardCalls
    rdfs:subClassOf nits:DataArtifact .

netex:onwardLinks
    rdfs:subClassOf nits:DataArtifact .

netex:operatingDays
    rdfs:subClassOf nits:DataArtifact .

netex:operatingPeriods
    rdfs:subClassOf nits:DataArtifact .

netex:operationalContexts
    rdfs:subClassOf nits:DataArtifact .

netex:operationalNumber
    rdfs:subClassOf nits:DataArtifact .

netex:operationalOrientation
    rdfs:subClassOf nits:DataArtifact .

netex:operatorActivities
    rdfs:subClassOf nits:DataArtifact .

netex:operators
    rdfs:subClassOf nits:DataArtifact .

netex:organisationRoleType
    rdfs:subClassOf nits:DataArtifact .

netex:organisationType
    rdfs:subClassOf nits:DataArtifact .

netex:orientation
    rdfs:subClassOf nits:DataArtifact .

netex:otherCountries
    rdfs:subClassOf nits:DataArtifact .

netex:otherFacilities
    rdfs:subClassOf nits:DataArtifact .

netex:otherModes
    rdfs:subClassOf nits:DataArtifact .

netex:otherTransportModes
    rdfs:subClassOf nits:DataArtifact .

netex:outOfService
    rdfs:subClassOf nits:DataArtifact .

netex:overnightParkingPermitted
    rdfs:subClassOf nits:DataArtifact .

netex:overtakingWidth
    rdfs:subClassOf nits:DataArtifact .

netex:ownResponsibilitySets
    rdfs:subClassOf nits:DataArtifact .

netex:panicButton
    rdfs:subClassOf nits:DataArtifact .

netex:parkingChargeBand
    rdfs:subClassOf nits:DataArtifact .

netex:parkingChargeBands
    rdfs:subClassOf nits:DataArtifact .

netex:parkingComponents
    rdfs:subClassOf nits:DataArtifact .

netex:parkingLayout
    rdfs:subClassOf nits:DataArtifact .

netex:parkingPaymentCode
    rdfs:subClassOf nits:DataArtifact .

netex:parkingPaymentProcess
    rdfs:subClassOf nits:DataArtifact .

netex:parkingProperties
    rdfs:subClassOf nits:DataArtifact .

netex:parkingReservation
    rdfs:subClassOf nits:DataArtifact .

netex:parkingStayType
    rdfs:subClassOf nits:DataArtifact .

netex:parkingType
    rdfs:subClassOf nits:DataArtifact .

netex:parkingUserType
    rdfs:subClassOf nits:DataArtifact .

netex:parkingUserTypes
    rdfs:subClassOf nits:DataArtifact .

netex:parkingVehicleType
    rdfs:subClassOf nits:DataArtifact .

netex:parkingVehicleTypes
    rdfs:subClassOf nits:DataArtifact .

netex:parkingVisibility
    rdfs:subClassOf nits:DataArtifact .

netex:partial
    rdfs:subClassOf nits:DataArtifact .

netex:parts
    rdfs:subClassOf nits:DataArtifact .

netex:passageType
    rdfs:subClassOf nits:DataArtifact .

netex:passengerAtStopTimes
    rdfs:subClassOf nits:DataArtifact .

netex:passengerCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:passengerSpaceType
    rdfs:subClassOf nits:DataArtifact .

netex:passengerSpotAllocations
    rdfs:subClassOf nits:DataArtifact .

netex:passengerSpots
    rdfs:subClassOf nits:DataArtifact .

netex:passengerVehicleSpots
    rdfs:subClassOf nits:DataArtifact .

netex:passengersPerMinute
    rdfs:subClassOf nits:DataArtifact .

netex:passingThrough
    rdfs:subClassOf nits:DataArtifact .

netex:passingTimeDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:passingTimes
    rdfs:subClassOf nits:DataArtifact .

netex:pathHeading
    rdfs:subClassOf nits:DataArtifact .

netex:pathInstructions
    rdfs:subClassOf nits:DataArtifact .

netex:pathJunctions
    rdfs:subClassOf nits:DataArtifact .

netex:pathLinks
    rdfs:subClassOf nits:DataArtifact .

netex:pathLinksInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:paymentMeans
    rdfs:subClassOf nits:DataArtifact .

netex:paymentMethod
    rdfs:subClassOf nits:DataArtifact .

netex:paymentMethods
    rdfs:subClassOf nits:DataArtifact .

netex:pedestal
    rdfs:subClassOf nits:DataArtifact .

netex:pedestrianLights
    rdfs:subClassOf nits:DataArtifact .

netex:penaltyFee
    rdfs:subClassOf nits:DataArtifact .

netex:penaltyIfWithoutTicket
    rdfs:subClassOf nits:DataArtifact .

netex:penaltyPolicyType
    rdfs:subClassOf nits:DataArtifact .

netex:period
    rdfs:subClassOf nits:DataArtifact .

netex:periodicity
    rdfs:subClassOf nits:DataArtifact .

netex:personCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:personalOperationType
    rdfs:subClassOf nits:DataArtifact .

netex:petsAllowed
    rdfs:subClassOf nits:DataArtifact .

netex:phone
    rdfs:subClassOf nits:DataArtifact .

netex:phoneVerified
    rdfs:subClassOf nits:DataArtifact .

netex:photo
    rdfs:subClassOf nits:DataArtifact .

netex:placeCentre
    rdfs:subClassOf nits:DataArtifact .

netex:placeEquipments
    rdfs:subClassOf nits:DataArtifact .

netex:placeName
    rdfs:subClassOf nits:DataArtifact .

netex:placeTypes
    rdfs:subClassOf nits:DataArtifact .

netex:placement
    rdfs:subClassOf nits:DataArtifact .

netex:placesInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:planned
    rdfs:subClassOf nits:DataArtifact .

netex:plateCode
    rdfs:subClassOf nits:DataArtifact .

netex:platformHeight
    rdfs:subClassOf nits:DataArtifact .

netex:plugType
    rdfs:subClassOf nits:DataArtifact .

netex:point
    rdfs:subClassOf nits:DataArtifact .

netex:pointNumber
    rdfs:subClassOf nits:DataArtifact .

netex:pointOfInterestClassificationHierarchies
    rdfs:subClassOf nits:DataArtifact .

netex:pointOfInterestSpaceType
    rdfs:subClassOf nits:DataArtifact .

netex:points
    rdfs:subClassOf nits:DataArtifact .

netex:pointsInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:pointsOfInterest
    rdfs:subClassOf nits:DataArtifact .

netex:poolingPolicyUrl
    rdfs:subClassOf nits:DataArtifact .

netex:poolsOfVehicles
    rdfs:subClassOf nits:DataArtifact .

netex:positionInTrain
    rdfs:subClassOf nits:DataArtifact .

netex:positionOfTrainElement
    rdfs:subClassOf nits:DataArtifact .

netex:possibleInstallmenttIntervals
    rdfs:subClassOf nits:DataArtifact .

netex:postCode
    rdfs:subClassOf nits:DataArtifact .

netex:postCodeExtension
    rdfs:subClassOf nits:DataArtifact .

netex:postalAddress
    rdfs:subClassOf nits:DataArtifact .

netex:postalRegion
    rdfs:subClassOf nits:DataArtifact .

netex:powerCouplingType
    rdfs:subClassOf nits:DataArtifact .

netex:pramPlaceCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:precision
    rdfs:subClassOf nits:DataArtifact .

netex:preparationDuration
    rdfs:subClassOf nits:DataArtifact .

netex:prerequisites
    rdfs:subClassOf nits:DataArtifact .

netex:presentationPosition
    rdfs:subClassOf nits:DataArtifact .

netex:previousCalls
    rdfs:subClassOf nits:DataArtifact .

netex:priceGroups
    rdfs:subClassOf nits:DataArtifact .

netex:priceUnits
    rdfs:subClassOf nits:DataArtifact .

netex:prices
    rdfs:subClassOf nits:DataArtifact .

netex:pricesFor
    rdfs:subClassOf nits:DataArtifact .

netex:pricingBasis
    rdfs:subClassOf nits:DataArtifact .

netex:pricingParameterSet
    rdfs:subClassOf nits:DataArtifact .

netex:pricingServices
    rdfs:subClassOf nits:DataArtifact .

netex:primaryMode
    rdfs:subClassOf nits:DataArtifact .

netex:primaryOrientation
    rdfs:subClassOf nits:DataArtifact .

netex:principalCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:print
    rdfs:subClassOf nits:DataArtifact .

netex:priority
    rdfs:subClassOf nits:DataArtifact .

netex:privateCode
    rdfs:subClassOf nits:DataArtifact .

netex:privateContactDetails
    rdfs:subClassOf nits:DataArtifact .

netex:productType
    rdfs:subClassOf nits:DataArtifact .

netex:prohibitedForHazardousMaterials
    rdfs:subClassOf nits:DataArtifact .

netex:projection
    rdfs:subClassOf nits:DataArtifact .

netex:projections
    rdfs:subClassOf nits:DataArtifact .

netex:proofRequired
    rdfs:subClassOf nits:DataArtifact .

netex:properties
    rdfs:subClassOf nits:DataArtifact .

netex:propertyKeptForDuration
    rdfs:subClassOf nits:DataArtifact .

netex:proposedByServices
    rdfs:subClassOf nits:DataArtifact .

netex:proposingServices
    rdfs:subClassOf nits:DataArtifact .

netex:propulsionType
    rdfs:subClassOf nits:DataArtifact .

netex:propulsionTypes
    rdfs:subClassOf nits:DataArtifact .

netex:providesCard
    rdfs:subClassOf nits:DataArtifact .

netex:province
    rdfs:subClassOf nits:DataArtifact .

netex:psychosensoryNeed
    rdfs:subClassOf nits:DataArtifact .

netex:public
    rdfs:subClassOf nits:DataArtifact .

netex:publicUse
    rdfs:subClassOf nits:DataArtifact .

netex:publicityChannel
    rdfs:subClassOf nits:DataArtifact .

netex:pump
    rdfs:subClassOf nits:DataArtifact .

netex:purchaseAction
    rdfs:subClassOf nits:DataArtifact .

netex:purchaseMoment
    rdfs:subClassOf nits:DataArtifact .

netex:purchaseWhen
    rdfs:subClassOf nits:DataArtifact .

netex:pushchairCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:qualificationPercent
    rdfs:subClassOf nits:DataArtifact .

netex:qualifierName
    rdfs:subClassOf nits:DataArtifact .

netex:qualityStructureFactors
    rdfs:subClassOf nits:DataArtifact .

netex:quay
    rdfs:subClassOf nits:DataArtifact .

netex:quayAlignments
    rdfs:subClassOf nits:DataArtifact .

netex:quayType
    rdfs:subClassOf nits:DataArtifact .

netex:quays
    rdfs:subClassOf nits:DataArtifact .

netex:queueManagement
    rdfs:subClassOf nits:DataArtifact .

netex:queuingSeatedPossible
    rdfs:subClassOf nits:DataArtifact .

netex:railSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:railedQueue
    rdfs:subClassOf nits:DataArtifact .

netex:raisedButtons
    rdfs:subClassOf nits:DataArtifact .

netex:ramp
    rdfs:subClassOf nits:DataArtifact .

netex:rampDoorbell
    rdfs:subClassOf nits:DataArtifact .

netex:rampFreeAccess
    rdfs:subClassOf nits:DataArtifact .

netex:range
    rdfs:subClassOf nits:DataArtifact .

netex:rangeBetweenRefuelling
    rdfs:subClassOf nits:DataArtifact .

netex:rank
    rdfs:subClassOf nits:DataArtifact .

netex:ranking
    rdfs:subClassOf nits:DataArtifact .

netex:reachedFloorAnnouncement
    rdfs:subClassOf nits:DataArtifact .

netex:realTimeOccupancyAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:reason
    rdfs:subClassOf nits:DataArtifact .

netex:rechargingAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:rechargingPointAssignments
    rdfs:subClassOf nits:DataArtifact .

netex:rechargingProcessType
    rdfs:subClassOf nits:DataArtifact .

netex:rechargingSteps
    rdfs:subClassOf nits:DataArtifact .

netex:recognizable
    rdfs:subClassOf nits:DataArtifact .

netex:recycling
    rdfs:subClassOf nits:DataArtifact .

netex:refundBasis
    rdfs:subClassOf nits:DataArtifact .

netex:registrationDate
    rdfs:subClassOf nits:DataArtifact .

netex:registrationNumber
    rdfs:subClassOf nits:DataArtifact .

netex:registrationRequired
    rdfs:subClassOf nits:DataArtifact .

netex:relationToVehicle
    rdfs:subClassOf nits:DataArtifact .

netex:relativeLevelOrder
    rdfs:subClassOf nits:DataArtifact .

netex:relativeRanking
    rdfs:subClassOf nits:DataArtifact .

netex:relativeWeighting
    rdfs:subClassOf nits:DataArtifact .

netex:reliefOpportunities
    rdfs:subClassOf nits:DataArtifact .

netex:remarks
    rdfs:subClassOf nits:DataArtifact .

netex:remoteControl
    rdfs:subClassOf nits:DataArtifact .

netex:rentalPenaltyPolicyType
    rdfs:subClassOf nits:DataArtifact .

netex:rentalPolicyUrl
    rdfs:subClassOf nits:DataArtifact .

netex:replaces
    rdfs:subClassOf nits:DataArtifact .

netex:requestMethod
    rdfs:subClassOf nits:DataArtifact .

netex:requestMethodType
    rdfs:subClassOf nits:DataArtifact .

netex:requestStop
    rdfs:subClassOf nits:DataArtifact .

netex:requiresAccount
    rdfs:subClassOf nits:DataArtifact .

netex:requiresBookingReference
    rdfs:subClassOf nits:DataArtifact .

netex:requiresCard
    rdfs:subClassOf nits:DataArtifact .

netex:requiresDeposit
    rdfs:subClassOf nits:DataArtifact .

netex:requiresEmailAddress
    rdfs:subClassOf nits:DataArtifact .

netex:requiresEntitlement
    rdfs:subClassOf nits:DataArtifact .

netex:requiresNightsAway
    rdfs:subClassOf nits:DataArtifact .

netex:requiresPhoto
    rdfs:subClassOf nits:DataArtifact .

netex:requiresPositiveBalance
    rdfs:subClassOf nits:DataArtifact .

netex:requiresRegistration
    rdfs:subClassOf nits:DataArtifact .

netex:requiresReservation
    rdfs:subClassOf nits:DataArtifact .

netex:requiresValidation
    rdfs:subClassOf nits:DataArtifact .

netex:resellWhen
    rdfs:subClassOf nits:DataArtifact .

netex:reservationChargeType
    rdfs:subClassOf nits:DataArtifact .

netex:reservationRequired
    rdfs:subClassOf nits:DataArtifact .

netex:reservationUrl
    rdfs:subClassOf nits:DataArtifact .

netex:reservingRequirements
    rdfs:subClassOf nits:DataArtifact .

netex:residenceType
    rdfs:subClassOf nits:DataArtifact .

netex:residencyType
    rdfs:subClassOf nits:DataArtifact .

netex:resides
    rdfs:subClassOf nits:DataArtifact .

netex:responsibilities
    rdfs:subClassOf nits:DataArtifact .

netex:responsibilityRoles
    rdfs:subClassOf nits:DataArtifact .

netex:responsibilitySets
    rdfs:subClassOf nits:DataArtifact .

netex:restStopDistance
    rdfs:subClassOf nits:DataArtifact .

netex:restricted
    rdfs:subClassOf nits:DataArtifact .

netex:restrictedLine
    rdfs:subClassOf nits:DataArtifact .

netex:restrictedToChannel
    rdfs:subClassOf nits:DataArtifact .

netex:restrictionType
    rdfs:subClassOf nits:DataArtifact .

netex:retailConsortiums
    rdfs:subClassOf nits:DataArtifact .

netex:retailDevices
    rdfs:subClassOf nits:DataArtifact .

netex:returnFareTwiceSingle
    rdfs:subClassOf nits:DataArtifact .

netex:returnRouteIdentical
    rdfs:subClassOf nits:DataArtifact .

netex:returnTripsOnly
    rdfs:subClassOf nits:DataArtifact .

netex:reverse
    rdfs:subClassOf nits:DataArtifact .

netex:reverseMembers
    rdfs:subClassOf nits:DataArtifact .

netex:reversedOrientation
    rdfs:subClassOf nits:DataArtifact .

netex:reversible
    rdfs:subClassOf nits:DataArtifact .

netex:reversingDirection
    rdfs:subClassOf nits:DataArtifact .

netex:reviews
    rdfs:subClassOf nits:DataArtifact .

netex:revolvingDoor
    rdfs:subClassOf nits:DataArtifact .

netex:rightSideBorder
    rdfs:subClassOf nits:DataArtifact .

netex:roadAddress
    rdfs:subClassOf nits:DataArtifact .

netex:roadName
    rdfs:subClassOf nits:DataArtifact .

netex:roadNumber
    rdfs:subClassOf nits:DataArtifact .

netex:roles
    rdfs:subClassOf nits:DataArtifact .

netex:rollingStockInventories
    rdfs:subClassOf nits:DataArtifact .

netex:rollingStockItems
    rdfs:subClassOf nits:DataArtifact .

netex:rollingStockType
    rdfs:subClassOf nits:DataArtifact .

netex:roofRack
    rdfs:subClassOf nits:DataArtifact .

netex:roundIfGreaterThan
    rdfs:subClassOf nits:DataArtifact .

netex:roundTo
    rdfs:subClassOf nits:DataArtifact .

netex:roundingMethod
    rdfs:subClassOf nits:DataArtifact .

netex:roundingModulus
    rdfs:subClassOf nits:DataArtifact .

netex:roundingSteps
    rdfs:subClassOf nits:DataArtifact .

netex:roundings
    rdfs:subClassOf nits:DataArtifact .

netex:routeInstructions
    rdfs:subClassOf nits:DataArtifact .

netex:routes
    rdfs:subClassOf nits:DataArtifact .

netex:routingType
    rdfs:subClassOf nits:DataArtifact .

netex:rows
    rdfs:subClassOf nits:DataArtifact .

netex:ruleApplicability
    rdfs:subClassOf nits:DataArtifact .

netex:ruleStepResults
    rdfs:subClassOf nits:DataArtifact .

netex:runTime
    rdfs:subClassOf nits:DataArtifact .

netex:runTimes
    rdfs:subClassOf nits:DataArtifact .

netex:safeForGuideDog
    rdfs:subClassOf nits:DataArtifact .

netex:safetyEdge
    rdfs:subClassOf nits:DataArtifact .

netex:salesOfferPackageElements
    rdfs:subClassOf nits:DataArtifact .

netex:salesOfferPackageSubstitutions
    rdfs:subClassOf nits:DataArtifact .

netex:salesOfferPackages
    rdfs:subClassOf nits:DataArtifact .

netex:salesTransactions
    rdfs:subClassOf nits:DataArtifact .

netex:sameStationRentryPolicy
    rdfs:subClassOf nits:DataArtifact .

netex:sanitary
    rdfs:subClassOf nits:DataArtifact .

netex:satNav
    rdfs:subClassOf nits:DataArtifact .

netex:satisfiesFacilityRequirements
    rdfs:subClassOf nits:DataArtifact .

netex:scheduledHeadwayInterval
    rdfs:subClassOf nits:DataArtifact .

netex:schematicMaps
    rdfs:subClassOf nits:DataArtifact .

netex:scopeOfTicketsAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:scopingMethod
    rdfs:subClassOf nits:DataArtifact .

netex:season
    rdfs:subClassOf nits:DataArtifact .

netex:seasons
    rdfs:subClassOf nits:DataArtifact .

netex:seatAllocationMethod
    rdfs:subClassOf nits:DataArtifact .

netex:seatBackHeight
    rdfs:subClassOf nits:DataArtifact .

netex:seatDepth
    rdfs:subClassOf nits:DataArtifact .

netex:seatHeight
    rdfs:subClassOf nits:DataArtifact .

netex:seatingCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:seats
    rdfs:subClassOf nits:DataArtifact .

netex:secondClassDistance
    rdfs:subClassOf nits:DataArtifact .

netex:secondClassReturn
    rdfs:subClassOf nits:DataArtifact .

netex:secondClassSingle
    rdfs:subClassOf nits:DataArtifact .

netex:sectionType
    rdfs:subClassOf nits:DataArtifact .

netex:sections
    rdfs:subClassOf nits:DataArtifact .

netex:sectionsInSequence
    rdfs:subClassOf nits:DataArtifact .

netex:secure
    rdfs:subClassOf nits:DataArtifact .

netex:secureParking
    rdfs:subClassOf nits:DataArtifact .

netex:selfDriveSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:selfPropelled
    rdfs:subClassOf nits:DataArtifact .

netex:selfServiceLockers
    rdfs:subClassOf nits:DataArtifact .

netex:sensorsInSpot
    rdfs:subClassOf nits:DataArtifact .

netex:sequenceFromFront
    rdfs:subClassOf nits:DataArtifact .

netex:seriesConstraints
    rdfs:subClassOf nits:DataArtifact .

netex:seriesType
    rdfs:subClassOf nits:DataArtifact .

netex:servedPlaces
    rdfs:subClassOf nits:DataArtifact .

netex:servedScheduledStopPoints
    rdfs:subClassOf nits:DataArtifact .

netex:serviceAlteration
    rdfs:subClassOf nits:DataArtifact .

netex:serviceAlterationType
    rdfs:subClassOf nits:DataArtifact .

netex:serviceBookingArrangements
    rdfs:subClassOf nits:DataArtifact .

netex:serviceDesignator
    rdfs:subClassOf nits:DataArtifact .

netex:serviceFacilitySets
    rdfs:subClassOf nits:DataArtifact .

netex:services
    rdfs:subClassOf nits:DataArtifact .

netex:sharedUsage
    rdfs:subClassOf nits:DataArtifact .

netex:sharingPolicyUrl
    rdfs:subClassOf nits:DataArtifact .

netex:sharpsDisposal
    rdfs:subClassOf nits:DataArtifact .

netex:shortCode
    rdfs:subClassOf nits:DataArtifact .

netex:shortName
    rdfs:subClassOf nits:DataArtifact .

netex:shortStopCode
    rdfs:subClassOf nits:DataArtifact .

netex:shortTrip
    rdfs:subClassOf nits:DataArtifact .

netex:showAsAccessible
    rdfs:subClassOf nits:DataArtifact .

netex:showerFacility
    rdfs:subClassOf nits:DataArtifact .

netex:sideText
    rdfs:subClassOf nits:DataArtifact .

netex:signContentType
    rdfs:subClassOf nits:DataArtifact .

netex:signGraphic
    rdfs:subClassOf nits:DataArtifact .

netex:signageToLift
    rdfs:subClassOf nits:DataArtifact .

netex:siteFacilitySet
    rdfs:subClassOf nits:DataArtifact .

netex:siteFacilitySets
    rdfs:subClassOf nits:DataArtifact .

netex:skiRack
    rdfs:subClassOf nits:DataArtifact .

netex:smoker
    rdfs:subClassOf nits:DataArtifact .

netex:smokingAllowed
    rdfs:subClassOf nits:DataArtifact .

netex:snowAndIceSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:sosPanel
    rdfs:subClassOf nits:DataArtifact .

netex:spaces
    rdfs:subClassOf nits:DataArtifact .

netex:specialPlaceCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:specificParameterAssignments
    rdfs:subClassOf nits:DataArtifact .

netex:speed
    rdfs:subClassOf nits:DataArtifact .

netex:spiralStair
    rdfs:subClassOf nits:DataArtifact .

netex:spotAffinities
    rdfs:subClassOf nits:DataArtifact .

netex:spotAffinityType
    rdfs:subClassOf nits:DataArtifact .

netex:spotAllocations
    rdfs:subClassOf nits:DataArtifact .

netex:spotAvailabilityStatus
    rdfs:subClassOf nits:DataArtifact .

netex:spotColumns
    rdfs:subClassOf nits:DataArtifact .

netex:spotRows
    rdfs:subClassOf nits:DataArtifact .

netex:staffing
    rdfs:subClassOf nits:DataArtifact .

netex:stairFreeAccess
    rdfs:subClassOf nits:DataArtifact .

netex:stairRamp
    rdfs:subClassOf nits:DataArtifact .

netex:stakeholderRoleType
    rdfs:subClassOf nits:DataArtifact .

netex:standardTransferTime
    rdfs:subClassOf nits:DataArtifact .

netex:standardWaitTime
    rdfs:subClassOf nits:DataArtifact .

netex:standingAllowed
    rdfs:subClassOf nits:DataArtifact .

netex:standingCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:startDate
    rdfs:subClassOf nits:DataArtifact .

netex:startEvent
    rdfs:subClassOf nits:DataArtifact .

netex:startGeographicalValue
    rdfs:subClassOf nits:DataArtifact .

netex:startOfValidity
    rdfs:subClassOf nits:DataArtifact .

netex:startTime
    rdfs:subClassOf nits:DataArtifact .

netex:startTimeDayOffset
    rdfs:subClassOf nits:DataArtifact .

netex:startTimeInBlock
    rdfs:subClassOf nits:DataArtifact .

netex:startTimesAtStopPoints
    rdfs:subClassOf nits:DataArtifact .

netex:startValue
    rdfs:subClassOf nits:DataArtifact .

netex:status
    rdfs:subClassOf nits:DataArtifact .

netex:staySeated
    rdfs:subClassOf nits:DataArtifact .

netex:stepColourContrast
    rdfs:subClassOf nits:DataArtifact .

netex:stepCondition
    rdfs:subClassOf nits:DataArtifact .

netex:stepFree
    rdfs:subClassOf nits:DataArtifact .

netex:stepFreeAccess
    rdfs:subClassOf nits:DataArtifact .

netex:stepHeight
    rdfs:subClassOf nits:DataArtifact .

netex:stepLength
    rdfs:subClassOf nits:DataArtifact .

netex:stopPlaceType
    rdfs:subClassOf nits:DataArtifact .

netex:stopPlaceWeight
    rdfs:subClassOf nits:DataArtifact .

netex:stopPlaces
    rdfs:subClassOf nits:DataArtifact .

netex:stopRequestButton
    rdfs:subClassOf nits:DataArtifact .

netex:stopRequestTimeout
    rdfs:subClassOf nits:DataArtifact .

netex:stopType
    rdfs:subClassOf nits:DataArtifact .

netex:stopUse
    rdfs:subClassOf nits:DataArtifact .

netex:stopUseConstraint
    rdfs:subClassOf nits:DataArtifact .

netex:street
    rdfs:subClassOf nits:DataArtifact .

netex:structureFactors
    rdfs:subClassOf nits:DataArtifact .

netex:submodes
    rdfs:subClassOf nits:DataArtifact .

netex:subscriptionRenewalPolicy
    rdfs:subClassOf nits:DataArtifact .

netex:subscriptionTermType
    rdfs:subClassOf nits:DataArtifact .

netex:suburb
    rdfs:subClassOf nits:DataArtifact .

netex:subzones
    rdfs:subClassOf nits:DataArtifact .

netex:suitabilities
    rdfs:subClassOf nits:DataArtifact .

netex:suitable
    rdfs:subClassOf nits:DataArtifact .

netex:suitableFor
    rdfs:subClassOf nits:DataArtifact .

netex:suitableForCycles
    rdfs:subClassOf nits:DataArtifact .

netex:summaries
    rdfs:subClassOf nits:DataArtifact .

netex:supplementProductType
    rdfs:subClassOf nits:DataArtifact .

netex:supplementTo
    rdfs:subClassOf nits:DataArtifact .

netex:supportBarHeight
    rdfs:subClassOf nits:DataArtifact .

netex:surfaceType
    rdfs:subClassOf nits:DataArtifact .

netex:surname
    rdfs:subClassOf nits:DataArtifact .

netex:suspension
    rdfs:subClassOf nits:DataArtifact .

netex:suspensionPolicy
    rdfs:subClassOf nits:DataArtifact .

netex:tableType
    rdfs:subClassOf nits:DataArtifact .

netex:tactileActuators
    rdfs:subClassOf nits:DataArtifact .

netex:tactileGroundFloorButton
    rdfs:subClassOf nits:DataArtifact .

netex:tactileGuidanceAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:tactileGuidanceStrips
    rdfs:subClassOf nits:DataArtifact .

netex:tactileGuidingStrip
    rdfs:subClassOf nits:DataArtifact .

netex:tactileGuidingStripStatus
    rdfs:subClassOf nits:DataArtifact .

netex:tactileInterfaceAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:tactileValidationFeedback
    rdfs:subClassOf nits:DataArtifact .

netex:tactileWarningStrip
    rdfs:subClassOf nits:DataArtifact .

netex:tactileWarningStripContrast
    rdfs:subClassOf nits:DataArtifact .

netex:tactileWriting
    rdfs:subClassOf nits:DataArtifact .

netex:talkative
    rdfs:subClassOf nits:DataArtifact .

netex:targetEnergy
    rdfs:subClassOf nits:DataArtifact .

netex:tariffBasis
    rdfs:subClassOf nits:DataArtifact .

netex:tariffs
    rdfs:subClassOf nits:DataArtifact .

netex:taxCategory
    rdfs:subClassOf nits:DataArtifact .

netex:taxiRanks
    rdfs:subClassOf nits:DataArtifact .

netex:taxiStands
    rdfs:subClassOf nits:DataArtifact .

netex:taxiSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:telecabinSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:temporary
    rdfs:subClassOf nits:DataArtifact .

netex:text
    rdfs:subClassOf nits:DataArtifact .

netex:thirdPartyProducts
    rdfs:subClassOf nits:DataArtifact .

netex:throughLoader
    rdfs:subClassOf nits:DataArtifact .

netex:ticketCounter
    rdfs:subClassOf nits:DataArtifact .

netex:ticketCounterService
    rdfs:subClassOf nits:DataArtifact .

netex:ticketMachines
    rdfs:subClassOf nits:DataArtifact .

netex:ticketOffice
    rdfs:subClassOf nits:DataArtifact .

netex:ticketTypesAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:ticketValidatorType
    rdfs:subClassOf nits:DataArtifact .

netex:ticketedQueue
    rdfs:subClassOf nits:DataArtifact .

netex:ticketing
    rdfs:subClassOf nits:DataArtifact .

netex:tides
    rdfs:subClassOf nits:DataArtifact .

netex:tiltAngle
    rdfs:subClassOf nits:DataArtifact .

netex:tiltType
    rdfs:subClassOf nits:DataArtifact .

netex:time
    rdfs:subClassOf nits:DataArtifact .

netex:timeDemandTypes
    rdfs:subClassOf nits:DataArtifact .

netex:timeIntervals
    rdfs:subClassOf nits:DataArtifact .

netex:timeStructureFactors
    rdfs:subClassOf nits:DataArtifact .

netex:timeUnits
    rdfs:subClassOf nits:DataArtifact .

netex:timebands
    rdfs:subClassOf nits:DataArtifact .

netex:timingPointStatus
    rdfs:subClassOf nits:DataArtifact .

netex:timings
    rdfs:subClassOf nits:DataArtifact .

netex:title
    rdfs:subClassOf nits:DataArtifact .

netex:toCall
    rdfs:subClassOf nits:DataArtifact .

netex:toDate
    rdfs:subClassOf nits:DataArtifact .

netex:toFareClass
    rdfs:subClassOf nits:DataArtifact .

netex:toMode
    rdfs:subClassOf nits:DataArtifact .

netex:toVisitNumber
    rdfs:subClassOf nits:DataArtifact .

netex:toiletFacility
    rdfs:subClassOf nits:DataArtifact .

netex:toiletsType
    rdfs:subClassOf nits:DataArtifact .

netex:topographicPlaceType
    rdfs:subClassOf nits:DataArtifact .

netex:topographicPlaces
    rdfs:subClassOf nits:DataArtifact .

netex:totalCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:totalChargeEnergy
    rdfs:subClassOf nits:DataArtifact .

netex:totalPower
    rdfs:subClassOf nits:DataArtifact .

netex:totalWeight
    rdfs:subClassOf nits:DataArtifact .

netex:towards
    rdfs:subClassOf nits:DataArtifact .

netex:town
    rdfs:subClassOf nits:DataArtifact .

netex:traces
    rdfs:subClassOf nits:DataArtifact .

netex:tradingName
    rdfs:subClassOf nits:DataArtifact .

netex:trailerHitch
    rdfs:subClassOf nits:DataArtifact .

netex:trainComponentLabelAssignments
    rdfs:subClassOf nits:DataArtifact .

netex:trainElement
    rdfs:subClassOf nits:DataArtifact .

netex:trainElementType
    rdfs:subClassOf nits:DataArtifact .

netex:trainElementTypes
    rdfs:subClassOf nits:DataArtifact .

netex:trainElements
    rdfs:subClassOf nits:DataArtifact .

netex:trainNumbers
    rdfs:subClassOf nits:DataArtifact .

netex:trainRestrictions
    rdfs:subClassOf nits:DataArtifact .

netex:trainSize
    rdfs:subClassOf nits:DataArtifact .

netex:trainSizeType
    rdfs:subClassOf nits:DataArtifact .

netex:tramSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:transferDuration
    rdfs:subClassOf nits:DataArtifact .

netex:transferMode
    rdfs:subClassOf nits:DataArtifact .

netex:transferModes
    rdfs:subClassOf nits:DataArtifact .

netex:transferOnly
    rdfs:subClassOf nits:DataArtifact .

netex:transfers
    rdfs:subClassOf nits:DataArtifact .

netex:transitCarrier
    rdfs:subClassOf nits:DataArtifact .

netex:transition
    rdfs:subClassOf nits:DataArtifact .

netex:transmission
    rdfs:subClassOf nits:DataArtifact .

netex:transportMode
    rdfs:subClassOf nits:DataArtifact .

netex:transportModes
    rdfs:subClassOf nits:DataArtifact .

netex:transportSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:transportTypes
    rdfs:subClassOf nits:DataArtifact .

netex:travelDocuments
    rdfs:subClassOf nits:DataArtifact .

netex:travelSpecifications
    rdfs:subClassOf nits:DataArtifact .

netex:travellingWithPet
    rdfs:subClassOf nits:DataArtifact .

netex:tripTimes
    rdfs:subClassOf nits:DataArtifact .

netex:tripType
    rdfs:subClassOf nits:DataArtifact .

netex:turningSpacePosition
    rdfs:subClassOf nits:DataArtifact .

netex:type
    rdfs:subClassOf nits:DataArtifact .

netex:typeOfCoupling
    rdfs:subClassOf nits:DataArtifact .

netex:typeOfEntity
    rdfs:subClassOf nits:DataArtifact .

netex:typeOfFuel
    rdfs:subClassOf nits:DataArtifact .

netex:typeOfName
    rdfs:subClassOf nits:DataArtifact .

netex:types
    rdfs:subClassOf nits:DataArtifact .

netex:typesOfEntity
    rdfs:subClassOf nits:DataArtifact .

netex:typesOfFareProduct
    rdfs:subClassOf nits:DataArtifact .

netex:typesOfMachineReadabilities
    rdfs:subClassOf nits:DataArtifact .

netex:typesOfPaymentMethod
    rdfs:subClassOf nits:DataArtifact .

netex:typesOfRetailDevice
    rdfs:subClassOf nits:DataArtifact .

netex:typesOfServiceFeature
    rdfs:subClassOf nits:DataArtifact .

netex:typesOfTravelDocument
    rdfs:subClassOf nits:DataArtifact .

netex:typesOfTravelDocuments
    rdfs:subClassOf nits:DataArtifact .

netex:typesOfValue
    rdfs:subClassOf nits:DataArtifact .

netex:uicCode
    rdfs:subClassOf nits:DataArtifact .

netex:uicTrainRate
    rdfs:subClassOf nits:DataArtifact .

netex:units
    rdfs:subClassOf nits:DataArtifact .

netex:unlimitedMileage
    rdfs:subClassOf nits:DataArtifact .

netex:unlocalisedEquipments
    rdfs:subClassOf nits:DataArtifact .

netex:unusedTicketsOnly
    rdfs:subClassOf nits:DataArtifact .

netex:url
    rdfs:subClassOf nits:DataArtifact .

netex:usage
    rdfs:subClassOf nits:DataArtifact .

netex:usbPowerSockets
    rdfs:subClassOf nits:DataArtifact .

netex:useToExclude
    rdfs:subClassOf nits:DataArtifact .

netex:usedIn
    rdfs:subClassOf nits:DataArtifact .

netex:userAcronym
    rdfs:subClassOf nits:DataArtifact .

netex:userTypes
    rdfs:subClassOf nits:DataArtifact .

netex:vATNumber
    rdfs:subClassOf nits:DataArtifact .

netex:validBetween
    rdfs:subClassOf nits:DataArtifact .

netex:validDayBits
    rdfs:subClassOf nits:DataArtifact .

netex:validableElements
    rdfs:subClassOf nits:DataArtifact .

netex:validationGuidance
    rdfs:subClassOf nits:DataArtifact .

netex:validityConditions
    rdfs:subClassOf nits:DataArtifact .

netex:validityParameterAssignmentType
    rdfs:subClassOf nits:DataArtifact .

netex:validityParameterAssignments
    rdfs:subClassOf nits:DataArtifact .

netex:validityParameterGroupingType
    rdfs:subClassOf nits:DataArtifact .

netex:validityParameterSetSelectionType
    rdfs:subClassOf nits:DataArtifact .

netex:value
    rdfs:subClassOf nits:DataArtifact .

netex:valueName
    rdfs:subClassOf nits:DataArtifact .

netex:values
    rdfs:subClassOf nits:DataArtifact .

netex:variantText
    rdfs:subClassOf nits:DataArtifact .

netex:variants
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleCategories
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleCollection
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleEquipmentProfileMembers
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleEquipmentProfiles
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleMeetingLinks
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleMeetingPlaceAssignments
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleMeetingPointAssignments
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleMeetingPoints
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleMode
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleModelProfiles
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleModels
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleModes
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleOrientation
    rdfs:subClassOf nits:DataArtifact .

netex:vehiclePoolingDriverInfos
    rdfs:subClassOf nits:DataArtifact .

netex:vehiclePositionAlignments
    rdfs:subClassOf nits:DataArtifact .

netex:vehiclePreferences
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleRestrictions
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleServiceParts
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleSide
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleStoppingPlaces
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleStoppingPositions
    rdfs:subClassOf nits:DataArtifact .

netex:vehicleTypes
    rdfs:subClassOf nits:DataArtifact .

netex:vehicles
    rdfs:subClassOf nits:DataArtifact .

netex:versionFrames
    rdfs:subClassOf nits:DataArtifact .

netex:versionType
    rdfs:subClassOf nits:DataArtifact .

netex:versions
    rdfs:subClassOf nits:DataArtifact .

netex:viaFlag
    rdfs:subClassOf nits:DataArtifact .

netex:viaType
    rdfs:subClassOf nits:DataArtifact .

netex:vias
    rdfs:subClassOf nits:DataArtifact .

netex:vibratingCrossingAids
    rdfs:subClassOf nits:DataArtifact .

netex:visitNumber
    rdfs:subClassOf nits:DataArtifact .

netex:visualContrast
    rdfs:subClassOf nits:DataArtifact .

netex:visualGuidanceBands
    rdfs:subClassOf nits:DataArtifact .

netex:visualObstacle
    rdfs:subClassOf nits:DataArtifact .

netex:visualSignsAvailable
    rdfs:subClassOf nits:DataArtifact .

netex:visualValidationFeedback
    rdfs:subClassOf nits:DataArtifact .

netex:waitTime
    rdfs:subClassOf nits:DataArtifact .

netex:waitTimes
    rdfs:subClassOf nits:DataArtifact .

netex:waitingTime
    rdfs:subClassOf nits:DataArtifact .

netex:walkTransferDuration
    rdfs:subClassOf nits:DataArtifact .

netex:waterSubmode
    rdfs:subClassOf nits:DataArtifact .

netex:weeksOfMonth
    rdfs:subClassOf nits:DataArtifact .

netex:weight
    rdfs:subClassOf nits:DataArtifact .

netex:weighting
    rdfs:subClassOf nits:DataArtifact .

netex:wheelchairAccepted
    rdfs:subClassOf nits:DataArtifact .

netex:wheelchairAccess
    rdfs:subClassOf nits:DataArtifact .

netex:wheelchairBookingRequired
    rdfs:subClassOf nits:DataArtifact .

netex:wheelchairLuggageTrolleys
    rdfs:subClassOf nits:DataArtifact .

netex:wheelchairPassable
    rdfs:subClassOf nits:DataArtifact .

netex:wheelchairPassengers
    rdfs:subClassOf nits:DataArtifact .

netex:wheelchairPlaceCapacity
    rdfs:subClassOf nits:DataArtifact .

netex:wheelchairSuitable
    rdfs:subClassOf nits:DataArtifact .

netex:wheelchairTurningCircle
    rdfs:subClassOf nits:DataArtifact .

netex:wheelchairUnaided
    rdfs:subClassOf nits:DataArtifact .

netex:whitelistRefs
    rdfs:subClassOf nits:DataArtifact .

netex:whitelists
    rdfs:subClassOf nits:DataArtifact .

netex:width
    rdfs:subClassOf nits:DataArtifact .

netex:winterTyres
    rdfs:subClassOf nits:DataArtifact .

netex:withoutRiser
    rdfs:subClassOf nits:DataArtifact .

netex:womenOnly
    rdfs:subClassOf nits:DataArtifact .

netex:x
    rdfs:subClassOf nits:DataArtifact .

netex:xOffset
    rdfs:subClassOf nits:DataArtifact .

netex:xmlns
    rdfs:subClassOf nits:DataArtifact .

netex:xmlnsUrl
    rdfs:subClassOf nits:DataArtifact .

netex:y
    rdfs:subClassOf nits:DataArtifact .

netex:yOffset
    rdfs:subClassOf nits:DataArtifact .

netex:zebraCrossing
    rdfs:subClassOf nits:DataArtifact .

netex:zoneContainingStops
    rdfs:subClassOf nits:DataArtifact .

netex:zoneTopology
    rdfs:subClassOf nits:DataArtifact .

netex:zoneUse
    rdfs:subClassOf nits:DataArtifact .

netex:zones
    rdfs:subClassOf nits:DataArtifact .

netex:zonesInSeries
    rdfs:subClassOf nits:DataArtifact .

# nits:Journey
netex:canBreakJourney
    rdfs:subClassOf nits:Journey .

netex:coupledJourneys
    rdfs:subClassOf nits:Journey .

netex:courseOfJourneysNumber
    rdfs:subClassOf nits:Journey .

netex:coursesOfJourneys
    rdfs:subClassOf nits:Journey .

netex:excludedJourneyPatternRefs
    rdfs:subClassOf nits:Journey .

netex:farePointsInPattern
    rdfs:subClassOf nits:Journey .

netex:fromStopPointInJourneyPattern
    rdfs:subClassOf nits:Journey .

netex:journeyPattern
    rdfs:subClassOf nits:Journey .

netex:numberOfJourneysToShow
    rdfs:subClassOf nits:Journey .

netex:onMainRoute
    rdfs:subClassOf nits:Journey .

netex:pointsInPattern
    rdfs:subClassOf nits:Journey .

netex:registerBreakOfJourney
    rdfs:subClassOf nits:Journey .

netex:replacedJourneys
    rdfs:subClassOf nits:Journey .

netex:serviceJourneyPatternType
    rdfs:subClassOf nits:Journey .

netex:symbolMarkingUsualRoute
    rdfs:subClassOf nits:Journey .

netex:templateVehicleJourneyType
    rdfs:subClassOf nits:Journey .

netex:toStopPointInJourneyPattern
    rdfs:subClassOf nits:Journey .

netex:vehicleJourneySpotAllocations
    rdfs:subClassOf nits:Journey .

netex:vehicleJourneyStopAssignments
    rdfs:subClassOf nits:Journey .

# nits:Organisation
netex:additionalOperators
    rdfs:subClassOf nits:Organisation .

netex:comparisonOperator
    rdfs:subClassOf nits:Organisation .

netex:groupOfOperators
    rdfs:subClassOf nits:Organisation .

netex:groupsOfOperators
    rdfs:subClassOf nits:Organisation .

netex:hasOperatorRestrictions
    rdfs:subClassOf nits:Organisation .

netex:relatedOrganisations
    rdfs:subClassOf nits:Organisation .

netex:servicedOrganisationType
    rdfs:subClassOf nits:Organisation .

netex:typesOfOrganisation
    rdfs:subClassOf nits:Organisation .

# nits:SpatialEntity
netex:administrativeZones
    rdfs:subClassOf nits:SpatialEntity .

netex:allAreasWheelchairAccessible
    rdfs:subClassOf nits:SpatialEntity .

netex:boardingPositionEntrances
    rdfs:subClassOf nits:SpatialEntity .

netex:deckEntranceAssignments
    rdfs:subClassOf nits:SpatialEntity .

netex:deckEntranceCouples
    rdfs:subClassOf nits:SpatialEntity .

netex:deckEntranceType
    rdfs:subClassOf nits:SpatialEntity .

netex:deckEntranceUsages
    rdfs:subClassOf nits:SpatialEntity .

netex:deckEntrances
    rdfs:subClassOf nits:SpatialEntity .

netex:deckNavigationPaths
    rdfs:subClassOf nits:SpatialEntity .

netex:deckPathJunction
    rdfs:subClassOf nits:SpatialEntity .

netex:deckPathJunctions
    rdfs:subClassOf nits:SpatialEntity .

netex:deckPathLinks
    rdfs:subClassOf nits:SpatialEntity .

netex:fareZones
    rdfs:subClassOf nits:SpatialEntity .

netex:groupsOfTariffZones
    rdfs:subClassOf nits:SpatialEntity .

netex:hasZoneRestrictions
    rdfs:subClassOf nits:SpatialEntity .

netex:heightOfAccessArea
    rdfs:subClassOf nits:SpatialEntity .

netex:infoLink
    rdfs:subClassOf nits:SpatialEntity .

netex:isWaitPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:legSpace
    rdfs:subClassOf nits:SpatialEntity .

netex:lengthOfAccessArea
    rdfs:subClassOf nits:SpatialEntity .

netex:linksOnSection
    rdfs:subClassOf nits:SpatialEntity .

netex:mobilityServiceConstraintZones
    rdfs:subClassOf nits:SpatialEntity .

netex:navigationPaths
    rdfs:subClassOf nits:SpatialEntity .

netex:numberOfWheelchairAreas
    rdfs:subClassOf nits:SpatialEntity .

netex:parkingAreas
    rdfs:subClassOf nits:SpatialEntity .

netex:pointStandingForAZone
    rdfs:subClassOf nits:SpatialEntity .

netex:pointsOnSection
    rdfs:subClassOf nits:SpatialEntity .

netex:reversePointsOnSection
    rdfs:subClassOf nits:SpatialEntity .

netex:scheduledStopPoint
    rdfs:subClassOf nits:SpatialEntity .

netex:sensorsInEntrance
    rdfs:subClassOf nits:SpatialEntity .

netex:stopAreas
    rdfs:subClassOf nits:SpatialEntity .

netex:stopPlace
    rdfs:subClassOf nits:SpatialEntity .

netex:summerTimeZone
    rdfs:subClassOf nits:SpatialEntity .

netex:summerTimeZoneOffset
    rdfs:subClassOf nits:SpatialEntity .

netex:timeZone
    rdfs:subClassOf nits:SpatialEntity .

netex:timeZoneOffset
    rdfs:subClassOf nits:SpatialEntity .

netex:turningSpace
    rdfs:subClassOf nits:SpatialEntity .

netex:unscheduledPath
    rdfs:subClassOf nits:SpatialEntity .

netex:vehicleEntrances
    rdfs:subClassOf nits:SpatialEntity .

netex:wheelchairAreaLength
    rdfs:subClassOf nits:SpatialEntity .

netex:wheelchairAreaWidth
    rdfs:subClassOf nits:SpatialEntity .

netex:widthOfAccessArea
    rdfs:subClassOf nits:SpatialEntity .

# nits:TemporalEntity
netex:cappingPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:expireAfterPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:maximumBookingPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:maximumRentalPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:maximumSharingPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:maximumSubscriptionPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:maximumSuspensionPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:minimumBookingPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:minimumQualificationPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:minimumRentalPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:minimumSharingPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:minimumSubscriptionPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:minimumSuspensionPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:notificationPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:paymentGracePeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:qualificationPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:reservationExpiryPeriod
    rdfs:subClassOf nits:TemporalEntity .

netex:serviceCalendar
    rdfs:subClassOf nits:TemporalEntity .

netex:uicOperatingPeriod
    rdfs:subClassOf nits:TemporalEntity .

```

---

## Next steps

1. Review the proposed TTL block above
2. Copy approved lines into `nits-netex-align.ttl`
3. Bump `owl:versionInfo` in the alignment file
4. Run `make graphdb-load`
5. Re-run this command to confirm gap is closed
