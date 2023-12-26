from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from .serializers import CustomerSerializer
from .models import Customer
import requests, json


class MyDataAPIView(APIView):
    def get(self, request, start_date, end_date, month):
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

        all_data = fetch_data(start_date, end_date, month)

        for data in all_data:
            consignment_no = data['consignment_no']
            try:
                customer = Customer.objects.get(consignment_no=consignment_no)
                # Update existing customer data
                serializer = CustomerSerializer(customer, data=data)
            except Customer.DoesNotExist:
                # Create new customer
                serializer = CustomerSerializer(data=data)

            if serializer.is_valid():
                serializer.save()

        serialized_data = CustomerSerializer(all_data, many=True)
        return Response(serialized_data.data, status=status.HTTP_200_OK)
