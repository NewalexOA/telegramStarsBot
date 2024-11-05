from pathlib import Path
import aiofiles
import structlog
import hashlib
from typing import Optional

logger = structlog.get_logger()

class ImageCache:
    def __init__(self, cache_dir: str = "image_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"Initialized image cache in {self.cache_dir}")

    def _get_cache_path(self, image_id: str) -> Path:
        """Получает путь к кэшированному файлу"""
        # Используем хеш для создания подпапок
        hash_name = hashlib.md5(image_id.encode()).hexdigest()
        subdir = self.cache_dir / hash_name[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{image_id}.webp"

    async def get(self, image_id: str) -> Optional[bytes]:
        """Получает изображение из кэша"""
        cache_path = self._get_cache_path(image_id)
        if cache_path.exists():
            try:
                async with aiofiles.open(cache_path, 'rb') as f:
                    data = await f.read()
                logger.info(f"Cache hit for image {image_id}")
                return data
            except Exception as e:
                logger.error(f"Error reading from cache: {e}")
                return None
        return None

    async def put(self, image_id: str, data: bytes) -> bool:
        """Сохраняет изображение в кэш"""
        try:
            cache_path = self._get_cache_path(image_id)
            async with aiofiles.open(cache_path, 'wb') as f:
                await f.write(data)
            logger.info(f"Cached image {image_id}")
            return True
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")
            return False

    async def clear(self) -> None:
        """Очищает кэш"""
        try:
            for path in self.cache_dir.glob("**/*"):
                if path.is_file():
                    path.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}") 