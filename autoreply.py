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

json_file = './reply.json'
config_file = './settings/config.ini'
config = configparser.ConfigParser()
config.read(config_file, 'UTF-8')
update_id = None
CYCLE_SPAN = 630000
CP_SPAN = 18000


def main():
    """Run the bot."""
    global update_id
    # Telegram Bot Authorization Token
    api_token = str(config.get('login', 'api_key'))
    bot = telegram.Bot(api_token)

    # 現在のupdate_idを取得
    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None

    # JSONファイルから設定を取得。取得できなかったら終了。
    try:
        replyLists = jsonReader()
    except FileNotFoundError as e:
        print(e)
        return False
    except json.JSONDecodeError as e:
        print(e)
        return False

    while True:
        try:
            autoreply(bot, replyLists)
        except NetworkError:
            sleep(1)
        except Unauthorized:
            # BOTをリムーブ、ブロックされた場合はupdate_idを+1
            update_id += 1


def jsonReader():
    """Read json file for autoreply"""
    replyLoad = open(json_file)
    replyLists = json.load(replyLoad)
    return replyLists


def autoreply(bot, replyLists):
    """autoreply the message the user sent."""
    global update_id
    # 前回更新以降の更新がないかを確認
    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1

        if update.message:  # メッセージ更新時に発火
            for reply_ptn in replyLists['autoreplies']:
                for reply_trgs in reply_ptn[0]:
                    matched = False
                    rcv_text = str(update.message.text)
                    if re.match('regex:', reply_trgs) is not None:
                        fix_reply_trg = reply_trgs.replace('regex:', '')
                        if re.match(fix_reply_trg, rcv_text) is not None:
                            matched = True
                    elif(rcv_text == reply_trgs):
                        matched = True

                    if(matched is True):
                        reply_len = len(reply_ptn[1])
                        random.seed
                        if reply_len != 1:
                            reply_point = random.randrange(reply_len)
                        else:
                            reply_point = 0
                        reply_text = reply_ptn[1][reply_point]
                        # リプライに"/がついていたら機能判定実施
                        if re.match('/', reply_text) is not None:
                            reply_text = checkReply(reply_text, rcv_text)
                        # Reply to the message
                        update.message.reply_text(reply_text)


def checkReply(reply_text, rcv_text):
    # 判定を実施し、機能呼び出し
    if re.match('/cp', reply_text) is not None:
        return_text = countCycle(rcv_text)
    else:
        return_text = reply_text
    return(return_text)


def countCycle(rcv_text):
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
    cycle_start = (ret_time // CYCLE_SPAN) * CYCLE_SPAN
    cycle_no = (ret_time // CYCLE_SPAN) - 2205

    # CP計算。現在のCPを算出。
    now_cp = (ret_time - ((ret_time // CYCLE_SPAN) * CYCLE_SPAN)) // CP_SPAN

    return_text += "{0:%m/%d %H:%M}".format(local_time) + '\n'
    return_text += "CYCLE" + str(cycle_no) + '\n'

    for cycle in range(1, CP_NUMBER + 1, 1):
        cp_count = now_cp + cycle
        cp_start = cycle_start + cp_count * CP_SPAN
        cp_start_time = datetime.fromtimestamp(cp_start, JST)
        cp_start_format = "{0:%m/%d %H:%M}".format(cp_start_time)
        if (cp_count > 35):
            cp_count -= 35
        return_text += "CP" + str(cp_count) + ' ' + cp_start_format + '\n'

    return(return_text)


if __name__ == '__main__':
    main()
