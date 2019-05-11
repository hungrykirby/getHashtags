# -*- coding:utf-8 -*-

import json
from requests_oauthlib import OAuth1Session
import os
import re
from os.path import join, dirname
from dotenv import load_dotenv
import emoji
import requests

import argparse

from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc.parsing import osc_types

import sys
import calendar
import time

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

class OSC:
    port = None
    parser = None
    client = None

    def __init__(self, port):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--ip", default="127.0.0.1", help="The ip of th OSC Server")
        self.parser.add_argument("--port", type=int, default=port, help="The port the OSC server is listening on")
        args = self.parser.parse_args()
        self.client = udp_client.UDPClient(args.ip, args.port)

        print("ip:127.0.0.1, port:" + str(port) + ", address:/text")

    def sendInitMessage(self):
        try:
            msg = osc_message_builder.OscMessageBuilder(address="/text")
            msg.add_arg('タイムラインが流れます')
            msg = msg.build()

            msg2 = osc_message_builder.OscMessageBuilder(address="/created_at")
            msg2.add_arg('Today')
            msg2 = msg2.build()

            self.client.send(msg)
            self.client.send(msg2)
        except:
            print('ParserError')

    def sendMessage(self, text='', created_at=''):
        try:
            msg = osc_message_builder.OscMessageBuilder(address="/text")
            msg.add_arg(text)
            msg = msg.build()

            msg2 = osc_message_builder.OscMessageBuilder(address="/created_at")
            msg2.add_arg(created_at)
            msg2 = msg2.build()

            self.client.send(msg)
            self.client.send(msg2)
        except:
            print('ParserError')

class Twitter:
    twitter = None
    hashtag = None
    osc_sender = None

    def __init__(self, hashtag):
        CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
        CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
        ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
        ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET")
        self.twitter = OAuth1Session(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        self.hashtag = hashtag
        self.osc_sender = OSC(8002)
        self.osc_sender.sendInitMessage()

    def fetchhashtagTweets(self):
        url = "https://api.twitter.com/1.1/search/tweets.json"
        params = {'count' : 15, 'q' : self.hashtag}
        req = self.twitter.get(url, params = params)
        if req.status_code == 200:
            timeline = json.loads(req.text)
            for tweet in timeline['statuses']:
                if not 'retweeted_status' in tweet:
                    print(tweet['user']['name']+'::'+self.__shape_tweet(tweet['text']))
                    print(tweet['created_at'])
                    print('----------------------------------------------------')
                    self.osc_sender.sendMessage(text=self.__shape_tweet(tweet['text']), created_at=self.__shape_created_at(tweet['created_at']))
        else:
            print("ERROR: %d" % req.status_code)

    def get_screen_name(self):
        pass

    def streaming(self):
        url = "https://stream.twitter.com/1.1/statuses/filter.json"
        params = {"track": self.hashtag}
        RLT = 180
        while(True):
            try:
                req = self.twitter.post(url, stream=True, params=params)
                if req.status_code == 200:
                    if req.encoding is None:
                        req.encoding = "utf-8"
                    for js in req.iter_lines(chunk_size=1,decode_unicode=True):
                        try:
                            if js :
                                tweet = json.loads(js)
                                if 'text' in tweet and not 'retweeted_status' in tweet:
                                    user_name = (tweet["user"]["name"])
                                    user_id = tweet["user"]["id_str"]
                                    screen_name = (tweet["user"]["screen_name"])
                                    text = (tweet["text"])
                                    tweet_id = tweet["id_str"]
                                    created_at = tweet["created_at"]
                                    print ('----\n'+user_name+"(@"+screen_name+"):"+'\n'+self.__shape_tweet(text))

                                    self.osc_sender.sendMessage(text=self.__shape_tweet(text), created_at=self.__shape_created_at(created_at))

                                    continue
                                else:
                                    continue
                        except UnicodeEncodeError:
                            print('UnicodeEncodeError')
                elif req.status_code == 420:
                    print('Rate Limit: Reload after', RLT, 'Sec.')
                    time.sleep(RLT)

                else:
                    print("HTTP ERRORE: %d" % req.status_code)
                    break
            except KeyboardInterrupt:
                print("End")
                break

            except:
                print("except Error:", sys.exc_info())
                pass

    def __shape_created_at(self, created_at):
        time_utc = time.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
        unix_time = calendar.timegm(time_utc)
        time_local = time.localtime(unix_time)
        japan_time = time.strftime("%Y-%m-%d %H:%M:%S", time_local)

        return japan_time

    def __shape_tweet(self, tweet):
        shaped_tweet = tweet

        #URLを除去
        s = re.sub(r"\n*(\s*https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+\$,%#]+)\n*", "" ,shaped_tweet)

        #ハッシュタグを除去
        s = re.sub(r"\n*#(\w+)\n*", "", s)

        #リプライを除去
        s = re.sub(r"\n*(\s*@\S+\s*)\n*", "", s)

        #「診断して」を除去
        #s = re.sub(r"診断して", "", s)

        #タブ、インデント、改行を除去
        #s = re.sub(r"\s+", " ", s)

        #数字、英語を除去
        #s = re.sub(r"[a-zA-Z0-9]+", "", s)

        #全角数字を除去
        #s = re.sub(r"[０-９]+", "", s)

        #…を除く
        s = re.sub(r"…", "", s)
        s = re.sub(r"\.", "", s)

        #文頭、文末の改行を排除する
        s = re.sub("^(\n+)", "", s)
        s = re.sub("(\n+)$", "", s) #文末の改行群が削除されないので直したい。

        s = self.__remove_emoji(s)

        if(s == ''):
            s = ''

        return s


    def __remove_emoji(self, src_str):
        return ''.join(c for c in src_str if c not in emoji.UNICODE_EMOJI)
