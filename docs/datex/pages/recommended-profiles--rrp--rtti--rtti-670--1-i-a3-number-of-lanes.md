url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/rtti/rtti-670/1-i-a3-number-of-lanes/
title: DATEX&nbsp;II packages addressed by the RRP The types of data on infrastructure

## DATEX II packages addressed by the RRP The types of data on infrastructure
### Road network links and their physical attributes
#### Number of Lanes
The reference profile defines the minimum required information to indicate the number of lanes for road network links.
This information may be limited to regular driving lanes, or it may be extended to include additional road surface components (e.g. shoulders, medians, or auxiliary lanes). When extended, the profile should clarify which components are usable for vehicular traffic and specify their contribution to the directional traffic capacity. This ensures clarity for traffic management and related applications.
Note: As specified in ETSI TS 102 894-2, driving lanes are counted from the inner edge of the roadway, excluding the hard shoulder.
For further reference, see the ETSI Technical Specification 102 894-2 v2.3.1.
#### DATEXII Impact class
Imformation on the number of lanes is modelled as part of the DATEX II PayloadPublication package and provided via the Impact class. The Impact class can be used to indicate what influence is on (the use of/or road users on) the road.
The following image shows the contents of the Impact class as a whole.
Specification of the number of lanes is done using the fields:
- numberOfLanesResctricted: Number of lanes to which the restriction applies
- numberOfOperationalLanes: Number of lanes available to traffic
Go back to the previous page
