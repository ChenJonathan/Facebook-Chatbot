from fbchat.models import *

from mongo import *
from util import *

talent_descriptions = {
    Talent.TITAN: 'Increases your ATK and DEF by ' + str(talent_constants[Talent.TITAN]) + ' each per point.',
    Talent.BERSERKER: 'Increases your ATK and SPD by ' + str(talent_constants[Talent.BERSERKER]) + ' each per point.',
    Talent.VANGUARD: 'Increases your DEF and SPD by ' + str(talent_constants[Talent.VANGUARD]) + ' each per point.',
    Talent.SURVIVOR: 'Increases your maximum health by ' + str(talent_constants[Talent.SURVIVOR]) + ' per point.',
    Talent.MISTWEAVER: 'Regenerates ' + str(talent_constants[Talent.MISTWEAVER]) + ' health per hour per point.',
    Talent.MERCHANT: 'Increases gold gained through battle, explore, and quest by ' +
                     str(talent_constants[Talent.MERCHANT]) + '% per point.',
    Talent.EXPLORER: 'Increases all explore rewards by ' + str(talent_constants[Talent.EXPLORER]) + '% per point.',
    Talent.WANDERER: 'Increases travel speed by ' + str(talent_constants[Talent.WANDERER]) + '% per point.'
}

talent_summaries = {
    Talent.TITAN: lambda x: format_num(talent_bonus(x, Talent.TITAN), sign=True) + ' ATK, ' +
                            format_num(talent_bonus(x, Talent.TITAN), sign=True) + ' DEF',
    Talent.BERSERKER: lambda x: format_num(talent_bonus(x, Talent.BERSERKER), sign=True) + ' ATK, ' +
                                format_num(talent_bonus(x, Talent.BERSERKER), sign=True) + ' SPD',
    Talent.VANGUARD: lambda x: format_num(talent_bonus(x, Talent.VANGUARD), sign=True) + ' DEF, ' +
                               format_num(talent_bonus(x, Talent.VANGUARD), sign=True) + ' SPD',
    Talent.SURVIVOR: lambda x: format_num(talent_bonus(x, Talent.SURVIVOR), sign=True) + ' max health',
    Talent.MISTWEAVER: lambda x: format_num(talent_bonus(x, Talent.MISTWEAVER), sign=True) + ' health per hour',
    Talent.MERCHANT: lambda x: format_num(talent_bonus(x, Talent.MERCHANT), sign=True) + '% gold gain',
    Talent.EXPLORER: lambda x: format_num(talent_bonus(x, Talent.EXPLORER), sign=True) + '% explore rewards',
    Talent.WANDERER: lambda x: format_num(talent_bonus(x, Talent.WANDERER), sign=True) + '% travel speed'
}


def generate_talent_info(client, user, thread_id):
    reply = 'Talent information has been sent to you. Check your private messages (or message requests).'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = '<<Branching Paths>>\n'
    reply += 'Spend talent points with "!talent <slot> <amount>" in a group chat. '
    reply += '<amount> defaults to 1 if left blank. You have '
    reply += str(user['Talents'][Talent.UNSPENT.value]) + ' unspent talent points.'

    for i, talent in enumerate(list(Talent)[1:]):
        if talent == Talent.UNSPENT:
            continue
        reply += '\n\n' + str(i + 1) + '. ' + talent.value + ': ' + str(user['Talents'][talent.value])
        reply += ' (' + talent_summaries[talent](user) + ')\n-> ' + talent_descriptions[talent]
    client.send(Message(reply), thread_id=user['_id'])


def spend_talent_points(client, user, slot, amount, thread_id):
    if slot <= 0 or slot >= len(Talent):
        reply = 'Invalid slot number.'
    elif amount < 1:
        reply = 'Invalid point amount.'
    else:
        count = user['Talents'][Talent.UNSPENT.value]
        if count < amount:
            reply = 'You don\'t have enough points.'
        else:
            talent = list(Talent)[slot]
            if talent is Talent.SURVIVOR and user['_id'] in client.user_health:
                healing = amount * talent_constants[Talent.SURVIVOR]
                client.user_health[user['_id']] = min(client.user_health[user['_id']] + healing, base_health(user))
            talent_spend(user['_id'], talent.value, amount)
            reply = 'You have spent ' + str(amount) + ' talent point' + ('' if amount == 1 else 's')
            reply += ' training in the ways of the ' + talent.value + '.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def reset_talent_points(client, user, thread_id):
    cost = user['GoldFlow'] // 10
    total = sum(count for talent, count in user['Talents'].items())
    if user['_id'] in client.user_health:
        client.user_health[user['_id']] = min(client.user_health[user['_id']], default_health)
    gold_flow_add(user['_id'], -cost)
    talent_reset(user['_id'], total)
    reply = 'Your talents have been reset at the cost of ' + str(cost) + ' gold per hour.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)