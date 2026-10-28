import { Link } from '@tanstack/react-router';
import { useMemo, useState } from 'react';

import { EventCoprs, Match, Media, Team } from '~/api/tba/read';
import ScoutingExport from '~/components/tba/scoutingExport';
import { Button } from '~/components/ui/button';
import { type DelimitedFormat, generateCsv } from '~/lib/csvUtils';
import {
  transformCoprsToTable,
  transformMatchesToFlatSchedule,
  transformMatchesToRobotBreakdown,
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
  const [format, setFormat] = useState<DelimitedFormat>('tsv');

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

  const robotBreakdownTable = useMemo(
    () => transformMatchesToRobotBreakdown(matches),
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
        format,
      }),
    [teamListData, format],
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
        format,
      }),
    [scheduleData, format],
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
        format,
      }),
    [flatScheduleData, format],
  );

  const robotBreakdownCsv = useMemo(
    () => generateCsv({ ...robotBreakdownTable, format }),
    [robotBreakdownTable, format],
  );

  const coprsCsv = useMemo(
    () =>
      coprsTable
        ? generateCsv({
            columns: coprsTable.columns,
            data: coprsTable.data,
            format,
          })
        : '',
    [coprsTable, format],
  );

  return (
    <div className="space-y-4">
      <div
        className="flex flex-col gap-3 sm:flex-row sm:items-center
          sm:justify-between"
      >
        <p className="text-muted-foreground">
          Export event data for scouting spreadsheets. TSV pastes straight into
          Google Sheets and Excel. For JSON, use{' '}
          <Link to="/apidocs/v3">the API</Link>.
        </p>
        <fieldset className="flex shrink-0 gap-1" aria-label="Format">
          <Button
            size="sm"
            variant={format === 'csv' ? 'default' : 'outline'}
            aria-pressed={format === 'csv'}
            onClick={() => setFormat('csv')}
          >
            CSV
          </Button>
          <Button
            size="sm"
            variant={format === 'tsv' ? 'default' : 'outline'}
            aria-pressed={format === 'tsv'}
            onClick={() => setFormat('tsv')}
          >
            TSV
          </Button>
        </fieldset>
      </div>

      <ul className="divide-y rounded-xl border bg-card">
        <ScoutingExport
          title="Team List"
          description="One row per team"
          rowCount={teamListData.length}
          csvData={teamListCsv}
          filename={`${eventKey}_teams.${format}`}
          format={format}
        />

        <ScoutingExport
          title="Match Schedule"
          description="One row per match"
          rowCount={scheduleData.length}
          csvData={scheduleCsv}
          filename={`${eventKey}_schedule.${format}`}
          format={format}
        />

        <ScoutingExport
          title="Flat Match Schedule"
          description="One row per team per match"
          rowCount={flatScheduleData.length}
          csvData={flatScheduleCsv}
          filename={`${eventKey}_flat_schedule.${format}`}
          format={format}
        />

        {robotBreakdownTable.data.length > 0 && (
          <ScoutingExport
            title="Per-Robot Match Breakdown"
            description="One row per robot per played match"
            rowCount={robotBreakdownTable.data.length}
            csvData={robotBreakdownCsv}
            filename={`${eventKey}_robot_breakdown.${format}`}
            format={format}
          />
        )}

        {coprsTable && (
          <ScoutingExport
            title="Component OPRs"
            description="One row per team, one column per scoring component"
            rowCount={coprsTable.data.length}
            csvData={coprsCsv}
            filename={`${eventKey}_coprs.${format}`}
            format={format}
          />
        )}
      </ul>
    </div>
  );
}
