url: https://docs.datex2.eu/v3.7/levels/mastering/roadtrafficdata/
title: Measured and elaborated data publications

## Measured and elaborated data publications
### Introduction
The publications for these data are defined in the fifth part of EN 16157 that globally deals with. Road data, i.e. traffic data and weather data. Indeed, this document specifies three different publications (derived from the general payload publication of DATEX II):
- Measurement site table publication,
- Measured data publication,
- Elaborated data publication.
The first two ones are to use together. The third one is used alone. Measured data publication and elaborated data publication can be used to manage quite the same data. What is different is how the data are obtained and processed. Traffic values and weather values are normally provided as measured data, but can be provided as elaborated data if appropriate (e.g. because values are provided by calculation). These three publications share the same namespace.
### Measurement site table publication
#### Objectives and utilisation mechanisms
The measurement site table publication is used to provide information relating to predefined measurement sites and the measurements that can be made at these sites. The sites and the details of their measurement characteristics are seen as static or quasi static (i.e. they rarely change). The measurement site details and their measurement characteristics are referenced by measured data publications which enable these publications to be efficient when large volumes of measured data values need to be conveyed.
#### Content
This publication contains one or more measurement site tables.
With this publication, attributes can be given in the "InformationHeader" class which provide clients with information management details (confidentiality, information status, allowed delivery channels) relating to this publication. The measurement site table has a unique versioned identifier.
The measurement site table has a list of measurement sites, each corresponding to a single measurement site. It is associated with an information manager (class "InternationalIdentifier"). This latter information may be overridden at the measurement site level if it differs from the information defined for the table itself.
Every measurement site has a unique versioned identifier and the following attributes:
- Measurement equipment reference,
- Measurement equipment type used,
- Measurement site name,
- Measurement site number of lanes,
- Measurement site identification,
- Measurement site version time.
The measurement site always has a single location reference (but which can represent an itinerary or a non-ordered group of locations). Every site definition must also have an ordered list of measurement specific characteristics. This ordered (through an index) list of characteristics relates to the different types of measurements that can be made at that measurement site. The ordering is significant because this order is then used by indexing in the measured data publications to distinguish between the different measurements received from the referenced site. The following figure explain theses relations between both publications:
Figure 1: How measurement site table and measured data publications work together
Measurement specific characteristics contains information about:
- Accuracy,
- Period,
- Computation method,
- Smoothing factor,
- Specific measurement value type,
- Measurement side (according to the driving direction definition),
- Specific lane (number and usage),
- Specific vehicle characteristics,
- Specific axle characteristics (when the measurement is about classified axle flow).
These values are seen as static for the particular measurement at the site and do not have to be repeated for each measured value in the measured data publication, unless they need to be overridden in particular cases (see "measured data publication" section).
### Measured data publication
#### Objectives and utilisation mechanisms
This publication contains measurements from one or more sites. The measured data publication has to be used with one or several tables published by the "MeasuremementSiteTablePublication" publication and thus must contain a reference to the measurement site table used. This information is provided by the "measurementSiteTableReference" attribute (see figure 1). The reference mechanism and the indices are based on the values published by the referenced measurement site table publication.
#### Content
With this publication, attributes can be given in the "InformationHeader" class which provides clients with information management details (confidentiality, information status, allowed delivery channels) relating to this publication.
Each set of site measurement values must always contain a reference to the corresponding measurement site and information on "measurementTimeDefault" (value, meaning and/or precision). It represents information about the default time for each measured value if no other time is specified for an individual measurement. The other attributes can be considered as metadata on this value.
Each set of site measurements has an ordered (indexed) list of physical quantities representing the measured values, where the order (index) corresponds to the measurement definition order (index) in the measured site table. Therefore, there is no need for any further identification for each measured value. The values that are measured are referenced by the index in the ordered list of values for that site.
Physical quantities represent data that are either measured or calculated (elaborated). The physical quantity can be a single physical quantity, which means a measured or calculated physical quantity at a single instant or period in time.
Otherwise, the physical quantity can be a time-profiled physical quantity, which means a set of values for a measured or calculated physical quantity over a set of measurement or calculation times.
Each of these classes can be used for containing the data corresponding to a physical quantity. For one instance of the “TimeProfiledPhysicalQuantity” class, each instance of the “BasicData” class shall have the same concrete class, and shall have a different “timeValue” attribute.
Each physical quantity can identify the type of measurement equipment used. Other metadata can be attached to the physical quantity like the source, the identification of the data manager or details on an error or fault regarding this physical quantity. In case of fault when measuring this data, it is possible to specify the type of fault (intermittent data values, no data available, spurious unreliable data values, unknown fault or other).
A physical quantity can also have a location reference overriding the location reference attached to the measurement site. This may be especially used when there is need to override the predefined lanes attribute and to indicate a reversal of flow compared with that was defined in the measurement site table.
Each physical quantity (whatever its nature) comprises a basic data value which may be one of the following types:
- Travel time data
- Traffic status
- Traffic data
- Weather data
Basic data is a general abstract class which can be associated with the following attributes
- Time precision, precision to which time of calculation or measurement is given
- Period (in seconds)
- Time, the time when basic data value was measured or elaborated.
Moreover, the following points are of note for its use in the measured data publication:
- The point at which the measurement equipment is located (i.e. the site) is defined in the appropriate entry in the measurement site table. However, if the measurement relates to a section of road or a group of locations (e.g. ANPR which determines measurements over a stretch of road) this can also be provided via the “pertinentLocation” association with the physical quantity.
- Traffic status and travel time values are normally provided as elaborated data, but may be provided as measured data if appropriate (e.g. because values are provided by an outstation).
Traffic data is structured as follows. There are 6 kinds of traffic data:
- Traffic headway
- Traffic gap
- Traffic flow
- Traffic speed
- Traffic concentration
- Individual vehicle measurements.
Traffic data can be classified on the basis of vehicle characteristics.
Weather data value is structured as follows. There are 7 types of weather values:
- Precipitation information
- Wind information
- Temperature information
- Pollution information
- Road surface condition information
- Visibility information.
- Humidity information
It is important to note each basic data instance (traffic data or weather data) can be associated with its corresponding value. These classes are derived from the abstract class "DataValue". This class represents a data value of something that can be measured or calculated. It provides metadata to the different inherited data values like e.g. presence of error, measurement accuracy, computational method, the numbre of input values used or smoothing factor, … The following diagram explains the relationships between basic data and data value.
Figure 2: Relationships between “BasicData” and “DataValue” classes
### Elaborated data publication
#### Objectives and utilisation mechanisms
This publication is used to give information that is in some way elaborated or derived. Typically, these are data that have been calculated by a traffic centre from input data held in its database.
#### Content
This publication contains one or more elaborated data sets.
With this publication, attributes can be given in the "InformationHeader" class which provides clients with information management details (confidentiality, information status, allowed delivery channels) relating to this publication.
A set of default values for “forecast”, “period” and “time” can be provided to clients which are applicable throughout the publication if no others are provided at the detailed level. This helps in minimising the size of publications where large numbers of values are sent which share common parameters.
The elaborated data publication is also associated with an information manager (class "InternationalIdentifier"). This latter information may be overridden at the physical quantity level if it differs from the information defined for the publication itself.
Moreover, to contribute to minimise the volume of required values to be sent for traffic status covering wide expanses of a road network, the "ReferenceSettings" class can be used to provide a client with default information. This class comprises a reference to a predefined group of locations (see page on "predefined locations publication") and a default traffic status value that can be assumed by a client for the traffic status on all these locations if nothing specific is received. Thus, a supplier only needs to send for those locations the actual values of traffic status which deviate from this default value.
It can be indicated if the physical quantity is a forecast.
As for measured data source information can be given (country, identifier, name, type, reliable) for each elaborated data which are defined as physical quantities.
In case of fault when elaborating this data, it is possible to specify the type of fault (intermittent data values, no data available, spurious unreliable data values, unknown fault or other).
Each physical comprises a basic data value. Basic data value is a general abstract class which is described above. It may also have a pertinent location. A pertinent location is one location reference (refer “location” page). Generally, this location reference is predefined and here only its reference is provided. by; refer the following paragraph concerning predefined locations.
A validity can also be given basic data (as for situation records) composed of:
- Validity status which defines if the basic data has an “active” status or this status is defined according to periods of time (one can consider the third possible value “suspended” is not applicable for this kind of data element).
- One mandatory global first start time “overallStartTime”
- One optional global real end time “overallEndTime”
- Several periods, each having a start date and an end date, for which the elaborated data is active/valid, detailed with hours/days/weeks/months
- Exception periods, each having a start date and an end date, for which the elaborated data is not active/valid, detailed with hours/days/weeks/months.
The optional "overrunning" is not applicable for this kind of data element. For more details on validity, see page on "Common" data elements.
Basic data values are of one of the following types:
- Travel time data
- Traffic status
- Traffic data
- Weather data
The following paragraphs describe each of these basic data types:
Travel time data has the following specific attributes:
- Travel time trend type: decreasing, increasing, stable
- Travel time type: best, estimated, instantaneous, reconstituted
- Vehicle type for this travel time.
It may be also associated with:
- Travel time (in seconds)
- Free flow travel time
- Normally expected travel time
as well as:
- Free flow speed
Traffic status has the following specific attribute:
- Traffic trend type: traffic building up, traffic easing, traffic stable, unknown;
and can be associated with:
- Traffic status value: Impossible, congested, heavy, free flow, unknown if it differs from the reference value given for the publication.
Traffic data value (usually sent as Measured Data, but may also be sent as Elaborated Data) is defined in the paragraph on measured data. To note that individual vehicle measurements are not applicable for elaborated data. Weather data value (usually sent as Measured Data, but may also be sent as Elaborated Data) is defined in the paragraph on measured data.
Note
Traffic values and weather values are normally provided as measured data, but may be provided as elaborated data when appropriate (e.g. because values are provided by calculation).
Go back to the previous page
