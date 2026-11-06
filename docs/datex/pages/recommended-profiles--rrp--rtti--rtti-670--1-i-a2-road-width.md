url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-670/1-i-a2-road-width/
title: DATEX&nbsp;II packages addressed by the RRP The types of data on infrastructure

## DATEX II packages addressed by the RRP The types of data on infrastructure
### Road network links and their physical attributes
#### Road width
The reference profile defines the minimum required information to indicate the width of road network links.
This includes a systematic and discretized representation of the width of maintained road surface components—such as driving lanes, hard shoulders, medians, parking areas, and the roadside.
Note: In accordance with ETSI TS 102 894-2, driving lanes are counted from the innermost edge of the roadway, excluding the hard shoulder.
This reference profile is primarily intended to support dynamic changes in road width, such as those resulting from temporary traffic measures or roadworks.
For further reference, see the ETSI Technical Specification 102 894-2 v2.3.1.
#### DATEXII Impact class
Imformation on the width of the road is modelled as part of the DATEX II PayloadPublication package and provided via the Impact class. The Impact class can be used to indicate what influence is on (the use of/or road users on) the road.
The following image shows the contents of the Impact class as a whole.
Specification of the width characteristics is done using the fields:
- residualLaneWidth: The usable total lane width (individual lanes) in meters
- residualRoadWidth: The usable total lane width (all available lanes together) in meters
Go back to the previous page
