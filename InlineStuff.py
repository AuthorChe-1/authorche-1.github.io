# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# ©️ Codrago, 2024-2025
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html
# Updated by AuthorChe for AuthorBot
import re
import string

from herokutl.errors.rpcerrorlist import YouBlockedUserError
from herokutl.tl.functions.contacts import UnblockRequest
from herokutl.tl.types import Message

from .. import loader, utils
from ..inline.types import BotInlineMessage, InlineCall

@loader.tds
class InlineStuff(loader.Module):
    """Provides support for inline stuff"""

    strings = {"name": "InlineStuff",
               "start_text": "🪐 <b>Привіт! Це персональний, потужний модульний бот Автора. Вам, нажаль(чи на щастя) не доступний повноцінно, лиш деякі інлайн-команди і команди з /menu!</b>\nПроєкти й боти, які доступні вам: @wsinfo\n\n<b>🌍 <a href=\"https://authorche.top\">Сайт Автора</a></b>\n<b>👥 <a href=\"https://t.me/wsinfo\">Телеграм-канал</a></b>",
               "setting_start": "ℹ️ Основна інформація про АвторБота\n\n<blockquote>• Префікс: {prefix}\n• Використання RAM: {ram_usage} МБ\n• Використання CPU: {cpu_usage}%\n• Хостинг: {host}</blockquote>"
    }

    @loader.watcher(
        "out",
        "only_inline",
        contains="This message will be deleted automatically",
    )
    async def watcher(self, message: Message):
        if message.via_bot_id == self.inline.bot_id:
            await message.delete()

    @loader.watcher("out", "only_inline", contains="Opening gallery...")
    async def gallery_watcher(self, message: Message):
        if message.via_bot_id != self.inline.bot_id:
            return

        id_ = re.search(r"#id: ([a-zA-Z0-9]+)", message.raw_text)[1]

        await message.delete()

        m = await message.respond("✍️", reply_to=utils.get_topic(message))

        await self.inline.gallery(
            message=m,
            next_handler=self.inline._custom_map[id_]["handler"],
            caption=self.inline._custom_map[id_].get("caption", ""),
            force_me=self.inline._custom_map[id_].get("force_me", False),
            disable_security=self.inline._custom_map[id_].get(
                "disable_security", False
            ),
            silent=True,
        )

    async def _check_bot(self, username: str) -> bool:
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                await self._client(UnblockRequest(id="@BotFather"))
                m = await conv.send_message("/token")

            r = await conv.get_response()

            await m.delete()
            await r.delete()

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                return False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if username != button.text.strip("@"):
                        continue

                    m = await conv.send_message("/cancel")
                    r = await conv.get_response()

                    await m.delete()
                    await r.delete()

                    return True

    @loader.command()
    async def ch_heroku_bot(self, message: Message):
        args = utils.get_args_raw(message).strip("@")
        if (
            not args
            or not args.lower().endswith("bot")
            or len(args) <= 4
            or any(
                litera not in (string.ascii_letters + string.digits + "_")
                for litera in args
            )
        ):
            await utils.answer(message, self.strings("bot_username_invalid"))
            return

        try:
            await self._client.get_entity(f"@{args}")
        except ValueError:
            pass
        else:
            if not await self._check_bot(args):
                await utils.answer(message, self.strings("bot_username_occupied"))
                return

        self._db.set("heroku.inline", "custom_bot", args)
        self._db.set("heroku.inline", "bot_token", None)
        await utils.answer(message, self.strings("bot_updated"))

    @loader.command()
    async def ch_bot_token(self, message: Message):
        args = utils.get_args_raw(message)
        if not args or not re.match(r'[0-9]{8,10}:[a-zA-Z0-9_-]{34,36}', args):
            await utils.answer(message, self.strings('token_invalid'))
            return
        self._db.set("heroku.inline", "bot_token", args)
        await utils.answer(message, self.strings("bot_updated"))

    async def aiogram_watcher(self, message: BotInlineMessage):
        if message.text != "/start" and message.text != "/profile":
            return

        if message.text == "/start":
            await message.answer_photo(
                "https://raw.githubusercontent.com/AuthorChe-1/authorche-1.github.io/refs/heads/main/start.jpg",
                caption=self.strings("start_text"),
            )

        if message.text == "/profile":
            
            if message.from_user.id != self.client.tg_id:
                await message.answer("❌ You are not allowed to use this")
            else:
                await message.answer_photo(
                    "https://raw.githubusercontent.com/AuthorChe-1/authorche-1.github.io/refs/heads/main/start.jpg",
                    caption = self.strings["profile_cmd"].format(prefix=self.get_prefix(),ram_usage=utils.get_ram_usage(),cpu_usage=utils.get_cpu_usage(),host=utils.get_named_platform()), 
                    reply_markup = self.inline.generate_markup(
                        markup_obj=[
                            [
                                {
                                    "text": "🚀 Restart", 
                                    "callback": self.restart, 
                                    "args": (message,)
                                }
                            ],
                            [
                                {
                                    "text": "⚠️ Reset prefix", 
                                    "callback": self.reset_prefix,
                                    "args": (message,)
                                }
                            ]
                        ]
                    )
                )

    async def restart(self, call: InlineCall, message):
        await call.edit(self.strings["restart"])
        await self.invoke("restart", "-f", message=message, peer=self.inline.bot.id)

    async def reset_prefix(self, call: InlineCall, message):
        await message.answer(self.strings["prefix_reset"])
        self.db.set("heroku.main", "command_prefix", ".")
