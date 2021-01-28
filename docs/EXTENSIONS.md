# Adding new keywords

Adding kew keywords to the program should be rather easy. The general APRS message work flow is as follows:

## Part 1 - Receiving the input string

If an APRS messages has been received and has made it past the __primary__ input filter ([see INSTALLATION](docs/INSTALLATION.md)), MPAD examines the message and extracts certain information from that message:

- who has sent me the message (```from_callsign```)
- the ```adresse``` callsign that is supposed to receive the message. This is the message recipient - usually, it's our own bot process' call sign.
- the actual ```message text```
- ```message number``` if present in the message
- and finally, we extract the ```format``` string of that APRS message.

In order to enter the input parser, the following preconditions need to be met:

- ```format``` has to be ```message```. If the value is ```response```, we ignore that APRS message.
- ```from_callsign``` has to be in the program's __second__ filter. This is not the APRS-IS server filter but the filter that is rum by MPAD itself. See [the installation instructions](INSTALLLATION.md) on how to configure this setting.
- The __incoming__ message must not be a duplicate. For each message that is sent to MPAD, a hash key is built and added to a decaying cache. If the same message is received within 5 mins, it will be detected as a duplicate request. The message will neither re-acked nor processed. If your ham radio uses message IDs for APRS messages, sending the same message text __content__ will not trigger a duplicate detection if the message numbers differ. [See the TECHNICAL_DETAILS](docs/TECHNICAL_DETAILS.md) on how the dupe check works.

Finally, MPAD has a look for some corrupted APRS messages where the message ID is present but not properly transmitted. [aprslib](https://github.com/rossengeorgiev/aprs-python) does not detect these message IDs (since the message itself does not follow APRS standards). MPAD tries to extract and repair that data, if necessary.

If that previous process has found a message ID (or it has been previously identified), we will first send an acknowledgment to APRS-IS and then continue with parsing the data.

## Part 2 - Parsing the data

This is the part where we need to get our hands dirty. Herem we try to figure out what the user wants us to do. We do not perform those actual tasks (e.g. pull the wx report) in here - these are parts of the the output generator (see next chapter)

 ```input_parser.py``` has three input parameters:

- the aprs ```message text```
- the ```from_callsign``` ("who has sent me the data")
- and finally, the API key to aprs.fi

Output of the function consists of two variables:

- a general ```success``` variable. If that one is set to ```True```, we did not encounter any errors. If the value is ```False```, the output generator will send an error message to the user
- a ```dictionary``` which contains ```key```word-specific ```values```. Dependent on what you asked the program to do, these ```values``` may or may not be populated. 

That data structure comes with a couple of fields which are of universal nature. The most important ones:

- ```what``` contains the actual command that the user wants us to execute (e.g. 'get wx data', 'get position for user xyz'). The output parser will extract this field and then calls the respective subroutines for generating the outgoing content.
- ```when``` countains the normalized reference to a day, e.g. 'monday'. ```date_offset``` already represents its numerical nature in relation to the server's date settings. For example, if the user has requested data for 'Thursday' on a Tuesday, that field's value is '2'.
- ```when_daytime``` contains a normalized reference to a certain daytime (e.g. 'night', 'evening' etc)
- ```latitude``` and ```longitude```. Self-explanatory. These fields __always__ contain the user's coordinates or -if a different call sign is to be used as position reference- that user's call sign. Ann keywords use these lat/lon coordinates as their queries' point of destination, meaning that additional information such as city name, country etc is only used for data output to the user. The additional fields ```users_latitude``` and ```users_longitude``` are only used for the ```whereis``` command - for any other keyword, they are not populated.
- ```units``` represents the units of measure that the program will use (```metric``` (default) or ```imperial```)

Parsing the data in a nutshell:

Based on keyword-specific regex commands, the existing message text will be parsed. If a regex query was successful, MPAD will extract the information (related to the associated regex) and then set the ```what``` keyword with the command that the user has requested. Afterwards, we perform a little bit of a cleanup:

- The regex'ed string will be removed from the originating APRS message. As we need to continue our parser process (so far, we've only figured out 'what' the user wants us to do; the 'when' question is still unresolved), keeping that data might cause some unwanted effects.
- Finally, a general marker called ```found_my_duty_roster``` will be set. If that marker is set to ```True```, the parser knows that it has found a 'what' command that it is required to execute at a later point in time.

The parser starts with a query for WX information, followed by CWOP/Position/Celestial keywords. The first successful regex 'wins', meaning that if you e.g. create a message where you query for wx data and celestial data, the wx data keyword wins as this is one of the first regex keyword queries in the program.

At the end of the parsing process where we have taken a look at the complete message, the following things happen: 

- The remaining APRS message text will be split up (separator = blank). For each of these string words, another parser round will be issued. This is also the time where the ```when``` and ```when_daytime``` values are determined. If no 'real' ```when``` keyword has been found, the program will try to provide you a wx report for the current user's position. This is the prgram's default fallback
- All internal values will be added to that output ```dictionary```. It will then be the output generator's responsibility to turn these requests into something useful.

## Part 3 - Generating the output string

```output_generator.py``` is responsible for generating the outgoing messages to the user. Dependent on the ```what``` keyword, the program calls the respective functions which will then do the __actual__ work (e.g. get wx report etc.). Each of these functions uses a function called ```make_pretty_aprs_messages``` in order to add the content to a ```List``` item which contains 1..n lines of ready-to-be-sent text messages. Each of these messages has a max len of 67 characters, so you won't exceed the max. APRS message length. ```make_pretty_aprs_messages``` is responsible for a couple of things:

- optional removal of non-ASCII characters from the content if the program configuration requests this ([see INSTALLATION](docs/INSTALLATION.md))
- Initially, call ```make_pretty_aprs_messages``` without a ```List``` reference and provide your string. As a result, you'll get a reference to the output ```List``` item which contains your string.

For each new string that you are going to add, ```make_pretty_aprs_messages``` checks if the len for (current existing string plus your new string) exceed 67 characters. If that is the case, a new element is genarated (which represents your current input to the function). ```make_pretty_aprs_messages``` always tries to add the content without ripping it apart (e.g. the 67th byte of a message contains "1" and the 1st byte contains "2" for a temperature reference of 12 degrees. Yes, this might result in 'bloated' APRS messages so ensure that you add your content in a proper manner (see __Testing__).

There are a few safety nets: for the unlikely event of receiving an input string of more than 67 characters, MPAD refrains from keeping the logical connection and tries to split up that string on a per-word basis. This does not rip content apart but may break the logical connection. Finally, if there should ever be a string of more than 67 characters without any blanks (Martian landing coordinates?), MPAD will break up that string into chunks of 67 bytes. MPAD does not speak Martian and neither do I. This is the 'last resort' option which should never be triggered.

Here's how to call ```make_pretty_aprs_messages```:

- Start with the process by calling ```make_pretty_aprs_messages``` without a ```List``` item reference. You'll get a reference to the ```List``` object which contains your first message.
- For message contents 2..n, pass that reference to the function in order to ensure that the next message is added to that same ```List```.
- For each new message, that you add, a separator (default: space) is added between the previous message and the new message. If you don't want that message separator to be added, you can omit it by specifying the ```add_sep``` parameter.

Once your native routine has prepared that list, there is nothing else that you need to do. If the original incoming message was sent with a message ID, MPAD will automatically add unique message IDs to each outgoing message. Finally, the(se) message(s) are sent to APRS-IS.

The output generator has only two parameters:

- the ```dictionary``` from the ```input_parser.py``` module
- the API access key to openweathermap.org

Entering the output parser ONLY happens if the input parser has found a valid ```what``` command. Otherwise, a generic error message is presented to the user.

## Testing

For a non-live test of the input parser and output generator, you can use the ```parser_test.py``` Python file which is part of this repo. Simply specify your own call sign (the one that you would send the message from) and the APRS message. Both ```input_parser.py``` and ```output_generator.py``` will be triggered and you can test if your new keyword works as designed.
