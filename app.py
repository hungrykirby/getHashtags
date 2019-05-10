# -*- coding:utf-8 -*-

import twit_utils

search_word = input('>>>Hashtag>>> ')
search_word = str(search_word)

tw = twit_utils.Twitter(search_word)

if __name__ == "__main__":
    tw.fetchhashtagTweets()
    tw.streaming()
