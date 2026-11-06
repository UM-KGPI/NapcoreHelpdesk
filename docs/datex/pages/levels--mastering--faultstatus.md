url: https://docs.datex2.eu/v3.7/levels/mastering/faultstatus/
title: Device status and faults

## Device status and faults
The DATEX II device status and faults model was first created by a CEN project team and published as CEN TS 27241:2019. It was then adopted by the creators of DATEX II and revised as CEN TS 16157-13 (publication expected 2024 or 2025).
It supports use cases including the system-to-system exchange of detailed device configuration and status and fault information for device asset management and maintenance.
The central concept in the model is the “Device”, which represents a logical device that delivers a service, and so is not limited to represent a specific physical piece of equipment. One “Device” can be realised by different physical objects at different points in time, for example if a faulty item installed in the field is replaced by a spare of the same type at the same location – both can fulfil the same Device object albeit one or more of its detailed properties might change as a result of the replacement.
The model allows publications that identify the Devices that exist, and publications that describe the current status of those devices i.e. their current capability to perform their intended functions, and the faults that currently exist.
The device status and faults model is contained within its own namespace “FaultAndStatus” within the PayloadPublication package of DATEX II.
To use FaultAndStatus requires the Common, CommonExtension, and LocationReferencing namespaces to be included, but it is not dependent on any other payload namespace.
Optionally, it can be used in conjunction with the Vms and/or RoadTrafficData namespaces to provide status and faults of devices defined using those models.
FaultAndStatus defines three publications: the DevicePublication, the StatusPublication and the FaultPublication. The DevicePublication identifies the devices whose dynamic status is described in the StatusPublication and FaultPublication, but it is not essential to use the DevicePublication to use the dynamic publications, because the dynamic information can be related to devices in other more specific device publications instead, like VmsPublication or MeasurementSiteTablePublication.
### DevicePublication
A DevicePublication contains Device objects, either directly or contained in one or more DeviceTable objects, identifying what Devices exist and describing their static configuration.
A DeviceTable should contain all devices for some given scope, so if a Device which was previously included in a DeviceTable is omitted from a subsequent publication of that DeviceTable, that device should be considered to no longer exist.
An example use case for the direct inclusion of Device in DevicePublication without a DeviceTable is where one device is registering itself with a system by providing its own configuration.
Both Device and DeviceTable have the <> stereotype so that they can be referenced in the FaultPublication and StatusPublication.
The location of the device must always be supplied, using PointLocation from the LocationReferencing namespace. The physical device that currently fulfils the logical device service may be identified.
Devices may be composed of Components, which are themselves Devices, and this supports as many levels of hierarchy as may be needed. For components, the typeOfDevice property will typically be “other”, with the componentType identifying the type of component.
Optionally, a hierarchy of dependency can be specified using the “dependsOn” relation. If one Device is noted to depend on another Device, the former will not be able to perform its full function if the latter is not functioning.
Two properties of Device have reusable datatypes (IpAddress and PortNumber) that would naturally be placed in the Common namespace, but since that namespace was already frozen in version 3 for backwards compatibility reasons, those types have been placed in the CommonExtension namespace.
### StatusPublication
A StatusPublication contains status information for devices, either for individual devices or for a whole device table at once.
The referencing of devices and device tables is flexible – references can point to DeviceTable or Device from a DevicePublication, or to VmsUnit objects or MeasurementSite objects from other publications.
Various kinds of status information can be provided in a Status object, including the health of the device (i.e. its ability to provide its intended service), the operational state into which the device has been placed. There is a dedicated construct for information on the power supply to the device, although more generally the status of any sub-component of a device could be given if the component has been modelled as a component device in a DevicePublication.
The status and faults models both offer optional integration with an external information catalogue using ASN.1 object identifiers. For both the overall status of a device and its operational state, an ASN.1 object identifier may be provided to identify an external catalogue entry that may have further information.
A Status object can optionally provide one or more references to Fault objects in a FaultPublication.
This relatedFault attribute uses the VersionedReference type, which means that in XML the reference attribute will have an optional “version” property, but the likely target - the DeviceFault class – is <> rather than <> so does not have a corresponding “version” property. This should cause no problem – simply omit populating the optional “version” property in instances of the relatedFault element.
### FaultPublication
At the top level, the FaultPublication has the same pattern as the StatusPublication, allowing information on individual devices or a whole table, with reference either to Devices, VmsUnits, or MeasurementSites.
For each device, any number of DeviceFault objects can be given. DeviceFault is a specialisation of the basic Fault class in the Common namespace of DATEX II.
The only mandatory attribute of a DeviceFault is the type of fault, expressed as a FaultTypeEnum. Optionally a faulty component of the device can be identified simply by a textual identity and/or the type of component (DeviceComponentEnum). If this method provides sufficient information then it is not necessary to have used the capability of DevicePublication to model components as devices themselves.
Go back to the previous page
