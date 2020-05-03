#!/usr/bin/env python
import webapp2

import tba_config

from controllers.backup_controller import TbaCSVBackupEventsEnqueue, TbaCSVBackupEventDo, TbaCSVRestoreEventsEnqueue, TbaCSVRestoreEventDo
from controllers.backup_controller import TbaCSVBackupTeamsEnqueue

from controllers.datafeed_controller import TbaVideosGet, TbaVideosEnqueue
from controllers.datafeed_controller import FMSAPIAwardsEnqueue, FMSAPIEventAlliancesEnqueue, FMSAPIEventRankingsEnqueue, FMSAPIMatchesEnqueue
from controllers.datafeed_controller import FMSAPIAwardsGet, FMSAPIEventAlliancesGet, FMSAPIEventRankingsGet, FMSAPIMatchesGet
from controllers.datafeed_controller import HallOfFameTeamsGet

from controllers.cron_controller import DistrictPointsCalcEnqueue, DistrictPointsCalcDo, \
    MatchTimePredictionsEnqueue, MatchTimePredictionsDo, BlueZoneUpdateDo, SuggestionQueueDailyNag, RemapTeamsDo, \
    RebuildPlayoffAdvancementEnqueue, RebuildPlayoffAdvancementDo
from controllers.cron_controller import DistrictRankingsCalcEnqueue, DistrictRankingsCalcDo
from controllers.cron_controller import EventTeamStatusCalcEnqueue, EventTeamStatusCalcDo
from controllers.cron_controller import EventShortNameCalcEnqueue, EventShortNameCalcDo
from controllers.cron_controller import EventTeamRepairDo, EventTeamUpdate, EventTeamUpdateEnqueue
from controllers.cron_controller import EventMatchstatsDo, EventMatchstatsEnqueue
from controllers.cron_controller import FinalMatchesRepairDo
from controllers.cron_controller import UpcomingNotificationDo
from controllers.cron_controller import UpdateLiveEventsDo

from controllers.admin.admin_cron_controller import AdminMobileClearEnqueue, AdminMobileClear, AdminSubsClearEnqueue, AdminSubsClear, \
    AdminWebhooksClearEnqueue, AdminWebhooksClear, AdminRegistrationDayEnqueue, \
    AdminClearEventTeamsDo
from controllers.admin.admin_cron_controller import AdminRunPostUpdateHooksEnqueue, AdminRunPostUpdateHooksDo, AdminRunEventPostUpdateHookDo, AdminRunTeamPostUpdateHookDo, \
    AdminUpdateAllTeamSearchIndexEnqueue, AdminUpdateAllTeamSearchIndexDo, AdminUpdateTeamSearchIndexDo


app = webapp2.WSGIApplication([('/tasks/enqueue/csv_backup_events', TbaCSVBackupEventsEnqueue),
                               ('/tasks/enqueue/csv_backup_events/([0-9]*)', TbaCSVBackupEventsEnqueue),
                               ('/tasks/do/csv_backup_event/(.*)', TbaCSVBackupEventDo),
                               ('/tasks/enqueue/csv_restore_events', TbaCSVRestoreEventsEnqueue),
                               ('/tasks/enqueue/csv_restore_events/([0-9]*)', TbaCSVRestoreEventsEnqueue),
                               ('/tasks/do/bluezone_update', BlueZoneUpdateDo),
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
                               ('/tasks/get/hof_teams', HallOfFameTeamsGet),
                               ('/tasks/math/enqueue/district_points_calc/([0-9]*)', DistrictPointsCalcEnqueue),
                               ('/tasks/math/do/district_points_calc/(.*)', DistrictPointsCalcDo),
                               ('/tasks/math/enqueue/district_rankings_calc/([0-9]*)', DistrictRankingsCalcEnqueue),
                               ('/tasks/math/do/district_rankings_calc/(.*)', DistrictRankingsCalcDo),
                               ('/tasks/math/enqueue/event_team_status/([0-9]*)', EventTeamStatusCalcEnqueue),
                               ('/tasks/math/do/event_team_status/(.*)', EventTeamStatusCalcDo),
                               ('/tasks/math/enqueue/event_short_name_calc_enqueue/([0-9]*)', EventShortNameCalcEnqueue),
                               ('/tasks/math/do/event_short_name_calc_do/(.*)', EventShortNameCalcDo),
                               ('/tasks/math/enqueue/event_matchstats/(.*)', EventMatchstatsEnqueue),
                               ('/tasks/math/enqueue/eventteam_update/(.*)', EventTeamUpdateEnqueue),
                               ('/tasks/math/do/event_matchstats/(.*)', EventMatchstatsDo),
                               ('/tasks/math/do/eventteam_repair', EventTeamRepairDo),
                               ('/tasks/math/do/eventteam_update/(.*)', EventTeamUpdate),
                               ('/tasks/math/do/final_matches_repair/([0-9]*)', FinalMatchesRepairDo),
                               ('/tasks/math/enqueue/predict_match_times', MatchTimePredictionsEnqueue),
                               ('/tasks/math/do/predict_match_times/(.*)', MatchTimePredictionsDo),
                               ('/tasks/math/enqueue/playoff_advancement_update/(.*)', RebuildPlayoffAdvancementEnqueue),
                               ('/tasks/math/do/playoff_advancement_update/(.*)', RebuildPlayoffAdvancementDo),
                               ('/tasks/notifications/upcoming_match', UpcomingNotificationDo),
                               ('/tasks/admin/enqueue/clear_mobile_duplicates', AdminMobileClearEnqueue),
                               ('/tasks/admin/clear_mobile_duplicates', AdminMobileClear),
                               ('/tasks/admin/enqueue/clear_old_subs', AdminSubsClearEnqueue),
                               ('/tasks/admin/clear_old_subs', AdminSubsClear),
                               ('/tasks/admin/enqueue/clear_old_webhooks', AdminWebhooksClearEnqueue),
                               ('/tasks/admin/clear_old_webhooks', AdminWebhooksClear),
                               ('/tasks/admin/enqueue/registration_day', AdminRegistrationDayEnqueue),
                               ('/tasks/admin/enqueue/run_post_update_hooks/(.*)', AdminRunPostUpdateHooksEnqueue),
                               ('/tasks/admin/do/clear_eventteams/(.*)', AdminClearEventTeamsDo),
                               ('/tasks/admin/do/run_post_update_hooks/(.*)', AdminRunPostUpdateHooksDo),
                               ('/tasks/admin/do/run_event_post_update_hook/(.*)', AdminRunEventPostUpdateHookDo),
                               ('/tasks/admin/do/run_team_post_update_hook/(.*)', AdminRunTeamPostUpdateHookDo),
                               ('/tasks/enqueue/update_all_team_search_index', AdminUpdateAllTeamSearchIndexEnqueue),
                               ('/tasks/do/update_all_team_search_index', AdminUpdateAllTeamSearchIndexDo),
                               ('/tasks/do/update_team_search_index/(.*)', AdminUpdateTeamSearchIndexDo),
                               ('/tasks/do/update_live_events', UpdateLiveEventsDo),
                               ('/tasks/do/nag_suggestions', SuggestionQueueDailyNag),
                               ('/tasks/do/remap_teams/(.*)', RemapTeamsDo),
                               ],
                              debug=tba_config.DEBUG)
