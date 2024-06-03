#
# Multi-Purpose APRS Daemon
# Author: Joerg Schultze-Lutter, 2024
# Module: Apprise messaging
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import logging
import apprise
from utility_modules import check_if_file_exists

# Set up the global logger variable
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def send_apprise_message(
    message_header: str,
    message_body: str,
    apprise_config_file: str,
    message_attachment: str = None,
):
    """
    Generates Apprise messages and triggers transmission to the user
    We will only use this for post-mortem dumps in case MPAD is on the
    verge of crashing

    Parameters
    ==========
    message_header : 'str'
        The message header that we want to send to the user
    message_body : 'str'
        The message body that we want to send to the user
    apprise_config_file: 'str'
        Apprise Yaml configuration file

    Returns
    =======
    success: 'bool'
        True if successful
    """

    # predefine the output value
    success = False

    logger.debug(msg="Starting Apprise message processing")

    if not apprise_config_file or apprise_config_file == "NOT_CONFIGURED":
        logger.debug(msg="Skipping post-mortem dump; message file is not configured")
        return success

    if not check_if_file_exists(apprise_config_file):
        logger.error(
            msg=f"Apprise config file {apprise_config_file} does not exist; aborting"
        )
        return success

    if not check_if_file_exists(message_attachment):
        logger.debug("Attachment file missing; disabling attachments")
        message_attachment = None

    # Create the Apprise instance
    apobj = apprise.Apprise()

    # Create an Config instance
    config = apprise.AppriseConfig()

    # Add a configuration source:
    config.add(apprise_config_file)

    # Make sure to add our config into our apprise object
    apobj.add(config)

    if not message_attachment:
        # Send the notification
        apobj.notify(
            body=message_body,
            title=message_header,
            tag="all",
            notify_type=apprise.NotifyType.FAILURE,
        )
    else:
        # Send the notification
        apobj.notify(
            body=message_body,
            title=message_header,
            tag="all",
            notify_type=apprise.NotifyType.FAILURE,
            attach=message_attachment,
        )

    success = True

    logger.debug(msg="Finished Apprise message processing")
    return success


if __name__ == "__main__":
    pass
