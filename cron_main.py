#!/usr/bin/env python
import webapp2

import tba_config

from controllers.backup_controller import TbaCSVBackupEventsEnqueue, TbaCSVBackupEventDo, TbaCSVRestoreEventsEnqueue, TbaCSVRestoreEventDo
from controllers.backup_controller import TbaCSVBackupTeamsEnqueue

from controllers.datafeed_controller import TbaVideosGet, TbaVideosEnqueue
from controllers.datafeed_controller import FMSAPIAwardsEnqueue, FMSAPIEventAlliancesEnqueue, FMSAPIEventRankingsEnqueue, FMSAPIMatchesEnqueue
from controllers.datafeed_controller import FMSAPIAwardsGet, FMSAPIEventAlliancesGet, FMSAPIEventRankingsGet, FMSAPIMatchesGet

from controllers.cron_controller import DistrictPointsCalcEnqueue, DistrictPointsCalcDo
from controllers.cron_controller import EventShortNameCalcEnqueue, EventShortNameCalcDo
from controllers.cron_controller import EventTeamRepairDo, EventTeamUpdate, EventTeamUpdateEnqueue
from controllers.cron_controller import EventMatchstatsDo, EventMatchstatsEnqueue
from controllers.cron_controller import FinalMatchesRepairDo
from controllers.cron_controller import UpcomingNotificationDo

from controllers.admin.admin_cron_controller import AdminMobileClearEnqueue, AdminMobileClear, AdminSubsClearEnqueue, AdminSubsClear, \
    AdminWebhooksClearEnqueue, AdminWebhooksClear

app = webapp2.WSGIApplication([('/tasks/enqueue/csv_backup_events', TbaCSVBackupEventsEnqueue),
                               ('/tasks/enqueue/csv_backup_events/([0-9]*)', TbaCSVBackupEventsEnqueue),
                               ('/tasks/do/csv_backup_event/(.*)', TbaCSVBackupEventDo),
                               ('/tasks/enqueue/csv_restore_events', TbaCSVRestoreEventsEnqueue),
                               ('/tasks/enqueue/csv_restore_events/([0-9]*)', TbaCSVRestoreEventsEnqueue),
                               ('/tasks/do/csv_restore_event/(.*)', TbaCSVRestoreEventDo),
                               ('/tasks/enqueue/csv_backup_teams', TbaCSVBackupTeamsEnqueue),
                               ('/tasks/enqueue/tba_videos', TbaVideosEnqueue),
                               ('/tasks/enqueue/fmsapi_awards/(.*)', FMSAPIAwardsEnqueue),
                               ('/tasks/enqueue/fmsapi_event_alliances/(.*)', FMSAPIEventAlliancesEnqueue),
                               ('/tasks/enqueue/fmsapi_event_rankings/(.*)', FMSAPIEventRankingsEnqueue),
                               ('/tasks/enqueue/fmsapi_matches/(.*)', FMSAPIMatchesEnqueue),
                               ('/tasks/get/tba_videos/(.*)', TbaVideosGet),
                               ('/tasks/get/fmsapi_awards/(.*)', FMSAPIAwardsGet),
                               ('/tasks/get/fmsapi_event_alliances/(.*)', FMSAPIEventAlliancesGet),
                               ('/tasks/get/fmsapi_event_rankings/(.*)', FMSAPIEventRankingsGet),
                               ('/tasks/get/fmsapi_matches/(.*)', FMSAPIMatchesGet),
                               ('/tasks/math/enqueue/district_points_calc/([0-9]*)', DistrictPointsCalcEnqueue),
                               ('/tasks/math/do/district_points_calc/(.*)', DistrictPointsCalcDo),
                               ('/tasks/math/enqueue/event_short_name_calc_enqueue/([0-9]*)', EventShortNameCalcEnqueue),
                               ('/tasks/math/do/event_short_name_calc_do/(.*)', EventShortNameCalcDo),
                               ('/tasks/math/enqueue/event_matchstats/(.*)', EventMatchstatsEnqueue),
                               ('/tasks/math/enqueue/eventteam_update/(.*)', EventTeamUpdateEnqueue),
                               ('/tasks/math/do/event_matchstats/(.*)', EventMatchstatsDo),
                               ('/tasks/math/do/eventteam_repair', EventTeamRepairDo),
                               ('/tasks/math/do/eventteam_update/(.*)', EventTeamUpdate),
                               ('/tasks/math/do/final_matches_repair/([0-9]*)', FinalMatchesRepairDo),
                               ('/tasks/notifications/upcoming_match', UpcomingNotificationDo),
                               ('/tasks/admin/enqueue/clear_mobile_duplicates', AdminMobileClearEnqueue),
                               ('/tasks/admin/clear_mobile_duplicates', AdminMobileClear),
                               ('/tasks/admin/enqueue/clear_old_subs', AdminSubsClearEnqueue),
                               ('/tasks/admin/clear_old_subs', AdminSubsClear),
                               ('/tasks/admin/enqueue/clear_old_webhooks', AdminWebhooksClearEnqueue),
                               ('/tasks/admin/clear_old_webhooks', AdminWebhooksClear),
                               ],
                              debug=tba_config.DEBUG)
