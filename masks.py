import requests
import datetime
from config import URL_APPOINTMENTS, HEADERS_AUTH


def is_date(data):
    dates_list = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    data_list = data.split()
    return len(data_list) == 3 and data_list[0].isdigit() and data_list[1].isdigit() and data_list[2] in dates_list


def is_time(data):
    data_list = data.split(':')
    return len(data_list) == 2 and data_list[0].isdigit() and data_list[1].isdigit()


def is_full_name(data):
    return len(data.split()) == 3


def is_free_time(user_id, chosen_date, chosen_time):
    params = {
        'clinic_id': 1,
        'user_id': user_id,
        'date_start': chosen_date,
        'date_end': chosen_date,
    }
    appointments = requests.get(URL_APPOINTMENTS, headers=HEADERS_AUTH, params=params).json()
    chosen_time_dt = datetime.datetime.strptime(chosen_time, '%H:%M')
    for appointment in appointments['data']:
        time_start = datetime.datetime.strptime(appointment['attributes']['time'], '%H:%M')
        time_end = time_start + datetime.timedelta(minutes=appointment['attributes']['duration'])
        if chosen_time_dt >= time_start and chosen_time_dt < time_end:
            return 0
    return 1