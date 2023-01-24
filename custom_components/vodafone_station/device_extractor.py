from requests import Session
import hashlib
import time

#            requests.exceptions.ConnectionError,
#            requests.exceptions.Timeout,
            #requests.exceptions.ConnectTimeout,

class DeviceExtractor:
    def __init__(self, router_address: str, username: str, password: str):
        self.router_address = router_address
        self.username = username
        self.password = password

        self.session = Session()
        self.log = logging.getLogger("device_extractor")
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-CSRF-TOKEN": "",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": router_address,
        }

    def extract_devices(self):
        session = self.session

        # Get salt for login
        self.log.debug("Get salt for login")
        response = session.post(
            self.router_address + "/api/v1/session/login",
            headers=self.headers,
            data={"username": self.username, "password": "seeksalthash"},
        )
        if response.status_code != 200:
            self.log.error("Error to retrieve salt")
            self.log.error(response.text)
            return None
        salt_response = response.json()

        # Calculate hash
        self.log.debug("Calculate hash")
        a = hashlib.pbkdf2_hmac(
            "sha256",
            bytes(self.password, "utf-8"),
            bytes(salt_response["salt"], "utf-8"),
            1000,
        ).hex()[:32]
        b = hashlib.pbkdf2_hmac(
            "sha256",
            bytes(a, "utf-8"),
            bytes(salt_response["saltwebui"], "utf-8"),
            1000,
        ).hex()[:32]

        # Perform login
        self.log.debug("Perform login")
        response = session.post(
            self.router_address + "/api/v1/session/login",
            headers=self.headers,
            data={"username": username, "password": b},
        )
        login_response = response.json()
        if (
            response.status_code != 200
            or "error" in login_response
            and login_response["error"] == "error"
        ):
            self.log.error("Error during login")
            if login_response["message"] == "MSG_LOGIN_150":
                self.log.error("Another user is already logged in")
            self.log.error(response.text)
            return None
        self.log.debug(response.text)

        # Request menu
        self.log.debug("Get menu")
        now = int(time.time() * 1000)
        response = session.get(
            self.router_address + "/api/v1/session/menu?_=" + str(now),
            headers=self.headers,
        )
        if response.status_code != 200:
            self.log.error("Error during menu")
            self.log.error(response.text)
            return None

        # Get associated devices
        self.log.debug("Get associated devices")
        self.log.debug("Cookie: ")
        self.log.debug(self.session.cookies.get_dict())

        now = int(time.time() * 1000)
        response = session.get(
            self.router_address + "/api/v1/host/AssociatedDevices5?_=" + str(now),
            headers=self.headers,
        )
        if response.status_code != 200:
            self.log.error("Error during Associated Devices")
            self.log.error(response.text)
            return None
        self.log.debug(response.text)
        devices = response.json()["data"]["AssociatedDevices5"]
        for device in devices:
            yield device["macAddr"]

    def logout(self):
        # Logout
        # headers['X-CSRF-TOKEN'] = response.json()['token']
        self.log.debug("Logout")
        response = self.session.post(
            self.router_address + "/api/v1/session/logout", headers=self.headers
        )
        if response.status_code != 200:
            self.log.error("Error during logout")
            self.log.error(response.text)


if __name__ == "__main__":
    import os
    import logging

    FORMAT = "%(asctime)s [%(name)s] [%(levelname)-5.8s]  %(message)s"
    logging_formatter = logging.Formatter(FORMAT, "%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging_formatter)

    logging.basicConfig(level=logging.INFO, handlers=[console_handler])

    username = os.getenv("VODAFONE_USERNAME")
    password = os.getenv("VODAFONE_PASSWORD")
    router_address = "http://192.168.0.1"
    de = DeviceExtractor(
        router_address=router_address, username=username, password=password
    )
    devices = de.extract_devices()
    if devices:
        for device in devices:
            logging.info(device)

    de.logout()
