url: https://docs.datex2.eu/v3.7/levels/mastering/common/
title: Common publication

## Common publication
### Predefined model elements
#### General
Besides regulations for the use of UML constructors and a UML profile providing additional meta information via tagged values and stereotypes, the DATEX II modelling methodology furthermore stipulates a certain top-level model structure for all compliant UML models. These clauses are mainly motivated by the need to create a well-defined structure for DATEX II tools aiming at supporting users.
#### Top level model packages and classes
The following rules apply for top level model packages and classes:
- DATEX II compliant UML models shall have one single top-level UML package named "D2Payload" of stereotype "D2Namespace".
The DATEX II top level package "D2Payload" shall have four sub-packages with the following names:
- "Common" of stereotype "D2Namespace"
- "Extension" of stereotype "D2Namespace"
- "LocationReferencing" of stereotype "D2Namespace"
- "PayloadPublication" of stereotype "D2Package"
The "PayloadPublication" package may contain several sub-packages of stereotype "D2Namespace". The Situation Publication specifies the sub-package "Situation" and its content. The standardisation of further sub-packages may follow in the future.
- The usage of the "Extension" package for creating customised DATEX extensions is specified in TODO -Extension
The "Common" package shall have three sub-packages with the following names:
- "Classes" of stereotype "D2Package" - see 2 TODO
- "DataTypes" of stereotype "D2Package" - see 1.3 TODO
- "Enumerations" of stereotype "D2Package" - see 1.4 TODO
The further content of these packages is specified in the further chapters of this document.
The "Common::Classes" package shall contain one abstract UML Class named "PayloadPublication" of stereotype "D2ModelRoot". It may contain further packages and classes.
- The tagged value "rootElement" of the DATEX II class "PayloadPublication" shall be set to "payload".
The tagged value "modelBaseVersion" of the DATEX II class "PayloadPublication" shall be set to "3" which is current DATEX II model version identifier. The tagged value "version" of the DATEX II class "PayloadPublication" shall be set to "3.n" where "n" is the minor version number.
Note
The model base version “3” denotes the third iteration of the second generation of DATEX specifications, denoted “DATEX II”. The Arabic version number “3” is not to be mixed up with the Roman “II” used to this generation a name that distinguishes it from the EDIFACT-based “DATEX” standard developed in the 1990s, finally resulting in the meanwhile withdrawn CEN ENVs 13106:2000 and 13777:2000.
The tagged values "extensionName" and "extensionVersion" of the DATEX II class "Payload Publication" shall contain the name of the extension(s) contained in the model and a corresponding version identifier in the case that the "Extension" package is non-empty. These values shall be provided by the creator of the model - see also the next figure.
The tagged values "profileName" and "profileVersion" of the DATEX II class "Payload Publication" shall contain the name of the profile (sub-model) and a corresponding version identifier in the case a profile is derived from the model. These values shall be provided by the creator of the model - see also the following figure.
These rules provide a well-defined entry structure into a DATEX II XML publication, which always starts at top level with one concrete instance of a class specialized from "PayloadPublication".
The class "PayloadPublication" shall have the following structure:
The class "PayloadPublication" shall have a "D2Relation" composition to the "InternationalIdentifier" class.
The “GenericPublication” class (see the figure "Class Payloadpublication") is a specific realisable case of a “PayloadPublication” and used to make level B extensions at the publication level. Its attribute “genericPublicationName” is used to specify a name for any level B extended publication.
The “InternationalIdentifier” class (see the figure above) shall provide an identifier/name whose range is specific to the particular country.
Note
The possible upper case two-letter codes related to the “country” attribute of class "InternationalIdentifier" (https://www.iso.org/obp/ui/#search/code/)
The "DataTypes" package shall have two sub-packages named "Generic" and "Specific" of stereotype "D2Package".
#### Basic datatypes
The "DataTypes::Generic" package (as defined in point k above) shall contain the following classes of stereotype "D2Datatype":
- "Base64Binary", "Boolean", "Date", "DateTime", "Decimal", "Double", "Float", "Integer", "Language", "LongString", "MultilanguageString", "NonNegativeInteger", "Reference", "String", "Time", "Url", "VersionedReference".
According definitions and XML Schema Definition mappings for these datatypes are described in A.3. TODO
The "DataTypes::Specific" package (as defined in 1.2 k) shall contain the following classes of stereotype "D2Datatype":
- "AngleInDegrees", "AxlesPerHour", "ConcentrationKilogramsPerCubicMetre", "ConcentrationMicrogramsPerCubicMetre", "CountryCode", "CubicMetres", "Hectopascal", "IntensityKilogramsPerSquareMetre", "IntensityMillimetresPerHour", "KilometresPerHour", "MetresAsFloat", "MetresAsNonNegativeInteger", "Percentage", "Seconds", "TemperatureCelsius", "Tonnes", "VehiclesPerHour", "Year".
According definitions and XML Schema Definition mappings for these datatypes are described in A.3. (TODO)
The datatype "MultilingualString" shall represent text that can be defined in more than one language. For this reason, it shall be a defined as an unbounded sequence of pairs of "value" and "lang", with "value" representing a string of max. length 1024 characters and "lang" representing a language. The corresponding XML Schema definition mapping can be found in TODO . (see in "Common.xsd" the complex types "MultilingualString", "MultilingualStringValue" and "MultilingualStringValueType").
If text within a "MultilingualString" is specified in more than one language, the usage of the "lang" attribute shall be mandatory.
#### Enumerations
The "Enumerations" package shall contain the ”D2Enumeration” stereotyped elements with according definitions and XML Schema Definition mappings as described in A.4. TODO
### D2Package "Common::Classes"
- WeatherRelated package
- DataValue package
- Validity package
- Vehicle package
- VehicleCharacteristics package
- Other classes
Go back to the previous page
