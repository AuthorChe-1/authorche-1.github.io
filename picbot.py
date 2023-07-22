import telebot
import requests
from datetime import date

# Ваш токен Telegram Bot API
TOKEN = '5704591843:AAGy9xtsO2MTUmIcB7TsMQDojb_YMtmOZiQ'

# Ліміт запитів на день
REQUESTS_LIMIT = 50

# Зберігаємо стан запитів на день
requests_count = {}

# Створюємо екземпляр бота
bot = telebot.TeleBot(TOKEN)

# Обробка команди /start
@bot.message_handler(commands=['start'])
def start(message):
    """Повідомляємо користувача про те, як використовувати бота."""
    bot.reply_to(message, 'Привіт! Відправ мені команду /pic разом зі словом або фразою, і я знайду картинки для тебе.')

# Обробка команди /pic
@bot.message_handler(commands=['pic'])
def pic(message):
    """Шукаємо та надсилаємо картинки за запитом."""
    # Отримуємо запит користувача
    query = message.text.replace('/pic', '').strip()

    # Перевіряємо, чи досягнуто ліміту запитів на день
    if exceeded_requests_limit(message.chat.id):
        bot.reply_to(message, 'Ви досягли ліміту запитів на сьогодні. Спробуйте знову завтра.')
        return

    # URL для пошуку картинок
    search_url = f'https://api.unsplash.com/search/photos?page=1&query={query}&client_id=qkDjTVBkaJ4XZ7kPkZjmPVHHNcyJp4aXJSlnD48oYW0'

    # Виконуємо запит до API
    response = requests.get(search_url)
    data = response.json()

    # Отримуємо першу картинку з результатів пошуку
    if data['results']:
        image_url = data['results'][0]['urls']['regular']
        bot.send_photo(message.chat.id, image_url)

        # Оновлюємо лічильник запитів на день
        update_requests_count(message.chat.id)
    else:
        bot.reply_to(message, 'На жаль, не вдалося знайти жодної картинки за цим запитом.')

# Обробка будь-якого повідомлення
@bot.message_handler(func=lambda message: True)
def echo(message):
    """Відповідаємо на повідомлення користувача."""
    bot.reply_to(message, 'Я не розумію цю команду. Відправ мені команду /pic разом зі словом або фразою, і я знайду картинки для тебе.')

# Запускаємо бота
bot.polling()