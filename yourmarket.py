import json
import requests
from datetime import datetime, timedelta
from selenium.common import NoSuchElementException, TimeoutException
import csv
import re
from webdriver_manager.chrome import ChromeDriverManager
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import psycopg2
from yourmarket_db_config import DB_CONFIG

TABLE_NAME = 'customer_details'
api_key = "1CFE6FD1F558C7B412B63A7FA8A2F"

headers = {
    "Content-Type": "application/json",  # Adjust content type based on API requirements
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    "key": api_key
}

current_day = str(datetime.now().date()).replace('-', '_')

BASE_URL = "https://cpapp.azurewebsites.net/CustomerPortalAPI/api/reports/"
customer_summary_detail_report_url = "customersummarydetailreport"
booking_summary_report_url = "bookingsummaryreport"
qsr_report_url = "qsrreport"
customer_address_url = "https://cpapp.azurewebsites.net/CustomerPortalAPI/api/booking/GetCustomerInfo?phoneno="
customer_phone_url = "ConsigneeProfileReport"

login_url = 'https://mnpcourier.com/cplight/login'

# Chrome Setup
# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--disable-gpu")
# chrome_options.add_argument("--disable-blink-features=AutomationControlled")
# chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
# chrome_options.add_experimental_option("useAutomationExtension", False)
# # chrome_options.add_argument("--headless")
# chrome_options.add_argument(f"user-agent={headers['User-Agent']}")
#
# # Install ChromeDriver and use it
# driver_path = ChromeDriverManager().install()
# service = Service(executable_path=driver_path)
# driver = webdriver.Chrome(service=service, options=chrome_options)
# driver.get(login_url)
# driver.find_element(By.XPATH, '//*[@id="app"]/section/div/div/div/div[2]/form/div/div[1]/input').send_keys(
#     "mubeen_12y13")
# driver.find_element(By.XPATH, '//*[@id="app"]/section/div/div/div/div[2]/form/div/div[2]/input'). \
#     send_keys("Mubeen@123")
# login_button = driver.find_element(By.XPATH, '//*[@id="app"]/section/div/div/div/div[2]/form/div/div[4]/button')
# login_button.click()
# time.sleep(8.5)
#
# # Close that New Button
# close = driver.find_element(By.XPATH, '//*[@id="myModal"]/div/div[1]/button')
# close.click()
# print("Logged In  !")

print("Note: Start/End Date should not exceed 30 days limit !")
# start_date = input("Enter Start Date YYYY-MM-DD: ")
start_date = '2023-11-18'
# end_date = input("Enter End Date YYYY-MM-DD: ")
end_date = '2023-12-18'
# month = input("Enter Month MM: ")
month = '12'
# month_wise = input("Should be month wise or not?")

c_data = {
    "isMonthWise": False,
    "StartDate": start_date,
    "EndDate": end_date,
    "Year": "2023",
    "Month": month,
    "account": "12Y13",
    "creditclientid": "",
    "locationID": '30524',
    "reporttype": "received"
}


all_data = []


def get_api_response(url, payload):
    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json().get('data', [])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []


def get_api_GET_response(url):
    response = requests.get(url, headers=headers)
    try:
        return response.json().get('data', [])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []
def create_url(base_url, endpoint):
    return f"{base_url}{endpoint}"


def get_booking_summary_payload(start_date, end_date, month):
    return {
        "account": '12Y13',
        "status": "3",
        "consignee": "",
        "consigneePhone": "",
        "destinationCity": "",
        "from": start_date,
        "to": end_date,
        "locationId": ["30524"],
    }


def get_customer_number_payload(start_date, end_date):
    return {
        "account": ["12Y13"],
        "StartDate": start_date,
        "EndDate": end_date,
    }


def get_qsr_payload(start_date, end_date, month):
    return {
        "isMonthWise": False,
        "StartDate": start_date,
        "EndDate": end_date,
        "Year": "2023",
        "Month": month,
        "account": ["12Y13"],
        "creditclientid": "",
        "locationID": ["30524"],
        "reporttype": "received"
    }


def get_number_payload(number):
    return{
    "phoneno": number
}


def fetch_data(start_date, end_date, month):
    customer_summary_endpoint = create_url(BASE_URL, customer_summary_detail_report_url)
    customer_summary_data = get_api_response(customer_summary_endpoint, c_data)

    booking_summary_endpoint = create_url(BASE_URL, booking_summary_report_url)
    booking_summary_data = get_api_response(booking_summary_endpoint,
                                            get_booking_summary_payload(start_date, end_date, month))

    qsr_endpoint = create_url(BASE_URL, qsr_report_url)
    qsr_data = get_api_response(qsr_endpoint, get_qsr_payload(start_date, end_date, month))

    customer_phone_url_endpoint = create_url(BASE_URL, customer_phone_url)
    number_details = get_api_response(customer_phone_url_endpoint, get_customer_number_payload(start_date, end_date))

    all_data = []

    for csd in customer_summary_data:
        consignment_no = csd['consignmentNumber']
        address = next((bsd['consigneeAddress'] for bsd in booking_summary_data if bsd['cn'] == consignment_no), '')
        number = next((bsd['consigneePhoneNo'] for bsd in booking_summary_data if bsd['cn'] == consignment_no), '')
        if number == '':
            number = next((num['contact'] for num in number_details if num['detail'][0]['consignmentNumber'] == consignment_no), '')
        if address == '' and number:
            customer_info = get_api_GET_response(customer_address_url+number)
            if customer_info:
                address = customer_info['address']
        qsr_item = next((q for q in qsr_data if q['consignmentNumber'] == consignment_no), {})
        status = qsr_item.get('RRStatus', '')
        payment_id = qsr_item.get('paymentId', '')
        total_amount = int(qsr_item.get('totalAmount', 0))
        gst = int(qsr_item.get('GST', 0))
        charges = total_amount + gst
        attempts = qsr_item.get('Attempts', '')
        delivery_date = qsr_item.get('deliveryDate', '')

        data = {
            "consignment_no": consignment_no,
            "consignee": csd['consignee'],
            'consignee_address': address,
            'consignee_number': number,
            'booking_date': csd['BookingDate'],
            'destination_branch': csd['DestBranch'],
            'pieces': csd['pieces'],
            'weight': csd['weight'],
            'COD_amount': csd['codAmount'],
            'Status': status,
            'Delivery_date': delivery_date,
            'Total_Charges': charges,
            'Attempts': attempts,
            'productDescription': csd['productDescription'],
            'Payment_ID': payment_id
        }
        all_data.append(data)

    return all_data


class DataModel:
    def __init__(self, consignment_no, consignee, consignee_address, consignee_number,
                 booking_date, destination_branch, pieces, weight, COD_amount,
                 Status, Delivery_date, Total_Charges, Attempts, productDescription, Payment_ID):
        self.consignment_no = consignment_no
        self.consignee = consignee
        self.consignee_address = consignee_address
        self.consignee_number = consignee_number
        self.booking_date = booking_date
        self.destination_branch = destination_branch
        self.pieces = pieces
        self.weight = weight
        self.COD_amount = COD_amount
        self.Status = Status
        self.Delivery_date = Delivery_date
        self.Total_Charges = Total_Charges
        self.Attempts = Attempts
        self.productDescription = productDescription
        self.Payment_ID = Payment_ID


def create_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS {} (
            consignment_no TEXT PRIMARY KEY,
            consignee TEXT,
            consignee_address TEXT,
            consignee_number TEXT,
            booking_date TEXT,
            destination_branch TEXT,
            pieces INTEGER,
            weight REAL,
            COD_amount REAL,
            Status TEXT,
            Delivery_date TEXT,
            Total_Charges REAL,
            Attempts TEXT,
            productDescription TEXT,
            Payment_ID TEXT
        )
    '''.format(TABLE_NAME))


def insert_data(cursor, data):
    cursor.executemany('''
        INSERT INTO {} (
            consignment_no, consignee, consignee_address, consignee_number,
            booking_date, destination_branch, pieces, weight, COD_amount,
            Status, Delivery_date, Total_Charges, Attempts, productDescription, Payment_ID
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (consignment_no) DO UPDATE
        SET
            consignee = EXCLUDED.consignee,
            consignee_address = EXCLUDED.consignee_address,
            consignee_number = EXCLUDED.consignee_number,
            booking_date = EXCLUDED.booking_date,
            destination_branch = EXCLUDED.destination_branch,
            pieces = EXCLUDED.pieces,
            weight = EXCLUDED.weight,
            COD_amount = EXCLUDED.COD_amount,
            Status = EXCLUDED.Status,
            Delivery_date = EXCLUDED.Delivery_date,
            Total_Charges = EXCLUDED.Total_Charges,
            Attempts = EXCLUDED.Attempts,
            productDescription = EXCLUDED.productDescription,
            Payment_ID = EXCLUDED.Payment_ID
    '''.format(TABLE_NAME), data)



def main():
    # Chrome setup and login code...

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Create table if not exists
    create_table(cursor)

    all_data = fetch_data(start_date, end_date, month)



    # Batch insert data
    data_to_insert = [(d['consignment_no'], d['consignee'], d['consignee_address'], d['consignee_number'],
                       d['booking_date'], d['destination_branch'], d['pieces'], d['weight'], d['COD_amount'],
                       d['Status'], d['Delivery_date'], d['Total_Charges'], d['Attempts'], d['productDescription'],
                       d['Payment_ID']) for d in all_data]

    insert_data(cursor, data_to_insert)
    # Commit and close the connection
    conn.commit()
    conn.close()

    print("Data inserted successfully!")


if __name__ == '__main__':
    main()
