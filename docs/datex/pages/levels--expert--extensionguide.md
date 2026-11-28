url: https://docs.datex2.eu/v3.7/levels/expert/extensionguide/
title: Sharing extensions

### Extension guide
### Introduction and guideline
#### General extension rules
DATEX II models can be extended using extensions. The following conditions must be kept in mind:
- DATEX can be extended with application specific extensions.
- Extensions are recommended to be done in the UML model. Users are strongly discouraged to manually edit the generated schemas.
- A level A model can be extended and will then become a Level B if the Level B extensions rules are respected. If not, the model will become a Level C model.
### Level B Extension rules
The following rules apply to level B extensions:
- a Level B extension is an extension that preserves interoperability between Level A and Level B.
- a Level B extended client- or sever interface will have the same target namespace and version as the Level A version.
- a Level B extended client will function with a non-extended server as long as server interface and client interface have the same version number.
- a Level B extended server interface will function with a non-extended client interface as long as the interfaces have the same version number.
#### UML extension rules
The following rules are applicable to UML usage:
- extensions shall be placed in the Extension package.
- each extension shall have its own package in the Extension package either stereotyped as D2Package or D2Namespace.
- It's recommended to put new extensions in a D2Namespace, however a D2Namespace can include more then one extension.
- For a D2Namespace package, Select the newley created D2Namespace and enter values for the following tagged values
- Definition – a description of namespace
- Prefix – the prefix that should be used in the generated XSD for this namespace.
- Version – Version number (optional)
Below is an example of an extension called MyLevelBextension.
- When extending existing classes and enumerations, existing UML constructs from the DATEX II UML profile should be used. This is done by dragging a new class or enumeration from the resources tab, to the extension package. To indicate that a class or Enumeration is extending an existing element the D2LevelBExtension UML construct shall be used.
- All rules and constrains specified in CEN/EN 16157-1 / the Modelling methodology document shall be followed.
- It is not allowed to change anything in the Level A packages/namespaces.
#### Extending Classes
- To extend a Class, create a new Class by dragging a D2Class from the resources tab, to the extension package or a diagram in the extension package. To indicate that a class is extending an existing element, the D2LevelBExtension UML construct shall be used.
- The new Class extends an existing(Level A) class. In the following example the ExtendedPublicEvent extends the PublicEvent Class from Level A.
To new classes it’s allowed to
- Add new attributes, using existing or new data types and enumerations.
Add new relations to new or existing classes.
For D2Relation or D2LevelBExtension: click on the D2Relation or D2LevelBExtension stereotype in the DATEX UML profile tree in the “Resources” tab. Then with that still highlighted, drag between two classes in a class diagram to create a new D2Relation or D2LevelBExtension.
- For all other kinds of model element: drag the relevant stereotype from the profile onto the class diagram.
- It’s not allowed to make specializations of an extended class. (This is just to make it simple)
- It’s not allowed to extend an extension class (a class that is a specialization of a level A class using the D2LevelBExtension UML construct)
- It is not allowed to change anything in the Level A packages/namespaces.
- It is allowed to let a class in the extension package derive from classes in the non-extended part. Example of this is to create new datatypes or new datavalues.
Below is an example of a valid extension of a class extended by a new attribute(numberOfParticipants) and a relation to a new class(Address).
#### Choose an approach
When building new DATEX II models that have at least some re-use of existing DATEX II model elements, there are choices about which kinds of modelling constructs to use, and where to place them. This section offers a guide. It is designed to encourage future re-use while keeping it cost-effective, and is applicable to any DATEX II modelling, from specific project work to DATEX II TMG members creating new versions of the standardised DATEX II models.
#### Namespaces and packages
A DATEX II namespace can be considered as a unit of reuse of a model. There are a growing number of namespaces in DATEX II models; each specific application does not require every namespace, but rather a selected subset. Namespaces provide modularity in DATEX II. Model element names must be unique in a DATEX II namespace.
- Use a namespace for a functionally coherent set of constructs that would naturally work together in an implementation.
- When creating a new model for one new application, a single new namespace should normally be sufficient.
- When two or more new models are being created for new applications and find they have common new elements, additional namespaces may be created for the common parts.
- Occasionally in a large new model it may be considered that a subset of the model has additional potential for wider reuse in wider applications. If confidence in this future wider reuse is high, this subset might be factored into its own new namespace, but a caution to consider is that predictions about future software re-use are prone to becoming obsolete before they are realised, and the creation of a new namespace has a cost of complexity in implementations, so it can be better to defer such factoring decisions and refactor namespaces in a future revision when the reuse boundary is clearly known.
- Namespaces containing extensions using the “level B extension” mechanism should be placed under the Extension package.
A DATEX II package is only a grouping construct that makes the model easier to read.
- Add packages within a namespace to group related constructs where that helps comprehension of the model.
#### New publication classes
When modelling new kinds of DATEX II publications, the modeller has a choice whether to extend PayloadPublication directly, or extend its concrete subclass GenericPublication. Abstract classes cannot be the subject of DATEX II Level B extension, so the abstract PayloadPublication should be extended by regular UML specialisation, whereas the GenericPublication enables Level B extension. Using GenericPublication with Level B extension allows a very limited amount of extra interoperability – it allows receivers of the new publication to perform validation on the data content even if they do not know the schema for the new publication, but that validation only verifies that the data is a valid GenericPublication object, which is not much of an advantage. Unless there is a desire to support this limited feature (or some other limited generic processing of a GenericPublication) it is recommended to specialise PayloadPublication directly.
Such a direct specialisation means that by DATEX II methodology rules this model is considered a “Level C extension.” A Level C extension should not be considered inferior to a level B extension, it’s just that a Level C extension does not aim to support instances of the extension being substituted for instances of the core DATEX II model.
Another valid but unusual option is to extend another concrete publication class, giving a variant with extra information in new attributes or associations of the new publication. There is benefit in using Level B extension in that case, to allow instances of the new publication to be processed by a wider set of implementations.
#### Extending existing classes
Say within the details of a publication model a modeller wants to reuse an existing class in an existing namespace but with added features (great!).
If a modeller is already creating a Level B extension, because of a need for instances of the extension to be valid instances of the core DATEX II model, then regular specialisation relationships across the boundary between the core DATEX II model and the extension are prohibited by DATEX II methodology rules. All specialisation relationships across this boundary must be << D2LevelBExtension>>.
If a modeller is trying to create an entirely new kind of publication in a new namespace, the best approach depends on whether the extended class is very specific to a new purpose or is considered just as widely useful as the original class.
- If the extended class is clearly specific to the new purpose – place the new class in the new namespace and use regular UML specialisation rather than <<D2LevelBExtension>>.
Note
However, if the extended class is specific where the parent class is general, that may be a hint to consider whether a composition relationship may be be more appropriate than a generalisation/specialisation relationship in the first place. Valid cases of regular UML specialisation across a namespace boundary include new publications that specialise PayloadPublication.
- If the extended class is considered useful not just for the new model but wider purposes, use a <<D2LevelBExtension>> relationship which allows the new class to be used in other publications anywhere that the original class can be used, with DATEX II Level B interoperability preserved.
New level B extended classes should be placed under the Extension package of DATEX II. (If this new class is shared with the community, it might be selected for promotion as an “approved extension” of DATEX II and its features merged into the original class in the next major revision of DATEX II.)
New classes under the Extension package should be given a namespace whose name should be chosen carefully. A name like “SituationExtension”, although it has the advantage of signalling an intention to extend the Situation namespace, has the disadvantage that multiple projects could choose the same name, and then the models cannot easily be used together in the same implementation. Furthermore the DATEX II TMG may use that kind of name in minor releases of the DATEX II model, to signal that these concepts will be promoted to the original class in the next major release, so for other purposes this kind of namespace name should be avoided.
#### New model elements with wider re-use potential
When creating a new kind of publication in a new namespace, there may be new classes, enumerations or datatypes created that are considered more generally useful for a wider range of applications.
- If the likelihood of future wider re-use seems very high, these may be separated out into a namespace to allow reuse without dependency on the rest of the new publication (see namespace guidelines above).
- Otherwise these re-usable elements should be placed alongside the more specific elements in the namespace for the new publication. Refactoring of re-used elements can be performed later if it becomes needed.
### XSD extension rules
The following rules are implemented by the tool and defined by the methodology document. They are described here for those that are interested.
- the tool shall name the schema DATEXIISchema_[X]_[Namespace].xsd. Where X is the version of the UML model(modelBaseVersion tagged value) and Namespace is the name of the package stereotyped as namespace from the UML model.
- the namespace for the Level A schema should be set to http://datex2.eu/schema/[X]/[Namespace]. Where X is the version of the UML model(modelBaseVersion tagged value) and Namespace is the name of the package stereotyped as namespace from the UML model.
- extensions are generated in their own namespace and schema file separate from the other DATEX II namespaces and schema files. The tool shall resolve relations and imports of required schemas.
- when generating the Schema all complexTypes get an extra element [classname]Extension of the type ExtensionsType which is defined as follows
<xs:complexType name="_ExtensionsType"> <xs:sequence> <xs:any namespace="##any" processContents="lax" minOccurs="0" maxOccurs="unbounded"/> </xs:sequence> </xs:complexType>
This means that every class can be extended with anything and, if extended, it's known where the extension can be found.
- when the tool finds an extension class, by looking for the D2LevelBExtension construct, it shall generate a type that looks like:
<xsd:complexType name="_MyClassExtensionsType"> <xsd:sequence> <xsd:element name = "myClass" type ="Namespace:MyClass" minOccurs="0"> <xs:any namespace="##other" processContents="lax" minOccurs="0 maxOccurs="unbounded"/> </xsd:any> </xsd:sequence> </xsd:complexType>
Note
_[ClassName]ExtensionsType will be used as type on [Classname]Extension element instead of _ExtensionsType.
- if a class has two extensions, both of them will be added in list in the _[ClassName]ExtensionsType complexType. This means that a non extended client knows that there are some extensions points but does not care what they are. We still have a strict validation of the core part of the schema.
- when the tool finds an extended enumeration, by looking for the D2LevelBExtension construct, it should generate a new type that looks like:
<xs:simpleType name="_"EnumerationNameFromUMLModel"ExtensionType"> <xs:restriction base="xs:string"> <xs:enumeration value=NameOfLiteralFromExtension /> ... </xs:restriction> </xs:simpleType>
- if in a level B model one or more level B extensions exist for a DATEX II enumeration, the literals specified in all these extensions are collected in one type described above.
- this new type will be used as the type for the attribute _extendedValue in the definition of the enumeration (replace type="xs:string")
<xs:complexType name="_"EnumerationNameFromUMLModel> <xs:simpleContent> <xs:extension base=Namespace:EnumerationNameFromUMLModel> <xs:attribute name="_extendedValue" type="xs:string" /> </xs:extension> </xs:simpleContent> </xs:complexType>
- an enumeration value "_extended" is automatically generated for all "D2Enumeration" classes in support of compatible extensions.
Note
The solution allows a Level A instance to validate against any Level b extended model/schema as long as the modelBaseVersion is the same. An extended Level B instance can be validated against any Level A schema as long as the modelBaseVersion is the same.
#### Known limitations
There are two known limitations.
- An extended level B instance cannot validate against another extended level B Schema.
- It's not possible to sensibly extend abstract classes from Level A, due to the fact that the D2LevelBExtension mechanism does not provide real polymorphism. Hence, the extension could not be instantiated. To solve this limitation for SituationRecord and Publication classes in Level A, two concrete hook classes have been created; GenericPublicaiton and GenericSituationRecord. Use this to derive new types of Publications and SituationRecords.
#### Validation
The next image gives an overview of situation where successful validation is possible.
V[X] means Version of the interface where 1 and 2 is the version number. A means a Level A model / schema / interface B1, B2 means a Level B model / schema / interface. But they are different extensions. The arrows show between which interfaces successful validation can be performed. If there is no arrow between two interfaces then successful validation cannot be done
### Level C Extension rules
The following rules apply to level C extensions:
- a Level C extension is an extension that has no interoperability between Level A and Level C.
- a Level C extended client- or sever interface will not have the same namespace as Level A.
- a Level C extended client shall function with a server that has implemented the same level C extension.
- a Level C server interface shall function with a client that has implemented the same level C extension.
#### UML extension rules
The following rules are applicable to UML usage:
- a Level C extension can in principle change and modify anything of the D2Logical model Level A part. But it's recommended that the rules below which are similar to Level B extensions are followed.
- extensions should be placed in the Extension package.
- each extension should have its own package in the Extension package.
- it's only recommended to extend existing classes with new attributes and compositions. This is done by adding a new class, to the extension package. The new class is a specialization of an existing(Level A) class. This is done by using the ordinary UML Generalization construct.
- as compatibility is not preserved with Level A anything can in theory be changed in Level A part. A change will be detected by the tool and the model will be a Level C model.
- all rules and constrains specified in CEN/EN 16157-1 / the Modelling methodology document shall be followed.
- it's not recommended to change anything in the Level A packages / namespaces.
- the tool shall check compliance with level A and B when loading a model(XMI). If it detects that something has been changed in level A part in a non Level B valid way the tool shall classify the model as a level C model.
#### XSD extension rules
To make sure the namespace name and the schema name is not the same for Level C and Level A and B the beginning of the names are read from the configuration file. The schema name will begin with LevelC and the namespace will begin with http://levelC/schema. These two values can be changed in the configuration file.
### Importing and exporting extensions
Importing and exporting extensions are preferable done with XMI. In EA you highlight the package in the project Tree and choose import / export and the either "import package from XMI file" or "export package from XMI file".
Import dialog looks like this
Select the file and press Import. | The export dialog looks like this.
Choose file name and make sure the selections and versions of XMI is as above.Press Export.
## Sharing extensions
Extensions in XMI format can easily be shared, because it's just a file. If you have an extension that is used by more then one, please share this extension on the website www.datex2.eu. There is a extensions directory where you can upload your extension (XMI, UML model, XSD and documentation). Known extensions can be candidates for inclusion in future versions of DATEX.
Go back to the previous page
