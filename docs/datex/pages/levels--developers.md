url: https://docs.datex2.eu/v3.7/levels/developers/
title: Developers' corner

## Developers' corner
### JAXB
JAXB is the technology for Java-XML Schema binding that is built into Java editions. It is easy to generate Java code from DATEX II XML schemas using JAXB, but there are a couple of details worth knowing.
The DATEX II XML Schema rules produce underscore characters in certain constructs that support backwards-compatible extension of information models. With default options, JAXB doesn’t interpret these underscores as part of the generated type names, and that produces undesirable results. To get around this, you simply set a property read by JAXB, to tell it to keep the underscores in generated names: underscoreBinding="asCharInWord".
If you use the version 3 LocationReferencing module, there is a further detail: there is an abstract class NamedArea in the Common namespace that is specialised by a concrete class NamedArea in the LocationReferencing namespace; the DATEX II schema generation rules produce a property called _namedAreaExtension in both. When directly mapped to Java, this pattern of a class defining a field with the same name as a superclass field would be legal, if debatable practice, but JAXB does not like it and doesn’t generate the code you might expect. We will avoid this pattern in future; meanwhile it’s easy to work round it, for example by specifying another JAXB property to change one of the two names. An example JAXB property file covering both these workarounds looks like this:
<jxb:bindings xmlns:jxb="http://java.sun.com/xml/ns/jaxb" jxb:version="2.0" xmlns:xs="http://www.w3.org/2001/XMLSchema"> <jxb:globalBindings underscoreBinding="asCharInWord" /> <jxb:bindings schemaLocation="DATEXII_3_LocationReferencing.xsd" node="//xs:element[@name='_namedAreaExtension']"> <jxb:property name="_locNamedAreaExtension" /> </jxb:bindings> </jxb:bindings>
### DATEX II & Linked Open Data
Go back to the previous page
