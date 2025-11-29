from cachetools import TTLCache
from typing import Any, Callable, Optional


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class BaseCache(metaclass=SingletonMeta):
    def __init__(self, ttl: int, maxsize: int = 1000):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)

    def set(self, key: str, value: Any):
        self.cache[key] = value

    async def get_or_set(self, key: str, fetcher: Callable):
        cached = self.get(key)
        if cached is not None:
            return cached

        try:
            value = await fetcher()
            self.set(key, value)
            return value
        except Exception as error:
            raise error
