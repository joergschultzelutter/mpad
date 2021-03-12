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

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def prepare_aprs_email_position_report(call_sign: str, email_address:str):
    """
    Prepare an APRS-IS email message with an aprs.fi position_report

    Parameters
    ==========
    call_sign : 'str'
        Call sign that we will use for the aprs.fi position reporting
    email_address: 'str'
        email_address that the report is sent to

    Returns
    =======
    mail_content: 'str'
        outgoing message text
    """

    mail_content = f"{email_address} https://aprs.fi/{call_sign}"

    # Should never be the case :-)
    assert len(mail_content) <= 67

    return mail_content

if __name__ == "__main__":
    pass
