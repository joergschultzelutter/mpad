# mpad - Usage and Command Syntax

## What you need to know as a program user

- The program's default __action__ is to retrieve a __wx report__ for the given address/coordinates. This assumption is valid as long as the user has not specified a keyword that tells the program to do something different. This means that you can a single datetime-related keyword like e.g. 'tomorrow' and the program will try to return the wx report for you.

- Default __date__ is always 'today'. If you omit any date-related information, 'today' will be the default value.

- Default __daytime__ is always 'full', meaning that you will get e.g. the wx report for the whole day. See the next paragraph on limitations wrt keywords and time zones.

- Although both __date__ or __daytime__ settings can be specified at all times, any provided information in this matter may be partially or fully ignored by the program, dependent on the keyword (e.g. sunrise/set and moonrise/set will ignore the __daytime__ argument)

- All __time stamps__ are __always returned in reference to the UTC time zone__. If time-specific inquiries are issued (e.g. 'give me the wx report for tomorrow afternoon'), the 'afternoon' part also abides to UTC time zone settings. Dependent on where you are located in the world, that setting might be a different experience for you. Limiting the output to UTC may or may not change in future versions of this program but in general, time zones are a mess. And taking into consideration that daylight saving times may or may not be applicable to the user's position, sticking to UTC is the safest option for now. Therefore, all times reported by the program are provided with a Zulu time qualifier, e.g. 12:03Z

- Certain action command keywords can be specified in combination with a date setting and a daytime setting, e.g. request a wx report for the next day. The respective keyword documentation settings state if the keyword can be used in conjunction with a date/daytime keyword. All restrictions wrt UTC time settings do apply - see previous paragraph.

## Commands

- [Action commands](command_keywords/action_commands.md)

- [Date settings](command_keywords/date_keywords.md)

- [Daytime settings](command_keywords/daytime_keywords.md)

## Legal mumbo-jumbo

In reference to the European Union's GDPR regulations:

- This is a hobby project. It has no commercial background whatsoever. Source files are freely accessible.

- if you intend to host this software and submit data to APRS-IS, you need to be a licensed ham radio operator.

- The main purpose of this program is to provide you (the user) with information that is based on either your own location or someone else's position data on the APRS network. 

- The position information itself is acquired from freely accessible data sources such as the APRS-IS network, aprs.fi et al. These data sources gather APRS information from ham radio users who did decide to have their position information actively submitted to the APRS network. Any of these information sources can already be used for a various user's position inquiry.

- Based on the user's submitted keyword, information such as wx reports that position data is gathered and/or transposed into human-readable location information.

- That information is then returned back to the user via APRS-IS (and subsequently via radio transmission)

- Requesting data from the program is done by sending one or multiple keywords to it. This is done by actively sending an APRS message to the program, either via ham radio or APRS-IS. All commands need to be send to the program's APRS identifier (__MPAD__). The program will neither actively monitor a user's position or trigger any automatic transmissions to a user.

- No transaction data with the exception of the following cases is stored:

  - Number of transactions in total

  - Program exceptions and/or crashes may be stored to log files for debug purposes

- If you intend to host your own instance of MPAD, you need to provide API access keys to the following services (both are usually free of charge but may come with a transaction limit):

  - aprs.fi

  - openweathermap.org

If you use this program, then you agree to these terms and conditions. Thank you.
