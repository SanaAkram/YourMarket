from datetime import datetime
# from .serializers import CustomerSerializer
from .models import Customer_Details, Product_details
import requests
import json
from django.db.models import CharField
from yourmarket.authenticate_code import auth_check
from django.db.models import F
from django.core.mail import send_mail, EmailMessage
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tabulate import tabulate
import smtplib


class Customer_DataAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, start_date, end_date, month):
        # auth_check(self)
        api_key = "1CFE6FD1F558C7B412B63A7FA8A2F"
        headers = {
            "Content-Type": "application/json",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            "key": api_key
        }

        BASE_URL = "https://cpapp.azurewebsites.net/CustomerPortalAPI/api/reports/"
        customer_summary_detail_report_url = "customersummarydetailreport"
        booking_summary_report_url = "bookingsummaryreport"
        qsr_report_url = "qsrreport"
        payment_report_url = "paymentinstrumentreport"
        customer_address_url = "https://cpapp.azurewebsites.net/CustomerPortalAPI/api/booking/GetCustomerInfo?phoneno="
        customer_phone_url = "ConsigneeProfileReport"

        c_data = {
            "isMonthWise": False,
            "StartDate": start_date,
            "EndDate": end_date,
            "Year": str(datetime.now().year),
            "Month": month,
            "account": "12Y13",
            "creditclientid": "",
            "locationID": '30524',
            "reporttype": "received"
        }

        def get_api_GET_response(url):
            response = requests.get(url, headers=headers)
            try:
                return response.json().get('data', [])
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return []

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

        def get_api_response(url, payload):
            response = requests.post(url, headers=headers, json=payload)
            try:
                return response.json().get('data', [])
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return []

        def create_url(base_url, endpoint):
            return f"{base_url}{endpoint}"

        def fetch_data(start_date, end_date, month):
            customer_summary_endpoint = create_url(BASE_URL, customer_summary_detail_report_url)
            customer_summary_data = get_api_response(customer_summary_endpoint, c_data)

            booking_summary_endpoint = create_url(BASE_URL, booking_summary_report_url)
            booking_summary_data = get_api_response(booking_summary_endpoint,
                                                    get_booking_summary_payload(start_date, end_date, month))

            qsr_endpoint = create_url(BASE_URL, qsr_report_url)
            qsr_data = get_api_response(qsr_endpoint, get_qsr_payload(start_date, end_date, month))

            customer_phone_url_endpoint = create_url(BASE_URL, customer_phone_url)
            number_details = get_api_response(customer_phone_url_endpoint,
                                              get_customer_number_payload(start_date, end_date))

            all_data = []

            for csd in customer_summary_data:
                consignment_no = csd['consignmentNumber']
                address = next((bsd['consigneeAddress'] for bsd in booking_summary_data if bsd['cn'] == consignment_no),
                               '')
                number = next(
                    (bsd['consigneePhoneNo'] for bsd in booking_summary_data if bsd['cn'] == consignment_no), '')
                if number == '':
                    number = next(
                        (num['contact'] for num in number_details if
                         num['detail'][0]['consignmentNumber'] == consignment_no),
                        '')
                if address == '' and number:
                    customer_info = get_api_GET_response(customer_address_url + number)
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
                parsed_date = datetime.strptime(delivery_date, '%d %b %Y').strftime('%Y-%m-%d')
                booking_date = datetime.strptime(csd['BookingDate'], '%Y-%m-%dT%H:%M:%S')
                bookking_date = booking_date.date()

                data = {
                    "consignment_no": consignment_no,
                    "consignee": csd['consignee'],
                    'consignee_address': address,
                    'consignee_number': number,
                    'booking_date': bookking_date,
                    'destination_branch': csd['DestBranch'],
                    'pieces': csd['pieces'],
                    'weight': csd['weight'],
                    'cod_amount': csd['codAmount'],
                    'status': status,
                    'delivery_date': parsed_date,
                    'total_charges': charges,
                    'attempts': attempts,
                    'product_description': csd['productDescription'],
                    'payment_fk': payment_id
                }
                all_data.append(data)

            return all_data

        all_data = fetch_data(start_date, end_date, month)

        try:
            for data in all_data:
                consignment_no = data['consignment_no']

                customer, created = Customer_Details.objects.update_or_create(
                    consignment_no=consignment_no,
                    defaults=data
                )

                if not created:
                    # Existing customer was updated
                    print(f"Customer with consignment_no {consignment_no} updated.")
                else:
                    # New customer was created
                    print(f"New customer with consignment_no {consignment_no} created.")
            return Response({"data": f"{all_data}"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error updating/creating customers: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QSR_View(APIView):
    permission_classes = (AllowAny,)

    def calculate_total_wholesale_value(self, product_description):
        try:
            product_details = Customer_Details.objects.filter(product_description__exact=product_description)

            if product_details.exists():
                item_count = product_details.count()
                total_wholesale_value = item_count * int(product_details.first().product_fk.product_wholesale_rate)
                product_sale_price = sum(item.cod_amount for item in product_details)
                return item_count, total_wholesale_value, product_sale_price, product_details
            else:
                return 0, 0, 0, []
        except ObjectDoesNotExist:
            return 0, 0, 0, []

    def get(self, *args, **kwargs):
        # auth_check(self)
        ads = int(kwargs.get('ads'))
        dc = int(kwargs.get('dc'))

        products = [
            'Double Shoe Rack', 'Single Shoe Rack', 'Double Pin Garment Hanger Stand',
            'Double Straight', 'Single Pin Garment Hanger Stand', 'Single Straight'
        ]

        total_items_sold = 0
        total_wholesale_value = 0
        total_sale_value = 0

        all_data = []
        total = []

        for product in products:
            product_data = {}
            item_count, product_wholesale_value, product_sale_price, product_details = self.calculate_total_wholesale_value(
                product)
            total_items_sold += item_count
            total_wholesale_value += product_wholesale_value
            total_sale_value += product_sale_price

            # Save product details for later use
            product_data[product] = {
                'item_sold': item_count,
                'total_wholesale_value': product_wholesale_value,
                'product_sale_price': product_sale_price,
            }

            all_data.append(product_data)

        total = { 'QSR Report' : {
            'total_items_sold': total_items_sold,
            'total_wholesale_value': total_wholesale_value,
            'total_sale_value': total_sale_value,
            'Ads Expense': ads,
            'M&P Charges': dc,
            'Profit / Loss ': float(
                total_sale_value - total_wholesale_value - ads - dc)
        }}
        all_data.append(total)

        email_user = 'sanaakram582@gmail.com'
        email_password = 'arby dpsv jbrd lypr'

        # Recipient email address
        email_send = 'muhammadmubeen384@gmail.com'

        # Email subject and body
        subject = 'QSR report by Your Market'
        body = 'Please find the Report below:'
        subject = 'QSR Report by Your Market'
        body = (
            "Dear recipient,\n\n"
            "Here is the QSR report of Your Market:\n\n"
        )

        for item in all_data:
            for product, details in item.items():
                body += f"{product}:\n"
                for key, value in details.items():
                    body += f"  {key}: {value}\n"
                body += "\n"

        body += (
            "\nThank you for using Your Market services. If you have any questions, "
            "please feel free to contact us.\n\nBest regards,\nYour Market Team"
        )

        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = email_send
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(email_user, email_password)
                server.sendmail(email_user, email_send, msg.as_string())
            print('Email sent successfully.')

        except Exception as e:
            print('Error:', str(e))

        return Response(data=all_data, status=status.HTTP_200_OK)


        # auth_check(self)

        # customer_details_queryset = Customer_Details.objects.filter(customer_id__isnull=False)
        # customer_details_list = list(customer_details_queryset)
        # product_mapping = {}
        # for cm in customer_details_list:
        #     product_mapping[cm.product_description] = None
        #
        # matching_products = Product_details.objects.filter(product_name__in=product_mapping.keys())
        #
        # for matching_product in matching_products:
        #     product_mapping[matching_product.product_name] = matching_product
        #
        # for cm in customer_details_list:
        #     matching_product = product_mapping[cm.product_description]
        #     if matching_product:
        #         cm.product_fk_id = matching_product
        #         cm.save()

