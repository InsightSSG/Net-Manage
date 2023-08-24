#!/usr/bin/env python3

import re
from typing import Dict


def tokenize_f5_log(log_message: str) -> Dict[str, str]:
    """
    Tokenize an F5 log message into its constituent components.

    This function parses an F5 log message, extracts its core components,
    and obfuscates any passwords present in the message.

    Parameters
    ----------
    log_message : str
        The raw F5 log message string to be tokenized.

    Returns
    -------
    Dict[str, str]
        A dictionary with the tokenized components of the log message.

    Examples
    --------
    >>> log = "ltm 2023-08-10T09:02:08Z info bigip-1 systemd-journal[642]: Suppressed 781 messages from /system.slice/httpd.service"  # noqa
    >>> tokenize_f5_log(log)
    {'log_name': 'ltm', 'time stamp': '2023-08-10T09:02:08Z', ...}
    """

    # Extract the log name, timestamp, and the rest of the message
    log_name, timestamp, remainder = re.split(' ', log_message, 2)

    # Extract year, month, day, hour, minute, and seconds from the timestamp
    year, month, day = timestamp.split('T')[0].split('-')
    hour, minute, seconds = timestamp.split('T')[1].rstrip('Z').split(':')

    # Split the remainder by spaces to get the rest of the components
    level, host_name, service_pid, message_text = re.split(' ', remainder, 3)

    # Obfuscate the password, if present
    password_pattern = re.compile(r'\(([^)]+)\): BAD PASSWORD')
    message_text = password_pattern.sub(
        lambda m: '(*' + '*'*(len(m.group(1))-2) + '*): BAD PASSWORD',
        message_text)

    return {
        "log_name": log_name,
        "time stamp": timestamp,
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "seconds": seconds,
        "level": level,
        "host name": host_name,
        "service[pid]": service_pid.rstrip(':'),
        "message text": message_text
    }
