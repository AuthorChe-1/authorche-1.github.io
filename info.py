# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# ©️ AuthorChe, 2025
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import git
import time
import psutil
import os
import glob
import requests
import re
import emoji
import datetime
import logging

from bs4 import BeautifulSoup
from typing import Optional
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from herokutl.tl.types import Message
from herokutl.utils import get_display_name
from .. import loader, utils, version
from ..inline.types import InlineQuery
import platform as lib_platform
import getpass

logger = logging.getLogger(__name__)

@loader.tds
class InfoMod(loader.Module):
    """Show userbot info with enhanced functionality"""

    strings = {
        "name": "Info",
        "owner": "Owner",
        "version": "Version",
        "build": "Build", 
        "branch": "Branch",
        "prefix": "Prefix",
        "uptime": "Uptime",
        "cpu_usage": "CPU Usage",
        "ram_usage": "RAM Usage",
        "send_info": "Send bot info",
        "description": "ℹ This will not compromise any sensitive info",
        "up-to-date": "😌 Up-to-date",
        "update_required": "😕 Update required </b><code>{prefix}update</code><b>",
        "non_detectable": "Non-detectable",
        "incorrect_format_font": "❌ Incorrect font format. Use .ttf or .otf",
        "no_font": "❌ No font provided",
        "font_installed": "✅ Font installed successfully",
        "incorrect_img_format": "❌ Incorrect image format",
        "setinfo_no_args": "❌ No arguments provided",
        "setinfo_success": "✅ Custom message set successfully",
        "desc": "Heroku userbot info module",
        "ping_emoji": "Ping emoji",
        "_cfg_cst_msg": "Custom message for info. May contain {me}, {version}, {build}, {prefix}, {platform}, {upd}, {uptime}, {cpu_usage}, {ram_usage}, {ping}, {time} keywords",
        "_cfg_banner": "Banner URL for info message",
        "_cfg_cst_btn": "Custom button. Leave empty to remove button",
        "_cfg_close": "Close button text",
        "_cfg_time": "Timezone offset (e.g., +3, -5)",
        "_cfg_cst_bnr": "Custom banner URL",
        "_cfg_cst_frmt": "Custom file format for banner",
        "_cfg_inline_banner": "Set True to disable inline media banner"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                "",
                doc=lambda: self.strings("_cfg_cst_msg"),
            ),
            loader.ConfigValue(
                "banner_url",
                "https://raw.githubusercontent.com/AuthorChe-1/authorche-1.github.io/refs/heads/main/start.jpg",
                lambda: self.strings("_cfg_banner"),
            ),
            loader.ConfigValue(
                "show_heroku",
                True,
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "ping_emoji",
                "✍️",
                lambda: self.strings["ping_emoji"],
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "switchInfo",
                False,
                "Switch info to mode photo",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "imgSettings",
                ["imgSettings", 30, '#000', '0|0', "mm", 0, '#000'],
                "Image settings\n1. Additional nickname\n2. Font size\n3. Font color in HEX format '#000'\n4. Text coordinates '100|100'\n5. Text anchor\n6. Stroke size\n7. Stroke color in HEX format '#000'",
                validator=loader.validators.Series(
                    fixed_len=7,
                ),
            ),
            loader.ConfigValue(
                "custom_format",
                "photo",
                lambda: self.strings("_cfg_cst_frmt"),
                validator=loader.validators.Choice(["photo", "video", "audio", "gif"]),
            ),
            loader.ConfigValue(
                "disable_banner",
                False,
                lambda: self.strings("_cfg_banner"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "disable_inline_banner",
                False,
                lambda: self.strings("_cfg_inline_banner"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "timezone",
                "+3",
                lambda: self.strings("_cfg_time"),
            ),
            loader.ConfigValue(
                "close_btn",
                "🔻Close",
                lambda: self.strings("_cfg_close"),
            ),
            loader.ConfigValue(
                "custom_button1",
                ["🌐WebSite", "https://authorche.top"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button2",
                ["📱Telegram", "https://t.me/wsinfo"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button3",
                ["❤️Donate", "https://t.me/acdonate_bot"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button4",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button5",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button6",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
        )

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me()

    def _get_os_name(self):
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME"):
                        return line.split("=")[1].strip().strip('"')
        except FileNotFoundError:
            return self.strings['non_detectable']
        
    def remove_emoji_and_html(self, text: str) -> str:
        reg = r'<[^<]+?>'
        text = f"{re.sub(reg, '', text)}"
        allchars = [str for str in text]
        emoji_list = [c for c in allchars if c in emoji.EMOJI_DATA]
        clean_text = ''.join([str for str in text if not any(i in str for i in emoji_list)])
        return clean_text
    
    def imgur(self, url: str) -> str:
        page = requests.get(url, stream=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
        soup = BeautifulSoup(page.text, 'html.parser')
        metatag = soup.find("meta", property="og:image")
        return metatag['content']

    def _render_info(self, start: float) -> str:
        try:
            repo = git.Repo(search_parent_directories=True)
            diff = repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            upd = (
                self.strings("update_required").format(prefix=self.get_prefix()) if diff else self.strings("up-to-date")
            )
        except Exception:
            upd = ""

        me = self.config['imgSettings'][0] if (self.config['imgSettings'][0] != "imgSettings") and self.config['switchInfo'] else '<b><a href="tg://user?id={}">{}</a></b>'.format(
            self._client.heroku_me.id,
            utils.escape_html(get_display_name(self._client.heroku_me)),
        ).replace('{', '').replace('}', '')
        
        build = utils.get_commit_url()
        _version = f'<i>{".".join(list(map(str, list(version.__version__))))}</i>'
        prefix = f"«<code>{utils.escape_html(self.get_prefix())}</code>»"
        platform = utils.get_named_platform()

        # Time calculation
        try:
            offset = datetime.timedelta(hours=int(self.config["timezone"]))
            tz = datetime.timezone(offset)
            time_now = datetime.datetime.now(tz)
            current_time = time_now.strftime("%H:%M:%S")
        except:
            current_time = "N/A"

        # Platform emoji replacements
        for emoji_char, icon in [
            ("🍊", "<emoji document_id=5449599833973203438>🧡</emoji>"),
            ("🍇", "<emoji document_id=5449468596952507859>💜</emoji>"),
            ("😶‍🌫️", "<emoji document_id=5370547013815376328>😶‍🌫️</emoji>"),
            ("❓", "<emoji document_id=5407025283456835913>📱</emoji>"),
            ("🍀", "<emoji document_id=5395325195542078574>🍀</emoji>"),
            ("🦾", "<emoji document_id=5386766919154016047>🦾</emoji>"),
            ("🚂", "<emoji document_id=5359595190807962128>🚂</emoji>"),
            ("🐳", "<emoji document_id=5431815452437257407>🐳</emoji>"),
            ("🕶", "<emoji document_id=5407025283456835913>📱</emoji>"),
            ("🐈‍⬛", "<emoji document_id=6334750507294262724>🐈‍⬛</emoji>"),
            ("✌️", "<emoji document_id=5469986291380657759>✌️</emoji>"),
            ("💎", "<emoji document_id=5471952986970267163>💎</emoji>"),
            ("🛡", "<emoji document_id=5282731554135615450>🌩</emoji>"),
            ("🌼", "<emoji document_id=5224219153077914783>❤️</emoji>"),
            ("🎡", "<emoji document_id=5226711870492126219>🎡</emoji>"),
            ("🐧", "<emoji document_id=5361541227604878624>🐧</emoji>"),
            ("🧃", "<emoji document_id=5422884965593397853>🧃</emoji>"),
            ("💻", "<emoji document_id=5469825590884310445>💻</emoji>"),
            ("🍏", "<emoji document_id=5372908412604525258>🍏</emoji>")
        ]:
            platform = platform.replace(emoji_char, icon)

        return (
            (
                "✍️ АвторБот\n"
                if self.config["show_heroku"]
                else ""
            )
            + self.config["custom_message"].format(
                me=me,
                version=_version,
                build=build,
                prefix=prefix,
                platform=platform,
                upd=upd,
                uptime=utils.formatted_uptime(),
                cpu_usage=utils.get_cpu_usage(),
                ram_usage=f"{utils.get_ram_usage()} MB",
                branch=version.branch,
                hostname=lib_platform.node(),
                user=getpass.getuser(),
                os=self._get_os_name() or self.strings('non_detectable'),
                kernel=lib_platform.release(),
                cpu=f"{psutil.cpu_count(logical=False)} ({psutil.cpu_count()}) core(-s); {psutil.cpu_percent()}% total",
                ping=round((time.perf_counter_ns() - start) / 10**6, 3),
                time=current_time
            )
            if self.config["custom_message"]
            else (
                f'<b>✍️ АвторБот</b>\n\n'
                f'<b><emoji document_id=5373141891321699086>😎</emoji> {self.strings("owner")}:</b> {me}\n\n'
                f'<b><emoji document_id=5469741319330996757>💫</emoji> {self.strings("version")}:</b> {_version} {build}\n'
                f'<b><emoji document_id=5449918202718985124>🌳</emoji> {self.strings("branch")}:</b> <code>{version.branch}</code>\n'
                f'{upd}\n\n'
                f'<b><emoji document_id=5472111548572900003>⌨️</emoji> {self.strings("prefix")}:</b> {prefix}\n'
                f'<b><emoji document_id=5451646226975955576>⌛️</emoji> {self.strings("uptime")}:</b> {utils.formatted_uptime()}\n'
                f'<b>⌚ Time:</b> {current_time}\n\n'
                f'<b><emoji document_id=5431449001532594346>⚡️</emoji> {self.strings("cpu_usage")}:</b> <i>~{utils.get_cpu_usage()} %</i>\n'
                f'<b><emoji document_id=5359785904535774578>💼</emoji> {self.strings("ram_usage")}:</b> <i>~{utils.get_ram_usage()} MB</i>\n'
                f'<b>{platform}</b>'
            )
        )
    
    def _get_info_photo(self, start: float) -> Optional[Path]:
        imgform = self.config['banner_url'].split('.')[-1]
        imgset = self.config['imgSettings']
        if imgform in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
            response = requests.get(self.config['banner_url'] if not self.config['banner_url'].startswith('https://imgur') else self.imgur(self.config['banner_url']), stream=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
            img = Image.open(BytesIO(response.content))
            font = ImageFont.truetype(
                glob.glob(f'{os.getcwd()}/assets/font.*')[0], 
                size=int(imgset[1]), 
                encoding='unic'
            )
            w, h = img.size
            draw = ImageDraw.Draw(img)
            draw.text(
                (int(w/2), int(h/2)) if imgset[3] == '0|0' else tuple([int(i) for i in imgset[3].split('|')]),
                f'{utils.remove_html(self._render_info(start))}', 
                anchor=imgset[4],
                font=font,
                fill=imgset[2] if imgset[2].startswith('#') else '#000',
                stroke_width=int(imgset[5]),
                stroke_fill=imgset[6] if imgset[6].startswith('#') else '#000',
                embedded_color=True
            )
            path = f'{os.getcwd()}/assets/imginfo.{imgform}'
            img.save(path)
            return Path(path).absolute()
        return None

    def _get_mark(self, btn_count):
        btn_count = str(btn_count)
        return (
            {
                "text": self.config[f"custom_button{btn_count}"][0],
                "url": self.config[f"custom_button{btn_count}"][1],
            }
            if self.config[f"custom_button{btn_count}"]
            else None
        )

    @loader.inline_everyone
    async def info_inline_handler(self, query: InlineQuery) -> dict:
        """Show userbot info inline"""
        start = time.perf_counter_ns()
        m = {x: self._get_mark(x) for x in range(1, 7)}
        btns = [
            [
                *([m[1]] if m[1] else []),
                *([m[2]] if m[2] else []),
                *([m[3]] if m[3] else []),
            ],
            [
                *([m[4]] if m[4] else []),
                *([m[5]] if m[5] else []),
                *([m[6]] if m[6] else []),
            ],
        ]
        msg_type = "message" if self.config["disable_inline_banner"] else "caption"
        return {
            "title": self.strings("send_info"),
            "description": self.strings("description"),
            msg_type: self._render_info(start),
            self.config["custom_format"]: self.config["banner_url"],
            "thumb": "https://raw.githubusercontent.com/AuthorChe-1/authorche-1.github.io/refs/heads/main/start.jpg",
            "reply_markup": btns,
        }
    
    @loader.command()
    async def insfont(self, message: Message):
        "<Url|Reply to font> - Install font"
        if message.is_reply:
            reply = await message.get_reply_message()
            fontform = reply.document.mime_type.split("/")[1]
            if not fontform in ['ttf', 'otf']:
                await utils.answer(
                    message,
                    self.strings["incorrect_format_font"]
                )
                return
            origpath = glob.glob(f'{os.getcwd()}/assets/font.*')[0]
            ptf = f'{os.getcwd()}/font.{fontform}'
            os.rename(origpath, ptf)
            photo = await reply.download_media(origpath)
            if photo is None:
                os.rename(ptf, origpath)
                await utils.answer(
                    message,
                    self.strings["no_font"]
                )
                return
            os.remove(ptf)
        elif utils.check_url(utils.get_args_raw(message)):
            fontform = utils.get_args_raw(message).split('.')[-1]
            if not fontform in ['ttf', 'otf']:
                await utils.answer(
                    message,
                    self.strings["incorrect_format_font"]
                )
                return
            response = requests.get(utils.get_args_raw(message), stream=True)
            os.remove(glob.glob(f'{os.getcwd()}/assets/font.*')[0])
            with open(f'{os.getcwd()}/assets/font.{fontform}', 'wb') as file:
                file.write(response.content)
        else:
            await utils.answer(
                message,
                self.strings["no_font"]
            )
            return
        await utils.answer(
            message,
            self.strings["font_installed"]
        )

    @loader.command()
    async def infocmd(self, message: Message):
        """Send bot info with inline buttons"""
        start = time.perf_counter_ns()
        
        if self.config['switchInfo']:
            if self._get_info_photo(start) is None:
                await utils.answer(
                    message, 
                    self.strings["incorrect_img_format"]
                )
                return
           
            await utils.answer_file(
                message,
                self._get_info_photo(start),
                reply_to=getattr(message, "reply_to_msg_id", None),
            )
        else:
            # Prepare inline buttons
            m = {x: self._get_mark(x) for x in range(1, 7)}
            btns = [
                [
                    *([m[1]] if m[1] else []),
                    *([m[2]] if m[2] else []),
                    *([m[3]] if m[3] else []),
                ],
                [
                    *([m[4]] if m[4] else []),
                    *([m[5]] if m[5] else []),
                    *([m[6]] if m[6] else []),
                ],
            ]
            
            if '{ping}' in self.config.get("custom_message", ""):
                message = await utils.answer(message, self.config["ping_emoji"])
            
            # Use inline form with buttons
            await self.inline.form(
                message=message,
                text=self._render_info(start),
                reply_markup=btns,
                **{}
                if self.config["disable_banner"]
                else {self.config["custom_format"]: self.config["banner_url"]}
            )

    @loader.command()
    async def hinfo(self, message: Message):
        """Show module description"""
        await utils.answer(message, self.strings("desc"))

    @loader.command()
    async def setinfo(self, message: Message):
        """Set custom info message"""
        if not (args := utils.get_args_html(message)):
            return await utils.answer(message, self.strings("setinfo_no_args"))

        self.config["custom_message"] = args
        await utils.answer(message, self.strings("setinfo_success"))