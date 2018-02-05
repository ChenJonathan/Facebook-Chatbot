from fbchat import Client
from fbchat.models import *
from flask import Flask
from base64 import b64decode
from datetime import datetime
import cleverbot
import os
import random
import threading

from clock import set_timer
from commands import run_group_command, run_user_command
from emoji import random_emoji
from mongo import *
from quest import complete_quest
from util import master_id

cb = cleverbot.Cleverbot(os.environ.get('CLEVERBOT_KEY'))

class ChatBot(Client):

    def __init__(self, email, password):
        super().__init__(email, password)
        init_db(self)

        self.num_images = len(os.listdir('./images'))
        self.message_record = {}
        self.quest_record = {}
        self.travel_record = {}

        self.defines = {}
        self.responses = []

        set_timer()

    def send(self, message, thread_id, thread_type=ThreadType.USER):
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

    def matchUser(self, group_id, query):
        group = self.fetchGroupInfo(group_id)[group_id]
        users = self.fetchUserInfo(*group.participants)
        query = query.strip().lower()
        user = user_from_alias(query)
        if user and user['name'] in users.keys():
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

    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        if author_id == self.uid:
            return

        # Update travel status - Unrelated to messaging
        now = datetime.now()
        for user_id, record in list(self.travel_record.items()):
            if now > record[1]:
                location_set(user_id, record[0])
                del self.travel_record[user_id]

        # Check for chat commands
        if message_object.text[0] == '!':
            command, text, *_ = message_object.text.split(' ', 1) + ['']
            command = command[1:].lower()
            text = text.strip()
        else:
            command, text = None, message_object.text

        # Check for mentions
        mentions = []
        for mention in message_object.mentions:
            mentions.append(mention.thread_id)

        if thread_type == ThreadType.USER:

            # Forward direct messages
            if thread_id != master_id:
                user = self.fetchUserInfo(thread_id)[thread_id]
                message = Message('<' + user.name + '>: ' + message_object.text)
                self.send(message, thread_id=master_id)

            # Chat commands - User
            run_user_command(self, command, text, user_from_id(author_id))

        elif thread_type == ThreadType.GROUP:

            # Track last messages
            if command:
                self.message_record[thread_id] = [None, set()]
            else:
                if thread_id not in self.message_record:
                    self.message_record[thread_id] = [None, set()]
                group_record = self.message_record[thread_id]
                text_lower = message_object.text.lower()
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
                if text[0].lower() == 'wong,':
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
            run_group_command(self, command, text, user_from_id(author_id), thread_id)

    def onPersonRemoved(self, removed_id, author_id, thread_id, **kwargs):
        if exceeds_priority(removed_id, author_id):
            self.removeUserFromGroup(author_id, thread_id)
            self.addUsersToGroup([removed_id], thread_id)


app = Flask(__name__)

@app.route('/')
def index():
    return 'Welcome!'

class ServerThread(threading.Thread):

    def run(self):
        if os.environ.get('ON_HEROKU'):
            port = int(os.environ.get('PORT', 5000))
            app.run(host='0.0.0.0', port=port)

class ChatThread(threading.Thread):

    def run(self):
        client = ChatBot('Avenlokh@gmail.com', b64decode(os.environ.get('PASSWORD')))
        client.listen()


ChatThread().start()
ServerThread().start()