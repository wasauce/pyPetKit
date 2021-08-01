import hashlib
import json
import logging
import requests
import pytz

from datetime import datetime, time, timedelta

from .const import (
    API_LOGIN_URL,
    API_FEEDERMINI_DEVICE_URL,
    API_SERVER_LIST_URL
)
from .device import PetKitDevice
from .history import PetKitHistory

_LOGGER = logging.getLogger(__name__)


class PetKitAPI:
    def __init__(self, user, password, country = "AU", locale = "en-AU", timezone="Australia/Melbourne", access_token=None):
        """ Initialize PetKit API """
        hash = hashlib.md5()
        hash.update(password.encode('utf-8'))
        self._user = user
        self._password = hash.hexdigest()
        self._country = country
        self._locale = locale
        self._tzone = pytz.timezone(timezone)
        self._access_token = access_token
        self._expiration_date = datetime.utcnow()
        self.feeders = {}

    @property
    def is_authorized(self):
        return self._expiration_date > datetime.utcnow()

    def get_all_devices(self):
        """Populate all devices in the PetKit account."""
        if self.is_authorized == False:
            self.request_token()
        
        result = requests.get(
            API_FEEDERMINI_DEVICE_URL,
            headers={'X-Session': self._access_token}
        )
        try:
            for item in result.json()['result']:
                feeder = PetKitDevice(self._access_token, item)
                self.feeders[feeder.id] = feeder

        except (KeyError, TypeError) as err:
            _LOGGER.error(
                "Error requesting device from PetKit: {}".format(err)
            )

    def request_token(self):
        """Request access and refresh tokens from PetKit."""
        headers = {
            "User-Agent": "PETKIT/7.26.1 (iPhone; iOS 14.7.1; Scale/3.00)",
            "X-Timezone": f"{round(self._tzone._utcoffset.seconds/60/60)}.0",
            "X-Api-Version": "7.26.1",
            "X-Img-Version": "1",
            "X-TimezoneId": self._tzone.zone,
            "X-Client": "ios(14.7.1;iPhone13,4)",
            "X-Locale": "en_US"
        }
        params = {
            "timezoneId": self._tzone.zone,
            "timezone": f"{round(self._tzone._utcoffset.seconds/60/60)}.0",
            "username": self._user,
            "password": self._password,
            "locale": self._locale,
            "source": "app.petkit-ios-oversea",
            "platform": "ios",
            "version": "14.7.1",
            "name": "iPhone13,4",
            "encrypt": 1,
        }

        result = requests.post(API_LOGIN_URL, data=params, headers=headers)
        try:
            createdAt = datetime.strptime(
                result.json()['result']['session']['createdAt'],
                '%Y-%m-%dT%H:%M:%S.%fZ'
            )
            self._access_token = result.json()['result']['session']['id']
            self._expiration_date = createdAt + timedelta(
                seconds=result.json()['result']['session']['expiresIn']
            )
            _LOGGER.debug(
                "Obtained access token {} and expiration datetime {}".format(
                    self._access_token, self._expiration_date
                )
            )
        except (KeyError, TypeError) as err:
            _LOGGER.error("Error requesting token from PetKit: {}".format(err))

    def get_token(self):
        return self._access_token
    
    def get_sensors(self):
        return self.feeders

    def get_api_server_by_country(self, country="AU"):
        headers = {
            "User-Agent": "PETKIT/7.26.1 (iPhone; iOS 14.7.1; Scale/3.00)",
            "X-Timezone": f"{round(self._tzone._utcoffset.seconds/60/60)}.0",
            "X-Api-Version": "7.26.1",
            "X-Img-Version": "1",
            "X-TimezoneId": self._tzone.zone,
            "X-Client": "ios(14.7.1;iPhone13,4)",
            "X-Locale": "en_US"
        }   
        try:     
            result = requests.post(API_SERVER_LIST_URL, headers=headers)
         
            result_json = result.json()
            country_data = next((item for item in result_json['result']['list'] if item["id"] == country), None)

            return country_data
        except:
            pass

        return None