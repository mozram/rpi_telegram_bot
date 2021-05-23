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
$ python3.5 quiz.py <token>

Send a chat message to the bot. It will give you a math quiz. Stay silent for
10 seconds to end the quiz.

It handles callback query by their origins. All callback query originated from
the same chat message will be handled by the same `CallbackQueryOriginHandler`.
"""

class QuizStarter(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(QuizStarter, self).__init__(*args, **kwargs)

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        self.sender.sendMessage(
            'What do you want to know?',
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text='Temperature', callback_data='get_temp'),
                    InlineKeyboardButton(text='Throttled', callback_data='get_throttled'),
                    InlineKeyboardButton(text='RAM Usage', callback_data='get_ram_usage'),
                ]]
            )
        )
        self.close()  # let Quizzer take over

class Quizzer(telepot.helper.CallbackQueryOriginHandler):
    def __init__(self, *args, **kwargs):
        super(Quizzer, self).__init__(*args, **kwargs)
        self._score = {True: 0, False: 0}
        self._answer = None

    def _show_next_question(self, input):
        self.editor.editMessageText(
            input + '\n What do you want to know?',
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text='Temperature', callback_data='get_temp'),
                    InlineKeyboardButton(text='Throttled', callback_data='get_throttled'),
                    InlineKeyboardButton(text='RAM Usage', callback_data='get_ram_usage'),
                ]]
            )
        )
        return

    def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')

        # if query_data != 'get_temp':
        #     self._score[self._answer == int(query_data)] += 1

        if query_data == 'get_temp':
            out = subprocess.run(["vcgencmd",'measure_temp'], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif query_data == 'get_throttled':
            out = subprocess.run(["vcgencmd",'get_throttled'], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif query_data == 'get_ram_usage':
            out = subprocess.run(["free",'-m'], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._show_next_question(out.stdout)

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
        per_chat_id(), create_open, QuizStarter, timeout=3),
    pave_event_space()(
        per_callback_query_origin(), create_open, Quizzer, timeout=10),
])

MessageLoop(bot).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)