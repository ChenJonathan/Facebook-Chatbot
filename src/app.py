from fbchat import Client
from fbchat.models import *
from flask import Flask
from base64 import b64decode
import cleverbot
import threading
import time
import traceback

from battle import begin_battle, cancel_battle, complete_battle_quest
from duel import begin_duel, cancel_duel, complete_duel_quest
from clock import set_timer
from commands import run_group_command, run_user_command
from mongo import *
from polling import loop
from quest import complete_quest
from util import *

cb = cleverbot.Cleverbot(os.environ.get('CLEVERBOT_KEY'))
lock = threading.Lock()


class ChatBot(Client):

    def __init__(self, email, password):
        super().__init__(email, password)
        init_db(self)
        priority_set(self.uid, master_priority - 1)

        self.quest_record = {}
        self.explore_record = set()
        self.duel_requests = {}
        self.user_health = {}
        self.user_states = {}

        self.message_record = {}
        self.defines = {}
        self.responses = []

        set_timer(self, lock)

    def send(self, message, thread_id=None, thread_type=ThreadType.USER):
        super().send(message, thread_id=thread_id, thread_type=thread_type)
        
        # Avoid repeating own messages
        if thread_type == ThreadType.GROUP and message.text:
            if thread_id not in self.message_record:
                self.message_record[thread_id] = [None, set()]
            group_record = self.message_record[thread_id]
            message_lower = message.text.lower()
            if group_record[0] != message_lower:
                group_record[0] = message_lower
                group_record[1].clear()
            group_record[1].add(self.uid)

    def match_user(self, group_id, query):
        group = self.fetchGroupInfo(group_id)[group_id]
        users = self.fetchUserInfo(*group.participants)
        query = query.strip().lower()
        user = user_from_alias(query)
        if user and user['_id'] in users.keys():
            return users[user['_id']]
        for user_id, user in users.items():
            if query == user.name.lower():
                return user
        query = query.split(' ', 1)[0]
        for user_id, user in users.items():
            if query in user.name.lower().split():
                return user
        for user_id, user in users.items():
            if user.name.lower().startswith(query):
                return user
        return None

    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=None, thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):
        if author_id == self.uid:
            return

        lock.acquire()
        try:

            # Check for chat commands
            if message_object.text and message_object.text[0] == '!':
                command, text, *_ = message_object.text.split(' ', 1) + ['']
                command = command[1:].lower()
                text = text.strip()
            else:
                command, text = None, (message_object.text or '')

            # Check for mentions
            mentions = []
            for mention in message_object.mentions:
                mentions.append(mention.thread_id)

            if thread_type == ThreadType.USER:

                # Handle battle messages
                state, details = self.user_states.get(author_id, (UserState.Idle, {}))
                if state == UserState.Battle:
                    author = user_from_id(author_id)
                    if command == 'flee' or command == 'f':
                        cancel_battle(self, author)
                    elif details['Status'] == ChatState.Preparing:
                        if command == 'ready' or command == 'r':
                            begin_battle(self, author)
                    elif details['Status'] == ChatState.Quest:
                        complete_battle_quest(self, author, text)
                    return

                # Handle duel messages
                elif state == UserState.Duel:
                    author = user_from_id(author_id)
                    if command == 'flee' or command == 'f':
                        cancel_duel(self, author)
                    elif details['Status'] == ChatState.Preparing:
                        if command == 'ready' or command == 'r':
                            begin_duel(self, author)
                    elif details['Status'] == ChatState.Quest:
                        complete_duel_quest(self, author, text)
                    return

                # Forward direct messages
                if thread_id != master_id:
                    user = self.fetchUserInfo(thread_id)[thread_id]
                    message_object.text = '<' + user.name + '>: ' + (message_object.text or '')
                    self.send(message_object, thread_id=master_id)

                # Chat commands - User
                run_user_command(self, user_from_id(author_id), command, text)

            elif thread_type == ThreadType.GROUP:

                # Track last messages
                if command:
                    self.message_record[thread_id] = [None, set()]
                else:
                    if thread_id not in self.message_record:
                        self.message_record[thread_id] = [None, set()]
                    group_record = self.message_record[thread_id]
                    text_lower = (message_object.text or '').lower()
                    if text_lower != group_record[0]:
                        group_record[0] = text_lower
                        group_record[1].clear()
                    group_record[1].add(author_id)
                    if len(group_record[1]) >= 3 and self.uid not in group_record[1]:
                        message = Message(message_object.text)
                        self.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)

                # Check for active quest
                if author_id in self.quest_record:
                    complete_quest(self, user_from_id(author_id), text, thread_id)

                # Cleverbot messaging
                if not command:
                    text = text.split()
                    if text and text[0].lower() == 'wong,':
                        try:
                            if author_id == master_id and self.responses:
                                reply = self.responses.pop(0)
                            elif priority_get(author_id) == 0:
                                reply = 'Sorry, I don\'t respond to peasants.'
                            else:
                                reply = cb.say(' '.join(text[1:]))
                        except cleverbot.CleverbotError as error:
                            print(error)
                        else:
                            self.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
                    return

                # Check for defined override
                if command in self.defines:
                    if self.defines[command][0] == '!':
                        command, text, *_ = self.defines[command].split(' ', 1) + ['']
                        command = command[1:].lower()
                        text = text.strip()
                    else:
                        message = Message(self.defines[command])
                        self.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
                        return

                # Chat commands - Group
                run_group_command(self, user_from_id(author_id), command, text, thread_id)

        except:
            self.send(Message('Main: ' + traceback.format_exc()), thread_id=master_id)
        finally:
            lock.release()

    def onPersonRemoved(self, mid=None, removed_id=None, author_id=None, thread_id=None, ts=None, msg=None):
        if exceeds_priority(removed_id, author_id):
            self.removeUserFromGroup(author_id, thread_id)
            self.addUsersToGroup([removed_id], thread_id)


app = Flask(__name__)


@app.route('/')
def index():
    return 'Welcome!'


client = ChatBot('jonathanchen1025@gmail.com', b64decode(os.environ.get('PASSWORD')))


class ServerThread(threading.Thread):

    def run(self):
        if os.environ.get('ON_HEROKU'):
            port = int(os.environ.get('PORT', 5000))
            app.run(host='0.0.0.0', port=port)


class ReactiveThread(threading.Thread):

    def run(self):
        client.listen()


class ActiveThread(threading.Thread):

    def run(self):
        client.startListening()
        while True:
            time.sleep(0.001)
            lock.acquire()
            try:
                loop(client)
            except:
                client.send(Message('Polling: ' + traceback.format_exc()), thread_id=master_id)
            finally:
                lock.release()


ServerThread().start()
ReactiveThread().start()
ActiveThread().start()