from datetime import datetime
from json import load, dumps
from pathlib import Path

class FileMethods:

    @classmethod
    def create_datafile(cls, path, base_data):
        Path(path).touch()
        with open(path, 'w') as raw:
            print(dumps(base_data), file=raw)

    @classmethod
    def fetch_database_data(cls, path) -> dict:
        with open(path, 'r') as raw:
            data_dict = load(raw)
        return data_dict

    @classmethod
    def send_to_database(cls, path, data_dict: dict):
        data_to_save = {**cls.fetch_database_data(path), **data_dict}
        with open(path, 'w') as raw:
            print(dumps(data_to_save), file=raw)

class TimeMethods:

    @classmethod
    def formatted_timestamp(cls) -> list:
        timestamp = datetime.now()
        timevals = ['year', 'month', 'day', 'hour', 'minute', 'second']
        return [timestamp.__getattribute__(val) for val in timevals]

    @classmethod
    def get_time_dif(cls, timestamp1, timestamp2):
        diff = datetime(*tuple(timestamp1)) - datetime(*tuple(timestamp2))
        return [diff.days, diff.seconds]
