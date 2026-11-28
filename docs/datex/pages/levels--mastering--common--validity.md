url: https://docs.datex2.eu/v3.7/levels/mastering/common/validity/
title: Validity package

## Validity package
The package “Validity” shall comprise a sub-model for defining the temporal validity of a situation element (for instance described in a “SituationRecord” instance), or the impact of such a situation element, where validity in this context means the time period in which the real world event, activity, action or impact being described actually occurs or is predicted to occur (see the following figure).
Click image to zoom
### Semantics of the Validity package
The temporal validity of a situation element (for example defined by a “SituationRecord”) or its impact can be very simple with just overall start and end times, or complex having several valid and invalid periods within a period defined by overall start and end times. The temporal validity may also be temporarily suspended or active regardless of the validity time specification (i.e. the validity time specification is temporarily overridden).
#### Validity class
The "Validity" class shall allow a supplier to identify whether the temporal validity specified in the remainder of the package is currently overridden and whether the validity period is overrunning that previously stated.
Attribute “validityStatus” shall specify whether the temporal validity is specified by the remainder of this package or not. If not, it shall be specified as being “active” (i.e. temporarily valid regardless of the validity time specification in the remainder of this package) or “suspended” (i.e. temporarily invalid regardless of the validity time specification in the remainder of this package).
Attribute “overrunning” may be used to specify whether the validity period is overrunning its expectedduration as defined in previous versions of the publication, or even in current version.
#### OverallPeriod class
The “OverallPeriod” class shall be used to specify the bounding start and end times of the validity period, within which there may be any number of valid and invalid (exception) periods. There shall be at least an overall start time specified here.
#### Period class
The “Period” class may be used to specify either a single valid or invalid (exception) period or a set of repeating valid or invalid periods within a specified period. Hence each period shall be specified as either a single time period, or as a number of recurring time periods within a single time period.
There may be any number of these valid and invalid (exception) periods within the overall validity period. The overall validity period defined in the “OverallPeriod” class by the “startOfPeriod” and “endOfPeriod” attributes shall strictly bound (i.e. override) any periods defined in this class.
Note that where an invalid (exception) period overlaps (intersects) a valid period the validity shall be regarded as invalid.
#### DayWeekMonth class
The “DayWeekMonth” class may be used to allow recurring periods to be specified in terms of days of the week and months of the year. The recurring periods are defined by the intersection of each of these values (see also note below).
This class may be specialised by the class "CalendarWeekWithinMonth" to allow recurring periods to be specified in terms of the calendar week(s) of the month or may be specialised by "InstanceOfDayWithinMonth" to allow recurring periods to be specified in terms of instance(s) of the specified weekday within a month.
This class shall be used with an association that has a role name of “recurringDayWeekMonthPeriod” identifying that it is used for specifying recurring periods.
Attribute “applicableDay” may be used to identify in which day of the week the period resides. Note that where this recurring period is specified in conjunction with a “TimePeriodOfDay” (via the role name “recurringTimePeriodOfDay”) and that specifies a period which spans midnight then this “applicableDay” value relates to the start time of that period.
Attribute “applicableMonth” may be used to identify in which month of the year the period resides.
Note
Within each instance of this class, specific enumerated values can only be used once for all attributes. E.g. applicableMonth can only contain “january” once. A combination of applicableDay “monday” and “tuesday” and applicableMonth “may” and “june” results in a data set of all Mondays and Tuesday in May and June.
#### CalendarWeekWithinMonth class
The "CalendarWeekWithinMonth" class may be used to allow recurring periods to be specified in terms of the calendar week(s) of the month.
Note
By default, the WeekofMonth is calculated as follows: The calendar week commences on a Monday (as per ISO 8601). The first week of a month is the calendar week containing the first of the month. Several days of . 20the first week of the month may occur in the previous calendar month. The last week of the month contains the last day of the month in question.
#### InstanceOfDayWithinMonth class
The "InstanceOfDayWithinMonth" class may be used to allow recurring periods to be specified in terms of instance(s) of the specified weekday within a month.
When using this class, at least one "applicableDay" must be specified in class "DayWeekMonth".
#### TimePeriodOfDay class
The “TimePeriodOfDay” class may be used to allow recurring periods to be specified in terms of start and end time within a day. The recurring periods are defined by the intersection of each of these values.
This class shall be used with an association that has a role name of “recurringTimePeriodOfDay” identifying that it is used for specifying recurring periods.
#### SpecialDay class
The “SpecialDay” class may be used to allow recurring periods to be specified in terms of special days. It is also possible to specialise this class with the "PublicHoliday" class.
This class shall be used with an association that has a role name of “recurringSpecialDay” identifying that it is used for specifying recurring periods.
The special day shall be defined using an enumeration and optional an associated event. It is possible to attach a named area to the "SpecialDay" class.
Attribute "intersectionWithApplicableDays" specifies, whether the intersection or union of days is defined.
#### NamedArea class
The "NamedArea" class shall be an abstract hook class to hook in a model for a named area.
#### PublicHoliday class
The “PublicHoliday” class may be used to specialise the "SpecialDay" class representing a public holiday.
Go back to the previous page
