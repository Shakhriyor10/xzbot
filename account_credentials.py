import logging
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from config import ACCOUNT_SESSION_DIR, TELEGRAM_API_HASH, TELEGRAM_API_ID
from database import get_account_api_credentials, save_account_api_credentials

logger = logging.getLogger(__name__)


class CredentialError(RuntimeError):
    pass


class AccountCredentialStore:
    def __init__(self):
        self.directory = Path(ACCOUNT_SESSION_DIR).resolve()
        self.key_path = self.directory / ".credentials.key"

    def _cipher(self) -> Fernet:
        self.directory.mkdir(parents=True, exist_ok=True)
        if not self.key_path.exists():
            self.key_path.write_bytes(Fernet.generate_key())
            try:
                self.key_path.chmod(0o600)
            except OSError:
                logger.warning("Could not tighten credential key permissions", exc_info=True)
        return Fernet(self.key_path.read_bytes().strip())

    def save(self, owner_user_id: int, api_id: int, api_hash: str):
        encrypted = self._cipher().encrypt(api_hash.encode("utf-8")).decode("ascii")
        save_account_api_credentials(owner_user_id, api_id, encrypted)

    def get(self, owner_user_id: int) -> tuple[int, str] | None:
        row = get_account_api_credentials(owner_user_id)
        if row:
            try:
                api_hash = self._cipher().decrypt(row[1].encode("ascii")).decode("utf-8")
            except (InvalidToken, ValueError) as exc:
                raise CredentialError("Saqlangan API credential ochilmadi.") from exc
            return int(row[0]), api_hash
        if TELEGRAM_API_ID and TELEGRAM_API_HASH:
            return TELEGRAM_API_ID, TELEGRAM_API_HASH
        return None

    def configured_for(self, owner_user_id: int) -> bool:
        try:
            return self.get(owner_user_id) is not None
        except CredentialError:
            return False


credential_store = AccountCredentialStore()
