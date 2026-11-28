url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/mmtis/ls2b-availability-publicly-accessible-charging-and-refueling-stations/napdelivery/
title: NAP Delivery scenario's

## NAP Delivery scenario's
### Delivery scenario's NAP as registry only
In this scenario the data delivery is direct between each operator and service provider. Each //TODO
#### Functional responsibilities and dataflows
\ | CPO | DataPortal | ServiceProvider
Publish OCPI convert DATEX II aggregate datasets
x x
x
System functions required in the Dataportal to support this scenario
### Delivery scenario's with NAP as data-portal
#### Operators providing DATEX II merging done by SP
#### Functional responsibilities and dataflows
\ | CPO | DataPortal | ServiceProvider
Publish OCPI convert DATEX II aggregate datasets
x
x
x
#### Required Actions in the Dataportal to support this scenario
Action 0: preparations
- Take inventory whether available data meets IDACs requirements
- If applicable: assess whether data fullfills national requirements
- Create DATEX II profile if national obligations require additional datafields in DATEX II
- Define mapping of incoming information elements to DATEX II in case of available additional information.
- Define validation rules for consistency between static and dynamic dataflows.
- Develop the conversion tooling.
Action 1: set up the datachain
- Registration of credentials for accessing CPO data-source among which:
- datatype (location or status)
- delivery type (push or pull)
- update interval
- Define endpoint per CPO
- Provide endpoint-information per CPO to be registered in meta data catalogue
Action 2 Run the datachain
- receive data according to set parameters
- validate consistency between actual and dynamic datasets in line with the consistency checks defined in Action 0 step 5
- convert data according to the mapping defined in Action 0 step 4.
- Provide access credentials to service providers
- Monitor timeliness of delivery
#### Operators providing DATEX II merging done by dataportal
#### Functional responsibilities
\ | CPO | DataPortal | ServiceProvider
Publish OCPI convert DATEX II aggregate datasets
x x
x
#### Required Actions in the Dataportal to support this scenario
Action 0: preparations
- Take inventory whether available data meets IDACs requirements
- If applicable: assess whether data fulfills national requirements
- Create DATEX II profile if national obligations require additional data fields in DATEX II
- Define mapping of incoming information elements to DATEX II in case of available additional information.
- Define validation rules for consistency between static and dynamic dataflows.
- Develop the aggregation tooling.
Action 1: set up the datachain
- Registration of credentials for accessing CPO data-source among which:
- datatype (location or status)
- delivery type (push or pull)
- update interval
- Define endpoint for aggregated data-sources at NAP
- Provide endpoint-information of the NAP dataportal, including the information of data available per CPO to be registered in meta data catalogue
Action 2 Run the datachain
- receive data according to set parameters
- validate consistency between actual and dynamic datasets in line with the consistency checks defined in Action 0 step 5
- aggregate data to one endpoint.
- Provide access credentials to service providers
- Monitor timeliness of delivery
#### Operators providing OCPI merging and conversion done by dataportal
#### Functional responsibilities
\ | CPO | DataPortal | ServiceProvider
Publish OCPI convert DATEX II aggregate datasets
x
x x
#### Required Actions in the Dataportal to support this scenario
Action 0: preparations
- Take inventory whether available data meets IDACs requirements
- If applicable: assess whether data fullfills national requirements
- Create DATEX II profile if national obligations require additional datafields in DATEX II
- Define mapping of incoming information elements to DATEX II in case of available additional information.
- Define validation rules for consistency between static and dynamic dataflows.
- Develop the conversion tooling.
- Develop aggregation tooling
Action 1: set up the datachain
- Registration of credentials for accessing CPO data-source among which:
- datatype (location or status)
- delivery type (push or pull)
- update interval
- Define endpoint for aggregated data-sources at NAP
- Provide endpoint-information of the NAP dataportal, including the information of data available per CPO to be registered in meta data catalogue
Action 2 Run the datachain
- receive data according to set parameters
- validate consistency between actual and dynamic datasets in line with the consistency checks defined in Action 0 step 5
- convert data according to the mapping defined in Action 0 step 4.
- aggregate incoming data to one endpoint
- Provide access credentials to service providers
- Monitor timeliness of delivery
#### Hybrid dataprovision by operators merging and conversion done by dataportal
#### Functional responsibilities
\ | CPO | DataPortal | ServiceProvider
Publish OCPI convert DATEX II aggregate datasets
x x
x x
#### Required Actions in the Dataportal to support this scenario
Action 0: preparations
- Take inventory whether available data meets IDACs requirements
- If applicable: assess whether data fullfills national requirements
- Create DATEX II profile if national obligations require additional datafields in DATEX II
- Define mapping of incoming information elements to DATEX II in case of available additional information.
- Define validation rules for consistency between static and dynamic dataflows.
- Develop the conversion tooling.
- Develop the aggregation tooling, capable of receiving both native DATEX II from CPO's and internally converted datasets
Action 1: set up the datachain
- Registration of credentials for accessing CPO data-source among which:
- datatype (location or status)
- delivery type (push or pull)
- update interval
- Define endpoint for aggregated data-sources at NAP
- Provide endpoint-information of the NAP dataportal, including the information of data available per CPO to be registered in meta data catalogue
Action 2 Run the datachain
- receive data according to set parameters
- validate consistency between actual and dynamic datasets in line with the consistency checks defined in Action 0 step 5
- convert OCPI data according to the mapping defined in Action 0 step 4.'
- Aggregate native DATEX II provided data with converted datasets and publish
- Provide access credentials to service providers
- Monitor timeliness of delivery
Go back to the previous page
