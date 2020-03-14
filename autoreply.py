#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
edit echobot to autoreplybot
20190102 made by ovismeme
"""
import telegram
from telegram.error import NetworkError, Unauthorized
from time import time, sleep
from datetime import datetime, timezone, timedelta
import json
import re
import random
import configparser


class TelegramBot:
    def __init__(self):
        self.REPLY_SETTINGS = './reply.json'
        config_file = './settings/config.ini'
        config = configparser.ConfigParser()
        config.read(config_file, 'utf-8')
        self.TELEGRAM_TOKEN = str(config.get('login', 'api_key'))
        self.bot = telegram.Bot(self.TELEGRAM_TOKEN)
        try:
            self.update_id = self.bot.get_updates()[0].update_id
        except IndexError:
            self.update_id = None
        try:
            self.replyLists = self.jsonReader()
        except json.JSONDecodeError as e:
            raise('JSONファイルが不正です。')
        except Exception  as e:
            raise(e)

    def jsonReader(self):
        """Read json file for autoreply"""
        replyLoad = open(self.REPLY_SETTINGS,encoding="utf-8")
        replyLists = json.load(replyLoad)
        return replyLists

    def main(self):
        """Run the bot."""
        while True:
            try:
                self.autoreply()
            except NetworkError:
                sleep(1)
            except Unauthorized:
                # BOTをリムーブ、ブロックされた場合はupdate_idを+1
                self.update_id += 1

    def autoreply(self):
        """autoreply the message the user sent."""
        # 前回更新以降の更新がないかを確認
        for update in self.bot.get_updates(offset=self.update_id, timeout=10):
            self.update_id = update.update_id + 1
            rcv_text = str(update.message.text)
            self.rcv_user = str(update.effective_user['first_name'])
            if not update.message:
                continue
            for reply_ptn in self.replyLists['autoreplies']:
                for reply_trg in reply_ptn[0]:
                    if (re.match('regex:', reply_trg) is None or re.match(reply_trg.replace('regex:', ''), rcv_text) is None) and rcv_text != reply_trg:
                        continue
                    reply_text = reply_ptn[1][random.randrange(len(reply_ptn[1]))]
                    reply_text = reply_text.replace('{event.user.full_name}', self.rcv_user)
                    # リプライに"/がついていたら機能判定実施
                    if re.match('/', reply_text) is not None:
                        reply_text = self.checkReply(reply_text, rcv_text)
                    # Reply to the message
                    update.message.reply_text(reply_text)

    def checkReply(self, reply_text, rcv_text):
        # 判定を実施し、機能呼び出し
        if reply_text == '/reload':
            try:
                self.jsonReader()
                return_text = 'Reload reply-setting...OK!'
            except json.JSONDecodeError:
                return_text = 'JSON Error in ' + str(self.REPLY_SETTINGS)
        elif reply_text == '/whoami':
            return_text = self.rcv_user
        else:
            return_text = reply_text
        return(return_text)

if __name__ == '__main__':
    bot = TelegramBot()
    bot.main()
