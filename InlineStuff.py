# ©️ Vadym Yemelianov, 2025
# Універсальний модуль InlineStuff — інфо / inline / feedback
# Ліцензія: AGPLv3

import re
import string
import time
import psutil
import platform as lib_platform
import getpass
import socket
import logging
from html import escape

import telethon
from telethon.errors import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest

from aiogram.types import Message as AiogramMessage, InlineKeyboardMarkup, InlineKeyboardButton
from hikkatl.tl.types import Message
from hikkatl.utils import get_display_name

from .. import loader, utils
from ..inline.types import BotInlineMessage, InlineCall, InlineQuery

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
class InlineStuff(loader.Module):
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

    # --- Watchers ---
    @loader.watcher(
        "out",
        "only_inline",
        contains="This message will be deleted automatically",
    )
    async def watcher(self, message: Message):
        if getattr(message, "via_bot_id", None) == getattr(self.inline, "bot_id", None):
            try:
                await message.delete()
            except Exception:
                pass

    @loader.watcher("out", "only_inline", contains="Opening gallery...")
    async def gallery_watcher(self, message: Message):
        if getattr(message, "via_bot_id", None) != getattr(self.inline, "bot_id", None):
            return

        m = re.search(r"#id: ([a-zA-Z0-9]+)", getattr(message, "raw_text", "") or "")
        if not m:
            return
        id_ = m[1]

        try:
            await message.delete()
        except Exception:
            pass

        try:
            m2 = await message.respond("🪐", reply_to=utils.get_topic(message))
            await self.inline.gallery(
                message=m2,
                next_handler=self.inline._custom_map[id_]["handler"],
                caption=self.inline._custom_map[id_].get("caption", ""),
                force_me=self.inline._custom_map[id_].get("force_me", False),
                disable_security=self.inline._custom_map[id_].get("disable_security", False),
                silent=True,
            )
        except Exception:
            return

    # --- Check bot via BotFather ---
    async def _check_bot(self, username: str) -> bool:
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                try:
                    await self._client(UnblockRequest(id="@BotFather"))
                except Exception:
                    pass
                m = await conv.send_message("/token")

            r = await conv.get_response()

            try:
                await m.delete()
                await r.delete()
            except Exception:
                pass

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                return False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if username != button.text.strip("@"):
                        continue

                    try:
                        m2 = await conv.send_message("/cancel")
                        r2 = await conv.get_response()
                        await m2.delete()
                        await r2.delete()
                    except Exception:
                        pass

                    return True
        return False

    # --- Commands for inline bot username/token ---
    @loader.command()
    async def ch_bot_username(self, message: Message):
        """<username> - Змінити username inline бота"""
        args = utils.get_args_raw(message)
        if args:
            args = args.strip("@")
        if (
            not args
            or not args.lower().endswith("bot")
            or len(args) <= 4
            or any(ch not in (string.ascii_letters + string.digits + "_") for ch in args)
        ):
            await utils.answer(message, self.strings["bot_username_invalid"])
            return

        try:
            await self._client.get_entity(f"@{args}")
        except ValueError:
            pass
        else:
            if not await self._check_bot(args):
                await utils.answer(message, self.strings["bot_username_occupied"])
                return

        self._db.set("inline.bot", "custom_bot", args)
        self._db.set("inline.bot", "bot_token", None)
        await utils.answer(message, self.strings["bot_updated"])

    @loader.command()
    async def ch_bot_token(self, message: Message):
        """<token> - Встановити токен для inline бота"""
        args = utils.get_args_raw(message)
        if not args or not re.match(r'[0-9]{8,10}:[a-zA-Z0-9_-]{34,36}', args):
            await utils.answer(message, self.strings['token_invalid'])
            return
        self._db.set("inline.bot", "bot_token", args)
        await utils.answer(message, self.strings["bot_updated"])

    # --- System info rendering ---
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
        # надсилаємо фото + підпис
        try:
            await self.inline.form(
                message=message,
                text=self._render_sysinfo(),
                photo=self.config["sysinfo_banner_url"],
                reply_markup=[
                    [{"text": "🔻 Закрити", "callback": self.delete_form}],
                ],
            )
        except Exception:
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
        try:
            await call.delete()
        except Exception:
            pass

    # --- Фідбек команди ---
    @loader.command()
    async def flink(self, message):
        """- Отримати посилання на фідбек бота"""
        try:
            botname = getattr(self.inline, "bot_username", None) or "bot"
            slinkbot = f"{self.strings['flink']}: https://t.me/{botname}?start=feedback"
            await utils.answer(message, slinkbot)
        except Exception:
            await utils.answer(message, self.strings['flink'])

    @loader.command()
    async def banfeedback(self, message):
        """[UserID] - Заблокувати користувача фідбек бота"""
        user_id = utils.get_args_raw(message)
        if not user_id:
            await utils.answer(message, self.strings["not_arg"])
            return
        try:
            user_id = int(user_id)
        except Exception:
            await utils.answer(message, self.strings["not_arg"])
            return
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
            return
        try:
            user_id = int(user_id)
        except Exception:
            await utils.answer(message, self.strings["not_arg"])
            return
        if user_id in self._ban_list:
            self._ban_list.remove(user_id)
            self.db.set("UniversalInfoMod", "ban_list", self._ban_list)
            await utils.answer(message, self.strings["successfully_unban"])
        else:
            await utils.answer(message, self.strings["not_in_ban"])

    # --- Inline Handler ---
    @loader.inline_everyone
    async def info_inline_handler(self, query: InlineQuery) -> list:
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

    # --- Фідбек обробник (підв'язаний бот) ---
    async def aiogram_watcher(self, message: AiogramMessage):
        """Обробник команд для підв'язаного бота"""
        text = getattr(message, "text", "") or ""

        # /start — показує стартове повідомлення з фото, якщо доступне
        if text == "/start":
            textmsg = self.config["start_custom_text"] or self.strings["start_message"]
            try:
                await message.answer_photo(self.config["sysinfo_banner_url"], caption=textmsg)
            except Exception:
                try:
                    await message.answer(textmsg)
                except Exception:
                    pass
            return

        # /menu
        if text == "/menu":
            try:
                await message.answer(self.strings["/menu"])
            except Exception:
                pass
            return

        # /donate
        if text == "/donate":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="CryptoBot 💳", url=self.config["cryptobot_url"])]
            ])
            try:
                await message.answer(self.strings["/donate"], reply_markup=keyboard)
            except Exception:
                pass
            return

        # /profile - тільки власнику
        if text == "/profile":
            if not hasattr(self, "_me") or message.from_user.id != self._me.id:
                try:
                    await message.answer("❌ You are not allowed to use this")
                except Exception:
                    pass
                return

            caption = self.strings["profile_cmd"].format(
                prefix=self.get_prefix(),
                ram_usage=utils.get_ram_usage(),
                cpu_usage=utils.get_cpu_usage(),
                host=utils.get_named_platform()
            )
            try:
                await message.answer_photo(
                    self.config["sysinfo_banner_url"],
                    caption=caption,
                    reply_markup=self.inline.generate_markup(
                        markup_obj=[
                            [
                                {"text": "🚀 Restart", "callback": self.restart, "args": (message,)},
                            ],
                            [
                                {"text": "⚠️ Reset prefix", "callback": self.reset_prefix, "args": (message,)},
                            ],
                        ]
                    )
                )
            except Exception:
                pass
            return

        # Фідбек логіка
        if self.config["feedback_mode"] and message.from_user.id not in self._ban_list:
            if text == "/start feedback":
                text2 = self.config["start_custom_text"] or self.strings["feedback_start"]
                try:
                    await message.answer(text2)
                except Exception:
                    pass
                return

            if text == "/nometa":
                meta_text = self.config["no_meta"]
                if self.config["no_meta_baner"] is None:
                    try:
                        await self.inline.bot.send_message(chat_id=message.from_user.id, text=meta_text)
                    except Exception:
                        pass
                else:
                    try:
                        await self.inline.bot.send_photo(chat_id=message.from_user.id, photo=self.config["no_meta_baner"], caption=meta_text)
                    except Exception:
                        pass
                return

            # Відповідь власника
            if hasattr(self, "_me") and message.from_user.id == self._me.id:
                state = self.db.get("UniversalInfoMod", "state")
                if isinstance(state, str) and state.startswith("waiting_"):
                    parts = state.split("_")
                    if len(parts) >= 3:
                        try:
                            to_id = int(parts[1])
                            waiting_message_id = int(parts[2])
                            custom_text = f"{self.strings['owner_answer']}:\n\n{message.text}"
                            await self.inline.bot.send_message(chat_id=to_id, text=custom_text)
                            try:
                                await self.inline.bot.delete_message(chat_id=self._me.id, message_id=waiting_message_id)
                            except Exception:
                                pass
                            await self.inline.bot.send_message(chat_id=self._me.id, text=self.strings["successfully_send"])
                            self.db.set("UniversalInfoMod", "state", "done")
                        except Exception:
                            pass
                    return

            # Звичайне повідомлення від користувача (фідбек)
            if (message.text and not message.text.startswith('/')) or getattr(message, "caption", None):
                original_text = getattr(message, "caption", None) or message.text
                user_id = message.from_user.id
                
                WriteInPM = f'<b><a href="tg://user?id={user_id}">✏️Написати в особисті</a></b>'
                custom_text = f"{self.strings['new_m']} {escape(message.from_user.first_name)}:\n\n{escape(original_text) if original_text is not None else self.strings['not_text']}\n\nUserID: {message.from_user.id}\n{WriteInPM}"

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

                try:
                    await self.inline.bot.send_message(chat_id=self._me.id, text=custom_text, reply_markup=reply_markup)
                    await self.inline.bot.send_message(chat_id=message.from_user.id, text=self.strings['successfully_send'])
                except Exception:
                    pass
                return

        # Інші команди
        if text == "/bots":
            try:
                await message.answer(self.strings["/bots"])
            except Exception:
                pass
            return

        if text == "/author":
            try:
                await message.answer(self.strings["/author"])
            except Exception:
                pass
            return

        if text == "/feedback":
            try:
                await message.answer(self.strings["/feedback"])
            except Exception:
                pass
            return

        if text == "/xrocket":
            xrocket_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="TON", url="https://t.me/xrocket?start=inv_4Wfq3fmqadtyNEP")],
                [InlineKeyboardButton(text="USDT", url="https://t.me/xrocket?start=inv_i8nnYkalSWY7n8i")],
                [InlineKeyboardButton(text="TRX", url="https://t.me/xrocket?start=inv_QOTWjNQHWLPkfrJ")],
                [InlineKeyboardButton(text="BTC", url="https://t.me/xrocket?start=inv_QYFKjAKihGWpTW1")]
            ])
            try:
                await message.answer("🚀 <b>Оберіть спосіб оплати через xRocket:</b>", reply_markup=xrocket_keyboard)
            except Exception:
                pass
            return

        if text and text.startswith('/'):
            try:
                await message.answer(self.strings["/main"])
            except Exception:
                pass
            return

    # --- Feedback callback handler ---
    async def feedback_callback_handler(self, call: InlineCall):
        if getattr(call, "data", "") == "MessageDelete":
            try:
                await self.inline.bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            except Exception:
                pass
            return
            
        if getattr(call, "data", "").startswith("ban_"):
            try:
                user_id = int(call.data.split("_", 1)[1])
            except Exception:
                return
            if user_id not in self._ban_list:
                self._ban_list.append(user_id)
                self.db.set("UniversalInfoMod", "ban_list", self._ban_list)
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🔓 Розблокувати", callback_data=f"unban_{user_id}")
                    ]
                ]
            )
            try:
                await self.inline.bot.send_message(chat_id=self._me.id, text=f"{self.strings['successfully_ban']} ({user_id})", reply_markup=reply_markup)
            except Exception:
                pass
            return
            
        if getattr(call, "data", "").startswith("unban_"):
            try:
                user_id = int(call.data.split("_", 1)[1])
            except Exception:
                return
            if user_id in self._ban_list:
                self._ban_list.remove(user_id)
                self.db.set("UniversalInfoMod", "ban_list", self._ban_list)
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🔐 Заблокувати", callback_data=f"ban_{user_id}")
                    ]
                ]
            )
            try:
                await self.inline.bot.send_message(chat_id=self._me.id, text=f"{self.strings['successfully_unban']} ({user_id})", reply_markup=reply_markup)
            except Exception:
                pass
            return
            
        if getattr(call, "data", "").startswith("reply"):
            try:
                user_id = int(call.data.split("_", 1)[1])
            except Exception:
                return
            try:
                self.db.set("UniversalInfoMod", "state", f"waiting_{user_id}_{call.message.message_id}")
                reply_markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_reply")
                        ]
                    ]
                )
                await self.inline.bot.send_message(chat_id=self._me.id, text=self.strings["waiting_answer"], reply_markup=reply_markup)
            except Exception:
                pass
            return
            
        if getattr(call, "data", "") == "cancel_reply":
            try:
                self.db.set("UniversalInfoMod", "state", "done")
                await self.inline.bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            except Exception:
                pass
            return

    # --- Restart / Reset prefix (Inline buttons) ---
    async def restart(self, call: InlineCall, message):
        try:
            await call.edit(self.strings["restart"])
        except Exception:
            pass
        try:
            await self.invoke("restart", "-f", message=message, peer=self.inline.bot.id)
        except Exception:
            pass

    async def reset_prefix(self, call: InlineCall, message):
        try:
            await message.answer(self.strings["prefix_reset"])
        except Exception:
            pass
        try:
            self.db.set("inline.main", "command_prefix", ".")
        except Exception:
            pass