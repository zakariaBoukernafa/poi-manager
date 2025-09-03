import decimal
import os
from pathlib import Path
from typing import Optional, Tuple

from django.core.serializers.json import DjangoJSONEncoder


class CustomFieldJSONEncoder(DjangoJSONEncoder):
    """
    Custom JSON encoder that handles decimal values properly.
    """
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super().default(o)


def get_file_type(file_path: str) -> Optional[str]:
    """
    Determine file type from extension.

    Returns:
        'csv', 'json', 'xml', or None
    """
    ext = Path(file_path).suffix.lower()

    mapping = {
        ".csv": "csv",
        ".json": "json",
        ".xml": "xml",
    }

    return mapping.get(ext)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"


def validate_file_size(file_path: str, max_size_mb: int = 500) -> Tuple[bool, str]:
    """
    Validate file size is within limits.

    Returns:
        (is_valid, message)
    """
    file_size = os.path.getsize(file_path)
    max_size = max_size_mb * 1024 * 1024

    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        return False, f"File size ({size_mb:.1f} MB) exceeds limit ({max_size_mb} MB)"

    return True, "OK"


def chunked_bulk_create(model_class, objects, batch_size=1000):
    """
    Create objects in chunks to avoid memory issues.
    """
    created_count = 0

    for i in range(0, len(objects), batch_size):
        chunk = objects[i : i + batch_size]
        created = model_class.objects.bulk_create(
            chunk, ignore_conflicts=True, batch_size=min(batch_size, 500)
        )
        created_count += len(created)

    return created_count
