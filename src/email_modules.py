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
import imaplib
from email.message import EmailMessage
from email.utils import make_msgid
import re
import datetime
import mpad_config
from geo_conversion_modules import (
    convert_latlon_to_maidenhead,
    convert_latlon_to_dms,
    convert_latlon_to_utm,
    convert_latlon_to_mgrs,
)
from staticmap import render_png_map
from utility_modules import read_program_config

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

# The following three variables define the templates for the outgoing email
# Template 1 = plain text (also used as fallback format)
# Templates 2 and 3 = html data with/without image with user's position
#                     template without user's position is only used in case
#                     we were unable to generate the image
#
# YES - I KNOW. Normal people would import this from a file. Welcome to Team Different.

plaintext_template = """\
AUTOMATED EMAIL - PLEASE DO NOT RESPOND

APRS position data for REPLACE_MESSAGECALLSIGN on the Internet:

aprs.fi:                                        REPLACE_APRSDOTFI
FindU.com                                       REPLACE_FINDUDOTCOM
Google Maps:                                    REPLACE_GOOGLEMAPS
QRZ.COM:                                        REPLACE_QRZDOTCOM

Position details:
=================
Maidenhead Grid Locator:                        REPLACE_MAIDENHEAD
DMS Degrees and Decimal Minutes:                REPLACE_DMS
UTM Universal Transverse Mercator:              REPLACE_UTM
MGRS Military Grid Reference System / USNG:     REPLACE_MGRS
Latitude and Longitude / Decimal Degrees:       REPLACE_LATLON
Altitude                                        REPLACE_ALTITUDE
Last heard on APRS-IS                           REPLACE_LASTHEARD
Address data:                                   REPLACE_ADDRESS_DATA

This position report was requested by REPLACE_USERSCALLSIGN via APRS and was processed by MPAD (Multi-Purpose APRS Daemon). Generated at REPLACE_DATETIME_CREATED
More info on MPAD can be found here: https://www.github.com/joergschultzelutter/mpad
---
Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL
"""

html_template_without_image = """\
<h2>Automated email - please do not respond</h2>
<p>APRS position data for <strong>REPLACE_MESSAGECALLSIGN</strong> on the Internet:</p>
<ul>
<li><a href="REPLACE_APRSDOTFI" target="_blank" rel="noopener">aprs.fi</a></li>
<li><a href="REPLACE_FINDUDOTCOM" target="_blank" rel="noopener">FindU.com</a></li>
<li><a href="REPLACE_GOOGLEMAPS" target="_blank" rel="noopener">Google Maps</a>&nbsp;</li>
<li><a href="REPLACE_QRZDOTCOM" target="_blank" rel="noopener">QRZ.com</a>&nbsp;</li>
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
<td><strong>&nbsp;Maidenhead</strong> Grid Locator</td>
<td>&nbsp;REPLACE_MAIDENHEAD</td>
</tr>
<tr>
<td><strong>&nbsp;DMS</strong> Degrees and Decimal Minutes&nbsp;</td>
<td>&nbsp;REPLACE_DMS</td>
</tr>
<tr>
<td><strong>&nbsp;UTM</strong> Universal Transverse Mercator</td>
<td>&nbsp;REPLACE_UTM</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;MGRS</strong> Military Grid Reference System</p>
<p><strong>&nbsp;USNG</strong> United States National Grid</p>
</td>
<td>&nbsp;REPLACE_MGRS</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Latitude and Longitude</strong></p>
</td>
<td>&nbsp;REPLACE_LATLON</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Altitude</strong></p>
</td>
<td>&nbsp;REPLACE_ALTITUDE</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Last heard on APRS-IS</strong></p>
</td>
<td>&nbsp;REPLACE_LASTHEARD</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Address data</strong></p>
</td>
<td>
<p>&nbsp;REPLACE_ADDRESS_DATA</p>
</td>
</tr>
</tbody>
</table>
<p>This position report was requested by <strong>REPLACE_USERSCALLSIGN</strong> via APRS and was processed by <a href="https://aprs.fi/#!call=a%2FMPAD&amp;timerange=3600&amp;tail=3600" target="_blank" rel="noopener">MPAD (Multi-Purpose APRS Daemon)</a>. Generated at <strong>REPLACE_DATETIME_CREATED</strong></p>
<p>More info on MPAD can be found here: <a href="https://www.github.com/joergschultzelutter/mpad" target="_blank" rel="noopener">https://www.github.com/joergschultzelutter/mpad</a></p>
<hr />
<p>Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL</p>
"""

html_template_with_image = """\
<h2>Automated email - please do not respond</h2>
<p>APRS position data for <strong>REPLACE_MESSAGECALLSIGN</strong> on the Internet:</p>
<ul>
<li><a href="REPLACE_APRSDOTFI" target="_blank" rel="noopener">aprs.fi</a></li>
<li><a href="REPLACE_FINDUDOTCOM" target="_blank" rel="noopener">FindU.com</a></li>
<li><a href="REPLACE_GOOGLEMAPS" target="_blank" rel="noopener">Google Maps</a>&nbsp;</li>
<li><a href="REPLACE_QRZDOTCOM" target="_blank" rel="noopener">QRZ.com</a>&nbsp;</li>
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
<td><strong>&nbsp;Maidenhead</strong> Grid Locator</td>
<td>&nbsp;REPLACE_MAIDENHEAD</td>
</tr>
<tr>
<td><strong>&nbsp;DMS</strong> Degrees and Decimal Minutes&nbsp;</td>
<td>&nbsp;REPLACE_DMS</td>
</tr>
<tr>
<td><strong>&nbsp;UTM</strong> Universal Transverse Mercator</td>
<td>&nbsp;REPLACE_UTM</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;MGRS</strong> Military Grid Reference System</p>
<p><strong>&nbsp;USNG</strong> United States National Grid</p>
</td>
<td>&nbsp;REPLACE_MGRS</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Latitude and Longitude</strong></p>
</td>
<td>&nbsp;REPLACE_LATLON</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Altitude</strong></p>
</td>
<td>&nbsp;REPLACE_ALTITUDE</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Last heard on APRS-IS</strong></p>
</td>
<td>&nbsp;REPLACE_LASTHEARD</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Address data</strong></p>
</td>
<td>
<p>&nbsp;REPLACE_ADDRESS_DATA</p>
</td>
</tr>
</tbody>
</table>
<hr />
<p><center><img src="cid:{image_cid}" /></center></p>
<hr />
<p>This position report was requested by <strong>REPLACE_USERSCALLSIGN</strong> via APRS and was processed by <a href="https://aprs.fi/#!call=a%2FMPAD&amp;timerange=3600&amp;tail=3600" target="_blank" rel="noopener">MPAD (Multi-Purpose APRS Daemon)</a>. Generated at <strong>REPLACE_DATETIME_CREATED</strong></p>
<p>More info on MPAD can be found here: <a href="https://www.github.com/joergschultzelutter/mpad" target="_blank" rel="noopener">https://www.github.com/joergschultzelutter/mpad</a></p>
<hr />
<p>Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL</p>
"""

mail_subject_template = "APRS Position Report for REPLACE_MESSAGECALLSIGN"


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

    # get the required email data from our data pool
    smtpimap_email_address = response_parameters["smtpimap_email_address"]
    smtpimap_email_password = response_parameters["smtpimap_email_password"]

    latitude = response_parameters["latitude"]
    longitude = response_parameters["longitude"]
    altitude = response_parameters["altitude"]
    units = response_parameters["units"]
    message_callsign = response_parameters["message_callsign"]
    users_callsign = response_parameters["users_callsign"]
    mail_recipient = response_parameters["mail_recipient"]

    # Now try to generate an image map of the user's position...
    html_image = render_png_map(aprs_latitude=latitude, aprs_longitude=longitude)
    # ... and now choose the template according to whether we happen to
    # have been able to generate an image or not
    html_message = (
        html_template_with_image if html_image else html_template_without_image
    )

    # copy the remaining templates
    plaintext_message = plaintext_template
    subject_message = mail_subject_template

    # generate the time stamp
    lasttime = response_parameters["lasttime"]
    if not isinstance(lasttime, datetime.datetime):
        lasttime = datetime.datetime.min

    # Get the reverse-lookup'ed address from OpenStreetMap
    # Note: field can be of type None
    address = response_parameters["address"]

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
        latitude=latitude, longitude=longitude, output_precision=5
    )
    plaintext_message = plaintext_message.replace("REPLACE_MAIDENHEAD", maidenhead_grid)
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
    msg_string = f"{lat_deg:02d}° {lat_min:02d}'{round(lat_sec, 1):02.1f}\" {lat_hdg}, "
    msg_string += f"{lon_deg:02d}° {lon_min:02d}'{round(lon_sec, 1):02.1f}\" {lon_hdg}"
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
    if address:
        msg_string = address
    else:
        msg_string = "not available"
    plaintext_message = plaintext_message.replace("REPLACE_ADDRESS_DATA", msg_string)
    html_message = html_message.replace("REPLACE_ADDRESS_DATA", msg_string)

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

    # Add the FindU.com link
    msg_string = f"http://www.findu.com/cgi-bin//find.cgi?call={message_callsign}"
    plaintext_message = plaintext_message.replace("REPLACE_FINDUDOTCOM", msg_string)
    html_message = html_message.replace("REPLACE_FINDUDOTCOM", msg_string)

    # add the Time Created information
    utc_create_time = datetime.datetime.utcnow()
    msg_string = f"{utc_create_time.strftime('%d-%b-%Y %H:%M:%S')} UTC"
    plaintext_message = plaintext_message.replace(
        "REPLACE_DATETIME_CREATED", msg_string
    )
    html_message = html_message.replace("REPLACE_DATETIME_CREATED", msg_string)

    # split callsign and SSID whereas present
    callsign_list = message_callsign.split("-")
    if len(callsign_list) > 0:
        msg_string = f"https://www.qrz.com/db/{callsign_list[0]}"
    else:
        msg_string = "not available"
    plaintext_message = plaintext_message.replace("REPLACE_QRZDOTCOM", msg_string)
    html_message = html_message.replace("REPLACE_QRZDOTCOM", msg_string)

    # Finally, generate the message
    msg = EmailMessage()
    msg["Subject"] = subject_message
    msg["From"] = f"MPAD Multi-Purpose APRS Daemon <{smtpimap_email_address}>"
    msg["To"] = mail_recipient
    msg.set_content(plaintext_message)

    # Image present? Then encode it properly
    if html_image:
        image_cid = make_msgid()
        msg.add_alternative(
            html_message.format(image_cid=image_cid[1:-1]), subtype="html"
        )
        x = msg.get_payload()

        msg.get_payload()[1].add_related(
            html_image, maintype="image", subtype="png", cid=image_cid
        )
    else:
        # otherwise, send the HTML content without an image
        msg.add_alternative(html_message, subtype="html")

    success, output_message = send_message_via_snmp(
        smtpimap_email_address=smtpimap_email_address,
        smtpimap_email_password=smtpimap_email_password,
        message_to_send=msg,
    )
    output_list = [output_message]
    return output_list


def imap_garbage_collector(smtpimap_email_address: str, smtpimap_email_password: str):
    """
    Delete all messages in the MPAD user's iMAP account that are older than x days

    Parameters
    ==========
    smtpimap_email_address : 'str'
        email address for login
    smtpimap_email_password: 'str'
        password for login

    Returns
    =======
    """

    # Check if the garbage collector has been disabled and
    # abort the process if necessary
    if mpad_config.mpad_imap_mail_retention_max_days == 0:
        return

    regex_string = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    matches = re.search(
        pattern=regex_string, string=smtpimap_email_address, flags=re.IGNORECASE
    )
    if (
        matches
        and mpad_config.mpad_imap_server_port != 0
        and mpad_config.mpad_imap_server_address
    ):
        cutoff = (
            datetime.date.today()
            - datetime.timedelta(days=mpad_config.mpad_imap_mail_retention_max_days)
        ).strftime("%d-%b-%Y")
        query_parms = f'(BEFORE "{cutoff}")'
        with imaplib.IMAP4_SSL(
            host=mpad_config.mpad_imap_server_address,
            port=mpad_config.mpad_imap_server_port,
        ) as imap:
            logger.info(msg="Starting IMAP garbage collector process")
            typ, dat = imap.login(
                user=smtpimap_email_address, password=smtpimap_email_password
            )
            if typ == "OK":
                logger.info(msg="IMAP login successful")
                # typ, dat = imap.list()     # get list of mailboxes
                typ, dat = imap.select(mailbox=mpad_config.mpad_imap_mailbox_name)
                if typ == "OK":
                    logger.info(
                        msg=f"IMAP folder SELECT for {mpad_config.mpad_imap_mailbox_name} successful"
                    )
                    typ, msgnums = imap.search(None, "ALL", query_parms)
                    if typ == "OK":
                        for num in msgnums[0].split():
                            imap.store(num, "+FLAGS", "\\Deleted")
                        imap.expunge()
                        logger.info(
                            msg=f"Have executed IMAP cleanup with params '{query_parms}'"
                        )
                    imap.close()
                else:
                    logger.info(
                        msg=f"IMAP mailbox {mpad_config.mpad_imap_mailbox_name} does not exist"
                    )
                imap.logout()
            else:
                logger.info(
                    msg=f"Cannot perform IMAP login; user={smtpimap_email_address}, server={mpad_config.mpad_imap_server_address}, port={mpad_config.mpad_imap_server_port}"
                )


def send_message_via_snmp(
    smtpimap_email_address: str,
    smtpimap_email_password: str,
    message_to_send: EmailMessage,
):
    """
    Send an email via SMTP

    Parameters
    ==========
    smtpimap_email_address : 'str'
        email address for login
    smtpimap_email_password: 'str'
        password for login
    message_to_send: 'str'
        The message that has already been prepared for
        the end user

    Returns
    =======
    success: 'bool'
        True if successful
    output_messagee: 'str'
        status that corresponds to the SMTP delivery process
    """

    success = False
    output_message = ""
    # Check if the email address has been configured. By default, this value
    # is set to NOT_CONFIGURED in the program's template on github
    # if the mail address looks ok, then we assume that the user has
    # done his homework and had completed his local setup
    regex_string = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    matches = re.search(
        pattern=regex_string, string=smtpimap_email_address, flags=re.IGNORECASE
    )
    if (
        matches
        and mpad_config.mpad_smtp_server_port != 0
        and mpad_config.mpad_smtp_server_address
    ):
        with smtplib.SMTP_SSL(
            host=mpad_config.mpad_smtp_server_address,
            port=mpad_config.mpad_smtp_server_port,
        ) as smtp:
            try:
                code, resp = smtp.login(
                    user=smtpimap_email_address, password=smtpimap_email_password
                )
            except (smtplib.SMTPException, smtplib.SMTPAuthenticationError) as e:
                output_message = (
                    "Cannot connect to SMTP server or other issue; cannot send mail"
                )
                logger.info(msg=output_message)
                return False, output_message
            if code in [235, 503]:
                try:
                    smtp.send_message(msg=message_to_send)
                except:
                    output_message = "Connected to SMTP but Cannot send email"
                    logger.info(msg=output_message)
                    return False, output_message

            success = True
            output_message = (
                "The requested position report was emailed to its recipient"
            )
            smtp.quit()
    else:
        output_message = (
            "This MPAD instance is not configured for email position messages"
        )
    return success, output_message


if __name__ == "__main__":
    (
        success,
        aprsdotfi_api_key,
        openweathermap_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_callsign,
        dapnet_passcode,
        smtpimap_email_address,
        smtpimap_email_password,
    ) = read_program_config()
    imap_garbage_collector(smtpimap_email_address, smtpimap_email_password)
