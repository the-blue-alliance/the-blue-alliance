#!/usr/bin/env python
import webapp2

import tba_config

from controllers.backup_controller import TbaCSVBackupEventsEnqueue, TbaCSVBackupEventDo, TbaCSVRestoreEventsEnqueue, TbaCSVRestoreEventDo
from controllers.backup_controller import TbaCSVBackupTeamsEnqueue, TbaCSVBackupTeamsDo

from controllers.datafeed_controller import TbaVideosGet, TbaVideosEnqueue
from controllers.datafeed_controller import FmsEventListGet, FmsTeamListGet
from controllers.datafeed_controller import OffseasonMatchesGet
from controllers.datafeed_controller import TwitterFrcfmsMatchesGet
from controllers.datafeed_controller import UsfirstEventDetailsEnqueue, UsfirstEventDetailsGet, UsfirstEventListGet
from controllers.datafeed_controller import UsfirstAwardsEnqueue, UsfirstAwardsGet
from controllers.datafeed_controller import UsfirstEventAlliancesEnqueue, UsfirstEventAlliancesGet
from controllers.datafeed_controller import UsfirstMatchesEnqueue, UsfirstMatchesGet, UsfirstEventRankingsEnqueue, UsfirstEventRankingsGet
from controllers.datafeed_controller import UsfirstTeamDetailsEnqueue, UsfirstTeamDetailsRollingEnqueue, UsfirstTeamDetailsGet, UsfirstTeamsTpidsGet
from controllers.datafeed_controller import UsfirstPre2003TeamEventsEnqueue, UsfirstPre2003TeamEventsGet

from controllers.cron_controller import DistrictPointsCalcEnqueue, DistrictPointsCalcDo
from controllers.cron_controller import EventShortNameCalcEnqueue, EventShortNameCalcDo
from controllers.cron_controller import EventTeamRepairDo, EventTeamUpdate, EventTeamUpdateEnqueue
from controllers.cron_controller import EventMatchstatsDo, EventMatchstatsEnqueue
from controllers.cron_controller import FinalMatchesRepairDo
from controllers.cron_controller import YearInsightsEnqueue, YearInsightsDo, OverallInsightsEnqueue, OverallInsightsDo, TypeaheadCalcEnqueue, TypeaheadCalcDo

from controllers.firebase_controller import FirebasePushDo

from controllers.admin.admin_cron_controller import AdminMobileClearEnqueue, AdminMobileClearDo, AdminSubsClearEnqueue, AdminSubsClearDo, \
    AdminWebhooksClearEnqueue, AdminWebhooksClearDo


app = webapp2.WSGIApplication([('/tasks/enqueue/csv_backup_events', TbaCSVBackupEventsEnqueue),
                               ('/tasks/enqueue/csv_backup_events/([0-9]*)', TbaCSVBackupEventsEnqueue),
                               ('/tasks/do/csv_backup_event/(.*)', TbaCSVBackupEventDo),
                               ('/tasks/enqueue/csv_restore_events', TbaCSVRestoreEventsEnqueue),
                               ('/tasks/enqueue/csv_restore_events/([0-9]*)', TbaCSVRestoreEventsEnqueue),
                               ('/tasks/do/csv_restore_event/(.*)', TbaCSVRestoreEventDo),
                               ('/tasks/enqueue/csv_backup_teams', TbaCSVBackupTeamsEnqueue),
                               ('/tasks/do/csv_backup_teams', TbaCSVBackupTeamsDo),
                               ('/tasks/enqueue/tba_videos', TbaVideosEnqueue),
                               ('/tasks/enqueue/usfirst_event_alliances/(.*)', UsfirstEventAlliancesEnqueue),
                               ('/tasks/enqueue/usfirst_event_details/([0-9]*)', UsfirstEventDetailsEnqueue),
                               ('/tasks/enqueue/usfirst_event_rankings/(.*)', UsfirstEventRankingsEnqueue),
                               ('/tasks/enqueue/usfirst_awards/(.*)', UsfirstAwardsEnqueue),
                               ('/tasks/enqueue/usfirst_matches/(.*)', UsfirstMatchesEnqueue),
                               ('/tasks/enqueue/usfirst_team_details', UsfirstTeamDetailsEnqueue),
                               ('/tasks/enqueue/usfirst_team_details_rolling', UsfirstTeamDetailsRollingEnqueue),
                               ('/tasks/enqueue/usfirst_pre2003_team_events', UsfirstPre2003TeamEventsEnqueue),
                               ('/tasks/get/fms_event_list', FmsEventListGet),
                               ('/tasks/get/fms_team_list', FmsTeamListGet),
                               ('/tasks/get/offseason_matches/(.*)', OffseasonMatchesGet),
                               ('/tasks/get/tba_videos/(.*)', TbaVideosGet),
                               ('/tasks/get/twitter_frcfms_matches', TwitterFrcfmsMatchesGet),
                               ('/tasks/get/usfirst_event_alliances/(.*)', UsfirstEventAlliancesGet),
                               ('/tasks/get/usfirst_event_list/([0-9]*)', UsfirstEventListGet),
                               ('/tasks/get/usfirst_event_details/([0-9]*)/([0-9]*)', UsfirstEventDetailsGet),
                               ('/tasks/get/usfirst_event_rankings/(.*)', UsfirstEventRankingsGet),
                               ('/tasks/get/usfirst_awards/(.*)', UsfirstAwardsGet),
                               ('/tasks/get/usfirst_matches/(.*)', UsfirstMatchesGet),
                               ('/tasks/get/usfirst_team_details/(.*)', UsfirstTeamDetailsGet),
                               ('/tasks/get/usfirst_teams_tpids/([0-9]*)', UsfirstTeamsTpidsGet),
                               ('/tasks/get/usfirst_pre2003_team_events/(.*)', UsfirstPre2003TeamEventsGet),
                               ('/tasks/math/enqueue/district_points_calc/([0-9]*)/([0-9]*)', DistrictPointsCalcEnqueue),
                               ('/tasks/math/do/district_points_calc/(.*)', DistrictPointsCalcDo),
                               ('/tasks/math/enqueue/event_short_name_calc_enqueue/([0-9]*)', EventShortNameCalcEnqueue),
                               ('/tasks/math/do/event_short_name_calc_do/(.*)', EventShortNameCalcDo),
                               ('/tasks/math/enqueue/event_matchstats/(.*)', EventMatchstatsEnqueue),
                               ('/tasks/math/enqueue/eventteam_update/(.*)', EventTeamUpdateEnqueue),
                               ('/tasks/math/do/event_matchstats/(.*)', EventMatchstatsDo),
                               ('/tasks/math/do/eventteam_repair', EventTeamRepairDo),
                               ('/tasks/math/do/eventteam_update/(.*)', EventTeamUpdate),
                               ('/tasks/math/do/final_matches_repair/([0-9]*)', FinalMatchesRepairDo),
                               ('/tasks/math/enqueue/overallinsights/(.*)', OverallInsightsEnqueue),
                               ('/tasks/math/do/overallinsights/(.*)', OverallInsightsDo),
                               ('/tasks/math/enqueue/insights/(.*)/([0-9]*)', YearInsightsEnqueue),
                               ('/tasks/math/do/insights/(.*)/([0-9]*)', YearInsightsDo),
                               ('/tasks/math/enqueue/typeaheadcalc', TypeaheadCalcEnqueue),
                               ('/tasks/math/do/typeaheadcalc', TypeaheadCalcDo),
                               ('/tasks/posts/firebase_push', FirebasePushDo),
                               ('/tasks/admin/enqueue/clear_mobile_duplicates', AdminMobileClearEnqueue),
                               ('/tasks/admin/do/clear_mobile_duplicates', AdminMobileClearDo),
                               ('/tasks/admin/enqueue/clear_old_subs', AdminSubsClearEnqueue),
                               ('/tasks/admin/do/clear_old_subs', AdminSubsClearDo),
                               ('/tasks/admin/enqueue/clear_old_webhooks', AdminWebhooksClearEnqueue),
                               ('/tasks/admin/do/clear_old_webhooks', AdminWebhooksClearDo),
                               ],
                              debug=tba_config.DEBUG)
