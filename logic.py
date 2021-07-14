import requests
import datetime
from babel.dates import format_datetime

from config import URL_USERS, URL_SPECIALTIES, URL_CLIENTS, HEADERS_AUTH


def get_users():
    user_params_1 = {
        'count': 50,
        'page': 1,
    }

    user_params_2 = {
        'count': 50,
        'page': 2,
    }

    get_users = requests.get(
        URL_USERS, headers=HEADERS_AUTH, params=user_params_1)
    get_users_json = get_users.json()

    get_users_2 = requests.get(
        URL_USERS, headers=HEADERS_AUTH, params=user_params_2)
    get_users_json_2 = get_users_2.json()

    # Объединяю списки
    get_users_json['data'] += get_users_json_2['data']

    # Получаю специальности
    get_specialties = requests.get(URL_SPECIALTIES, headers=HEADERS_AUTH)
    get_specialties_json = get_specialties.json()

    # Формирую словарь специальностей
    specialties = {
        specialty['attributes']['id']: {
            'id': specialty['attributes']['id'],
            'title': specialty['attributes']['title']
        } for specialty in get_specialties_json['data']
    }

    # Форматирую список
    users = [
        {
            'id': user['attributes']['id'],
            'name': user['attributes']['name'],
            'surname': user['attributes']['surname'],
            'current_clinic_id': user['attributes']['current_clinic_id'],
            'user_status_id': 1,
            'has_appointment': user['attributes']['has_appointment'],
            'appointment_duration': user['attributes']['appointment_duration'],
            'specialty_ids': [
                specialties[specialty_id] for specialty_id in user['attributes']['specialty_ids']
            ],
            'full_name': user['attributes']['full_name']
        } for user in get_users_json['data'] if user['attributes']['has_appointment'] and user['attributes']['user_status_id'] == 1
    ]

    # Сортирую список врачей по алфавиту
    users = sorted(users, key=lambda d: d['full_name'])

    # Корректирую словарь
    for user in users:
        for i in range(len(user['specialty_ids'])):
            if user['specialty_ids'][i]['title'] == 'Медсестра' or user['specialty_ids'][i]['title'] == 'Лаборант' or user['full_name'] == 'Кузнецов Андрей Александрович':
                users.remove(user)
        if user['full_name'] == 'Дневной Стационар ** ***':
            users.remove(user)
        if user['full_name'] == 'Иконостасова Евгения Ивановна (8 903 089 88 31)':
            user['full_name'] = 'Иконостасова Евгения Ивановна'
    
    return users


def get_user_full_name(user_id):
    params = {
        'id': user_id
    }
    user = requests.get(URL_USERS, headers=HEADERS_AUTH, params=params).json()['data'][0]['attributes']
    user_full_name = user['surname'] + ' ' + user['name'] + ' ' + user['second_name']
    return user_full_name


def check_client_in_crm(phone):
    params = {
        'phone': phone
    }
    try:
        client = requests.get(URL_CLIENTS, headers=HEADERS_AUTH, params=params).json()['data'][0]
        return client
    except IndexError:
        return 0


def get_date_ru(datetime_date):
    date = datetime.datetime.strptime(datetime_date, '%Y-%m-%d')
    return format_datetime(date, 'd MMMM', locale='ru_RU')



def create_client(phone, client_full_name):
    global client_id
    client = client_full_name.split()
    surname = client[0]
    name = client[1]
    second_name = client[2]
    create_client_params = {
        'name': name,
        'surname': surname,
        'second_name': second_name,
        'phone': phone,
    }
    try:
        create_client = requests.post(URL_CLIENTS, headers=HEADERS_AUTH, params=create_client_params).json()
        client_id = create_client['data']['id']
    except:
        return 0