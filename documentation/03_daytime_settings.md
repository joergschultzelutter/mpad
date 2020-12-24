# Daytime settings

MPAD is able to understand the following keywords:

- __full__. Returns all data for the given day (program default)

- Morning (Keywords: __morn__, __morning__)

- Daytime (Keywords: __day__, __daytime__, __noon__)

- Evening (Keywords: __eve__, __evening__)

- Night (Keywords: __nite__, __night__, __tonite__, __tonight__)


All references are to UTC time zone settings.

Whereas noted for the respective [action keyword](01_actions.md), these daytime setting keywords (and also the [date](02_date_settings.md) setting keywords) can be combined with the action keywords. Examples:

```
San Francisco, CA tomorrow --> returns a wx report for location 'San Francisco' and date setting 'tomorrow'
satpass iss fri --> returns the first pass of the ISS on Friday
riseset thursday --> returns sunrise/sunset and moonrise / moonset values for Thursday.
```
