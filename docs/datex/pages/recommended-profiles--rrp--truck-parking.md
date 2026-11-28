url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/truck-parking/
title: Safe and Secure Truck Parking

## Safe and Secure Truck Parking
### Overview
This DATEX II Reference Profile for Safe and Secure Truck Parking (further called "RRP 885/2013" or just "profile") described here is based on CEN/TS 16157-6:2022 (thus following the DATEX II data model rules defined in EN 16157-1). It specifies a minimum profile for infrastructure and occupancy information for parking sites designed for and/or used (also) by lorries being in compliance with COMMISSION DELEGATED REGULATION (EU) No 885/2013 of 15 May 2013 supplementing ITS Directive 2010/40/EU (see chapter 2). Further classes, elements and attributes may be added by using the DATEX web tool to describe more aspects of truck parking.
#### Naming convention:
DATEX II is based upon British English, so the term “lorry” is used instead of “truck” within written text. Nevertheless, as the term “Truck Parking” is quite common, it is still used for the model itself. This implies the meaning and needs of “Intelligent Truck Parking” (ITP), although this term is not used here any further.
### Used classes
The RRP 885/2013 uses the following specific classes of the Parking Publications model defined in Clause 7.2 (“static part of the RRP” with ParkingTablePublication) and Clause 7.3 (“dynamic part of the RRP” with ParkingStatusPublication) of CEN/TS 16157-6:2022. It also uses classes of EN 16157-2 (Common data elements), EN 16157-7 (Location Referencing) and CEN/TS 16157-12 (Facility related publications), which are not described here in all aspects.
- Payload Publication*, HeaderInformation, InternationalIdentifier
- ParkingTablePublication, ParkingTable
- HierarchyElementGeneral, Place*, IdentifiedArea. SpecificArea
- CommonComponents, Characteristics, AdditionalCharacteristics
- OperatingPattern, UsageScenario*
- SafetyStandardClassification, CertifiedSecureParking
- Access, VehicularAccess*, AccessJunction, JunctionInformation*, AccessRoad, RoadInformation
- Assignment*, Eligibility, Qualification*, VehicleCharacteristics
- Organisation, UndefinedOrganisation, UnknownOrganisation, OrganisationByReference
- OrganisationSpecification, OrganisationUnit, ContactInformation, ContactPerson
- Rates, UnknownRates, UnspecifiedRates, FreeOfCharge, GeneralRateInformation, RatesByReference
- RateTable*, RateLineCollection, RateLine, RelativeTimes
- Facility, FacilityObject, SupplementalFacility, SupplementalEquipment, SupplementalServiceFacility
- LocationReference, Location, NetworkLocation, PointLocation, PointByCoordinates, PointPointCoordinates
FacilityLocation, Address, AddressLine
ParkingStatusPublication, ParkingStatusInformation*
- FacilityStatus, FacilityObjectStatus
- PlaceStatus*, AccessStatus
- Occupancy*
In classes marked with a star * , some attributes have been omitted in the RRP.
In classes marked with a double star * , all attributes have been omitted in the RRP.*
### Modified Enumerations
For the RRP 885/2013, the following Enumerations have been limited to a smaller set of literals. Nevertheless, these omitted literals might be useful for a specific profile, thus they can be added again, if necessary. - ParkingUsageScenarioEnum – restricted to truck parking - StructureTypeEnum – restricted to offstreet-surface - VehicleTypeEnum – restricted to a basic set of vehicles - LoadTypeEnum – restricted to refrigerated goods - ParkingPlaceStatusEnum – removed elements for overcrowding
### Rules to check
For the RRP 885/2013, a number of rules shall apply that are not implemented in the schema (due to technical restrictions). Thus the following rules shall be checked carefully in resulting XML files manually:
#### ParkingTablePublication
a) At least one "Place" instance shall be present with "CommonComponents" – ("OperatorPattern") - "UsageScenario" – "type" set to "truckParking".
This place element can be topmost in the hierarchy with layer = 0, but can also be integrated in another level of further hierarchy elements. "ParentId" and "childId" are used to define the hierarchy).
For this identified truck-parking element from a), the following rules shall apply:
b) The "name" has to be provided.
c) The role “operator” with "OrganisationSpecification" and "OrganisationUnit" has to be provided, with at least the following information for the corresponding "ContactPerson": “name”, "firstName", “telephoneNumber”, “eMail” [all String] and “publishingAgreement” (class "OrganisationSpecification") [Boolean]. It is allowed to use the construct “OrganisationByReference” instead, in case the information above is given for the referenced contact.
d) A "LocationReference" has to be provided, with using the "FacilityLocation" to specify the address using the "Address" and "AddressLine" classes.
e) One or more "Access" instances shall be present being hierarchly connected to the identified truck-parking element from b) by using the "parentId" and "childId" elements. This can be a VehicularAccess as mentioned in f). Its "LocationReference" must be specified by its ETRS89 point coordinates (class “PointCoordinates”, attributes “latitude” and “longitude” [Float]).
f) One or more "VehicularAccess" instances shall be present being hierarchly connected to the identified truck-parking element from b) by using the "parentId" and "childId" elements.
For every access at least one "primaryRoad" shall be defined with the following parameters (class “AccessRoad” – "Road Information"):
- “roadName” [0..1], [String]
- “roadNumber” [0..1], [String]
- “roadDestination” [0..1], [String] (= direction)
- “distance” [0..1], [Metres] (class “AccessRoad”)
"VehicularAccess" – "correspondingJunction" may be used with attribute "distance" and "JunctionInformation" with a “junctionName” [MultilingualString] and a "junctionNumber", if applicable.
g) Specifying places for lorries:
Either the truck parking element from b) can be used directly, or a "SpecificArea" instance shall be present being hierarchly connected to it.
At least one of those elements shall reflect lorry spaces by using ("CommonComponents" –) “AdditionalCharacteristics" – "Assignment" – “exclusivelyAssignedFor” / "applicableFor" – "Qualification" – "VehicleCharacteristics" – "vehicleType" = “lorry”. Specify the number of spaces by using "CommonComponents" – "Characteristics" – "spacesTotal".
This element can be used to specify the vacant spaces for lorries in the dynamic part of the model.
h) Specifying places for refrigerated good transports:
Either the truck parking element from b) can be used directly, or a "SpecificArea" instance shall be present being hierarchly connected to it. At least one of those elements shall reflect places for refrigerated good transports by using ("CommonComponents" –) “AdditionalCharacteristics" – "Assignment" – "onlyAssignedParking” - “exclusivelyAssignedFor” / "applicableFor" – "Qualification" – "VehicleCharacteristics" – "loadType" = “refrigeratedGoods”. Specify the number of spaces by using "CommonComponents" – "Characteristics" – "spacesTotal".
This element can also be used to specify the vacant spaces for refrigerated good transports in the dynamic part of the model.
i) At least one "RateTable" must be specified. Within a "RateTable", several instances of “RateLineCollections” with multiple instances of “RateLines” can be defined for a parking area (Place). Each rate line collection may be restricted to simple periods, but each rate table may be restricted to complex periods, also to special days, for example to Saturdays and Sundays (via "RateEligibility" – "RightSpecification"). The rate line collection may specify the "applicableCurrency” [enumeration according to ISO 4217 [6] for the currency in which the parking charge is specified (e.g. EUR, GBP, SEK, CZK)]. The rate itself can be specified with attribute “value” [AmountOfMoney] in class "RateLine".
It is allowed to use the class “FreeOfCharge” (as a specialisation of "Rate") instead, meaning that there is no price to pay for parking.
j) The following attributes of class “SafetyStandardClassification” shall be used, if applicable:
- “securityFeature” [Enumeration, values see figure below]
- "additionalSecurity" [Multilingual String]
- "safety" [Enumeration, values see figure below]
- "additionalSafety" [Multilingual String]
- "securityLevel" according to the European secure parking organisation
- "supervision" [Enumeration, values see figure below]
- "securityNationalClassification" [Multilingual String] Furthermore, certifications ("CertifiedSecureParking") can be specified with type and date.
Figure 1 — Enumerations for safety standard classificiation
Furthermore, other equipment or service facilities may be defined with the class “SupplementalFacility".
k) The class “SupplementalFacility” provides up to 60 different types of equipment or service facilities, which may be described with their number, location, opening times or tariffs or vehicle restrictions, if applicable. Examples are electric charging stations, ice-free-scaffolds, toilets, restaurants or truck wash services. Using the literal “other” and element "description" [MultilingualString], custom elements may be provided in case the enumeration values do not fit. Every element may be specified for the parking area itself (Place) or belonging to a dedicated group of parking spaces (SpecificArea).
For every type of equipment or service facility, “SupplementalFacility” has to be instantiated either as "SupplementalEquipment" or "SupplementalServiceFacility". In case there is no equipment or service existent, do not use any instance of “SupplementalFacility” at all.
If the type of equipment or service facility is designed for 'specific goods vehicles', the “applicableForVehicles” role may be used to specify them.
For electric charging, the SupplementalFacility class may be specialised as "ElectricChargingEquipment" (from Namespace EnergyInfrastructure) to specify an electric charging point.
#### ParkingStatusPublication
These rules only apply, if dynamic data is provided.
l) Free spaces for lorries:
The element for lorry spaces defined in g) shall be referenced in class "ParkingStatusInformation" or "PlaceStatus" by "reference". The number of free spaces for lorries shall be specified in "Occupancy" - “numberOfVacantSpaces” [NonNegativeInteger].
m) Status or free spaces:
The possible values for the status of a parking place are shown in Figure 2, available in the dynamic part of the RRP (class “PlaceStatus”).
Note that additional literals for overcrowding are not part of the RRP 885/2013, but can be added to an individual profile manually, if needed.
Figure 2 — Parking place status
For a status that is not included in the enumeration “ParkingPlaceStatusEnum”, “statusDescription” [MultilingualString] (in class “ParkingStatusInformation”) can be used instead. In class "Occupancy", the attribute "numberOfVacantSpaces” [NonNegativeInteger] may be used to specify the number of free spaces.
Note that either the status or the number of free spaces has to be provided.
### Compliance of the RRP 885/2013 with the EU Truck Parking regulation
### Overview
The DATEX II Recommended Reference Profile for 885/2013 (also called RRP further on) is in compliance with the “COMMISSION DELEGATED REGULATION (EU) No 885/2013 of 15 May 2013 supplementing ITS Directive 2010/40/EU of the European Parliament and of the Council with regard to the provision of information services for safe and secure parking places for trucks and commercial vehicles” (here within further called “EU Truck Parking regulation” or “regulation”).
This chapter shows a mapping from the EU Truck Parking regulation to the RRP 885/2013.
#### Annotations to the mapping
A “parking area” in the sense of the EU Truck Parking regulation corresponds to a “Place” object in the RRP.
In the RRP 885/2013, it is not intended to limit the number of characters for attributes (despite for the datatype String, which is limited to 1024 characters).
In the following chapters 2.2 to 2.4, the first column in the tables show the EU Truck Parking regulation with numbered entries. In the second column, the corresponding DATEX II representation of the RRP is denoted, referring to chapter 1.4.
#### Static data related to the parking areas
Static data related to the parking areas, including (where applicable)
1. Identification information of parking area (name and address of the truck parking area (limited to 200 characters)) | b), d)
2. Location information of the entry point in the parking area (latitude/longitude) (20 + 20 characters) | e)
3. Primary road identifier1/direction (20 characters/20 characters), and Primary road identifier2/direction (20 characters/20 characters) if same parking accessible from two different roads | f)
4. If needed, the indication of the Exit to be taken (limited to 100 characters)/Distance from primary road (integer 3) km or miles | f)
5. Total number of free parking places for trucks (integer 3) | g), l)
6. Price and currency of parking places (300 characters) | i)
Information on safety and equipment of the parking area
1. Description of security, safety and service equipment of the parking including national classification if one is applied (500 characters) | j)
2. Number of parking places for refrigerated goods vehicles (numerical 4 digits) | h)
3. Information on specific equipment or services for specific goods vehicles and other (300 characters) | k)
4. Contact information of the parking operator: - Name and surname (up to 100 characters) | c)
- Telephone number (up to 20 characters)
- E-mail address (up to 50 characters)
- Consent of the operator to make his contact information public (Yes/No)
Dynamic data
Dynamic data on availability of parking places including whether a parking is: full, closed or number of free places that are available. | l), m)
### DATEX II representation of the EU Truck Parking regulation in figures
#### ParkingTablePublication
This chapter shows the DATEX II elements described above in form of figures. Note that this RRP 885/2013 represents a minimal set to be compliant to the EU Truck Parking regulation – further elements might be added in individual profiles.
Figure 1 — Parking Table Publication
Figure 2 — Place
Figure 3 — Enumerations for safety standard classification
Figure 4 — IdentifiedArea
Figure 5 — Assignment
Figure 6 — Facility
Figure 7 — SupplementalFacility
Figure 8 — Organisation
Figure 9 — Rates
Figure 10 — LocationReference
Figure 11 — Address
### ParkingStatusPublication
Figure 12 — ParkingStatusPublication
Go back to the previous page
