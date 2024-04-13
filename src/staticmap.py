#
# Multi-Purpose APRS Daemon: Generate a static
# image and indicate the user's coordinates on the map
# Author: Joerg Schultze-Lutter, 2020
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
import sys

import staticmaps
import io
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def render_png_map(
    aprs_latitude: float = None,
    aprs_longitude: float = None,
):
    """
    Render a static PNG image of the user's destination
    and add markers based on user's lat/lon data.
    Return the binary image object back to the user
    Parameters
    ==========
    aprs_latitude : 'float'
            APRS dynamic latitude (if applicable)
    aprs_longitude : 'float'
            APRS dynamic longitude (if applicable)

    Returns
    =======
    iobuffer : 'bytes'
            'None' if not successful, otherwise binary representation
            of the image
    """

    assert aprs_latitude, aprs_longitude

    # Create the object
    context = staticmaps.Context()
    context.set_tile_provider(staticmaps.tile_provider_OSM)

    # Add a green marker for the user's position
    marker_color = staticmaps.RED
    context.add_object(
        staticmaps.Marker(
            staticmaps.create_latlng(aprs_latitude, aprs_longitude),
            color=marker_color,
            size=12,
        )
    )

    # create a buffer as we need to write to write to memory
    iobuffer = io.BytesIO()

    try:
        # Try to render via pycairo - looks nicer
        if staticmaps.cairo_is_supported():
            image = context.render_cairo(800, 500)
            image.write_to_png(iobuffer)
        else:
            # if pycairo is not present, render via pillow
            image = context.render_pillow(800, 500)
            image.save(iobuffer, format="png")

        # reset the buffer position
        iobuffer.seek(0)

        # get the buffer value and return it
        view = iobuffer.getvalue()
    except Exception as ex:
        view = None

    return view


if __name__ == "__main__":
    render_png_map(aprs_latitude=52.5186729836, aprs_longitude=13.3704687765)
