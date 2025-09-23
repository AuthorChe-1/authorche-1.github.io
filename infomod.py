import time
import psutil
import platform as lib_platform
import getpass
import telethon
import socket
import logging

from aiogram.types import Message as AiogramMessage, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery as AiogramCallbackQuery
from hikkatl.tl.types import Message
from hikkatl.utils import get_display_name
from ..inline.types import InlineCall, InlineQuery
from html import escape
from .. import loader, utils

logger = logging.getLogger(__name__)

# --- Helper functions ---
def bytes2human(n):
    symbols = ('B','K','M','G','T','P')
    prefix = {s:1<<(i*10) for i,s in enumerate(symbols[1:],1)}
    for s in reversed(symbols[1:]):
        if n >= prefix[s]:
            return f"{n/prefix[s]:.2f}{s}"
    return f"{n}B"

def format_uptime(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return f"{int(d)}д {int(h)}г {int(m)}хв"

def get_distro_info():
    name = ver = "N/A"
    try:
        with open("/etc/os-release") as f:
            data = dict(line.strip().split("=", 1) for line in f if "=" in line)
        name = data.get("PRETTY_NAME", data.get("NAME", "Невідомо")).strip('"')
        ver = data.get("VERSION_ID", "").strip('"')
    except: pass
    return name, ver

def get_cpu_model():
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":",1)[1].strip()
    except: pass
    return lib_platform.processor() or "Невідомо"

@loader.tds
class UniversalInfoMod(loader.Module):
    """Універсальний інформаційний модуль з фідбек системою"""

    strings = {
        "name": "Універсальний Інфо",
        
        # Фідбек система
        "new_m": "🗣 Нове повідомлення від",
        "not_text": "🔎 Текст не знайдено.",
        "waiting_answer": "⏳ Очікування відповіді користувача",
        "flink": "Ось моє посилання на фідбек бота",
        "owner_answer": "🗣 Відповідь власника",
        "successfully_send": "💬 Повідомлення успішно відправлено",
        "not_arg": "❌ Не вказано UserID",
        "successfully_ban": "✅ Користувача успішно заблоковано",
        "successfully_unban": "✅ Користувача успішно розблоковано",
        "already_banned": "🚫 Користувач вже заблокований",
        "not_in_ban": "✅ Користувач не знаходиться в списку заблокованих",
        "reply_button": "📃 Відповісти",
        "feedback_description": "Написати повідомлення розробнику",
        "feedback_help": "Щоб надіслати повідомлення, просто напишіть його сюди.",
        "feedback_start": "Ласкаво просимо до фідбек бота! Напишіть своє повідомлення, і я його перешлю розробнику.",
        
        # Системна інформація
        "send_sysinfo": "Надіслати системну інформацію",
        "sysinfo_description": "ℹ Детальна інформація про сервер",
        "send_donate_info": "Надіслати інформацію для донату",
        "donate_description": "❤️ Підтримати автора фінансово",
        "donate_text": """<b>Підтримайте мою творчість</b>
<i>Кожен внесок розпалює нові ідеї і дозволяє створювати більше віршів та музики.</i>
<b>💳 Банківські картки</b>
🍏ABank24
<code>4323 3473 9773 4135</code>
💵Privat24
<code>5168 7451 5064 0644</code>
<b>Криптовалюта</b>
🪙BTC
<code>123MgBkkpu6XwrU53SvrBxiW9useRSt6qR</code>
💎TON
<code>UQDicYt03peG8l0CBCKW2YQJ914YoKkzObWFbbIIdUlqnpNJ</code>
💸USDT (TON)
<code>UQBqKU8fvbZVZJvyAw85wQP88O0sTzFkBxW1lfbht9hGayBK</code>
💸USDT (TRX)
<code>TXkiayvYBwyuX7r9dj5NvEfdF5FCJbu5kb</code>
Дякую за вашу підтримку 🚀""",
        "close_button": "🔻 Закрити",
        "website_button": "Підтримати на сайті",
        "cryptobot_button": "CryptoBot",
        "xrocket_button": "xRocket",
        
        # Команди бота
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
            "😎 /author — дізнатися про автора бота\n"
            "🤖 /bots — переглянути інші проєкти автора\n"
            "❤️ /donate — підтримати розробку фінансово\n"
            "💬 /feedback — зв'язатися з розробником\n"
            "📋 /nometa — правила спілкування\n"
            "📝 /menu — показати це меню ще раз\n\n"
            "<b>Просто напишіть повідомлення</b> — і я передам його розробнику!"
        ),
        "/feedback": (
            "💬 <b>Зв'язок з розробником</b>\n\n"
            "Щоб зв'язатися зі мною, просто напишіть будь-яке повідомлення в цьому чаті!\n\n"
            "✉️ <b>Як це працює:</b>\n"
            "- Ви пишете повідомлення тут\n"
            "- Я його одразу пересилаю розробнику\n"
            "- Він вам відповість особисто\n\n"
            "📋 <b>Перед надсиланням ознайомтесь з правилами:</b> /nometa\n\n"
            "<i>Напишіть ваше питання або пропозицію, і я обов'язково її передам!</i>"
        ),
        "/nometa": (
            "<b>Увага!</b>\n\n"
            "Будь ласка, не задавайте мені питання такі, як:\n\n"
            "• «Привіт»\n"
            "• «Як справи?»\n" 
            "• «Що робиш?»\n"
            "• «Чим займаєшся?»\n"
            "• та інші подібні\n\n"
            "Якщо ви хочете у мене щось запитати, питайте по суті, а також всю суть питання опишіть в одному повідомленні.\n\n"
            "<i>Це дозволить економити час і отримати якісну відповідь!</i>"
        ),
        "start_heroku_init": "🚀 <b>Бот успішно перезапущено!</b>",
        "start_message": (
            "👋 <b>Привіт! Я багатофункціональний бот</b>\n\n"
            "Я можу передавати повідомлення розробнику та надавати корисну інформацію.\n\n"
            "📋 <b>Доступні команди:</b>\n"
            "• /menu — головне меню\n"
            "• /author — інформація про автора\n"
            "• /bots — інші боти автора\n"
            "• /donate — підтримати проєкт\n"
            "• /feedback — зв'язок з розробником\n"
            "• /nometa — правила спілкування\n\n"
            "💬 <b>Просто напишіть повідомлення</b> — і я передам його розробнику!"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            # Фідбек налаштування
            loader.ConfigValue(
                "feedback_mode",
                True,
                "Увімкнути/вимкнути функціонал фідбек бота",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "start_custom_text",
                None,
                "Введіть кастомний текст для привітання",
            ),
            loader.ConfigValue(
                "no_meta",
                "<b>Увага!</b>\nБудь ласка, не задавайте мені питання такі, як:\n\n«Привіт» , «Як справи?» , «Що робиш?» , «Чим займаєшся?» і т.д.\n\nЯкщо ви хочете у мене щось запитати, питайте по суті, а також всю суть питання опишіть в одному повідомленні.",
                "Введіть кастомний текст для команди /nometa",
            ),
            loader.ConfigValue(
                "no_meta_baner",
                "https://te.legra.ph/file/91a54dee84cf1ec5990fd.jpg",
                "Введіть кастомне посилання на мета-банер",
                validator=loader.validators.Link(),
            ),
            
            # Інфо налаштування
            loader.ConfigValue(
                "donate_text",
                None,
                "Текст, що відображається в команді .info",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "donate_banner_url",
                "https://authorche.top/poems/logo.jpg",
                "URL банера для команди .info",
                validator=loader.validators.Link(),
            ),
            loader.ConfigValue(
                "sysinfo_banner_url",
                "https://raw.githubusercontent.com/AuthorChe-1/authorche-1.github.io/refs/heads/main/start.jpg",
                "URL банера для інлайн-режиму sysinfo",
                validator=loader.validators.Link(),
            ),
            loader.ConfigValue(
                "website_url",
                "https://authorche.top/sup",
                "URL-адреса для кнопки 'Підтримати на сайті'",
                validator=loader.validators.Link(),
            ),
            loader.ConfigValue(
                "cryptobot_url",
                "https://t.me/send?start=IVzEgNnRlefO",
                "URL-адреса для кнопки 'CryptoBot'",
                validator=loader.validators.Link(),
            ),
            loader.ConfigValue(
                "xrocket_url",
                "https://t.me/acdonate_bot?start=xrocket",
                "URL-адреса для кнопки 'xRocket'",
                validator=loader.validators.Link(),
            ),
        )

    async def on_dlmod(self, client, db):
        self.db.set("UniversalInfoMod", "ban_list", [])

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me()
        self._name = utils.escape_html(get_display_name(self._me))
        
        # Фідбек ініціалізація
        self.forwarding_enabled = {}
        self._ban_list = self.db.get("UniversalInfoMod", "ban_list", [])
        self.db.set("UniversalInfoMod", "state", "done")

    def _render_sysinfo(self):
        uname = lib_platform.uname()
        boot = psutil.boot_time()
        uptime = time.time() - boot
        freq = psutil.cpu_freq()
        load = psutil.cpu_percent(interval=0.5)
        user = getpass.getuser()
        vm, sm = psutil.virtual_memory(), psutil.swap_memory()
        net = psutil.net_io_counters()
        io = psutil.disk_io_counters()
        distro_name, distro_ver = get_distro_info()
        cpu_model = get_cpu_model()

        net_info = []
        for iface, addrs in psutil.net_if_addrs().items():
            ip = mac = "—"
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip = addr.address
                elif hasattr(socket, 'AF_PACKET') and addr.family == socket.AF_PACKET:
                    mac = addr.address
            net_info.append(f"<b>{iface}</b>: IP <code>{ip}</code>, MAC <code>{mac}</code>")

        freq_str = f"{freq.current:.0f} MHz" if freq else "N/A"

        return (
            f"<blockquote><emoji document_id=5776118099812028333>📟</emoji> <b>Інформація про систему</b>\n\n"
            f"<emoji document_id=5215186239853964761>🖥️</emoji> <b><u>ОС та система:</u></b>\n"
            f"<b>ОС:</b> <code>{uname.system} {uname.release}</code>\n"
            f"<b>Дистрибутив:</b> <code>{distro_name} {distro_ver}</code>\n"
            f"<b>Ядро:</b> <code>{uname.version}</code>\n"
            f"<b>Архітектура:</b> <code>{uname.machine}</code>\n"
            f"<b>Користувач:</b> <code>{user}</code>\n\n"
            f"<emoji document_id=5341715473882955310>⚙️</emoji> <b><u>Процесор:</u></b>\n"
            f"<b>Модель:</b> <code>{cpu_model}</code>\n"
            f"<b>Ядра:</b> <code>{psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}</code>\n"
            f"<b>Частота:</b> <code>{freq_str}</code>\n"
            f"<b>Навантаження:</b> <code>{load}%</code>\n\n"
            f"<emoji document_id=5237799019329105246>🧠</emoji> <b><u>Оперативна пам'ять:</u></b>\n"
            f"<b>Використано:</b> <code>{bytes2human(vm.used)}</code> / <code>{bytes2human(vm.total)}</code>\n"
            f"<b>Файл підкачки:</b> <code>{bytes2human(sm.used)}</code> / <code>{bytes2human(sm.total)}</code>\n\n"
            f"<emoji document_id=5462956611033117422>💾</emoji> <b><u>Диск:</u></b>\n"
            f"<b>Читання:</b> <code>{bytes2human(io.read_bytes)}</code>\n"
            f"<b>Запис:</b> <code>{bytes2human(io.write_bytes)}</code>\n\n"
            f"<emoji document_id=5321141214735508486>📡</emoji> <b><u>Мережа:</u></b>\n"
            f"<b>Отримано:</b> <code>{bytes2human(net.bytes_recv)}</code>\n"
            f"<b>Відправлено:</b> <code>{bytes2human(net.bytes_sent)}</code>\n"
            f"{chr(10).join(net_info)}\n\n"
            f"<emoji document_id=5382194935057372936>⏱</emoji> <b><u>Час роботи:</u></b>\n"
            f"<b>З:</b> <code>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(boot))}</code>\n"
            f"<b>Аптайм:</b> <code>{format_uptime(uptime)}</code>\n\n"
            f"<emoji document_id=5854908544712707500>📦</emoji> <b><u>Версії:</u></b>\n"
            f"<b>Python:</b> <code>{lib_platform.python_version()}</code>\n"
            f"<b>Telethon:</b> <code>{telethon.__version__}</code></blockquote>"
        )

    # --- Userbot Commands ---

    @loader.command()
    async def sysinfo(self, message: Message):
        """Надіслати детальну системну інформацію про сервер"""
        await utils.answer(message, self._render_sysinfo())
    
    @loader.command()
    async def info(self, message: Message):
        """Надіслати інформацію для підтримки проєкту"""
        donate_text = self.config["donate_text"] or self.strings["donate_text"]
        await self.inline.form(
            message=message,
            text=donate_text,
            photo=self.config["donate_banner_url"],
            reply_markup=[
                [{"text": self.strings["website_button"], "url": self.config["website_url"]}],
                [
                    {"text": self.strings["cryptobot_button"], "url": self.config["cryptobot_url"]},
                    {"text": self.strings["xrocket_button"], "url": self.config["xrocket_url"]},
                ],
                [{"text": self.strings["close_button"], "callback": self.delete_form}],
            ],
        )

    async def delete_form(self, call):
        await call.delete()

    # --- Фідбек команди ---

    @loader.command()
    async def flink(self, message):
        """- Отримати посилання на фідбек бота"""
        slinkbot = f"{self.strings['flink']}: https://t.me/{self.inline.bot_username}?start=feedback"
        await utils.answer(message, slinkbot)

    @loader.command()
    async def banfeedback(self, message):
        """[UserID] - Заблокувати користувача фідбек бота"""
        user_id = utils.get_args_raw(message)
        if not user_id:
            await utils.answer(message, self.strings["not_arg"])
        else:
            user_id = int(user_id)
            if user_id not in self._ban_list:
                self._ban_list.append(user_id)
                self.db.set("UniversalInfoMod", "ban_list", self._ban_list)
                await utils.answer(message, self.strings["successfully_ban"])
            else:
                await utils.answer(message, self.strings["already_banned"])

    @loader.command()
    async def unbanfeedback(self, message):
        """[UserID] - Розблокувати користувача фідбек бота"""
        user_id = utils.get_args_raw(message)
        if not user_id:
            await utils.answer(message, self.strings["not_arg"])
        else:
            user_id = int(user_id)
            if user_id in self._ban_list:
                self._ban_list.remove(user_id)
                self.db.set("UniversalInfoMod", "ban_list", self._ban_list)
                await utils.answer(message, self.strings["successfully_unban"])
            else:
                await utils.answer(message, self.strings["not_in_ban"])

    # --- Inline Handler ---

    @loader.inline_everyone
    async def info_inline_handler(self, query: InlineQuery) -> dict:
        """Обробляє інлайн-запити для sysinfo та info"""
        donate_text = self.config["donate_text"] or self.strings["donate_text"]
        
        info_result = {
            "title": self.strings["send_donate_info"],
            "description": self.strings["donate_description"],
            "caption": donate_text,
            "photo": self.config["donate_banner_url"],
            "thumb": self.config["donate_banner_url"],
            "reply_markup": [
                [{"text": self.strings["website_button"], "url": self.config["website_url"]}],
                [
                    {"text": self.strings["cryptobot_button"], "url": self.config["cryptobot_url"]},
                    {"text": self.strings["xrocket_button"], "url": self.config["xrocket_url"]},
                ],
            ],
        }

        sysinfo_result = {
            "title": self.strings["send_sysinfo"],
            "description": self.strings["sysinfo_description"],
            "message": self._render_sysinfo(),
            "thumb": self.config["sysinfo_banner_url"],
        }
        
        return [info_result, sysinfo_result]

    # --- Фідбек обробник ---
    async def aiogram_watcher(self, message: AiogramMessage):
        """Обробник команд для підв'язаного бота"""
        
        # Перевірка для фідбеку
        if self.config["feedback_mode"] and message.from_user.id not in self._ban_list:
            if message.text == "/start feedback":
                text = self.config["start_custom_text"] or self.strings["feedback_start"]
                await message.answer(text)
                return

            elif message.text == "/nometa":
                meta_text = self.config["no_meta"]
                if self.config["no_meta_baner"] is None:
                    await self.inline.bot.send_message(
                        chat_id=message.from_user.id, text=meta_text
                    )
                else:
                    await self.inline.bot.send_photo(
                        chat_id=message.from_user.id,
                        photo=self.config["no_meta_baner"],
                        caption=meta_text,
                    )
                return

            # Обробка відповіді від власника
            if message.from_user.id == self._me.id:
                state = self.db.get("UniversalInfoMod", "state")
                if state.startswith("waiting_"):
                    to_id = int(state.split("_")[1])
                    waiting_message_id = int(state.split("_")[2])
                    custom_text = f"{self.strings['owner_answer']}:\n\n{message.text}"
                    await self.inline.bot.send_message(chat_id=to_id, text=custom_text)
                    await self.inline.bot.delete_message(
                        chat_id=message.chat.id, message_id=waiting_message_id
                    )
                    await self.inline.bot.send_message(
                        chat_id=self._me.id, text=f"{self.strings['successfully_send']}"
                    )
                    self.db.set("UniversalInfoMod", "state", "done")
                    return

            # Обробка звичайних повідомлень користувача
            if (message.text and not message.text.startswith('/')) or message.caption:
                original_text = message.caption if message.caption else message.text
                user_id = message.from_user.id
                
                WriteInPM = f'<b><a href="tg://user?id={user_id}">✏️Написати в особисті</a></b>'
                custom_text = f"{self.strings['new_m']} {escape(message.from_user.first_name)}:\n\n{escape(original_text) if original_text is not None else self.strings['not_text']}\n\nUserID: {message.from_user.id}\n{WriteInPM}"

                # Створюємо кнопки як у оригінальному модулі AuroraFeedBack
                buttons = [
                    [
                        InlineKeyboardButton(
                            text=self.strings["reply_button"], 
                            callback_data=f"reply_{user_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(text="🔐 Заблокувати", callback_data=f"ban_{user_id}"),
                        InlineKeyboardButton(text="🗑️ Видалити", callback_data="MessageDelete")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)

                await self.inline.bot.send_message(
                    chat_id=self._me.id, text=custom_text, reply_markup=reply_markup
                )
                await self.inline.bot.send_message(
                    chat_id=message.from_user.id, text=f"{self.strings['successfully_send']}"
                )
                return

        # Команди бота
        if message.text and message.text.startswith("/start heroku init"):
            await message.answer(self.strings["start_heroku_init"])
            return

        if message.text == "/donate":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="CryptoBot 💳", url=self.config["cryptobot_url"])]
            ])
            await message.answer(self.strings["/donate"], reply_markup=keyboard)
        elif message.text == "/menu" or message.text == "/start":
            await message.answer(self.strings["/menu"])
        elif message.text == "/bots":
            await message.answer(self.strings["/bots"])
        elif message.text == "/author":
            await message.answer(self.strings["/author"])
        elif message.text == "/feedback":
            await message.answer(self.strings["/feedback"])
        elif message.text == "/nometa":
            await message.answer(self.strings["/nometa"])
        elif message.text == "/xrocket":
            xrocket_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="TON", url="https://t.me/xrocket?start=inv_4Wfq3fmqadtyNEP")],
                [InlineKeyboardButton(text="USDT", url="https://t.me/xrocket?start=inv_i8nnYkalSWY7n8i")],
                [InlineKeyboardButton(text="TRX", url="https://t.me/xrocket?start=inv_QOTWjNQHWLPkfrJ")],
                [InlineKeyboardButton(text="BTC", url="https://t.me/xrocket?start=inv_QYFKjAKihGWpTW1")]
            ])
            await message.answer("🚀 <b>Оберіть спосіб оплати через xRocket:</b>", reply_markup=xrocket_keyboard)
        elif message.text and message.text.startswith('/'):
            await message.answer(self.strings["/main"])

    # --- Обробник кнопок фідбеку ---
    async def feedback_callback_handler(self, call: InlineCall):
        if call.data == "MessageDelete":
            await self.inline.bot.delete_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
            )
            return
            
        if call.data.startswith("ban_"):
            user_id = int(call.data.split("_")[1])
            if user_id not in self._ban_list:
                self._ban_list.append(user_id)
                self.db.set("UniversalInfoMod", "ban_list", self._ban_list)
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔓 Розблокувати", callback_data=f"unban_{user_id}"
                        )
                    ]
                ]
            )
            await self.inline.bot.send_message(
                chat_id=self._me.id,
                text=f"{self.strings['successfully_ban']} ({user_id})",
                reply_markup=reply_markup,
            )
            return
            
        if call.data.startswith("unban_"):
            user_id = int(call.data.split("_")[1])
            if user_id in self._ban_list:
                self._ban_list.remove(user_id)
                self.db.set("UniversalInfoMod", "ban_list", self._ban_list)
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔐 Заблокувати", callback_data=f"ban_{user_id}"
                        )
                    ]
                ]
            )
            await self.inline.bot.send_message(
                chat_id=self._me.id,
                text=f"{self.strings['successfully_unban']} ({user_id})",
                reply_markup=reply_markup,
            )
            return
            
        if call.data.startswith("reply"):
            user_id = int(call.data.split("_")[1])
            self.db.set(
                "UniversalInfoMod",
                "state",
                f"waiting_{user_id}_{call.message.message_id}",
            )
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="❌ Скасувати", callback_data=f"cancel_reply"
                        )
                    ]
                ]
            )
            await self.inline.bot.send_message(
                chat_id=self._me.id,
                text=f"{self.strings['waiting_answer']}",
                reply_markup=reply_markup,
            )
            
        if call.data == "cancel_reply":
            self.db.set("UniversalInfoMod", "state", "done")
            await self.inline.bot.delete_message(
                chat_id=call.message.chat.id, message_id=call.message.message_id
            )