from threading import Thread
from icalendar import Calendar, Event, vDDDTypes
from typing import Union

from config.config import generate_database_connection, Configuration
from tools.database_interaction_functions import modulate_status, get_metadata_from_db

import pytz
import datetime
import requests
import time
import json
import sqlite3


def configure_timezone_to_UTC_if_naive(unknown_datetime: datetime.datetime) -> datetime.datetime: 
    if unknown_datetime.tzinfo is not pytz.UTC:
        utc_timezone = pytz.timezone("UTC")
        unknown_datetime = unknown_datetime.astimezone(utc_timezone)
    return unknown_datetime

def attempt_convert_to_datetime_if_not(dt_time: Union[str, datetime.datetime]) -> datetime.datetime:
    if isinstance(dt_time, datetime.datetime):
        return configure_timezone_to_UTC_if_naive(dt_time)
    elif isinstance(dt_time, str):
        date_with_time = '%Y-%m-%d %H:%M:%S.%f %Z'
        return configure_timezone_to_UTC_if_naive(datetime.datetime.strptime(dt_time, date_with_time))
    else:
        print("unaccepted dt_time given:", dt_time)

def check_events(calendar: Calendar, config: Configuration, database_connection: sqlite3.Connection) -> bool:
    event_found = False
    now = datetime.datetime.now()
    now = configure_timezone_to_UTC_if_naive(now)
    for event in calendar.walk('VEVENT'):
        end_time = event['DTEND'].dt
        start_time = event['DTSTART'].dt
        if not isinstance(start_time, datetime.datetime) or not isinstance(end_time, datetime.datetime):
            continue
        start_time = configure_timezone_to_UTC_if_naive(start_time)
        end_time = configure_timezone_to_UTC_if_naive(end_time)
        if not start_time <= now <= end_time:
            continue
        duration = end_time - start_time
        while True:
            retrieved_metadata = get_metadata_from_db(database_connection, config)
            if retrieved_metadata.status == "avaliable":
                status = "busy"
                modulate_status(status, duration, database_connection, config)
            else:
                break
        event_found = True
        break
    if event_found:
        print("event found at current time")
    return event_found

def event_thread_wrapper(config: Configuration) -> None:
    def event_checker_thread(config: Configuration) -> None:
        ics_download_link = config.calendar_at
        print("current calendar at from config is: ", ics_download_link)
        response_from_ical_request = requests.get(ics_download_link)
        calendar = Calendar.from_ical(response_from_ical_request.text)
        connection = generate_database_connection(config)
        check_events(calendar, config, connection) 
    while True:
        time.sleep(60)
        event_checker_thread(config)

