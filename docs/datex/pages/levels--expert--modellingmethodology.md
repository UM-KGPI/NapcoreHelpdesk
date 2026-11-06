url: https://docs.datex2.eu/v3.7/levels/expert/modellingmethodology/
title: Modelling methodology

## Modelling methodology
This section of the DATEX II document portal describes the basic methodology underlying the DATEX II content model. It is aiming at those readers that intend to start modelling themselves in DATEX II (e.g. to create a DATEX II extension) and who need to understand the basic rules that govern DATEX II content models. Readers of the sections addressing the Platform Independent Model should be familiar with the Unified Modelling Language UML. Readers also aiming to read and understand the XML schema encoding also need a good understanding of the XML Schema Definition standard.
### Introduction
#### Normative references
The following documents, in whole or in part, are normatively referenced in this specification and are indispensable for its application. For dated references, only the edition cited applies. For undated references, the latest edition of the referenced document (including any amendments) applies.
ISO/IEC 19505-1:2012, Information technology — Object Management Group Unified Modeling Language (OMG UML) — Part 1: Infrastructure
ISO/IEC 19508:2014, Information technology -- Object Management Group Meta Object Facility (MOF) Core
ISO/IEC 14977:1996, Information technology — Syntactic metalanguage — Extended BNF
#### Terms and definitions
For the purposes of this specification, the following terms and definitions apply.
Terms and definitions adapted from ISO/IEC 19505-1:2012
Note
Definitions have been adapted to meet the particular use of UML within this specification.
- Association: semantic relationship between classes
- Attribute: named slot within a class that describes a range of values that instances of the class may hold
- Class: description of a set of objects that share the same attributes, relationships, and semantics
Composition: an association between two classes, where one class is a composite and the other is a part
Note
This characteristic is expressed in UML with an attribute named "isComposite" on the part end of the Association being set to "true".
Dependency: implementation or functioning of one or more elements that requires the presence of one or more other elements
- Enumeration: data type whose range is a list of predefined values, called enumeration literals
- Enumeration literal: element of the value space of an enumeration data type
- Generalization: taxonomic relationship between a more general element and a more specific element
Multiplicity: range of integers specifying the allowable cardinalities for an instantiation of an element
Note
The upper bound of the range cannot be below the lower bound. The lower bound must be a nonnegative integer. The upper bound must be a nonnegative integer or the special value unlimited, which indicates there is no upper bound on the range.
Package: grouping of model elements
UML profile: mechanism that allows metaclasses from existing metamodels to be extended to adapt them for different purposes
Note
The term profile within the term UML profile has a different meaning than the term profile defined in the definition of the term "Profile".
Stereotype: concept provides a way of branding (classifying) model elements so that they behave in some respects as if they were instances of new virtual metamodel constructs
Other terms and definitions
For the purposes of this specification, the following terms and definitions apply.
- binary (association): association that connects exactly two classes.
- extension: a set of data model elements not in the Level A model and following the Level B extension rules of DATEX II
- Globally Unique Identifier – GUID: Identifier that is unique in space and time, i.e. no other object will ever have the same identifier at any other place and at any time.
Lower Camel Case – LCC: description of the practice of concatenating compound phrases without whitespace in between where phrases are delimited by upper case letters.
Note
Lower Camel Case describes the case where the initial letter is lower case, e.g. as in lowerCamelCase.
Model Element: generic term for any construct of metadata used within to specify a particular aspect or element of this model.
Platform Independent Model – PIM: model of aspects of an information system (e.g. the data model) that is independent of any technical platform used to implement the model.
Note
Concrete implementations can be derived from the platform independent model by platform specific models or mappings.
Platform Specific Model – PSM: model of aspects of an information system (e.g. the data model) that is linked to a specific technological platform (e.g. a specific programming language or data transfer syntax).
Publication: traffic related information or associated management information created at a specific point in time that can be exchanged via a DATEX II interface.
Note
The “PayloadPublication” class is the top level root class for DATEX II Level A.
Upper Camel Case – UCC: description of the practice of concatenating compound phrases without whitespace in between where phrases are delimited by upper case letters.
Note
Upper Camel Case describes the case where the initial is upper case, e.g. as in UpperCamelCase.
Unique Resource Identifier/Locator – URI/URL: identifier is character string of well defined structure used to uniquely identify a resource. If that string is actually pointing at a resource accessible via the Internet, it is called a Unique Resource Locator.
eXtensible Markup Language – XML: set of rules for encoding electronic documents defined by the World Wide Web Consortium W3C.
Note
Although developed for documents, it is today widely used for data exchange in general, usually in conjunction with an XML Schema Definition.
XML Metadata Interchange – XMI: XML based specification for the interoperable exchange of metadata.
Note
It is today most commonly used to exchange UML models between UML tools. XMI is specified in ISO/IEC 19508:2014.
XML Schema Definition – XSD: formal description of the allowed content of an XML document that claims compliance to the schema.
Note
XML Schema Definitions allow for formal validation of syntactical compliance of instance documents.
Extension: an enlarged model incorporating new elements
- Profile: a selection of possible, optional elements
- Superclass: a generalisation class containing elements a class shares with other classes
- Namespace: an identifier that specifies a set of unique names
- Facet: defining aspect of a value space
Symbols and abbreviations
GUID | Globally Unique identifier
PIM | Platform Independent Model
UCC | Upper Camel Case
UML | Unified Modeling Language
W3C | Unified Modeling Language
### General conventions and requirements
#### Metamodelling
The DATEX II data modelling methodology uses the Unified Modelling Language (UML), version 2 as specified in ISO/IEC 19505-1:2012. More accurately the release 2.4.1 of UML 2 is used.
UML provides a vast set of modelling elements that are not all used for DATEX II data modelling. In fact, DATEX II uses a fairly small UML profile, based on the following metaclasses from the Core::Basic and Core:Constructs packages specified in ISO/IEC 19505-1:2012:
- Association (stereotypes: D2Relation)
- Attribute (stereotypes: D2Attribute, D2Literal)
- Class (stereotypes: D2Class, D2Identifiable, D2VersionedIdentifiable, D2ModelRoot, ExternalClass)
- DataType (stereotypes: D2Datatype, ExternalType)
- Enumeration (stereotype: D2Enumeration)
- Generalization (some of them having the stereotype: D2LevelBExtension)
- Package (stereotypes: D2Package, D2Namespace, ExternalNamespace)
DATEX II specifies metadata for the metaclasses in a UML profile with stereotypes which are assigned to the metaclasses, as listed above.
Simple types that may be assigned to attributes are defined as datatypes or enumerations.
Complex types (data structures) are defined as classes, with potential substructures connected via a composition.
Generalization between classes is allowed, but multiple inheritance is prohibited, i.e. each class shall have either zero or one superclass.
Classes, datatypes and enumerations may be structured in namespace packages, which define a namespace for their contained classes, datatypes, enumerations and sub-packages. They may also be structured simply in packages, which have no further semantics in DATEX II, they simply serve to structure DATEX II models and make them more accessible.
Namespaces, classes and datatypes also have an option to refer to an external namespace, class or datatype. The stereotypes defined for this purpose contain only the metadata required to refer to the external entity. The specification of such external model elements is entirely out of the scope of this specification.
Further to that, additional properties have been defined in this section to govern the platform specific mapping to XML schema definitions. Other property sets may be added to generate an alternative platform specific model. Models that claim to comply with this specification may use these UML elements but shall comply with all provisions regarding the use of these elements.
For readers not familiar with using UML or its graphical notations there is plenty of introductory material available to learn about UML in general and we would like to refer the reader to these resources for further study (e.g. to 1 or 2). It should be noted that this specification uses only the default graphical representation of all UML elements used.
Note that no provisions are made regarding the existence and use of other UML elements. Thus, compliant models may use these other elements, but they have no defined semantics in the framework of DATEX II.
The stereotypes of the DATEX II UML profile related to the platform independent model have defined properties which are used in subsequent sections to specify metamodel aspects. The allocation of which properties are used by which stereotypes is depicted in the diagrams in section Platform independent model rules. Further to that, additional properties have been defined to govern the platform specific mapping to XML schema definitions. Note that the following list of properties constitutes the list of properties governed by this specification. Other properties may exist but are not governed by this specification and have no semantics in the DATEX II specifications.
#### DATEX II stereotype properties
Properties for the Platform Independent Model are:
- definition: a clear, comprehensible and unambiguous definition of the modelled concept
- description: a general textual reference and explanation of an external specification that is included in a DATEX II model by using either classes with stereotype "ExternalNamespace", "ExternalType" and/or "ExternalClass".
- extensionName: the name of an extension if the model is extended
- extensionVersion: the version of an extension if the model is extended
- modelBaseVersion: the number of the major component of a version number, e.g. "n" in case of version number "n.m"
- namespaceUri: a Universal Resource Identifier that uniquely identifed an external namespace
- order: allows determining the order in which multiple metaclasses shall occur in a serialised structure of a container
- profileName: the name of a profile if the model is a profile
- profileVersion: the version of a profile if the model is a profile
- regulatoryContext: a description of any relevant regulatory context that governs the creation or the structure of a metaclass, if applicable
- version: the full version number of the associated metaclass
Properties for the Platform Specific Model are:
- facets: the value of this property shall be a valid content for the restriction element of an XML schema simple type definition of a type restriction of the XML schema type that a DATEX II metaclass is mapped to
- prefix: a unique prefix used to represent a namespace in an XML Schema mapping
- rootElement: the indication to generate a top level element in the schema with the class as type, using the property value as element name
- schemaAttribute: if this property is set to "yes", an attribute with simple type (datatype or enumeration) from the platform independent model will be mapped to an XML attribute, if the property is empty or has any other value, it will be mapped to an XML element
- schemaLocation: A URL that points to an external XML schema that will be imported into the DATEX II schema
- schemaName: if this property is non-empty, its value will be used in the mapping of the metaclass instead of the metaclass' own "name" attribute or any name following any of the naming conventions provided in subsequent sections of this specification
- schemaType: this property is used to name a XML Schema simple type that a DATEX II datatype is mapped to (ref. Requirements for mapping to XML schema definitions)
- schemaTypeInclude: a reference to an externally specified XML schema type to be used as a mapping for this metaclass (ref. Requirements for mapping to XML schema definition)
- targetClass: for attributes referring to other classes (i.e. classes with stereotype "D2Identifiable" or "D2VersionedIdentifiable"), this attributes depicts the name of the other class and is used to create a typed reference.
### Naming conventions
All names used in DATEX II UML models shall comply with the following rule set.
The following UML constructs used in this specification may have a name that is used by the DATEX II metamodel: Attribute, Class, DataType, Enumeration, Package, Property. This name is specified via a "name" metaattribute from that metaclass. If such a name metaattribute is provided, it shall begin with a letter, followed by none or more letters or digits. A name is case sensitive. In formal terms, a DATEX II name shall comply with the following definition using Extended Backus Naur Form as of ISO/IEC 14977:1996.
name ::= letter , { letter | digit }
letter ::= "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" | "M" | "N" | "O" | "P" | "Q" | "R" | "S" | "T" | "U" | "V" | "W" | "X" | "Y" | "Z" | "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t" | "u" | "v" | "w" | "x" | "y" | "z"
digit ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
The names of the instances of the following UML metaclasses shall be in Upper Camel Case notation, i.e. they shall start with an upper case letter ('A' to 'Z'), they shall consist of one or more logical components, and each component itself shall again begin with an upper case letter (Example: Component1Component2Component3): Class, DataType, Enumeration, Package
The names of the instances of the following UML metaclasses shall be in Lower Camel Case notation, i.e. they shall start with a lower case letter ('a' to 'z'), they shall consist of one or more logical components, and each component starting with the second component shall begin with an upper case letter (Example: component1Component2Component3): Attribute, Property
In all DATEX II names, acronyms should be avoided, but in cases where they are used, their capitalization shall be modified to comply with the provisions in subsections 0 and 3.
Note
In some parts of this specification, default names are defined by turning names of other constructs from Upper Camel Case to Lower Camel Case. This transformation is strictly defined as turning only the first character from upper case to lower case. Example: a proper class name may be "ANameExample". If referred by another class via a composition without role name and qualifier, the XML schema encoding of the enclosing class will contain an attribute that will implicitly be named "aNameExample".
The names of the following DATEX II UML constructs shall be unique in their namespace: Class, DataType, Enumeration
### Platform independent model rules
#### General
The DATEX II modelling methodology implies a certain structure of a UML model that seeks to claim compliance with this specification. This subsection states the requirements that UML models shall comply with in terms of constraints on the use of certain UML constructs. Note that no statements are made concerning other UML constructs, i.e. models that contain other UML constructs may still claim DATEX II compliance, as long as all requirements for the named UML constructs are met.
The provisions in this subsection address the particular requirements for the platform independent model, i.e. they do not address requirements for mapping DATEX II models to specific transfer syntax for exchange of data. Such requirements are dealt with in later subsections of this specification.
Attributes of the base UML metaclasses, that are shown in Figure 1-8 but are not described in the corresponding parts, have no semantics in this specification, since they are tool related build-in metaclass properties.
#### Requirements on associations
The following figure depicts the stereotype "D2Relation" defined for DATEX II associations (in this case associations with Association.memberEnd.isComposite = true; this is why DATEX II associations are depicted as "Composition").
- DATEX II models may contain UML Core::Constructs::Association with two memberEnd instances (i.e. binary association) where one memberEnd.isComposite attribute set to "true". Such binary compositions may have a "D2Relation" stereotype from the "UML Profile for DATEX II" assigned to it. Binary compositions with this stereotype assigned are called "DATEX II relations" for brevity in the rest of this specification.
- DATEX II models may contain UML Core::Constructs::Association that have no "D2Relation" stereotype or have other stereotypes assigned. Associations without "D2Relation" stereotype assigned and other stereotypes on associations are not governed by this specification and have no semantics in the DATEX II specifications.
- If the "name" metaattribute of a DATEX II relation is empty, the default assumption is a name constructed from the name of the connected memberEnd UML Class, with its first character turned to lower case.
- If the multiplicity of a DATEX II relations memberEnd is not explicitly specified, the default value for Multiplicity.lower as well as for Multiplicity.upper is "1".
- The "order" property of a DATEX II relation shall be a non-negative Integer and shall be different from any other value of any other DATEX II relation that is connected to the same UML Class (i.e. all associations adjacent to a composite class shall have distinct order values).
- If two or more UML Associations connect the same UML Classes, they shall have non-empty "definition" properties.
- UML Associations may have a "qualifier" UML Property.
#### Requirements on attributes
The figure below depicts the stereotype "D2Attribute" defined for DATEX II attributes.
- Attributes of DATEX II classes may have a "D2Attribute" stereotype assigned. Such attributes are called "DATEX II attributes" for brevity in the rest of this specification.
- DATEX II models may contain attributes that have no "D2Attribute” stereotype or have other stereotypes assigned. Attributes without "D2Attribute” stereotype assigned and other stereotypes on attributes are not governed by this specification, i.e. they have no semantics in the context of the DATEX II specifications.
- The type of a DATEX II attribute shall be a UML DataType with stereotype "D2Datatype" (Note that built-in UML types are not allowed) or "ExternalType", or it shall be a UML Enumeration with stereotype "D2Enumeration". If the assigned type is either "Reference" or "VersionedReference”, the "D2Attribute” stereotype may have a non-empty "targetClass" property, which shall provide a name of a DATEX II class that has an "D2Identifiable” or "D2VersionedIdentifiable” stereotype assigned, respectively.
- The "definition" property of a DATEX II attribute shall not be empty and shall contain a clear, comprehensible and unambiguous definition of the modelled concept.
- Any DATEX II attribute shall have a non-empty "order” property. This order shall be a non-negative integer and all order values of such properties of the DATEX II attributes of the same DATEX II class shall be unique within this class.
- DATEX II attributes - as all UML attributes - inherit a "lower" and an "upper" attribute from UML Core::Basic::MultiplicityElement. In case multiplicity attributes are not provided explicitly, a default value of "1" is used.
#### Requirements on classes
The figure below depicts the stereotype "D2Class" defined in general for DATEX II classes. It also contains special stereotypes for classes that shall create a top level element ("D2ModelRoot") and for classes that have a unique identity ("D2Identifiable") which can optionally also have an iterative life cycle ("D2VersionedIdentifiable"). The last stereotype "ExternalClass" is used to describe classes that are imported from other namespaces and can thus be used in the model.
- DATEX II models may use UML Core::Basic::Class. Such classes may have a "D2Class", "D2ModelRoot", "D2Identifiable", "D2VersionedIdentifiable" or a "ExternalClass" stereotype from the "UML Profile for DATEX II" assigned to it. Classes with one of these stereotypes except "ExternalClass" assigned are called "DATEX II classes" for brevity in the rest of this specification.
- DATEX II classes shall not have more than one stereotype "D2Class", "D2ModelRoot", "D2Identifiable", "D2VersionedIdentifiable" or "ExternalClass" assigned
- DATEX II models may contain UML Core::Basic::Classes that have none of the following stereotypes "D2Class", "D2ModelRoot", "D2Identifiable", "D2VersionedIdentifiable” or a "ExternalClass" assigned or they may have other stereotypes assigned. Classes without "D2Class", "D2ModelRoot", "D2Identifiable", "D2VersionedIdentifiable" or a "ExternalClass" stereotype assigned and other stereotypes on classes are not governed by this specification, i.e. they have no semantics in the context of the DATEX II specifications.
- The "definition" property of a DATEX II class (except for "ExternalClass") shall not be empty and shall contain a clear, comprehensible and unambiguous definition of the class modelled.
- A UML model that claims conformance with this specification shall contain at least one class with a "D2ModelRoot” stereotype assigned to it.
- A "D2ModelRoot" DATEX II class that claims conformance with this specification shall have the "modelBaseVersion" property set to a value "3" and the "version" property set to "3.x", where x is a non-negative integer. They may have non-empty "extensionName" and "extensionVersion" properties if the model is extended, making use of rules in section Extension rules.
- DATEX II classes may be declared to be abstract, i.e. their "isAbstract" attribute may be set to "true".
- DATEX II classes (except "ExternalClass" classes) shall not have more than one superclass.
- "ExternalClass" classes shall have no superclass and no attributes and no associations. They only serve as a reference to classes imported from outside the schema generated from the model.
For all DATEX II classes, the following UML constructs shall be unique within each class:
UML Attributes "name"
- "name" values of remote Association.memberEnd UML Properties connected to the class
- "name" values of UML Classes connected via a UML Association with an empty UML Association.memberEnd.name on the connected end, where according to requirement 4 in section Requirements on associations, this name is set to the "name" of their connected UML Class, with the first letter turned to lower case.
#### Requirements on datatypes
The figure below depicts the stereotype "D2Datatype" used in general for defining DATEX II datatypes. External datatypes may also be used via declaring them using the "ExternalType" stereotype.
- DATEX II models may use UML Core::Basic::DataType. Such datatypes may have a "D2Datatype" or an "ExternalType" stereotype from the "UML Profile for DATEX II" assigned to it. Datatypes with a "D2Datatype" stereotype assigned are called "DATEX II datatypes" for brevity in the rest of this specification.
- DATEX II datatypes shall not have both stereotypes “D2Datatype” and "ExternalType" assigned.
- DATEX II models may contain UML Core::Basic::DataType that have no “D2Datatype” or "ExternalType" stereotype assigned or they may have other stereotypes assigned. Datatypes without “D2Datatype” or "ExternalType" stereotype assigned and other stereotypes on datatypes are not governed by this specification, i.e. they have no semantics in the context of the DATEX II specifications.
- DATEX II datatypes with an "ExternalType" stereotype shall be defined inside packages that have an "ExternalNamespace" stereotype assigned or that have an ancestor with that stereotype, i.e. either they are defined directly inside an "ExternalNamespace" package or in packages defined in the package hierarchy below such a package.
- The "definition" property of a "D2Datatype" DATEX II datatype shall not be empty and shall contain a clear, comprehensible and unambiguous definition of the datatype modelled.
Note
The DATEX II PIM does not contain a formal specification of a datatype (e.g. lexical space, value range, etc,). All required information needed to properly implement the concept intended with a datatype in any specific transfer syntax model shall be clearly specified in the definition.
#### Requirements on enumerations
The figure below depicts the stereotype "D2Enumeration" defined for DATEX II enumerations.
- DATEX II models may use UML Core::Basic::Enumeration. Such enumerations may have a "D2Enumeration" stereotype from the "UML Profile for DATEX II" assigned to it. Enumerations with this stereotype assigned are called "DATEX II enumerations" for brevity in the rest of this specification.
- DATEX II models may contain UML Core::Basic::Enumeration that have no "D2Enumeration" stereotype or have other stereotypes assigned. Enumerations without "D2Enumeration" stereotype assigned and other stereotypes on enumerations are not governed by this specification, i.e. they have no semantics in the context of the DATEX II specifications.
- The "definition" property of a DATEX II enumeration shall not be empty and shall contain a clear, comprehensible and unambiguous definition of the enumeration modelled.
#### Requirements on generalizations
The figure below depicts the stereotype "D2LevelBExtension" defined for DATEX II extensions. This type of generalization can be used to depict level B extensions of classes (generalization from a D2Class in a level B extension namespace to a D2Class in the core model) or enumerations (generalization from a D2Enumeration in a level B extension namespace to a D2Enumeration in the core model).
Note
Not all generalisations have to have the stereotype "D2LevelBExtension".
- DATEX II generalizations may have a "D2LevelBExtension" stereotype assigned.
#### Requirements on literals
The figure below depicts the stereotype "D2Literal" defined for the literals of DATEX II enumerations.
- Literals of DATEX II enumerations may have a "D2Literal" stereotype assigned. Such attributes are called "DATEX II literals" for brevity in the rest of this specifcation.
- DATEX II models may contain literals that have no "D2Literal" stereotype or have other stereotypes assigned. Literals without “D2Literal” stereotype assigned and other stereotypes on literals are not governed by this specification, i.e. they have no semantics in the context of the DATEX II specifications.
- The "definition" property of a DATEX II literal shall not be empty and shall contain a clear, comprehensible and unambiguous definition of the modelled concept.
- Any DATEX II literal shall have a non-empty "order" property. This order shall be a non-negative integer and all order values of such properties of the DATEX II literals of the same DATEX II enumeration shall be unique within this enumeration.
#### Requirements on packages
The figure below depicts the stereotypes "D2Namespace" and "D2Package" defined for the DATEX II packages (with or without defining a namespace for the contained metaclasses). "ExternalNamespace" packages are used to declare classes or datatypes which are imported from an external namespace.
- DATEX II models may use UML Core::Basic::Package. Such packages may have a "D2Namespace", "D2Package" or "ExternalNamespace" stereotype from the "UML Profile for DATEX II" assigned to it. Packages with one of these stereotypes assigned are called "DATEX II packages" for brevity in the rest of this specification.
- DATEX II packages shall not have more than one stereotype "D2Namespace", "D2Package" or "ExternalNamespace" assigned.
- DATEX II models may contain UML Core::Basic::Package that have neither of "D2Namespace", "D2Package" or "ExternalNamespace" assigned or they may have other stereotypes assigned. Packages without "D2Namespace", "D2Package" or "ExternalNamespace" stereotype assigned and other stereotypes on packages are not governed by this specification, i.e. they have no semantics in the context of the DATEX II specifications.
- "ExternalNamespace" packages may contain only "ExternalClass" and "ExternalType" metaclass definitions.
- The values of the "name" UML Property shall be unique for all DATEX II packages with "D2Namespace" stereotype assigned.
### Extension rules
#### General
DATEX II models enable application specific extensions. These extensions may implement innovative concepts, and while they may happily reuse data types, enumerations, components and even identifiable entities from an existing model, they cannot seek any type of system level interoperability with systems being implemented without being cognizant of this particular extension. Such extensions are denoted as level C extensions.
In other scenarios, extensions may only seek to add some limited amount of application specific business logic whilst at the same time requiring backward compatibility with an existing model. "Compatibility" here means system level interoperability, e.g. for systems exchanging XML messages a valid instance of an extended model shall always be also a valid instance for the core model. This level of interoperability is in DATEX II denoted as level B extension. The levels' names actually indicate a compatibility hierarchy where the top level (maximum compatibility) is denoted as level A, where both interacting systems use an identical model which is pre-defined in other parts of this specification, without any extensions.
#### Numbered list of requirements
A model that is conforming to this specification may be extended. Extensions may either seek compatibility to an existing model (denoted 'core model' in this section), or they may create a new model not compatible to any previous model, but nevertheless using the methodology provided within this specification and – potentially – reusing classes taken from other, existing models.
Note
A compatible extension is denoted within the DATEX II specification as a level B extension. Non compatible extensions are denoted as level C extensions.
All extensions shall fully comply with all other rules presented so far in this specification.
- An extended model shall provide extension name and version number in two UML Properties called "extensionName" and "extensionVersion" on the "D2ModelRoot" UML Stereotype of a root level element that shall be usable in conjunction with extended elements.
- Extensions that add new "D2ModelRoot" classes are always level C extensions. Extensions that do not add new "D2ModelRoot" classes may be level B or level C extensions, depending on whether they fulfil the level B rules provided in this section.
- DATEX II classes belonging to a level B extension shall not become superclasses of classes in the core model, i.e. UML generalizations from a DATEX II class from the core model to a DATEX II class in the extension shall not be added to the model.
- DATEX II classes belonging to the core model may become superclasses of DATEX II classes in a level B extension, i.e. UML generalizations from a DATEX II class from a level B extension to a DATEX II class in the core model may be added to the model. Such generalizations shall have a "D2LevelBExtension" stereotype from the "UML Profile for DATEX II" assigned to it. It is important to note that generalizations without the “D2LevelBExtension” stereotype are not allowed from a level B extension to the core model due to the support of polymorphism in DATEXII, which would lead potentially to instances that do not validate against level A. Where needed, workarounds have to be found using the DATEX II composition mechanism.
- "D2Relation" compositions between DATEX II classes in an extension and DATEX II classes in the core model may be added to a level B extended model if they have a core model class on the ‘element’ side (i.e. the side without the diamond) and an extension class on their other end. Thus, existing classes from the core model may become components from containers in the level B extension model (class reuse), but classes from the level B extensions shall not become components of existing containers in the core model.
- DATEX II enumerations belonging to a level B extension shall not become superclasses of enumerations in the core model, i.e. UML generalizations from a DATEX II enumeration from the core model to a DATEX II enumerations in the extension shall not be added to the model.
DATEX II enumerations belonging to the core model may become superclasses of DATEX II enumerations in a level B extension, i.e. UML Generalizations from a DATEX II enumeration from a level B extension to a DATEX II enumerations in the core model may be added to the model. Such generalizations shall have a "D2LevelBExtension" stereotype from the "UML Profile for DATEX II" assigned to it.
Note
Multiple level B extensions of one core model enumerations may exist.
The "order" properties of all literals of an enumeration and all its extensions shall be unique
- DATEX II datatypes belonging to a level B extension shall not become superclasses of datatypes in the core model, i.e. UML generalizations from a DATEX II datatype from the core model to a DATEX II datatype in the extension shall not be added to the model.
- DATEX II datatypes belonging to the core model may become superclasses of DATEX II datatypes in a level B extension, i.e. UML Generalizations from a DATEX II datatype from a level B extension to a DATEX II datatype in the core model may be added to the model.
- UML generalizations with a "D2LevelBExtension" stereotype from the "UML Profile for DATEX II" assigned to them shall not be used in any situation other than those specified in requirements 6, 9, and 12.
- UML Datatypes and UML Enumerations of the core model may be reused in level B extensions.
### XML Schema Definition Mapping
#### General
The constructs of the UML profile for a platform independent model presented in the main sections of this specification – complemented by additional metadata for a platform specific model – govern the mapping of DATEX II models to XML Schema Definitions (XSD – see 3 and 4). This section describes how the normative schemas used in all further parts of this specification are actually created from a UML model conform to the previous sections of this specification.
The XSD mapping is basically covered by a small set of general rules, which are then amended / extended by further detailed mechanisms that handle specific cases. These rules are described in the rest of this normative section.
#### Platform specific model rules for XML with XML schema definition
#### General
A model that needs to be mapped to XML Schema Definition shall fulfil additional requirements on top of those specified in the previous sections of this specification. These additional requirements are captured in this annex. Conformant models fulfilling these requirements can be mapped to a corresponding XML Schema Definition according to the mapping described in subsequent subsections.
#### Requirements for mapping to XML schema definition
- UML Datatypes with a "D2Datatype" or "ExternalType" UML Stereotype assigned may have a non-empty "schemaType" property. "D2Datatype" datatypes may have a non-empty "schemaTypeInclude" UML TaggedValue. Both properties may also be empty.
- "D2Datatype" datatypes shall not have a non-empty "schemaType" and "schemaTypeInclude" property at the same time.
The value of a "schemaType" property shall be an XML Schema Definition built-in simple type, i.e. it shall follow the following production rule:
schema-type ::= "duration" , "dateTime" , "time" , "date" , "gYearMonth" , "gYear" , "gMonthDay" , "gDay" , "gMonth" , "boolean" , "base64Binary" , "hexBinary" , "float" , "double" , "anyURI" , "QName" , "NOTATION" , "string" , "decimal" , "normalizedString" , "token" , "language" , "Name" , "NMTOKEN" , "NCName" , "NMTOKENS" , "ID" , "IDREF" , "IDREFS" , "ENTITY" , "ENTITIES" , "integer" , "nonPositiveInteger" , "long" , "nonNegativeInteger" , "negativeInteger" , "int" , "unsignedLong" , "positiveInteger" , "short" , "unsignedInt" , "byte" , "unsignedShort" , "unsignedByte”
"D2Datatype" datatypes that have both an empty "schemaType" and "schemaTypeInclude" property themselves shall have an ancestor class (i.e. a direct UML Generalization, UML Generalization of its UML Generalization, etc.) that has either a non-empty "schemaType" or "schemaTypeInclude" property.
- The value of a "schemaTypeInclude" property shall be a URI that uniquely denotes an XML schema type definition for a type of the same name as the UML class that the "schemaTypeInclude" UML TaggedValue is assigned to.
- Classes whose "schemaTypeInclude" property points to a definition of a complex type for the name of the UML Class shall not have specializations.
- UML Datatypes with a "D2Datatype" UML Stereotype assigned may have a "facets" property, but only if they are mapped to an XML schema simple type. The value of this property shall be a valid content for the restriction element of an XML schema simple type definition of a type restriction of the XML schema type the UML Class is mapped to. The mapping type defines which facets are allowed according to the XML Schema specifications.
- Attributes of DATEX II Classes may have a non-empty "schemaAttribute" property, which may have a value of either "yes" or "no", but only if their type is mapped to an XML schema simple type and if their multiplicity is either "0..1" or "1..1".
- Attributes of DATEX II Classes may have a non-empty "schemaName" property.
Extending the uniqueness requirements for all DATEX II Classes, the following UML constructs shall be unique within each class:
UML Attributes "name"
- "name" values of remote Association.memberEnd UML Properties connected to the class
- "name" values of UML Classes connected via a UML Association with an empty UML Association.memberEnd.name on the connected end, where according to 7.2.4, this name is set to the "name" of their connected UML Class, with the first letter turned to lower case. – plus
Values of "schemaName" properties of attributes of this UML Class
Note
This means that none of the listed names or "schemaName" values shall be lexically equal.
Every DATEX II model shall have at least one "D2Namespace" UML package called "Common".
#### Mapping the PSM to XML schema definition
#### General
The following classes describe how the constructs of a DATEX II compliant UML model (i.e. a UML model compliant with the previous sections of this specification) can be mapped to XML Schema (XSD).
#### Mapping of "D2Datatype" and "ExternalType"
- "D2Datatype" types are in principle mapped to XSD type definitions of the same name as the type. Exceptions – i.e. cases where a “D2Datatype” type is mapped to something else – do exist and are described below. The value of the type’s "definition" metaattribute is mapped to an XML Schema "annotation" element, i.e. the principle structure looks like this:
<xs:simpleType name=TypeNameFromUMLModel> <xs:annotation> <xs:documentation> ContentOfDefinitionPropertyFromUMLModel </xs:documentation> </xs:annotation> <xs:restriction base=Namespace:RestrictionBase /> </xs:simpleType>
Note
The "annotation" element is optional and schemas may be produced with or without annotations
The value of “RestrictionBase” is determined according to the following algorithm:
- If the assigned “D2Datatype” Stereotype has got a non-empty “schemaType” Property, this value must be an XML Schema pre-defined simple type from the list provided in section Requirements for mapping to XML schema definition. The value of “RestrictionBase” is this XML Schema pre-defined type name.
If the assigned “D2Datatype” stereotype has an empty “schemaType” and an empty “schemaTypeInclude” Property, the value of “RestrictionBase” is the name of the type’s supertype. Note that the requirements in Requirements for mapping to XML schema definition ensure that any such a type does have a supertype.
The XML Schema type definitions generated by this rule may be modified by providing content in the “facets” Property. In this case, the “xs:restriction” element will be expanded and the content of the "facets" Property of the “D2Datatype” Stereotype will be inserted between the opening and the closing element:
<xs:restriction base=Namespace:RestrictionBase> ContentOfFacetsPropertyHere </xs:restriction>
Note
Note that according to Requirements for mapping to XML schema definition, the content of this UML Property shall be a valid content model for the “xs:restriction” element.
- This principle mapping rules for “D2Datatype” types may be overridden by providing a user supplied XML Schema type mapping via a sub-schema provided via the "schemaTypeInclude" UML Property – which is helpful in cases where intended type definitions do not fit into the scheme described above. The content of the user supplied type definition is not captured in the tagged value itself but at a different place that is uniquely denoted by a URI contained in the tagged values. This may be either by treating the tagged value as a URL – trying to load the content from there – or by another means that allows providing external XML Schema type definitions (e.g. as file from local disk).
- "ExternalType" types are not mapped to XSD type definitions. The corresponding datatype is assumed to be made available via an external XML schema in the namespace that they are defined in.
#### Mapping of "D2Enumeration" and "D2Literal"
"D2Enumeration" classes – and their corresponding “D2Literal” classes – are always mapped to an XML Schema simple type definition with the following structure:
<xs:simpleType name=EnumerationNameFromUMLModel> <xs:annotation> <xs:documentation> ContentOfDefinitionPropertyFromUMLModel </xs:documentation> </xs:annotation> <xs:restriction base="xs:string"> <xs:enumeration value=EnumerationLiteralNameFromUMLModel> <xs:annotation> <xs:documentation> ContentOfDefinitionPropertyFromUMLModel </xs:documentation> </xs:annotation> </xs:enumeration> ... <xs:enumeration value="_extended" /> </xs:restriction> </xs:simpleType>
The literals are mapped in the order of increasing values of their "order" property.
Generated schemas may be profiled in the sense that types may be restricted as long as each valid instance of the restricted profile is also valid for the full mapping. For enumeration classes this means that profiled schemas may omit literals.
The last enumeration value “_extended” is automatically generated for all “D2Enumeration” classes in support of compatible extensions.
A second complex type is generated for all "D2Enumeration" classes:
<xs:complexType name=_EnumerationNameFromUMLModel> <xs:simpleContent> <xs:extension base=Namespace:EnumerationNameFromUMLModel> <xs:attribute name="_extendedValue" type="xs:string" /> </xs:extension> </xs:simpleContent> </xs:complexType>
Wherever a "D2Enumeration" is given as the type of a "D2Attribute", the XML element created for this attribute uses this "_" type, which allows for setting the element content to "_extended" – in case none of the original literals is applicable – and providing the extended value via the "_extendedValue" attribute.
<xs:complexType name=ClassNameFromUMLModel> … <xs:sequence> … <xs:element name=AttributeNameFromUMLModel type=Namespace:_EnumerationNameFromUMLModel minOccurs="1" maxOccurs="1"/> … </xs:sequence> … </xs:complexType>
If in a level B model one or more level B extensions exist for a DATEX II enumeration, the literals specified in all these extensions are collected and a third enumeration type is added to the corresponding schema:
<xs:simpleType name="_"+ EnumerationNameFromUMLModel +"ExtensionType"> <xs:restriction base="xs:string"> <xs:enumeration value=NameOfLiteralFromExtension /> … </xs:restriction> </xs:simpleType>
In such a case, the type of the "extendedValue" XML attribute is changed from "xs:string" to the new extension type name =""+EnumerationNameFromUMLModel+"ExtensionType".
#### Mapping of "D2Class"
#### Mapping of “D2Class” classes that do not have a superclass
- Those “D2Class” classes that do not have a superclass are mapped in principle to the following structure:
<xs:complexType name=ClassNameFromUMLModel> <xs:annotation> <xs:documentation> ContentOfDefinitionPropertyFromUMLModel </xs:documentation> </xs:annotation> <xs:sequence> <xs:element name=NameFromUMLModel type=Namespace:TypeFromUMLModel minOccurs=LowerBound maxOccurs=UpperBound> <xs:annotation> <xs:documentation> ContentOfDefinitionPropertyFromUMLModel </xs:documentation> </xs:annotation> </xs:element> … </xs:sequence> </xs:complexType>
The name of the generated XML Schema type is taken from the "name" metaattribute of the UML Class, the content of the "xs:documentation" element is taken from the mandatory "definition" Property of the assigned Stereotype from the DATEX II UML profile.
The "xs:element" entries in the sequence are generated from:
The "ownedAttribute" UML Properties specified in the UML Class and appearing in the order of the "order" Properties of their assigned "D2Attribute" Stereotypes. TypeFromUMLModel is the name for DATEX II datatypes or "ExternalType" datatypes, or the name of a DATEX II enumeration preceded by "_".
- The UML Associations that are connected to the UML Class, again appearing in the order of the "order" UML Properties of the "D2Relation" associations connected to the "D2Class" class.
A single extension element at the very end.
Instances of the "D2Attribute" and "D2Relation" classes are mapped to the following structure:
<xs:element name=NameFromUMLModel type=Namespace:TypeFromUMLModel minOccurs=LowerBound maxOccurs=UpperBound> <xs:annotation> <xs:documentation> ContentOfDefinitionPropertyFromUMLModel </xs:documentation> </xs:annotation> </xs:element>
If lower or upper bounds are not provided, a default of "1" is assumed. Note that "xs:annotation" elements may be omitted in cases where they are not required by rules and not provided by the model (e.g. in case of a single association between two "D2Class" classes).
Generated schemas may be profiled in the sense that multiplicity ranges may be restricted as long as each valid instance of the restricted profile is also valid for the full mapping. If an upper bound is reduced to zero, the element definition may be omitted. If such an element omission makes a class declaration obsolete – i.e. the class is no longer referenced anywhere in the model – the class declaration may be omitted as well. i.e. it is may be excluded from the generated schema.
The "NameFromUMLModel" is created for "D2Attributes" according to the following hierarchy:
The value of the "schemaName" UML Property of the associated "D2Attribute" UML Stereotype, if non-empty.
The value of the "name" metaattribute of the "D2Attribute" class.
The "NameFromUMLModel" is created for "D2Relations" according to the following hierarchy:
The "name" of the "memberEnd" UML Property representing the associated UML Class, if present.
The "name" of the associated UML Class, turned to lower case (by turning the first character to lower case).
"TypeFromUMLModel" is the "name" of either the associated "D2Enumeration" or the associated "D2Datatype" for "D2Attributes".
- Generated schemas may be profiled in the sense that implementations of this DATEX II methodology may allow specifying constraining facets on "D2Attributes", thus reducing the permissible value space and consequently also the lexical space, but only if they are mapped to an XML schema simple type. The applied facets shall be a valid content for the restriction element of the respective XML schema simple type definition.
In such a case, the mapping of a "D2Attribute" as of A.3.4.1.3 is changed to:
<xs:element name=NameFromUMLModel minOccurs=LowerBound maxOccurs=UpperBound> <xs:annotation> <xs:documentation> ContentOfDefinitionPropertyFromUMLModel </xs:documentation> </xs:annotation> <xs:simpleType> <xs:restriction base=Namespace:TypeFromUMLModel> Facets </xs:restriction> </xs:simpleType> </xs:element>
- For "D2Relations" it is by default the "name" of the associated class, with a single deviation from this rule in case the UML Association metaclass directly connected to the UML Class has a "qualifier" UML Property. Note that in this particular case "LowerBound" is hardcoded to "0" and "UpperBound" is hardcoded to "unbounded"!
In this case, the type name is created as "_\<name>" where \<name> is determined according to the following hierarchy:
- The "name" of the remote "memberEnd" UML Property connected to the class – turned to UCC – if present.
- A concatenation of the "name" of the UML Class plus the “name” of the "qualifier" UML Attribute (turned to UCC) plus the "name" of the UML Class connected on the other side of the UML Association.
A definition for this type is then also added to the schema as:
<xs:complexType name="_"Name> <xs:sequence> <xs:element name=Name1 type=Name2 minOccurs="1" maxOccurs="1" /> </xs:sequence> <xs:attribute name=NameFromUMLQualifier type="xs:int" use="required" /> </xs:complexType>
where Name2 is the "name" of the UML Class connected on the other side of the UML Association, whereas Name1 is the same name turned to LCC.
- The structure of the final extension element of a "D2Class" is:
<xs:element name="_"ClassNameToLCC"Extension" type=Namespace:"_"ExtensionType minOccurs="0" />
Again, the name of this element is generated by taking the class' name and turning it to lower camel case (by turning the first character to lower case), prefixing it with "_" (to indicate a generated name) and then appending the fixed string “Extension”.
- "D2Attribute" instances may alternatively be mapped to an XML Attribute by setting a "schemaAttribute" UML Property to "yes". In this case, the structure is extended by adding "xs:attribute" elements to the content model.
<xs:complexType name=ClassNameFromUMLModel> <xs:annotation> ... </xs:annotation> <xs:sequence> ... </xs:sequence> <xs:attribute name=AttributeNameFromUMLModel type=TypeFromUMLModel use=”required” /> ... </xs:complexType>
The 'use="required"' is set if multiplicity is 1..1 and omitted in case of 0..1. Note that other multiplicities are not allowed and that the attribute's mapped type shall be an XML Schema simple type according to Requirements for mapping to XML schema definition.
#### Mapping of “D2Class” with a superclass
Those "D2Class" classes with a superclass are mapped in a similar way, just that they are mapped to extensions of their superclass:
<xs:complexType name=ClassNameFromUMLModel> <xs:annotation> <xs:documentation> ContentOfDefinitionPropertyFromUMLModel </xs:documentation> </xs:annotation> <xs:complexContent> <xs:extension base=Namespace:NameOfSuperclassFromUMLModel> <xs:sequence> ... </xs:sequence> </xs:extension> </xs:complexContent> </xs:complexType>
#### Mapping of "D2Identifiable" and "D2VersionedIdentifiable" classes
- "D2Identifiable" classes are mapped in the same way as “D2Class” classes, just that they have the following additional attribute definition.
<xs:attribute name="id" type="xs:string" use="required" />
For “D2VersionedIdentifiable” classes, a second attribute is created for the version number.
<xs:attribute name="version" type="xs:string" use="required" />
- Besides the type itself, an Identity-constraint definition will be created that ensures uniqueness of instances of the type, depending on "id" or "id"+"version", respectively. This constraint definition has the following structure (example for the versioned case including a "version" attribute)
<xs:unique name="_"Element+TargetClass"Constraint"> <xs:selector xpath=".//"TargetClass} /> <xs:field xpath="@id" /> <xs:field xpath="@version" /> </xs:unique>
- Furthermore, corresponding referencing types are created, that allow to refer to elements of these types, based on common untyped reference types ("Reference" & "VersionedReference").
<xs:complexType name="Reference"> <xs:attribute name="id" type="xs:string" use="required" /> </xs:complexType>
and
<xs:complexType name="VersionedReference"> <xs:attribute name="id" type="xs:string" use="required"/> <xs:attribute name="version" type="xs:string" use="optional" /> </xs:complexType>
Depending on whether the target type for a class TargetClass is versioned or not, the corresponding reference type looks like this
<xs:complexType name="_"TargetClass"Reference"> <xs:complexContent> <xs:extension base=Namespace:Reference> <xs:attribute name="targetClass" use="required" fixed=TargetClass /> </xs:extension> </xs:complexContent> </xs:complexType>
or like this
<xs:complexType name="_"TargetClass"VersionedReference"> <xs:complexContent> <xs:extension base=Namespace: VersionedReference> <xs:attribute name="targetClass" use="required" fixed=TargetClass /> </xs:extension> </xs:complexContent> </xs:complexType>
Note
The "version" attribute in type "VersionedReference" is optional. Hence it is possible to refer to a particular version of such a target or it is optional to refer just to the target, leaving the choice of the version at the discretion of the client receiving the data.
Note
This specification does not specify a minimum model structure. Hence, a model that claims conformance to this specification and wants to make use of the mapping for typed references specified in this section will itself have to ensure that the base classes "Reference" and "VersionedReference" are available by specifying corresponding DATEX II classes of that name in the "Common" namespace "http://datex2.eu/schema/3/Common>".
- The TargetClass is determined by setting a "targetClass" UML Property value in the "D2Attribute" UML Stereotype on the attribute that implements the reference. This value shall be provided using the appropriate namespace prefix defined in the "prefix" property in the corresponding "D2Namespace" package, where the target class is located. If “targetClass” is left empty, the corresponding generic reference type ("Reference" or "VersionedReference") is used.
#### XML elements
- At least one class in the model shall have a “D2ModelRoot” Stereotype. For each such class a top level XML element declaration is generated that has the following structure:
<xs:element name=NameFromRootELementProperty type=Namespace:ClassName />
The content of the "rootElement" UML Property is used for the "name" attribute and the class name itself is used for the "type" attribute.
- For "D2ModelRoot" the following structure is created:
<xs:attribute name="modelBaseVersion" type="xs:string" use="required" fixed="3" /> <xs:attribute name="extensionName" type="xs:string" use="optional"/> <xs:attribute name="extensionVersion" type="xs:string" use="optional"/> <xs:attribute name="profileName" type="xs:string" use="optional"/> <xs:attribute name="profileVersion" type="xs:string" use="required"/>
#### Extension mapping
- There is a special deviation from the mapping presented so far for mapping a level B extended model to XML Schema. The only difference in the mapping is for specialisations that cross the extension border, i.e. specialisations where the superclass is in the core model and the subclass is in the extension. This situation is determined by a superclass / subclass pair connected with a generalisation relationship with a UML Stereotype "D2LevelBExtension".
- In the case of extended DATEX II classes, the specialisation is not mapped to an XML extension, but the extension element of the superclass is replaced by an XML element of the same name that is of an internal complex type which consists of a sequence of XML elements that represent the – potentially – multiple classes that extend this superclass in the extensions.
This means that \<xs:element name=""SomeClassExtension type=Namespace":_ExtensionType" minOccurs="0" /> is replaced by \<xs:element name=""SomeClassExtension type=Namespace":"SomeClassExtensionType minOccurs="0" /> Where ""SomeClassExtensionType" is defined as:
<xs:complexType name="_"SomeClassExtensionType> <xs:sequence> <xs:element name=classA type=Namespace:ClassA minOccurs=”0” /> <xs:element name=classB type=Namespace:ClassB minOccurs=”0” /> ... <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/> </xs:sequence> </xs:complexType>
- In case of extended DATEX II enumerations, a new simple type _ExtendedEnumerationName-ExtensionType is created for the extension enumeration, following exactly the normal enumeration mapping and containing only the newly defined literals.
Furthermore, the following type is created:
<xs:complexType name="_"ExtendedEnumerationName> <xs:simpleContent> <xs:extension base=Namespace:ExtendedEnumerationName> <xs:attribute name="_extendedValue" type=Namespace":_"EnumerationNameExtensionType /> </xs:extension> </xs:simpleContent> </xs:complexType>
The convention to use this new type is that if the value of an attribute of that type is a literal from the supertype, the literal is just used as the XML element content:
\<ext:foo>OldLiteralFromSupertype\</ext:foo>
If the value is a literal from the new, extended enumeration, the element content is either set to an applicable literal from the supertype (which may be "_extended"), and the XML attribute "_extendedValue" is set to the new literal:
\<ext:foo _extendedValue=NewLiteralFromSubtype>LiteralFromSupertype\</ext:foo>
- Extended datatypes are mapped to XSD constructs exactly like non-extended datatypes.
#### Overall document structure and namespaces
The whole set of type and element definitions provided so far in this subsection is finally wrapped into multiple XML schema definition files, each with the following XML structure:
<?xml version="1.0" encoding="UTF-8" standalone="no"?> <xs:schema elementFormDefault="qualified" attributeFormDefault="unqualified" xmlns:Prefix=NamespaceURL version=Version targetNamespace=NamespaceURL … {further namespace declarations where required} xmlns:xs="http://www.w3.org/2001/XMLSchema"> … </xs:schema>
The full DATEX II v3 Level A specification consists of the following packages, which are defined in further parts of this specification:
- One package of common DATEX II elements called “Common” used by multiple payload publications
Note
that this package also hosts the "Reference" and "VersionedReference" type definition as specified in A.3.5.3.
- One package of DATEX II elements dealing with location referencing called "LocationReferencing"
- One empty Extension package that is prepared for inserting DATEX II extensions
- One PayloadPublication package containing multiple packages, each containing all classes that belong to a set of related payload publications and that are not already contained in the "Common" package
Each of these packages has its own namespace and is mapped to its own XML Schema Definition file ({Namespace}.xsd), with appropriate "import" statements where required (e.g. all payload packages import Common).
The target namespace of each schema is: http://datex2.eu/schema/3/{Package}
The schemas of the Level A packages ("Common", "LocationReferencing" plus all payload publication packages) further contain an XML element "version" that contains the DATEX model version 3.[n] ("n" being the minor version), taken from the "version" UML Property of the "D2ModelRoot" UML Stereotype.
#### Bibliography
Grady Booch, James Rumbaugh, Ivar Jacobson (2005). Unified Modeling Language User Guide, The, 2nd Edition. Addison-Wesley. ISBN 0-3212-6797-4. ↩
Chonoles, Michael Jesse; James A. Schardt (2003). UML 2 for Dummies. Wiley Publishing. ISBN 0-7645-2614-6. ↩
World Wide Web Consortium. XML Schema Part 1: Structures Second Edition, ed. Henry S. Thompson, David Beech, Murray Maloney, and Noah Mendelsohn. W3C Recommendation 28 October 2004 ↩
World Wide Web Consortium. XML Schema Part 2: Datatypes Second Edition, ed. Paul V. Biron, Ashok Malhotra. W3C Recommendation 28 October 2004 ↩
Go back to the previous page
