#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
https://ahe.atino.net/api/devices
https://ahe.atino.net/api/reminder
https://ahe.atino.net/api/pickup-schedule

af81be7b-95d2-4770-baa5-d87428fc0008

{
    "city": "",
    "houseNumber": "",
    "postalCode": "",
    "street": ""
}
"""

import logging
from homeassistant.const import (
    CONF_NAME, CONF_VALUE_TEMPLATE,
    STATE_UNKNOWN)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
import voluptuous as vol
import urllib.request
import json
from datetime import datetime
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

DATE_FORMAT = '%Y-%m-%d'
AHE_HOST = 'https://ahe.atino.net/api'
STATE_NONE = 'Keine'

CONF_CITY = 'city'
CONF_STREET = 'street'
CONF_HOUSE_NUMBER = 'house_number'
CONF_ZIP = 'zip'
CONF_TARGET_DAY = 'target_day'

_QUERY_SCHEME = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_STREET): cv.string,
    vol.Required(CONF_HOUSE_NUMBER): cv.string,
    vol.Required(CONF_ZIP): cv.string,
    vol.Required(CONF_CITY): cv.string,
    vol.Optional(CONF_TARGET_DAY): cv.string,
    vol.Optional(CONF_VALUE_TEMPLATE): cv.template
})

def setup_platform(
    hass,
    config,
    add_devices,
    discovery_info=None
    ):
    """Setup the sensor platform."""
    value_template = config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        value_template.hass = hass

    add_devices([AheSensor(config.get(CONF_NAME), config.get(CONF_CITY), config.get(CONF_STREET), config.get(CONF_HOUSE_NUMBER), config.get(CONF_ZIP), config.get(CONF_TARGET_DAY), value_template)])

class AheSensor(Entity):

    """Representation of a Sensor."""
    def __init__(self, name, city, street, houseNumber, zip, day, value_template):
        """Initialize the sensor."""
        self._name = name
        self._street = street 
        self._city = city 
        self._houseNumber = houseNumber
        self._zip = zip
        self._day = day
        self._value_template = value_template
        self._state = STATE_UNKNOWN
        self._attributes = None
        headers = {"client": "af81be7b-95d2-4770-baa5-d87428fc0008"}
        values = {
            'city': city,
            'houseNumber': houseNumber,
            'postalCode': zip,
            'street': street
        }
        try:
            req = urllib.request.Request(AHE_HOST + "/devices")
            req.add_header('Content-Type', 'application/json')            
            req.add_header('client', 'af81be7b-95d2-4770-baa5-d87428fc0008')
            _LOGGER.info(json.dumps(values).encode('utf-8'))
            with urllib.request.urlopen(req, json.dumps(values).encode('utf-8')) as response:
                    value_json = json.loads(response.read().decode())
                    self._myId = value_json['id']
        except Exception as e:
          _LOGGER.error('API call error' + e)
          return

        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return None

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        day = datetime.now() + timedelta(days=(0 if self._zip == 'today' else 1))
        dayInDelta = day + timedelta(days=30)

        try:
          req = urllib.request.Request(AHE_HOST + '/pickup-schedule')
          req.add_header('device', self._myId)
          with urllib.request.urlopen(req) as url:
              value_json = json.loads(url.read().decode())
              _LOGGER.info(value_json)
        except Exception as e:
          _LOGGER.error('API call error' + e)
          return

        trashdates = value_json
        attributes = {}
        attributes.update({'id': self._myId})
        for trashdate in trashdates:
            print(trashdate)
            dayDate = datetime.strptime(trashdate['nextDates'][0], DATE_FORMAT)
            typ = trashdate['bin']['name']
            existingTyp = attributes.get(dayDate.strftime(DATE_FORMAT))
            if existingTyp is not None:
              typ = typ + ', ' + existingTyp
            attributes.update({dayDate.strftime(DATE_FORMAT): typ})
        
        attributes.update({'Zuletzt aktualisiert': datetime.now().strftime(DATE_FORMAT + ' %H:%M:%S')})
        data = attributes.get(day.strftime(DATE_FORMAT), "Keine")

        if self._value_template is not None:
            self._state = self._value_template.async_render_with_possible_json_value(
                data, None)
        else:
            self._state = data

        self._attributes = dict(sorted(attributes.items()))
