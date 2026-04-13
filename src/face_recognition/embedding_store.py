"""
Embedding store management — load/save encrypted embeddings.
"""
import numpy as np
from pathlib import Path
from typing import Dict
from src.utils.crypto import encrypt_embedding, decrypt_embedding
from src.utils.logger import logger


class EmbeddingStore:
    """Manages encrypted face embedding files on disk."""

    def __init__(self, embedding_dir: Path = Path("data/embeddings")):
        self.embedding_dir = embedding_dir
        self.embedding_dir.mkdir(parents=True, exist_ok=True)

    def save(self, roll_number: str, embedding: np.ndarray):
        """Save encrypted embedding to disk."""
        encrypted = encrypt_embedding(embedding)
        path = self.embedding_dir / f"{roll_number}.enc"
        path.write_bytes(encrypted)
        logger.debug(f"Saved embedding for {roll_number}")

    def load(self, roll_number: str) -> np.ndarray | None:
        """Load and decrypt a single embedding."""
        path = self.embedding_dir / f"{roll_number}.enc"
        if not path.exists():
            return None
        try:
            return decrypt_embedding(path.read_bytes())
        except Exception as e:
            logger.error(f"Failed to load embedding for {roll_number}: {e}")
            return None

    def load_all(self) -> Dict[str, np.ndarray]:
        """Load all embeddings into memory."""
        embeddings = {}
        for enc_file in self.embedding_dir.glob("*.enc"):
            roll = enc_file.stem
            emb = self.load(roll)
            if emb is not None:
                embeddings[roll] = emb
        logger.info(f"Loaded {len(embeddings)} embeddings from store")
        return embeddings

    def delete(self, roll_number: str) -> bool:
        """Delete embedding (DPDP consent revocation)."""
        path = self.embedding_dir / f"{roll_number}.enc"
        if path.exists():
            path.unlink()
            logger.info(f"Deleted embedding for {roll_number}")
            return True
        return False

    def exists(self, roll_number: str) -> bool:
        """Check if an embedding exists for a student."""
        return (self.embedding_dir / f"{roll_number}.enc").exists()

    def count(self) -> int:
        """Count enrolled students."""
        return len(list(self.embedding_dir.glob("*.enc")))
