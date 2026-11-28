url: https://docs.datex2.eu/v3.7/levels/mastering/location/alertc/
title: Alert-C (Point, linear and area location)

## Alert-C (Point, linear and area location)
→ Adevice and Problem Location for European Road Traffic, Version C
link to the model
This section describes the ALERT-C referencing system and gives details of the contents of ALERT-C tables.
Note
An ALERT-C location is a tabular address defining a locating element belonging to this table.
Only the reference is transmitted between the Supplier and the Client. It is up to the client to look it up in the table for the descriptive elements corresponding to the referenced location using the ALERT-C code. To have a unique ALERT-C coding at the European level, the reference must comprise three elements (triplet):
- Country Code,
- Table number,
- Location number
Two distinct locations at the European level cannot have the same triplet.
Warning
Caution: the eventually not allotted codes for country table references are invalid.
It is the European standard EN ISO 14819-3 that defines the rules of constitution of the ALERT-C location tables.
This location reference system allows to define the 3 kinds of location representation.
### The "Point location" with 2 methods available in package
#### "AlertCMethod4Point" Package
This package supplies classes and attributes to the definition of a point location using the method 4 as explained in EN ISO 14819-3:2013, Annex C.
An ALERT-C point using method 4 represents a single point on the road network as defined by reference to a point in a pre-defined ALERT-C location table (class “AlertCMethod4PrimaryPointLocation”).
It shall be augmented with the non-negative distance in metres between the ALERT-C point and the actual referenced point (class “OffsetDistance”). This point is called primary point.
It also has an associated direction of traffic flow representing the direction of traffic flow along the road to which the information relates (class “AlertCDirection”).
The positive direction corresponds to the point (and segment when it exists)) order when going from the first point to the last point using positive offsets. It is named “AlertC chaining” in the picture in the example below.
The ALERT-C point location is given an ALERT-C direction using a set of predefined coded values. The attribute “alertCDirectionCoded” is used to define which offset type (i.e. negative or positive) is used to navigate in the ALERT-C location table.
The attribute “alertCAffectedDirection” specifies the driving direction(s) affected by the traffic object. A name may also be added to complete the direction definition. (attribute "alertCDirectionNamed")
Examples of AlertCMethod4Point use cases :
1 - Case of negative and aligned directions for a Point event
Example_1 of AlertCMethod4Point
2 - Case of positive and aligned directions for a Point event
Example_2 of AlertCMethod4Point
3 - Case of negative and opposite directions for a Point event
Example_3 of AlertCMethod4Point
4 - Case of positive and opposite directions for a Point event
Example_4 of AlertCMethod4Point
5 - Case of negative and both directions for a Point event
Example_5 of AlertCMethod4Point
6 - Case of positive and both directions for a Point event
Example_6 of AlertCMethod4Point
NB: To see all this examples in XML format : Download Here
#### "AlertCMethod2Point" Package
This package supplies classes and attributes to the definition of a point location using the method 2 as explained in EN ISO 14819-3:2013, Annex C.
It represents a single point on the road network defined by reference to a point in a pre-defined ALERT-C location table (class “AlertCMethod2PrimaryPointLocation”).
Else this package works as the AlertCMethod4Point package, explain above, except for the class “OffsetDistance” wich doesn't exist in the method2.
### Linear location with 3 methods available in package
#### "AlertCMethod4Linear" Package
This package “AlertCMethod4Linear” supplies classes and attributes to the definition of a linear location using the method 4 as explained in EN ISO 14819-3:2013, Annex C.
An ALERT-C linear location reference using method 4 class “AlertCMethod4Linear”) represents a linear section along a road between two points, primary and secondary, which are pre-defined in an ALERT-C location table, accompanied by distances.
The distance is defined as being the non-negative distance in metres between the ALERT-C point and the actual referenced point (class “OffsetDistance”).
Direction is FROM the secondary point (class “AlertCMethod4SecondaryPointLocation”) TO the primary point (class “AlertCMethod4PrimaryPointLocation”)
So, the secondary point is the first Alert-C point met, and located upstream of the tail of the event according to the direction of traffic impacted, and the primary point is the second Alert-C point met, and located downstream of the head of the event.
The direction of traffic flow along the road to which the information relates is given by the class “AlertCDirection”.
The attribute “alertCDirectionCoded” is used to define which offset type (I.e. negative or positive) is used to navigate in the ALERT-C location table. Therefore, this attribute determine the situation of the primary and secondary points.
- In case of a ring road, the “alertCDirectionCoded” attribute is used to remove the ambiguity how to reach the primary point from the secondary point.
The attribute “alertCAffectedDirection” specifies the driving direction(s) affected by the event.
- both: indicates that both directions of traffic flow are affected by the situation or relate to the traffic data.
- opposite: indicates that the direction of traffic flow affected by the situation or related to the traffic data is in the opposite sense to the direction in which the linear event is defined.
- aligned: indicates that the direction of traffic flow affected by the situation or related to the traffic data is in the same sense as the direction in which the linear event is defined.
A name may also be added to complete the direction definition. (attribute "alertCDirectionNamed")
Examples of AlertCMethod4Linear use cases :
1 - Case of negative and aligned directions for a Linear event
Example_1 of AlertCMethod4Linear
2 - Case of positive and aligned directions for a Linear event
Example_2 of AlertCMethod4Linear
3 - Case of negative and opposite directions for a Linear event
Example_3 of AlertCMethod4Linear
4 - Case of positive and opposite directions for a Linear event
Example_4 of AlertCMethod4Linear
5 - Case of negative and both directions for a Linear event
Example_5 of AlertCMethod4Linear
6 - Case of positive and both directions for a Linear event
Example_6 of AlertCMethod4Linear
NB: To see all this examples in XML format : Download Here
#### "AlertCMethod2Linear" Package
This package supplies classes and attributes to the definition of a linear location using the method 2 as explained in EN ISO 14819-3:2013, Annex C.
An ALERT-C linear location reference using method 2 represents a linear section along a road between two points, primary and secondary, which are pre-defined in an ALERT-C location table.
As for the point location, this package works as the AlertCMethod4Linear package, explain above, except for the class “OffsetDistance” wich doesn't exist in the method2.
#### "AlertCLinearByCode" Package
This package “AlertCLinearByCode” supplies classes and attributes to the definition of a linear location using a pre-defined ALERT-C linear location.
An ALERT-C linear location reference by code presents a linear section along a road defined by an ALERT-C code I.e. a tabular reference of linear location in an ALERT-C location table (class “AlertCLinearByCode”). It shall have an associated direction of traffic flow representing the direction of traffic flow along the road to which the information relates (class “AlertCDirection”).
The ALERT-C linear location reference is given an ALERT-C direction using a set of predefined coded values. The attribute “alertCDirectionCoded” is used to define which offset type (I.e. negative or positive) is used to navigate in the ALERT-C location table. The attribute “alertCAffectedDirection” specifies the driving direction(s) affected by the traffic object.
A name may also be added to complete the direction definition. (attribute "alertCDirectionNamed")
### Area location with 1 method available in package
#### "AlertCArea" Package
This package “AlertCArea” supplies classes and attributes to the definition of an area-typed location using a pre-defined ALERT-C area location.
It represents an area defined by reference to an area already defined in a pre-defined ALERT-C location table.
The following table gives indications on the contents of the various common attributes used by the classes related to the ALERT-C location.
AlertC_dataDictionary
Go back to the previous page
