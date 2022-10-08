from pypetkit import PetKitAPI
from settings import (
    API_USERNAME,
    API_PASSWORD,
    API_COUNTRY_CODE,
    API_LOCALE_CODE,
    API_TIMEZONE,
)

from pprint import pprint

petkit_api = PetKitAPI(
    API_USERNAME, API_PASSWORD, API_COUNTRY_CODE, API_LOCALE_CODE, API_TIMEZONE
)

petkit_api.request_token()

print(f"Authorized: {petkit_api.is_authorized}")

pprint(
    petkit_api.send_api_request(
        "d4/saveDailyFeed", params={"deviceId": 10019856, "amount": 10, "time": -1}
    )
)
