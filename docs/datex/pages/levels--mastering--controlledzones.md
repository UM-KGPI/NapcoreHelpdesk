url: https://docs.datex2.eu/v3.7/levels/mastering/controlledzones/
title: Controlled Zone publications

## Controlled Zone publications
### The ControlledZone model
The ControlledZone model provides a structure for publishing information on controlled zones. The model reuses existing classes and datatypes from the DATEX II Common, LocationReferencing and TrafficRegulation namespaces (see Figure 1).
#### ControlledZone namespace dependencies
Figure 1 – ControlledZone Namespace relations and dependencies
#### ControlledZone model package structure
The controlled zone model is divided into packages as shown in Figure 2.
Figure 2 – ControlledZone model package structure
### The "ControlledZonePublication" package
The controlled zone model has two different entry points. On the one hand, a "ControlledZoneTable" containing one or more "ControlledZone" instances can be published using the "ControlledZoneTablePublication" class (see Figure 3). On the other hand, activation statuses of controlled zones can be published in a "CzDynamicActivationPublication" by referencing controlled zones that have already been published in a "ControlledZoneTablePublication". The class "CzActivation" is used to describe whether the activation is due to a predefined condition (class "PredefinedConditionActivation") or whether the activation is defined ad-hoc (class "NonPredefinedConditionActivation"). It is also possible to activate individual traffic regulation orders inside one "ControlledZone" (class "CzRestrictionActivation").
Figure 3 – "ControlledZonePublication" class diagram
### The "Classes" package
A "ControlledZone" may be implemented in two different ways.
Firstly, the "ControlledZone" may be implemented by a "TrafficRegulationOrder", connecting the "ControlledZone" model to the "TrafficRegulation" model (see Figure 4). Besides the traffic regulation order, a "ControlledZone" may also contain general information describing the controlled zone as well as alternative mobility options and tariff information.
As an alternative – if the controlled zone is not implemented by a traffic regulation order – the traffic regulations of a "ControlledZone" can be defined as "ControlledZoneRegulation" instances. The "ControlledZoneRegulation" class is a specialisation of the "TrafficRegulation" class from the "TrafficRegulation" model and therefore inherits all model elements from its super class (see Figure 4). Besides these, it is also composed of the following additional elements:
- "Penalty": A penalty for violating the traffic regulation defined by an amount and a description.
- "CzRegulationOperationalCharacteristics": Operational characteristics of the controlled zone regulations.
Figure 4 – "ControlledZone" class diagram
Besides the "Condition" classes that are defined in the "TrafficRegulation" model, further conditions are required for controlled zones (see Figure 5). Thus, the "ControlledZone" model adds the following classes to the "Condition" model of the "TrafficRegulation" namespace:
- "RetrofittingCondition": information on retrofitting details
- "NonCodableCondition": specification of conditions that are not covered by the condition model by giving a description of the condition and a type, which corresponds to the existing condition classes (e.g., VehicleCondition)
- "TariffCondition": an indicator whether a tariff is paid
- "PeriodCondition": conditions for time periods
This way, using either the "ControlledZoneRegulation" alone, or a combination of the "TrafficRegulation" and "ControlledZone" models, all the features of controlled zones can be represented.
Figure 5 – "ControlledZoneCondition" class diagram
Go back to the previous page
