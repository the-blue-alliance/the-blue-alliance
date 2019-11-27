import urllib

import cloudstorage
import csv
import datetime
import json
import logging
import os
import StringIO
import time

from google.appengine.api.app_identity import app_identity

import tba_config

from collections import defaultdict

from consts.media_type import MediaType

from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

try:  # Tests fail on import. 2017-11-13
    from google.cloud import bigquery
    from google.cloud.bigquery.job import WriteDisposition
except Exception:
    logging.error("bigquery import failed")

from helpers.award_manipulator import AwardManipulator
from helpers.event_manipulator import EventManipulator
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.match_manipulator import MatchManipulator

from models.award import Award
from models.event import Event
from models.event_details import EventDetails
from models.match import Match
from models.media import Media
from models.sitevar import Sitevar
from models.team import Team

from datafeeds.csv_alliance_selections_parser import CSVAllianceSelectionsParser
from datafeeds.csv_awards_parser import CSVAwardsParser
from datafeeds.offseason_matches_parser import OffseasonMatchesParser


class MainBackupsEnqueue(webapp.RequestHandler):
    """
    Handles kicking off backup jobs
    """
    def get(self):
        # Enqueue a datastore backup
        taskqueue.add(
            url='/backend-tasks/backup/datastore',
            queue_name='backups',
            method='GET')

        # After 15 minutes, kick off a bigquery sync
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d')
        taskqueue.add(
            url='/backend-tasks/bigquery/import/{}'.format(timestamp),
            queue_name='backups',
            countdown=15 * 60,
            method='GET')

        # After an hour, set this backup's files to COLDLINE storage, since we will rarely
        # be accessing them ever again
        taskqueue.add(
            url='/backend-tasks/backup/archive/{}'.format(timestamp),
            queue_name='backups',
            countdown=60 * 60,
            method='GET')


class BackupControllerBase(webapp.RequestHandler):
    backup_config_sitevar = None

    def get_backup_config(self):
        if self.backup_config_sitevar:
            return self.backup_config_sitevar
        else:
            self.backup_config_sitevar = Sitevar.get_by_id('backup_config')
        if not self.backup_config_sitevar:
            self.abort(400)
        return self.backup_config_sitevar

    def get_oauth_token(self, scope):
        # This uses the default service account for this application
        access_token, _ = app_identity.get_access_token(scope)
        return access_token

    def get_backup_entities(self):
        backup_config_sitevar = self.get_backup_config()
        return backup_config_sitevar.contents.get('datastore_backup_entities', [])

    def get_backup_bucket(self):
        backup_config_sitevar = self.get_backup_config()
        return backup_config_sitevar.contents.get(
            'datastore_backup_bucket',
            'tba-prod-rawbackups'
        )

    def get_bigquery_dataset(self):
        backup_config_sitevar = self.get_backup_config()
        return backup_config_sitevar.contents.get('bigquery_dataset', '')

    def check_backup_exists(self, backup_bucket, file_name):
        try:
            cloudstorage.stat("/{}/{}".format(backup_bucket, file_name))
        except Exception, e:
            logging.info("Unable to find backup {} in GCS bucket {} - {}".format(
                file_name,
                backup_bucket,
                e.message))
            self.abort(400, "Unable to check backup exists")

    def fetch_url(self, url, payload=None, method=urlfetch.GET, deadline=60, headers=None):
        try:
            logging.info("Fetching {}, payload={}, headers={}".format(url, payload, headers))
            result = urlfetch.fetch(
                url=url,
                payload=payload,
                method=method,
                deadline=deadline,
                headers=headers)
            if result.status_code == 200:
                logging.info(result.content)
            elif result.status_code >= 500:
                logging.error(result.content)
            else:
                logging.warning(result.content)
            return result.status_code, result.content
        except urlfetch.Error, e:
            logging.exception('URL fetch failed: {}'.format(e.message))
            self.abort(500)


class DatastoreBackupFull(BackupControllerBase):
    """
    Backup a specific datastore entity to Google Cloud Storage
    Based on: https://cloud.google.com/datastore/docs/schedule-export
    """

    def get(self):
        access_token = self.get_oauth_token('https://www.googleapis.com/auth/datastore')
        app_id = app_identity.get_application_id()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d')

        backup_entities = self.get_backup_entities()
        backup_bucket = self.get_backup_bucket()
        output_url_prefix = "gs://{}/{}".format(backup_bucket, timestamp)

        entity_filter = {
            'kinds': backup_entities,
        }
        request = {
            'project_id': app_id,
            'output_url_prefix': output_url_prefix,
            'entity_filter': entity_filter
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + access_token
        }
        url = 'https://datastore.googleapis.com/v1beta1/projects/%s:export' % app_id
        status, _ = self.fetch_url(
            url=url,
            payload=json.dumps(request),
            method=urlfetch.POST,
            headers=headers)

        status_sitevar = Sitevar.get_by_id('apistatus')
        if status == 200 and status_sitevar and 'backup' in status_sitevar.contents:
            status_sitevar.contents['backup']['db_export'] = timestamp
            status_sitevar.put()


class DatastoreBackupArchive(BackupControllerBase):

    def get(self, backup_date):
        # Make sure the requested backup exists
        backup_bucket = self.get_backup_bucket()
        backup_dir = "/{}/{}/".format(backup_bucket, backup_date)

        backup_files = cloudstorage.listbucket(backup_dir)
        bucket_prefix = "/{}/".format(backup_bucket)
        count = 0
        for bfile in backup_files:
            if bfile.is_dir:
                continue

            count += 1
            fname = bfile.filename
            path = fname[len(bucket_prefix):]
            taskqueue.add(
                url='/backend-tasks/backup/archive/file',
                params={
                    'bucket': backup_bucket,
                    'object': path,
                },
                queue_name='backups',
                method='POST')

        self.response.out.write("Enqueued updates for {} files".format(count))


class DatastoreBackupArchiveFile(BackupControllerBase):
    def get_object_metadata(self, bucket_name, object_name, access_token):
        bucket_name = urllib.quote_plus(bucket_name)
        object_name = urllib.quote_plus(object_name)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + access_token
        }
        url = "https://www.googleapis.com/storage/v1/b/{0}/o/{1}"\
            .format(bucket_name, object_name)
        status, content = self.fetch_url(
            url=url,
            headers=headers)
        return json.loads(content) if status == 200 else {}

    def set_file_storage_class(self, bucket_name, object_name, storage_class, access_token):
        bucket_name = urllib.quote_plus(bucket_name)
        object_name = urllib.quote_plus(object_name)
        request = {
            'storageClass': 'coldline',
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + access_token
        }
        url = "https://www.googleapis.com/storage/v1/b/{0}/o/{1}/rewriteTo/b/{0}/o/{1}"\
            .format(bucket_name, object_name)
        self.fetch_url(
            url=url,
            payload=json.dumps(request),
            method=urlfetch.POST,
            deadline=90,
            headers=headers)

    def post(self):
        backup_bucket = self.request.get('bucket', None)
        path = self.request.get('object', None)

        if not backup_bucket or not path:
            logging.warning("Bad arguments, bucket: {}, path: {}".format(backup_bucket, path))
            self.abort(400)
        logging.info("Updating storage class for {}/{}".format(backup_bucket, path))
        # This uses the default service account for this application
        access_token, _ = app_identity.get_access_token(
            'https://www.googleapis.com/auth/devstorage.read_write')
        metadata = self.get_object_metadata(backup_bucket, path, access_token)
        storage_class = metadata.get('storageClass')
        if storage_class == 'COLDLINE':
            logging.info("File is already set to COLDLINE")
            return
        self.set_file_storage_class(backup_bucket, path, 'coldline', access_token)


class BigQueryImportEnqueue(BackupControllerBase):
    def get(self, backup_date):
        # Make sure the requested backup exists
        backup_bucket = self.get_backup_bucket()
        backup_entities = self.get_backup_entities()
        for entity in backup_entities:
            taskqueue.add(
                url='/backend-tasks/bigquery/import/{}/{}'.format(backup_date, entity),
                queue_name='backups',
                method='GET')


class BigQueryImportEntity(BackupControllerBase):
    def get(self, backup_date, entity):
        # Make sure the requested backup exists
        backup_bucket = self.get_backup_bucket()

        file_name = "{0}/all_namespaces/kind_{1}/all_namespaces_kind_{1}.export_metadata".format(
            backup_date,
            entity)
        metadata_url = "/{}/{}".format(backup_bucket, file_name)
        self.check_backup_exists(backup_bucket, file_name)

        # Set the first character of the entity name to lowercase
        table_name = entity[:1].lower() + entity[1:]
        bigquery_dataset = self.get_bigquery_dataset()

        # This is authenticated using the default App Engine service account
        # See https://cloud.google.com/docs/authentication/production
        bigquery_client = bigquery.Client()
        dataset = bigquery_client.dataset(bigquery_dataset)
        table = dataset.table(table_name)

        now = int(time.time())
        job_name = "{}_{}_{}".format(backup_date, entity, now)
        source_url = "gs:/{}".format(metadata_url)

        logging.info("[{}] Loading {} into {}".format(job_name, source_url, table))
        job = bigquery_client.load_table_from_storage(job_name, table, source_url)
        job.source_format = "DATASTORE_BACKUP"
        job.write_disposition = WriteDisposition.WRITE_TRUNCATE

        job.begin()
        logging.info("[{}] Job started at {}".format(job_name, job.started))

        wait_count = 50
        job.reload()
        while job.state != 'DONE' and wait_count > 0:
            logging.info("[{}] Job is {} ".format(datetime.datetime.now(), job.state))
            time.sleep(10)
            job.reload()

        logging.info("[{}] Job ended at: {}".format(job_name, job.ended))
        logging.info("[{}] Job ended with state: {}".format(job_name, job.state))
        if job.errors:
            logging.error("Job error result: {}".format(job.error_result))
        else:
            logging.info("[{}] Job imported {} rows to bigquery".format(job_name, job.output_rows))
        if 'X-Appengine-Taskname' not in self.request.headers:
            self.response.out.write("[{}] Job ended with state: {}".format(job_name, job.state))


class TbaCSVBackupEventsEnqueue(webapp.RequestHandler):
    """
    Enqueues CSV backup
    """
    def get(self, year=None):
        if year is None:
            years = range(tba_config.MIN_YEAR, datetime.datetime.now().year + 1)
            for y in years:
                taskqueue.add(
                    url='/tasks/enqueue/csv_backup_events/{}'.format(y),
                    method='GET')
            self.response.out.write("Enqueued backup for years: {}".format(years))
        else:
            event_keys = Event.query(Event.year == int(year)).fetch(None, keys_only=True)

            for event_key in event_keys:
                taskqueue.add(
                    url='/tasks/do/csv_backup_event/{}'.format(event_key.id()),
                    method='GET')

            template_values = {'event_keys': event_keys}
            path = os.path.join(os.path.dirname(__file__), '../templates/backup/csv_backup_enqueue.html')
            self.response.out.write(template.render(path, template_values))


class TbaCSVBackupEventDo(webapp.RequestHandler):
    """
    Backs up event awards, matches, team list, rankings, and alliance selection order
    """

    AWARDS_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/events/{}/{}/{}_awards.csv'  # % (year, event_key, event_key)
    MATCHES_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/events/{}/{}/{}_matches.csv'  # % (year, event_key, event_key)
    TEAMS_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/events/{}/{}/{}_teams.csv'  # % (year, event_key, event_key)
    RANKINGS_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/events/{}/{}/{}_rankings.csv'  # % (year, event_key, event_key)
    ALLIANCES_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/events/{}/{}/{}_alliances.csv'  # % (year, event_key, event_key)

    def get(self, event_key):
        event = Event.get_by_id(event_key)

        event.prepAwardsMatchesTeams()

        if event.awards:
            with cloudstorage.open(self.AWARDS_FILENAME_PATTERN.format(event.year, event_key, event_key), 'w') as awards_file:
                writer = csv.writer(awards_file, delimiter=',')
                for award in event.awards:
                    for recipient in award.recipient_list:
                        team = recipient['team_number']
                        if type(team) == int:
                            team = 'frc{}'.format(team)
                        self._writerow_unicode(writer, [award.key.id(), award.name_str, team, recipient['awardee']])

        if event.matches:
            with cloudstorage.open(self.MATCHES_FILENAME_PATTERN.format(event.year, event_key, event_key), 'w') as matches_file:
                writer = csv.writer(matches_file, delimiter=',')
                for match in event.matches:
                    red_score = match.alliances['red']['score']
                    blue_score = match.alliances['blue']['score']
                    self._writerow_unicode(writer, [match.key.id()] + match.alliances['red']['teams'] + match.alliances['blue']['teams'] + [red_score, blue_score])

        if event.teams:
            with cloudstorage.open(self.TEAMS_FILENAME_PATTERN.format(event.year, event_key, event_key), 'w') as teams_file:
                writer = csv.writer(teams_file, delimiter=',')
                self._writerow_unicode(writer, [team.key.id() for team in event.teams])

        if event.rankings:
            with cloudstorage.open(self.RANKINGS_FILENAME_PATTERN.format(event.year, event_key, event_key), 'w') as rankings_file:
                writer = csv.writer(rankings_file, delimiter=',')
                for row in event.rankings:
                    self._writerow_unicode(writer, row)

        if event.alliance_selections:
            with cloudstorage.open(self.ALLIANCES_FILENAME_PATTERN.format(event.year, event_key, event_key), 'w') as alliances_file:
                writer = csv.writer(alliances_file, delimiter=',')
                for alliance in event.alliance_selections:
                    self._writerow_unicode(writer, alliance['picks'])

        self.response.out.write("Done backing up {}!".format(event_key))

    def _writerow_unicode(self, writer, row):
        unicode_row = []
        for s in row:
            try:
                unicode_row.append(s.encode("utf-8"))
            except:
                unicode_row.append(s)
        writer.writerow(unicode_row)


class TbaCSVRestoreEventsEnqueue(webapp.RequestHandler):
    """
    Enqueues CSV restore
    """
    def get(self, year=None):
        if tba_config.CONFIG["env"] == "prod":  # disable in prod for now
            logging.error("Tried to restore events from CSV for year {} in prod! No can do.".format(year))
            return

        if year is None:
            years = range(tba_config.MIN_YEAR, datetime.datetime.now().year + 1)
            for y in years:
                taskqueue.add(
                    url='/tasks/enqueue/csv_restore_events/{}'.format(y),
                    method='GET')
            self.response.out.write("Enqueued restore for years: {}".format(years))
        else:
            event_keys = Event.query(Event.year == int(year)).fetch(None, keys_only=True)

            for event_key in event_keys:
                taskqueue.add(
                    url='/tasks/do/csv_restore_event/{}'.format(event_key.id()),
                    method='GET')

            template_values = {'event_keys': event_keys}
            path = os.path.join(os.path.dirname(__file__), '../templates/backup/csv_restore_enqueue.html')
            self.response.out.write(template.render(path, template_values))


class TbaCSVRestoreEventDo(webapp.RequestHandler):
    """
    Restores event awards, matches, team list, rankings, and alliance selection order
    """

    BASE_URL = 'https://raw.githubusercontent.com/the-blue-alliance/tba-data-backup/master/events/{}/{}/'  # % (year, event_key)
    ALLIANCES_URL = BASE_URL + '{}_alliances.csv'  # % (year, event_key, event_key)
    AWARDS_URL = BASE_URL + '{}_awards.csv'  # % (year, event_key, event_key)
    MATCHES_URL = BASE_URL + '{}_matches.csv'  # % (year, event_key, event_key)
    RANKINGS_URL = BASE_URL + '{}_rankings.csv'  # % (year, event_key, event_key)
    # TEAMS_URL = BASE_URL + '{}_teams.csv'  # % (year, event_key, event_key)  # currently unused

    def get(self, event_key):
        if tba_config.CONFIG["env"] == "prod":  # disable in prod for now
            logging.error("Tried to restore {} from CSV in prod! No can do.".format(event_key))
            return

        event = Event.get_by_id(event_key)

        # alliances
        result = urlfetch.fetch(self.ALLIANCES_URL.format(event.year, event_key, event_key))
        if result.status_code != 200:
            logging.warning('Unable to retreive url: ' + (self.ALLIANCES_URL.format(event.year, event_key, event_key)))
        else:
            data = result.content.replace('frc', '')
            alliance_selections = CSVAllianceSelectionsParser.parse(data)

            event_details = EventDetails(
                id=event_key,
                alliance_selections=alliance_selections
            )
            EventDetailsManipulator.createOrUpdate(event_details)

        # awards
        result = urlfetch.fetch(self.AWARDS_URL.format(event.year, event_key, event_key))
        if result.status_code != 200:
            logging.warning('Unable to retreive url: ' + (self.AWARDS_URL.format(event.year, event_key, event_key)))
        else:
            # convert into expected input format
            data = StringIO.StringIO()
            writer = csv.writer(data, delimiter=',')
            for row in csv.reader(StringIO.StringIO(result.content), delimiter=','):
                writer.writerow([event.year, event.event_short, row[1], row[2].replace('frc', ''), row[3]])

            awards = []
            for award in CSVAwardsParser.parse(data.getvalue()):
                awards.append(Award(
                    id=Award.render_key_name(event.key_name, award['award_type_enum']),
                    name_str=award['name_str'],
                    award_type_enum=award['award_type_enum'],
                    year=event.year,
                    event=event.key,
                    event_type_enum=event.event_type_enum,
                    team_list=[ndb.Key(Team, 'frc{}'.format(team_number)) for team_number in award['team_number_list']],
                    recipient_json_list=award['recipient_json_list']
                ))
            AwardManipulator.createOrUpdate(awards)

        # matches
        result = urlfetch.fetch(self.MATCHES_URL.format(event.year, event_key, event_key))
        if result.status_code != 200:
            logging.warning('Unable to retreive url: ' + (self.MATCHES_URL.format(event.year, event_key, event_key)))
        else:
            data = result.content.replace('frc', '').replace('{}_'.format(event_key), '')
            match_dicts, _ = OffseasonMatchesParser.parse(data)
            matches = [
                Match(
                    id=Match.renderKeyName(
                        event.key.id(),
                        match.get("comp_level", None),
                        match.get("set_number", 0),
                        match.get("match_number", 0)),
                    event=event.key,
                    year=event.year,
                    set_number=match.get("set_number", 0),
                    match_number=match.get("match_number", 0),
                    comp_level=match.get("comp_level", None),
                    team_key_names=match.get("team_key_names", None),
                    alliances_json=match.get("alliances_json", None)
                )
            for match in match_dicts]
            MatchManipulator.createOrUpdate(matches)

        # rankings
        result = urlfetch.fetch(self.RANKINGS_URL.format(event.year, event_key, event_key))
        if result.status_code != 200:
            logging.warning('Unable to retreive url: ' + (self.RANKINGS_URL.format(event.year, event_key, event_key)))
        else:
            # convert into expected input format
            rankings = list(csv.reader(StringIO.StringIO(result.content), delimiter=','))

            event_details = EventDetails(
                id=event_key,
                rankings=rankings
            )
            EventDetailsManipulator.createOrUpdate(event_details)

        self.response.out.write("Done restoring {}!".format(event_key))


class TbaCSVBackupTeamsEnqueue(webapp.RequestHandler):
    """
    Enqueues CSV teams backup
    """
    def get(self):
        taskqueue.add(
            target='backend-tasks-b2',
            url='/backend-tasks-b2/do/csv_backup_teams',
            method='GET')
        self.response.out.write("Enqueued CSV teams backup")


class TbaCSVBackupTeamsDo(webapp.RequestHandler):
    """
    Backs up teams
    """
    TEAMS_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/teams/teams.csv'

    def get(self):
        team_keys_future = Team.query().order(Team.team_number).fetch_async(keys_only=True)
        social_media_keys_future = Media.query(Media.year == None).fetch_async(keys_only=True)

        team_futures = ndb.get_multi_async(team_keys_future.get_result())
        social_futures = ndb.get_multi_async(social_media_keys_future.get_result())

        socials_by_team = defaultdict(dict)
        for social_future in social_futures:
            social = social_future.get_result()
            for reference in social.references:
                socials_by_team[reference.id()][social.media_type_enum] = social

        if team_futures:
            with cloudstorage.open(self.TEAMS_FILENAME_PATTERN, 'w') as teams_file:
                writer = csv.writer(teams_file, delimiter=',')
                for team_future in team_futures:
                    team = team_future.get_result()
                    team_row = [team.key.id(), team.nickname, team.name, team.city, team.state_prov, team.country, team.website, team.rookie_year]
                    for social_type in MediaType.social_types:
                        social = socials_by_team[team.key.id()].get(social_type, None)
                        team_row.append(social.social_profile_url if social is not None else None)
                    self._writerow_unicode(writer, team_row)

        self.response.out.write("Done backing up teams!")

    def _writerow_unicode(self, writer, row):
        unicode_row = []
        for s in row:
            try:
                unicode_row.append(s.encode("utf-8"))
            except:
                unicode_row.append(s)
        writer.writerow(unicode_row)
