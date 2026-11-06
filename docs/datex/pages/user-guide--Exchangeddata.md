url: https://docs.datex2.eu/v3.7/user-guide/Exchangeddata/
title: Overview of the exchanged data

## Overview of the exchanged data
### Introduction
Before diving into the UML model, this chapter presents the exchanged data. Exchanged data are made with basic elements which are available inside publications.
This presentation is a functional one, and do not present elements in the order of the UML model. Click here for datamodel and details about classes and attributes.
### Basic elements
Information exchanged with DATEX II systems is composed of different basic elements:
- Road and traffic related events (called “Traffic elements”),
- Operator actions,
- Impacts,
- Measured or elaborated data (e.g. travel times, measured traffic speed, elaborated traffic status, weather measurements…),
- Messages displayed on Variable Message Signs (VMS),
- Service information (no rest area, delays on trains…).
In addition, there are also Predefined Locations, Parking table, VMS Table and Measurement Site Table information exchanged. They are not part of the basic elements, but are required if the corresponding information in the basic elements is to be understood by a client.
#### Road and traffic related events (called "Traffic elements")
These are all events which are not initiated by the traffic operator and force him to undertake (re)actions. They are classified in 6 main categories:
- Abnormal traffic (long queues, stop and go, …),
- Accidents,
- Activities (public event, disturbance, …),
- Conditions: driving conditions related to weather (ice, snow, … ) or not (oil, …), conditions related to environment (precipitation, wind, …), …
- Obstructions:
- animal presence,
- vehicle presence,
- obstructions due to environment (avalanches, flooding, fallen trees, rock falls, …),
- obstructions due to infrastructure (fallen power cables, …),
- other obstructions including people,
- Incidents on equipments or systems (Variable message sign out of order, tunnel ventilation not working, emergency telephone not working, …).
#### Operator actions
Operator actions are classified in 4 main categories:
- Network management: road closure, alternate traffic, contraflow ...
- traffic control: rerouting, temporary limits
- Roadworks: resurfacing, salting, grass cutting ...
- Roadside assistance: vehicle repair, helicopter rescue, food delivery ...
- Sign settings: This refers to a VMS message.
#### Impacts
It contains, in particular, information on lane availability and on delays (in seconds, in time range or globally).
#### Measured or elaborated data
These sets of data can be derived from direct inputs from outstations or equipments at specific measurement sites (e.g. loop detection sites or weather stations) which are received on a regular (normally frequent) basis, or can derived on a periodic basis by the Traffic Centre from input data for specified locations:
- measured traffic values about:
- flow,
- speed,
- headway,
- concentration
- individual vehicle measurements,
- normally published as measured data, but can be derived on a periodic basis and published as elaborated data,
- traffic status:
- free flow, heavy, congested, impossible, unknown,
- normally published as elaborated data, but direct outstation derived values can be published as measured data,
- travel times:
- elaborated time, free flow time, normally expected time,
- normally published as elaborated data, but direct outstation values can be published as measured data,
- weather values:
- precipitation, wind, temperature, pollution, road surface condition and visibility,
- it can be measured, or can be derived on a periodic basis and published as elaborated data,
They can be forecast values.
#### Service information
It means information about a service which may influence the behaviour of drivers and hence the characteristics of the traffic flow, i.e.:
- transit information,
- Information about other transport means,
- For example, cancellation, or delay, on a tram, train, plane, etc. journey,
- service disruption (rest area closed, no diesel…),
- road service disruption (no patrol, emergency call out of order …).
#### VMS messages
These data sets include different possible messages according to different technologies, including textual messages, pictograms or combinations as well as allowing for full matrix VMS. They are completed by some information about equipment status and position.
### Publication of basic elements
The previous basic elements can be exchanged individually or grouped. For these exchanges, the notion of publication is used. There are 5 main publications:
- Situation publication
- For traffic elements, operator actions, impacts, or service information,
- Elaborated data publication,
- for traffic status, and for travel times,
- If relevant, for traffic values and weather values,
- Measured data publication,
- for traffic values and weather values,
- and if relevant, for traffic status, and for travel times,
- Parking Publication,
- for parking information
- VMS publication,
- for VMS messages
#### Situation publication
A situation publication can contain several different situations.
A situation represents a traffic/travel situation comprising one or more traffic/travel circumstances which are linked by one or more causal relationships and which apply to related locations. Each traffic/travel circumstance is represented by a Situation Record.
A situation record is one element of a situation. It is characterized by values at a given time, defining one version of this element. When these values change, a new version is created. One situation record can be:
- A road or traffic related event (traffic element),
- An operator action,
- A non-road event information,
and can contain:
- Impact details.
#### Elaborated data publication
This publication is used to send periodically elaborated data derived by a Traffic Centre relating to specified locations. Locations may be explicitly defined in the publication or, more simply, may be referred to by references to predefined locations which have been exchanged via the “predefined locations” publication.
#### Measured data publication
This publication is used to send periodically measured data which has been derived from equipment at specific measurement sites, where each site is identified by reference to an entry in a predefined measurement site table. The measurement site table can be exchanged via the “measurement site table” publication and provides for each site the details of its location and parameters associated with the different types of measurements that can be made at the site.
Each set of measurements from a site is ordered (i.e. indexed), where each ordered measurement might be of a different type. The order (or indexing) of these measurements for each site within the Measured Data publication must correspond with the ordered (indexed) definition of the measurement in the Measurement Site Table publication for the particular site.
#### VMS publication
This publication is used to send periodically messages elaborated by a Traffic Control Centre relating to a set of display equipments among a road network. Static VMS characteristics may be explicitly defined in the publication (for mobile VMS e.g.) or, more simply, may be referred to by references to predefined VMS installations which have already been exchanged via the “VMS table” publication.
Go back to the previous page
