# Adding new keywords

Adding kew keywords to the program should be rather easy. The general process is as follows:

## Part 1 - Receiving the input string

If an APRS messages has been received and has made it past the __primary__ input filter (this is the APRS-IS server filter setting), MPAD examines the message and extracts certain information from that message:

- who has sent me the message (```from_callsign```)
- the ```adresse``` callsign that is supposed to receive the message. This is the message recipient - usually, it's our bot process' call sign.
- the actual ```message```
- ```message number``` if present in the message
- and finally, we extract the ```format``` string of that message.

In order to enter the input parser, the following preconditions need to be met:

- ```format``` has to be ```message```. If the value is ```response```, we ignore the message.
- ```from_callsign``` has to be in the program's __second__ filter. This is not the APRS-IS server filter but the filter that is rum by MPAD itself. See [the installation instructions](INSTALLLATION.md) on how to configure this setting.
- The __incoming__ message must not be a duplicate. For each message that is sent to MPAD, a hash key is built and added to a decaying cache. If the same message is received within 5 mins, it will be detected as a duplicate request. The message will neither re-acked nor processed. If your ham radio uses message IDs for APRS messages, sending the same message text __content__ will not trigger a duplicate detection if the message numbers differ.

Finally, MPAD has a look at some corrupted APRS messages where the message ID is present but not properly transmitted. [aprslib](https://github.com/rossengeorgiev/aprs-python) does not detect these message IDs (since the message itself does not follow APRS standards). MPAD tries to extract and repair that data, if necessary.

If that previous process has found a message ID (or it has been previously identified), we will first send an acknowledgment to APRS-IS and then continue with parsing the data.

## Part 2 - Parsing the data

This is the part where we need to get our hands dirty. The program has three input parameters:

- the aprs ```message text```
- the ```from_callsign``` ("who has sent me the data")
- and finally, the API key to aprs.filter

Output of the function consists of two variables:

- a general ```success``` variable. If that one is set to ```True```, we did not encounter any errors.
- a dictionary which contains keyword-specific fields. Dependent on what you asked the program to do, these fields may or may not be populated.

That data structure comes with a couple of fields which are of universal nature. The most important ones:

- ```what``` contains the actual command. The output parser will extract this field and then calls the respective subroutines for generating the outgoing content.
- ```when``` countains the normalized reference to a day, e.g. 'monday'. ```date_offset``` already represents its numerical nature in relation to the server's date settings. For example, if the user has requested data for 'Thursday' on a Tuesday, that field's value is '2'.
- ```when_daytime``` contains a normalized reference to a certain daytime (e.g. night, evening etc)
- ```latitude``` and ```longitude```. Self-explanatory. These fields __always__ contain the user's coordinates or -if a different call sign has been queried for- that user's call sign. WX inquiries as well as any other task always build their queries on lat/lon and not on the street information. ```users_latitude``` and ```users_longitude``` are only used for the ```whereis``` command.
- ```units``` represents the units of measure that the program will use.

Parsing the data in a nutshell:

Based on certain regex commands, the existing data will be parsed. If such a regex query was successful, MPAD will extract the information (related to the associated regex) and then set the ```what``` keyword. Ultimately, two other things happen:

- the regex'ed string will be removed from the main message. As we need to continue our parser process, keeping that data might cause some unwanted effects.
- Ultimately, a general marker called ```found_my_duty_roster``` will be set. If that marker is set to ```True```, the parser knows that it has found a command that it is required to execute at a later point in time.

Ultimately at the end of the parser, the following things happen: 

- The string will be split up (separator = blank) and for each of these string words, another parser round will be issues. This is also the time where the ```when``` and ```when_daytime``` values are determined. If no 'real' ```when``` keyword has been found, the program will try to give you a wx report for the current user's position.
- All internal values will be added to that dictionary. It will then be the output generator's responsibility to turn these requests into something useful.

## Part 3 - Generating the output string

lorem ipsum
