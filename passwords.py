"""Password hashing shared by the desktop and web interfaces."""

import hashlib
import secrets

ITERATIONS = 200_000


def hash_password(password):
    """Return a salted PBKDF2-HMAC-SHA256 digest."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS
    )
    return salt + "$" + digest.hex()


def verify_password(password, stored):
    """Check a password against its stored salt and digest."""
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS
    )
    return secrets.compare_digest(check.hex(), digest)
