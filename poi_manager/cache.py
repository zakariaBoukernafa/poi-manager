from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json


def make_cache_key(prefix, *args, **kwargs):
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)

    if len(key_string) > 200:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    return key_string


def cache_result(timeout=300, key_prefix="poi"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = make_cache_key(
                f"{key_prefix}:{func.__name__}", *args[1:], **kwargs
            )

            result = cache.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result

        return wrapper

    return decorator


def invalidate_cache_pattern(pattern):
    if hasattr(cache, "_cache"):
        client = cache._cache.get_client()
        for key in client.keys(f"*{pattern}*"):
            cache.delete(key.decode("utf-8"))


def invalidate_poi_caches():
    patterns = [
        "poi_categories_with_counts",
        "import_batch_statistics",
        "nearby_*",
        "poi:*",
    ]

    for pattern in patterns:
        invalidate_cache_pattern(pattern)


class CacheInvalidator:
    @staticmethod
    def on_poi_save(sender, instance, **kwargs):
        cache.delete("poi_categories_with_counts")
        cache.delete("import_batch_statistics")
        invalidate_cache_pattern(f"nearby_*")

    @staticmethod
    def on_batch_save(sender, instance, **kwargs):
        cache.delete("import_batch_statistics")
