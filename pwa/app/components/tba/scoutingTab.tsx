import { useMemo } from 'react';

import { EventCoprs, Match, Media, Team } from '~/api/tba/read';
import ScoutingExport from '~/components/tba/scoutingExport';
import { generateCsv } from '~/lib/csvUtils';
import {
  transformCoprsToTable,
  transformMatchesToFlatSchedule,
  transformMatchesToSchedule,
  transformTeamsToTeamList,
} from '~/lib/scoutingUtils';

interface ScoutingTabProps {
  teams: Team[];
  media: Media[];
  matches: Match[];
  eventKey: string;
  coprs?: EventCoprs;
}

export default function ScoutingTab({
  teams,
  media,
  matches,
  eventKey,
  coprs,
}: ScoutingTabProps) {
  // Transform data - memoized to avoid recalculation
  const teamListData = useMemo(
    () => transformTeamsToTeamList(teams, media),
    [teams, media],
  );

  const scheduleData = useMemo(
    () => transformMatchesToSchedule(matches),
    [matches],
  );

  const flatScheduleData = useMemo(
    () => transformMatchesToFlatSchedule(matches),
    [matches],
  );

  const coprsTable = useMemo(
    () => (coprs ? transformCoprsToTable(coprs) : null),
    [coprs],
  );

  // Generate CSV strings - memoized to avoid regeneration
  const teamListCsv = useMemo(
    () =>
      generateCsv({
        columns: [
          'team_number',
          'team_name',
          'city',
          'state_prov',
          'country',
          'robot_picture_url',
        ],
        data: teamListData,
      }),
    [teamListData],
  );

  const scheduleCsv = useMemo(
    () =>
      generateCsv({
        columns: [
          'match_key',
          'scheduled_date',
          'scheduled_time',
          'comp_level',
          'match_number',
          'set_number',
          'red1',
          'red2',
          'red3',
          'blue1',
          'blue2',
          'blue3',
          'red_score',
          'blue_score',
        ],
        data: scheduleData,
      }),
    [scheduleData],
  );

  const flatScheduleCsv = useMemo(
    () =>
      generateCsv({
        columns: [
          'match_key',
          'scheduled_date',
          'scheduled_time',
          'comp_level',
          'match_number',
          'set_number',
          'color',
          'team',
        ],
        data: flatScheduleData,
      }),
    [flatScheduleData],
  );

  const coprsCsv = useMemo(
    () =>
      coprsTable
        ? generateCsv({
            columns: coprsTable.columns,
            data: coprsTable.data,
          })
        : '',
    [coprsTable],
  );

  return (
    <div className="space-y-8">
      <p className="text-muted-foreground">
        Export event data in CSV format for scouting purposes.
      </p>

      <ScoutingExport
        title="Team List"
        csvData={teamListCsv}
        filename={`${eventKey}_teams.csv`}
      />

      <ScoutingExport
        title="Match Schedule"
        csvData={scheduleCsv}
        filename={`${eventKey}_schedule.csv`}
      />

      <ScoutingExport
        title="Flat Match Schedule"
        csvData={flatScheduleCsv}
        filename={`${eventKey}_flat_schedule.csv`}
      />

      {coprsTable && (
        <ScoutingExport
          title="Component OPRs"
          csvData={coprsCsv}
          filename={`${eventKey}_coprs.csv`}
        />
      )}
    </div>
  );
}
