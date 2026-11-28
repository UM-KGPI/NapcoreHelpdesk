url: https://docs.datex2.eu/v3.7/recommended-profiles/rsp/
title: Recommended Service Profiles

## Recommended Service Profiles
### EIP Recommended Service Profiles
#### Introduction
Updating all service descriptions to the state of the art, including latest developments in digitalisation and C-ITS, as well as incorporating to the harmonisation requirements knowledge gained from the collection of Best Practices and the results of the ITS Corridors and the EU EIP activities (e.g. Quality Package, NAPs, KPIs, among others) is fundamental, in order to provide guidance to the ITS Community that is up-to-date, comprehensive and complete in all aspects has been a goal of .
Making the information easier to reach and easier to understand and assimilate was another goal of the planned update, eliminating redundancies and merging all previously separate documents into a complete for harmonized ITS core service deployment in Europe.
This page is the result of the joint effort between the EU EIP and the DATEX II PSA to create Recommende Service Profiles for ITS services described in the for harmonized ITS core service deployment in Europe. The Recommended Service Profiles are available here and provided free of charge. The ITS service descriptions refer to the corresponding profiles.
All ITS applications process digital data, some of them process data that is input from other systems and some produce data that needs to be sent out to other systems. This introduction describes the data sharing context of the ITS services in a technology agnostic way. These requirements reflect the regulatory context as well as the technical conditions at the time when this text was created. In subsequent parts of the document, the current technical implementation options for the interfaces will be described, based on mature technologies available for operational roll-out and also based on current relevant regulation. Note that other technical options are currently considered in the context of R&I projects, but these are not on a level of maturity yet for everyday operation. The structure for describing the data sharing context of the ITS services described in the Reference Handbook is depicted in Figure 1. The centre of the diagram represents the ITS service and its system boundary. The architecture overview is used as a symbol for this. On the service boundary – depicted by a dotted line – we see three interfaces.
Figure 1 Data sharing architecture
Interface IF1 realises a backbone interface that allows the service to communicate with other backbone systems. These may be systems of other road operators, systems of service providers for vehicle fleets or end-user apps operated inside the vehicle, or other systems. The interfaces IF2 and IF3 describe direct communication links with individual vehicles or other devices used inside the vehicle e.g. smartphones, where IF2 is the interface to convey information from the service into the vehicles, and IF3 is the reverse interface for in-vehicle data being input into the service. This opens up two ways of sharing data with vehicles, via the immediate links (sometimes referred to as ‘short leg’) or via a backbone interface to the backbone of a fleet operator who has himself a link into the vehicles belonging to this fleet (‘long leg’). As stated above, the description so far was technology agnostic. In order to do actual implementations of the service, concrete technologies have to be selected to implement these interfaces. The requirements presented in this document will provide the required choices regarding technologies and data profiles. The requirements with regard to IF1 are mainly governed by the Delegated Regulations published by the European Commission in the scope of the ITS Directive. These stipulate the use of National Access points and the application of DATEX II standard (CEN 16157 series) for data encoding.
The Reference Handbook ITS Services that have an RSP defined can be accessed below.
EU EIP A2
Reference Handbook
#### Documentation
For now only documentation on the 'Road Weather Information' is available. All other documentation will follow shortly. You can get the Recommended Service Profiles at the DATEX II webtool.
Forecast and Realtime Event Information
Traffic Condition and Travel Time Information
Speed Limit Information
Road Weather Information
Multi-Modal Traveller Information
Dynamic Lane Management
Variable Speed Limits
Ramp Metering
Hardshoulder Running
Incident Warning and Management
HGV Overtaking Ban
Traffic Management for Corridors and Networks
Intelligent and Secure Truck Parking
### IDACS Recommended Service Profiles
#### Introduction
In the course of the Programme Support Action (PSA) “Data collection related to recharging/refuelling points for alternative fuels and the unique identification codes related to e-Mobility actors” that was subsequently given the name IDACS, or “ID and Data Collection for Sustainable fuels in Europe”, the 15 member states of the consortium mandatorily have to collect data related to alternative fuels infrastructures, namely electric charging points and hydrogen refuelling stations (HRS) as part of activity 2. Other alternative fuels, such as CNG, LNG, LPG and highly-blended biofuels can be covered optionally.
As data collection mandatorily has to take place via the National Access Points (NAP) as defined in directive 2010/40/EU on the framework for the deployment of Intelligent Transport Systems in the field of road transport and for interfaces with other modes of transport, it is the aim of these profiles to give guidance on how this can be achieved.
#### Documentation
The DATEX II Profiles made available for exchange of this information are the IDACS Recommended Service Profiles
### UVARBox
#### Introduction
UVARBox digitized five types of UVARs for which five profiles are available as RSP in the . The five UVAR types are: - low emission zones - limited traffic zones - pedestrian zones - congestion charging - parking zones
As these profiles are based on un unstable version of DATEX II Traffic Regulations users have to be aware of non-interoperable changes are expected in a stable future v3 release of TrafficRegulation and ControlledZone.
#### Documentation
Regarding the documentation of these profiles we refer to the on the .
documentation
UVARBox website
Go back to the previous page
