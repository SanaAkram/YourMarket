import traceback
from datetime import datetime, timedelta
from django.core.management import BaseCommand
from customer.Jobs.qsr_job import QSRJob
from customer.functions import start_server, wait_for_server
import calendar


class Command(BaseCommand):
    help = 'Update/ Create Customer Details Table'

    def handle(self, *args, **options):
        get_all_qsr_data()


def get_start_end_dates(year, month):
    try:
        next_month = (month % 12) + 1
        next_year = year + (month // 12)

        start_date = datetime(year, month, 1)
        last_day_of_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        return start_date, last_day_of_month, next_month, next_year
    except Exception as e:
        print(e)


def get_all_qsr_data():
    response_list = []
    current_date = datetime.now()
    start_date = datetime(2023, 1, 1)

    try:
        start_server()
        wait_for_server()
        while start_date <= current_date:
            start_date, end_date, next_month, next_year = get_start_end_dates(start_date.year, start_date.month)
            tf = QSRJob()
            tf.hit_api_for_month(start_date=start_date.strftime('%Y-%m-%d'), month=start_date.month,
                                 end_date=end_date.strftime('%Y-%m-%d'))

            # Calculate the next month's start date using calendar.monthrange
            _, days_in_next_month = calendar.monthrange(next_year, next_month)
            start_date = start_date.replace(day=1).replace(month=next_month)
    except Exception as e:
        response = {'status': 'FAILURE',
                    'key': 'QSR Report',
                    'error_traceback': traceback.format_exc()}
        print(response)
        response_list.append(response)
