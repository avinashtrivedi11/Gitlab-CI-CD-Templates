import requests
import os

UTILITY_APIS_BASE_URL = os.environ['UTILITY_APIS_BASE_URL']
COMPANY_ID = os.environ['COMPANY_ID']

db_setting_url = UTILITY_APIS_BASE_URL + "/api/utility_service/db_settings_configuration"
db_setting_response = requests.get(url=db_setting_url)
db_setting_resp = db_setting_response.json()

for key in db_setting_resp.keys():
    if key != "default":
        print(key)
