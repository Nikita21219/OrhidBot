import telebot
import datetime
import requests
from babel.dates import format_datetime

from config import URL_SHEDULES, HEADERS_AUTH
from logic import get_users


def get_users_markup():
    keyboard = telebot.types.InlineKeyboardMarkup()
    # Добавляю каждого врача в клавиатуру
    for user in get_users():
        if user['full_name']:
            doctor_button = telebot.types.InlineKeyboardButton(user['full_name'], callback_data=user['id'])
            keyboard.add(doctor_button)
    main_menu_button = telebot.types.InlineKeyboardButton('В главное меню ◀️', callback_data='main_menu')
    keyboard.add(main_menu_button)
    return keyboard


def get_main_menu_markup():
    button_appointment = telebot.types.KeyboardButton('Записаться на прием')
    button_info = telebot.types.KeyboardButton('Информация')
    button_shedule = telebot.types.KeyboardButton('График')
    button_contacts = telebot.types.KeyboardButton('Контакты')
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(button_info, button_shedule, button_contacts).add(button_appointment)
    return markup


def get_schedule_for_4_weeks_markup(user_id):
    day = datetime.datetime.today()
    i = 0
    schedule_for_4_weeks = []
    while i != 5:
        params = {
            'date': day.strftime('%Y-%m-%d'),
            'days_count': 7,
            'clinic_id': 1,
            'user_ids': user_id,
        }
        schedule_for_4_weeks += requests.get(URL_SHEDULES, headers=HEADERS_AUTH, params=params).json()
        day += datetime.timedelta(weeks=1)
        i += 1
    
    available_days = []
    for day in schedule_for_4_weeks:
        if day['worktimes'][0]['worktime']:
            available_days.append(datetime.datetime.strptime(day['date'], '%Y-%m-%d'))

    # Если есть рабочие дни отпраляю их
    if available_days:
        markup = telebot.types.InlineKeyboardMarkup()
        for day in available_days:
            date_ru = str(format_datetime(day, 'd MMMM', locale='ru_RU'))
            year = datetime.datetime.now()
            year = datetime.datetime.strftime(year, '%Y')
            callback = year + ' ' + date_ru
            date_button = telebot.types.InlineKeyboardButton(date_ru, callback_data=callback)
            markup.add(date_button)
        main_menu_button = telebot.types.InlineKeyboardButton('В главное меню ◀️', callback_data='main_menu')
        markup.add(main_menu_button)
        return markup
    return 0


def get_confirming_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('Подтвердить'))
    markup.add(telebot.types.KeyboardButton('В главное меню ◀️'))
    return markup


def get_yes_or_no_markup():
    keyboard = telebot.types.InlineKeyboardMarkup()
    yes_button = telebot.types.InlineKeyboardButton('Да', callback_data='yes')
    no_button = telebot.types.InlineKeyboardButton('Нет', callback_data='no')
    keyboard.add(yes_button, no_button)
    main_menu_button = telebot.types.InlineKeyboardButton('В главное меню ◀️', callback_data='main_menu')
    keyboard.add(main_menu_button)
    return keyboard


def get_social_networks_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    vk_button = telebot.types.InlineKeyboardButton('VK 🌐', url='https://vk.com/orchid_74')
    ok_button = telebot.types.InlineKeyboardButton('OK 🌐', url='https://ok.ru/meditsinsi')
    inst_button = telebot.types.InlineKeyboardButton('Instagram 🌐', url='https://www.instagram.com/orhideya7414/')
    site_button = telebot.types.InlineKeyboardButton('Наш сайт 🌐', url='https://xn---74-mddfq5bq9bzg.xn--p1ai/')
    markup.add(vk_button, ok_button, inst_button)
    markup.add(site_button)
    main_menu_button = telebot.types.InlineKeyboardButton('В главное меню ◀️', callback_data='main_menu')
    markup.add(main_menu_button)
    return markup