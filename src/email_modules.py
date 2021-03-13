#
# Multi-Purpose APRS Daemon: Email modules
# Author: Joerg Schultze-Lutter, 2021
#
# Purpose: process messages from/to APRS-IS (http://www.aprs-is.net/Email.aspx)
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

import logging
import smtplib
from email.message import EmailMessage
import re
import datetime
import mpad_config
from geo_conversion_modules import (
    convert_latlon_to_maidenhead,
    convert_latlon_to_dms,
    convert_latlon_to_utm,
    convert_latlon_to_mgrs,
)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

# The following two variables define the templates for the outgoing email
# The first one is simple plain text whereas the second one is HTML
#
# YES - I KNOW. Normal people would import this from a file. Welcome to Team Different.

plaintext_template = """\
AUTOMATED EMAIL - PLEASE DO NOT RESPOND

Position reports for REPLACE_MESSAGECALLSIGN on the internet:

aprs.fi:                                        REPLACE_APRSDOTFI
Google Maps:                                    REPLACE_GOOGLEMAPS

Position details:
=================
Maidenhead Grid Locator:                        REPLACE_MAIDENHEAD
DMS Degrees and Decimal Minutes:                REPLACE_DMS
UTM Universal Transverse Mercator:              REPLACE_UTM
MGRS Military Grid Reference System / USNG:     REPLACE_MGRS
Latitude and Longitude / Decimal Degrees:       REPLACE_LATLON
Altitude                                        REPLACE_ALTITUDE
Last heard on aprs.fi                           REPLACE_LASTHEARD
Address data:                                   REPLACE_ADDRESS_DATA_LINE1
                                                REPLACE_ADDRESS_DATA_LINE2

This position report was requested by REPLACE_USERSCALLSIGN via APRS and was processed by MPAD (Multi-Purpose APRS Daemon). Generated at REPLACE_DATETIME_CREATED UTC
More info on MPAD can be found here: https://www.github.com/joergschultzelutter/mpad
---
Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL
"""

html_template = """\
<h2>Automated email - please do not respond</h2>
<p>Position data for REPLACE_MESSAGECALLSIGN on the Internet:</p>
<ul>
<li>aprs.fi<a href="REPLACE_APRSDOTFI" target="_blank" rel="noopener">REPLACE_APRSDOTFI</a></li>
<li>Google Maps: <a href="REPLACE_GOOGLEMAPS" target="_blank" rel="noopener">REPLACE_GOOGLEMAPS</a>&nbsp;</li>
</ul>
<table border="1">
<thead>
<tr style="background-color: #bbbbbb;">
<td><strong>Position details</strong></td>
<td><strong>Values</strong></td>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Maidenhead</strong> Grid Locator</td>
<td>REPLACE_MAIDENHEAD</td>
</tr>
<tr>
<td><strong>DMS</strong> Degrees and Decimal Minutes&nbsp;</td>
<td>REPLACE_DMS</td>
</tr>
<tr>
<td><strong>UTM</strong> Universal Transverse Mercator</td>
<td>REPLACE_UTM</td>
</tr>
<tr>
<td>
<p><strong>MGRS</strong> Military Grid Reference System /&nbsp;<strong>USNG</strong> United States National Grid</p>
</td>
<td>REPLACE_MGRS</td>
</tr>
<tr>
<td>
<p><strong>Latitude and Longitude</strong> Decimal Degrees</p>
</td>
<td>REPLACE_LATLON</td>
</tr>
<tr>
<td>
<p><strong>Altitude</strong></p>
</td>
<td>REPLACE_ALTITUDE</td>
</tr>
<tr>
<td>
<p><strong>Last heard on aprs.fi</strong></p>
</td>
<td>REPLACE_LASTHEARD</td>
</tr>
<tr>
<td>
<p><strong>Address data</strong></p>
</td>
<td>
<p>REPLACE_ADDRESS_DATA_LINE1</p>
<p>REPLACE_ADDRESS_DATA_LINE2</p>
</td>
</tr>
</tbody>
</table>
<p>This position report was requested by REPLACE_USERSCALLSIGN via APRS and was processed by <a href="https://aprs.fi/#!call=a%2FMPAD&amp;timerange=3600&amp;tail=3600" target="_blank" rel="noopener">MPAD (Multi-Purpose APRS Daemon)</a>. Generated at REPLACE_DATETIME_CREATED UTC</p>
<p>More info on MPAD can be found here: <a href="https://www.github.com/joergschultzelutter/mpad" target="_blank" rel="noopener">https://www.github.com/joergschultzelutter/mpad</a></p>
<hr />
<p>Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL</p>
"""

mail_subject_template = (
    "Multi-Purpose APRS Daemon: Position Report for REPLACE_MESSAGECALLSIGN"
)


def send_email_position_report(response_parameters: dict):
    """
    Prepare an APRS-IS email message with an aprs.fi position_report

    Parameters
    ==========
    response_parameters : 'dict'
        The all-knowing dictionary with our settings and parser values

    Returns
    =======
    success: 'bool'
        False in case an error has occurred
    output_list: 'list'
        List item, containing the message(s) that are going to be sent
        back to the APRS user (does not contain any email content)
    """

    smtp_email_address = response_parameters["smtp_email_address"]
    smtp_email_password = response_parameters["smtp_email_password"]

    # Check if the email address has been configured. By default, this value
    # is set to NOT_CONFIGURED in the program's template on github
    # if the mail address looks ok, then we assume that the user has
    # done his homework and had completed his local setup
    regex_string = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    matches = re.search(
        pattern=regex_string, string=smtp_email_address, flags=re.IGNORECASE
    )
    if (
        matches
        and mpad_config.mpad_smtp_server_port != 0
        and mpad_config.mpad_smtp_server_address
    ):
        # copy the templates
        plaintext_message = plaintext_template
        html_message = html_template
        subject_message = mail_subject_template

        latitude = response_parameters["latitude"]
        longitude = response_parameters["longitude"]
        altitude = response_parameters["altitude"]
        units = response_parameters["units"]
        message_callsign = response_parameters["message_callsign"]
        users_callsign = response_parameters["users_callsign"]
        mail_recipient = response_parameters["mail_recipient"]

        lasttime = response_parameters["lasttime"]
        if not isinstance(lasttime, datetime.datetime):
            lasttime = datetime.datetime.min

        # all of the following data was reverse-lookup'ed and can be 'None'
        city = response_parameters["city"]
        state = response_parameters["state"]
        zipcode = response_parameters["zipcode"]
        country = response_parameters["country"]
        county = response_parameters["county"]
        street = response_parameters["street"]
        street_number = response_parameters["street_number"]

        # Replace data on whose position is this for
        plaintext_message = plaintext_message.replace(
            "REPLACE_MESSAGECALLSIGN", message_callsign
        )
        html_message = html_message.replace("REPLACE_MESSAGECALLSIGN", message_callsign)
        subject_message = subject_message.replace(
            "REPLACE_MESSAGECALLSIGN", message_callsign
        )

        # Replace data on who requested this report
        plaintext_message = plaintext_message.replace(
            "REPLACE_USERSCALLSIGN", users_callsign
        )
        html_message = html_message.replace("REPLACE_USERSCALLSIGN", users_callsign)

        # calculate maidenhead coordinates and remove the placeholders in the template
        maidenhead_grid = convert_latlon_to_maidenhead(
            latitude=latitude, longitude=longitude
        )
        plaintext_message = plaintext_message.replace(
            "REPLACE_MAIDENHEAD", maidenhead_grid
        )
        html_message = html_message.replace("REPLACE_MAIDENHEAD", maidenhead_grid)

        # Calculate DMS coordinates and remove the placeholders in the template
        (
            lat_deg,
            lat_min,
            lat_sec,
            lat_hdg,
            lon_deg,
            lon_min,
            lon_sec,
            lon_hdg,
        ) = convert_latlon_to_dms(latitude=latitude, longitude=longitude)
        msg_string = (
            f"{lat_deg:02d}° {lat_min:02d}'{round(lat_sec, 1):02.1f}\" {lat_hdg}, "
        )
        msg_string += (
            f"{lon_deg:02d}° {lon_min:02d}'{round(lon_sec, 1):02.1f}\" {lon_hdg}"
        )
        plaintext_message = plaintext_message.replace("REPLACE_DMS", msg_string)
        html_message = html_message.replace("REPLACE_DMS", msg_string)

        # Get latitude/longitude and remove the placeholders in the template
        msg_string = f"{latitude}, {longitude}"
        plaintext_message = plaintext_message.replace("REPLACE_LATLON", msg_string)
        html_message = html_message.replace("REPLACE_LATLON", msg_string)

        # If altitude is available, calculate value and remove the placeholders in the template
        if altitude:
            altitude_uom = "m"
            altitude_value = round(altitude)

            if units == "imperial":
                altitude_uom = "ft"
                altitude_value = round(altitude * 3.28084)  # convert m to feet

            msg_string = f"{altitude_value}{altitude_uom}"
        else:
            msg_string = "not available"
        plaintext_message = plaintext_message.replace("REPLACE_ALTITUDE", msg_string)
        html_message = html_message.replace("REPLACE_ALTITUDE", msg_string)

        # Calculate UTM coordinates and remove the placeholders in the template
        zone_number, zone_letter, easting, northing = convert_latlon_to_utm(
            latitude=latitude, longitude=longitude
        )
        msg_string = f"Zone {zone_number}{zone_letter} E:{easting} N:{northing}"
        plaintext_message = plaintext_message.replace("REPLACE_UTM", msg_string)
        html_message = html_message.replace("REPLACE_UTM", msg_string)

        # Calculate MGRS coordinates and remove the placeholders in the template
        msg_string = convert_latlon_to_mgrs(latitude=latitude, longitude=longitude)
        plaintext_message = plaintext_message.replace("REPLACE_MGRS", msg_string)
        html_message = html_message.replace("REPLACE_MGRS", msg_string)

        # Determine the human readable address line 1 if available
        msg_string = ""
        if city:
            msg_string = city
        if zipcode:
            msg_string += f", {zipcode}"
        if state:
            msg_string += f", {state}"
        if county:
            msg_string += f", {county}"
        plaintext_message = plaintext_message.replace(
            "REPLACE_ADDRESS_DATA_LINE1", msg_string
        )
        html_message = html_message.replace("REPLACE_ADDRESS_DATA_LINE1", msg_string)

        # Determine the human readable address line 2 if available
        msg_string = ""
        if street:
            msg_string = street
            if street_number:
                # per https://en.wikipedia.org/wiki/Address, we try to honor the native format
                # for those countries who list the street number before the street name
                if country in mpad_config.street_number_precedes_street:
                    msg_string = f"{street_number} " + msg_string
                else:
                    msg_string = msg_string + f" {street_number}"
        plaintext_message = plaintext_message.replace(
            "REPLACE_ADDRESS_DATA_LINE2", msg_string
        )
        html_message = html_message.replace("REPLACE_ADDRESS_DATA_LINE2", msg_string)

        # Check if a "last time heard on aprs.fi" timestamp is available and add it if present
        if lasttime is not datetime.datetime.min:
            msg_string = f"{lasttime.strftime('%d-%b-%Y %H:%M:%S')} UTC"
        else:
            msg_string = "not available"
        plaintext_message = plaintext_message.replace("REPLACE_LASTHEARD", msg_string)
        html_message = html_message.replace("REPLACE_LASTHEARD", msg_string)

        # Add the aprs.fi call sign link
        msg_string = f"https://aprs.fi/#!call=a%2F{message_callsign}"
        plaintext_message = plaintext_message.replace("REPLACE_APRSDOTFI", msg_string)
        html_message = html_message.replace("REPLACE_APRSDOTFI", msg_string)

        # Add the Google Maps call sign link
        msg_string = f"https://maps.google.com/?q={latitude},{longitude}"
        plaintext_message = plaintext_message.replace("REPLACE_GOOGLEMAPS", msg_string)
        html_message = html_message.replace("REPLACE_GOOGLEMAPS", msg_string)

        utc_create_time = datetime.datetime.utcnow()
        msg_string = f"{utc_create_time.strftime('%d-%b-%Y %H:%M:%S')} UTC"
        plaintext_message = plaintext_message.replace(
            "REPLACE_DATETIME_CREATED", msg_string
        )
        html_message = html_message.replace("REPLACE_DATETIME_CREATED", msg_string)

        # Finally, generate the message
        msg = EmailMessage()
        msg["Subject"] = subject_message
        msg["From"] = smtp_email_address
        msg["To"] = mail_recipient
        msg.set_content(plaintext_message)
        msg.add_alternative(html_message, subtype="html")

        output_message = "The requested position report was emailed to its recipient"

        try:
            with smtplib.SMTP_SSL(
                mpad_config.mpad_smtp_server_address, mpad_config.mpad_smtp_server_port
            ) as smtp:
                smtp.login(smtp_email_address, smtp_email_password)
                smtp.send_message(msg)
                smtp.quit()
        except smtplib.SMTPAuthenticationError:
            output_message = (
                "MPAD instance has invalid SMTP access credentials; cannot send mail"
            )
            logger.info(output_message)
        except:
            output_message = "Cannot connect to server / other issue; cannot send mail"
            logger.info(output_message)
    else:
        output_message = (
            "This MPAD instance is not configured for email position messages"
        )

    output_list = [output_message]
    return output_list


if __name__ == "__main__":
    pass
