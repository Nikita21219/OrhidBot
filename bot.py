import telebot
import datetime
import requests

from config import BOT_TOKEN, URL_USERS, URL_SHEDULES, URL_APPOINTMENTS, HEADERS_AUTH
from masks import is_date, is_time, is_full_name, is_free_time
from logic import get_user_full_name, check_client_in_crm, get_date_ru, create_client, date_ru_in_datetime
from keyboards import get_users_markup, get_main_menu_markup, get_schedule_for_4_weeks_markup, get_confirming_markup, get_yes_or_no_markup, get_social_networks_markup


bot = telebot.TeleBot(BOT_TOKEN)

user_id = 0
chosen_date = ''
chosen_time = ''
client_full_name = ''
min_delta_appointment = datetime.timedelta(minutes=20) # Минимальная длительность приема врача по дефолту
client_id = 0
phone = ''


def get_times_markup(user_id, date):
    global chosen_date
    global min_delta_appointment
    chosen_date = datetime.datetime.strftime(date_ru_in_datetime(date), '%Y-%m-%d')
    schedules_params = {
        'date': chosen_date,
        'days_count': 1,
        'clinic_id': 1,
        'user_ids': user_id,
    }
    user_params = {
        'id': user_id
    }
    # Если минимальная длительность приема есть
    appointment_duration = requests.get(URL_USERS, headers=HEADERS_AUTH, params=user_params).json()['data'][0]['attributes']['appointment_duration']
    if appointment_duration:
        min_delta_appointment = datetime.timedelta(minutes=int(appointment_duration))

    requset_times = requests.get(URL_SHEDULES, headers=HEADERS_AUTH, params=schedules_params).json()


    # Формирую список словарей с графиком работы врача
    worktime = []
    for time in requset_times[0]['worktimes'][0]['worktime']:
        time_start = schedules_params['date'] + ' ' + time[0]
        time_end = schedules_params['date'] + ' ' + time[1]
        time_start = datetime.datetime.strptime(
            time_start, '%Y-%m-%d %H:%M')
        time_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M')
        worktime_dict = {
            'time_start': time_start,
            'time_end': time_end,
        }
        worktime.append(worktime_dict)

    # Формирую список из словарей со временем начала и конца приема
    busy_times = []
    for appointment in requset_times[0]['worktimes'][0]['appointments']:
        delta_appointment = datetime.timedelta(minutes=appointment[1])
        start_appointment = datetime.datetime.strptime(
            schedules_params['date'] + ' ' + appointment[0], '%Y-%m-%d %H:%M')
        end_appointment = start_appointment + delta_appointment
        appointment_dict = {
            'start_appointment': start_appointment,
            'end_appointment': end_appointment,
        }
        busy_times.append(appointment_dict)
    busy_times = sorted(
        busy_times, key=lambda k: k['start_appointment'])

    # Формирую список со свободным временем, которое доступно для записи перед первым приемом и после последнего
    free_times = []
    if busy_times:
        first_appointment = busy_times[0]['start_appointment']
        last_appointment = busy_times[len(
            busy_times) - 1]['end_appointment']
        for wt in worktime:
            start_worktime = wt['time_start']
            if first_appointment > start_worktime:
                while first_appointment != start_worktime:
                    first_appointment -= min_delta_appointment
                    if first_appointment < start_worktime:
                        break
                    else:
                        free_times.append(
                            first_appointment.strftime('%H:%M'))
            end_worktime = wt['time_end']
            while end_worktime - last_appointment >= min_delta_appointment:
                free_times.append(last_appointment.strftime('%H:%M'))
                last_appointment += min_delta_appointment

    # Дополняю список свободным временем для записи, которое доступно между приемами
    if len(worktime) <= 1:  # Дополняю только в том случае, если нет нерабочего времени
        for i in range(len(busy_times) - 1):
            start_time_next_appointment = busy_times[i + 1]['start_appointment']
            end_time_appointment = busy_times[i]['end_appointment']
            while start_time_next_appointment - end_time_appointment >= min_delta_appointment:
                free_times.append(
                    end_time_appointment.strftime('%H:%M'))
                end_time_appointment += min_delta_appointment

    keyboard = telebot.types.InlineKeyboardMarkup()
    if free_times:
        # Добавляю время в клавиатуру
        for time in sorted(free_times):
            time_button = telebot.types.InlineKeyboardButton(time, callback_data=time)
            keyboard.add(time_button)
        main_menu_button = telebot.types.InlineKeyboardButton('В главное меню ◀️', callback_data='main_menu')
        keyboard.add(main_menu_button)
        return keyboard
    return 0


def make_appointment(user_id, chosen_date, chosen_time, client_id):
    # Конвертирую продолжительность приема врача в int и записываю в переменную mm
    hh, mm, ss = map(int, str(min_delta_appointment).split(':'))

    create_appointment_params = {
        'duration': mm,
        'clinic_id': 1,
        'date': chosen_date,
        'time': chosen_time,
        'user_id': user_id,
        'client_id': client_id,
        'appointment_type_id': 1,
        'appointment_source_id': 2
    }
    my_post_request = requests.post(URL_APPOINTMENTS, headers=HEADERS_AUTH, params=create_appointment_params)
    if my_post_request:
        return 1
    return 0


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f'Привет, {message.from_user.first_name}! Я бот, который поможет тебе взаимодействать с медицинским центром Белая Орхидея!\nЧто тебя интересует?',
        reply_markup=get_main_menu_markup()
    )


@bot.message_handler(content_types=['text'])
def bot_message(message):
    global client_full_name
    global chosen_date
    global chosen_time
    global client_id
    if message.chat.type == 'private':
        if message.text == 'В главное меню ◀️':
            bot.send_message(message.chat.id, 'Вы вернулись в главное меню', reply_markup=get_main_menu_markup())
        elif message.text == 'Записаться на прием':
            # Отправляю в сообщении клавиатуру полученную в функции get_users_markup
            bot.send_message(message.chat.id, 'Загружаю актуальных врачей, подождите немного')
            bot.send_message(message.chat.id, 'Выберите врача', reply_markup=get_users_markup())
        elif message.text == 'Информация':
            bot.send_message(message.chat.id, 'Многопрофильный медицинский центр Белая Орхидея - это современные методы обследования и диагностики, передовое техническое оснащение, высокотехнологичное оборудование, безупречная вежливость и внимательность персонала а также сервис высочайшего уровня. \n\nМы предоставляем такие услуги как:\nУрология.\nЭндокринология.\nAкушерство и гинекология.\nГастроэнтеролог.\nДерматология.\nДетский невролог.\nЛазерная хирургия.\nКардиология.\nЛаборатория.\nЛор.\nМаммология.\nНеврология.\nОнкология.\nОфтальмология.\nПроктология.\nТерапия.\nТравмотолог-ортопед.\nУЗИ.\nХирургия.\nФлеболог\n\nНаши соц.сети:', reply_markup=get_social_networks_markup())
        elif message.text == 'График':
            bot.send_message(message.chat.id, 'Понедельник - суббота: с 8.00 до 20.00\nВоскресенье: с 8.00 до 18.00\nБез перерывов', reply_markup=get_main_menu_markup())
        elif message.text == 'Контакты':
            bot.send_message(message.chat.id, 'Ул. Ленина, 84, город Троицк, Челябинская область, 457100\n\nТелефоны:\n8-951-258-36-51\n8-982-363-41-00\n8-35163-5-80-10\n8-35163-7-16-61', reply_markup=get_main_menu_markup())
        # Если пользователь ввел ФИО
        elif is_full_name(message.text):
            if user_id and chosen_date and chosen_time and phone:
                client_id = create_client(phone, message.text)
                bot.send_message(message.chat.id, f'Информация правильная?\nВаше ФИО: {message.text}\nВаш телефон: {phone}', reply_markup=get_yes_or_no_markup())
            else:
                bot.send_message(message.chat.id, 'Я тебя не понимаю')
        elif message.text == 'Подтвердить':
            if user_id and chosen_date and chosen_time and client_id and client_full_name and is_free_time(user_id, chosen_date, chosen_time):
                if make_appointment(user_id, chosen_date, chosen_time, client_id):
                    bot.send_message(message.chat.id, f'Вы успешно записались на прием к врачу {get_user_full_name(user_id)} на {get_date_ru(chosen_date)} в {chosen_time}.\nВ ближайшее время с вами свяжется администратор')
                else:
                    bot.send_message(message.chat.id, 'Что-то пошло не так, попробуйте снова')
            else:
                bot.send_message(message.chat.id, 'Что-то пошло не так, попробуйте снова')
        else:
            bot.send_message(message.chat.id, 'Я тебя не понимаю')


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    global chosen_time
    global chosen_date
    global client_full_name
    global user_id
    global client_id
    # Если callback это id врача
    if call.data.isdigit():
        user_id = int(call.data)
        markup = get_schedule_for_4_weeks_markup(user_id)
        if markup:
            bot.send_message(call.message.chat.id, 'Выберите дату', reply_markup=markup)
        # Иначе вывожу соответствующее сообщение
        else:
            bot.send_message(call.message.chat.id, 'У этого врача в ближайшее время нет доступного времени.\nДля более подробной информации звонить в медициский центр (поле "Контакты" в меню)', reply_markup=get_main_menu_markup())
    # Если callback это выбранная дата посещения
    elif is_date(call.data):
        chosen_date = call.data
        if chosen_date and user_id:
            keyboard_times = get_times_markup(user_id, call.data)
            if keyboard_times:
                bot.send_message(call.message.chat.id, 'Выберите время', reply_markup=keyboard_times)
            else:
                bot.send_message(call.message.chat.id, 'В этот день у врача нет свободного времени, выберите другой день', reply_markup=get_main_menu_markup())
        else:
            bot.send_message(call.message.chat.id, 'Что-то пошло не так. Попробуйте еще раз выбрать врача', reply_markup=get_main_menu_markup())
    # Если callback это выбранное время для посещения
    elif is_time(call.data):
        chosen_time = call.data
        phone_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        phone_markup.add(telebot.types.KeyboardButton('Отправить свой номер телефона ☎️', request_contact=True))
        phone_markup.add(telebot.types.KeyboardButton('В главное меню ◀️'))
        bot.send_message(call.message.chat.id, 'Для записи на прием нам необходим твой номер телефона', reply_markup=phone_markup)
    # Обрабатываю случай когда клиент есть в crm
    elif call.data == 'yes':
        if phone and user_id and chosen_date and chosen_time:
            client = check_client_in_crm(phone)
            client_full_name = client['attributes']['surname'] + ' ' + client['attributes']['name']
            date_ru = get_date_ru(chosen_date)
            bot.send_message(
                call.message.chat.id,
                f'Подтвердите запись на прием\nВыбранный врач: {get_user_full_name(user_id)}\nВыбранная дата: {date_ru}\nВыбранное время: {chosen_time}',
                reply_markup=get_confirming_markup()
            )
        else:
            bot.send_message(call.message.chat.id, 'Что-то пошло не так', reply_markup=get_main_menu_markup())
    # Обрабатываю случай когда клиента нет в crm
    elif call.data == 'no':
        bot.send_message(call.message.chat.id, f'Введите ФИО в формате "Иванов Иван Иванович" без пробелов в начале и конце', reply_markup=get_main_menu_markup())
    elif call.data == 'main_menu':
        bot.send_message(call.message.chat.id, 'Вы вернулись в главное меню', reply_markup=get_main_menu_markup())


@bot.message_handler(content_types=['contact'])
def read_contact_phone(message):
    global client_id
    global phone
    phone = message.contact.phone_number
    # Проверяю есть ли клиент в crm
    client = check_client_in_crm(phone)
    if chosen_time and chosen_date and user_id:
        if client:
            client_id = client['id']
            full_name = client['attributes']['surname'] + ' ' + client['attributes']['name']
            bot.send_message(message.chat.id, f'Ваше имя {full_name}?', reply_markup=get_yes_or_no_markup())
        # Запрашиваю ФИО
        else:
            bot.send_message(message.chat.id, f'Введите ФИО в формате "Иванов Иван Иванович" без пробелов в начале и конце', reply_markup=get_main_menu_markup())
    else:
        bot.send_message(message.chat.id, 'Что-то пошло не так', reply_markup=get_main_menu_markup())

bot.polling(none_stop=True, interval=0)
