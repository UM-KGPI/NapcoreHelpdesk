url: https://docs.datex2.eu/v3.7/recommended-profiles/rrp/srti/categoryE/
title: DATEX II packages addressed by the RRP Reduced visibility

## DATEX II packages addressed by the RRP Reduced visibility
This RRP (Recommended Reference Profile) tailors the following DATEX II model packages:
- Common – commonly used DATEX II data elements used by the tailored packages below (CEN/EN 16157-7:2018)
- Situation – the DATEX II general traffic event packages tailored for reduced visibility information (CEN/EN 16157-3:2018)
The Situation package is used for publishing event-type information on reduced visibility as a SituationPublication.
Instances of TrafficElement -> Obstruction -> EnvironmentalObstruction contain environmentalObstructionType, see Figure 1.
Figure 1 EnvironmentalObstruction
The available environmentalObstructionTypes in this RRP are:
- seriousFire
Instances of TrafficElement -> Conditions -> PoorEnvironmentConditions contain poorEnvironmentType, see Figure 2.
Figure 2 PoorEnvironmentConditions
The available poorEnvironmentTypes in this RRP are:
- visibilityReduced
- smokeHazard
- denseFog
- patchyFog
- blowingSnow
- fog
Instances of SituationPublication -> Situation -> SituationRecord contain safetyRelatedMessage, see Figure 3. The attribute safetyRelatedMessage shall be set to “true” for content in the scope of the Delegated Regulation for safety related messages.
Figure 3 SituationRecord
Instances of OperatorAction -> NetworkManagement can be a specialisation to GeneralInstructionOrMessageToRoadUsers, see Figure 4. This class shall be used to provide driving behaviour advice, where appropriate.
Figure 4 GeneralInstructionOrMessageToRoadUsers
### LocationReference profile
This RRP does not specify the location referencing methods to use. The applied method for location referencing is the choice of the specific user implementing this profile.
### PayloadPublication and SituationPublication profile
The general ‘wrapper’ classes for conveying event information are the following classes: • PayloadPublication: The generic base class for all DATEX II publications • SituationPublication: This is a container class and has no extra attributes
### Application of the RRP
The RRP can be selected in the schema creation wizard at DATEX II webtool.
- If you want to implement the RRP “as-is”, you simply click through the wizard starting with the default selection of the package in the first step.
You skip Step 2.
Choose the respective RRP in Step 3.
In step 4 you select the location referencing method(s) you are going to implement.
Then you skip the subsequent steps and choose which type of output (XML Schema or JSON Schema) you want to produce in Step 6.
These schemas will then be used by the implementer of your RRP to create the interface software, e.g. by application of data binding.
If your service manages more data elements which have not been selected in the RRP, it is possible to extend the profile in Step 5 by selecting further elements.
Go back to the previous page
