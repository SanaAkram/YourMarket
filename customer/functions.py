from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

import requests

from yourmarket.settings import DEFAULT_FROM_EMAIL, EMAIL_TO, EMAIL_HOST_PASSWORD
import subprocess
import time
from datetime import datetime, timedelta


def send_email(email_body, subject):
    msg = MIMEMultipart()
    msg['From'] = DEFAULT_FROM_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(email_body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(DEFAULT_FROM_EMAIL, EMAIL_HOST_PASSWORD)
            server.sendmail(DEFAULT_FROM_EMAIL, EMAIL_TO, msg.as_string())
        print('Email sent successfully.')

    except Exception as e:
        print('Error:', str(e))


def create_qsr_report_body(data):
    body = (
        "Dear recipient,\n\n"
        "Here is the QSR report of Your Market:\n\n"
    )

    for item in data:
        for product, details in item.items():
            body += f"{product}:\n"
            for key, value in details.items():
                body += f"  {key}: {value}\n"
            body += "\n"

    body += (
        "\nThank you for using Your Market services. If you have any questions, "
        "please feel free to contact us.\n\nBest regards,\nYour Market Team"
    )

    return body


def start_server():
    try:
        with open("server_log.txt", "w") as log_file:
            server_process = subprocess.Popen(["python", "manage.py", "runserver"], stdout=log_file, stderr=log_file)
            print("Django server started. PID:", server_process.pid)
        time.sleep(3)
        return server_process
    except subprocess.CalledProcessError as e:
        print(f"Error starting Django server: {e}")


def is_server_running():
    try:
        # Check if the server is reachable by making a request
        response = requests.get("http://127.0.0.1:8000/")
        return response.status_code == 200
    except OSError as e:
        # Access errno using .args
        error_number = e.args[0]

        # Handle the error based on the error number
        if error_number == 2:
            print("File not found.")
        elif error_number == 13:
            print("Permission denied.")
        else:
            print(f"OSError with errno {error_number}: {e}")


# Wait for the server to start
def wait_for_server():
    max_attempts = 30
    attempts = 0

    while not is_server_running() and attempts < max_attempts:
        time.sleep(1)
        attempts += 1

    if is_server_running():
        print("Server is running.")
    else:
        print("Timeout: Unable to verify if the server is running.")


def create_email_body(shipments):
    email_body = """
Dear Mubeen,

I hope this email finds you well. We wanted to provide you with an update on recent shipments. Below is a summary of the latest consignments:

"""

    for shipment in shipments:
        email_body += f"""{shipment['consignment_no']}
   - Consignee: {shipment['consignee']}
   - Address: {shipment['consignee_address']}
   - Consignee Number: {shipment['consignee_number']}
   - Booking Date: {shipment['booking_date']}
   - Destination Branch: {shipment['destination_branch']}
   - Weight: {shipment['weight']} kg
   - Items: {shipment['pieces']} 
   - COD Amount: Rs. {shipment['cod_amount']} 
   - Status: {shipment['status']}
   - Delivery Date: {shipment['delivery_date']}
   - Total Charges: Rs. {shipment['total_charges']:.2f}

"""

    email_body += """
Please let us know if you need any further information or assistance.

Best regards,
Your Market
"""

    return email_body