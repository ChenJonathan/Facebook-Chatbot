from datetime import datetime

_threads = []  # Called repeatedly
_timers = []   # Called when time is exceeded


def polling():
    now = datetime.now()
    for handler in _threads:
        handler(now)


# - Handler should take in time
def add_thread(handler):
    _threads.append(handler)


# - Handler should take in time and args
def add_timer(time, handler, args):
    index = 0
    while index < len(_timers) and _timers[index][0] < time:
        index += 1
    _timers.insert(index, (time, handler, args))


def _timer_handler(time):
    while len(_timers) and time > _timers[0][0]:
        timer_time, handler, args = _timers.pop(0)
        handler(timer_time, args)


add_thread(_timer_handler)
