from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types.input_file import InputFile
import os
import aiohttp

class ExchangeForm(StatesGroup):
    сurrency_from = State()
    currency_to = State()
    quantity = State() 


async def weather(city_name: str) -> str:
    '''
    Асинхронная функция, которая делает запрос по 
    API OpenWeatherAPI и возвращает 
    градусы цельсия
    '''
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_WEATHER}') as response:
            result = await response.json()
            if len(result) < 1: # Проверка, не пришел ли пустой запрос
                return None
            lat = result[0]['lat']
            lon = result[0]['lon']
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_WEATHER}&units=metric') as response:
            result = await response.json()
            data = result['main']['temp']
    
    return data

'''
Берем переменную из окружения.
Для того, чтобы создать переменную в Windows, нужно в cmd прописать команду
set TOKEN="Токен_вашего_бота"
'''
API_EXCHANGE = os.environ.get('API_EXCHANGE', 'TE3fYoK9we5P2Khtm8SvbaTp3mFw0djb')
API_WEATHER = os.environ.get('API_WEATHER', '62d12181917e61699eaa46ce67509b48')
TOKEN = os.environ.get('TOKEN')

# Создаем объекты бота и диспетчера
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

# Главная клавиатура
start_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Выберите сервис")
weather_btn = types.KeyboardButton('Определить погоду 🌤')
currency_btn = types.KeyboardButton('Конвертация валют 💱')
animal_btn = types.KeyboardButton('Случайная картинка с животными 🐶')
polls_btn = types.KeyboardButton('Создать опрос для группы 📊')

start_kb.add(weather_btn).add(currency_btn).add(animal_btn).add(polls_btn)

# Клавиатура погоды
weather_kb = types.InlineKeyboardMarkup()
w_btn1 = types.InlineKeyboardButton('Москва', callback_data='wМосква')
w_btn2 = types.InlineKeyboardButton('Екатеринбург', callback_data='wЕкатеринбург')
w_btn3 = types.InlineKeyboardButton('Санкт-Петербург', callback_data='wСанкт-Петербург')
w_btn4 = types.InlineKeyboardButton('Казань', callback_data='wКазань')
w_btn5 = types.InlineKeyboardButton('Нижний Новгород', callback_data='wНижний Новгород')
w_btn6 = types.InlineKeyboardButton('Новосибирск', callback_data='wНовосибирск')
weather_kb.add(w_btn1).add(w_btn2).add(w_btn3).add(w_btn4).add(w_btn5).add(w_btn6)

# Клавиатура для выбора валюты
list_cur = ['RUB', 'KZT', 'USD', 'EUR', 'CNY', 'BYR']
exc_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
e_btn1 = types.KeyboardButton('RUB')
e_btn2 = types.KeyboardButton('KZT')
e_btn3 = types.KeyboardButton('USD')
e_btn4 = types.KeyboardButton('EUR')
e_btn5 = types.KeyboardButton('CNY')
e_btn6 = types.KeyboardButton('BYR')
e_btn7 = types.KeyboardButton('Вернуться назад')

exc_kb.add(e_btn1).add(e_btn2).add(e_btn3).add(e_btn4).add(e_btn5).add(e_btn6).add(e_btn7)


@dp.message_handler(commands=['start'])
async def startMessage(message: types.Message):
    await message.answer('''Стартовое сообщение бота.\nИспользуйте клавиатуру, чтобы выбрать сервис''', reply_markup=start_kb)

@dp.message_handler(Text(equals='Вернуться назад', ignore_case=True), state='*')
async def cancelState(message: types.Message, state: FSMContext):
    '''
    Позволяет пользователю выйти из состояний
    '''
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await message.answer('Выберите функцию бота', reply_markup=start_kb)
    await state.finish()

@dp.message_handler(state=ExchangeForm.сurrency_from)
async def process_currency_from(message: types.Message, state: FSMContext):
    """
    Выбор валюты (из какой нужно конвертировать)
    """
    if message.text not in list_cur:
        await message.answer('Такой валюты не существует!\nВыберите валюту из списка', reply_markup=start_kb)
        return
    async with state.proxy() as data:
        data['from'] = message.text

    await ExchangeForm.next()
    await message.answer("В какую валюту вы хотите конвертировать?", reply_markup=exc_kb)

@dp.message_handler(state=ExchangeForm.currency_to)
async def process_gender(message: types.Message, state: FSMContext):
    """
    Выбор валюты (в какую нужно конвертировать)
    """

    if message.text not in list_cur:
        await message.answer('Такой валюты не существует!\nВыберите валюту из списка', reply_markup=start_kb)
        return

    async with state.proxy() as data:
        data['to'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton('Вернуться назад')
    markup.add(btn)

    await ExchangeForm.next()
    await message.answer('Напишите сумму, которую хотите конвертировать в эту валюту', reply_markup=markup)

@dp.message_handler(state=ExchangeForm.currency_to)
async def process_currency_to(message: types.Message, state: FSMContext):
    if message.text not in list_cur:
        await message.answer('Такой валюты не существует!', reply_markup=start_kb)
        return

    async with state.proxy() as data:
        data['quantity'] = message.text

    await ExchangeForm.next()
    await message.answer('Напишите сумму, которую хотите конвертировать в эту валюту')

@dp.message_handler(state=ExchangeForm.quantity)
async def process_result(message: types.Message, state: FSMContext):
    if not message.text.replace(' ', '').isdigit():
        await message.answer('Не правильно написана сумма.\nВ сообщении должны быть только цифры.')
        return
    async with state.proxy() as data:
        data['quantity'] = message.text
    

    async with aiohttp.ClientSession() as session:
        from_c = data['from']
        to_c = data['to']
        amount = data['quantity']
        async with session.get(f'https://api.apilayer.com/exchangerates_data/convert?apikey={API_EXCHANGE}&to={from_c}&from={to_c}&amount={amount}') as response:
            result = await response.json()
            res = result['result']

    await message.answer(f'{from_c} ➡ {to_c} = {res}{to_c}', reply_markup=start_kb)
    await state.finish()

@dp.callback_query_handler()
async def get_weather(callback_query: types.CallbackQuery):
    if callback_query.data and callback_query.data.startswith('w'):
        city_name = callback_query.data.replace('w', '')
        temp = await weather(city_name)
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
        await bot.send_message(callback_query.from_user.id, text=f'Погода в городе {city_name} - {int(temp)} ℃', reply_markup=weather_kb)

@dp.message_handler()
async def weather_list(message: types.Message):
    if message.text == 'Определить погоду 🌤':
        await message.answer('Выберите город', reply_markup=weather_kb)
    if message.text == 'Конвертация валют 💱':
        await ExchangeForm.сurrency_from.set()
        await message.answer('Выберите валюту, которую хотите перевести', reply_markup=exc_kb)
    if message.text == 'Случайная картинка с животными 🐶':
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://random.dog/woof') as response:
                endpoint = await response.text()
        
        url = 'https://random.dog/' + endpoint
        await bot.send_photo(chat_id=message.chat.id, photo=url)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

