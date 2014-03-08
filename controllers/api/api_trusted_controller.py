import json
import webapp2

from helpers.match_manipulator import MatchManipulator

from models.match import Match
from models.sitevar import Sitevar


class ApiTrustedAddMatchYoutubeVideo(webapp2.RequestHandler):
    def post(self):
        trusted_api_secret = Sitevar.get_by_id("trusted_api.secret")
        if trusted_api_secret is None:
            raise Exception("Missing sitevar: trusted_api.secret. Can't accept YouTube Videos.")

        secret = self.request.get('secret', None)
        if secret is None:
            self.response.set_status(400)
            self.response.out.write(json.dumps({"400": "No secret given"}))
            return

        if str(trusted_api_secret.values_json) != str(secret):
            self.response.set_status(400)
            self.response.out.write(json.dumps({"400": "Incorrect secret"}))
            return

        match_key = self.request.get('match_key', None)
        if match_key is None:
            self.response.set_status(400)
            self.response.out.write(json.dumps({"400": "No match_key given"}))
            return

        youtube_id = self.request.get('youtube_id', None)
        if youtube_id is None:
            self.response.set_status(400)
            self.response.out.write(json.dumps({"400": "No youtube_id given"}))
            return

        match = Match.get_by_id(match_key)
        if match is None:
            self.response.set_status(400)
            self.response.out.write(json.dumps({"400": "Match {} does not exist!".format(match_key)}))
            return

        if youtube_id not in match.youtube_videos:
            match.youtube_videos.append(youtube_id)
            match.dirty = True  # This is so hacky. -fangeugene 2014-03-06
            MatchManipulator.createOrUpdate(match)
