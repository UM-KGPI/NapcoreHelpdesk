url: https://docs.datex2.eu/v3.7/user-guide/UMLbasicelements/
title: Short description UML basic elements

## Short description UML basic elements
This section contains a short description of UML 2.0 basic elements used by DATEX II. A full definition and specification can be found in UML reference documents.
Add link to UML reference section
### Class
A class is a template for a given data element which can contain attributes. It is a rectangle divided into three compartments. The topmost compartment contains the name of the class. The middle compartment contains a list of attributes owned by that class and the bottom compartment contains a list of operations which is not shown here because operations are not used in this standard. In some diagrams, the bottom compartment of Attributes may be omitted for clarity reason. An attribute line has a specifier “+, # or –“ for the visibility (not used in this standard) a name of the attribute and after a colon a data type and in squared brackets the multiplicity which is described in aggregation hereunder.
### Specialisation
A Specialisation (i.e. Inheritance) defines a general class (super class) which properties are inherited from the derived class. In data structures that imply that the derived class has at least the same attributes as the super class and normally will define more attributes to it. Reason for using a inheritance in general is the capability of having different specialisations from one super class.
### Aggregation
The aggregation is a more explicit design element for describing attributes. It is a more strong association telling that the class on the side of the diamond “has” an instance of the aggregated class. The name of that instance is given on the left side of the connection and starts again with the “+” as specifier of visibility. On the right side the multiplicity of that instance is given as a range of the allowed count of occurrences. An aggregation does let open if the aggregated element has the same lifetime as the aggregating class. In data structures the aggregation can be a reference to another data structure or a embedded data element.
### Composition
The composition strengthens the type of aggregation in that way, that the lifetime of the composed element is the same as the composing class, i.e. the structure can be seen as a “composition”. In data structures composition is normally seen as an embedded data element.
### Dependency
The dependency is an unspecific type of relationship between two classes.
Go back to the previous page
