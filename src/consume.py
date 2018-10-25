from fbchat.models import *

_user_map = {}
_group_map = {}


# - Handler should take in author, text, thread_id, and thread_type
def add_user_consumption(handler, user_id):
    if user_id not in _user_map:
        _user_map[user_id] = []
    _user_map[user_id].append(handler)


# - Handler should take in author, text, thread_id, and thread_type
def add_group_consumption(handler, user_id, thread_id):
    if thread_id not in _group_map:
        _group_map[thread_id] = {}
    current_map = _group_map[thread_id]
    if user_id not in current_map:
        current_map[user_id] = []
    current_map[user_id].append(handler)


# - Handler should take in author, text, thread_id, and thread_type
def add_consumption(handler, user_id, thread_id, thread_type):
    if thread_type == ThreadType.USER:
        add_user_consumption(handler, thread_id)
    else:
        add_group_consumption(handler, user_id, thread_id)


def try_user_consumption(author, text, thread_id):
    if thread_id not in _user_map:
        return False
    consumed = False

    for consumer in list(_user_map[thread_id]):
        result = consumer(author, text, thread_id, ThreadType.USER)
        if result:
            _user_map[thread_id].remove(consumer)
            consumed = True
    if not len(_user_map[thread_id]):
        del _user_map[thread_id]
    return consumed


def try_group_consumption(author, text, thread_id):
    author_id = author["_id"]
    if thread_id not in _group_map:
        return False
    current_map = _group_map[thread_id]
    consumed = False

    if author_id in current_map:
        for consumer in list(current_map[author_id]):
            result = consumer(author, text, thread_id, ThreadType.GROUP)
            if result:
                current_map[author_id].remove(consumer)
                consumed = True
        if not len(current_map[author_id]):
            del current_map[author_id]

    if None in current_map:
        for consumer in list(current_map[None]):
            result = consumer(author, text, thread_id, ThreadType.GROUP)
            if result:
                current_map[None].remove(consumer)
                consumed = True
        if not len(current_map[None]):
            del current_map[None]

    if not len(current_map):
        del _group_map[thread_id]
    return consumed
