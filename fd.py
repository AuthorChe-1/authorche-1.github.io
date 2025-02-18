import telebot
import os

# Ваш токен бота Telegram
bot_token = '7619958750:AAGKCxMX4zqPLuXeQlIUrlyx_6ZQTVUbKDM'

# Айді користувача, якому дозволено керувати файлами
allowed_user_id = 6316376597

# Ініціалізація бота
bot = telebot.TeleBot(bot_token)

# Обробник команди /files
@bot.message_handler(commands=['files'])
def show_files(message):
    if message.from_user.id == allowed_user_id:
        files = os.listdir(os.path.dirname(os.path.abspath(__file__)))
        if files:
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
            for file in files:
                if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), file)):
                    markup.add(telebot.types.KeyboardButton(file))
            bot.reply_to(message, "Оберіть файл для завантаження:", reply_markup=markup)
        else:
            bot.reply_to(message, "У вказаному каталозі немає файлів для завантаження.")
    else:
        bot.reply_to(message, "Ви не маєте дозволу використовувати цю команду.")

# Обробник вибору файлу
@bot.message_handler(content_types=['text'])
def download_file(message):
    if message.from_user.id == allowed_user_id:
        file_name = message.text
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as file:
                bot.send_document(message.chat.id, file)
        else:
            bot.reply_to(message, "Вибраний файл не існує.")
    else:
        bot.reply_to(message, "Ви не маєте дозволу використовувати цю команду.")

# Запуск бота
bot.polling()
