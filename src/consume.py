from fbchat.models import *

from util import *

_handler_map = {}  # Handler name to handler
_active_map, _passive_map = load_state("Consumes")  # thread_id to user_id to consumer dicts


# - Handler should take in author, text, thread_id, thread_type, and args
def add_handler(handler_name, handler):
    _handler_map[handler_name] = handler


def add_active_consumption(user_id, thread_id, thread_type, handler_name, prompt=None, args=None):
    if thread_id not in _active_map:
        _active_map[thread_id] = {}
    current_map = _active_map[thread_id]

    # - "None" is used to represent all users
    user_id = user_id or "None"
    if user_id not in current_map:
        current_map[user_id] = []
        if prompt is not None:
            client.send(Message(prompt), thread_id, thread_type)

    current_map[user_id].append({
        "Handler": handler_name,
        "Prompt": prompt,
        "Args": args
    })
    save_state("Consumes", [_active_map, _passive_map])


def add_passive_consumption(user_id, thread_id, handler_name, args=None):
    if thread_id not in _passive_map:
        _passive_map[thread_id] = {}
    current_map = _passive_map[thread_id]

    # - "None" is used to represent all users
    user_id = user_id or "None"
    if user_id not in current_map:
        current_map[user_id] = []

    current_map[user_id].append({
        "Handler": handler_name,
        "Args": args
    })
    save_state("Consumes", [_active_map, _passive_map])


def try_consumption(author, text, thread_id, thread_type):
    if _try_active_consumption(author, text, thread_id, thread_type):
        return True
    _try_passive_consumption(author, text, thread_id, thread_type)
    return False


def _try_active_consumption(author, text, thread_id, thread_type):
    author_id = author["_id"]
    if thread_id not in _active_map:
        return False
    current_map = _active_map[thread_id]
    current_key = author_id if author_id in current_map else "None"
    if current_key not in current_map:
        return False

    consumer = current_map[current_key][0]
    handler = _handler_map[consumer["Handler"]]
    if handler(author, text, thread_id, thread_type, consumer["Args"]):
        current_map[current_key].pop(0)
        if len(current_map[current_key]):
            prompt = current_map[current_key][0]["Prompt"]
            if prompt is not None:
                client.send(Message(prompt), thread_id, thread_type)
        else:
            del current_map[current_key]
            if not len(current_map):
                del _active_map[thread_id]
    save_state("Consumes", [_active_map, _passive_map])
    return True


def _try_passive_consumption(author, text, thread_id, thread_type):
    author_id = author["_id"]
    if thread_id not in _passive_map:
        return False
    current_map = _passive_map[thread_id]

    for current_key in [author_id, "None"]:
        if current_key not in current_map:
            continue

        for consumer in list(current_map[current_key]):
            if consumer["Handler"] not in _handler_map:
                current_map["None"].remove(consumer)
                continue

            handler = _handler_map[consumer["Handler"]]
            if handler(author, text, thread_id, thread_type, consumer["Args"]):
                current_map[current_key].remove(consumer)

        if not len(current_map[current_key]):
            del current_map[current_key]
            if not len(current_map):
                del _passive_map[thread_id]

    save_state("Consumes", [_active_map, _passive_map])
    return False
