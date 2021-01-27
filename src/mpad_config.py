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
#

###########################
# Constants, do not change#
###########################
#
mpad_version: str = "0.01"
#
# APRS position report: message symbol
# see also http://www.aprs.org/symbols/symbolsX.txt and aprs_communication.py
# on how this is used. Normally, you don't want to change these settings
#
aprs_table: str = "/"  # APRS symbol table (/=primary \=secondary, or overlay)
aprs_symbol: str = "?"  # APRS symbol: Server
#
# Delay settings: These sleep settings are applied for each SINGLE message that is sent out
# to APRS-IS. If the program has to send two bulletin messages, then the total run time of\
# sending out those bulletins is 2 * x secs
#
packet_delay_message: float = 6.0  # packet delay in seconds after sending data to aprs-is
packet_delay_other: float = 6.0  # packet delay after sending an acknowledgment, bulletin or beacon
#
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
mpad_latitude: str = "5150.34N"  # 8 chars fixed length, ddmm.ssN
mpad_longitude: str = "00819.60E"  # 9 chars fixed length, dddmm.ssE
#
# Program alias: This is the APRS name that will be used for all outgoing messages
mpad_alias: str = "MPAD"  # Identifier for sending outgoing data to APRS-IS
#
# Altitude in *FEET* (not meters) for APRS beacon. Details: see aprs101.pdf chapter 8
mpad_beacon_altitude_ft = 243
#
# APRS "TOCALL" identifier - see http://aprs.org/aprs11/tocalls.txt
# Needs to get its own identifier at a later point in time
mpad_aprs_tocall: str = "APRS"  # APRS "TOCALL"
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
#aprsis_server_filter = "g/WXBOT/WXYO"  # server filter criteria for aprs.is
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
#mpad_callsigns_to_parse = ["WXBOT", "WXYO"]  # (additional) call sign filter
mpad_callsigns_to_parse = ["MPAD"]  # (additional) call sign filter
#
#############################################################
# Time-to-live settings for the decaying APRS message cache #
#############################################################
#
# This value represents the time span for how long MPAD considers incoming
# messages as duplicates if these messages have been sent to the program
# For each processed message (regardless of its actual success state), MPAD
# is going to add a key to a decaying dictionary. That key consists of
# the user's call sign, the APRS message ID (or - if not present - 'None) and
# an md5'ed version of the message text. If another delayed or duplicate
# message is received within that specified time frame, that message is going
# to be ignored by the program
#
mpad_msg_cache_time_to_live = 5 * 60  # ttl = 5 minutes
#
############################################
# Character encoding for outgoing messages #
############################################
#
# By default, MPAD will send out UTF-8 messages to its users; this is a supported
# feature (see http://www.aprs.org/aprs12/utf-8.txt). Note that aprs101.pdf still
# limits the character encoding to ASCII 7bit, so the information from the previous
# link supersedes these restrictions
# If -for whatever reason- you do want MPAD to enforce plain ASCII messages,
# then set this marker to True.
mpad_enforce_plain_ascii_messages = False
