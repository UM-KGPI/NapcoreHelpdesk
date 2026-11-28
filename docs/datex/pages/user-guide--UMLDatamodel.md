url: https://docs.datex2.eu/v3.7/user-guide/UMLDatamodel/
title: Details of UML data model content

## Details of UML data model content
### Introduction
#### Objectives
This section is intended to assist readers in understanding the structure and content of the DATEX II UML model.
When reading this section, the Data Dictionary tool and documentation which groups all definitions (classes, attributes, enumeration values ...) may also be of help.
#### Prerequisite
The UML model is available on the DATEX web site in two format:
- an Enterprise Architect .eap file. The reader must have one Enterprise Architect tool version installed in order to read the model .
- The UML model may also be directly navigated on the website (html version)
The reader should be familiar with UML modelling.
The UML basic class diagram elements used in the model are presented briefly in this section.
#### Modelling methodology
For more details of the UML features used in the model please refer to the modelling methodology section.
### Logical diagrams structure
All the diagrams are in the same Namespace called "D2Payload". This namespace gathered logical diagrams in 3 namespaces:
- Common: contains all the classes, the datatypes and enumerations that are in common with all publications.
- Extension: is a placeholder for containing the elements composing possible extension.
- LocationReferencing: contains classes about locations.
and 1 package:
- PayloadPublication: containing description of publications data to be exchanged.
The logical diagram hierarchy is as the titles in the next parties. This hierarchy is synthetized in the datamodel.
Go back to the previous page
