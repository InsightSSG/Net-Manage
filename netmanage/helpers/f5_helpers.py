import re
from datetime import datetime, timedelta
from typing import Tuple, Union


def convert_tmsh_time(tmsh_time: str, adjust_end_date=False) -> \
        Union[str, Tuple[str, str]]:
    """
    Convert F5's tmsh format time to ISO 8601 format time.

    For inputs like 'now-2d', this function returns a tuple containing start
    and end times in ISO 8601 format. If a single date or datetime is provided,
    it returns a string representation of that date or datetime in ISO 8601
    format.

    Parameters
    ----------
    tmsh_time : str
        Time in F5's tmsh format.
    adjust_end_date : bool, optional
        If True, adjusts the end date by adding an extra day. Useful when
        specifying date ranges. Defaults to False.

    Returns
    -------
    Union[str, Tuple[str, str]]
        Either a single date-time string or a tuple containing start and end
        date-times.
    """
    if 'now' in tmsh_time:
        end_time = datetime.utcnow()
        match = re.search(r'-(\d+)d', tmsh_time)
        if match:
            days = int(match.group(1))
            start_time = end_time - timedelta(days=days)
            return (start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    end_time.strftime('%Y-%m-%dT%H:%M:%SZ'))
        else:
            return end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    elif re.match(r'^\d{4}-\d{2}-\d{2}$', tmsh_time):  # if 'YYYY-MM-DD' format
        end_time = datetime.strptime(tmsh_time, '%Y-%m-%d')
        if adjust_end_date:
            end_time += timedelta(days=1)
    else:
        end_time = datetime.strptime(tmsh_time, '%Y-%m-%dT%H:%M:%SZ')
    return end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
