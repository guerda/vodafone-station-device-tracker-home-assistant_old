"""Support for Vodafone Station."""
import datetime
import hashlib
import hmac
import html
import logging
import re
import urllib.parse

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from aiohttp.hdrs import CONTENT_TYPE
from homeassistant.components.device_tracker import (
    DOMAIN,
    PLATFORM_SCHEMA,
    DeviceScanner,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


def get_scanner(hass, config):
    """Return the Vodafone  Station device scanner."""
    scanner = VodafoneStationDeviceScanner(config[DOMAIN])

    return scanner if scanner.success_init else None


class VodafoneStationDeviceScanner(DeviceScanner):
    """This class queries a router running Vodafone Station firmware."""

    def __init__(self, config):
        """Initialize the scanner."""
        self.host = config[CONF_HOST]
        self.username = config[CONF_USERNAME]
        self.password = config[CONF_PASSWORD]
        self.password = urllib.parse.quote(self.password)
        self.password = html.unescape(self.password)
        self.last_results = {}

        # Test the router is accessible.
        data = self.get_router_data()
        self.success_init = data is not None

    def scan_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        self._update_info()
        return [client["mac"] for client in self.last_results]

    def get_device_name(self, device):
        """Return the name of the given device or None if we don't know."""
        if not self.last_results:
            return None
        for client in self.last_results:
            if client["mac"] == device:
                return client["name"]
        return None

    def _update_info(self):
        """Ensure the information from the Vodafone Station is up to date.

        Return boolean if scanning successful.
        """
        if not self.success_init:
            return False

        _LOGGER.debug("Loading data from Vodafone Station")
        data = self.get_router_data()
        if not data:
            return False

        active_clients = [
            client for client in data.values() if client["status"] == "on"
        ]
        self.last_results = active_clients
        return True

    def get_router_data(self):
        """Retrieve data from Vodafone Station and return parsed result."""

        devices = {}

        #_LOGGER.debug("kv retrieved: %s" % kv)
        #if "wifi_user" not in kv and "wifi_guest" not in kv and "ethernet" not in kv:
        #    _LOGGER.info("No device in response from Vodafone Station")
        #    return devices

        #        devices[device_fields[2]] = {
        #            "ip": device_fields[4],
        #            "mac": device_fields[3],
        #            "status": device_fields[0],
        #            "name": device_fields[2],
        
        return devices
