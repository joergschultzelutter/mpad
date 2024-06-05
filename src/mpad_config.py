#
# Multi-Purpose APRS Daemon: various APRS routines
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: Program configuration entries
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
import os

#
# Program version
#
mpad_version: str = "0.61"
#
###########################
# Constants, do not change#
###########################
# APRS position report: message symbol
# see also http://www.aprs.org/symbols/symbolsX.txt and aprs_communication.py
# on how this is used. Normally, you don't want to change these settings
#
aprs_table: str = "/"  # APRS symbol table (/=primary \=secondary, or overlay)
aprs_symbol: str = "?"  # APRS symbol: Server
#
# Delay settings: These sleep settings are applied for each SINGLE message that is sent out
# to APRS-IS. If the program has to send two bulletin messages, then the total run time of
# sending out those bulletins is 2 * x secs
#
# packet delay in seconds after sending data to aprs-is
packet_delay_message: float = 6.0
# packet delay after sending an acknowledgment, bulletin or beacon
packet_delay_other: float = 6.0

# Help text that the user receives as APRS messages in case he has requested help
help_text_array = [
    "See https://github.com/joergschultzelutter/mpad for command syntax",
    "Supports: Wx forecasts,position reporting,OSM category searches,",
    "repeater data lookups,CWOP reports,METAR and TAR reports,celestial",
    "calculations,satellite passes&frequency data,DAPNET messaging,",
    "radiosonde landing predictions",
]

##########################
# Configuration settings #
##########################
#
#################################
# General Program Configuration #
#################################
#
# Location of our process (Details: see aprs101.pdf see aprs101.pdf chapter 6 pg. 23)
# Ensure to honor the format settings as described in the specification, otherwise
# your package might get rejected and/or not surface on aprs.fi
# Degrees: lat: 0-90, lon: 0-180
# Minutes and Seconds: 00-60
# Bearing: latitude N or S, longitude: E or W
mpad_latitude: str = "5151.84N"  # 8 chars fixed length, ddmm.ssN
mpad_longitude: str = "00935.48E"  # 9 chars fixed length, dddmm.ssE
#
# Program alias: This is the APRS name that will be used for all outgoing messages
mpad_alias: str = "MPAD"  # Identifier for sending outgoing data to APRS-IS
#
# Altitude in *FEET* (not meters) for APRS beacon. Details: see aprs101.pdf chapter 8
mpad_beacon_altitude_ft = 824
#
# APRS "TOCALL" identifier - see http://aprs.org/aprs11/tocalls.txt
# The original MPAD instance has its own TOCALL identifier - if you clone & modify
# the program, you might request a new one for yourself via WP4APR
mpad_aprs_tocall: str = "APMPAD"  # APRS "TOCALL"
#
####################
# APRS-IS Settings #
####################
#
# APRS-IS login Server / login Port
aprsis_server_name = "euro.aprs2.net"  # our login server
aprsis_server_port = 14580  # server port
#
# APRS-IS server filter setting (This is the program's PRIMARY message filter)
# Syntax: see http://www.aprs-is.net/javAPRSFilter.aspx
# If you remove/disable this filter, MPAD will 'see' all aprs-is messages
# (the whole APRS-IS traffic)
aprsis_server_filter = "g/MPAD"  # server filter criteria for aprs.is
#
#############################
# Secondary filter settings #
#############################
#
#
# MPAD SECONDARY filter setting. This filter will be applied to those
# messages which have made it past the PRIMARY filter (from APRS-IS)
# If that secondary filter is also passed, then we will have a look
# at the user's message and try to process it
#
mpad_callsigns_to_parse = ["MPAD"]  # (additional) call sign filter
#
#############################################################
# Time-to-live settings for the decaying APRS message cache #
#############################################################
#
# The first value represents the time span for how long MPAD considers incoming
# messages as duplicates if these messages have been sent to the program
# For each processed message (regardless of its actual success state), MPAD
# is going to add a key to a decaying dictionary. That key consists of
# the user's call sign, the APRS message ID (or - if not present - 'None) and
# an md5'ed version of the message text. If another delayed or duplicate
# message is received within that specified time frame, that message is going
# to be ignored by the program
# The 2nd value represents the max. number of entries that the decaying cache
# is going to accept
#
# ttl = 60 minutes
mpad_msg_cache_time_to_live = 60 * 60
# 2160 possible entries (max. of 36 per min is possible)
mpad_msg_cache_max_entries = 2160

#
############################################
# Character encoding for outgoing messages #
############################################
#
# By default, MPAD will send out ASCII messages to its users even though UTF-8 is
# supported (see http://www.aprs.org/aprs12/utf-8.txt) for both incoming and
# outgoing messages. However, many radios such as my FTM-400XDE and the FT3DE
# are unable to cope with UTF-8 messages and don't display these messages in a
# proper way.
# If you do want MPAD to enable for OUTGOING unicode messages, then set this
# marker to True. INCOMING messages are always processed with unicode in mind.
#
# Future versions of this switch should check whether it is possible to build a
# list of supported unicode 'TOCALL' devices from the official list tocall list
# (http://www.aprs.org/aprs11/tocalls.txt). MPAD could then decide whether a
# device is unicode capable or not - and activate unicode whenever it is supported.
#
mpad_enforce_unicode_messages = False
#
# Openstreetmap 'special phrases'
# The values in this list need to match the ones in the OSM
# documentation: https://wiki.openstreetmap.org/wiki/Nominatim/Special_Phrases/EN
# Add/remove categories if necessary but ensure that the keywords' writing
# matches the one in the OSM documentation (this is case sensitive data!)
#
osm_supported_keyword_categories = [
    "aerodrome",
    "alpine_hut",
    "ambulance_station",
    "atm",
    "bakery",
    "bank",
    "butcher",
    "car_rental",
    "car_repair",
    "charging_station",
    "chemist",
    "clinic",
    "college",
    "deli",
    "dentist",
    "department_store",
    "doctor",
    "drinking_water",
    "dry_cleaning",
    "electronics",
    "fire_station",
    "fuel",
    "hairdresser",
    "hospital",
    "hostel",
    "hotel",
    "information",
    "laundry",
    "mall",
    "motorcycle",
    "optician",
    "pharmacy",
    "phone",
    "photographer",
    "police",
    "post_box",
    "post_office",
    "pub",
    "shoes",
    "subway",
    "supermarket",
    "taxi",
    "telephone",
    "tobacco",
    "toilets",
    "train_station",
    "university",
]
#
# Default user agent for accessing aprs.fi, openstreetmap et al
# Change this if you run your own MPAD instance
mpad_default_user_agent = f"multi-purpose-aprs-daemon/{mpad_version} (+https://github.com/joergschultzelutter/mpad/)"

#
# DAPNET API server and transmitter group
#
mpad_dapnet_api_server = "http://www.hampager.de:8080/calls"
mpad_dapnet_api_transmitter_group = "all"

#
# SMTP server and port
#
mpad_smtp_server_address = "smtp.gmail.com"
mpad_smtp_server_port = 465

#
# IMAP server and port
#
mpad_imap_server_address = "imap.gmail.com"
mpad_imap_server_port = 993
mpad_imap_mail_retention_max_days = 1  # Delete mails after x days (0 = disable)
mpad_imap_mailbox_name = '"[Gmail]/Sent Mail"'

#
# Directory for MPAD data files (e.g. TLE data, repeater data files et al)
#
mpad_data_directory = "data_files"
mpad_root_directory = os.path.abspath(os.getcwd())

#
# Deutscher Wetterdienst (DWD) Warncell-IDs
# This is for German users only. If you populate this dictionary, then
# MPAD will be instructed to broadcast severe wx warnings for
# specific municipal areas in Germany.
#
# Leave this dictionary empty if you do not want MPAD to issue DWD bulletins
#
# Dictionary key: warncell id
# Dictionary value: max 3-character city identifier
#
# List of valid Warncell IDs can be found on this page:
# https://www.dwd.de/DE/leistungen/opendata/hilfe.html
# Direct file link:
# https://www.dwd.de/DE/leistungen/opendata/help/warnungen/cap_warncellids_csv.csv?__blob=publicationFile&v=3
mpad_dwd_warncells = {
    "103255000": "HOL",
    "105762000": "HX",
}

#
# The program's bulletin and beacon messages
#
# APRS_IS bulletin messages (will be sent every 4 hrs)
# Note: these HAVE to have 67 characters (or less) per entry
# MPAD will NOT check the content and send it out 'as is'
aprs_bulletin_messages: dict = {
    "BLN0": f"{mpad_alias} {mpad_version} Multi-Purpose APRS Daemon",
    "BLN1": f"See https://github.com/joergschultzelutter/mpad for command syntax",
    "BLN2": f"and program source code. 73 de DF1JSL",
}
#
# APRS_IS beacon messages (will be sent every 30 mins)
# - APRS Position (first line) needs to have 63 characters or less
# - APRS Status can have 67 chars (as usual)
# Details: see aprs101.pdf chapter 8
#
# MPAD will NOT check the content and send it out 'as is'
#
# This message is a position report; format description can be found on pg. 23ff and pg. 94ff.
# of aprs101.pdf. Message symbols: see http://www.aprs.org/symbols/symbolsX.txt and aprs101.pdf
# on page 104ff.
# Format is as follows: =Lat primary-symbol-table-identifier lon symbol-identifier test-message
# Lat/lon from the configuration have to be valid or the message will not be accepted by aprs-is
#
# Example nessage: MPAD>APRS:=5150.34N/00819.60E?MPAD 0.01
# results in
# lat = 5150.34N
# primary symbol identifier = /
# lon = 00819.60E
# symbol identifier = ?
# plus some text.
# The overall total symbol code /? refers to a server icon - see list of symbols
#
aprs_beacon_messages: list = [
    f"={mpad_latitude}{aprs_table}{mpad_longitude}{aprs_symbol}{mpad_alias} {mpad_version} /A={mpad_beacon_altitude_ft:06}",
    #    ">Multi-Purpose APRS Daemon",
]
#
# Several file names that are used throughout the program and act as local databases
mpad_airport_stations_filename = "airport_stations.txt"
mpad_tle_amateur_satellites_filename = "tle_amateur_satellites.txt"
mpad_satellite_frequencies_filename = "satellite_frequencies.csv"
mpad_hearham_raw_data_filename = "hearham_raw_data.json"
mpad_repeatermap_raw_data_filename = "repeatermap_raw_data.json"
mpad_repeater_data_filename = "mpad_repeater_data.json"
mpad_satellite_data_filename = "mpad_satellite_data.json"

# definitions for the various day times (e.g. "noon"), used by the wx forecast process
# Each definition represents the hour in LOCAL TIME format, e.g. 12 = 12h local time
mpad_int_morning = 6
mpad_int_daytime = 12
mpad_int_evening = 18
mpad_int_night = 0

# These are the internal keywords for the various day times
mpad_str_morning = "morning"
mpad_str_daytime = "daytime"
mpad_str_evening = "evening"
mpad_str_night = "night"
mpad_str_full = "full"

# hour-to-string mapper for daytimes
mpad_daytime_mapper = {
    mpad_int_morning: mpad_str_morning,
    mpad_int_daytime: mpad_str_daytime,
    mpad_int_evening: mpad_str_evening,
    mpad_int_night: mpad_str_night,
}

# This is the file name for the file that we use for our nohup
# stdout content. We use this name in order to send the log file
# to mpad's host in case the program has crashed.
#
# Only used if you activate the Apprise messaging option.
#
# Example: assume that you have started MPAD via
#
#       nohup python aprs_listener & 2>nohup.out
#
# Now, the program crashes because its author messed up things :-)
# Assuming that you have activated the Apprise messaging option,
# MPAD will look up the file associated with mpad_nohup_filename and
# is going to send you a copy prior to the actual program crash
# Note that the call stack is always included as message attachment
# and not as message content - the call stack might be rather large, thus
# getting potentially truncated in the message body
#
mpad_nohup_filename = "nohup.out"
