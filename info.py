import time
import psutil
import platform as lib_platform
import getpass
import telethon
import socket
import logging
import abc

from aiogram.types import Message as AiogramMessage, InlineKeyboardMarkup, InlineKeyboardButton
from hikkatl.tl.types import Message
from hikkatl.utils import get_display_name
from .. import loader, utils
from ..inline.types import InlineQuery

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
    return f"{int(d)}d {int(h)}h {int(m)}m"

def get_distro_info():
    name = ver = "N/A"
    try:
        with open("/etc/os-release") as f:
            data = dict(line.strip().split("=", 1) for line in f if "=" in line)
        name = data.get("PRETTY_NAME", data.get("NAME", "Unknown")).strip('"')
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
    return lib_platform.processor() or "Unknown"

@loader.tds
class InfoMod(loader.Module):
    """Універсальний інформаційний модуль з розширеним функціоналом"""

    strings = {
        "name": "Інфо",
        # --- Strings for sysinfo command ---
        "send_sysinfo": "Надіслати системну інформацію",
        "sysinfo_description": "ℹ Детальна інформація про сервер",
        # --- Strings for info (donate) command ---
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
        # --- Strings for bot commands ---
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

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "donate_text",
                self.strings["donate_text"],
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

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me()
        self._name = utils.escape_html(get_display_name(self._me))

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
            f"<blockquote><emoji document_id=5776118099812028333>📟</emoji> <b>System Info</b>\n\n"
            f"<emoji document_id=5215186239853964761>🖥️</emoji> <b><u>ОС и система:</u></b>\n"
            f"<b>OS:</b> <code>{uname.system} {uname.release}</code>\n"
            f"<b>Distro:</b> <code>{distro_name} {distro_ver}</code>\n"
            f"<b>Kernel:</b> <code>{uname.version}</code>\n"
            f"<b>Arch:</b> <code>{uname.machine}</code>\n"
            f"<b>User:</b> <code>{user}</code>\n\n"
            f"<emoji document_id=5341715473882955310>⚙️</emoji> <b><u>CPU:</u></b>\n"
            f"<b>Model:</b> <code>{cpu_model}</code>\n"
            f"<b>Cores:</b> <code>{psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}</code>\n"
            f"<b>Freq:</b> <code>{freq_str}</code>\n"
            f"<b>Load:</b> <code>{load}%</code>\n\n"
            f"<emoji document_id=5237799019329105246>🧠</emoji> <b><u>RAM:</u></b>\n"
            f"<b>Used:</b> <code>{bytes2human(vm.used)}</code> / <code>{bytes2human(vm.total)}</code>\n"
            f"<b>Swap:</b> <code>{bytes2human(sm.used)}</code> / <code>{bytes2human(sm.total)}</code>\n\n"
            f"<emoji document_id=5462956611033117422>💾</emoji> <b><u>Диск:</u></b>\n"
            f"<b>Read:</b> <code>{bytes2human(io.read_bytes)}</code>\n"
            f"<b>Write:</b> <code>{bytes2human(io.write_bytes)}</code>\n\n"
            f"<emoji document_id=5321141214735508486>📡</emoji> <b><u>Сеть:</u></b>\n"
            f"<b>Recv:</b> <code>{bytes2human(net.bytes_recv)}</code>\n"
            f"<b>Sent:</b> <code>{bytes2human(net.bytes_sent)}</code>\n"
            f"{chr(10).join(net_info)}\n\n"
            f"<emoji document_id=5382194935057372936>⏱</emoji> <b><u>Аптайм:</u></b>\n"
            f"<b>Since:</b> <code>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(boot))}</code>\n"
            f"<b>Uptime:</b> <code>{format_uptime(uptime)}</code>\n\n"
            f"<emoji document_id=5854908544712707500>📦</emoji> <b><u>Версии:</u></b>\n"
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
        await self.inline.form(
            message=message,
            text=str(self.config["donate_text"]),
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

    # --- Inline Handler ---

    @loader.inline_everyone
    async def info_inline_handler(self, query: InlineQuery) -> dict:
        """Переглянути інформацію про систему та пітримку проєкту."""
        info_result = {
            "title": self.strings("send_donate_info"),
            "description": self.strings("donate_description"),
            "caption": self.config["donate_text"],
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
            "title": self.strings("send_sysinfo"),
            "description": self.strings("sysinfo_description"),
            "message": self._render_sysinfo(),
            "thumb": self.config["sysinfo_banner_url"],
        }
        
        return [info_result, sysinfo_result]

    # --- Bot Commands Watcher ---

    async def aiogram_watcher(self, message: AiogramMessage):
        """Обробник команд для підв'язаного бота"""
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
        elif message.text == "/xrocket":
            xrocket_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="TON", url="https://t.me/xrocket?start=inv_4Wfq3fmqadtyNEP")],
                [InlineKeyboardButton(text="USDT", url="https://t.me/xrocket?start=inv_i8nnYkalSWY7n8i")],
                [InlineKeyboardButton(text="TRX", url="https://t.me/xrocket?start=inv_QOTWjNQHWLPkfrJ")],
                [InlineKeyboardButton(text="BTC", url="https://t.me/xrocket?start=inv_QYFKjAKihGWpTW1")]
            ])
            await message.answer("🚀 <b>Оберіть спосіб оплати через xRocket:</b>", reply_markup=xrocket_keyboard)
        elif message.text:
            await message.answer(self.strings["/main"])
