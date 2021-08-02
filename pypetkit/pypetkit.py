import hashlib
import json
import logging
import requests
import pytz

from datetime import datetime, time, timedelta

from .const import (
    API_SERVER_LIST_URL,
    API_LOGIN_PATH,
    API_DEVICE_PATH,
    API_FEEDERMINI_DEVICE_PATH,
    API_FEEDERMINI_HISTORY_PATH
)
from .device import PetKitDevice
from .history import PetKitHistory

_LOGGER = logging.getLogger(__name__)


class PetKitAPI:
    def __init__(self, user, password, country="AU", locale="en-AU", timezone="Australia/Melbourne", access_token=None):
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
        self._apiServerInfo = self.get_api_server_by_country(country)
        self._apiServerBaseURL = self._apiServerInfo['gateway']
        self.feeders = {}

    @property
    def is_authorized(self):
        return self._expiration_date > datetime.utcnow()

    def get_all_devices(self):
        """Populate all devices in the PetKit account."""
        if self.is_authorized == False:
            self.request_token()

        custom_headers = {
            'X-Session': self._access_token,
            "User-Agent": "PETKIT/7.26.1 (iPhone; iOS 14.7.1; Scale/3.00)",
            "X-Timezone": f"{round(self._tzone._utcoffset.seconds/60/60)}.0",
            "X-Api-Version": "7.26.1",
            "X-Img-Version": "1",
            "X-TimezoneId": self._tzone.zone,
            "X-Client": "ios(14.7.1;iPhone13,4)",
            "X-Locale": self._locale.replace("-", "_")
        }
        result = requests.get(self._apiServerBaseURL + API_FEEDERMINI_DEVICE_PATH, headers = custom_headers)
        
        try:
            for item in result.json()['result']:
                feeder = PetKitDevice(self._access_token, item, self._apiServerBaseURL)
                self.feeders[feeder.id] = feeder

        except (KeyError, TypeError) as err:
            _LOGGER.error(
                "Error requesting device from PetKit: {}".format(err)
            )

    def request_token(self):
        """Request access and refresh tokens from PetKit."""
        custom_headers = {
            "User-Agent": "PETKIT/7.26.1 (iPhone; iOS 14.7.1; Scale/3.00)",
            "X-Timezone": f"{round(self._tzone._utcoffset.seconds/60/60)}.0",
            "X-Api-Version": "7.26.1",
            "X-Img-Version": "1",
            "X-TimezoneId": self._tzone.zone,
            "X-Client": "ios(14.7.1;iPhone13,4)",
            "X-Locale": self._locale.replace("-", "_")
        }
        params = {
            "timezoneId": self._tzone.zone,
            "timezone": f"{round(self._tzone._utcoffset.seconds/60/60)}.0",
            "username": self._user,
            "password": self._password,
            "locale": self._locale,
            "encrypt": 1
        }

        result = requests.post(self._apiServerBaseURL + API_LOGIN_PATH, data=params, headers = custom_headers)

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
        ''' Retrieve list of API servers, preferable for different countries and save country API info. '''
        custom_headers = {
            "User-Agent": "PETKIT/7.26.1 (iPhone; iOS 14.7.1; Scale/3.00)",
            "X-Timezone": f"{round(self._tzone._utcoffset.seconds/60/60)}.0",
            "X-Api-Version": "7.26.1",
            "X-Img-Version": "1",
            "X-TimezoneId": self._tzone.zone,
            "X-Client": "ios(14.7.1;iPhone13,4)",
            "X-Locale": self._locale.replace("-", "_")
        }

        country_data = None  
        try:     
            result = requests.post(API_SERVER_LIST_URL, headers = custom_headers)
         
            result_json = result.json()
            country_data = next((item for item in result_json['result']['list'] if item["id"] == country), None)

            return country_data
        except:
            pass
        
        # If all else has failed, populate API server info with Australia values
        country_data = {
            "accountType": "email",
            "gateway": "http://api.petkt.com/latest/",
            "id": "AU",
            "name": "Australia"
        }
        return country_data