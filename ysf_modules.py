#
# Author: Joerg Schultze-Lutter, 2020
# Prototype: YSF repeatermap parser
#

import requests
import re
from geo_conversion_modules import convert_dms_to_latlon
import logging

def get_ysf_repeater_list(url: str = "https://www.yaesu.com/jp/en/wires-x/id/active_node.php"):
    success = False

    counter = 0

    resp = requests.get("https://www.yaesu.com/jp/en/wires-x/id/active_node.php")
    if resp.status_code == 200:
        lines = resp.text.splitlines()
        for line in lines:
            if line.startswith("dataList["):
                matches = re.search(r"^dataList\[.*\] = ({.*});$", line, re.IGNORECASE)
                if matches:
                    content = matches[1]
                    matches = re.search(r"^{id:\"(.*)\",\s*dtmf_id:\"(.*)\",\s*call_sign:\"(.*)\",\s*ana_dig:\"(.*)\",\s*city:\"(.*)\",\s*state:\"(.*)\",\s*country:\"(.*)\",\s*freq:\"(.*)\",\s*sql:\"(.*)\",\s*lat:\"(.*)\",\s*lon:\"(.*)\",\s*comment:\"(.*)}$",content, re.IGNORECASE)
                    if matches:
                        id = matches[1]
                        dfmf_id = matches[2]
                        call_sign = matches[3]
                        ana_dig = matches[4]
                        city = matches[5]
                        state = matches[6]
                        country = matches[7]
                        freq = matches[8]
                        sql = matches[9]
                        lat = matches[10]
                        lon = matches[11]
                        comment = matches[12]
                        if lat and lon and freq:
                            lat_deg = lat_min = lat_sec = lat_dir = lon_deg = lon_min = lon_sec = lon_dir = None
                            matches = re.search(r"^(N|S|E|W):(\d*)\s*(\d*)'\s*(\d*)&quot;$",lat, re.IGNORECASE)
                            if matches:
                                lat_dir = matches[1]
                                lat_deg = int(matches[2])
                                lat_min = int(matches[3])
                                lat_sec = int(matches[4])
                            matches = re.search(r"^(N|S|E|W):(\d*)\s*(\d*)'\s*(\d*)&quot;$",lon, re.IGNORECASE)
                            if matches:
                                lon_dir = matches[1]
                                lon_deg = int(matches[2])
                                lon_min = int(matches[3])
                                lon_sec = int(matches[4])
                            if lat_dir and lon_dir:
                                latitude, longitude = convert_dms_to_latlon(lat_deg,lat_min,lat_sec,lat_dir,lon_deg,lon_min,lon_sec,lon_dir)
                                print (city, latitude,longitude,freq)
                                counter += 1
    print (counter)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(module)s -%(levelname)s- %(message)s')
    get_ysf_repeater_list()