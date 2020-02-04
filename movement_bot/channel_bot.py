import asyncio
import json
import re
import threading
from mattermostdriver import Driver


class ChannelBot:
    """ A mattermost bot acting in a specified channel. """

    def __init__(self, url, token, channel_name, team_name, help_text, message_handler, port=8065, scheme='https', debug=False):
        self.help_text = help_text
        self.message_handler = message_handler
        self.debug = debug

        self.driver = Driver({
            'url': url,
            'port': port,
            'token': token,
            'scheme': scheme,
            'debug': debug,
        })
        user_result = self.driver.login()
        self.username = user_result["username"]
        self.userid = user_result["id"]

        # get channel id for name
        res = self.driver.channels.get_channel_by_name_and_team_name(team_name, channel_name)
        self.channel_id = res['id']

    def start_listening(self):
        worker = threading.Thread(target=ChannelBot._start_listening_in_thread, args=(self,))
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

            if self.userid in mentions: # and channel_id == self.channel_id:
                self._handle_bot_message(channel_id, post_id, sender_id, message)

    def _handle_bot_message(self, channel_id, post_id, sender_id, message):
        if re.match(r'(@' + self.username + ')?\s*help\s*', message):
            self._show_help(channel_id, post_id)
        else:
            res = self.driver.users.get_user(sender_id)
            sender_name = res['username']

            self.message_handler.handle_message(sender_id, sender_name, message, post_id, channel_id, self)

    def _show_help(self, channel_id, post_id):
        self.driver.posts.create_post({
            'channel_id': channel_id,
            'message': self.help_text,
            'root_id': post_id,
        })

    def send_message_to_channel(self, message):
        post_options = {
            'channel_id': self.channel_id,
            'message': message,
        }

        self.driver.posts.create_post(post_options)

    def answer_message_in_channel(self, channel_id, post_id, message):
        post_options = {
            'channel_id': channel_id,
            'root_id': post_id,
            'message': message,
        }

        self.driver.posts.create_post(post_options)