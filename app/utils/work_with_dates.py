from datetime import datetime

from fastapi import HTTPException, status
from loguru import logger


@logger.catch(reraise=True)
def parse_like_date(date_str: str):
    """
    Parses a string into date using formats:
    `DD.MM.YYYY` | `YYYY.MM.DD` | `DD-MM-YYYY` | `YYYY-MM-DD`
    """
    date_formats = ("%d.%m.%Y", "%Y.%m.%d", "%d-%m-%Y", "%Y-%m-%d")
    for date_format in date_formats:
        try:
            return datetime.strptime(date_str, date_format).date()
        except ValueError:
            pass
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Cannot parse date format «{date_str}». "
                "Please, use one of this examples: "
                f"{' | '.join(date_formats)}"))
