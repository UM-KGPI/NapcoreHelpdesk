url: https://docs.datex2.eu/v3.7/levels/expert/extensionintroduction/
title: Introduction extensions

## Introduction extensions
DATEX II models can be extended using extensions. The following conditions must be kept in mind:
- DATEX can be extended with application specific extensions.
- Extensions are recommended to be done in the UML model. Users are strongly discouraged to manually edit the generated schemas.
- A level A model can be extended and will then become a Level B if the Level B extensions rules are respected. If not, the model will become a Level C model.
### Extending Enumerations
On this level only the extending of enumerations is described. If you want to consult the whole guide click here
- To extend an enumeration, create a new enumeration by dragging a D2Enumeration from the resources tab, to the extension package or a diagram in the extension package. To indicate that an enumeration is extending an existing element, the D2LevelBExtension UML construct shall be used.
- The new enumeration extends an existing(Level A) enumeration. In the following example the ExtendedPublicEventTypeEnum extends the existing PublicEventTypeEnum from Level A.
- To new enumerations it’s allowed to add new enumeration literals.
Go back to the previous page
