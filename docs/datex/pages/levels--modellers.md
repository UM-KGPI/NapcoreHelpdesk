url: https://docs.datex2.eu/v3.7/levels/modellers/
title: Modelling Guidance

## Modelling Guidance
### Pattern use
At first glance there seems nothing at all wrong with the pattern shown in the diagram, where a class in one namespace is specialised by a class with an identical name in another namespace.
However, when DATEX II XML schema mapping rules are applied, to support DATEX II backwards-compatible extension both types acquire an identically-named property (in our example here it would be _fooExtension).
While that is a legal construct in XML Schema, and in programming languages like Java and C#, it is sometimes considered a debatable practice because it could encourage programming errors when the property is manipulated in code. An instance of B::Foo has both a B::Foo::_fooExtension property and an A::Foo::_fooExtension property. Programming language rules determine which is meant when a reference to _fooExtension is made, but programmers have sometimes made mistakes in this situation. The pattern can also cause unexpected code Java generation when using JAXB from DATEX II XML schemas. So we recommend avoiding this modelling pattern entirely – choose a different name for each class in the same inheritance tree.
### Anti-Patterns and their refactored solutions
The following paragraphs contain additional advice for creating DATEX II model, in the form of “anti-patterns” – design patterns that turn out to have more drawbacks than advantages – with corresponding preferred patterns. The criteria for inclusion here are that each anti-pattern:
- Has occurred more than once in models in CEN 16157 series (DATEX II) drafts (although the examples here are fictitious illustrations!), leading to comments and resolutions.
- Is not just a mistake that the modeller didn’t notice – the anti-pattern has been chosen intentionally because the modeller didn’t consider the drawbacks identified here.
For further guidance see also the SOLID principles, which several of the anti-patterns violate.
Anti-pattern: Class name in the plural that is intended for single instance of the concept.
Anti-pattern example: Class named “Roads” is created with the intention of representing roads, where each instance will represent a single road.
It is a practice sometimes used by database developers, who sometimes think of the class name as a table name describing the whole population of entities.
Drawbacks: This leads to unnatural code and serialised data.
Road road = new Road(“A1”);
makes more sense than:
Roads road = new Roads(“A1”);
if the class is supposed to represent one road. Similarly in that context:
<Road><name>A1</name></Road> <Road><name>B2</name></Road>
makes more sense than:
<Roads><name>A1</name></Roads> <Roads><name>B2</name></Roads>
Desirable pattern: A class name (and definition) should denote one instance of the class.
Anti-pattern: Mutual dependency of namespaces
Anti-pattern example:
For example a mutual dependency might be caused where one conceptually specific namespace (say Foo) depends on a conceptually more general namespace (say CommonThings), but where also amongst the various parts of CommonThings there is specialised use case where a CommonThing can have an associated FooThing.
Drawbacks: Having more namespaces brings more artefacts (schemas, namespaces etc) to contemplate and process. Where namespaces are independent it is a valuable advantage to be able to include or omit namespaces in a profile or software build, but where 2 namespaces are interdependent they must always be used together, so that valuable advantage is not present to compensate for the extra complexity from the extra parts.
Desirable pattern: Have coherent namespaces without mutual dependency. You can still use packages within a namespace to signal the semantic distinction if that is useful.
Desirable pattern example:
A single unified namespace may be preferable. (Imagine FooBar really is a sensible name for the unified concept, not just the arbitrary concatenation of two concepts).
Alternatively the model elements causing mutual dependency can be refactored so that the dependencies are all in one direction. Returning to the anti-pattern example with CommonThings, the CommonThing class could be factored so that there is specialisation across namespaces. the dependency from CommonThing to the Foo namespace is removed.
(These names are all placeholders; good names should represent concepts.)
In DATEX II we also have a lesser kind of dependency created by use of a Reference or VersionedReference where the target class is another namespace. This produces no visible dependency in the model, or (depending on the platform-specific mapping) the generated schemas, but may entail a dependency in application code, so care should be taken over that kind of dependency too. It comes with a cost for developers, and it may be avoidable through the solutions described above; if it is needed then it should be signposted.
Anti-pattern: Model definitions show their context as model elements.
Anti-pattern example: A class “Vms” defined as “Class representing a variable message sign”.
Drawbacks: While there is no clear right and wrong practice for definitions, we have normally followed the practice of the definition describing the subject matter concept, rather than IT concepts, and so where we describe IT concepts (and those are not the subject matter) the main drawback is a lack of consistency. We want to be able to treat the class definition as defining a subject matter term, and our convention produces clear and concise definitions which identify the kinds of objects that are represented by the model construct.
Desirable pattern: A class definition should define an instance of the class.
Desirable pattern example: A class “Vms” is defined as “Variable message sign”, or “A variable message sign”.
(The underlying principle here also suggests that the DATEX II convention of suffixing all enumerations with the word “Enum” is undesirable – “Type” would have been sufficient - but that is now a long-established precedent.)
Anti-pattern: Class name containing ‘And’ or ‘Or’.
Anti-pattern example: A class called ImpactAndDelay.
Drawbacks: A class name containing “And” or “Or” is a sign that there is a missing concept, and the model and its communicative power and conciseness could all be clarified by making that concept explicit. That isn’t always true - occasionally there is no better overall solution than accepting “And” or “Or”, but we should always try to avoid it if we can. If no common concept is apparent, then ask why these two concepts have been grouped into one, and whether they would be better separated. If there is a reason to group them, that reason may suggest a term.
Desirable pattern: A class name should explicitly and concisely identify one coherent subject matter concept being represented.
Desirable pattern example: Factor ImpactAndDelay into two classes: Impact and Delay.
Anti-pattern: Element name repeating the name of its enclosing scope
Anti-pattern example: A class in the Vms namespace, called VmsPictogram, with attributes such as vmsPictogramDescription.
Drawbacks: The scope of “Vms” is understood from the namespace, and the scope of “Pictogram” is understood from the class, so the extra words make code and data longer without any value, in fact they make it harder to quickly distinguish the meaning of different concepts.
Desirable pattern: Concise element names whose meaning is understood from their name and their context in the model.
Desirable pattern example: Class in Vms namespace called “Pictogram”, with attributes such as “description”.
Anti-pattern: Model element name with an added redundant word
Anti-pattern examples: Elements ending “Data”, “Record”, “Information”, or “Related”.
e.g. a Road namespace with a number of sub-packages, some with specific names, but one called RoadRelated because no specific name was instantly apparent.
Drawbacks: All our classes hold data, they are all records, they are all related to the subject matter concepts that they are named for, so the words are redundant. A RoadRelated package can surely not be any more related to roads than say “Parking” is related to parking. If there is a reason why the element cannot be used without the redundant suffix, that reason should suggest a better name or better factoring of the model, which communicates concepts more clearly and explicitly.
Occasionally a “record” or “information” might really be a subject matter concept, in which case the term might be used.
Desirable pattern: Choose factorings and names that identify the subject matter concepts clearly and explicitly but concisely. For a package, choose the name representing the common concept that its elements have in common, and if that is nothing then consider reallocating them to appropriate specific packages.
Anti-pattern: Structural duplication
Anti-pattern example:
Drawbacks: Models and generated code are bigger than necessary, and often (although not in the simple example shown) there is a missing concept that would clarify the model if made explicit.
Desirable pattern: Factor to avoid all duplication.
Desirable pattern example:
Anti-pattern: Optional elements with possibility for inconsistency
Anti-pattern example:
A class with multiple optional attributes, where some permutations would not make sense. In this example an instance could have a commentDateTime but no Comment.
Another example is having two or more optional attributes in the same class that can never make sense if populated at the same time.
Drawbacks: A careless implementation could populate in an inconsistent way, breaking expected invariants. This is unlikely, but the possibility for inconsistency is the sign that the design can be improved by introducing a concept that clarifies and may also allow reuse.
Desirable pattern: Factor classes to avoid possibility for inconsistency of permutations of optional attributes.
Desirable pattern example:
Anti-pattern: Base class element that makes no sense for subclass
Anti-pattern example:
Drawbacks: A careless implementation could populate in an inconsistent way, breaking expected invariants.
Desirable pattern: Factor classes to avoid possibility for inconsistency – move the attribute to the appropriate class – which might be a new class.
Desirable pattern example:
The example is rather artificial in that a more likely solution would be to not populate a ResponsibleOrganisation relation when there is none, but assuming that a need for an instance of ResponsibleOrganisation led to the Boolean attribute, the anti-pattern is removed as shown.
Anti-pattern: UML comments specify constraints that could be enforced through model structure
Anti-pattern example:
A UML comment on an attribute says that it should only be populated in certain circumstances.
Drawbacks: A careless implementation could populate in an inconsistent way, breaking expected invariants. This is unlikely, but the possibility for inconsistency is the sign that the design can be improved by introducing a concept that clarifies and may also allow reuse.
Desirable pattern: Factor classes to avoid the need for UML comments.
Desirable pattern example:
A subclass is introduced, with semantics indicating the special condition mentioned in the UML comment, and the attribute is moved to the subclass, and the UML comment is removed.
Anti-pattern: Attributes with specific formats and conventions are squeezed into plain generic types
Anti-pattern examples: Float for a money amount. NonNegativeInteger for a phone number.
Drawbacks: Not all values can be exactly represented, there may be confusion on units, and there may be missed opportunity for reuse of processing code.
Desirable pattern: Select or create appropriate specific types.
Desirable pattern examples: A money amount uses a specific type designed to represent money amount; a phone number uses a specific type designed to represent a phone number.
Anti-pattern: Base class name which can only ever describe the base class properties
Anti-pattern examples: A base class prefixed “Basic” or “General”, where subclasses are not limited to basic or general concepts.
Drawbacks: In UML and object-oriented design in general, an instance of a subclass should be considered a valid instance of its superclass. The model shown says that an instance of AdvancedRoad is a BasicRoad too, and that is probably not a true reflection of the subject matter. BasicRoad only describes the role of the class in an IT sense. Some code may be written at the superclass level, and it could confuse a reader that instances of “AdvancedRoad” are used in code which says they are “BasicRoad”.
Similarly the model says that an instance of Acme3x18FiveMetreVariableMessageSign is a GeneralDevice, which carries an implication that this specific device is general - but how can it be general if it is so specific? The modeller obviously intends simply that GeneralDevice represents the general properties of a device, but when reading code written to process GeneralDevice a reader may reasonably expect the instances to be “general devices”.
Desirable pattern: In class hierarchies, use class names that support the “is a” test.
Desirable pattern examples:
Admittedly the prefixes “Basic” and “General” have typically been used when there is some reason why the unadorned name is not possible or appropriate, but there must be another name that conveys the subject matter concept, or another refactoring that makes the appropriate name available.
Go back to the previous page
