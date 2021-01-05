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
