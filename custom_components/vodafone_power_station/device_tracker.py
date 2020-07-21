"""Support for Vodafone Power Station."""
import logging

from aiohttp.hdrs import CONTENT_TYPE
import datetime
import hashlib
import hmac
import html 
import re
import requests
import urllib.parse
import voluptuous as vol

from homeassistant.components.device_tracker import (
    DOMAIN,
    PLATFORM_SCHEMA,
    DeviceScanner,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string
    }
)

def get_scanner(hass, config):
    """Return the Vodafone Power Station device scanner."""
    scanner = VodafonePowerStationDeviceScanner(config[DOMAIN])

    return scanner if scanner.success_init else None

class VodafonePowerStationDeviceScanner(DeviceScanner):
    """This class queries a router running Vodafone Power Station firmware."""

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
        """Ensure the information from the Vodafone Power Station is up to date.

        Return boolean if scanning successful.
        """
        if not self.success_init:
            return False

        _LOGGER.debug("Loading data from Vodafone Power Station")
        data = self.get_router_data()
        if not data:
            return False

        active_clients = [client for client in data.values() if client["status"] == "on"]
        self.last_results = active_clients
        return True

    def get_router_data(self):
        """Retrieve data from Vodafone Power Station and return parsed result."""

        devices = {}

        try:
            s = requests.Session() # creates session to store cookies
            url = f"http://{self.host}/login.html"
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-GB,en;q=0.5',
                'Origin': f"http://{self.host}",
                'Referer': f"http://{self.host}/login.html",
                'DNT': '1'
                }

            r = s.get(url, headers=headers, timeout=10)
            m = re.search("(?<=csrf_token = ')[^']+", r.text)
            csrf = m.group(0)

            ts = datetime.datetime.now().strftime("%s")
            url = f"http://{self.host}/data/user_lang.json?_={ts}&csrf_token={csrf}"
            r = s.get(url, headers=headers, timeout=10)  

            j = r.json()
            user_obj = {}
            for item in j:
                key = list(item.keys())[0]
                val = list(item.values())[0]
                user_obj[key] = val

            salt = user_obj['salt']
            encryption_key = user_obj['encryption_key']

            hash1_pass = hmac.new(bytes('$1$SERCOMM$' , 'latin-1'), msg = bytes(self.password , 'latin-1'), digestmod = hashlib.sha256).hexdigest()
            user_password = hmac.new(bytes(encryption_key , 'latin-1'), msg = bytes(hash1_pass , 'latin-1'), digestmod = hashlib.sha256).hexdigest()

            cookie_obj = requests.cookies.create_cookie(domain=self.host,name='login_uid',value='1')
            s.cookies.set_cookie(cookie_obj)
            ts = datetime.datetime.now().strftime("%s")
            url = f"http://{self.host}/data/reset.json?_={ts}&csrf_token={csrf}"
            response = s.post(url,  headers=headers, timeout=10)

            payload = {'LoginName': 'vodafone', 'LoginPWD': user_password}

            ts = datetime.datetime.now().strftime("%s")
            url = f"http://{self.host}/data/login.json?_={ts}&csrf_token={csrf}"
            response = s.post(url, data=payload, headers=headers, timeout=10)

            ts = datetime.datetime.now().strftime("%s")
            url = f"http://{self.host}/data/overview.json?_={ts}&csrf_token={csrf}"

            response = s.get(url, headers=headers, timeout=10)
            _LOGGER.debug("Full Response: %s" % response.json())
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout,
        ):
            _LOGGER.info("No response from Vodafone Power Station")
            return devices
        kv_tuples = [(list(v.keys())[0], (list(v.values())[0])) for v in response.json()]
        kv = {}
        for entry in kv_tuples:
            kv[entry[0]] = entry[1]

        _LOGGER.debug("kv retrieved: %s" % kv)
        if "wifi_user" not in kv and "wifi_guest" not in kv and "ethernet" not in kv:
            _LOGGER.info("No device in response from Vodafone Power Station")
            return devices

# 'on|smartphone|Telefono Nora (2.4GHz)|00:0a:f5:6d:8b:38|192.168.1.128;'
        arr_devices = []
        arr_wifi_user = kv["wifi_user"].split(';')
        arr_wifi_user = filter(lambda x : x.strip() != '', arr_wifi_user)
        arr_wifi_guest = kv["wifi_guest"].split(';')
        arr_wifi_guest = filter(lambda x : x.strip() != '', arr_wifi_guest)
        arr_devices.append(arr_wifi_user)
        arr_devices.append(arr_wifi_guest)
        arr_ethernet = [dev for dev in kv["ethernet"].split(';')]
        arr_ethernet = filter(lambda x : x.strip() != '', arr_ethernet)
        arr_ethernet = ['on|' + dev for dev in arr_ethernet]
        arr_devices.append(arr_ethernet)
        arr_devices = [item for sublist in arr_devices for item in sublist]
        _LOGGER.debug("Arr_devices: %s" % arr_devices)

        for device_line in arr_devices:
            device_fields = device_line.split('|')
            try:
                devices[device_fields[2]] = {
                    "ip": device_fields[4],
                    "mac": device_fields[3],
                    "status": device_fields[0],
                    "name": device_fields[2]
                }
            except (KeyError, requests.exceptions.RequestException,IndexError):
                _LOGGER.warn("Error processing line: %s" % device_line)

        return devices
