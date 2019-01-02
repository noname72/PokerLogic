from datetime import datetime
from json import load, dumps
from pathlib import Path

class FileMethods:

    @staticmethod
    def create_datafile(path, base_data):
        Path(path).touch()
        with open(path, 'w', encoding='UTF-8') as raw:
            print(dumps(base_data), file=raw)

    @staticmethod
    def fetch_database_json(path) -> dict:
        with open(path, 'r') as raw:
            data_dict = load(raw)
        return data_dict

    @classmethod
    def send_to_database(cls, path, data_dict: dict):
        data_to_save = {**cls.fetch_database_json(path), **data_dict}
        with open(path, 'w', encoding='UTF-8') as _file:
            print(dumps(data_to_save), file = _file)

class TimeMethods:

    @classmethod
    def formatted_timestamp(cls) -> list:
        timestamp = datetime.now()
        timevals = ['year', 'month', 'day', 'hour', 'minute', 'second']
        return [timestamp.__getattribute__(val) for val in timevals]

    @classmethod
    def get_time_diff(cls, timestamp1, timestamp2):
        diff = datetime(*tuple(timestamp1)) - datetime(*tuple(timestamp2))
        days = diff.days
        seconds = diff.seconds
        hours, seconds = seconds // 3600, seconds % 3600
        minutes, seconds = seconds // 60, seconds % 60
        return {'days': days, 'hours': hours, 'minutes': minutes, 'seconds': seconds}

    @classmethod
    def get_time_remainder(cls, timestamp1, timestamp2, waiting_period=4):
        diff = datetime(*tuple(timestamp1)) - datetime(*tuple(timestamp2))
        seconds = (waiting_period - diff.days * 24) * 3600 - diff.seconds
        seconds = seconds if seconds >= 0 else 0
        days, seconds = seconds // (3600 * 24), seconds % (3600 * 24)
        hours, seconds = seconds // 3600, seconds % 3600
        minutes, seconds = seconds // 60, seconds % 60
        return {'days': days, 'hours': hours, 'minutes': minutes, 'seconds': seconds}
