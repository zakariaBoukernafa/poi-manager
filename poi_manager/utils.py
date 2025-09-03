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


