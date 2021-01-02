#
# Multi-Purpose APRS Daemon: various APRS routines
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: Program configuration entries
#

# Configuration settings
mpad_version: str = "0.01"
mpad_latitude: str = "51.8388N"  # 8 chars fixed length, ddmm.mmN, see chapter 6 pg. 23
# fmt: off
mpad_longitude: str = "008.3266E"  # 9 chars fixed length, dddmm.mmE, see chapter 6 pg. 23)
# fmt: on
mpad_alias: str = "MPAD"  # Identifier for sending data to APRS-IS
mpad_aprs_tocall: str = "APRS"  # APRS "TOCALL", see http://aprs.org/aprs11/tocalls.txt. Needs to get its own identifier at a later point in time

# Constants, do not change
aprs_table: str = "/"  # my symbol table (/=primary \=secondary, or overlay)
aprs_symbol: str = "?"  # APRS symbol: Server
packet_delay_long: float = 2.0  # packet delay in seconds after sending data to aprs-is
packet_delay_short: float = 1.0  # packet delay in seconds after sending data to aprs-is

# Beacon / Bulletin config settings
myaprsis_login_callsign = "N0CALL"  # APRS-IS login

myaprs_server_name = "euro.aprs2.net"  # our login server
myaprs_server_port = 14580  # server port
myaprs_server_filter = "g/WXBOT/WXYO"  # server filter criteria for aprs.is
mycallsigns_to_parse = ["WXBOT", "WXYO"]  # (additional) call sign filter
