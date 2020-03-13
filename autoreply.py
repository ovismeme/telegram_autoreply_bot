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
        self.CYCLE_SPAN = str(config.get('Ingress', 'CYCLE_SPAN'))
        self.CP_SPAN = str(config.get('Ingress', 'CP_SPAN'))
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
            if not update.message:
                continue
            for reply_ptn in self.replyLists['autoreplies']:
                for reply_trg in reply_ptn[0]:
                    rcv_text = str(update.message.text)
                    if (re.match('regex:', reply_trg) is None or re.match(reply_trg.replace('regex:', ''), rcv_text) is None) and rcv_text != reply_trg:
                        continue
                    reply_text = reply_ptn[1][random.randrange(len(reply_ptn[1]))]
                    # リプライに"/がついていたら機能判定実施
                    if re.match('/', reply_text) is not None:
                        reply_text = self.checkReply(reply_text, rcv_text)
                    # Reply to the message
                    update.message.reply_text(reply_text)

    def checkReply(self, reply_text, rcv_text):
        # 判定を実施し、機能呼び出し
        if re.match('/cp', reply_text) is not None:
            return_text = self.countCycle(rcv_text)
        elif re.match('/reload', reply_text) is not None:
            try:
                self.jsonReader()
                return_text = 'Reload reply-setting...OK!'
            except json.JSONDecodeError:
                return_text = 'JSON Error in ' + str(self.REPLY_SETTINGS)
        else:
            return_text = reply_text
        return(return_text)

    def countCycle(self, rcv_text):
        """
        Ingressのサイクルを返却

        入力：ユーザー発話
        返却：サイクル時間

        ユーザー指定がないか不正の場合は現在日
        ユーザー指定はmm/ddに対応した日付でサイクルを送信する。

        """
        # 返却数を定数定義
        CP_NUMBER = 6
        return_text = ""
        JST = timezone(timedelta(hours=+9), 'JST')
        # 現在時間を取得し、サイクルに書き換える
        now = round(time())
        timematch = re.search(r"^.*\s(\d+)\/(\d+).*$", rcv_text)
        if timematch and timematch.group(1) and timematch.group(2):
            now_year = int("{0:%y}".format(datetime.fromtimestamp(now)))
            now_month = int("{0:%y}".format(datetime.fromtimestamp(now)))
            # 現在月以前の値が来た場合翌年対応
            try:
                if (now_month < int(timematch.group(1))):
                    now_year += 1
            except:
                # エラーはスルー
                now_year = now_year

            select_date = str(now_year) + ' '
            select_date += str(timematch.group(1)) + ' ' + str(timematch.group(2))
            select_date += ' 00:00 JST'
            try:
                ret_time = datetime.strptime(select_date, '%y %m %d %H:%M %Z')
                ret_time = round(ret_time.timestamp())
            except:
                # 異常時には現在時刻でとるようにして、入力例外に対応
                ret_time = now
        else:
            ret_time = now

        local_time = datetime.fromtimestamp(ret_time, JST)
        cycle_start = (ret_time // self.CYCLE_SPAN) * self.CYCLE_SPAN
        cycle_no = (ret_time // self.CYCLE_SPAN) - 2205

        # CP計算。現在のCPを算出。
        now_cp = (ret_time - ((ret_time // self.CYCLE_SPAN) * self.CYCLE_SPAN)) // self.CP_SPAN

        return_text += "{0:%m/%d %H:%M}".format(local_time) + '\n'
        return_text += "CYCLE" + str(cycle_no) + '\n'

        for cycle in range(1, CP_NUMBER + 1, 1):
            cp_count = now_cp + cycle
            cp_start = cycle_start + cp_count * self.CP_SPAN
            cp_start_time = datetime.fromtimestamp(cp_start, JST)
            cp_start_format = "{0:%m/%d %H:%M}".format(cp_start_time)
            if (cp_count > 35):
                cp_count -= 35
            return_text += "CP" + str(cp_count) + ' ' + cp_start_format + '\n'

        return(return_text)


if __name__ == '__main__':
    bot = TelegramBot()
    bot.main()
