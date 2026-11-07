import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import jwt
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PRIVATE_KEY = BASE_DIR / "certs" / "jwt-private.pem"
DEFAULT_PUBLIC_KEY = BASE_DIR / "certs" / "jwt-public.pem"
ALGORITHM = "RS256"

def _read_key(env_var: str, default: Path) -> str:
    path = Path(os.getenv(env_var, default))
    try:
        return path.read_text()
    except FileNotFoundError:
        raise RuntimeError(
            f"JWT-ключ не найден: {path}. "
            f"Сгенерируй ключи в certs/ или задай {env_var}."
        ) from None
def load_private_key() -> str:
    return _read_key("JWT_PRIVATE_KEY_PATH", DEFAULT_PRIVATE_KEY)

def load_public_key() -> str:
    return _read_key("JWT_PUBLIC_KEY_PATH", DEFAULT_PUBLIC_KEY)

def create_access_token(
        user_id: int,
        expires_delta: timedelta = timedelta(minutes=15),
) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, load_private_key(), ALGORITHM)

def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        load_public_key(),
        algorithms=[ALGORITHM],
        options={"require": ["sub", "iat", "exp"]},
    )