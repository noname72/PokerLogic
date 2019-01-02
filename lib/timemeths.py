def formatted_timestamp(cls) -> list:
    timestamp = datetime.now()
    timevals = ['year', 'month', 'day', 'hour', 'minute', 'second']
    return '/'.join([timestamp.__getattribute__(val) for val in timevals])

def get_time_diff(cls, timestamp1, timestamp2):
    diff = datetime(*tuple(timestamp1)) - datetime(*tuple(timestamp2))
    days = diff.days
    seconds = diff.seconds
    hours, seconds = seconds // 3600, seconds % 3600
    minutes, seconds = seconds // 60, seconds % 60
    return {'days': days, 'hours': hours,
            'minutes': minutes, 'seconds': seconds}

def get_time_remainder(cls, timestamp1, timestamp2, waiting_period=4):
    timestamp1 = [int(elt) for elt in timestamp1.split('/')]
    timestamp2 = [int(elt) for elt in timestamp2.split('/')]
    diff = datetime(*tuple(timestamp1) - datetime(*tuple(timestamp2))
    seconds = (waiting_period - diff.days * 24) * 3600 - diff.seconds
    seconds = seconds if seconds >= 0 else 0
    days, seconds = seconds // (3600 * 24), seconds % (3600 * 24)
    hours, seconds = seconds // 3600, seconds % 3600
    minutes, seconds = seconds // 60, seconds % 60
    return {'days': days, 'hours': hours,
            'minutes': minutes, 'seconds': seconds}
