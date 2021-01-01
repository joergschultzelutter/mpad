# Daytime settings

MPAD is able to understand the following keywords:

- __full__. Returns all data for the given day (program default)

- Morning (Keywords: __morn__, __morning__)

- Daytime (Keywords: __day__, __daytime__, __noon__)

- Evening (Keywords: __eve__, __evening__)

- Night (Keywords: __nite__, __night__, __tonite__, __tonight__)


All references are to UTC time zone settings.

Whereas noted for the respective [action keyword](action_commands_.md), these daytime setting keywords (and also the [date](date_keywords.md) setting keywords) can be combined with the action keywords. Examples:

```
San Francisco, CA tomorrow full --> returns a full wx report for location 'San Francisco' and date setting 'tomorrow'
satpass iss friday morning --> returns the first pass of the ISS on Friday morning
riseset thursday --> returns sunrise/sunset and moonrise / moonset values for Thursday.
```
