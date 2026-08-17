import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic
from urllib.parse import urlparse

from telethon import TelegramClient, events, utils
from telethon.errors import (
    FloodWaitError,
    InviteRequestSentError,
    SessionPasswordNeededError,
    UserAlreadyParticipantError,
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import (
    CheckChatInviteRequest,
    ImportChatInviteRequest,
)
from telethon.tl.types import ChannelParticipantsAdmins

from account_credentials import CredentialError, credential_store
from config import ACCOUNT_SESSION_DIR
from database import (
    get_connected_account,
    get_connected_accounts,
    save_connected_account,
)

logger = logging.getLogger(__name__)


class AccountError(RuntimeError):
    """A safe, user-facing connected-account error."""


@dataclass
class LoginFlow:
    client: TelegramClient
    session_name: str
    phone: str
    phone_code_hash: str


@dataclass
class CollectedUser:
    user_id: int
    label: str
    username: str = ""
    sent: bool | None = None


@dataclass
class CollectionFlow:
    owner_user_id: int
    listen_account_id: int
    send_account_id: int
    group_ref: str
    handler: object
    back_data: str = "acc:menu"
    users: dict[int, CollectedUser] = field(default_factory=dict)
    last_rendered_at: float = 0.0
    render_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class AccountManager:
    def __init__(self):
        self.session_dir = Path(ACCOUNT_SESSION_DIR).resolve()
        self.clients: dict[tuple[int, int], TelegramClient] = {}
        self.login_flows: dict[int, LoginFlow] = {}
        self.collections: dict[int, CollectionFlow] = {}

    def configured_for(self, owner_user_id: int) -> bool:
        return credential_store.configured_for(owner_user_id)

    def _credentials(self, owner_user_id: int) -> tuple[int, str]:
        try:
            credentials = credential_store.get(owner_user_id)
        except CredentialError as exc:
            raise AccountError(str(exc)) from exc
        if not credentials:
            raise AccountError(
                "⚠️ TELEGRAM_API_ID va TELEGRAM_API_HASH ni avval kiriting."
            )
        return credentials

    def _session_path(self, session_name: str) -> str:
        safe_name = Path(session_name).name
        return str(self.session_dir / safe_name)

    def _new_client(self, owner_user_id: int, session_name: str) -> TelegramClient:
        api_id, api_hash = self._credentials(owner_user_id)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        return TelegramClient(
            self._session_path(session_name),
            api_id,
            api_hash,
            auto_reconnect=True,
        )

    async def restore(self):
        self.session_dir.mkdir(parents=True, exist_ok=True)
        for owner_user_id in self._all_known_owners():
            for account_id, _username, _name, session_name in get_connected_accounts(
                owner_user_id
            ):
                try:
                    client = self._new_client(owner_user_id, session_name)
                    await client.connect()
                    if await client.is_user_authorized():
                        self.clients[(owner_user_id, account_id)] = client
                    else:
                        await client.disconnect()
                except Exception:
                    # A broken account must not prevent the bot from starting.
                    logger.exception(
                        "Connected account restore failed for owner=%s account=%s",
                        owner_user_id,
                        account_id,
                    )
                    continue

    @staticmethod
    def _all_known_owners() -> list[int]:
        import sqlite3

        from database import DB_NAME

        with sqlite3.connect(DB_NAME) as conn:
            return [
                row[0]
                for row in conn.execute(
                    "SELECT DISTINCT owner_user_id FROM connected_accounts"
                ).fetchall()
            ]

    async def get_client(self, owner_user_id: int, account_id: int) -> TelegramClient:
        row = get_connected_account(owner_user_id, account_id)
        if not row:
            raise AccountError("❌ Account topilmadi. Menyuni qayta oching.")

        key = (int(owner_user_id), int(account_id))
        client = self.clients.get(key)
        if client is None:
            client = self._new_client(owner_user_id, row[3])
            await client.connect()
            if not await client.is_user_authorized():
                await client.disconnect()
                raise AccountError("❌ Account sessioni eskirgan. Accountni qayta ulang.")
            self.clients[key] = client
        elif not client.is_connected():
            await client.connect()
        return client

    async def begin_phone_login(self, owner_user_id: int, phone: str):
        self._credentials(owner_user_id)
        await self.cancel_login(owner_user_id)
        session_name = f"account_{int(owner_user_id)}_{secrets.token_hex(8)}"
        client = self._new_client(owner_user_id, session_name)
        await client.connect()
        sent_code = await client.send_code_request(phone)
        self.login_flows[int(owner_user_id)] = LoginFlow(
            client,
            session_name,
            phone,
            sent_code.phone_code_hash,
        )

    async def finish_code(self, owner_user_id: int, code: str):
        flow = self.login_flows.get(int(owner_user_id))
        if not flow:
            raise AccountError("❌ Login sessiyasi topilmadi. Qayta urinib ko‘ring.")
        try:
            await flow.client.sign_in(
                phone=flow.phone,
                code=code,
                phone_code_hash=flow.phone_code_hash,
            )
        except SessionPasswordNeededError:
            return "2fa", None
        return "ready", await self.finalize_login(owner_user_id)

    async def finish_2fa(self, owner_user_id: int, password: str):
        flow = self.login_flows.get(int(owner_user_id))
        if not flow:
            raise AccountError("❌ Login sessiyasi topilmadi. Qayta urinib ko‘ring.")
        await flow.client.sign_in(password=password)
        return await self.finalize_login(owner_user_id)

    async def finalize_login(self, owner_user_id: int):
        flow = self.login_flows.get(int(owner_user_id))
        if not flow:
            raise AccountError("❌ Login sessiyasi topilmadi.")
        me = await flow.client.get_me()
        display_name = " ".join(x for x in (me.first_name, me.last_name) if x)
        save_connected_account(
            owner_user_id,
            me.id,
            me.username or "",
            display_name or str(me.id),
            flow.session_name,
        )
        self.clients[(int(owner_user_id), int(me.id))] = flow.client
        try:
            Path(self._session_path(flow.session_name) + ".session").chmod(0o600)
        except OSError:
            logger.warning("Could not tighten session file permissions", exc_info=True)
        self.login_flows.pop(int(owner_user_id), None)
        return me

    async def cancel_login(self, owner_user_id: int):
        flow = self.login_flows.pop(int(owner_user_id), None)
        if flow:
            await flow.client.disconnect()
            for suffix in (".session", ".session-journal"):
                try:
                    Path(self._session_path(flow.session_name) + suffix).unlink(missing_ok=True)
                except OSError:
                    logger.warning("Could not remove incomplete session file", exc_info=True)

    async def join_group(self, owner_user_id: int, account_id: int, group_link: str):
        client = await self.get_client(owner_user_id, account_id)
        value = (group_link or "").strip()
        try:
            invite_hash = self._invite_hash(value)
            if invite_hash:
                updates = await client(ImportChatInviteRequest(invite_hash))
                entity = updates.chats[0] if updates.chats else None
                return "joined", utils.get_peer_id(entity) if entity else None

            username = self._public_username(value)
            if not username:
                raise AccountError("❌ Guruh havolasi noto‘g‘ri.")
            await client(JoinChannelRequest(username))
            entity = await client.get_entity(username)
            return "joined", utils.get_peer_id(entity)
        except UserAlreadyParticipantError:
            if invite_hash:
                invite = await client(CheckChatInviteRequest(invite_hash))
                entity = getattr(invite, "chat", None)
            else:
                entity = await client.get_entity(self._public_username(value))
            return "already", utils.get_peer_id(entity) if entity else None
        except InviteRequestSentError:
            return "requested", None
        except FloodWaitError as exc:
            raise AccountError(
                f"⏳ Telegram limiti: {exc.seconds} soniyadan keyin qayta urinib ko‘ring."
            ) from exc
        except AccountError:
            raise
        except Exception as exc:
            raise AccountError(f"❌ Guruhga qo‘shilib bo‘lmadi: {type(exc).__name__}") from exc

    @staticmethod
    def _invite_hash(value: str) -> str | None:
        parsed = urlparse(value if "://" in value else f"https://{value}")
        path = parsed.path.strip("/")
        if path.startswith("+"):
            return path[1:]
        if path.startswith("joinchat/"):
            return path.split("/", 1)[1]
        return None

    @staticmethod
    def _public_username(value: str) -> str | None:
        if value.startswith("@"):
            return value
        parsed = urlparse(value if "://" in value else f"https://{value}")
        path = parsed.path.strip("/")
        return f"@{path.split('/', 1)[0]}" if path else None

    async def get_admins(self, owner_user_id: int, account_id: int, group_ref: str):
        client = await self.get_client(owner_user_id, account_id)
        try:
            entity = await client.get_entity(group_ref)
            result = []
            async for user in client.iter_participants(
                entity, filter=ChannelParticipantsAdmins
            ):
                label = f"@{user.username}" if user.username else (
                    " ".join(x for x in (user.first_name, user.last_name) if x)
                    or str(user.id)
                )
                result.append(CollectedUser(user.id, label, user.username or ""))
            return result
        except FloodWaitError as exc:
            raise AccountError(
                f"⏳ Telegram limiti: {exc.seconds} soniyadan keyin qayta urinib ko‘ring."
            ) from exc
        except Exception as exc:
            raise AccountError(f"❌ Adminlarni olib bo‘lmadi: {type(exc).__name__}") from exc

    async def start_collection(
        self,
        owner_user_id: int,
        listen_account_id: int,
        send_account_id: int,
        group_ref: str,
        on_change,
    ):
        owner_user_id = int(owner_user_id)
        if owner_user_id in self.collections:
            raise AccountError(
                "⚠️ Username terish jarayoni hali davom etmoqda. "
                "Avval /usernamestop bilan to‘xtating."
            )
        client = await self.get_client(owner_user_id, listen_account_id)
        entity = await client.get_entity(group_ref)

        async def handler(event):
            if event.out:
                return
            sender = await event.get_sender()
            if not sender or getattr(sender, "bot", False):
                return
            flow = self.collections.get(owner_user_id)
            if not flow or sender.id in flow.users:
                return
            label = f"@{sender.username}" if sender.username else (
                " ".join(x for x in (sender.first_name, sender.last_name) if x)
                or str(sender.id)
            )
            flow.users[sender.id] = CollectedUser(
                sender.id, label, sender.username or ""
            )
            async with flow.render_lock:
                delay = 1.0 - (monotonic() - flow.last_rendered_at)
                if delay > 0:
                    await asyncio.sleep(delay)
                await on_change(flow)
                flow.last_rendered_at = monotonic()

        client.add_event_handler(handler, events.NewMessage(chats=entity))
        flow = CollectionFlow(
            owner_user_id,
            int(listen_account_id),
            int(send_account_id),
            group_ref,
            handler,
        )
        self.collections[owner_user_id] = flow
        return flow

    async def stop_collection(self, owner_user_id: int) -> bool:
        flow = self.collections.pop(int(owner_user_id), None)
        if not flow:
            return False
        try:
            client = await self.get_client(owner_user_id, flow.listen_account_id)
            if flow.handler is not None:
                client.remove_event_handler(flow.handler)
        except Exception:
            logger.exception("Could not detach username collector for owner=%s", owner_user_id)
        return True

    async def set_static_users(
        self,
        owner_user_id: int,
        listen_account_id: int,
        send_account_id: int,
        group_ref: str,
        users: list[CollectedUser],
    ):
        await self.stop_collection(owner_user_id)
        flow = CollectionFlow(
            int(owner_user_id),
            int(listen_account_id),
            int(send_account_id),
            group_ref,
            handler=None,
        )
        flow.users = {user.user_id: user for user in users}
        self.collections[int(owner_user_id)] = flow
        return flow

    async def send_to_collected_user(self, owner_user_id: int, target_user_id: int, text: str):
        flow = self.collections.get(int(owner_user_id))
        if not flow or int(target_user_id) not in flow.users:
            raise AccountError("❌ Username terish jarayoni yoki user topilmadi.")
        client = await self.get_client(owner_user_id, flow.send_account_id)
        try:
            await client.send_message(int(target_user_id), text)
            flow.users[int(target_user_id)].sent = True
            return True
        except FloodWaitError as exc:
            raise AccountError(
                f"⏳ Telegram limiti: {exc.seconds} soniyadan keyin qayta urinib ko‘ring."
            ) from exc
        except Exception:
            logger.info(
                "Selected message delivery failed for owner=%s target=%s",
                owner_user_id,
                target_user_id,
                exc_info=True,
            )
            flow.users[int(target_user_id)].sent = False
            return False

    async def shutdown(self):
        for owner_user_id in list(self.collections):
            await self.stop_collection(owner_user_id)
        for owner_user_id in list(self.login_flows):
            await self.cancel_login(owner_user_id)
        for client in list(self.clients.values()):
            await client.disconnect()
        self.clients.clear()


account_manager = AccountManager()
