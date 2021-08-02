import datetime

from pypetkit import PetKitAPI, schedule
from demo_settings import (API_USERNAME, API_PASSWORD, API_COUNTRY_CODE, API_LOCALE_CODE, API_TIMEZONE)

from pprint import pprint

petkit_api = PetKitAPI(API_USERNAME, API_PASSWORD, API_COUNTRY_CODE, API_LOCALE_CODE, API_TIMEZONE)

#server_info_json = petkit_api.get_api_server_by_country(API_COUNTRY_CODE)
#pprint(server_info_json)

petkit_api.request_token()
petkit_api.get_all_devices()

feeders = petkit_api.get_sensors()

pprint(feeders)

pass