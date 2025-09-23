# scope: hikka_only
# scope: hikka_min 1.2.10

import asyncio
import logging
import os
import shutil
import signal
import sys
import tempfile
from collections import deque
from pathlib import Path
from telethon.errors.rpcerrorlist import MessageNotModifiedError
from telethon.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class BotHostMod(loader.Module):
    """Хостинг для Python ботів з керуванням через інлайн-кнопки."""

    strings = {
        "name": "BotHost",
        "bot_added": "✅ <b>Бота <code>{}</code> успішно додано та запущено.</b>",
        "bot_updated": "✅ <b>Бота <code>{}</code> успішно оновлено та перезапущено.</b>",
        "bot_add_error": "🚫 <b>Файл має бути .py або .zip.</b>",
        "reply_to_file": "✍️ <b>Відповідайте на файл з кодом бота (.py або .zip).</b>",
        "zip_missing_main_file": "🚫 <b>У ZIP-архіві відсутній головний файл <code>{}.py</code>.</b>",
        "no_py_files_in_zip": "🚫 <b>У ZIP-архіві не знайдено жодного .py файлу.</b>",
        "select_main_file": "🐍 <b>Оберіть головний файл для запуску бота <code>{}</code>:</b>",
        "select_new_main_file": "🐍 <b>Оберіть новий головний файл для бота <code>{}</code>:</b>\n<i>(👈 - поточний)</i>",
        "main_file_changed": "✅ <b>Файл запуску для <code>{}</code> змінено на <code>{}</code>.</b>",
        "restarting_with_new_file": "🔄 <b>Перезапускаю бота з новим файлом...</b>",
        "managing_bots": "⚙️ <b>Керування ботами:</b>",
        "no_bots": "🤷‍♂️ <b>Немає доданих ботів.</b>",
        "confirm_delete": "🗑 <b>Ви впевнені, що хочете видалити бота <code>{}</code>? Ця дія незворотна.</b>",
        "bot_deleted": "✅ <b>Бота <code>{}</code> видалено.</b>",
        "archiving": "📥 <b>Архівую...</b>",
        "bot_exported": "✅ <b>Бота вивантажено!</b>",
        "bot_stopped": "🔴 <b>Бота зупинено.</b>",
        "bot_started": "🟢 <b>Бота запущено.</b>",
        "bot_locked": "🔒 <b>Бота заблоковано від видалення.</b>",
        "bot_unlocked": "🔓 <b>Бота розблоковано.</b>",
        "bot_is_locked_del": "🔒 <b>Бот заблокований і не може бути видалений!</b>",
        "export_prompt": "📤 <b>Куди надіслати архів бота <code>{}</code>?</b>",
        "running": "🟢", "stopped": "🔴", "locked_icon": "🔒", "terminal_icon": "👨‍💻",
        "btn_turn_off": "🔴 Вимкнути", "btn_turn_on": "🟢 Увімкнути",
        "btn_delete": "🗑 Видалити", "btn_export": "📤 Вивантажити",
        "btn_lock": "🔒 Заблокувати", "btn_unlock": "🔓 Розблокувати",
        "btn_terminal": "👨‍💻 Термінал", "btn_logs": "📜 Логи",
        "btn_change_main_file": "🐍 Змінити файл запуску",
        "btn_back": "◀️ Назад", "btn_confirm_del": "🗑 Так, видалити",
        "btn_cancel_del": "◀️ Ні, назад", "btn_export_here": "📤 Сюди",
        "btn_export_saved": "❤️ В обране",
        "btn_autorestart_on": "🔄 Автоперезапуск (Увімк.)",
        "btn_autorestart_off": "🔄 Автоперезапуск (Вимк.)",
        "autorestart_on": "✅ <b>Автоперезапуск для <code>{}</code> увімкнено.</b>",
        "autorestart_off": "🔴 <b>Автоперезапуск для <code>{}</code> вимкнено.</b>",
        "no_bot_for_log": "🚫 <b>Бота <code>{}</code> не знайдено.</b>",
        "no_logs": "✍️ <b>Логи для бота <code>{}</code> порожні.</b>",
        "bot_logs_header": "📜 <b>Останні 100 рядків логу для</b> <code>{}</code>:",
        "installing_deps": "📦 <b>Встановлюю залежності:</b> {}",
        "deps_installed": "✅ <b>Залежності успішно встановлено!</b>",
        "deps_install_error": "🚫 <b>Помилка встановлення залежностей:</b>{}",
        "update_no_bot": "🚫 <b>Бота з іменем <code>{}</code> не знайдено.</b>",
        "update_args": "✍️ <b>Вкажіть ім'я бота для оновлення.</b>",
        "rename_success": "✅ <b>Бота <code>{}</code> успішно перейменовано на <code>{}</code>.</b>",
        "rename_exists": "🚫 <b>Бот з іменем <code>{}</code> вже існує.</b>",
        "rename_args": "✍️ <b>Вкажіть старе та нове ім'я бота.</b>\nПриклад: <code>.renamebot стара_назва нова_назва</code>",
        "rename_no_bot": "🚫 <b>Бота з іменем <code>{}</code> не знайдено.</b>",
        "term_args": "✍️ <b>Вкажіть ім'я бота для терміналу.</b>",
        "term_not_running": "🚫 <b>Бот <code>{}</code> не запущений. Запустіть його, щоб відкрити термінал.</b>",
        "term_already_exists": "ℹ️ <b>Термінал для бота <code>{}</code> вже відкрито в цьому чаті.</b>",
        "term_started": "👨‍💻 <b>Термінал для <code>{}</code> запущено.</b>\nВідповідайте на це повідомлення для надсилання команд.",
        "term_stopped": "✅ <b>Термінал для <code>{}</code> закрито.</b>",
        "term_logs_header": "📜 <b>Вивід</b>",
        "term_not_found": "🚫 <b>Термінал для <code>{}</code> не знайдено в цьому чаті.</b>",
    }
    
    def __init__(self):
        self.BOTS_DIR = Path("hosted_bots")
        self.bot_tasks = {}
        self.bot_processes = {}
        self.terminal_sessions = {}

    async def on_dlmod(self):
        self.BOTS_DIR.mkdir(exist_ok=True)
        self.db.set("BotHost", "running_bots", {})
        self.db.set("BotHost", "metadata", {})

    async def on_unload(self):
        logger.info("BotHostMod unloading. Stopping all components...")
        for sessions in self.terminal_sessions.values():
            for session in sessions.values():
                session["task"].cancel()
        for task in self.bot_tasks.values():
            task.cancel()
        for bot_name in self.db.get("BotHost", "running_bots", {}).copy():
            await self._stop_bot(bot_name, cancel_task=False)
        logger.info("All hosted bots stopped.")

    async def client_ready(self, client, db):
        self.db, self.client = db, client
        self.BOTS_DIR.mkdir(exist_ok=True)
        for key in ["running_bots", "locked_bots", "metadata"]:
            if self.db.get("BotHost", key) is None:
                self.db.set("BotHost", key, {} if key != "locked_bots" else [])
        await self._restart_bots_on_startup()
    
    async def _monitor_bot(self, bot_name: str, process: asyncio.subprocess.Process):
        bot_logs = deque(self.db.get("BotHost", f"logs_{bot_name}", []), maxlen=100)

        async def read_stream(stream, stream_name):
            while True:
                line = await stream.readline()
                if not line: break
                decoded_line = line.decode('utf-8', errors='ignore').strip()
                logger.info(f"[BotHost][{bot_name}] {stream_name}: {decoded_line}")
                bot_logs.append(decoded_line)
                self.db.set("BotHost", f"logs_{bot_name}", list(bot_logs))
                for sessions in self.terminal_sessions.values():
                    for session in sessions.values():
                        if session["bot_name"] == bot_name:
                            await session["queue"].put(decoded_line)
        
        stdout_task = asyncio.create_task(read_stream(process.stdout, "stdout"))
        stderr_task = asyncio.create_task(read_stream(process.stderr, "stderr"))
        
        await process.wait()
        stdout_task.cancel(); stderr_task.cancel()
        
        logger.warning(f"Bot '{bot_name}' (PID: {process.pid}) has terminated with code {process.returncode}.")
        running_bots = self.db.get("BotHost", "running_bots", {})
        if running_bots.get(bot_name, {}).get("pid") == process.pid:
            del running_bots[bot_name]
            self.db.set("BotHost", "running_bots", running_bots)
        
        self.bot_tasks.pop(bot_name, None)
        self.bot_processes.pop(bot_name, None)
        await self._close_bot_terminals(bot_name, f"🔴 <b>Процес бота <code>{bot_name}</code> завершився. Термінал закрито.</b>")
        
        metadata = self.db.get("BotHost", "metadata", {})
        if metadata.get(bot_name, {}).get("autorestart", False):
            logger.warning(f"Auto-restarting bot '{bot_name}'...")
            await asyncio.sleep(5) 
            await self._start_bot(bot_name)

    async def _restart_bots_on_startup(self):
        logger.info("Checking for bots to restart on startup...")
        if not self.BOTS_DIR.is_dir(): return
        for bot_dir in self.BOTS_DIR.iterdir():
            if not bot_dir.is_dir(): continue
            bot_path_py = self.BOTS_DIR / bot_dir.name / f"{bot_dir.name}.py"
            if bot_path_py.exists():
                logger.info(f"Restarting bot on startup: {bot_dir.name}")
                await self._start_bot(bot_dir.name)

    def _get_bots_status(self) -> dict:
        bots, running_bots = {}, self.db.get("BotHost", "running_bots", {})
        if not self.BOTS_DIR.is_dir(): return {}
        for bot_dir in self.BOTS_DIR.iterdir():
            if not bot_dir.is_dir(): continue
            bot_name = bot_dir.name
            metadata = self.db.get("BotHost", "metadata", {})
            main_file_name = metadata.get(bot_name, {}).get("main_file")
            path = bot_dir / main_file_name if main_file_name else next(bot_dir.glob("*.py"), None)
            if not path: continue
            
            is_running = False
            if pid := running_bots.get(bot_name, {}).get("pid"):
                try: os.kill(pid, 0); is_running = True
                except OSError:
                    del running_bots[bot_name]
                    self.db.set("BotHost", "running_bots", running_bots)
            bots[bot_name] = {"status": is_running, "path": path}
        return bots

    async def _start_bot(self, bot_name: str) -> bool:
        metadata = self.db.get("BotHost", "metadata", {})
        main_file = metadata.get(bot_name, {}).get("main_file", f"{bot_name}.py")
        bot_path = self.BOTS_DIR / bot_name / main_file
        if not bot_path.exists() or not bot_path.name.endswith(".py"): return False
        
        process = await asyncio.create_subprocess_exec(sys.executable, "-u", str(bot_path), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        self.bot_processes[bot_name] = process
        running_bots = self.db.get("BotHost", "running_bots", {})
        running_bots[bot_name] = {"pid": process.pid}
        self.db.set("BotHost", "running_bots", running_bots)
        self.bot_tasks[bot_name] = asyncio.create_task(self._monitor_bot(bot_name, process))
        logger.info(f"Started bot '{bot_name}' with PID {process.pid}")
        return True

    async def _stop_bot(self, bot_name: str, cancel_task: bool = True) -> bool:
        await self._close_bot_terminals(bot_name, f"🔴 <b>Бота <code>{bot_name}</code> було зупинено. Термінал закрито.</b>")
        if cancel_task and (task := self.bot_tasks.pop(bot_name, None)): task.cancel()
        running_bots = self.db.get("BotHost", "running_bots", {})
        if not (bot_info := running_bots.get(bot_name)): return False
        try: os.kill(bot_info["pid"], signal.SIGTERM)
        except Exception as e: logger.error(f"Failed to stop bot '{bot_name}': {e}")
        del running_bots[bot_name]
        self.db.set("BotHost", "running_bots", running_bots)
        self.bot_processes.pop(bot_name, None)
        return True

    async def _handle_bot_upload(self, message: Message, bot_name: str, is_update: bool):
        reply, bot_dir = await message.get_reply_message(), self.BOTS_DIR / bot_name
        bot_dir.mkdir(exist_ok=True)
        if reply.file.name.endswith(".zip"):
            with tempfile.NamedTemporaryFile(suffix=".zip") as temp_zip:
                await reply.download_media(file=temp_zip.name)
                try: await utils.run_sync(shutil.unpack_archive, temp_zip.name, bot_dir)
                except Exception as e: return await utils.answer(message, f"🚫 <b>Помилка:</b> <code>{e}</code>")
            
            py_files = [str(p.relative_to(bot_dir)) for p in bot_dir.glob("**/*.py")]
            if not py_files:
                shutil.rmtree(bot_dir)
                return await utils.answer(message, self.strings("no_py_files_in_zip"))
            
            if len(py_files) == 1: await self._complete_setup(message, bot_name, py_files[0], is_update)
            else:
                buttons = [[{"text": f"🐍 {file}", "callback": self._main_file_selected, "args": (bot_name, file, is_update)}] for file in py_files]
                await self.inline.form(message=message, text=self.strings("select_main_file").format(bot_name), reply_markup=buttons)
        else:
            main_py_file = bot_dir / f"{bot_name}.py"
            await reply.download_media(file=main_py_file)
            await self._complete_setup(message, bot_name, main_py_file.name, is_update)

    async def _main_file_selected(self, call, bot_name: str, selected_file: str, is_update: bool):
        await call.edit(f"Обрано файл <code>{selected_file}</code>. Завершую налаштування...")
        await self._complete_setup(call, bot_name, selected_file, is_update)

    async def _complete_setup(self, context, bot_name: str, main_file: str, is_update: bool):
        metadata = self.db.get("BotHost", "metadata", {}); metadata.setdefault(bot_name, {})["main_file"] = main_file
        self.db.set("BotHost", "metadata", metadata)

        bot_dir, all_requirements = self.BOTS_DIR / bot_name, set()
        if (req_file := bot_dir / "requirements.txt").exists():
            all_requirements.update(line.strip() for line in req_file.read_text().splitlines() if line.strip() and not line.strip().startswith("#"))

        for py_file in bot_dir.glob("**/*.py"):
            try:
                content = py_file.read_text("utf-8")
                if req_line := next((line for line in content.splitlines() if line.strip().lower().startswith("# requires:")), None):
                    all_requirements.update(req_line.split(":", 1)[1].strip().split())
            except Exception as e: logger.warning(f"Could not read/parse {py_file} for requirements: {e}")

        if requirements := list(all_requirements):
            status_msg = await utils.answer(context, self.strings("installing_deps").format(", ".join(f"<code>{r}</code>" for r in requirements)))
            pip = await asyncio.create_subprocess_exec(sys.executable, "-m", "pip", "install", *requirements, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            _, stderr = await pip.communicate()
            if pip.returncode != 0: return await utils.answer(status_msg, self.strings("deps_install_error").format(f"\n<code>{utils.escape_html(stderr.decode(errors='ignore'))}</code>"))
            await utils.answer(status_msg, self.strings("deps_installed"))
        
        if await self._start_bot(bot_name):
            await utils.answer(context, self.strings("bot_updated" if is_update else "bot_added").format(bot_name))
        else:
            await utils.answer(context, f"🚫 <b>Не вдалося запустити бота {bot_name}.</b>")

    @loader.command(ru_doc="<відп. на .py/.zip> [назва] - Додати бота")
    async def addbot(self, message: Message):
        """<відп. на .py/.zip> [назва] - Додати нового бота"""
        args, reply = utils.get_args_raw(message), await message.get_reply_message()
        if not reply or not reply.file or not (reply.file.name.endswith((".py", ".zip"))):
            return await utils.answer(message, self.strings("reply_to_file" if not (reply and reply.file) else "bot_add_error"))
        await self._handle_bot_upload(message, args or Path(reply.file.name).stem, is_update=False)

    @loader.command(ru_doc="<відп. на .py/.zip> <назва> - Оновити бота")
    async def updatebot(self, message: Message):
        """<відп. на .py/.zip> <назва> - Оновити існуючого бота"""
        args, reply = utils.get_args_raw(message), await message.get_reply_message()
        if not args: return await utils.answer(message, self.strings("update_args"))
        if not reply or not reply.file or not (reply.file.name.endswith((".py", ".zip"))):
            return await utils.answer(message, self.strings("reply_to_file" if not (reply and reply.file) else "bot_add_error"))
        if not (self.BOTS_DIR / args).is_dir(): return await utils.answer(message, self.strings("update_no_bot").format(args))
        await self._stop_bot(args); shutil.rmtree(self.BOTS_DIR / args)
        await self._handle_bot_upload(message, args, is_update=True)

    @loader.command(ru_doc="<стара_назва> <нова_назва> - Перейменувати бота")
    async def renamebot(self, message: Message):
        """<стара_назва> <нова_назва> - Перейменувати бота"""
        args = utils.get_args(message)
        if len(args) != 2: return await utils.answer(message, self.strings("rename_args"))
        old, new = args
        if not (self.BOTS_DIR / old).is_dir(): return await utils.answer(message, self.strings("rename_no_bot").format(old))
        if (self.BOTS_DIR / new).exists(): return await utils.answer(message, self.strings("rename_exists").format(new))
        await self._perform_rename(old, new)
        await utils.answer(message, self.strings("rename_success").format(old, new))

    @loader.command(ru_doc="- Меню керування ботами")
    async def bots(self, message: Message):
        """- Відкрити меню керування ботами"""
        await self.inline.form(message=message, text=self.strings("managing_bots"), reply_markup=await self._get_main_menu_buttons(message.chat_id), silent=True)

    @loader.command(ru_doc="<назва> - Логи бота")
    async def botlog(self, message: Message):
        """<назва> - Переглянути збережені логи бота"""
        bot_name = utils.get_args_raw(message)
        if not bot_name: return await utils.answer(message, "<b>Вкажіть ім'я бота.</b>")
        if not (self.BOTS_DIR / bot_name).is_dir(): return await utils.answer(message, self.strings("no_bot_for_log").format(bot_name))
        logs = self.db.get("BotHost", f"logs_{bot_name}")
        if not logs: return await utils.answer(message, self.strings("no_logs").format(bot_name))
        log_text = "\n".join(f"<code>{utils.escape_html(line)}</code>" for line in logs)
        await utils.answer(message, f"{self.strings('bot_logs_header').format(bot_name)}\n{log_text}")

    async def _get_main_menu_buttons(self, chat_id: int) -> list:
        bots, locked_bots = self._get_bots_status(), self.db.get("BotHost", "locked_bots", [])
        if not bots: return [[{"text": self.strings("no_bots"), "data": "none"}]]
        return [[{"text": f"{'🟢' if info['status'] else '🔴'} {'🔒 ' if bot_name in locked_bots else ''}{bot_name}", "callback": self.bot_menu, "args": (bot_name, chat_id)}] for bot_name, info in sorted(bots.items())]

    async def main_menu_handler(self, call, chat_id: int):
        await call.edit(self.strings("managing_bots"), reply_markup=await self._get_main_menu_buttons(chat_id))

    async def bot_menu(self, call, bot_name: str, chat_id: int):
        info = self._get_bots_status().get(bot_name)
        if not info: await call.answer("Бот не знайдений!", show_alert=True); return await self.main_menu_handler(call, chat_id)
        
        is_locked = bot_name in self.db.get("BotHost", "locked_bots", [])
        metadata = self.db.get("BotHost", "metadata", {})
        autorestart = metadata.get(bot_name, {}).get("autorestart", False)
        
        lock_row = [{"text": self.strings("btn_unlock"), "callback": self.unlock_bot, "args": (bot_name, chat_id)}] if is_locked else \
                   [{"text": self.strings("btn_delete"), "callback": self.delete_bot_confirm, "args": (bot_name, chat_id)}, {"text": self.strings("btn_lock"), "callback": self.lock_bot, "args": (bot_name, chat_id)}]
        
        autorestart_btn = {"text": self.strings("btn_autorestart_on") if autorestart else self.strings("btn_autorestart_off"), "callback": self.toggle_autorestart, "args": (bot_name, chat_id)}

        buttons = [
            [{"text": self.strings("btn_turn_off") if info["status"] else self.strings("btn_turn_on"), "callback": self.toggle_bot, "args": (bot_name, chat_id)}],
            lock_row,
            [{"text": self.strings("btn_export"), "callback": self.export_menu, "args": (bot_name, chat_id)}, {"text": self.strings("btn_terminal"), "callback": self.start_terminal_from_menu, "args": (bot_name, chat_id)}],
            [autorestart_btn, {"text": self.strings("btn_logs"), "callback": self.show_logs, "args": (bot_name, chat_id)}],
        ]
        
        if len(list((self.BOTS_DIR / bot_name).glob("**/*.py"))) > 1:
            buttons.append([{"text": self.strings("btn_change_main_file"), "callback": self.change_main_file_menu, "args": (bot_name, chat_id)}])
            
        buttons.append([{"text": self.strings("btn_back"), "callback": self.main_menu_handler, "args": (chat_id,)}])
        await call.edit(f"<b>Керування ботом:</b> <code>{bot_name}</code>", reply_markup=buttons)

    async def show_logs(self, call, bot_name: str, chat_id: int):
        logs = self.db.get("BotHost", f"logs_{bot_name}")
        if not logs: return await call.answer(self.strings("no_logs").format(bot_name), show_alert=True)
        log_text = "\n".join(f"<code>{utils.escape_html(line)}</code>" for line in logs)
        back_button = [[{"text": self.strings["btn_back"], "callback": self.bot_menu, "args": (bot_name, chat_id)}]]
        await call.edit(f"{self.strings('bot_logs_header').format(bot_name)}\n{log_text}", reply_markup=back_button)

    async def toggle_autorestart(self, call, bot_name: str, chat_id: int):
        metadata = self.db.get("BotHost", "metadata", {})
        current_state = metadata.setdefault(bot_name, {}).get("autorestart", False)
        metadata[bot_name]["autorestart"] = not current_state
        self.db.set("BotHost", "metadata", metadata)
        
        await call.answer(self.strings("autorestart_on" if not current_state else "autorestart_off").format(bot_name))
        await self.bot_menu(call, bot_name, chat_id)

    async def change_main_file_menu(self, call, bot_name: str, chat_id: int):
        bot_dir, metadata = self.BOTS_DIR / bot_name, self.db.get("BotHost", "metadata", {})
        py_files = [p.relative_to(bot_dir).as_posix() for p in bot_dir.glob("**/*.py")]
        current_main = metadata.get(bot_name, {}).get("main_file", f"{bot_name}.py")
        
        buttons = [[{"text": f"{'👈 ' if file == current_main else '🐍 '}{file}", "callback": self.set_main_file_action, "args": (bot_name, file, chat_id)}] for file in py_files]
        buttons.append([{"text": self.strings["btn_back"], "callback": self.bot_menu, "args": (bot_name, chat_id)}])
        await call.edit(self.strings("select_new_main_file").format(bot_name), reply_markup=buttons)

    async def set_main_file_action(self, call, bot_name: str, new_main_file: str, chat_id: int):
        metadata = self.db.get("BotHost", "metadata", {}); metadata.setdefault(bot_name, {})["main_file"] = new_main_file
        self.db.set("BotHost", "metadata", metadata)
        await call.answer(self.strings("main_file_changed").format(bot_name, new_main_file))
        if self._get_bots_status().get(bot_name, {}).get("status"):
            await call.edit(self.strings("restarting_with_new_file"))
            await self._stop_bot(bot_name); await asyncio.sleep(1); await self._start_bot(bot_name)
        await self.bot_menu(call, bot_name, chat_id)

    async def _perform_rename(self, old, new):
        is_running = old in self.db.get("BotHost", "running_bots", {})
        await self._stop_bot(old); (self.BOTS_DIR / old).rename(self.BOTS_DIR / new)
        
        if old in (metadata := self.db.get("BotHost", "metadata", {})):
            metadata[new] = metadata.pop(old); self.db.set("BotHost", "metadata", metadata)
        
        if old in (locked := self.db.get("BotHost", "locked_bots", [])):
            locked.remove(old); locked.append(new); self.db.set("BotHost", "locked_bots", locked)

        if logs := self.db.get("BotHost", f"logs_{old}"):
            self.db.set("BotHost", f"logs_{new}", logs); self.db.set("BotHost", f"logs_{old}", None)

        if is_running: await self._start_bot(new)

    async def toggle_bot(self, call, bot_name: str, chat_id: int):
        info = self._get_bots_status().get(bot_name)
        if info['status']:
            await self._stop_bot(bot_name)
            await call.answer(self.strings["bot_stopped"])
        else:
            await self._start_bot(bot_name)
            await call.answer(self.strings["bot_started"])
        await asyncio.sleep(0.5); await self.bot_menu(call, bot_name, chat_id)

    async def delete_bot_confirm(self, call, bot_name: str, chat_id: int):
        if bot_name in self.db.get("BotHost", "locked_bots", []): return await call.answer(self.strings["bot_is_locked_del"], show_alert=True)
        await call.edit(self.strings("confirm_delete").format(bot_name), reply_markup=[[{"text": self.strings("btn_confirm_del"), "callback": self.delete_bot_action, "args": (bot_name, chat_id)}, {"text": self.strings("btn_cancel_del"), "callback": self.bot_menu, "args": (bot_name, chat_id)}]])

    async def delete_bot_action(self, call, bot_name: str, chat_id: int):
        await self._stop_bot(bot_name)
        if (bot_dir := self.BOTS_DIR / bot_name).exists(): shutil.rmtree(bot_dir)
        self.db.set("BotHost", f"logs_{bot_name}", None)
        if bot_name in (locked := self.db.get("BotHost", "locked_bots", [])):
            locked.remove(bot_name); self.db.set("BotHost", "locked_bots", locked)
        if bot_name in (metadata := self.db.get("BotHost", "metadata", {})):
            del metadata[bot_name]; self.db.set("BotHost", "metadata", metadata)
        await call.answer(self.strings["bot_deleted"]); await self.main_menu_handler(call, chat_id)
        
    async def lock_bot(self, call, bot_name: str, chat_id: int):
        locked = self.db.get("BotHost", "locked_bots", []); locked.append(bot_name); self.db.set("BotHost", "locked_bots", locked)
        await call.answer(self.strings["bot_locked"]); await self.bot_menu(call, bot_name, chat_id)

    async def unlock_bot(self, call, bot_name: str, chat_id: int):
        if bot_name in (locked := self.db.get("BotHost", "locked_bots", [])):
            locked.remove(bot_name); self.db.set("BotHost", "locked_bots", locked)
        await call.answer(self.strings["bot_unlocked"]); await self.bot_menu(call, bot_name, chat_id)

    async def export_menu(self, call, bot_name: str, chat_id: int):
        await call.edit(self.strings("export_prompt").format(bot_name), reply_markup=[[{"text": self.strings("btn_export_here"), "callback": self.export_bot_action, "args": (bot_name, chat_id)}, {"text": self.strings("btn_export_saved"), "callback": self.export_bot_action, "args": (bot_name, self.client.tg_id)}], [{"text": self.strings("btn_back"), "callback": self.bot_menu, "args": (bot_name, chat_id)}]])

    async def export_bot_action(self, call, bot_name: str, target_chat_id: int):
        await call.answer(self.strings["archiving"])
        if not (self.BOTS_DIR / bot_name).is_dir(): return await call.answer(f"Папка бота {bot_name} не знайдена!", show_alert=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = await utils.run_sync(shutil.make_archive, base_name=f"{temp_dir}/{bot_name}", format="zip", root_dir=self.BOTS_DIR, base_dir=bot_name)
            await self.client.send_file(target_chat_id, archive_path, caption=f"🗂 <b>Архів бота:</b> <code>{bot_name}</code>")
        await call.answer(self.strings["bot_exported"]); await self.bot_menu(call, bot_name, target_chat_id)

    async def _terminal_updater_task(self, chat_id: int, message_id: int, bot_name: str, queue: asyncio.Queue):
        logs = deque(maxlen=15)
        last_update_time = 0
        
        async def update_message():
            nonlocal last_update_time
            # <<< ВИПРАВЛЕННЯ: Спершу створюємо рядок, потім вставляємо у f-string
            log_content = utils.escape_html('\n'.join(logs))
            text = f"{self.strings('term_started').format(bot_name)}\n\n<b>{self.strings('term_logs_header')}:</b>\n<tg-spoiler>{log_content}</tg-spoiler>"
            try:
                await self.client.edit_message(chat_id, message_id, text)
            except MessageNotModifiedError:
                pass
            except Exception as e:
                logger.error(f"Terminal updater error for {bot_name}: {e}")
                if "invalid" in str(e).lower() and "message id" in str(e).lower():
                    raise asyncio.CancelledError
            last_update_time = asyncio.get_event_loop().time()

        while True:
            try:
                log_line = await asyncio.wait_for(queue.get(), timeout=1.0)
                logs.append(log_line)
                
                if asyncio.get_event_loop().time() - last_update_time > 1.5:
                    await update_message()
            except asyncio.TimeoutError:
                if queue.qsize() == 0 and len(logs) > 0 and asyncio.get_event_loop().time() - last_update_time > 1.5:
                    await update_message()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Terminal task unexpected error: {e}")
                break
        
        await update_message()
    
    @loader.command(ru_doc="<назва> - Запустити термінал для бота")
    async def botterm(self, message: Message):
        """<назва> - Запустити інтерактивний термінал для бота"""
        bot_name = utils.get_args_raw(message)
        if not bot_name: return await utils.answer(message, self.strings("term_args"))
        if not self._get_bots_status().get(bot_name, {}).get("status"): return await utils.answer(message, self.strings("term_not_running").format(bot_name))
        if message.chat_id in self.terminal_sessions and any(s['bot_name'] == bot_name for s in self.terminal_sessions[message.chat_id].values()):
            return await utils.answer(message, self.strings("term_already_exists").format(bot_name))
        
        queue = asyncio.Queue()
        term_msg = await utils.answer(message, self.strings('term_started').format(bot_name))
        updater_task = asyncio.create_task(self._terminal_updater_task(term_msg.chat_id, term_msg.id, bot_name, queue))
        
        if term_msg.chat_id not in self.terminal_sessions: self.terminal_sessions[term_msg.chat_id] = {}
        self.terminal_sessions[term_msg.chat_id][term_msg.id] = {"bot_name": bot_name, "queue": queue, "task": updater_task}
        await message.delete()

    async def start_terminal_from_menu(self, call, bot_name: str, chat_id: int):
        msg = await self.client.send_message(chat_id, f".botterm {bot_name}")
        await self.botterm(msg)
        await call.answer(f"Термінал для {bot_name} запущено.")

    @loader.command(ru_doc="<назва> - Зупинити термінал для бота")
    async def stopterm(self, message: Message):
        """<назва> - Зупинити термінал для бота в поточному чаті"""
        bot_name = utils.get_args_raw(message)
        if not bot_name: return await utils.answer(message, self.strings("term_args"))
        if not await self._close_bot_terminals(bot_name, self.strings("term_stopped").format(bot_name), message.chat_id):
            await utils.answer(message, self.strings("term_not_found").format(bot_name))

    async def _close_bot_terminals(self, bot_name: str, final_text: str, specific_chat_id: int = None):
        closed = False
        chats_to_check = [specific_chat_id] if specific_chat_id else list(self.terminal_sessions.keys())
        for chat_id in chats_to_check:
            if chat_id not in self.terminal_sessions: continue
            for msg_id, session in list(self.terminal_sessions[chat_id].items()):
                if session["bot_name"] == bot_name:
                    session["task"].cancel()
                    try: await self.client.edit_message(chat_id, msg_id, final_text)
                    except Exception: pass
                    del self.terminal_sessions[chat_id][msg_id]
                    closed = True
            if not self.terminal_sessions[chat_id]: del self.terminal_sessions[chat_id]
        return closed

    @loader.watcher(no_commands=True, only_replies=True)
    async def terminal_input_watcher(self, message: Message):
        if message.chat_id not in self.terminal_sessions or message.reply_to_msg_id not in self.terminal_sessions[message.chat_id]: return
        session = self.terminal_sessions[message.chat_id][message.reply_to_msg_id]
        if process := self.bot_processes.get(session["bot_name"]):
            try:
                process.stdin.write((message.raw_text + '\n').encode('utf-8'))
                await process.stdin.drain()
                await message.delete()
            except (BrokenPipeError, OSError) as e: logger.error(f"Can't write to {session['bot_name']} stdin: {e}")
