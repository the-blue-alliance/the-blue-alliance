#!/usr/bin/env python
import webapp2

import tba_config

from controllers.admin.admin_cron_controller import AdminPostEventTasksDo, AdminCreateDistrictTeamsEnqueue, AdminCreateDistrictTeamsDo, \
    AdminRebuildDivisionsDo, AdminRebuildDivisionsEnqueue, AdminBackfillPlayoffTypeDo, \
    AdminBackfillPlayoffTypeEnqueue
from controllers.backup_controller import DatastoreBackupFull, BigQueryImportEnqueue, \
    BigQueryImportEntity, MainBackupsEnqueue, DatastoreBackupArchive, DatastoreBackupArchiveFile
from controllers.datafeed_controller import EventListEnqueue, EventDetailsEnqueue
from controllers.datafeed_controller import EventListGet, EventDetailsGet, TeamDetailsGet, TeamAvatarGet, DistrictListGet, DistrictRankingsGet, TeamBlacklistWebsiteDo, EventListCurrentEnqueue


app = webapp2.WSGIApplication([('/backend-tasks/enqueue/event_list/([0-9]*)', EventListEnqueue),
                               ('/backend-tasks/enqueue/event_list/current', EventListCurrentEnqueue),
                               ('/backend-tasks/enqueue/event_details/(.*)', EventDetailsEnqueue),
                               ('/backend-tasks/get/event_list/([0-9]*)', EventListGet),
                               ('/backend-tasks/get/district_list/([0-9]*)', DistrictListGet),
                               ('/backend-tasks/get/event_details/(.*)', EventDetailsGet),
                               ('/backend-tasks/get/team_details/(.*)', TeamDetailsGet),
                               ('/backend-tasks/get/team_avatar/(.*)', TeamAvatarGet),
                               ('/backend-tasks/do/team_blacklist_website/(.*)', TeamBlacklistWebsiteDo),
                               ('/backend-tasks/get/district_rankings/(.*)', DistrictRankingsGet),
                               ('/backend-tasks/do/post_event_tasks/(.*)', AdminPostEventTasksDo),
                               ('/backend-tasks/enqueue/rebuild_district_teams/([0-9]+)', AdminCreateDistrictTeamsEnqueue),
                               ('/backend-tasks/do/rebuild_district_teams/([0-9]+)', AdminCreateDistrictTeamsDo),
                               ('/backend-tasks/enqueue/rebuild_divisions/([0-9]+)', AdminRebuildDivisionsEnqueue),
                               ('/backend-tasks/enqueue/backfill_playoff_type/([0-9]+)', AdminBackfillPlayoffTypeEnqueue),
                               ('/backend-tasks/do/backfill_playoff_type/([0-9]+)', AdminBackfillPlayoffTypeDo),
                               ('/backend-tasks/do/rebuild_divisions/([0-9]+)', AdminRebuildDivisionsDo),

                               # Backup Tasks
                               ('/backend-tasks/backup/archive/([0-9\-]+)', DatastoreBackupArchive),
                               webapp2.Route(r'/backend-tasks/backup/archive/file',
                                             DatastoreBackupArchiveFile,
                                             methods=['POST']),
                               ('/backend-tasks/backup/datastore', DatastoreBackupFull),
                               ('/backend-tasks/backup/enqueue', MainBackupsEnqueue),
                               ('/backend-tasks/bigquery/import/([0-9\-]+)', BigQueryImportEnqueue),
                               ('/backend-tasks/bigquery/import/([0-9\-]+)/([A-Za-z]+)', BigQueryImportEntity),
                               ],
                              debug=tba_config.DEBUG)
