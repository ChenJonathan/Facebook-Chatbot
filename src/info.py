from fbchat.models import *

from mongo import *
from util import priority_names, master_priority, master_id

def generate_user_info(client, text, author):
    text = text.lower()
    is_master = author['_id'] == master_id
    if not is_master:
        return

    if len(text) == 0:
        reply = '<<Command List>>\n'
        reply += '!alias: Alias assignment\n'
        reply += '!check: See user statistics\n'
        reply += '!define: Command remapping\n'
        reply += '!help: Read documentation\n'
        reply += '!message: Gateway messaging\n'
        reply += '!perm: Change user priority\n'
        reply += '!secret: List active secrets\n'
        reply += '!wong: Response priming\n'
        reply += '(See what commands do with "!help <command>")'
    
    elif text == 'alias':
        reply = '<<Alias>>\n'
        reply += 'Usage: "!alias <alias> <search_string>"\n'
        reply += 'Example: "!alias wong Wong Liu"\n'
        reply += 'Assigns an alias to a user (found using <search_string>) for '
        reply += 'use in other private chat commands. Aliases must be a single word.'

    elif text == 'check':
        reply = '<<Check>>\n'
        reply += 'Usage: "!check <alias>"\n'
        reply += 'Returns some information on the user designated by <alias>.\n\n'
        reply += 'Usage: "!check"\n'
        reply += 'Returns some information on all users with aliases.'

    elif text == 'define':
        reply = '<<Define>>\n'
        reply += 'Usage: "!define <command> <mapping>"\n'
        reply += 'Example: "!define quit !mute"\n'
        reply += 'Example: "!define roll Jonathan Chen rolls a 6."\n'
        reply += 'Remaps <command> so that using it has the effect of the command '
        reply += 'specified in <mapping>. If <mapping> is not a command, Wong will '
        reply += 'instead send <mapping> as a message. Note that these mappings only '
        reply += 'apply to you.\n\n'
        reply += 'Usage: "!define <command>"\n'
        reply += 'Clears the mapping for <command> to its default.'

    elif text == 'help':
        reply = '<<Help>>\n'
        reply += 'Usage: "!help"\n'
        reply += 'Lists all the user commands that you can use. Differs per person.\n\n'
        reply += 'Usage: "!help <command>"\n'
        reply += 'Example: "!help secret"\n'
        reply += 'Explains the syntax and effects of the provided user <command>.'

    elif text == 'message':
        reply = '<<Message>>\n'
        reply += 'Usage: "!message <alias> <message>"\n'
        reply += 'Example: "!message raph This is Wong."\n'
        reply += 'Sends a message from Wong to the user designated by <alias>.\n\n'
        reply += 'Usage: "!message <alias>"\n'
        reply += 'Example: "!message raph"\n'
        reply += 'Sends the default chat emoji from Wong to the user designated by <alias>.'

    elif text == 'perm':
        reply = '<<Perm>>\n'
        reply += 'Usage: "!perm <priority> <alias>"\n'
        reply += 'Example: "!perm 0 raph"\n'
        reply += 'Sets the priority of the user designated by <alias> to <priority>.'

    elif text == 'secret':
        reply = '<<Secret>>\n'
        reply += 'Usage: "!secret"\n'
        reply += 'Lists all of your active secrets. This includes command mappings '
        reply += '(!define) and primed responses (!wong).'

    elif text == 'wong':
        reply = '<<Wong>>\n'
        reply += 'Usage: "!wong <response>"\n'
        reply += 'Example: "!wong Anime belongs in the trash."\n'
        reply += 'Primes a response for Wong. The next time you talk to Wong, his '
        reply += 'normal response will be replaced by <response>. Multiple responses '
        reply += 'can be primed at once - they will be used oldest first.'

    else:
        return
    client.send(Message(reply), thread_id=author['_id'], thread_type=ThreadType.USER)

def generate_group_info(client, text, author, thread_id):
    text = text.lower()
    is_master = author['_id'] == master_id

    if len(text) == 0:
        reply = '<<Command List>>\n'
        reply += '!alias: Alias assignment\n'
        reply += '!bully: Harass someone\n'
        reply += '!check: See user statistics\n'
        reply += '!daily: Subscribe to daily events\n'
        reply += '!explore: Discover new locations\n'
        reply += '!give: Give someone gold\n'
        reply += '!help: Read documentation\n'
        reply += '!inventory: Check your inventory\n'
        reply += '!jail: Send someone to jail\n'
        reply += '!mute: Kick someone from the chat\n'
        reply += '!perm: Change user priority\n'
        reply += '!quest: Earn gold through quizzes\n'
        reply += '!random: Random chat emoji / color\n'
        reply += '!roll: Roll the dice\n'
        reply += '!scoreboard: Show group rankings\n'
        reply += '!shop: Spend gold\n'
        reply += '!travel: Travel around the world\n'
        reply += '(See how commands work with "!help <command>")'

    elif text == 'alias':
        reply = '<<Alias>>\n'
        reply += 'Usage: "!alias <alias> <search_string>"\n'
        reply += 'Example: "!alias wong Wong Liu"\n'
        reply += 'Assigns an alias to a user (found using <search_string>) for '
        reply += 'use in other private chat commands. Aliases must be a single word. '
        reply += 'Only usable by ' + priority_names[master_priority] + ' priority.'

    elif text == 'bully':
        reply = '<<Bully>>\n'
        reply += 'Usage: "!bully <search_string>"\n'
        reply += 'Example: "!bully Raphael"\n'
        reply += 'Generates an insult for a user (found using <search_string>). '
        reply += 'The user defaults to you if <search_string> is left blank.'

    elif text == 'check':
        reply = '<<Check>>\n'
        reply += 'Usage: "!check <search_string>"\n'
        reply += 'Example: "!check Raphael"\n'
        reply += 'Returns some information on the user designated by <search_string>.\n\n'
        reply += 'Usage: "!check"\n'
        reply += 'Returns some information on yourself.'

    elif text == 'daily':
        reply = '<<Daily>>\n'
        reply += 'Usage: "!daily <event>"\n'
        reply += 'Example: "!daily emoji"\n'
        reply += 'Toggles the group\'s subscription to <event>. Events occur at midnight '
        reply += 'EST. Current events include the following:\n'
        reply += '"color" - Changes the chat color\n'
        reply += '"emoji" - Changes the chat emoji'

    elif text == 'explore':
        reply = '<<Explore>>\n'
        reply += 'Usage: "!explore"\n'
        reply += 'Explores the current location. Exploration will various rewards and '
        reply += 'gradually discover surrounding locations. Can be done once per hour.'

    elif text == 'give':
        reply = '<<Give>>\n'
        reply += 'Usage: "!give <amount> <search_string>"\n'
        reply += 'Example: "!give 10 Raphael"\n'
        reply += 'Gives <amount> gold to the user designated by <search_string>.'

    elif text == 'help':
        reply = '<<Help>>\n'
        reply += 'Usage: "!help"\n'
        reply += 'Lists all the group commands that you can use. Differs per person.\n\n'
        reply += 'Usage: "!help <command>"\n'
        reply += 'Example: "!help quest"\n'
        reply += 'Explains the syntax and effects of the provided group <command>.'

    elif text == 'inventory':
        reply = '<<Inventory>>\n'
        reply += 'Usage: "!inventory"\n'
        reply += 'Lists the contents of your inventory to you in a private message. '
        reply += 'Items can be found through exploration. There is no limit to '
        reply += 'inventory size.'

    elif text == 'jail':
        reply = '<<Jail>>\n'
        reply += 'Usage: "!jail"\n'
        reply += 'Sends a person to jail, preventing them from taking any actions '
        reply += '(such as questing or exploring). If the person is already in jail, '
        reply += 'they will be freed from jail instead and sent to Lith Harbor. '
        reply += 'Only usable by ' + priority_names[master_priority - 1]
        reply += ' priority and above.'

    elif text == 'mute':
        reply = '<<Mute>>\n'
        reply += 'Usage: "!mute <search_string>"\n'
        reply += 'Example: "!mute Raphael"\n'
        reply += 'Kicks a user (found using <search_string>) from the group chat. '
        reply += 'The user defaults to you if <search_string> is left blank.'

    elif text == 'perm':
        reply = '<<Perm>>\n'
        reply += 'Usage: "!perm <priority> <search_string>"\n'
        reply += 'Example: "!perm 0 Raphael"\n'
        reply += 'Sets the priority of the user designated by <search_string> '
        reply += 'to <priority>. Only usable by ' + priority_names[master_priority]
        reply += ' priority.'

    elif text == 'quest':
        reply = '<<Quest>>\n'
        reply += 'Usage: "!quest"\n'
        reply += 'Generates a multiple choice question for you. You can answer by '
        reply += 'replying with either the answer itself or the choice number. '
        reply += 'Correct responses increase gold while incorrect responses decrease it.\n\n'
        reply += 'Usage: "!quest <type>"\n'
        reply += 'Example: "!quest trivia"\n'
        reply += 'Sets the type of multiple choice question that will be generated '
        reply += 'for you. Current quest types include the following:\n'
        reply += '"vocab" - GRE vocabulary questions\n'
        reply += '"trivia" - Trivia questions from various topics'

    elif text == 'random':
        reply = '<<Random>>\n'
        reply += 'Usage: "!random"\n'
        reply += 'Randomly sets the group chat\'s color and emoji.'

    elif text == 'roll':
        reply = '<<Roll>>\n'
        reply += 'Usage: "!roll <sides>"\n'
        reply += 'Example: "!roll 10"\n'
        reply += 'Rolls a <sides> sided die. <sides> defaults to 6 if left blank.'

    elif text == 'scoreboard':
        reply = '<<Scoreboard>>\n'
        reply += 'Usage: "!scoreboard <page>"\n'
        reply += 'Example: "!scoreboard 2"\n'
        reply += 'Lists the top people in the group chat by score. Score takes all '
        reply += 'gameplay factors into account. Each page lists 9 people.'

    elif text == 'shop':
        reply = '<<Shop>>\n'
        reply += 'Usage: "!shop"\n'
        reply += 'Lists all the items available in the shop. Differs per person.\n\n'
        reply += 'Usage: "!shop <slot>"\n'
        reply += 'Example: "!shop 1"\n'
        reply += 'Purchases the shop item designated by <slot>. Make sure to check the '
        reply += 'shop first to see which item is in each slot.'

    elif text == 'travel':
        reply = '<<Travel>>\n'
        reply += 'Usage: "!travel <location>"\n'
        reply += 'Example: "!travel Ellinia"\n'
        reply += 'Sets your character on a journey to <location>. You will be unable '
        reply += 'to take any actions (such as questing or exploring) while traveling.\n\n'
        reply += 'Usage: "!travel"\n'
        reply += 'Check which locations you can travel to from your current location.'

    else:
        return
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)