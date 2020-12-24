# mpad - Usage and Command Syntax

## What you need to know as a progran user

- The program's default __action__ is to retrieve a __wx report__ for the given address/coordinates. This assumption is valid as long as the user has not specified a keyword that tells the program to do something different. This means that you can a single datetime-related keyword like e.g. 'tomorrow' and the program will try to return the wx report for you.

- Default __date__ is always 'today'. If you omit any date-related information, 'today' will be the default.

- Default __daytime__ is always 'full', meaning that you will get e.g. the wx report for the whole day. See the next paragraph on limitations wrt keywords and time zones.

- All __time stamps__ are returned in __UTC__ time zone settings. If time-specific inquiries are issued (e.g. 'give me the wx report for tomorrow afternoon'), the 'afternoon' part also applies to UTC time zone settings. Dependent on where you are located in the world, that setting might be a different experience for you. Limiting the output to UTC may or may not change in future versions of this program but in general, time zones are a mess. And taking into consideration that daylight saving times may or may not be applicable to the user's position, sticking to UTC is the safest option for now. Therefore, all times reported by the program come with a zulu time qualifier, e.g. 12:03Z

- Certain action command keywords can be specified in combination with a date setting and a daytime setting, e.g. request a wx report for the next day. The respective keyword documentation settings state if the keyword can be used in conjunction with a date/daytime keyword. All restrictions wrt UTC time settings do apply - see previous paragraph.

## Commands

- [Action commands](01_actions.md)

- [Date settings](02_date_settings.md)

- [Daytime settings](03_daytime_settings.md)

## The fine print

lorem ipsum