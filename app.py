# -*- coding:utf-8 -*-

import twit_utils

tw = twit_utils.Twitter('キリチャレの日')

if __name__ == "__main__":
    tw.fetchhashtagTweets()
    tw.streaming()
