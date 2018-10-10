from datetime import timedelta
import random

from command import *
from consume import *
from data import terms, definitions
from polling import *

_quests = {}


def _quest_timer(client, time, args):
    quest, thread_id = args["Quest"], args["ThreadID"]
    if thread_id not in _quests:
        add_group_consumption(_prompt_handler, None, thread_id)
    _quests[thread_id] = quest
    client.send(Message(quest["Question"]), thread_id=thread_id, thread_type=ThreadType.GROUP)


def _prompt_handler(client, author, text, thread_id, thread_type):
    quest = _quests[thread_id]
    if author["_id"] not in quest["Attempted"]:
        quest["Attempted"].add(author["_id"])
        if text == str(quest["Correct"] + 1) or text == quest["Answers"][quest["Correct"]]:
            del _quests[thread_id]
            reward = int(len(quest["Answers"]) * random.uniform(2, 10))
            author["Gold"] += reward
            user_update(author["_id"], {"$set": {"Gold": author["Gold"]}})
            reply = "{} has gained {} gold ".format(author["Name"], format_num(reward, truncate=True))
            reply += "and is now at {} gold total!".format(format_num(author["Gold"] + reward, truncate=True))
            client.reactToMessage(client.last_message.uid, MessageReaction.YES)
            client.send(Message(reply), thread_id=thread_id, thread_type=thread_type)
            return True
        else:
            client.reactToMessage(client.last_message.uid, MessageReaction.NO)
    return False


def _quest_handler(client, author, args, thread_id, thread_type):
    try:
        choices = int(args) if len(args) else 5
        choices = min(max(choices, 2), 20)
    except ValueError:
        return False
    indices = random.sample(range(0, len(terms)), choices)
    correct = random.randint(0, choices - 1)
    if random.randint(0, 1):
        quest = {}
        quest["Question"] = "Which word means \"{}\"?".format(definitions[indices[correct]])
        quest["Answers"] = [terms[index] for index in indices]
    else:
        quest = {}
        quest["Question"] = "What does \"{}\" mean?".format(terms[indices[correct]])
        quest["Answers"] = [definitions[index] for index in indices]
    for i, answer in enumerate(quest["Answers"]):
        quest["Question"] += "\n{}. {}".format(i + 1, answer)
    quest["Correct"] = correct
    quest["Attempted"] = set()

    if thread_type == ThreadType.USER:
        if thread_id not in _quests:
            add_user_consumption(_prompt_handler, author["_id"])
        _quests[thread_id] = quest
        reply = quest["Question"]
    else:
        add_timer(datetime.now() + timedelta(seconds=5), _quest_timer, {"Quest": quest, "ThreadID": thread_id})
        reply = "A quest will be sent out in 5 seconds."
    client.send(Message(reply), thread_id=thread_id, thread_type=thread_type)
    return True


_quest_info = """<<Quest>>
*Usage*: "!quest"
Generates a multiple choice question. The first correct response will reward gold. Only one response per user.

*Usage*: "!quest <choices>"
*Example*: "!quest 8"
Generates a multiple choice question with <choices> choices.
"""

map_user_command(["quest", "q"], _quest_handler, 2, _quest_info)
map_group_command(["quest", "q"], _quest_handler, 0, _quest_info)
