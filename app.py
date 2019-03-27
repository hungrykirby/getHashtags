# -*- coding:utf-8 -*-

import twit_utils

tw = twit_utils.Twitter('#ケムリクサ')

if __name__ == "__main__":
    tw.fetchhashtagTweets()
    tw.streaming()
