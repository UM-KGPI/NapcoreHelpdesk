url: https://docs.datex2.eu/v3.7/levels/mastering/location/namedarea/
title: NamedArea (Area location)

## NamedArea (Area location)
link to the model
This section describes the "NamedArea" referencing system.
### NamedArea Package
This package supplies classes and attributes to the definition of an area-typed location only using names. It is pictured including the relationships between the classes in Figure 23.
An area defined by names only is a specific case of area location. It is defined by a name and/or in terms of known boundaries, such as country or county boundaries or allocated control area of a particular authority.
It is also inherited from the class of the same name (Common::Classes::Validity::NamedArea) defined in EN 16157-7.
To instanciate such a class it is necessary to provide:
- the country code,
- the area name (in one or several language)
- and the type of named area.
Two other classes are inherited from NamedArea:
- when using codes according to ISO 3166-2 that defines codes for identifying the principal subdivisions (e.g. provinces or states) of all countries coded in EN ISO 3166-1 (class “IsoNamedArea”). The “subdivisionType” attribute is defined according to this ISO standard.
- when using codes according to the NUTS classification (for Nomenclature of Units for Territorial Statistics, (class “NutsNamedArea”)) set up by the European Union (Regulation (EC) no 1059/2003 of 26 May 2003). This classification of administrative territories includes the three NUTS levels and also for below the two level of local administrative units (LAU) formerly named NUTS-4 and NUTS-5. The “nutsCodeType” attribute is defined according to the corresponding regulation.
The following table gives indications on the contents of the various common attributes used by the classes related to the NamedArea location.
NamedArea_dataDictionary
Go back to the previous page
