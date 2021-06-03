import sys
import subprocess
import time
import random
import telepot
import telepot.helper
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.delegate import (
    per_chat_id, per_callback_query_origin, create_open, pave_event_space)

"""
$ python3.5 main.py <token>

Send a chat message to the bot. It will give you a math quiz. Stay silent for
10 seconds to end the quiz.

It handles callback query by their origins. All callback query originated from
the same chat message will be handled by the same `CallbackQueryOriginHandler`.
"""
keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text='Temperature', callback_data='get_temp'),
                    InlineKeyboardButton(text='Throttled', callback_data='get_throttled'),
                    InlineKeyboardButton(text='RAM Usage', callback_data='get_ram_usage'),
                ]])

user_id = ""

version = "0.2"

class RequestStarter(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(RequestStarter, self).__init__(*args, **kwargs)

    def on_chat_message(self, msg):
        global keyboard
        global user_id
        content_type, chat_type, chat_id = telepot.glance(msg)

        if msg['text'] == '/start':
            user_id = chat_id
            self.sender.sendMessage(
                'What do you want to know?',
                reply_markup = keyboard
            )
        self.close()  # let Requestor take over

class Requestor(telepot.helper.CallbackQueryOriginHandler):
    def __init__(self, *args, **kwargs):
        super(Requestor, self).__init__(*args, **kwargs)
        self._score = {True: 0, False: 0}
        self._answer = None

    def _show_next_question(self, input):
        global keyboard
        self.editor.editMessageText(
            input + '\nWhat do you want to know?',
            reply_markup = keyboard
        )
        return

    def on_callback_query(self, msg):
        global temperature
        global throttled
        global free

        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')

        # if query_data != 'get_temp':
        #     self._score[self._answer == int(query_data)] += 1
        response = ""

        if query_data == 'get_temp':
            response = temperature
        elif query_data == 'get_throttled':
            response = throttled
        elif query_data == 'get_ram_usage':
            free_out = subprocess.run(["free",'-m'], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            response = free_out.stdout
        self._show_next_question(response)

    def on__idle(self, event):
        text = '%d out of %d' % (self._score[True], self._score[True]+self._score[False])
        self.editor.editMessageText(
            text + '\n\nThis message will disappear in 5 seconds...',
            reply_markup=None)

        time.sleep(5)
        self.editor.deleteMessage()
        self.close()

TOKEN = sys.argv[1]

bot = telepot.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(), create_open, RequestStarter, timeout=3),
    pave_event_space()(
        per_callback_query_origin(), create_open, Requestor, timeout=10),
])

def sendNotification(msg):
    global user_id

    if user_id != "":
        bot.sendMessage(user_id, msg)

MessageLoop(bot).run_as_thread()
print('Telegram Bot v' + version)
print('Listening ...')

while 1:
    global temperature
    global throttled

    measure_temp_out = subprocess.run(["vcgencmd",'measure_temp'], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    get_throttled_out = subprocess.run(["vcgencmd",'get_throttled'], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    temperature = measure_temp_out.stdout
    throttled = get_throttled_out.stdout

    temperature_filtered = int ( ''.join(filter(str.isdigit, temperature) ) )
    throttled_filtered = int ( ''.join(filter(str.isdigit, throttled) ) )

    if temperature_filtered > 650:
        sendNotification("Warning! " + temperature)
    if throttled_filtered > 0:
        sendNotification("Warning! " + throttled)

    time.sleep(5)
    
