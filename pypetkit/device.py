import json
import requests

from datetime import datetime
from .schedule import PetKitSchedule
from .history import PetKitHistory
from .const import *

class PetKitDevice:
    def __init__(self, token, sensor, apiServerUrl = 'http://api.petkt.com/latest/'):
      self._access_token = token
      self._sensor = sensor
      self._sensor["schedule"] = {}
      self._apiServerBaseURL = apiServerUrl
      for sh in sensor["feed"]["items"]:
          shd = PetKitSchedule(sh)
          self._sensor["schedule"][sh["id"]] = shd
      self.get_history(datetime.now().strftime("%Y%m%d"))

    @property
    def id(self):
        return self._sensor["id"]

    @property
    def name(self):
        return self._sensor["name"]

    @property
    def type(self):
        return self._sensor["type"]

    @property
    def batteryPower(self):
        return self._sensor["state"]["batteryPower"]

    @property
    def batteryStatus(self):
        return self._sensor["state"]["batteryStatus"]

    @property
    def desiccantLeftDays(self):
        return self._sensor["state"]["desiccantLeftDays"]

    @property
    def food(self):
        return self._sensor["state"]["food"] == 1

    @property
    def feeding(self):
        return self._sensor["state"]["feeding"] == 1

    @property
    def schedule(self):
        return self._sensor["schedule"]

    @property
    def history(self):
        return self._sensor["history"]

    def get_history(self, day):
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

        params = {
            "deviceId": self._sensor["id"],
            "days": day
        }
        result = requests.post(
            self._apiServerBaseURL + API_FEEDERMINI_HISTORY_PATH, data = params, headers = custom_headers)
        try:
            self._sensor["history"] = []
            for item in result.json()['result']:
                for history in item['items']:
                  self._sensor["history"].append(PetKitHistory(history))

        except (KeyError, TypeError) as err:
            _LOGGER.error(
                "Error requesting history from PetKit: {}".format(err)
            )
