"""
Encryption utilities for FOCUS.
Used for encrypting/decrypting face embeddings at rest (DPDP Act compliance).
Uses Fernet symmetric encryption from the cryptography library.
"""
import os
import numpy as np
from cryptography.fernet import Fernet
from config.settings import settings


def _get_fernet() -> Fernet:
    """Get or generate Fernet encryption key."""
    key = settings.EMBEDDING_ENCRYPTION_KEY
    if not key:
        # Auto-generate and warn
        key = Fernet.generate_key().decode()
        # In production, this should be set in .env
        import warnings
        warnings.warn(
            "EMBEDDING_ENCRYPTION_KEY not set in .env — using auto-generated key. "
            "Set a persistent key for production use.",
            RuntimeWarning
        )
    else:
        # Ensure it's bytes
        if isinstance(key, str):
            key = key.encode()
    return Fernet(key if isinstance(key, bytes) else key.encode())


def encrypt_embedding(embedding: np.ndarray) -> bytes:
    """
    Encrypt a numpy embedding array for secure storage.
    DPDP Act PRI-05: Only encrypted embeddings are persisted.
    """
    f = _get_fernet()
    embedding_bytes = embedding.tobytes()
    return f.encrypt(embedding_bytes)


def decrypt_embedding(encrypted_data: bytes) -> np.ndarray:
    """Decrypt an encrypted embedding back to numpy array."""
    f = _get_fernet()
    decrypted = f.decrypt(encrypted_data)
    return np.frombuffer(decrypted, dtype=np.float32)


def generate_encryption_key() -> str:
    """Generate a new Fernet key. Use this to populate EMBEDDING_ENCRYPTION_KEY in .env."""
    return Fernet.generate_key().decode()
