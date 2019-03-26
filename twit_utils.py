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
        msg = osc_message_builder.OscMessageBuilder(address="/text")
        msg.add_arg('ping')
        msg = msg.build()
        self.client.send(msg)

    def sendMessage(self, text):
        msg = osc_message_builder.OscMessageBuilder(address="/text")
        msg.add_arg(text)
        msg = msg.build()
        self.client.send(msg)

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
                print(tweet['user']['name']+'::'+self.__shape_tweet(tweet['text']))
                print(tweet['created_at'])
                print('----------------------------------------------------')

                self.osc_sender.sendMessage(self.__shape_tweet(tweet['text']))
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
                                if 'text' in tweet:
                                    user_name = (tweet["user"]["name"])
                                    user_id = tweet["user"]["id_str"]
                                    screen_name = (tweet["user"]["screen_name"])
                                    text = (tweet["text"])
                                    tweet_id = tweet["id_str"]
                                    print ('----\n'+user_name+"(@"+screen_name+"):"+'\n'+self.__shape_tweet(text))

                                    self.osc_sender.sendMessage(self.__shape_tweet(text))

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

    def __shape_tweet(self, tweet):
        shaped_tweet = tweet

        #URLを除去
        s = re.sub(r"(\s*https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+\$,%#]+)", "" ,shaped_tweet)

        #ハッシュタグを除去
        s = re.sub(r"#(\w+)", "", s)

        #リプライを除去
        s = re.sub(r"(\s*@\S+\s*)", "", s)

        #「診断して」を除去
        #s = re.sub(r"診断して", "", s)

        #タブ、インデント、改行を除去
        #s = re.sub(r"\s+", " ", s)

        #数字、英語を除去
        #s = re.sub(r"[a-zA-Z0-9]+", "", s)

        #全角数字を除去
        #s = re.sub(r"[０-９]+", "", s)

        s = self.__remove_emoji(s)

        if(s == ''):
            s = ''

        return s


    def __remove_emoji(self, src_str):
        return ''.join(c for c in src_str if c not in emoji.UNICODE_EMOJI)