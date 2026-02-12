
# meta pic: https://authorche.top/1/security.jpg
# scope: hikka_only
# scope: hikka_min 3.0.0

import logging
import time
from telethon.tl.functions.contacts import BlockRequest
from telethon.tl.functions.messages import DeleteHistoryRequest, ReportSpamRequest
from telethon.tl.types import Message, PeerUser, User
from telethon.utils import get_display_name

from .. import loader, utils

logger = logging.getLogger(__name__)

__version__ = (3, 2, 0)

@loader.tds
class AuthorSecurityMod(loader.Module):
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
            "▫️ <b>.allowpm</b> — Whitelist a user manually."
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
        self._ratelimit_timeout = 5 * 60  # 5 minutes
        self._ratelimit_threshold = 10
        
        if not self.get("ignore_hello", False):
            await self.inline.bot.send_photo(
                self._tg_id,
                photo=self.config["photo"],
                caption=self.strings("hello"),
                parse_mode="HTML",
            )
            self.set("ignore_hello", True)

    def _format_bool(self, state: bool) -> str:
        return "Enabled ✅" if state else "Disabled ❌"

    async def pmblcmd(self, message: Message):
        """Toggle the AuthorSecurity protection system."""
        current = self.get("state", False)
        new_state = not current
        self.set("state", new_state)
        
        await utils.answer(
            message,
            self.strings("state").format(
                "Active ✅" if new_state else "Inactive 💤",
                self._format_bool(self.config["report_spam"]),
                self._format_bool(self.config["delete_dialog"]),
            ),
        )

    async def testpmcmd(self, message: Message):
        """Send the current block message to this chat for testing."""
        caption = self.config["custom_message"] or self.strings("banned_msg")
        
        # We delete the command message to make it look clean
        await message.delete()
        
        # Sending via client (as User) to see exactly what others see
        await message.client.send_file(
            message.chat_id,
            file=self.config["photo"],
            caption=caption,
            parse_mode="HTML"
        )

    async def pmbanlastcmd(self, message: Message):
        """<count> - Mass ban and clear history for N recent PMs."""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit():
            await utils.answer(message, self.strings("args_pmban"))
            return

        n = int(args)
        await utils.answer(message, self.strings("removing").format(n))

        dialogs = []
        async for dialog in self._client.iter_dialogs(limit=n*2, ignore_pinned=True):
            if not isinstance(dialog.message.peer_id, PeerUser):
                continue
            if dialog.message.peer_id.user_id == self._tg_id:
                continue
            dialogs.append(dialog)

        to_ban = dialogs[:n]

        for d in to_ban:
            user_id = d.message.peer_id.user_id
            try:
                await self._client(BlockRequest(id=user_id))
                await self._client(DeleteHistoryRequest(peer=user_id, just_clear=True, max_id=0))
            except Exception as e:
                logger.error(f"Failed to ban {user_id}: {e}")

        await utils.answer(message, self.strings("removed").format(len(to_ban)))

    def _approve(self, user_id: int, reason: str = "unknown"):
        if user_id not in self._whitelist:
            self._whitelist.append(user_id)
            self.set("whitelist", self._whitelist)
            logger.debug(f"User {user_id} whitelisted. Reason: {reason}")

    async def allowpmcmd(self, message: Message):
        """<reply/user> - Whitelist a user, allowing them to PM you."""
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

        self._approve(user.id, "manual_command")
        await utils.answer(
            message, 
            self.strings("approved").format(user.id, get_display_name(user))
        )

    async def watcher(self, message: Message):
        """Monitors incoming messages."""
        if (
            not isinstance(message, Message)
            or getattr(message, "out", False)
            or not isinstance(message.peer_id, PeerUser)
            or not self.get("state", False)
        ):
            return

        if message.sender_id in {
            777000,  # Telegram
            1271266957,  # Replies
            self._tg_id
        }:
            return

        self._queue.append(message)

    @loader.loop(interval=0.05, autostart=True)
    async def ban_loop(self):
        """Processes the ban queue."""
        if not self._ban_queue:
            return

        message = self._ban_queue.pop(0)
        
        current_time = time.time()
        self._ratelimit = [t for t in self._ratelimit if t + self._ratelimit_timeout > current_time]

        sender_user = None
        try:
            sender_user = await self._client.get_entity(message.peer_id)
        except Exception:
            pass
            
        sender_name = get_display_name(sender_user) if sender_user else str(message.sender_id)

        # 1. Send Warning to User (if not silent and under rate limit)
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
                    # Fallback if image fails or privacy settings prevent it
                    try:
                        await self._client.send_message(
                            message.peer_id,
                            self.config["custom_message"] or self.strings("banned_msg"),
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass # Can't write to user, ignore
                        
                self._ratelimit.append(current_time)

        # 2. Log to Saved Messages (Bot)
        msg_content = "Media/Sticker"
        if message.raw_text:
            msg_content = message.raw_text[:300]

        await self.inline.bot.send_message(
            self._tg_id,
            self.strings("banned_log").format(
                message.sender_id,
                utils.escape_html(sender_name),
                self._format_bool(self.config["report_spam"]),
                self._format_bool(self.config["delete_dialog"]),
                utils.escape_html(msg_content),
            ),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

        # 3. Block and Cleanup
        try:
            await self._client(BlockRequest(id=message.sender_id))
            
            if self.config["report_spam"]:
                await self._client(ReportSpamRequest(peer=message.sender_id))
            
            if self.config["delete_dialog"]:
                await self._client(DeleteHistoryRequest(peer=message.sender_id, just_clear=True, max_id=0))
                
        except Exception as e:
            logger.error(f"Error acting on {message.sender_id}: {e}")

        self._approve(message.sender_id, "banned_auto")

    @loader.loop(interval=0.01, autostart=True)
    async def queue_processor(self):
        """Analyzes messages to decide if they should be banned."""
        if not self._queue:
            return

        message = self._queue.pop(0)
        sender_id = message.sender_id

        if sender_id in self._whitelist:
            return

        try:
            entity = await self._client.get_entity(sender_id)
            
            if getattr(entity, 'bot', False):
                self._approve(sender_id, "is_bot")
                return

            if self.config["ignore_contacts"] and getattr(entity, 'contact', False):
                self._approve(sender_id, "is_contact")
                return
        except Exception:
            pass

        try:
            history = await self._client.get_messages(sender_id, limit=200)
            
            # If the user has EVER replied to YOU, or you started it
            if history:
                if history[-1].sender_id == self._tg_id:
                    self._approve(sender_id, "initiated_by_owner")
                    return

            if self.config["ignore_active"]:
                my_msg_count = sum(1 for msg in history if msg.sender_id == self._tg_id)
                if my_msg_count >= self.config["active_threshold"]:
                    self._approve(sender_id, "active_conversation")
                    return
        except Exception:
            pass

        # If logic reaches here -> BAN
        self._ban_queue.append(message)
