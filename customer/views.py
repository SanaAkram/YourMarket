from datetime import datetime
from .models import Customer_Details, Product_details, PaymentDetails, Email
import requests
import json
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .constants import products
from .functions import send_email, create_qsr_report_body, create_email_body
from yourmarket.settings import EMAIL_TO, EMAIL_HOST_USER


class Customer_DataAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, start_date=None, end_date=None, month=None):
        if '<str:' in start_date:
            return Response(data='', status=status.HTTP_200_OK)
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
        customer_details_url = "https://cpapp.azurewebsites.net/CustomerPortalAPI/api/Reports/CnDetails?cn="

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

        def set_payment_id(payment_id):
            payment_obj = PaymentDetails.objects.filter(payment_id=payment_id).first()
            # print(f'Consignment number {consignment_no} has Payment Id {payment_obj}')
            if payment_obj:
                return payment_obj
            else:
                return None

        def get_product_fk(product_description):
            product_obj = Product_details.objects.filter(product_name=product_description).first()
            return product_obj

        def process_string(input_string):
            cleaned_string = ''.join(char for char in input_string if not char.isdigit())
            cleaned_string = cleaned_string.replace(' ', '_').lstrip('_')
            cleaned_string = cleaned_string.lower()
            if 'single' in cleaned_string or 'singal' in cleaned_string:
                if 'shoe' in cleaned_string:
                    cleaned_string = 'Single Shoe Rack'
                else:
                    cleaned_string = 'Single Pin Garment Hanger Stand'
            elif 'double' in cleaned_string:
                if 'shoe' in cleaned_string:
                    cleaned_string = 'Double Shoe Rack'
                elif 'straight' in cleaned_string:
                    cleaned_string = 'Double Straight'
                else:
                    cleaned_string = 'Double Pin Garment Hanger Stand'
            elif 'straight' in cleaned_string and 'double' not in cleaned_string:
                cleaned_string = 'Straight'
            return cleaned_string

        def db_entry(all_data, db_table):
            try:
                for data in all_data:
                    customer, created = db_table.objects.update_or_create(
                        payment_id=data['payment_id'],
                        defaults=data
                    )
                    if not created:
                        # Existing customer was updated
                        print(f" Payments with updated.")
                    else:
                        # New customer was created
                        print(f"New Entry of Payments with created.")

            except Exception as e:
                print(f"Error updating/creating customers: {str(e)}")

        def fetch_data(start_date, end_date, month):
            customer_summary_endpoint = create_url(BASE_URL, customer_summary_detail_report_url)
            customer_summary_data = get_api_response(customer_summary_endpoint, c_data)

            booking_summary_endpoint = create_url(BASE_URL, booking_summary_report_url)
            booking_summary_data = get_api_response(booking_summary_endpoint,
                                                    get_booking_summary_payload(start_date, end_date, month))

            qsr_endpoint = create_url(BASE_URL, qsr_report_url)
            qsr_data = get_api_response(qsr_endpoint, get_qsr_payload(start_date, end_date, month))

            if not qsr_data:
                body = f'QSR Report cannot be generated as there are no records between {start_date} to {end_date}'
                send_email(email_body=body, subject='QSR Report Generation Failed')
            payment_endpoint = create_url(BASE_URL, payment_report_url)
            payment_data = get_api_response(payment_endpoint, get_qsr_payload(start_date, end_date, month))
            payments = []
            for payment in payment_data:
                p_data = {
                    "payment_id": payment['PaymentID'],
                    "paid_on": payment['PaidOn'],
                    'rr_amount': payment['RRAmount'],
                    'invoice_amount': payment['InvoiceAmount'],
                    'ibft_fee': payment['IBFTFee'],
                    'net_payable': payment['NetPayable'],
                    'instrument_mode': payment['InstrumentMode'],
                    'instrument_number': payment['InstrumentNumber'],
                }

                payments.append(p_data)
            db_entry(payments, PaymentDetails)

            # customer_phone_url_endpoint = create_url(BASE_URL, customer_phone_url)
            # number_details = get_api_response(customer_phone_url_endpoint,
            #                                   get_customer_number_payload(start_date, end_date))

            all_data = []

            for csd in customer_summary_data:
                consignment_no = csd['consignmentNumber']
                address = next((bsd['consigneeAddress'] for bsd in booking_summary_data if bsd['cn'] == consignment_no),
                               '')
                number = next(
                    (bsd['consigneePhoneNo'] for bsd in booking_summary_data if bsd['cn'] == consignment_no), '')
                if address == '' or number == '':
                    customer_details_endpoint = customer_details_url + consignment_no
                    c_details = get_api_response(customer_details_endpoint, '')
                    if c_details:
                        address = c_details[0]['ConsigneeAddress']
                        number = c_details[0]['ConsigneeCell']
                # if number == '':
                #     number = next(
                #         (num['contact'] for num in number_details if
                #          num['detail'][0]['consignmentNumber'] == consignment_no),
                #         '')
                # if address == '' and number:
                #     customer_info = get_api_GET_response(customer_address_url + number)
                #     if customer_info:
                #         address = customer_info['address']

                qsr_item = next((q for q in qsr_data if q['consignmentNumber'] == consignment_no), {})
                status = qsr_item.get('RRStatus', '')
                p_id = qsr_item.get('paymentId', '')
                if p_id:
                    payment_id = set_payment_id(p_id)
                else:
                    payment_id = None
                total_amount = int(qsr_item.get('totalAmount', 0))
                gst = int(qsr_item.get('GST', 0))
                charges = total_amount + gst
                attempts = qsr_item.get('Attempts', '')
                delivery_date = qsr_item.get('deliveryDate', '')
                parsed_date = datetime.strptime(delivery_date, '%d %b %Y').strftime('%Y-%m-%d')
                booking_date = datetime.strptime(csd['BookingDate'], '%Y-%m-%dT%H:%M:%S')
                bookking_date = booking_date.date()
                product_detail = process_string(csd['productDescription'])
                product_fk = get_product_fk(product_detail)

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
                    'product_description': product_detail,
                    'payment_fk': payment_id,
                    'product_fk': product_fk
                }
                all_data.append(data)

            return all_data

        all_data = fetch_data(start_date, end_date, month)
        email_body = create_email_body(all_data)
        subject = f'Shipment Update - Summary Report for Date {start_date} and {end_date}'
        existing_email, created = Email.objects.update_or_create(
            subject=subject,
            defaults={'body': email_body, 'sender': EMAIL_HOST_USER, 'recipient': EMAIL_TO}
        )

        if created:
            send_email(email_body, subject)
            print(f"Email sent with subject '{subject}' and added to the Email model.")
        else:
            print(f"Email with subject '{subject}' already exists. Skipping.")
        try:
            for index, data in enumerate(all_data):
                consignment_no = data['consignment_no']

                customer, created = Customer_Details.objects.update_or_create(
                    consignment_no=consignment_no,
                    defaults=data
                )

                if not created:
                    # Existing customer was updated
                    print(f"Customer with consignment_no {consignment_no} updated. with Index {index}")
                else:
                    # New customer was created
                    print(f"New customer with consignment_no {consignment_no} created with Index {index}")

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
            product_data[product] = {
                'item_sold': item_count,
                'total_wholesale_value': product_wholesale_value,
                'product_sale_price': product_sale_price,
            }

            all_data.append(product_data)

        total = {'QSR Report': {
            'total_items_sold': total_items_sold,
            'total_wholesale_value': total_wholesale_value,
            'total_sale_value': total_sale_value,
            'Ads Expense': ads,
            'M&P Charges': dc,
            'Profit / Loss ': float(
                total_sale_value - total_wholesale_value - ads - dc)
        }}
        all_data.append(total)

        email_body = create_qsr_report_body(all_data)
        send_email(email_body, subject='QSR Report by Your Market')

        return Response(data=all_data, status=status.HTTP_200_OK)