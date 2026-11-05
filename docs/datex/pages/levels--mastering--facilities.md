url: https://docs.datex2.eu/v3.7/levels/mastering/facilities/
title: Facilities

## Facilities
### The Facility concept
The facility structure is defined as "An abstract class structure to provide information about a facility, which is defined by a specialisation class. A facility may be any kind of site, building, structure, including also service- or supplemental facilities and equipment."
As can be seen in the following figure, a number of classes take use of the Generalisation "Facility", and more can be added (don't mind about the Parking classes, they will most probably change in future).
The separation into a Facility and a FacilityObject (both abstract) is of technical reasons to avoid recursions in the context of a supplemental facility (formerly known as EquipmentOrServiceFacility). For an implementer, this is no disadvantage. The class Facility itself indeed has got no further attributes.
Hint: The blue shaded classes represent a larger sub model in behind. Note that often no attributes are visualised in this case, even if they are mandatory.
Note that there currently is no "Facility publication" as such; whenever you want to publish facility-related content, you have to use the foreseen individual publications like for example a EnergyInfrastructureTablePublication.
A Facility (or more precise the FacilityObject) has got a number of useful properties, all defined in the Facilities namespace – see next figure. Every specialisation of Facility inherits them all:
- Basic information: A name, alias, external identifier, timestamp of last update, a description, information on accessibility and some additional information
- URLs of information websites and photos
- Photos (in binary format)
- Operating hours (including closure information), see chapters below
- Location reference (all available DATEX location methods as specified in EN 16157-2)
- Owner and operator information, using the Organisation structure, see chapters below
- Associated facility: A reference to another facility or a short indication of it
- Rates: Tariffs and payment information, see chapters below
- Applicable vehicles, as specified by the DATEX VehicleCharacteristics model
- Dimension, i.e. basic information on height, width, length or usable area
- Supplemental facility: Some associated service facility or equipment, being itself characterised as a facility, see chapters below
### FacilityStatus
There is a quite similar structure for the FacilityStatus, thus for dynamic status publications:
- Basic status information: The reference to the static facility object, timestamp of last update, the opening status, a status description
- Operating hours (will replace formerly defined operating hours)
- Rates (will replace formerly defined rates)
- A fault
- Supplemental facility status. As this is a facility itself, each supplemental facility can be addressed and referenced by the versioned-identifiable mechanism of the FacilityObject.
Note
The Facility concept allows quite straight forward implementing, because all facility elements have the same basic features (including a location).
Note
Technical note: For the DATEX Tool, when creating a profile in the 'tree', it requires you to make intensive use of the right mouse to open new sub-windows to display the members or aggregations, because the Facility elements are not directly displayed in the flat tree. Nevertheless, all elements can be accessed by the Tool with this procedure.
### The Facilities sub models
For the three sub-models Organisation, Rates and Operating Hours, the following construct-template applies, which is demonstrated here for 'Organisation':
There are two possibilities to use this construct:
On the one hand, there is a publication (in yellow), by which you can define several tables that hold the information of the specification class (in blue). On the other hand, you can plug-in the main class (Organisation in this case, yellow) into your model directly and define and use the specification. By specific specialisations, it is also possible to set the element as unknown or undefined or use a reference, for example on those specification elements (versioned identifiable), that have been published with the publication mechanism before.
Note
The second connection between Organisation and OrganisationSpecification is quite specific and allows the definition of sub-organisations. Such a connection is not available in the other two models.
Note
For Rates, the corresponding table class is named 'RateMatrix' (a class 'RateTable' also exists, but has got another function in the hierarchy, which is due to the alignment with the APDS model).
### Organisation (and Address extension for Location)
The organisation publication as described above is not shown here, only the second option starting with the Organisation class:
Note: For implementing Address information, an extension to location is available (see next figure). As an organisation unit can be supplied by a location, also an address can be specified for it.
This address concept for a delivery or street address follows the APDS model and is defined from a profile of an existing ISO standard for this purpose, ISO-19160-4.
Postcode, city and country are directly specified by attributes, all other information can be defined line-wise ('AddressLine') with a corresponding enumeration value.
### Operating Hours
The operating hours publication as described above is not shown here, only the second option starting with the OperatingHours class. It is basically based on the Validity structure defined in the Common Namespace.
### Rates
This figure shows the RatesPublication. As mentioned before, there is a class RateMatrix which contains RateTables.
The Rates model as such is visualised in the next figure (click to enlarge).
Note
Beginning with the RateTable class, the model bases on the APDS model. APDS has got a very extensive "Rights"-structure. But for the DATEX model, only the class RightsSpecification with some additions was adopted into the DATEX rates model
The RateEligibility part is continued in the next figure, together with the Qualification and RightsSpecification.
A RateTable represents a set of charges that are applied to a single set of criteria and a single RightSpecification for parking or other operations (e.g. delivery permits, rideshare access, etc) at the Place. Examples of a RateTable are a weekday charge rate scales in a public multi-storey car park. Other related RateTables might be evening rates and weekend rates. The validity start and end define the period of validity of a RateTable. If the validity end is not set, the RateTable is considered to be valid until it is replaced. The rateSupercedeLink attribute may be used to indicate a reference to a previous RateTable that is being temporarily superseded.
A RateMatrix is defined as an aggregation of instances of RateTable. There are no specific constraints to the construction of a RateMatrix – it is simply an aggregation of instances of RateTable the data supplier wishes to provide together. It cannot be assumed that the RateTable in a RateMatrix relate to only one Place or that they provide any particular semantic meaning as an aggregation of RateTable.
To support the transmission of a RateTable that may contain multiple charging elements, a RateTable contains one to many RateLineCollection(s). An example could be a RateTable that contains a flat rate fee for e.g. reservation, plus a tiered time-based rate structure for charging over the time of the session. Each RateLineCollection represents one of those charging elements. A RateLineCollection is constructed of one-to-many RateLine.
The RateLine concept is flexible and supports a range of different characterisations, which include:
Flat rate – where the RateLine is active the applied fee charge is a flat rate, unrelated to the duration or timing of the parking or other type of session; An example is a flat rate reservation fee for a session. Flat rate RateLine are defined by use of defining a value, but no use of the durationStart, durationEnd or incrementingPeriod attributes.
Flat rate tier – where the applied fee charged is charged in full if the parking or other type of session indicates that that specific RateLine is active.
Example: in the second hour of a session the fee is 1€ – for any part of that hour.
For a flat rate within a tier the RateLines are defined the time boundary of the tier by use of the durationStart and durationEnd attributes and the value attribute to define the charge amount. If used, the incrementingPeriod attribute, in this case, shall be the same as the period between the durationStart and durationEnd (i.e. there is one increment). Charging is assumed to occur at the start of each increment.
IncrementingRate – where the applied fee charged is related to the duration of this specific tier that has been activated by the parking or other type of Session. This charge type supports a RateTable that applies for short incrementing periods or time-based small increments of charge.
Example: in the second hour of a Session, charging is done at a rate of 0,05 € every 3 minutes.
For an incrementing rate within a tier, the RateLine defines the time boundary of the tier by use of the durationStart and durationEnd attributes. The incrementingPeriod and the value attribute indicate the charge amount of each increment (e.g. 0,05 € each 3 minutes). Charging is assumed to occur at the start of each increment.
Under most circumstances the start and end of charging periods are fixed and relative to local time (e.g. between 08:00 and 17:00 weekdays). In some instances, the charging period and related tiers may be relevant to a specific event. This is indicated by the use of the relativeTimes set to TRUE in the RateLineCollection and the use of the RelativeTimeRates class. All times are defined relative to the referenceTimeStart.
The applicable currency is defined in the RateLineCollection.
Individual RateLine support indication of whether tax is applicable within the defined RateTable or applied in addition to the defined Rate. The level of tax, if included, can be specified as either a monetary amount or a percentage rate. Taxes may also be applied to a RateLineCollection in a similar manner. It is common practice for taxes to be applied at the RateLine level – for example the application of Value Added Tax (VAT) in Europe which is added to a basic parking fee and declared in the cost of the parking to the end user.
A RateLineCollection indicates whether the child RateLine are a chargeable tariff or represent a surcharge, which may be partially or fully refundable.
Each RateTable is applicable to a singular set of criteria and a single RightSpecification. The specification of the qualifying criteria is specified using Eligibility, see Figure 6.
Eligibility is specified as a collection of individual Qualifications. A Qualification is specified as a test with any of the attributes in the Qualification class set. In addition, Qualifications can be specified for other qualifications like for vehicle characteristics as defined in EN 16157-7.
Eligibility may be related or defined by membership. Typically, the Qualification in this case is defined by the withMembership attribute set to TRUE and the membershipName attribute set to the names of the relevant memberships (e.g. J-Park frequent users club, shoppers, cinema attendees, event ticket holders, military, industry specific vehicle, etc).
Additionally, Eligibility may be defined by the use of another RateTable (memberofOtherRateTable set to FALSE), or if the parker is a member of another specific RateTable (memberofOtherRateTable set to TRUE), and the rateTableMember set to identify the earlier linked RateTable.
### SupplementalFacilities
A SupplementalFacility is basically one type of equipment (e.g. elevator, bike parking, …) or a service facility (e.g. restaurant, shop, …), usually located within or nearby another Facility. As it inherits all FacilityObject properties, all standard description elements like rates, location, operating hours etc. are available.
Each instance of the “SupplementalFacility” class describes exactly one type of available supplemental equipment or one type of service facility (here within further called ‘element’).
The element may be enhanced with additional information (sometimes by inheritance of FacilityObject), for example
its number or its availability,
a description and a comment,
the name or brand of the service provided,
accessibility information (e.g. persons with disabilities or wheelchair accessible),
restriction to particular users,
operating hours, see chapters above
a fee (class “Rates”, see chapters above)
its location (all available DATEX location methods as specified in EN 16157-2)
or applicable vehicles, defined by their characteristics (class “VehicleCharacteristics)
The number of the element – with respect to the restrictions mentioned above - may be defined for each element by the attribute “quantity”.
Example: 5 toilets, 1 restaurant, 2 toilets for persons with disabilities, 2 toilets for men; note that for each example one instance of the class “SupplementalFacility” is necessary.
Operating hours for the element may be specified (i.e. a regular time schedule, at which the element should be available or open). Examples would be the operating hours of toilets or restaurants. Please note that different operating hours (e.g. for more than one restaurant) require multiple instances of the “SupplementalFacility” class.
The current availability of the element may be specified in a dynamic model by using the class “SupplementalFacilityStatus”.
Note
For supplemental service facilities, it is possible to define the amount of sub items within the specialisation class. Thus, for example, it is possible to define that there are 5 restaurants with 300 restaurant places in total or 1 medical facility with 2 surgeries. See the table below for details.
For a reference-link between instances of "SupplementalFacility" and "SupplementalFacilityStatus" the versioned identifiable mechanism and the attribute "reference" of class FacilityObjectStatus shall be used.
The following table shows the semantics of the "quantity" and "numberfOfSubItems" attributes for each service facility type:
Go back to the previous page
