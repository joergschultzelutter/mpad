#
# Multi-Purpose APRS Daemon: radiosonde landing prediction
# Author: Joerg Schultze-Lutter, 2020
#
# Radiosonde landing prediction
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
from utility_modules import read_program_config
import logging
from aprsdotfi_modules import get_position_on_aprsfi
from datetime import datetime, timedelta
import re
import requests
import xmltodict

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def get_ascent_descent_burst(clmb: float, altitude: float):
    """
    Determines the ascent rate, descent rate and burst altitude
    based on both clmb rate and altitude from aprs.fi

    Parameters
    ==========
    clmb: 'float'
        Climb rate from the aprs.fi position report
    altitude: 'float'
        Altitude from the aprs.fi position report

    Returns
    =======
    ascent_rate: 'float'
        Ascent rate in meters
    descent_rate: 'float'
        Descent rate in meters
    burst_altitude: 'float'
        Burst altitude in meters
    """

    if clmb >= 0:
        ascent_rate = clmb
        descent_rate = 5
        if altitude < 25000:
            burst_altitude = 25000
        elif 25000 < altitude < 30000:
            burst_altitude = 30000
        elif 30000 < altitude < 35000:
            burst_altitude = 35000
        else:
            burst_altitude = 38000
    else:
        burst_altitude = altitude + 1
        ascent_rate = 0.0
        descent_rate = abs(clmb)
    return ascent_rate, descent_rate, burst_altitude


def get_clmb_from_comment(probe_comment: str):
    """
    Gets the 'clmb' rate from the aprs.fi position
    report (if present)

    Parameters
    ==========
    probe_comment: 'str'
        aprs.fi 'comment' from position report

    Returns
    =======
    clmb: 'float'
        Climb rate in meters
    """
    clmb = None
    matches = re.search(
        pattern=r"Clb=(-?[0-9]\d*(?:\.\d+)?)",
        string=probe_comment,
        flags=re.IGNORECASE,
    )

    if matches:
        try:
            clmb = float(matches[1])
        except ValueError:
            clmb = 0.0
    return clmb


def get_kml_data_from_habhub(
    latitude: float, longitude: float, altitude: float, clmb: float
):
    """
    Gets the 'clmb' rate from the aprs.fi position
    report (if present)

    Parameters
    ==========
    latitude: 'float'
        latitude from aprs.fi position report
    longitude: 'float'
        longitude from aprs.fi position report
    altitude: 'float'
        altitude from aprs.fi position report
    clmb: 'float'
        extracted clmb value from aprs.fi position report

    Returns
    =======
    success: 'bool'
        True if we were able to determine landing coordinates etc
    landing_latitude: 'float'
        Latitude of the predicted probe landing (if success = True)
    landing_longitude: 'float'
        Longitude of the predicted probe landing (if success = True)
    landing_timestamp: 'float'
        Timestamp of the predicted probe landing (if success = True)
    """

    landing_latitude = landing_longitude = 0.0
    landing_timestamp = datetime.min
    success = False

    ascent_rate, descent_rate, burst_altitude = get_ascent_descent_burst(
        clmb=clmb, altitude=altitude
    )

    # we can't use the aprs.fi timestamp as it is always in the past
    # the web site demands that we have a timestamp that is at least 1
    # minute in the future. So let's use the current UTC time and add
    # one minute to it
    timestamp = datetime.utcnow() + timedelta(minutes=1)

    # Create the payload item for the POST operation
    hubhab_payload = {
        "launchsite": "Other",
        "lat": f"{latitude}",
        "lon": f"{longitude}",
        "initial_alt": f"{altitude}",
        "hour": f"{timestamp.hour}",
        "min": f"{timestamp.minute}",
        "second": f"0",
        "day": f"{timestamp.day}",
        "month": f"{timestamp.month}",
        "year": f"{timestamp.year}",
        "ascent": f"{ascent_rate}",
        "burst": f"{burst_altitude}",
        "drag": f"{descent_rate}",
        "submit": "Run+Prediction",
    }
    # logger.info(hubhab_payload)

    # Send the payload to the site. If all goes well, Habhub responds
    # with a HTTP200 and provides us with a UUID
    url = "http://predict.habhub.org/ajax.php?action=submitForm"
    resp = requests.post(url=url, data=hubhab_payload)
    if resp:
        if resp.status_code == 200:
            json_content = resp.json()

            # Check if we have received a valid response from the  site
            valid = "false"
            if "valid" in json_content:
                valid = json_content["valid"]

            # Everything seems to be okay so let's get the UUID (if present)
            if valid == "true":
                if "uuid" in json_content:
                    uuid = json_content["uuid"]

                    # We're going to download the KML file for this UUID
                    # Let's construct the respective URL
                    url = f"http://predict.habhub.org/kml.php?uuid={uuid}"
                    resp = requests.get(url=url)
                    if resp:
                        if resp.status_code == 200:

                            # We have received XML content. For better navigation throughout
                            # the data structure, let's convert the content to a 'dict' object
                            # (xmltodict converts to an OrderedDict)
                            try:
                                kml_dict = xmltodict.parse(resp.text)
                            except:
                                kml_dict = {}

                            # Now navigate through the structure and get our data
                            # The stuff that we want is in the "Placemark" subsection
                            if "kml" in kml_dict:
                                if "Document" in kml_dict["kml"]:
                                    if "Placemark" in kml_dict["kml"]["Document"]:
                                        placemarks = kml_dict["kml"]["Document"][
                                            "Placemark"
                                        ]

                                        # Iterate through the available placemark objects and start
                                        # parsing once we have hit the "Predicted Balloon Landing" entry
                                        for placemark in placemarks:
                                            if "name" in placemark:
                                                name = placemark["name"]
                                                if name == "Predicted Balloon Landing":
                                                    # We have a winner! Our content is stored in the 'description' field
                                                    if "description" in placemark:
                                                        description = placemark[
                                                            "description"
                                                        ]

                                                        # run some regex magic for extracting what we want
                                                        regex_string = r"^Balloon landing at (\d*[.]\d*),\s*(\d*[.]\d*)\s*at\s*(\d*[:]\d* \d{2}\/\d{2}\/\d{4}).$"
                                                        matches = re.search(
                                                            pattern=regex_string,
                                                            string=description,
                                                            flags=re.IGNORECASE,
                                                        )
                                                        if matches:
                                                            # extract lat/lon/timestamp
                                                            # fmt: off
                                                            success = True
                                                            try:
                                                                landing_latitude = float(matches[1])
                                                                landing_longitude = float(matches[2])
                                                            except ValueError:
                                                                landing_latitude = landing_longitude = 0.0
                                                                success = False
                                                            ts_string = matches[3] + " UTC"  # timezone is UTC
                                                            # fmt: on
                                                            try:
                                                                landing_timestamp = datetime.strptime(
                                                                    ts_string,
                                                                    "%H:%M %d/%m/%Y %Z",
                                                                )
                                                                pass
                                                            except ValueError:
                                                                landing_latitude = (
                                                                    landing_longitude
                                                                ) = 0
                                                                landing_timestamp = (
                                                                    datetime.min
                                                                )
                                                                success = False
                                                            break  # we have what we want so let's finish up
    return success, landing_latitude, landing_longitude, landing_timestamp


def get_radiosonde_landing_prediction(aprsfi_callsign: str, aprsdotfi_api_key: str):
    """
    Provides a radiosonde landing prediction based on
    an aprs.fi call sign

    Parameters
    ==========
    aprsfi_callsign: 'str'
        aprs.fi callsign
    aprsdotfi_api_key: 'str'
        aprs.fi API access key

    Returns
    =======
    success: 'bool'
        True if we were able to determine landing coordinates etc
    landing_latitude: 'float'
        Latitude of the predicted probe landing (if success = True)
    landing_longitude: 'float'
        Longitude of the predicted probe landing (if success = True)
    landing_timestamp: 'float'
        Timestamp of the predicted probe landing (if success = True)
    """
    success = False
    landing_latitude = landing_longitude = 0.0
    landing_timestamp = datetime.min

    aprsfi_callsign = aprsfi_callsign.upper()

    # Try to get the position of the probe on aprs.fi
    # we explicitly ask for an aprs.fi "object" type
    # see https://aprs.fi/page/api
    (
        success,
        latitude,
        longitude,
        altitude,
        timestamp,
        comment,
        message_callsign,
    ) = get_position_on_aprsfi(
        aprsfi_callsign=aprsfi_callsign,
        aprsdotfi_api_key=aprsdotfi_api_key,
        aprs_target_type="o",
    )

    # We found the entry - so let's continue
    if success:
        if comment:
            # logger.info(comment)
            clmb = get_clmb_from_comment(probe_comment=comment)
            if clmb:
                (
                    success,
                    landing_latitude,
                    landing_longitude,
                    landing_timestamp,
                ) = get_kml_data_from_habhub(
                    latitude=latitude, longitude=longitude, altitude=altitude, clmb=clmb
                )
    return success, landing_latitude, landing_longitude, landing_timestamp


if __name__ == "__main__":
    (
        success,
        aprsdotfi_api_key,
        openweathermapdotorg_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_callsign,
        dapnet_passcode,
        smtpimap_email_address,
        smtpimap_email_password,
    ) = read_program_config()
    if success:
        logger.info(
            get_radiosonde_landing_prediction(
                aprsfi_callsign="r3320169", aprsdotfi_api_key=aprsdotfi_api_key
            )
        )
