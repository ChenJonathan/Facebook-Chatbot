import random

from command import *
from consume import *
from util import *

_MIN_PLAYERS = 5
_MAX_PLAYERS = 10
_GOOD_COUNT = [3, 4, 4, 5, 6, 6]
_GOOD_CHARS = ["Merlin", "Percival"]
_EVIL_CHARS = ["Mordred", "Morgana", "Oberon"]
_DESCRIPTIONS = {
    "Merlin": "Knows all evil players except Mordred",
    "Percival": "Knows who Merlin and Morgana are, but not who is who",
    "Mordred": "Evil wins if he guesses Merlin's identity correctly",
    "Morgana": "Appears as Merlin to Percival",
    "Oberon": "Unknown to the other evil players",
}
_TEAM_SIZE = [
    [2, 3, 2, 3, 3],
    [2, 3, 4, 3, 4],
    [2, 3, 3, 4, 4],
    [3, 4, 4, 5, 5],
    [3, 4, 4, 5, 5],
    [3, 4, 4, 5, 5]
]
_FAIL_THRESHOLD = [[2 if size >= 2 and quest == 3 else 1 for quest in range(5)] for size in range(len(_TEAM_SIZE))]


class _GameState(Enum):
    LOBBY = "Lobby"
    TEAM = "Team"
    VOTE = "Vote"
    QUEST = "Quest"
    ASSASSIN = "Assassin"


_games = {group["_id"]: group["Avalon"] for group in group_query_all({"Avalon": {"$exists": True}})}


def _avalon_handler(author, text, thread_id, thread_type):
    command, text = partition(text, ["status", "start", "join", "add", "clear", "submit"])
    command = command or "status"

    result = False
    if command == "start":
        result = _start_handler(author, thread_id)
    elif command == "join":
        result = _join_handler(author, thread_id)
    elif command in ["add", "clear", "submit"]:
        result = _team_handler(author, command, text, thread_id)

    if result:
        group_update(thread_id, {"$set": {"Avalon": _games[thread_id]}})
    else:
        _status_handler(thread_id)
    return True


def _start_handler(author, thread_id):
    game = _games.get(thread_id, None)
    if game is None:
        _games[thread_id] = {
            "State": _GameState.LOBBY.value,
            "Host": author["_id"],
            "Players": {author["_id"]: {"Name": author["Name"], "Role": None}}
        }
        if "Alias" in author:
            _games[thread_id]["Players"][author["_id"]]["Name"] += " ({})".format(author["Alias"])
        reply = "An Avalon session has been created! Join the game with \"!avalon join\" "
        reply += "and use \"!avalon start\" again once all players have joined to begin."
    elif game["State"] == _GameState.LOBBY.value:
        if len(game["Players"]) < _MIN_PLAYERS:
            reply = "Not enough players to start the game. (minimum {})".format(_MIN_PLAYERS)
        elif author["_id"] != game["Host"]:
            reply = "Only the session host can start the game."
        else:
            _assign_roles(thread_id)
            game["State"] = _GameState.TEAM.value
            game["Leaders"] = [random.choice(list(game["Players"].keys()))]
            game["Team"] = []
            game["Success"] = 0
            game["Fail"] = 0
            team_size = _TEAM_SIZE[len(game["Players"]) - _MIN_PLAYERS][0]
            reply = "The current leader is {} ".format(game["Players"][game["Leaders"][-1]]["Name"])
            reply += "and {} players are needed for the team.\n\n".format(team_size)
            reply += "Use \"!avalon add <name>\" to add players to the team, \"!avalon clear\" "
            reply += "to clear the current team, and \"!avalon submit\" to submit the current team."
    else:
        reply = "A game is already in progress."
    client.send(Message(reply), thread_id, ThreadType.GROUP)
    return True


def _join_handler(author, thread_id):
    game = _games.get(thread_id, None)
    if game is None:
        return False
    elif game["State"] != _GameState.LOBBY.value:
        reply = "A game is already in progress."
    else:
        players = game["Players"]
        if author["_id"] in players:
            reply = "You are already in the session."
        elif len(players) >= _MAX_PLAYERS:
            reply = "The session is full. (maximum {})".format(_MAX_PLAYERS)
        else:
            players[author["_id"]] = {"Name": author["Name"], "Role": None}
            if "Alias" in author:
                game["Players"][author["_id"]]["Name"] += " ({})".format(author["Alias"])
            reply = "You have joined the session! There are now {} players total.".format(len(players))
    client.send(Message(reply), thread_id, ThreadType.GROUP)
    return True


def _team_handler(author, command, text, thread_id):
    game = _games.get(thread_id, None)
    if game is None:
        return False
    elif game["State"] != _GameState.TEAM.value:
        reply = "A team is not currently being proposed."
    elif game["Leaders"][-1] != author["_id"]:
        reply = "Only the leader can propose a team."

    elif command == "add":
        quest = game["Success"] + game["Fail"]
        if len(game["Team"]) >= _TEAM_SIZE[len(game["Players"]) - _MIN_PLAYERS][quest]:
            reply = "The team is full."
        else:
            user = match_user_in_group(thread_id, text)
            if user is None:
                reply = "User not found."
            elif user["_id"] in game["Team"]:
                reply = "{} is already on the team.".format(user["Name"])
            elif user["_id"] not in game["Players"]:
                reply = "{} is not in the game.".format(user["Name"])
            else:
                game["Team"].append(user["_id"])
                reply = "{} has been added to the team.".format(user["Name"])

    elif command == "clear":
        game["Team"].clear()
        reply = "The team has been cleared."

    else:
        quest = game["Success"] + game["Fail"]
        team_size = _TEAM_SIZE[len(game["Players"]) - _MIN_PLAYERS][quest]
        if len(game["Team"]) != team_size:
            reply = "{} players are needed for the team. The current team size is {}."
            reply = reply.format(team_size, len(game["Team"]))
        else:
            game["State"] = _GameState.VOTE.value
            game["Votes"] = {"Accept": [], "Reject": []}
            prompt = "A team has been proposed consisting of the following players:"
            for member in game["Team"]:
                prompt += "\n-> {}".format(game["Players"][member]["Name"])
            prompt += "\n\nEnter \"accept\" to accept the team or \"reject\" to reject the team."
            for player_id in game["Players"].keys():
                add_active_consumption(None, player_id, ThreadType.USER, "AvalonVote", prompt, thread_id)
            reply = "A team has been proposed! Please vote on the team in private chat."

    client.send(Message(reply), thread_id, ThreadType.GROUP)
    return True


def _status_handler(thread_id):
    game = _games.get(thread_id, None)
    if game is None:
        reply = "There is no active Avalon session. Create one with \"!avalon start\"."

    elif game["State"] == _GameState.LOBBY.value:
        reply = "The Avalon game has not yet started. Join the game with \"!avalon join\" "
        reply += "and use \"!avalon start\" again once all players have joined to begin.\n\n"
        reply += "*Host*: {}\n".format(game["Players"][game["Host"]]["Name"])
        reply += "*Current players*:"
        for player in game["Players"].values():
            reply += "\n-> {}".format(player["Name"])

    elif game["State"] == _GameState.TEAM.value:
        reply = "A quest team is being proposed. The leader should use \"!avalon add <name>\" "
        reply += "to add players to the team, \"!avalon clear\" to clear the current team, "
        reply += "and \"!avalon submit\" to submit the current team.\n\n"
        reply += "*Successful quests*: {}\n".format(game["Success"])
        reply += "*Failed quests*: {}\n\n".format(game["Fail"])
        reply += "*Rejected teams*: {}\n".format(len(game["Leaders"]) - 1)
        reply += "*Current leader*: {}\n".format(game["Players"][game["Leaders"][-1]]["Name"])
        if len(game["Team"]):
            reply += "*Current team*:"
            for player in game["Team"]:
                reply += "\n-> {}".format(game["Players"][player]["Name"])

    elif game["State"] == _GameState.VOTE.value:
        reply = "A quest team is being voted on. Enter \"accept\" or \"reject\" in private chat to enter your vote.\n\n"
        reply += "*Successful quests*: {}\n".format(game["Success"])
        reply += "*Failed quests*: {}\n\n".format(game["Fail"])
        reply += "*Rejected teams*: {}\n".format(len(game["Leaders"]) - 1)
        reply += "*Current leader*: {}\n".format(game["Players"][game["Leaders"][-1]]["Name"])
        reply += "*Current team*:"
        for player in game["Team"]:
            reply += "\n-> {}".format(game["Players"][player]["Name"])
        votes = game["Votes"]
        missing = filter(lambda p: p[0] not in votes["Accept"] and p[0] not in votes["Reject"], game["Players"].items())
        reply += "\n\n*Missing votes*:"
        for user_id, player in sorted(missing, key=lambda p: p[1]["Name"]):
            reply += "\n-> {}".format(player["Name"])

    elif game["State"] == _GameState.QUEST.value:
        reply = "The selected team is embarking on a quest. Use \"success\" or \"fail\" in private chat "
        reply += "to determine the outcome of the quest if you are on the selected team.\n\n"
        reply += "*Successful quests*: {}\n".format(game["Success"])
        reply += "*Failed quests*: {}\n\n".format(game["Fail"])
        reply += "*Current team*:"
        for player in game["Team"]:
            reply += "\n-> {}".format(game["Players"][player]["Name"])
        missing = filter(lambda p: p not in game["Votes"]["Success"] and p not in game["Votes"]["Fail"], game["Team"])
        reply += "\n\n*Missing votes*:"
        for user_id in sorted(missing, key=lambda p: game["Players"][p]["Name"]):
            reply += "\n-> {}".format(game["Players"][user_id]["Name"])

    else:
        reply = "Three quests have been completed successfully, but Mordred still has one last chance to kill "
        reply += "Merlin. Use \"!avalon kill <name>\" to select your target if you are Mordred.\n\n"
        mordred = next(filter(lambda p: p["Role"] == "Mordred", game["Players"].values()), None)["Name"]
        reply += "*Mordred*: {}".format(mordred)
        reply += "*Merlin*: ???"

    client.send(Message(reply), thread_id, ThreadType.GROUP)


def _assign_roles(thread_id):
    game = _games[thread_id]
    order = list(game["Players"].values())
    random.shuffle(order)
    good_count = _GOOD_COUNT[len(order) - _MIN_PLAYERS]
    good_players, evil_players = order[:good_count], order[good_count:]
    roles = {}
    for i, player in enumerate(good_players):
        if i < len(_GOOD_CHARS):
            player["Role"] = _GOOD_CHARS[i]
            roles[_GOOD_CHARS[i]] = player["Name"]
        else:
            player["Role"] = "Servant"
    for i, player in enumerate(evil_players):
        if i < len(_EVIL_CHARS):
            player["Role"] = _EVIL_CHARS[i]
            roles[_EVIL_CHARS[i]] = player["Name"]
        else:
            player["Role"] = "Minion"

    # Inform players of their roles
    for user_id, player in game["Players"].items():
        role_name = player["Role"]
        if role_name == "Servant":
            role_name = "a Loyal Servant of Arthur"
        elif role_name == "Minion":
            role_name = "a Minion of Mordred"
        reply = "You are playing as {}! ".format(role_name)

        if player["Role"] == "Merlin":
            reply += "You are on the side of good. You know the identities of all evil players except for Mordred, "
            reply += "but make sure Mordred doesn't figure out your identity or your side will lose!\n\n"
            reply += "The evil players (minus Mordred) are as follows:"
            for name in sorted([player["Name"] for player in filter(lambda p: p["Role"] != "Mordred", evil_players)]):
                reply += "\n-> {}".format(name)

        elif player["Role"] == "Percival":
            reply += "You are on the side of good. You know the identities of Merlin (good) and Morgana (evil), "
            reply += "but you don't know who is who! Make sure Mordred doesn't figure out Merlin's identity "
            reply += "or your side will lose!\n\n"
            reply += "Merlin and Morgana are {} and {}.".format(*sorted([roles["Merlin"], roles["Morgana"]]))

        elif player["Role"] == "Servant":
            reply += "You are on the side of good. Help complete three quests successfully and make sure "
            reply += "Merlin's identity isn't found out to win the game!"

        elif player["Role"] == "Mordred":
            reply += "You are on the side of evil. Merlin does not know you are evil and you will have a chance "
            reply += "to assassinate him at the end of the game, so try to figure out Merlin's identity!\n\n"
            reply += "The other evil players are as follows:"
            for name in sorted([player["Name"] for player in filter(lambda p: p != player, evil_players)]):
                reply += "\n-> {}".format(name)

        elif player["Role"] == "Morgana":
            reply += "You are on the side of evil. Percival knows who you and Merlin are, but can't figure out "
            reply += "who is who. Try to deceive him!\n\n"
            reply += "The other evil players are as follows:"
            for name in sorted([player["Name"] for player in filter(lambda p: p != player, evil_players)]):
                reply += "\n-> {}".format(name)

        elif player["Role"] == "Oberon":
            reply += "You are on the side of evil. But unlike other evil characters, you don't know who the other "
            reply += "evil characters are and they don't know who you are! Try to cooperate with your team without "
            reply += "revealing your identity to the side of good!"

        elif player["Role"] == "Minion":
            reply += "You are on the side of evil. Help sabotage three quests or have Mordred figure out "
            reply += "Merlin's identity to win the game!\n\n"
            reply += "The other evil players are as follows:"
            for name in sorted([player["Name"] for player in filter(lambda p: p != player, evil_players)]):
                reply += "\n-> {}".format(name)

        client.send(Message(reply), user_id, ThreadType.USER)

    # Summarize game rules
    group_reply = "The game has begun! The side of good wins if three quests are completed successfully. "
    group_reply += "The side of evil wins if three quests fail or if Mordred can guess Merlin's identity "
    group_reply += "at the end of the game.\n\n"
    group_reply += "For each quest, a leader is chosen at random to select the team for that quest. "
    group_reply += "The rest of the players vote to accept or reject the team. Once a team is chosen, "
    group_reply += "the team members can chose whether or not to sabotage the quest.\n\n"
    group_reply += "Many players have special roles. The special roles in this game are as follows:"
    for role_name in filter(lambda r: r in roles, _GOOD_CHARS):
        group_reply += "\n-> *{}* ({}): {}".format(role_name, "Good", _DESCRIPTIONS[role_name])
    for role_name in filter(lambda r: r in roles, _EVIL_CHARS):
        group_reply += "\n-> *{}* ({}): {}".format(role_name, "Evil", _DESCRIPTIONS[role_name])


def _prompt_vote(author, text, thread_id, thread_type, args):
    text, _ = partition(text, ["accept", "reject"])
    game = _games.get(args, None)
    if game is None:
        result = True
        reply = "The game is no longer active."
    elif text is None:
        result = False
        reply = "Enter \"accept\" to accept the team or \"reject\" to reject the team."
    else:
        result = True
        if text == "accept":
            game["Votes"]["Accept"].append(author["_id"])
        elif text == "reject":
            game["Votes"]["Reject"].append(author["_id"])
        reply = "Your vote has been received."
    client.send(Message(reply), thread_id, ThreadType.USER)

    # Check for vote completion
    if len(game["Players"]) == len(game["Votes"]["Accept"]) + len(game["Votes"]["Reject"]):
        group_reply = "*Accept*:"
        for user_id in game["Votes"]["Accept"]:
            group_reply += "\n-> {}".format(game["Players"][user_id]["Name"])
        group_reply += "\n*Reject*:"
        for user_id in game["Votes"]["Reject"]:
            group_reply += "\n-> {}".format(game["Players"][user_id]["Name"])

        # Begin quest phase
        if len(game["Votes"]["Accept"]) > len(game["Votes"]["Reject"]):
            game["State"] = _GameState.QUEST.value
            del game["Leaders"]
            game["Votes"] = {"Success": [], "Fail": []}
            quest = game["Success"] + game["Fail"]
            fail_threshold = _FAIL_THRESHOLD[len(game["Players"]) - _MIN_PLAYERS][quest]
            group_reply += "\n\nThe vote has passed! The team must now vote to complete the quest in private chat."
            group_reply += " The quest fails with {} fail vote(s).".format(fail_threshold)
            prompt = "\n\nEnter \"success\" or \"fail\" in private chat to determine the outcome of the quest. "
            prompt += "The quest fails with {} fail vote(s).".format(fail_threshold)
            for player_id in game["Team"]:
                add_active_consumption(None, player_id, ThreadType.USER, "AvalonQuest", prompt, args)

        # Five attempts failed
        elif len(game["Leaders"]) >= 5:
            group_reply += "\n\nFive attempts to create a team have failed. The side of evil wins by default."
            del _games[args]
            # TODO game rewards

        # Create another team
        else:
            game["State"] = _GameState.TEAM.value
            order = list(game["Players"].keys())
            random.shuffle(order)
            for user_id in order:
                if user_id not in game["Leaders"]:
                    game["Leaders"].append(user_id)
                    break
            game["Team"] = []
            group_reply += "\n\nThe vote has failed. {} ".format(game["Players"][game["Leaders"][-1]]["Name"])
            group_reply += "has been assigned as the new leader. As before, use \"!avalon add <name>\", "
            group_reply += "\"!avalon clear\", and \"!avalon submit\" to create the team."
            if len(game["Leaders"]) == 5:
                group_reply += "\n\nNote that this is the last attempt! The side of evil wins by default "
                group_reply += "if the vote does not pass this time."
        client.send(Message(group_reply), args, ThreadType.GROUP)

    if args in _games:
        group_update(args, {"$set": {"Avalon": _games[args]}})
    else:
        group_update(args, {"$unset": {"Avalon": None}})
    return result


def _prompt_quest(author, text, thread_id, thread_type, args):
    text, _ = partition(text, ["success", "fail"])
    game = _games.get(args, None)
    if game is None:
        result = True
        reply = "The game is no longer active."
    elif text is None:
        result = False
        reply = "Enter \"success\" or \"fail\" to determine the outcome of the quest."
    else:
        result = True
        reply = "Your vote has been received."
        if text == "success":
            game["Votes"]["Success"].append(author["_id"])
        elif text == "fail":
            role = game["Players"][author["_id"]]["Role"]
            if role in _GOOD_CHARS or role == "Servant":
                result = False
                reply = "The side of good is not allowed to fail quests. Please vote success instead."
            else:
                game["Votes"]["Fail"].append(author["_id"])
        if len(game["Team"]) == len(game["Votes"]["Success"]) + len(game["Votes"]["Fail"]):
            quest = game["Success"] + game["Fail"]
            fail_threshold = _FAIL_THRESHOLD[len(game["Players"]) - _MIN_PLAYERS][quest]

            if len(game["Votes"]["Fail"]) < fail_threshold:
                game["Success"] += 1
                group_reply = "The quest was completed successfully!"
            else:
                game["Fail"] += 1
                group_reply = "The quest was sabotaged!"

            if game["Success"] >= 3:
                group_reply += " The side of good wins!"  # TODO assassin phase and delete team / votes
                del _games[args]
            elif game["Fail"] >= 3:
                group_reply += " The side of evil wins!"  # TODO game rewards
                del _games[args]
            else:
                game["State"] = _GameState.TEAM.value
                game["Leaders"] = [random.choice(list(game["Players"].keys()))]
                game["Team"] = []
                del game["Votes"]
                quest = game["Success"] + game["Fail"]
                team_size = _TEAM_SIZE[len(game["Players"]) - _MIN_PLAYERS][quest]
                group_reply += "\n\n*Successful quests*: {}\n".format(game["Success"])
                group_reply += "*Failed quests: {}*\n\n".format(game["Fail"])
                group_reply += "The new leader is {} ".format(game["Players"][game["Leaders"][-1]]["Name"])
                group_reply += "and {} players are needed for the team.".format(team_size)
                group_reply += "Use \"!avalon add <name>\" to add players to the team, \"!avalon clear\" "
                group_reply += "to clear the current team, and \"!avalon submit\" to submit the current team."

            client.send(Message(group_reply), args, ThreadType.GROUP)
    client.send(Message(reply), thread_id, ThreadType.USER)
    if args in _games:
        group_update(args, {"$set": {"Avalon": _games[args]}})
    else:
        group_update(args, {"$unset": {"Avalon": None}})
    return result


_avalon_info = """<<Avalon>>
*Usage*: "!avalon start"
Creates an Avalon session. Use this command again after players have joined to start the game.

*Usage*: "!avalon join"
Joins the chat's current Avalon session.

*Usage*: "!avalon status"
Summarizes the status of the current Avalon session and tells you how to continue."""

map_group_command(["avalon"], _avalon_handler, 1, _avalon_info)
add_handler("AvalonVote", _prompt_vote)
add_handler("AvalonQuest", _prompt_quest)
