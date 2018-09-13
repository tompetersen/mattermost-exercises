"""
A small bot for movement via mattermost.

Uses: https://github.com/Vaelor/python-mattermost-driver
"""

import asyncio
import itertools
import json
import re
import threading
from mattermostdriver import Driver


class SubscriptionBot:
    """ A mattermost bot implementing a publish/subscribe mechanism. """

    SUBSCRIBED_MESSAGE = "Hi there - thx for joining!"
    UNSUBSCRIBED_MESSAGE = "Bye then, couch potato!"
    NOT_SUBSCRIBED_MESSAGE = "Are you also trying to cancel your gym membership before even registering?"
    UNKNOWN_COMMAND_TEXT = "I don't get it, want to join? Try 'subscribe' instead. 'help' may also be your friend."
    HELP_TEXT = """
|Command|Description|
|:------|:----------|
|subscribe|Join the growing list of subscribers now!|
|unsubscribe|Go back to your boring office-chair-only life.|
|help|I'm quite sure, you know what this one does.|        
"""

    def __init__(self, username, password, scheme='https', debug=False):
        self.subscriptions = set()

        self.username = username
        self.debug = debug

        self.driver = Driver({
            'url': "192.168.122.254",
            'login_id': username,
            'password': password,
            'scheme': scheme,
            'debug': debug,
        })
        self.driver.login()

        # get userid for username since it is not automatically set to driver.client.userid ... for reasons
        res = self.driver.users.get_user_by_username('bot')
        self.userid = res['id']

    def start_listening(self):
        worker = threading.Thread(target=SubscriptionBot._start_listening_in_thread, args=(self,))
        worker.daemon = True
        worker.start()

        print("Initialized bot.")

    def _start_listening_in_thread(self):
        # Setting event loop for thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self.driver.init_websocket(self.websocket_handler)

    @asyncio.coroutine
    def websocket_handler(self, event_json):
        event = json.loads(event_json)

        if self.debug:
            print("websocket_handler:" + json.dumps(event, indent=4))

        if 'event' in event and event['event'] == 'posted':
            # mentions is automatically set in direct messages
            mentions = json.loads(event['data']['mentions']) if 'mentions' in event['data'] else []

            post = json.loads(event['data']['post'])
            post_id = post['id']
            message = post['message']
            channel_id = post['channel_id']
            sender_id = post['user_id']

            if self.userid in mentions:
                self.handle_bot_message(channel_id, post_id, sender_id, message)

    def handle_bot_message(self, channel_id, post_id, sender_id, message):
        if re.match(r'(@' + self.username + ')?\s*help\s*', message):
            self._show_help(channel_id, post_id)
        elif re.match(r'(@' + self.username + ')?\s*subscribe\s*', message):
            self._handle_subscription(sender_id, channel_id, post_id)
        elif re.match(r'(@' + self.username + ')?\s*unsubscribe\s*', message):
            self._handle_unsubscription(channel_id, post_id, sender_id)
        else:
            self._handle_unknown_command(channel_id, post_id)

    def _show_help(self, channel_id, post_id):
        self.driver.posts.create_post({
            'channel_id': channel_id,
            'message': self.HELP_TEXT,
            'root_id': post_id,
        })

    def _handle_subscription(self, sender_id, channel_id, post_id):
        self.subscriptions.add(sender_id)
        if self.debug:
            print(sender_id + " subscribed.")

        self.driver.posts.create_post({
            'channel_id': channel_id,
            'message': self.SUBSCRIBED_MESSAGE,
            'root_id': post_id,
        })

    def _handle_unsubscription(self, channel_id, post_id, sender_id):
        if sender_id in self.subscriptions:
            self.subscriptions.discard(sender_id)
            if self.debug:
                print(sender_id + " unsubscribed.")

            self.driver.posts.create_post({
                'channel_id': channel_id,
                'message': self.UNSUBSCRIBED_MESSAGE,
                'root_id': post_id,
            })
        else:
            self.driver.posts.create_post({
                'channel_id': channel_id,
                'message': self.UNSUBSCRIBED_MESSAGE,
                'root_id': post_id,
            })

    def _handle_unknown_command(self, channel_id, post_id):
        self.driver.posts.create_post({
            'channel_id': channel_id,
            'message': self.UNKNOWN_COMMAND_TEXT,
            'root_id': post_id,
        })

    def send_messages_to_subscribers(self, message):
        for subscriber in self.subscriptions:
            self._send_direct_message(subscriber, message)

    def _send_direct_message(self, user_id, message, root_id=None):
        res = self.driver.channels.create_direct_message_channel([self.userid, user_id])
        channel_id = res['id']

        post_options = {
            'channel_id': channel_id,
            'message': message,
        }
        if root_id:
            post_options['root_id'] = root_id

        self.driver.posts.create_post(post_options)
