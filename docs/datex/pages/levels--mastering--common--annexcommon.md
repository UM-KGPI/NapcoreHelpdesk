url: https://docs.datex2.eu/v3.7/levels/mastering/common/annexcommon/
title: Annex A

## Annex A
(normative)
### Data Dictionary
This data dictionary identifies the definitions and characteristics of the different classes, attributes, association ends, data types and enumerations appearing in the common data model defined in 0 and 2. The data dictionary is specified in three parts, one for packages, one for <<D2Datatypes>> and one for <<D2Enumerations>>, each ordered alphabetically.
The first part of the data dictionary is partitioned into sub-Clauses which relate to each of the UML model packages and each sub-Clause defines the contained classes, their attributes and any association ends defined between the classes within that package.
The Data Dictionary tables use the following columns:
- Column Class name: it provides the symbolic name (Upper Camel Case) given to the corresponding class.
- Column Association end: it provides the symbolic name (Lower Camel Case) given to the corresponding association end.
- Column Attribute name: it provides the symbolic name (Lower Camel Case) given to the corresponding attribute of a class.
- Column Enumerated value name: It provides the symbolic name (Lower Camel Case) given to the corresponding enumerated value.
- Column Designation: it provides the corresponding name in natural language of the corresponding class, attribute, association end or enumeration value.
- Column Definition: it provides a comprehensive definition detailing the class, attribute or association end.
- Column Stereotype: it provides a statement of the stereotype that is assigned to the class - see Part 1 of EN 16157 Clause 6.2 for further details.
- Column Abstract: it provides a statement as to whether the class is abstract (non realisable. or concrete (realisable).
- Column Multiplicity: it provides a statement of the allowed multiplicity for the attribute or association end.
- Column Target: It provides the name of the class to which the association end applies.
- Column Type: it provides the name of the class used to define the data type relating to the attribute of the Overview
### A.2 Data Dictionary for "Common"
#### A.2.1 "Classes" package
D2Payload/Common/Classes
A.2.1.1 "Classes" package classes
Table A.1— Classes of the "Classes" package
Class name | Designation | Definition | Stereotype | Abstract
GenericPublication | Generic publication | A publication used to make level B extensions at the publication level. | D2Class | no
GlobalReference | Global reference | A versioned reference to an object that may be in another publication from another publisher. | D2Class | yes
GroupOfVehiclesInvolved | Group of vehicles involved | Group of the vehicles involved having common characteristics and/or status | D2Class | no
HazardousMaterials | Hazardous materials | Details of hazardous materials. | D2Class | no
HeaderInformation | Header information | Management information relating to the data contained within a publication | D2Class | no
InternationalIdentifier | International identifier | An identifier/name whose range is specific to the particular country. | D2Class | no
PayloadPublication | Payload publication | A payload publication of traffic related information or associated management information created at a specific point in time that can be exchanged via a DATEX II interface. | D2ModelRoot | yes
Source | Source | Details of the source from which the information was obtained. | D2Class | no
UrlLink | URL link | Details of a Uniform Resource Locator (URL) address pointing to a resource available on the Internet from where further relevant information may be obtained. | D2Class | no
A.2.1.2 Associations of "Classes" package
Table A.2— Associations of the "Classes" package
Class name | Association end | Designation | Definition | Multiplicity | Target
GlobalReference | externalPublisher | External publisher | Identifier for an external DATEX II publisher | 0..1 | InternationalIdentifier
GroupOfVehiclesInvolved | vehicleCharacteristics | Vehicle characteristics | 0..1 | VehicleCharacteristics
PayloadPublication | publicationCreator | Publication creator | 1..1 | InternationalIdentifier
A.2.1.3 "Classes" package attributes
Table A.3— Attributes of the “Classes” package
Class name | Attribute name | Designation | Definition | Multiplicity | Type
GenericPublication | genericPublicationName | Generic publication name | The name of the generic publication. | 1..1 | String
GlobalReference | externalPublicationIdentifier | External publication identifier | Identifier for an external DATEX II publication | 0..1 | String
GroupOfVehiclesInvolved | numberOfVehicles | Number of vehicles | The number of vehicles of this group that are involved. | 0..1 | NonNegativeInteger
vehicleStatus | Vehicle status | Vehicle status. | 0..1 | VehicleStatusEnum
HazardousMaterials | chemicalName | Chemical name | The chemical name of the hazardous substance carried by the vehicle. | 1..1 | MultilingualString
dangerousGoodsFlashPoint | Dangerous goods flash point | The temperature at which the vapour from a hazardous substance will ignite in air. | 0..1 | TemperatureCelsius
dangerousGoodsRegulations | Dangerous goods regulations | The code defining the regulations, international or national, applicable for a means of transport. | 0..1 | DangerousGoodsRegulationsEnum
hazardCodeIdentification | Hazard code identification | The dangerous goods description code. | 0..1 | String
hazardCodeVersionNumber | Hazard code version number | The version/revision number of date of issuance of the hazardous material code used. | 0..1 | NonNegativeInteger
A number giving additional hazard code classification of a goods item within the applicable dangerous goods regulation.
hazardSubstanceItemPageNumber | Hazard substance item page number | 0..1 | String
tremCardNumber | Trem card number | The identification of a transport emergency card giving advice for emergency actions. | 0..1 | String
undgNumber | UNDG number | A unique serial number assigned within the United Nations to substances and articles contained in a list of the dangerous goods most commonly carried. | 0..1 | String
volumeOfDangerousGoods | Volume of dangerous goods | The volume of dangerous goods on the vehicle(s) reported in a traffic/travel situation. | 0..1 | CubicMetres
weightOfDangerousGoods | Weight of dangerous goods | The weight of dangerous goods on the vehicle(s) reported in a traffic/travel situation. | 0..1 | Tonnes
HeaderInformation | allowedDeliveryChannel | Allowed delivery channel | The allowed delivery channel. | 0..* | InformationDeliveryServicesEnum
confidentiality | Confidentiality | The extent to which the related information may be circulated, according to the recipient type. | 0..1 | ConfidentialityValueEnum
informationStatus | Information status | The status of the related information (real, test, exercise ....). | 1..1 | InformationStatusEnum
InternationalIdentifier | country | Country | EN ISO 3166-1 two-character country code. | 1..1 | CountryCode
nationalIdentifier | National identifier | Identifier or name unique within the specified country. | 1..1 | String
PayloadPublication | defaultLanguage | Default language | The default language used throughout the payload publication. | 1..1 | Language
feedDescription | Feed description | A description of the information which is to be found in the publications originating from the particular feed (URL). | 0..1 | MultilingualString
feedType | Feed type | A classification of the information which is to be found in the publications originating from the particular feed. | 0..1 | String
publicationTime | Publication time | Date/time at which the payload publication was created. | 1..1 | DateTime
Source | reliable | Reliable | An indication as to whether the source deems the associated information to be reliable/correct. "True" indicates it is deemed reliable. | 0..1 | Boolean
sourceCountry | Source country | EN ISO 3166-1 two-character country code of the source of the information. | 0..1 | CountryCode
sourceIdentification | Source identification | Language independent textual code or identifier for the organisation or the equipment that has produced the information. | 0..1 | String
sourceName | Source name | The name of the organisation which has produced the information relating to this version of the information. | 0..1 | MultilingualString
sourceType | Source type | Information about the technology used for measuring the data or the method used for obtaining qualitative descriptions relating to this version of the information. | 0..1 | SourceTypeEnum
UrlLink | urlLinkAddress | URL link address | A Uniform Resource Locator (URL) address pointing to a resource available on the Internet from where further relevant information may be obtained. | 1..1 | Url
urlLinkDescription | URL link description | Description of the relevant information available on the Internet from the URL link. | 0..1 | MultilingualString
urlLinkType | URL link type | Details of the type of relevant information available on the Internet from the URL link. | 0..1 | UrlLinkTypeEnum
#### A.2.2 "DataValue" package
D2Payload/Common/Classes/DataValue
A.2.2.1 "DataValue" package classes
Table A.4— Classes of the "DataValue" package
Class name | Designation | Definition | Stereotype | Abstract
ApplicationRateValue | Application rate value | A measured or calculated value of the application rate of a substance. | D2Class | no
DataValue | Data value | A data value of something that can be measured or calculated. Any provided meta-data values specified in the attributes override any specified generic characteristics such as defined for a specific measurement in the MeasurementSiteTable. | D2Class | yes
DirectionBearingValue | Direction bearing value | A measured or calculated value of direction as a bearing. | D2Class | no
DirectionCompassValue | Direction compass value | A measured or calculated value of direction as a point of the compass. | D2Class | no
FloatingPointMetreDistanceValue | Floating point metre distance value | A measured or calculated value of distance in metres in a floating point format. | D2Class | no
FrictionValue | Friction value | A measured or calculated value of road surface friction. | D2Class | no
IntegerMetreDistanceValue | Integer metre distance value | A measured or calculated value of distance in whole metres. | D2Class | no
KilogramsConcentrationValue | Kilograms concentration value | A measured or calculated value of concentration of a substance in kilograms per unit volume. | D2Class | no
MicrogramsConcentrationValue | Micrograms concentration value | A measured or calculated value of concentration of a substance in micrograms per unit volume. | D2Class | no
PercentageValue | Percentage value | A measured or calculated value expressed as a percentage. | D2Class | no
PrecipitationIntensityValue | Precipitation intensity value | A measured or calculated value of the accumulation rate of precipitation. | D2Class | no
PressureValue | Pressure value | A measured or calculated value of atmospheric pressure. | D2Class | no
SpeedValue | Speed value | A measured or calculated value of speed. | D2Class | no
TemperatureValue | Temperature value | A measured or calculated value of temperature. | D2Class | no
VehicleFlowValue | Vehicle flow value | A measured or calculated value of the flow rate of vehicles. | D2Class | no
WindSpeedValue | Wind speed value | A measured or calculated value of wind speed. | D2Class | no
A.2.2.2 Associations of "DataValue" package
There are no defined associations in the "DataValue" package.
A.2.2.3 "DataValue" package attributes
Table A.5— Attributes of the "DataValue" package
Class name | Attribute name | Designation | Definition | Multiplicity | Type
ApplicationRateValue | applicationRate | Application rate | A value of the rate of application of a substance expressed in kilogrammes per square metre. | 1..1 | IntensityKilogramsPerSquareMetre
DataValue | accuracy | Accuracy | The extent to which the value is expected to be free from error, measured as a ercentage of the data value. 100% means fully accurate. | 0..1 | Percentage
computationalMethod | Computational method | Method of computation which has been used to compute this data value. | 0..1 | ComputationMethodEnum
dataError | Data error | Indication of whether the value is deemed to be erroneous by the supplier (true = erroneous). If not present, the data value is assumed to be ok. This may be used when automatic fault detection information relating to sensors is available. | 0..1 | Boolean
numberOfIncompleteInputs | Number of incomplete inputs | The number of inputs detected but not completed during the sampling or measurement period; e.g. vehicles detected entering but not exiting the detection zone. | 0..1 | NonNegativeInteger
numberOfInputValuesUsed | Number of input values used | The number of input values used in the sampling or measurement period to determine the data value. | 0..1 | NonNegativeInteger
reasonForDataError | Reason for data error | The reason why the value is deemed to be erroneous by the supplier. | 0..1 | MultilingualString
smoothingFactor | Smoothing factor | Coefficient required when a moving average is computed to give specific weights to the former average and the new data. A typical formula is, F being the smoothing factor: New average = (old average) F + (new data) (1 - F). | 0..1 | Float
standardDeviation | Standard deviation | The standard deviation of the sample of input values from which this value was derived, measured in the units of the data value. | 0..1 | Float
supplierCalculatedDataQuality | Supplier calculated data quality | A measure of data quality assigned to the value by the supplier. 100% equates to ideal/perfect quality. The method of calculation is supplier specific and needs to be agreed between supplier and client | 0..1 | Percentage
DirectionBearingValue | directionBearing | Direction bearing | A value of direction expressed in terms of a bearing measured in whole degrees. Unless otherwise specified the reference direction corresponding to 0 degrees is North. | 1..1 | AngleInDegrees
DirectionCompassValue | directionCompass | Direction compass | A value of direction expressed in terms of points of the compass. | 1..1 | DirectionCompassEnum
FloatingPointMetreDistanceValue | distance | Distance | A value of distance expressed in metres in a floating point format. | 1..1 | MetresAsFloat
FrictionValue | friction | Friction | Friction, usually a value between 0 and 1. | 1..1 | Float
IntegerMetreDistanceValue | integerMetreDistance | Integer metre distance | A value of distance expressed in metres in a non-negative integer format. | 1..1 | MetresAsNonNegativeInteger
KilogramsConcentrationValue | kilogramsConcentration | Kilograms concentration | A value defining the amount of a substance in a given volume (concentration) expressed in kilograms per cubic metre. | 1..1 | ConcentrationKiloramsPerCubicMetre
MicrogramsConcentrationValue | microgramsConcentration | Micrograms concentration | A value of the amount of a substance in a given volume (concentration) expressed in µg/m3 (micrograms/cubic metre). | 1..1 | ConcentrationMicrogramsPerCubicMetre
PercentageValue | percentage | Percentage | A value expressed as a percentage. | 1..1 | Percentage
PrecipitationIntensityValue | millimetresPerHourIntensity | Millimetres per hour intensity | A value of precipitation intensity expressed in units of millimetres per hour. | 1..1 | IntensityMillimetresPerHour
PressureValue | pressure | Pressure | Atmospheric pressure. | 1..1 | Hectopascal
SpeedValue | speed | Speed | A value of speed expressed in kilometres per hour. | 1..1 | KilometresPerHour
TemperatureValue | temperature | Temperature | A value of temperature expressed in degrees Celsius. | 1..1 | TemperatureCelsius
VehicleFlowValue | vehicleFlowRate | Vehicle flow rate | A value of vehicle flow rate expressed in vehicles per hour. | 1..1 | VehiclesPerHour
WindSpeedValue | windSpeed | Wind speed | A value of wind speed expressed in metres per second. | 1..1 | MetresPerSecond
#### A.2.3 "Fault" package
D2Payload/Common/Classes/Fault
A.2.3.1 "Fault" package classes
Table A.6— Classes of the "Fault" package
Class name | Designation | Definition | Stereotype | Abstract
Fault | Fault | Information about a fault relating to a specific piece of equipment or process. | D2Class | no
A.2.3.2 Associations of "Fault" package
There are no defined associations in the "Fault" package.
A.2.3.3 "Fault" package attributes
Table A.7— Attributes of the “Fault” package
Class name | Attribute name | Designation | Definition | Multiplicity | Type
Fault | faultCreationTime | Fault creation time | The date and time at which the fault was originally recorded/reported. | 0..1 | DateTime
faultDescription | Fault description | Textual description of the fault. | 0..1 | MultilingualString
faultIdentifier | Fault identifier | Unique identifier of the fault. | 0..1 | String
faultImpactSeverity | Fault impact severity | The severity of the fault in terms of how it affects the usability of the equipment or the reliability of the data generated by the equipment. | 0..1 | FaultSeverityEnum
faultLastUpdateTime | Fault last update time | The date and time at which the fault information as specified in this instance was last updated. | 1..1 | DateTime
faultUrgencyToRectify | Fault urgency to rectify | The urgency to rectify the fault. | 0..1 | FaultUrgencyEnum
manufacturerFaultCode | Manufacturer fault code | A manufacturer specific code for the fault. | 0..1 | String
#### A.2.4 "Validity" package
D2Payload/Common/Classes/Validity
A.2.4.1 "Validity" package classes
Table A.8— Classes of the "Validity" package
Class name | Designation | Definition | Stereotype | Abstract
CalendarWeekWithinMonth | Calendar week within month | Specification of periods defined by relevant calendar weeks in a month, see ISO8601. Note: Calendar weeks start with Monday. First week is the week containing the first of the month. | D2Class | no
DayWeekMonth | Day week month | Specification of periods defined by the intersection of days or instances of them, calendar weeks and months. | D2Class | no
InstanceOfDayWithinMonth | Instance of day within month | Specification of periods defined by the instance of a specific weekday within a month (e.g. 3rd Tuesday in May) | D2Class | no
NamedArea | Named area | An abstract hook class to hook in a model for a named area. | D2Class | yes
OverallPeriod | Overall period | A continuous or discontinuous period of validity defined by overall bounding start and end times and the possible intersection of valid periods (potentially recurring) with the complement of exception periods (also potentially recurring). | D2Class | no
Period | Period | A continuous time period or a set of discontinuous time periods defined by the intersection of a set of criteria all within an overall delimiting interval. | D2Class | no
PublicHoliday | Public holiday | Specification of a specific public holiday in case specialDayType is set to 'publicHoliday'. | D2Class | no
SpecialDay | Special day | Specification of a special type of day, possibly also a public holiday. Can be country or region specific. | D2Class | no
TimePeriodOfDay | Time period of day | Specification of a continuous period of time within a 24 hour period. | D2Class | no
Validity | Validity | Specification of validity, either explicitly or by a validity time period specification which may be discontinuous. | D2Class | no
A.2.4.2 Associations of "Validity" package
Table A.9— Associations of the "Validity" package
Class name | Association end | Designation | Definition | Multiplicity | Target
OverallPeriod | exceptionPeriod | Exception period | A single time period, a recurring time period or a set of different recurring time periods during which validity is false. | 0..* | Period
validPeriod | Valid period | A single time period, a recurring time period or a set of different recurring time periods during which validity is true. | 0..* | Period
Period | recurringSpecialDay | Recurring special day | A recurring period in terms of special days. | 0..* | SpecialDay
recurringDayWeekMonthPeriod | Recurring day week month period | A recurring period defined in terms of days of the week, weeks of the month and months of the year. | 0..* | DayWeekMonth
recurringTimePeriodOfDay | Recurring time period of day | A recurring period of a day. | 0..* | TimePeriodOfDay
SpecialDay | namedArea | Named area | 0..* | NamedArea
Validity | validityTimeSpecification | Validity time specification | A specification of periods of validity defined by overall bounding start and end times and the possible intersection of valid periods with exception periods (exception periods overriding valid periods). | 1..1 | OverallPeriod
A.2.4.3 "Validity" package attributes
Table A.10— Attributes of the "Validity" package
Class name | Attribute name | Designation | Definition | Multiplicity | Type
Calender week in month. See ISO8601. All weeks of the month" is expressed by not using the CalendarWeekOfMonth class.
Note: Calendar weeks start with Monday. First week is the week containing the first of the month.
CalendarWeekWithinMonth | applicableCalenderWeekWithinMonth | Applicable calender week within month | 1..6 | CalendarWeekWithinMonthEnum
DayWeekMonth | applicableDay | Applicable day | Applicable day of the week. "All days of the week" is expressed by non-inclusion of this attribute. | 0..7 | DayEnum
applicableMonth | Applicable month | Applicable month of the year. "All months of the year" is expressed by non-inclusion of this attribute. | 0..12 | MonthOfYearEnum
InstanceOfDayWithinMonth | applicableInstanceOfDayWithinMonth | Applicable instance of day within month | The specified integer instance of the specified applicable day within a month. | 1..5 | InstanceOfDayEnum
OverallPeriod | overallEndTime | Overall end time | End of bounding period of validity defined by date and time. | 0..1 | DateTime
overallStartTime | Overall start time | Start of bounding period of validity defined by date and time. | 1..1 | DateTime
Period | endOfPeriod | End of period | End of a period. | 0..1 | DateTime
periodName | Period name | The name of the period. | 0..1 | MultilingualString
startOfPeriod | Start of period | Start of period. | 0..1 | DateTime
PublicHoliday | publicHolidayName | Public holiday name | Specification of a specific public holiday by its name. | 1..1 | MultilingualString
SpecialDay | intersectWithApplicableDays | Intersect with applicable days | When true, the period is the intersection of applicable days and this special day. When false, the period is the union of applicable days and this special day. | 1..1 | Boolean
publicEvent | Public event | Type of public event on this special day. | 0..1 | PublicEventTypeEnum
specialDayType | Special day type | Specification of a special day, for example schoolDay, publicHoliday, ... | 1..1 | SpecialDayTypeEnum
TimePeriodOfDay | endTimeOfPeriod | End time of period | End of time period. | 1..1 | Time
startTimeOfPeriod | Start time of period | Start of time period. | 1..1 | Time
Validity | overrunning | Overrunning | The activity or action described by the SituationRecord is still in progress, overrunning its planned duration as indicated in a previous version of this record or even in current version. | 0..1 | Boolean
validityStatus | Validitystatus | Specification of validity, either explicitly overriding the validity time specification or confirming it. | 1..1 | ValidityStatusEnum
#### A.2.5 "Vehicle" package
D2Payload/Common/Classes/Vehicle
A.2.5.1 "Vehicle" package classes
Table A.11— Classes of the “Vehicle” package
Class name | Designation | Definition | Stereotype | Abstract
AxleSpacing | Axle spacing | The spacing details between the axle sets of an individual vehicle numbered from the front to the back of the vehicle. | D2Class | no
AxleWeight | Axle weight | The weight details of a specific axle on the vehicle. | D2Class | no
Vehicle | Vehicle | Details of an individual vehicle. | D2Class | no
A.2.5.2 Associations of "Vehicle" package
Table A.12— Associations of the "Vehicle" package
Class name | Association end | Designation | Definition | Multiplicity | Target
Vehicle | vehicleCharacteristics | Vehicle characteristics | 0..1 | VehicleCharacteristics
axleSpacingOnVehicle | Axle spacing on vehicle | The spacing between axles on the vehicles. | 0..* | AxleSpacing
hazardousGoodsAssociatedWithVehicle | Hazardous goods associated with vehicle | Details of hazardous goods carried by the vehicle. | 0..1 | HazardousMaterials
specificAxleWeight | Specific axle weight | The weight details relating to a specific axle on the vehicle. | 0..* | AxleWeight
A.2.5.3 "Vehicle" package attributes
Table A.13— Attributes of the "Vehicle" package
Class name | Attribute name | Designation | Definition | Multiplicity | Type
AxleSpacing | axleSpacing | Axle spacing | The spacing interval, indicated by the axleSpacingSequenceIdentifier, between the axles of an individual vehicle from front to back of the vehicle. | 1..1 | MetresAsFloat
axleSpacingSequenceIdentifier | Axle spacing sequence identifier | Indicates the sequence number of the interval between the axles of the individual vehicle from front to back (e.g. 1, 2, 3...). This cannot exceed (numberOfAxles -1) if the numberOfAxles is also given as part of the VehicleCharacteristics. | 1..1 | NonNegativeInteger
AxleWeight | axlePositionIdentifier | Axle position identifier | Indicates the position of the axle on the vehicle numbered from front to back (i.e. 1, 2, 3...). This cannot exceed the numberOfAxles if provided as part of VehicleCharacteristics. | 1..1 | NonNegativeInteger
axleWeight | Axle weight | The weight of the specific axle, indicated by the axleSequenceIdentifier, on the vehicle numbered from front to back of the vehicle. | 0..1 | Tonnes
maximumPermittedAxleWeight | Maximum permitted axle weight | The maximum permitted weight of this specific axle on the vehicle. | 0..1 | Tonnes
Vehicle | anonymizedVehicleReference | Anonymized vehicle reference | A reference for a vehicle derived from vehicle properties such as registration number but encoded so that it does not allow a human to identify the vehicle directly from the encoded value | 0..1 | String
vehicleColour | Vehicle colour | The colour of the vehicle. | 0..1 | MultilingualString
vehicleCountryOfOrigin | Vehicle country of origin | Specification of the country in which the vehicle is registered. The code is the 2-alpha code as given in EN ISO 3166-1 which is updated by the ISO 3166 Maintenance Agency. | 0..1 | CountryCode
vehicleIdentifier | Vehicle identifier | A vehicle identification number (VIN) comprising 17 characters that is based on either ISO 3779 or ISO 3780 and uniquely identifies the individual vehicle. This is normally securely attached to the vehicle chassis. | 0..1 | String
vehicleManufacturer | Vehicle manufacturer | Indicates the stated manufacturer of the vehicle, e.g. Ford. | 0..1 | String
vehicleModel | Vehicle model | Indicates the model (or range name) of the vehicle, e.g. Mondeo. | 0..1 | String
vehicleRegistrationPlateIdentifier | Vehicle registration plate identifier | An identifier or code displayed on a vehicle registration plate attached to the vehicle used for official identification purposes. The registration identifier is numeric or alphanumeric and is unique within the issuing authority's region. | 0..1 | String
vehicleStatus | Vehicle status | Vehicle status. | 0..1 | VehicleStatusEnum
#### A.2.6 "VehicleCharacteristics" package
D2Payload/Common/Classes/VehicleCharacteristics
A.2.6.1 "VehicleCharacteristics" package classes
Table A.14— Classes of the “VehicleCharacteristics” package
Class name | Designation | Definition | Stereotype | Abstract
Emissions | Emissions | Emission characteristics of vehicles. | D2Class | no
GrossWeightCharacteristic | Gross weight characteristic | Gross weight characteristic of a vehicle. | D2Class | no
HeaviestAxleWeightCharacteristic | Heaviest axle weight characteristic | Weight characteristic of the heaviest axle on the vehicle. | D2Class | no
HeightCharacteristic | Height characteristic | Height characteristic of a vehicle. | D2Class | no
LengthCharacteristic | Length characteristic | Length characteristic of a vehicle. | D2Class | no
NumberOfAxlesCharacteristic | Number of axles characteristic | Number of axles characteristic of a vehicle. | D2Class | no
VehicleCharacteristics | Vehicle characteristics | The characteristics of a vehicle, e.g. lorry of gross weight greater than 30 tonnes. | D2Class | no
WidthCharacteristic | Width characteristic | Width characteristic of a vehicle. | D2Class | no
A.2.6.2 Associations of "VehicleCharacteristics" package
Table A.15— Associations of the "VehicleCharacteristics" package
Class name | Association end | Designation | Definition | Multiplicity | Target
VehicleCharacteristics | emissions | Emissions | 0..1 | Emissions
grossWeightCharacteristic | Gross weight characteristic | 0..2 | GrossWeightCharacteristic
heaviestAxleWeightCharacteristic | Heaviest axle weight characteristic | 0..2 | HeaviestAxleWeightCharacteristic
heightCharacteristic | Height characteristic | 0..2 | HeightCharacteristic
lengthCharacteristic | Length characteristic | 0..2 | LengthCharacteristic
numberOfAxlesCharacteristic | Number of axles characteristic | 0..2 | NumberOfAxlesCharacteristic
widthCharacteristic | Width characteristic | 0..2 | WidthCharacteristic
A.2.6.3 "VehicleCharacteristics" package attributes
Table A.16— Attributes of the "VehicleCharacteristics" package
Class name | Attribute name | Designation | Definition | Multiplicity | Type
The minimum Euro emission classification the vehicle(s) have to comply with according to the 1970 Directive 70/220/EEC and its several amendments.
Note that vehicleType and fuelType need to be provided in order to make this classification explicit.
Emissions | emissionClassificationEuro | Emission classification euro | 0..1 | EmissionClassificationEuroEnum
emissionClassificationOther | Emission classification other | Some other (probably locally defined) value(s) for emission classification. | 0..* | String
emissionLevel | Emission level | The low emission level of a vehicle. | 0..1 | LowEmissionLevelEnum
GrossWeightCharacteristic | comparisonOperator | Comparison operator | The operator to be used in the vehicle characteristic comparison operation. | 1..1 | ComparisonOperatorEnum
grossVehicleWeight | Gross vehicle weight | The gross weight of the vehicle and its load, including any trailers. | 1..1 | Tonnes
typeOfWeight | Type of weight | The meaning of the weight value | 1..1 | WeightTypeEnum
HeaviestAxleWeightCharacteristic | comparisonOperator | Comparison operator | The operator to be used in the vehicle characteristic comparison operation. | 1..1 | ComparisonOperatorEnum
heaviestAxleWeight | Heaviest axle weight | The weight of the heaviest axle on the vehicle. | 1..1 | Tonnes
HeightCharacteristic | comparisonOperator | Comparison operator | The operator to be used in the vehicle characteristic comparison operation. | 1..1 | ComparisonOperatorEnum
vehicleHeight | Vehicle height | The height of the highest part, excluding antennae, of an individual vehicle above the road surface, in metres. | 1..1 | MetresAsFloat
LengthCharacteristic | comparisonOperator | Comparison operator | The operator to be used in the vehicle characteristic comparison operation. | 1..1 | ComparisonOperatorEnum
vehicleLength | Vehicle length | The overall distance between the front and back of an individual vehicle, including the length of any trailers, couplings, embedded features etc. | 1..1 | MetresAsFloat
NumberOfAxlesCharacteristic | comparisonOperator | Comparison operator | The operator to be used in the vehicle characteristic comparison operation. | 1..1 | ComparisonOperatorEnum
numberOfAxles | Number of axles | The total number of axles of an individual vehicle. | 1..1 | NonNegativeInteger
VehicleCharacteristics | fuelType | Fuel type | The type of fuel used by the vehicle. | 0..* | FuelTypeEnum
loadType | Load type | The type of load carried by the vehicle, especially in respect of hazardous loads. | 0..1 | LoadTypeEnum
vehicleEquipment | Vehicle equipment | The type of equipment in use or on board the vehicle. | 0..1 | VehicleEquipmentEnum
vehicleType | Vehicle type | Vehicle type. | 0..* | VehicleTypeEnum
vehicleUsage | Vehicle usage | The type of usage of the vehicle (i.e. for what purpose is the vehicle being used). | 0..1 | VehicleUsageEnum
yearOfFirstRegistration | Year of first registration | Year of first registration of the vehicle | 0..1 | Year
WidthCharacteristic | comparisonOperator | Comparison operator | The operator to be used in the vehicle characteristic comparison operation. | 1..1 | ComparisonOperatorEnum
vehicleWidth | Vehicle width | The maximum width of an individual vehicle, including any features embedded or fixed on it, in metres. | 1..1 | MetresAsFloat
#### A.2.7 "WeatherRelated" package
D2Payload/Common/Classes/WeatherRelated
A.2.7.1 "WeatherRelated" package classes
Table A.17— Classes of the "WeatherRelated" package
Class name | Designation | Definition | Stereotype | Abstract
Humidity | Humidity | Details of atmospheric humidity. | D2Class | no
Pollution | Pollution | Details of atmospheric pollution. | D2Class | no
PrecipitationDetail | Precipitation detail | Details of precipitation (rain, snow etc.). | D2Class | no
Pressure | Pressure | Details of atmospheric pressure. | D2Class | no
RoadSurfaceConditionMeasurements | Road surface condition measurements | Measurements of the road surface condition which relate specifically to the weather. | D2Class | no
Temperature | Temperature | Details of atmospheric temperature. | D2Class | no
TemperatureBelowOrAboveRoadSurface | Temperature below or above road surface | Measurement of temperature below or above the road surface. | D2Class | no
Visibility | Visibility | Details of atmospheric visibility. | D2Class | no
Wind | Wind | Wind conditions on the road. | D2Class | no
A.2.7.2 Associations of "WeatherRelated" package
Table A.18— Associations of the "WeatherRelated" package
Class name | Association end | Designation | Definition | Multiplicity | Target
Humidity | relativeHumidity | Relative humidity | The amount of water vapour in the air, as a percentage of the amount of water vapour in saturated air at the same temperature and at atmospheric pressure. The measurement is taken between 1.5 and 2 m above the ground and behind a meteorological screen. | 1..1 | PercentageValue
Pollution | pollutantConcentration | Pollutant concentration | The average concentration of the pollutant in the air. | 0..1 | MicrogramsConcentrationValue
PrecipitationDetail | depositionDepth | Deposition depth | The equivalent depth of the water layer resulting from precipitation or deposition on a non-porous horizontal surface. Non liquid precipitation is considered as melted in water form. | 0..1 | FloatingPointMetreDistanceValue
precipitationIntensity | Precipitation intensity | The height of the precipitation received per unit time. | 0..1 | PrecipitationIntensityValue
Pressure | pressureValue | Pressure value | 1..1 | PressureValue
RoadSurfaceConditionMeasurements | temperatureBelowOrAboveRoadSurface | Temperature below or above road surface | Temperature measurements below or above the road surface. | 0..* | TemperatureBelowOr AboveRoadSurface
deIcingApplicationRate | De-icing application rate | Indicates the rate at which de-icing agents have been applied to the specified road. | 0..1 | ApplicationRateValue
protectionTemperature | Protection temperature | The road surface temperature down to which the surface is protected from freezing. | 0..1 | TemperatureValue
depthOfSnow | Depth of snow | The depth of snow recorded on the road`surface. | 0..1 | FloatingPointMetreDistanceValue
iceLayerThickness | Ice layer thickness | The depth of ice to be found on the road surface. | 0..1 | FloatingPointMetreDistanceValue
friction | Friction | The friction value of the road. | 0..1 | FrictionValue
deIcingConcentration | De-icing concentration | Indicates the concentration of de-icing agent present in surface water on the specified road. | 0..1 | KilogramsConcentrationValue
icePercentage | Ice percentage | The percentage of ice in the water. | 0..1 | PercentageValue
roadSurfaceTemperature | Road surface temperature | The temperature measured on the road surface. | 0..1 | TemperatureValue
waterFilmThickness | Water film thickness | The depth of standing water to be found on the road surface. | 0..1 | FloatingPointMetreDistanceValue
Temperature | minimumTemperature | Minimum temperature | The minimum temperature during the forecast or measurement period. | 0..1 | TemperatureValue
dewPointTemperature | Dew point temperature | The temperature to which the air would have to cool (at constant pressure and water vapour content) in order to reach saturation. | 0..1 | TemperatureValue
maximumTemperature | Maximum temperature | The maximum temperature during the forecast or measurement period. | 0..1 | TemperatureValue
airTemperature | Air temperature | The air temperature measured in the shade between 1.5 and 2 metres above ground level. | 0..1 | TemperatureValue
TemperatureBelowOrAboveRoadSurface | temperatureBelowOrAboveRoadSurface | Temperature below or above road surface | The temperature measured at the specified height below or above the road surface. | 1..1 | TemperatureValue
Visibility | minimumVisibilityDistance | Minimum visibility distance | The minimum distance, measured or estimated, beyond which drivers may be unable to clearly see a vehicle or an obstacle. | 1..1 | IntegerMetreDistanceValue
Wind | maximumWindDirectionBearing | Maximum wind direction bearing | The direction from which the maximum wind blows, in terms of a bearing measured in degrees (0 - 359). | 0..1 | DirectionBearingValue
windDirectionBearing | Wind direction bearing | The average direction from which the wind blows, in terms of a bearing measured in degrees (0 - 359). | 0..1 | DirectionBearingValue
windDirectionCompass | Wind direction compass | The average direction from which the wind blows, in terms of points of the compass. | 0..1 | DirectionCompassValue
maximumWindDirectionCompass | Maximum wind direction compass | The direction from which the maximum wind blows, in terms of points of the compass. | 0..1 | DirectionCompassValue
windSpeed | Wind speed | The wind speed averaged over at least 10 minutes, measured at a default height of 10 metres (meteorological standard) above the road surface, unless measurement height is specified. | 0..1 | WindSpeedValue
maximumWindSpeed | Maximum wind speed | The maximum wind speed in a measurement period of 10 minutes. | 0..1 | WindSpeedValue
A.2.7.3 "WeatherRelated" package attributes
Table A.19— Attributes of the "WeatherRelated" package
Class name | Attribute name | Designation | Definition | Multiplicity | Type
Pollution | pollutantType | Pollutant type | The type of pollutant in the air. | 1..1 | PollutantTypeEnum
PrecipitationDetail | precipitationIntensityGrade | Precipitation intensity grade | The intensity of precipitation expressed by enumerated value, | 0..1 | PrecipitationIntensityEnum
precipitationType | Precipitation type | The type of precipitation which is affecting the driving conditions. | 0..1 | PrecipitationTypeEnum
TemperatureBelowOrAboveRoadSurface | heightBelowOrAboveRoadSurface | Height below or above road surface | The height of the measurement either below (negative value) or above (positive value) the road surface. | 1..1 | MetresAsFloat
Wind | windMeasurementHeight | Wind measurement height | The height in metres above the road surface at which the wind is measured. | 0..1 | MetresAsNonNegativeInteger
### A.3 Data Dictionary of <<D2Datatype>> for "Common"
This clause contains the definitions of all data types which are used in the "Common".
A.3.1 The <<D2Datatype>> "AngleInDegrees"
An integer number representing an angle in whole degrees between 0 and 359.
A.3.2 The <<D2Datatype>> "AxlesPerHour"
Vehicle axles per hour.
A.3.3 The <<D2Datatype>> "Base64Binary"
Binary data in base 64 encoding, for example for image data.
A.3.4 The <<D2Datatype>> "Boolean"
Boolean has the value space required to support the mathematical concept of binary-valued logic: {true, false}.
A.3.5 The <<D2Datatype>> "ConcentrationKilogramsPerCubicMetre"
Concentration defined in kilograms per cubic metre (equivalent to grams per litre under standard conditions).
A.3.6 The <<D2Datatype>> "ConcentrationMicrogramsPerCubicMetre"
A measure of concentration defined in µg/m3 (micrograms/cubic metre).
A.3.7 The <<D2Datatype>> "CountryCode"
EN ISO 3166-1 alpha-2 two-letter country code
A.3.8 The <<D2Datatype>> "CubicMetres"
A volumetric measure defined in cubic metres.
A.3.9 The <<D2Datatype>> "Date"
A combination of year, month and day integer-valued properties plus an optional timezone property. It represents an interval of exactly one day, beginning on the first moment of the day in the timezone, i.e. '00:00:00' up to but not including '24:00:00'.
A.3.10 The <<D2Datatype>> "DateTime"
A combination of integer-valued year, month, day, hour, minute properties, a decimal-valued second property and a time zone property from which it is possible to determine the local time, the equivalent UTC time and the time zone offset from UTC.
A.3.11 The <<D2Datatype>> "Decimal"
A decimal number whose value space is the set of numbers that can be obtained by multiplying an integer by a non-positive power of ten, i.e., expressible as i × 10\^-n where i and n are integers and n >= 0.
A.3.12 The <<D2Datatype>> "Double"
A double precision number whose value space consists of the values m × 2\^e, where m is an integer whose absolute value is less than 2\^53, and e is an integer between -1024 and 1023, inclusive.
A.3.13 The <<D2Datatype>> "Float"
A floating point number whose value space consists of the values m × 2\^e, where m is an integer whose absolute value is less than 2\^24, and e is an integer between -149 and 104, inclusive.
A.3.14 The <<D2Datatype>> "Hectopascal"
A measure of pressure defined in hectopascal.
A.3.15 The <<D2Datatype>> "Integer"
An integer number whose value space is the set {-2147483648, -2147483647, -2147483646, ..., -2, -1, 0, 1, 2, ..., 2147483645, 2147483646, 2147483647}.
A.3.16 The <<D2Datatype>> "IntensityKilogramsPerSquareMetre"
A measure of the quantity of application of a substance to an area defined in kilograms per square metre.
A.3.17 The <<D2Datatype>> "IntensityMillimetresPerHour"
A measure of precipitation intensity defined in millimetres per hour.
A.3.18 The <<D2Datatype>> "KilometresPerHour"
A measure of speed defined in kilometres per hour.
A.3.19 The <<D2Datatype>> "Language"
A language datatype, identifies a specified language by an ISO 639-1 2-alpha code.
A.3.20 The <<D2Datatype>> "LongString"
A character string with no specified length limit, whose value space is the set of finite-length sequences of characters. Every character has a corresponding Universal Character Set code point (as defined in ISO/IEC 10646), which is an integer.
A.3.21 The <<D2Datatype>> "MetresAsFloat"
A measure of distance defined in metres in a floating point format.
A.3.22 The <<D2Datatype>> "MetresAsNonNegativeInteger"
A measure of distance defined in metres in a non negative integer format.
A.3.23 The <<D2Datatype>> "MetresPerSecond"
A measure of speed defined in metres per second.
A.3.24 The <<D2Datatype>> "MultilingualString"
A multilingual string, whereby the same text may be expressed in more than one language.
A.3.25 The <<D2Datatype>> "NonNegativeInteger"
An integer number whose value space is the set {0, 1, 2, ..., 2147483645, 2147483646, 2147483647}.
A.3.26 The <<D2Datatype>> "Percentage"
A measure of percentage.
A.3.27 The <<D2Datatype>> "Reference"
A reference to an identifiable managed object where the identifier is unique. It comprises an identifier (e.g. GUID) and a string identifying the class of the referenced object.
A.3.28 The <<D2Datatype>> "Seconds"
Seconds.
A.3.29 The <<D2Datatype>> "String"
A character string whose value space is the set of finite-length sequences of characters. Every character has a corresponding Universal Character Set code point (as defined in ISO/IEC 10646), which is an integer.
A.3.30 The <<D2Datatype>> "TemperatureCelsius"
A measure of temperature defined in degrees Celsius.
A.3.31 The <<D2Datatype>> "Time"
An instant of time that recurs every day. The value space of time is the space of time of day values as defined in § 5.3 of [ISO 8601]. Specifically, it is a set of zero-duration daily time instances.
A.3.32 The <<D2Datatype>> "Tonnes"
A measure of weight defined in metric tonnes.
A.3.33 The <<D2Datatype>> "Url"
A Uniform Resource Locator (URL) address comprising a compact string of characters for a resource available on the Internet.
A.3.34 The <<D2Datatype>> "VehiclesPerHour"
Vehicles per hour.
A.3.35 The <<D2Datatype>> "VersionedReference"
A reference to an identifiable version managed object where the combination of the identifier and version is unique. It comprises an identifier (e.g. GUID), a version (NonNegativeInteger) and a string identifying the class of the referenced object.
A.3.36 The <<D2Datatype>> "Year"
A year.
### A.4 Data Dictionary of <<D2Enumeration>> for "Common"
This clause contains the definitions of all enumerations which are used in the "Common".
A.4.1 The <<D2Enumeration>> "CalendarWeekWithinMonthEnum"
Calendar week within month (see ISO8601).
Table A.20— Values contained in the enumeration "CalendarWeekWithinMonthEnum"
Enumerated value name | Designation | Definition
fifthWeek | Fifth week | Fifth week of the month.
firstWeek | First week | Calendar week containing the first of the month. Several days of the first week of the month may occur in the previous calendar month. By construction, the last week of a preceding month can also be the first week of a subsequent month.
fourthWeek | Fourth week | Fourth week of the month.
lastWeek | Last week | Last calendar week within month, regardless of its actual number. The last calendar week is the week beginning with Monday and containing the last of the month.
secondWeek | Second week | Second week of the month.
sixthWeek | Sixth week | Sixth week of the month.
thirdWeek | Third week | Third week of the month.
A.4.2 The <<D2Enumeration>> "ComparisonOperatorEnum"
Logical comparison operations.
Table A.21— Values contained in the enumeration "ComparisonOperatorEnum"
Enumerated value name | Designation | Definition
equalTo | Equal to | Logical comparison operator of equal to".
greaterThan | Greater than | Logical comparison operator of "greater than".
greaterThanOrEqualTo | Greater than or equal to | Logical comparison operator of "greater than or equal to".
lessThan | Less than | Logical comparison operator of "less than".
lessThanOrEqualTo | Less than or equal to | Logical comparison operator of "less than or equal to".
A.4.3 The <<D2Enumeration>> "ComputationMethodEnum"
Types of computational methods used in deriving data values for data sets.
Table A.22— Values contained in the enumeration "ComputationMethodEnum"
Enumerated value name | Designation | Definition
arithmeticAverageOfSamplesBasedOnAFixedNumberOfSamples | Arithmetic average of samples based on a fixed number of samples | Arithmetic average of sample values based on a fixed number of samples.
arithmeticAverageOfSamplesInATimePeriod | Arithmetic average of samples in a time period | Arithmetic average of sample values in a time period.
harmonicAverageOfSamplesInATimePeriod | Harmonic average of samples in a time period | Harmonic average of sample values in a time period.
medianOfSamplesInATimePeriod | Median of samples in a time period | Median of sample values taken over a time period.
movingAverageOfSamples | Moving average of samples | Moving average of sample values.
A.4.4 The <<D2Enumeration>> "ConfidentialityValueEnum"
Values of confidentiality.
Table A.23— Values contained in the enumeration "ConfidentialityValueEnum"
Enumerated value name | Designation | Definition
internalUse | Internal use | For internal use only of the recipient organisation.
noRestriction | No restriction | No restriction on usage.
restrictedToAuthorities | Restricted to authorities | Restricted for use only by authorities.
restrictedToAuthoritiesAndTrafficOperators | Restricted to authorities and traffic operators | Restricted for use only by authorities and traffic operators.
A.4.5 The <<D2Enumeration>> "DangerousGoodsRegulationsEnum"
Types of dangerous goods regulations.
Table A.24— Values contained in the enumeration "DangerousGoodsRegulationsEnum"
Enumerated value name | Designation | Definition
adr | ADR | European agreement on the international carriage of dangerous goods on road.
iataIcao | IATA ICAO | Regulations covering the international transportation of dangerous goods issued by the International Air Transport Association and the International Civil Aviation Organisation.
imoImdg | IMO IMDG | Regulations regarding the transportation of dangerous goods on ocean-going vessels issued by the International Maritime Organisation.
railroadDangerousGoodsBook | Railroad dangerous goods book | International regulations concerning the international carriage of dangerous goods by rail.
A.4.6 The <<D2Enumeration>> "DayEnum"
Days of the week.
Table A.25— Values contained in the enumeration "DayEnum"
Enumerated value name | Designation | Definition
friday | Friday | Friday.
monday | Monday | Monday.
saturday | Saturday | Saturday.
sunday | Sunday | Sunday.
thursday | Thursday | Thursday.
tuesday | Tuesday | Tuesday.
wednesday | Wednesday | Wednesday.
A.4.7 The <<D2Enumeration>> "DirectionCompassEnum"
Cardinal direction points of the compass.
Table A.26— Values contained in the enumeration "DirectionCompassEnum"
Enumerated value name | Designation | Definition
east | East | East.
eastNorthEast | East north east | East north east.
eastSouthEast | East south east | East south east.
north | North | North.
northEast | North east | North east.
northNorthEast | North north east | North north east.
northNorthWest | North north west | North north west.
northWest | North west | North west.
south | South | South.
southEast | South east | South east.
southSouthEast | South south east | South south east.
southSouthWest | South south west | South south west.
southWest | South west | South west.
west | West | West.
westNorthWest | West north west | West north west.
westSouthWest | West south west | West south west.
A.4.8 The <<D2Enumeration>> "EmissionClassificationEuroEnum"
Classification of emission according to the Euro emission classification (based on serveral amendments on 1970 Directive 70/220/EEC). Note That vehicleType as well as fuelType are mandatory to provide to make this classification explicit.
Table A.27— Values contained in the enumeration "EmissionClassificationEuroEnum"
Enumerated value name | Designation | Definition
euro5 | Euro5 | Euro 5.
euro5a | Euro5a | Euro 5a.
euro5b | Euro5b | Euro 5b.
euro6 | Euro6 | Euro 6.
euro6a | Euro6a | Euro 6a.
euro6b | Euro6b | Euro 6b.
euro6c | Euro6c | Euro 6c.
euroV | Euro v | Euro V.
euroVI | Euro v i | Euro VI.
other | Other | Any other level.
A.4.9 The <<D2Enumeration>> "FaultSeverityEnum"
Classification of the severity of faults.
Table A.28— Values contained in the enumeration "FaultSeverityEnum"
Enumerated value name | Designation | Definition
high | High | The fault is of high severity which will render the equipment unusable or any data generated by the equipment to be of no value.
low | Low | The fault is of low severity and has only limited impact on the usability of the equipment or the value of the data generated by the equipment.
medium | Medium | The fault is of medium severity which will significantly limit the usability of the equipment or devalue the usefulness of the data generated by the equipment.
unknown | Unknown | The fault is of unknown severity and hence its effect on the usability of the equipment or the usefulness of the data generated by the equipment can not be assessed.
A.4.10 The <<D2Enumeration>> "FaultUrgencyEnum"
Classification of the urgency to rectify a fault.
Table A.29— Values contained in the enumeration "FaultUrgencyEnum"
Enumerated value name | Designation | Definition
extremelyUrgent | Extremely urgent | The fault is to be rectified extremely urgency.
normal | Normal | The fault is of normal urgency.
unknown | Unknown | The fault is of unknown urgency.
urgent | Urgent | The fault is to be rectified urgent.
A.4.11 The <<D2Enumeration>> "FuelTypeEnum"
Type of fuel used by a vehicle.
Table A.30— Values contained in the enumeration "FuelTypeEnum"
Enumerated value name | Designation | Definition
all | All | All sort of fuel is accepted.
battery | Battery | Battery.
biodiesel | Biodiesel | Biodiesel.
diesel | Diesel | Fuel used for compression-ignition (CI) engines.
dieselBatteryHybrid | Diesel battery hybrid | Diesel and battery hybrid.
ethanol | Ethanol | Ethanol.
hydrogen | Hydrogen | Hydrogen.
liquidGas | Liquid gas | Liquid gas of any type including LPG.
lpg | LPG | Liquid petroleum gas.
methane | Methane | Methane gas.
other | Other | Other.
petrol | Petrol | Fuel used for positive-ignition (PI) engines.
petrol95Octane | Petrol95 octane | Petrol with 95 octane.
petrol98Octane | Petrol98 octane | Petrol with 98 octane.
petrolBatteryHybrid | Petrol battery hybrid | Petrol and battery hybrid.
petrolLeaded | Petrol leaded | Leaded petrol.
petrolUnleaded | Petrol unleaded | Unleaded petrol.
unknown | Unknown | The sort of fuel is not known.
A.4.12 The <<D2Enumeration>> "InformationDeliveryServicesEnum"
List of service channels or devices on which information or data exchanged can be delivered.
Table A.31— Values contained in the enumeration "InformationDeliveryServicesEnum"
Enumerated value name | Designation | Definition
anyGeneralDeliveryService | Any general delivery service | Includes any general delivery channel such as broadcast channels (e.g. radio, tv, RDS-TMC, TPEG services, etc.) or web publishing available to public or to specific users, depending on Service Provider policies.
safetyServices | Safety services | Specific services which deliver warning alerts to end users to enhance safety via any specific application available to drivers, including C-ITS services.
vms | Vms | Variable Message Signs or any other visual roadside devices which information are accessible to drivers which aim to affect driving style improving safety and road network LoS.
A.4.13 The <<D2Enumeration>> "InformationStatusEnum"
Status of the related information (i.e. real, test or exercise).
Table A.32— Values contained in the enumeration "InformationStatusEnum"
Enumerated value name | Designation | Definition
real | Real | The information is real. It is not a test or exercise.
securityExercise | Security exercise | The information is part of an exercise which is for testing security.
technicalExercise | Technical exercise | The information is part of an exercise which includes tests of associated technical subsystems.
test | Test | The information is part of a test for checking the exchange of this type of information.
A.4.14 The <<D2Enumeration>> "InstanceOfDayEnum"
Instances of a day of the week in a month
Table A.33— Values contained in the enumeration "InstanceOfDayEnum"
Enumerated value name | Designation | Definition
fifthInstance | Fifth instance | Fifth instance of specified day of week in month.
firstInstance | First instance | First instance of specified day of week in month.
fourthInstance | Fourth instance | Fourth instance of specified day of week in month.
lastInstance | Last instance | Last instance of specified day of week in month (regardless its actual instance number).
secondInstance | Second instance | Second instance of specified day of week in month.
thirdInstance | Third instance | Third instance of specified day of week in month.
A.4.15 The <<D2Enumeration>> "LoadTypeEnum"
Types of load carried by a vehicle.
Table A.34— Values contained in the enumeration "LoadTypeEnum"
Enumerated value name | Designation | Definition
abnormalLoad | Abnormal load | A load that exceeds normal vehicle dimensions in terms of height, length, width, gross vehicle weight or axle weight or any combination of these. Generally termed an "abnormal load".
ammunition | Ammunition | Ammunition.
chemicals | Chemicals | Chemicals of unspecified type.
combustibleMaterials | Combustible materials | Combustible materials of unspecified type.
corrosiveMaterials | Corrosive materials | Corrosive materials of unspecified type.
debris | Debris | Debris of unspecified type.
empty | Empty | No load.
explosiveMaterials | Explosive materials | Explosive materials of unspecified type.
extraHighLoad | Extra high load | A load of exceptional height.
extraLongLoad | Extra long load | A load of exceptional length.
extraWideLoad | Extra wide load | A load of exceptional width.
fuel | Fuel | Fuel of unspecified type.
glass | Glass | Glass.
goods | Goods | Any goods of a commercial nature.
hazardousMaterials | Hazardous materials | Materials classed as being of a hazardous nature.
liquid | Liquid | Liquid of an unspecified nature.
livestock | Livestock | Livestock.
materials | Materials | General materials of unspecified type.
materialsDangerousForPeople | Materials dangerous for people | Materials classed as being of a danger to people or animals.
materialsDangerousForTheEnvironment | Materials dangerous for the environment | Materials classed as being potentially dangerous to the environment.
materialsDangerousForWater | Materials dangerous for water | Materials classed as being dangerous when exposed to water (e.g. materials which may react exothermically with water).
oil | Oil | Oil.
ordinary | Ordinary | Materials that present limited environmental or health risk. Non-combustible, non-toxic, non-corrosive.
other | Other | Other than as defined in this enumeration.
perishableProducts | Perishable products | Products or produce that will significantly degrade in quality or freshness over a short period of time.
petrol | Petrol | Petrol or petroleum.
pharmaceuticalMaterials | Pharmaceutical materials | Pharmaceutical materials.
radioactiveMaterials | Radioactive materials | Materials that emit significant quantities of electro-magnetic radiation that may present a risk to people, animals or the environment.
refrigeratedGoods | Refrigerated goods | Refrigerated goods.
refuse | Refuse | Refuse.
toxicMaterials | Toxic materials | Materials of a toxic nature which may damage the environment or endanger public health.
vehicles | Vehicles | Vehicles of any type which are being transported.
A.4.16 The <<D2Enumeration>> "LowEmissionLevelEnum"
The emission level of a vehicle.
Table A.35— Values contained in the enumeration "LowEmissionLevelEnum"
Enumerated value name | Designation | Definition
freeOfEmission | Free of emission | Only vehicles that do not produce emissions (e.g. electric driven). Hybrid driven cars are allowed, when they switch to emission free mode within the considered situation.
lowLevelEmission | Low level emission | Vehicles with low level mission.
A.4.17 The <<D2Enumeration>> "MonthOfYearEnum"
A list of the months of the year.
Table A.36— Values contained in the enumeration "MonthOfYearEnum"
Enumerated value name | Designation | Definition
april | April | The month of April.
august | August | The month of August.
december | December | The month of December.
february | February | The month of February.
january | January | The month of January.
july | July | The month of July.
june | June | The month of June.
march | March | The month of March.
may | May | The month of May.
november | November | The month of November.
october | October | The month of October.
september | September | The month of September.
A.4.18 The <<D2Enumeration>> "PollutantTypeEnum"
Types of pollutant that can be measured in the atmosphere.
Table A.37— Values contained in the enumeration "PollutantTypeEnum"
Enumerated value name | Designation | Definition
benzeneTolueneXylene | Benzene toluene xylene | Benzene, toluene or xylene.
carbonMonoxide | Carbon monoxide | Carbon monoxide.
lead | Lead | Lead.
methane | Methane | Methane.
nitricOxide | Nitric oxide | Nitric oxide.
nitrogenDioxide | Nitrogen dioxide | Nitrogen dioxide.
nitrogenMonoxide | Nitrogen monoxide | Nitrogen monoxide.
nitrogenOxides | Nitrogen oxides | Nitrogen oxides.
nonMethaneHydrocarbons | Non methane hydrocarbons | Non-methane hydrocarbons.
ozone | Ozone | Ozone.
particulates10 | Particulates10 | Particulate matter which passes through a size-selective inlet with a 50% cut-off efficiency at an aerodynamic diameter of 10 µm (micrometres).
polycyclicAromaticHydrocarbons | Polycyclic aromatic hydrocarbons | Polycyclic aromatic ydrocarbons.
primaryParticulate | Primary particulate | Primary particulate particles.
sulphurDioxide | Sulphur dioxide | Sulphur dioxide.
totalHydrocarbons | Total hydrocarbons | Total hydrocarbons, i.e. including methane and non-methane.
A.4.19 The <<D2Enumeration>> "PrecipitationIntensityEnum"
Intensity of precipitation.
Table A.38— Values contained in the enumeration "PrecipitationIntensityEnum"
Enumerated value name | Designation | Definition
heavy | Heavy | Heavy precipitation.
light | Light | Light precipitation.
moderate | Moderate | Moderate precipitation.
noPhenomena | No phenomena | No precipitation phenomena.
severe | Severe | #
violent | Violent | Violent precipitation.
A.4.20 The <<D2Enumeration>> "PrecipitationTypeEnum"
Types of precipitation.
Table A.39— Values contained in the enumeration "PrecipitationTypeEnum"
Enumerated value name | Designation | Definition
clearIce | Clear ice | Clear ice.
dew | Dew | Dew.
diamondDust | Diamond dust | Diamond dust.
drizzle | Drizzle | Light, fine rain.
freezingRain | Freezing rain | Freezing rain.
glaze | Glaze | Glaze.
hail | Hail | Small balls of ice and compacted snow.
hardRime | Hard rime | Hard rime.
hoarFrost | Hoar frost | Hoar frost.
iceCrystals | Ice crystals | Ice crystals.
icePellets | Ice pellets | Ice pellets.
liquidFreezing | Liquid freezing | Liquid, freezing precipitation.
liquidNotFreezing | Liquid not freezing | Liquid precipitation but not freezing.
noPrecipitation | No precipitation | No precipitation.
rain | Rain | Rain.
rime | Rime | Rime.
sleet | Sleet | Wet snow mixed with rain.
smallHail | Small hail | Small Hail.
snow | Snow | Snow.
snowGrains | Snow grains | Snow grains.
snowPellets | Snow pellets | Snow pellets.
softRime | Soft rime | Soft rime.
solid | Solid | Solid precipitation.
unknown | Unknown | Unknown type of precipitation.
wetSnow | Wet snow | Wet snow.
whiteDev | White dev | White Dev.
A.4.21 The <<D2Enumeration>> "PublicEventTypeEnum"
Types of public events.
Table A.40— Values contained in the enumeration "PublicEventTypeEnum"
Enumerated value name | Designation | Definition
agriculturalShow | Agricultural show | Agricultural show or event which could disrupt traffic.
airShow | Air show | Air show or other aeronautical event which could disrupt traffic.
artEvent | Art event | Art event
athleticsMeeting | Athletics meeting | Athletics event that could disrupt traffic.
ballGame | Ball game | Ball game event that could disrupt traffic.
baseballGame | Baseball game | Baseball game event that could disrupt traffic.
basketballGame | Basketball game | Basketball game event that could disrupt traffic.
beerFestival | Beer festival | Beer festival
bicycleRace | Bicycle race | Bicycle race that could disrupt traffic.
boatRace | Boat race | Regatta (boat race event of sailing, powerboat or rowing) that could disrupt traffic.
boatShow | Boat show | Boat show which could disrupt traffic.
boxingTournament | Boxing tournament | Boxing event that could disrupt traffic.
bullFight | Bull fight | Bull fighting event that could disrupt traffic.
ceremonialEvent | Ceremonial event | Formal or religious act, rite or ceremony that could disrupt traffic.
commercialEvent | Commercial event | Commercial event which could disrupt traffic.
concert | Concert | Concert event that could disrupt traffic.
cricketMatch | Cricket match | Cricket match that could disrupt traffic.
culturalEvent | Cultural event | Cultural event which could disrupt traffic.
exhibition | Exhibition | Major display or trade show which could disrupt traffic.
fair | Fair | Periodic (e.g. annual), often traditional, gathering for entertainment or trade promotion, which could disrupt traffic.
festival | Festival | Celebratory event or series of events which could disrupt traffic.
filmFestival | Film festival | Film festival
filmTVMaking | Film TV making | Film or TV making event which could disrupt traffic.
fireworkDisplay | Firework display | Firework display
flowerEvent | Flower event | Flower event
foodFestival | Food festival | Food festival
footballMatch | Football match | Football match that could disrupt traffic.
funfair | Funfair | Periodic (e.g. annual), often traditional, gathering for entertainment, which could disrupt traffic.
gardeningOrFlowerShow | Gardening or flower show | Gardening and/or flower show or event which could disrupt traffic.
golfTournament | Golf tournament | Golf tournament event that could disrupt traffic.
hockeyGame | Hockey game | Hockey game event that could disrupt traffic.
horseRaceMeeting | Horse race meeting | Horse race meeting that could disrupt traffic.
internationalSportsMeeting | International sports meeting | Large sporting event of an international nature that could disrupt traffic.
majorEvent | Major event | Significant organised event either on or near the roadway which could disrupt traffic.
marathon | Marathon | Marathon, cross-country or road running event that could disrupt traffic.
market | Market | Periodic (e.g. weekly) gathering for buying and selling, which could disrupt traffic.
match | Match | Sports match of unspecified type that could disrupt traffic.
motorShow | Motor show | Motor show which could disrupt traffic.
motorSportRaceMeeting | Motor sport race meeting | Motor sport race meeting that could disrupt traffic.
openAirConcert | Open air concert | Open air concert
other | Other | Other than as defined in this enumeration.
parade | Parade | Formal display or organized procession which could disrupt traffic.
procession | Procession | An organised procession which could disrupt traffic.
raceMeeting | Race meeting | Race meeting (other than horse or motor sport) that could disrupt traffic.
rugbyMatch | Rugby match | Rugby match that could disrupt traffic.
severalMajorEvents | Several major events | A series of significant organized events either on or near the roadway which could disrupt traffic.
show | Show | Entertainment event that could disrupt traffic.
showJumping | Show jumping | Horse showing jumping and tournament event that could disrupt traffic.
soundAndLightShow | Sound and light show | Sound and light show.
sportsMeeting | Sports meeting | Sports event of unspecified type that could disrupt traffic.
stateOccasion | State occasion | Public ceremony or visit of national or international significance which could disrupt traffic.
streetFestival | Street festival | Street festival
tennisTournament | Tennis tournament | Tennis tournament that could disrupt traffic.
theatricalEvent | Theatrical event | Theatrical event
tournament | Tournament | Sporting event or series of events of unspecified type lasting more than one day which could disrupt traffic.
tradeFair | Trade fair | A periodic (e.g. annual), often traditional, gathering for trade promotion, which could disrupt traffic.
unknown | Unknown | Service provider does not know at time of message generation.
waterSportsMeeting | Water sports meeting | Water sports meeting that could disrupt traffic.
wineFestival | Wine festival | Wine festival
winterSportsMeeting | Winter sports meeting | Winter sports meeting or event (e.g. skiing, ski jumping, skating) that could disrupt traffic.
A.4.22 The <<D2Enumeration>> "SourceTypeEnum"
Type of sources from which situation information may be derived.
Table A.41— Values contained in the enumeration "SourceTypeEnum"
Enumerated value name | Designation | Definition
automobileClubPatrol | Automobile club patrol | A patrol of an automobile club.
cameraObservation | Camera observation | A camera observation (either still or video camera).
freightVehicleOperator | Freight vehicle operator | An operator of freight vehicles.
inductionLoopMonitoringStation | Induction loop monitoring station | A station dedicated to the monitoring of the road network by processing inductive loop information.
infraredMonitoringStation | Infrared monitoring station | A station dedicated to the monitoring of the road network by processing infrared image information.
microwaveMonitoringStation | Microwave monitoring station | A station dedicated to the monitoring of the road network by processing microwave information.
mobileTelephoneCaller | Mobile telephone caller | A caller using a mobile telephone (who may be or not on the road network).
nonPoliceEmergencyServicePatrol | Non police emergency service patrol | Emergency service patrols other than police.
otherInformation | Other information | Other sources of information.
otherOfficialVehicle | Other official vehicle | Personnel from a vehicle belonging to the road operator or authority or any emergency service, including authorised breakdown service organisations.
policePatrol | Police patrol | A police patrol.
privateBreakdownService | Private breakdown service | A private breakdown service.
publicAndPrivateUtilities | Public and private utilities | A utility organisation, either public or private.
registeredMotoristObserver | Registered motorist observer | A motorist who is an officially registered observer.
roadAuthorities | Road authorities | A road authority.
roadOperatorPatrol | Road operator patrol | A patrol of the road operator or authority.
roadsideTelephoneCaller | Roadside telephone caller | A caller who is using an emergency roadside telephone.
spotterAircraft | Spotter aircraft | A spotter aircraft of an organization specifically assigned to the monitoring of the traffic network.
trafficMonitoringStation | Traffic monitoring station | A station, usually automatic, dedicated to the monitoring of the road network.
transitOperator | Transit operator | An operator of a transit service, e.g. bus link operator.
vehicleProbeMeasurement | Vehicle probe measurement | A specially equipped vehicle used to provide measurements.
videoProcessingMonitoringStation | Video processing monitoring station | A station dedicated to the monitoring of the road network by processing video image information.
A.4.23 The <<D2Enumeration>> "SpecialDayTypeEnum"
Collection of special types of days.
Table A.42— Values contained in the enumeration "SpecialDayTypeEnum"
Enumerated value name | Designation | Definition
dayBeforePublicHoliday | Day before public holiday | The day preceding a public holiday.
dayFollowingPublicHoliday | Day following public holiday | A day following a public holiday.
inLieuOfPublicHoliday | In lieu of public holiday | A holiday in lieu of a public holiday that falls on a weekend.
longWeekendDay | Long weekend day | A day between a public holiday and the weekend.
other | Other | Some other special day.
publicEventDay | Public event day | A day of a public event. You may use the publicEvent attribute to specify the corresponding event.
publicHoliday | Public holiday | A public holiday in general. You may use the PublicHoliday class to refer on a specific public holiday.
schoolDay | School day | A school day.
schoolHolidays | School holidays | A day within the school holidays.
A.4.24 The <<D2Enumeration>> "TimePrecisionEnum"
List of precisions to which times can be given.
Table A.43— Values contained in the enumeration "TimePrecisionEnum"
Enumerated value name | Designation | Definition
halfHour | Half hour | Time given to the nearest half hour.
hour | Hour | Time given to the nearest hour.
minute | Minute | Time given to the nearest minute.
quarterHour | Quarter hour | Time given to the nearest quarter hour.
second | Second | Time given to the nearest second.
tenthsOfSecond | Tenths of second | Time given to the nearest tenth of a second.
A.4.25 The <<D2Enumeration>> "TrafficTrendTypeEnum"
List of term1s used to describe the trend in traffic conditions.
Table A.44— Values contained in the enumeration "TrafficTrendTypeEnum"
Enumerated value name | Designation | Definition
trafficBuildingUp | Traffic building up | Traffic conditions are changing from free-flow to heavy or slow service levels. Queues may also be expected.
trafficEasing | Traffic easing | Traffic conditions are changing from heavy or slow service levels to free flow.
trafficStable | Traffic stable | Traffic conditions are currently stable.
unknown | Unknown | The trend of traffic conditions is currently unknown.
A.4.26 The <<D2Enumeration>> "UrlLinkTypeEnum"
Types of URL links.
Table A.45— Values contained in the enumeration "UrlLinkTypeEnum"
Enumerated value name | Designation | Definition
documentPdf | Document PDF | URL link to a pdf document.
html | HTML | URL link to an html page.
image | Image | URL link to an image.
other | Other | Other than as defined in this enumeration.
rss | RSS | URL link to an RSS feed.
videoStream | Video stream | URL link to a video stream.
voiceStream | Voice stream | URL link to a voice stream.
A.4.27 The <<D2Enumeration>> "ValidityStatusEnum"
Values of validity status that can be assigned to a described event, action or item.
Table A.46— Values contained in the enumeration "ValidityStatusEnum"
Enumerated value name | Designation | Definition
active | Active | The described event, action or item is currently active regardless of the definition of the validity time specification.
definedByValidityTimeSpec | Defined by validity time spec | The validity status of the described event, action or item is in accordance with the definition of the validity time specification.
planned | Planned | The described event, action or item is currently planned regardless of the definition of the validity time specification.
suspended | Suspended | The described event, action or item is currently suspended, that is inactive, regardless of the definition of the validity time specification.
A.4.28 The <<D2Enumeration>> "VehicleEquipmentEnum"
Types of vehicle equipment in use or on board.
Table A.47— Values contained in the enumeration "VehicleEquipmentEnum"
Enumerated value name | Designation | Definition
notUsingSnowChains | Not using snow chains | Vehicle not using snow chains.
notUsingSnowChainsOrTyres | Not using snow chains or tyres | Vehicle not using either snow tyres or snow chains.
snowChainsInUse | Snow chains in use | Vehicle using snow chains.
snowChainsOrTyresInUse | Snow chains or tyres in use | Vehicle using snow tyres or snow chains.
snowTyresInUse | Snow tyres in use | Vehicle using snow tyres.
withoutSnowTyresOrChainsOnBoard | Without snow tyres or chains on board | Vehicle which is not carrying on board snow tyres or chains.
A.4.29 The <<D2Enumeration>> "VehicleStatusEnum"
The status of a vehicle.
Table A.48— Values contained in the enumeration "VehicleStatusEnum"
Enumerated value name | Designation | Definition
abandoned | Abandoned | Abandoned vehicle.
brokenDown | Broken down | Broken down vehicle (i.e. it is immobile due to mechanical breakdown).
burntOut | Burnt out | Burnt out vehicle, but fire is extinguished.
damaged | Damaged | Vehicle is damaged following an incident or collision. It may be able or not to move by itself.
damagedAndImmobilized | Damaged and immobilized | Vehicle is damaged following an incident or collision. It is immobilized and therefore needs assistance to be moved.
inDitch | In ditch | Vehicle has left roadway and ended in a ditch next to the roadway
jacknifed | Jacknifed | The pulling vehicle is in a jackknifed position with its trailer
offRoad | Off road | Vehicle has left the carriageway
onFire | On fire | Vehicle is on fire.
onTopOfCrashBarrier | On top of crash barrier | Vehicle is on top of the crash barrier, and cannot leave that position autonomously
onWheels | On wheels | Vehicle is in its upright position after the accident. No special lifting equipment is needed to put it on its wheels
overturned | Overturned | Vehicle is on its side or upside down
rollable | Rollable | The vehicle can be rolled on its own wheels. There is no special equipment needed to lift the vehicle, because of blocked wheels or other mechanical problems.
spunAround | Spun around | Vehicle has come to rest not facing its intended line of travel.
A.4.30 The <<D2Enumeration>> "VehicleTypeEnum"
Types of vehicle.
Table A.49— Values contained in the enumeration "VehicleTypeEnum"
Enumerated value name | Designation | Definition
agriculturalVehicle | Agricultural vehicle | Vehicle normally used for agricultural purposes, e.g. tractor, combined harvester etc.
anyVehicle | Any vehicle | Vehicle of any type.
articulatedBus | Articulated bus | Articulated bus
articulatedTrolleyBus | Articulated trolley bus | Articulated trolley bus
articulatedVehicle | Articulated vehicle | Articulated vehicle.
bicycle | Bicycle | Bicycle.
bus | Bus | Bus.
car | Car | Vehicles designed and constructed for the carriage of passengers and comprising no more than eight seats in addition to the driver’s seat, and having a maximum mass (“technically permissible maximum laden mass”) not exceeding 3.5 tons (M1).
caravan | Caravan | Caravan.
carOrLightVehicle | Car or light vehicle | Car or light vehicle.
carWithCaravan | Car with caravan | Car towing a caravan.
carWithTrailer | Car with trailer | Car towing a trailer.
constructionOrMaintenanceVe hicle | Construction or maintenance vehicle | Vehicle normally used for construction or maintenance purposes, e.g. digger, excavator, bulldozer, lorry mounted crane etc.
fourWheelDrive | Four wheel drive | Four wheel drive vehicle.
heavyDutyTransporter | Heavy duty transporter | A transporter for heavy duty (usually with abnormal dimensions).
heavyGoodsVehicle | Heavy goods vehicle | Vehicles with a total weight above 3,500 kg (vehicle and load).
heavyGoodsVehicleWithTrailer | Heavy goods vehicle with trailer | Heavy goods vehicle with trailer
heavyVehicle | Heavy vehicle | Vehicle whose weight means it should be classed as a heavy vehicle
highSidedVehicle | High sided vehicle | High sided vehicle.
largeCar | Large car | Large car
largeGoodsVehicle | Large goods vehicle | Vehicles for the carriage of goods and having a maximum mass exceeding 3.5 tonnes (belonging to class N2 when not exceeding 12 tonnes, otherwise class N3).
lightCommercialVehicle | Light commercial vehicle | Vehicles for the carriage of goods and having a maximum mass not exceeding 3.5 tonnes (class N1).
lightCommercialVehicleWithTr ailer | Light commercial vehicle with trailer | Light goods vehicle with trailer
longHeavyLorry | Long heavy lorry | A heavy lorry that is longer than normal.
lorry | Lorry | Lorry of any type.
metro | Metro | Metro
minibus | Minibus | Vehicles designed and constructed for the carriage of passengers, comprising more than eight seats in addition to the driver’s seat, and having a maximum mass not exceeding 5 tonnes (class M2).
moped | Moped | Moped (a two wheeled motor vehicle characterized by a small engine typically less than 50cc and by normally having pedals).
motorcycle | Motorcycle | Motorcycle.
motorcycleWithSideCar | Motorcycle with side car | Three wheeled vehicle comprising a motorcycle with an attached side car.
motorhome | Motorhome | Motorhome
motorscooter | Motorscooter | Motorscooter (a two wheeled motor vehicle characterized by a step through frame and small diameter wheels).
other | Other | Other than as defined in this enumeration.
passengerCar | Passenger car | Passenger car
smallCar | Small car | Small car
tanker | Tanker | Vehicle with large tank for carrying bulk liquids.
threeWheeledVehicle | Three wheeled vehicle | Three wheeled vehicle of unspecified type.
trailer | Trailer | Trailer.
tram | Tram | Tram.
trolleyBus | Trolley bus | Trolley bus
twoWheeledVehicle | Two wheeled vehicle | Two wheeled vehicle of unspecified type.
unknown | Unknown | Unknown.
van | Van | Van.
vehicleWithCaravan | Vehicle with caravan | Vehicle (of unspecified type) towing a caravan.
vehicleWithCatalyticConverter | Vehicle with catalytic converter | Vehicle with catalytic converter.
vehicleWithoutCatalyticConver ter | Vehicle without catalytic converter | Vehicle without catalytic converter.
vehicleWithTrailer | Vehicle with trailer | Vehicle (of unspecified type) towing a trailer.
withEvenNumberedRegistratio nPlates | With even numbered registration plates | Vehicle with even numbered registration plate.
withOddNumberedRegistratio nPlates | With odd numbered registration plates | Vehicle with odd numbered registration plate.
A.4.31 The <<D2Enumeration>> "VehicleUsageEnum"
Types of usage of a vehicle.
Table A.50— Values contained in the enumeration "VehicleUsageEnum"
Enumerated value name | Designation | Definition
agricultural | Agricultural | Vehicle used for agricultural purposes.
carSharing | Car sharing | Vehicles operated by a car-sharing company.
cityLogistics | City logistics | Vehicles that are used to deliver goods in a city area.
commercial | Commercial | Vehicle which is limited to non private usage or public transport usage.
emergencyServices | Emergency services | Vehicle used by the emergency services.
military | Military | Vehicle used by the military.
nonCommercial | Non commercial | Vehicle used for non-commercial or private purposes.
patrol | Patrol | Vehicle used as part of a patrol service, e.g. road operator or automobile association patrol vehicle.
recoveryServices | Recovery services | Vehicle used to provide a recovery service.
roadMaintenanceOrConstructi on | Road maintenance or construction | Vehicle used for road maintenance or construction work purposes.
roadOperator | Road operator | Vehicle used by the road operator.
taxi | Taxi | Vehicle used to provide an authorised taxi service.
A.4.32 The <<D2Enumeration>> "WeatherRelatedRoadConditionTypeEnum"
Types of road surface conditions which are related to the weather.
Table A.51— Values contained in the enumeration "WeatherRelatedRoadConditionTypeEnum"
Enumerated value name | Designation | Definition
blackIce | Black ice | Severe skid risk due to black ice (i.e. clear ice, which is impossible or very difficult to see).
deepSnow | Deep snow | Deep snow on the roadway.
dry | Dry | There is no humidity over the sensor.
freezingOfWetRoads | Freezing of wet roads | The wet road surface is subject to freezing.
freezingPavements | Freezing pavements | The pavements for pedestrians are subject to freezing.
freezingRain | Freezing rain | Severe skid risk due to rain falling on sub-zero temperature road surface and freezing.
freshSnow | Fresh snow | Fresh snow (with little or no traffic yet) on the roadway.
glaze | Glaze | Glaze of the road surface.
ice | Ice | Increased skid risk due to ice (of any kind).
iceBuildUp | Ice build up | Ice is building up on the roadway causing a serious skid hazard.
iceWithWheelBarTracks | Ice with wheel bar tracks | Ice on the road frozen in the form of wheel tracks.
icyPatches | Icy patches | Severe skid risk due to icy patches (i.e. intermittent ice on roadway).
looseSnow | Loose snow | Powdery snow on the road which is subject to being blown by the wind.
moist | Moist | From (0,01 mm) water film thickness over the sensor
normalWinterConditionsForPe destrians | Normal winter conditions for pedestrians | Conditions for pedestrians are consistent with those normally expected in winter.
notDry | Not dry | The road surface is not dry.
other | Other | Other than as defined in this enumeration.
packedSnow | Packed snow | Packed snow (heavily trafficked) on the roadway.
rime | Rime | Fresh snow (with little or no traffic yet) on the roadway.
roadSurfaceMelting | Road surface melting | The road surface is melting, or has melted due to abnormally high temperatures.
slippery | Slippery | Detection at least of the presence of partly or wholly solidified aqueous solution over the sensor.
slushOnRoad | Slush on road | Increased skid risk due to melting snow (slush) on road.
slushStrings | Slush strings | Melting snow (slush) on the roadway is formed into wheel tracks.
snow | Snow | Fresh snow (with little or no traffic yet) on the roadway.
snowDrifts | Snow drifts | Snow drifting is in progress or patches of deep snow are present due to earlier drifting.
snowOnPavement | Snow on pavement | Snow is on the pedestrian pavement.
snowOnTheRoad | Snow on the road | Snow is lying on the road surface.
streamingWater | Streaming water | From (2 mm) water film thickness over the sensor.
surfaceWater | Surface water | Water is resting on the roadway which provides an increased hazard to vehicles.
wet | Wet | From (0,2 mm) water film thickness over the sensor
wetAndIcyRoad | Wet and icy road | Increased skid risk due to partly thawed, wet road with packed snow and ice, or rain falling on packed snow and ice.
wetIcyPavement | Wet icy pavement | Partly thawed, wet pedestrian pavement with packed snow and ice, or rain falling on packed snow and ice.
A.4.33 The <<D2Enumeration>> "WeightTypeEnum"
Type of weight - describing the meaning of a vehicle weight value
Table A.52— Values contained in the enumeration “WeightTypeEnum”
Enumerated value name | Designation | Definition
actual | Actual | The weight is the actual weight of a specific vehicle
maximumPermitted | Maximum permitted | The weight is the maximum permitted weight for a vehicle
A.4.34 The <<D2Enumeration>> "WinterEquipmentManagementTypeEnum"
Instructions relating to the use of winter equipment.
Table A.53— Values contained in the enumeration "WinterEquipmentManagementTypeEnum"
Enumerated value name | Designation | Definition
doNotUseStudTyres | Do not use stud tyres | Do not use stud tyres.
other | Other | Other than as defined in this enumeration.
useSnowChains | Use snow chains | Use snow chains.
useSnowChainsOrTyres | Use snow chains or tyres | Use snow chains or snow tyres.
useSnowTyres | Use snow tyres | Use snow tyres.
winterEquipmentOnBoardRequired | Winter equipment on board required | The carrying of winter equipment (snow chains and/or snow tyres) is required.
Go back to the previous page
