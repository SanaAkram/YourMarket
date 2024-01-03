import requests
from datetime import datetime, timedelta
import time

API_URL = "http://127.0.0.1:8000/customer/cm_data/{}/{}/{}/"


class QSRJob:
    @classmethod
    def hit_api_for_month(cls, start_date, month, end_date):

        api_endpoint = API_URL.format(start_date, end_date, month)
        try:
            response = requests.get(api_endpoint)
            if response.status_code == 200:
                print(f"API request successful for {start_date} - {end_date}")
                print("Response content:")
                print(response.content.decode("utf-8"))
            else:
                print(f"API request failed for {start_date} - {end_date}. Status code: {response.status_code}")

        except Exception as e:
            print(f"Error occurred: {e}")
