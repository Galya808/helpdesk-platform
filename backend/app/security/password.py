from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
dummy_password_hash = password_hash.hash("dummy-password-used-for-timing-protection")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)
