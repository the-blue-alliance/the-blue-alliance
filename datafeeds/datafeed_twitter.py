import logging
import json
import oauth2

from datafeeds.datafeed_base import DatafeedBase
from datafeeds.twitter_matches_parser import TwitterMatchesParser
import tba_config

from models.sitevar import Sitevar


class DatafeedTwitter(DatafeedBase):
    def __init__(self, *args, **kw):
        super(DatafeedTwitter, self).__init__(*args, **kw)

    def getMatches(self):
        """
        Doesn't actually return Match objects. Instead, returns dict where
        the key is the event_short and the value is a list of strings
        in the following CSV format:
        match_id, red1, red2, red3, blue1, blue2, blue3, red score, blue score

        """
        toReturn = {}

        max_id = None

        tweets = self.getSomeTweets(max_id)
        while tweets:
            for tweet in tweets:
                event_key, match = TwitterMatchesParser.parse(tweet['text'])
                if event_key in toReturn:
                    toReturn[event_key].append(match)
                else:
                    toReturn[event_key] = [match]
                max_id = tweet['id'] - 1
            tweets = self.getSomeTweets(max_id)
        return toReturn

    def getSomeTweets(self, max_id=None):
        URL = 'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=frcfms&count=200'
        if max_id:
            return json.loads(self.oauth_req(URL + '&max_id=' + str(max_id)))
        else:
            return json.loads(self.oauth_req(URL))

    def oauth_req(self,
                  url,
                  http_method="GET",
                  post_body=None,
                  http_headers=None):

        twitter_secrets = Sitevar.get_by_id("twitter.secrets")
        if not twitter_secrets:
            raise Exception(
                "Missing sitevar: twitter.secrets. Cant scrape twitter.")

        TWITTER_CONSUMER_KEY = twitter_secrets.contents['TWITTER_CONSUMER_KEY']
        TWITTER_CONSUMER_SECRET = twitter_secrets.contents[
            'TWITTER_CONSUMER_SECRET']
        TWITTER_ACCESS_TOKEN = twitter_secrets.contents['TWITTER_ACCESS_TOKEN']
        TWITTER_ACCESS_TOKEN_SECRET = twitter_secrets.contents[
            'TWITTER_ACCESS_TOKEN_SECRET']

        consumer = oauth2.Consumer(
            key=TWITTER_CONSUMER_KEY, secret=TWITTER_CONSUMER_SECRET)
        token = oauth2.Token(
            key=TWITTER_ACCESS_TOKEN, secret=TWITTER_ACCESS_TOKEN_SECRET)
        client = oauth2.Client(consumer, token)

        resp, content = client.request(
            url,
            method=http_method,
            body=post_body,
            headers=http_headers,
            force_auth_header=True)
        return content
