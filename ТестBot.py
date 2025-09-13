# AuthorChe
# 🌐
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import abc

from aiogram.types import Message as AiogramMessage, InlineKeyboardMarkup, InlineKeyboardButton
from telethon.utils import get_display_name

from .. import loader, utils

@loader.tds
class MenuBotMod(loader.Module):
    """Simple menu for bot"""

    metaclass = abc.ABCMeta

    strings = {
        "name": "ТестBot",
        "/donate": (
            "<b>Підтримати проєкт — це чудова ідея! ❤️</b>\n\n"
            "<i>Ви можете зробити переказ на мої картки (UA):</i>\n"
            "🍏 <b>ABank24:</b> <code>4323347397734135</code>\n"
            "💸 <b>Privat24:</b> <code>5168745150640644</code>\n\n"
            "<i>Або на мої криптовалютні гаманці:</i>\n"
            "🪙 <b>BTC:</b>\n<code>123MgBkkpu6XwrU53SvrBxiW9useRSt6qR</code>\n"
            "💎 <b>TON:</b>\n<code>UQDicYt03peG8l0CBCKW2YQJ914YoKkzObWFbbIIdUlqnpNJ</code>\n"
            "💲 <b>USDT (TON):</b>\n<code>UQBqKU8fvbZVZJvyAw85wQP88O0sTzFkBxW1lfbht9hGayBK</code>\n"
            "💲 <b>USDT (TRC-20):</b>\n<code>TXkiayvYBwyuX7r9dj5NvEfdF5FCJbu5kb</code>\n\n"
            "🚀 <b>Швидкий донат через xRocket:</b> /xrocket\n\n"
            "<i>Для вас це дрібниця, а для мене — величезна підтримка та мотивація! Дякую!</i> 😊"
        ),
        "/author": (
            "😎 <b>Автор бота:</b> @Author_Che.\n\n"
            "Цей бот є <i>повністю безкоштовним та не містить реклами</i>. "
            "Його мета — зробити використання Telegram простішим та зручнішим.\n\n"
            "Інші мої проєкти можна знайти тут: @wsinfo.\n\n"
            "<b>Буду вдячний за підтримку проєкту:</b> /donate"
        ),
        "/bots": (
            "<b>🤖 Мої безкоштовні боти:</b>\n\n"
            "💬 @vyfb_bot — надійний помічник для зворотного зв'язку.\n"
            "🛠️ @UniVersalAuthorBot — багатофункціональний бот (веб-версія: authorche.pp.ua/tools).\n"
            "🎲 @ac_moder_bot — модератор для груп із казино.\n"
            "📱 @ADBCheHelperBot — помічник для роботи з командами ADB.\n"

            "✅ @pollplot_bot — списки завдань та опитування.\n"
            "☁️ @authorcloud_bot — безкоштовне хмарне сховище в Telegram.\n\n"
            "<i>🥺 На жаль, через відсутність стабільного хостингу не всі боти працюють стабільно. "
            "Ваш донат допоможе відновити їхню роботу.</i>\n\n"
            "<b>Підтримати проєкти:</b> /donate"
        ),
        "/main": (
            "😅 <b>Не можу розпізнати команду.</b>\n\n"
            "Будь ласка, скористайтесь головним меню, щоб побачити доступні функції: /menu"
        ),
        "/menu": (
            "👋 <b>Привіт! Це головне меню.</b>\n\n"
            "Ось список доступних команд:\n\n"
            "😎 /author — дізнатися про автора бота.\n"
            "🤖 /bots — переглянути інші проєкти автора.\n"
            "❤️ /donate — підтримати розробку фінансово.\n"
            "📝 /menu — показати це меню ще раз."
        ),
        "start_heroku_init": "🚀 <b>Бот успішно перезапущено!</b>",
    }

    async def client_ready(self):
        self._name = utils.escape_html(get_display_name(self._client.heroku_me))
        self.doc = "Menu for bot\n"

    async def aiogram_watcher(self, message: AiogramMessage):
        # Обробка команди перезапуску
        if message.text.startswith("/start heroku init"):
            await message.answer(self.strings["start_heroku_init"])
            return

        # Основні команди
        if message.text == "/donate":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="CryptoBot 💳", url="http://t.me/send?start=IVzEgNnRlefO")]
            ])
            await message.answer(
                self.strings["/donate"].format(self._name),
                reply_markup=keyboard
            )
        elif message.text == "/menu":
            await message.answer(self.strings["/menu"])
        elif message.text == "/bots":
            await message.answer(self.strings["/bots"])
        elif message.text == "/author":
            await message.answer(self.strings["/author"])
        elif message.text == "/xrocket":
            xrocket_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="TON", url="https://t.me/xrocket?start=inv_4Wfq3fmqadtyNEP")],
                [InlineKeyboardButton(text="USDT", url="https://t.me/xrocket?start=inv_i8nnYkalSWY7n8i")],
                [InlineKeyboardButton(text="TRX", url="https://t.me/xrocket?start=inv_QOTWjNQHWLPkfrJ")],
                [InlineKeyboardButton(text="BTC", url="https://t.me/xrocket?start=inv_QYFKjAKihGWpTW1")]
            ])
            await message.answer(
                "🚀 <b>Оберіть спосіб оплати через xRocket:</b>",
                reply_markup=xrocket_keyboard
            )
        elif message.text:
            await message.answer(self.strings["/main"])

