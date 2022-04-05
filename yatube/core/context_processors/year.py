from datetime import datetime
from typing import Dict

from django.http import HttpRequest


def year(request: HttpRequest) -> Dict[str, int]:
    """Возвращает словарь с текущим годом."""
    return {
        'year': datetime.now().year
    }
