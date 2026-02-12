# meta developer: @author_che
# meta pic: https://authorche.top/1/security.jpg
# scope: hikka_only
# scope: hikka_min 3.0.0

import logging
import time
import contextlib
from typing import Optional

from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.messages import DeleteHistoryRequest, ReportSpamRequest
from telethon.tl.types import Message, PeerUser, User
from telethon.utils import get_display_name, get_peer_id

from .. import loader, utils

logger = logging.getLogger(__name__)

__version__ = (3, 4, 0)

def format_(state: Optional[bool]) -> str:
    if state is None:
        return "❔"
    return "Enabled ✅" if state else "Disabled ❌"

@loader.tds
class AuthorSecurity(loader.Module):
    """
    Enterprise-grade Private Message Protection System.
    Filters unauthorized contacts with a professional AI-assistant persona.
    """

    strings = {
        "name": "AuthorSecurity",
        
        # --- Internal System Status ---
        "state": (
            "<b>🛡 AuthorSecurity Status</b>\n"
            "➖➖➖➖➖➖➖➖➖➖➖\n"
            "<b>System Active:</b> {}\n"
            "<b>Auto-Report Spam:</b> {}\n"
            "<b>Auto-Delete History:</b> {}"
        ),
        
        # --- Log for Vadim (The Author) ---
        "banned_log": (
            "<b>🛡 Security Alert: Incoming Message</b>\n"
            "➖➖➖➖➖➖➖➖➖➖➖\n"
            "👤 <b>From:</b> <a href=\"tg://user?id={}\">{}</a>\n"
            "🚫 <b>Action:</b> Temporarily Blocked\n"
            "⚠️ <b>Spam Report:</b> {}\n"
            "🗑 <b>History Wiped:</b> {}\n\n"
            "📝 <b>Intercepted Content:</b>\n<code>{}</code>"
        ),
        
        "removing": "<b>🔄 System Processing...</b>\n<i>Analyzing and purging last {} unauthorized dialogs.</i>",
        "removed": "<b>✅ Maintenance Complete</b>\n<i>Successfully processed {} dialogs.</i>",
        "user_not_specified": "<b>⚠️ System Error:</b> Target user entity not specified.",
        "approved": "<b>✅ Access Granted</b>\nUser <a href=\"tg://user?id={}\">{}</a> has been whitelisted.",
        "args_pmban": "<b>⚠️ Syntax Error:</b> Usage: <code>.pmbanlast <count></code>",
        
        # --- Force BL / Test Strings ---
        "force_reset": (
            "<b>🔄 Security Reset</b>\n"
            "User <a href=\"tg://user?id={}\">{}</a> has been removed from whitelist and unblocked.\n"
            "<i>Next message from them will trigger the Security System.</i>"
        ),
        
        # --- The Message sent to the Stranger (Public Face) ---
        "banned_msg": (
            "<b>🛡 AuthorSecurity System | Automated Response</b>\n\n"
            "Greetings. This is an automated notification from the <b>AuthorSecurity</b> assistant.\n\n"
            "To maintain workflow efficiency and security, this account utilizes a strict filter for new connections. <b>Your direct access is currently restricted.</b>\n\n"
            "ℹ️ <b>Status: Pending Review</b>\n"
            "The Author (Vadim) has been notified of your message. He reviews the security log personally.\n"
            "• <b>If you are a human/contact:</b> He will whitelist you and reply shortly.\n"
            "• <b>Note:</b> Until manual approval is granted, further messages here will not be seen.\n\n"
            "<i>Thank you for your understanding and patience.</i>\n\n"
            "🔗 <a href='https://authorche.top'><b>Official Website</b></a>  |  ☕ <a href='https://authorche.top/sup'><b>Support Author</b></a>"
        ),
        
        "hello": (
            "<b>🛡 AuthorSecurity System initialized.</b>\n\n"
            "Enterprise-level protection for your private messages.\n\n"
            "▫️ <b>.pmbl</b> — Toggle protection state.\n"
            "▫️ <b>.pmblsett</b> — Configure security parameters.\n"
            "▫️ <b>.testpm</b> — Preview the blockade message.\n"
            "▫️ <b>.forcebl</b> — Reset user status (simulate new user)."
        ),
    }

    def __init__(self):
        self._queue = []
        self._ban_queue = []
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "ignore_contacts",
                True,
                lambda: "Automatically whitelist saved contacts?",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "ignore_active",
                True,
                lambda: "Ignore users you have previously chatted with?",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "active_threshold",
                5,
                lambda: "Minimum outgoing messages to consider a user 'trusted'",
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "custom_message",
                doc=lambda: "Override the default blocking message (Leave empty for default)",
            ),
            loader.ConfigValue(
                "photo",
                "https://authorche.top/1/security.jpg",
                lambda: "URL for the security banner image",
                validator=loader.validators.Link(),
            ),
            loader.ConfigValue(
                "report_spam",
                False,
                lambda: "Automatically report blocked users as spam?",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "delete_dialog",
                False,
                lambda: "Automatically delete the chat history after blocking?",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "silent",
                False,
                lambda: "Silent Mode: Block without sending any notification message",
                validator=loader.validators.Boolean(),
            ),
        )

    async def client_ready(self):
        self._whitelist = self.get("whitelist", [])
        self._ratelimit = []
        self._ratelimit_timeout = 5 * 60
        self._ratelimit_threshold = 10
        
        if not self.get("ignore_hello", False):
            await self.inline.bot.send_photo(
                self._tg_id,
                photo=self.config["photo"],
                caption=self.strings("hello"),
                parse_mode="HTML",
            )
            self.set("ignore_hello", True)

    async def pmblcmd(self, message: Message):
        """Toggle PMBL"""
        current = self.get("state", False)
        new = not current
        self.set("state", new)
        await utils.answer(
            message,
            self.strings("state").format(
                "Active ✅" if new else "Inactive 💤",
                format_(self.config["report_spam"]),
                format_(self.config["delete_dialog"]),
            ),
        )

    async def testpmcmd(self, message: Message):
        """Send the current block message to this chat for testing."""
        caption = self.config["custom_message"] or self.strings("banned_msg")
        await message.delete()
        await message.client.send_file(
            message.chat_id,
            file=self.config["photo"],
            caption=caption,
            parse_mode="HTML"
        )

    async def forceblcmd(self, message: Message):
        """<reply/user> - Unblock and remove from whitelist (Simulate new user)."""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        user = None

        try:
            if reply:
                user = await self._client.get_entity(reply.sender_id)
            elif args:
                user = await self._client.get_entity(args)
        except Exception:
            pass

        if not user or not isinstance(user, User):
            await utils.answer(message, self.strings("user_not_specified"))
            return

        # 1. Remove from whitelist
        if user.id in self._whitelist:
            self._whitelist.remove(user.id)
            self.set("whitelist", self._whitelist)
        
        # 2. Unblock
        try:
            await self._client(UnblockRequest(id=user.id))
        except Exception:
            pass

        await utils.answer(
            message, 
            self.strings("force_reset").format(user.id, get_display_name(user))
        )

    async def pmbanlastcmd(self, message: Message):
        """<number> - Ban and delete dialogs with n most new users"""
        n = utils.get_args_raw(message)
        if not n or not n.isdigit():
            await utils.answer(message, self.strings("args_pmban"))
            return

        n = int(n)
        await utils.answer(message, self.strings("removing").format(n))

        dialogs = []
        async for dialog in self._client.iter_dialogs(ignore_pinned=True):
            try:
                if not isinstance(dialog.message.peer_id, PeerUser):
                    continue
            except AttributeError:
                continue

            # Original logic for reliable sorting
            m = (
                await self._client.get_messages(
                    dialog.message.peer_id,
                    limit=1,
                    reverse=True,
                )
            )[0]

            dialogs += [
                (
                    get_peer_id(dialog.message.peer_id),
                    int(time.mktime(m.date.timetuple())),
                )
            ]

        dialogs.sort(key=lambda x: x[1])
        to_ban = [d for d, _ in dialogs[::-1][:n]]

        for d in to_ban:
            try:
                await self._client(BlockRequest(id=d))
                await self._client(DeleteHistoryRequest(peer=d, just_clear=True, max_id=0))
            except Exception as e:
                logger.error(f"Error acting on {d}: {e}")

        await utils.answer(message, self.strings("removed").format(n))

    def _approve(self, user: int, reason: str = "unknown"):
        self._whitelist += [user]
        self._whitelist = list(set(self._whitelist))
        self.set("whitelist", self._whitelist)
        logger.debug(f"User approved in pm {user}, filter: {reason}")
        return

    async def allowpmcmd(self, message: Message):
        """<reply or user> - Allow user to pm you"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        user = None

        try:
            user = await self._client.get_entity(args)
        except Exception:
            with contextlib.suppress(Exception):
                user = await self._client.get_entity(reply.sender_id) if reply else None

        if not user:
            chat = await message.get_chat()
            if not isinstance(chat, User):
                await utils.answer(message, self.strings("user_not_specified"))
                return
            user = chat

        self._approve(user.id, "manual_approve")
        try:
            await self._client(UnblockRequest(id=user.id))
        except:
            pass

        await utils.answer(
            message, self.strings("approved").format(user.id, get_display_name(user))
        )

    async def watcher(self, message: Message):
        # ORIGINAL WATCHER LOGIC (Proven to work)
        if (
            getattr(message, "out", False)
            or not isinstance(message, Message)
            or not isinstance(message.peer_id, PeerUser)
            or not self.get("state", False)
            or utils.get_chat_id(message)
            in {
                1271266957,  # @replies
                777000,  # Telegram Notifications
                self._tg_id,  # Self
            }
        ):
            return

        self._queue += [message]

    @loader.loop(interval=0.05, autostart=True)
    async def ban_loop(self):
        if not self._ban_queue:
            return

        message = self._ban_queue.pop(0)
        self._ratelimit = list(
            filter(
                lambda x: x + self._ratelimit_timeout < time.time(),
                self._ratelimit,
            )
        )

        dialog = None

        # 1. Send Warning (using new strings)
        if len(self._ratelimit) < self._ratelimit_threshold:
            if not self.config["silent"]:
                try:
                    await self._client.send_file(
                        message.peer_id,
                        self.config["photo"],
                        caption=self.config["custom_message"] or self.strings("banned_msg"),
                        parse_mode="HTML"
                    )
                except Exception:
                    await utils.answer(
                        message,
                        self.config["custom_message"] or self.strings("banned_msg"),
                    )

                self._ratelimit += [round(time.time())]

            try:
                dialog = await self._client.get_entity(message.peer_id)
            except ValueError:
                pass

        # 2. Log to Saved Messages
        msg_content = "Media/Sticker"
        if message.raw_text:
            msg_content = message.raw_text[:300]
        elif message.sticker:
            msg_content = "<sticker>"
        elif message.photo:
            msg_content = "<photo>"

        sender_name = get_display_name(dialog) if dialog else str(message.sender_id)

        await self.inline.bot.send_message(
            self._client.tg_id,
            self.strings("banned_log").format(
                dialog.id if dialog is not None else message.sender_id,
                utils.escape_html(sender_name),
                format_(self.config["report_spam"]),
                format_(self.config["delete_dialog"]),
                utils.escape_html(msg_content),
            ),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

        # 3. Block and Cleanup
        try:
            await self._client(BlockRequest(id=message.sender_id))
        except Exception as e:
            logger.error(f"Failed to block {message.sender_id}: {e}")

        if self.config["report_spam"]:
            try:
                await self._client(ReportSpamRequest(peer=message.sender_id))
            except: pass

        if self.config["delete_dialog"]:
            try:
                await self._client(
                    DeleteHistoryRequest(peer=message.sender_id, just_clear=True, max_id=0)
                )
            except: pass

        self._approve(message.sender_id, "banned")

    @loader.loop(interval=0.01, autostart=True)
    async def queue_processor(self):
        # ORIGINAL PROCESSOR LOGIC (Proven to work)
        if not self._queue:
            return

        message = self._queue.pop(0)

        cid = utils.get_chat_id(message)
        if cid in self._whitelist:
            return

        peer = (
            getattr(getattr(message, "sender", None), "username", None)
            or message.peer_id
        )

        with contextlib.suppress(ValueError):
            entity = await self._client.get_entity(peer)

            if entity.bot:
                return self._approve(cid, "bot")

            if self.config["ignore_contacts"]:
                if entity.contact:
                    return self._approve(cid, "ignore_contacts")

        # Original history check logic (reliable)
        try:
            first_message = (
                await self._client.get_messages(
                    peer,
                    limit=1,
                    reverse=True,
                )
            )[0]

            if (
                getattr(message, "raw_text", False)
                and first_message.sender_id == self._tg_id
            ):
                return self._approve(cid, "started_by_you")
        except Exception:
            pass

        if self.config["ignore_active"]:
            q = 0
            async for msg in self._client.iter_messages(peer, limit=200):
                if msg.sender_id == self._tg_id:
                    q += 1

                if q >= self.config["active_threshold"]:
                    return self._approve(cid, "active_threshold")

        self._ban_queue += [message]

    @loader.debug_method(name="unwhitelist")
    async def denypm(self, message: Message):
        user = (await message.get_reply_message()).sender_id
        self.set("whitelist", list(set(self.get("whitelist", [])) - {user}))
        return f"User unwhitelisted: {user}"
