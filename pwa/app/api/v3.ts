/**
 * The Blue Alliance API v3
 * 3.9.5
 * DO NOT MODIFY - This file has been generated using oazapfts.
 * See https://www.npmjs.com/package/oazapfts
 */
import * as Oazapfts from '@oazapfts/runtime';
import * as QS from '@oazapfts/runtime/query';

export const defaults: Oazapfts.Defaults<Oazapfts.CustomHeaders> = {
  headers: {},
  baseUrl: 'https://www.thebluealliance.com/api/v3',
};
const oazapfts = Oazapfts.runtime(defaults);
export const servers = {
  server1: 'https://www.thebluealliance.com/api/v3',
};
export type ApiStatusAppVersion = {
  /** Internal use - Minimum application version required to correctly connect and process data. */
  min_app_version: number;
  /** Internal use - Latest application version available. */
  latest_app_version: number;
};
export type ApiStatus = {
  /** Year of the current FRC season. */
  current_season: number;
  /** Maximum FRC season year for valid queries. */
  max_season: number;
  /** True if the entire FMS API provided by FIRST is down. */
  is_datafeed_down: boolean;
  /** An array of strings containing event keys of any active events that are no longer updating. */
  down_events: string[];
  ios: ApiStatusAppVersion;
  android: ApiStatusAppVersion;
};
export type Team = {
  /** TBA team key with the format `frcXXXX` with `XXXX` representing the team number. */
  key: string;
  /** Official team number issued by FIRST. */
  team_number: number;
  /** Team nickname provided by FIRST. */
  nickname: string;
  /** Official long name registered with FIRST. */
  name: string;
  /** Name of team school or affilited group registered with FIRST. */
  school_name: string | null;
  /** City of team derived from parsing the address registered with FIRST. */
  city: string | null;
  /** State of team derived from parsing the address registered with FIRST. */
  state_prov: string | null;
  /** Country of team derived from parsing the address registered with FIRST. */
  country: string | null;
  /** Will be NULL, for future development. */
  address: string | null;
  /** Postal code from the team address. */
  postal_code: string | null;
  /** Will be NULL, for future development. */
  gmaps_place_id: string | null;
  /** Will be NULL, for future development. */
  gmaps_url: string | null;
  /** Will be NULL, for future development. */
  lat: number | null;
  /** Will be NULL, for future development. */
  lng: number | null;
  /** Will be NULL, for future development. */
  location_name: string | null;
  /** Official website associated with the team. */
  website?: string | null;
  /** First year the team officially competed. */
  rookie_year: number | null;
};
export type TeamSimple = {
  /** TBA team key with the format `frcXXXX` with `XXXX` representing the team number. */
  key: string;
  /** Official team number issued by FIRST. */
  team_number: number;
  /** Team nickname provided by FIRST. */
  nickname: string;
  /** Official long name registered with FIRST. */
  name: string;
  /** City of team derived from parsing the address registered with FIRST. */
  city: string | null;
  /** State of team derived from parsing the address registered with FIRST. */
  state_prov: string | null;
  /** Country of team derived from parsing the address registered with FIRST. */
  country: string | null;
};
export type DistrictList = {
  /** The short identifier for the district. */
  abbreviation: string;
  /** The long name for the district. */
  display_name: string;
  /** Key for this district, e.g. `2016ne`. */
  key: string;
  /** Year this district participated. */
  year: number;
};
export type Webcast = {
  /** Type of webcast, typically descriptive of the streaming provider. */
  type:
    | 'youtube'
    | 'twitch'
    | 'ustream'
    | 'iframe'
    | 'html5'
    | 'rtmp'
    | 'livestream'
    | 'direct_link'
    | 'mms'
    | 'justin'
    | 'stemtv'
    | 'dacast';
  /** Type specific channel information. May be the YouTube stream, or Twitch channel name. In the case of iframe types, contains HTML to embed the stream in an HTML iframe. */
  channel: string;
  /** The date for the webcast in `yyyy-mm-dd` format. May be null. */
  date?: string | null;
  /** File identification as may be required for some types. May be null. */
  file?: string | null;
};
export type Event = {
  /** TBA event key with the format yyyy[EVENT_CODE], where yyyy is the year, and EVENT_CODE is the event code of the event. */
  key: string;
  /** Official name of event on record either provided by FIRST or organizers of offseason event. */
  name: string;
  /** Event short code, as provided by FIRST. */
  event_code: string;
  /** Event Type, as defined here: https://github.com/the-blue-alliance/the-blue-alliance/blob/master/consts/event_type.py#L2 */
  event_type: number;
  district: DistrictList | null;
  /** City, town, village, etc. the event is located in. */
  city: string | null;
  /** State or Province the event is located in. */
  state_prov: string | null;
  /** Country the event is located in. */
  country: string | null;
  /** Event start date in `yyyy-mm-dd` format. */
  start_date: string;
  /** Event end date in `yyyy-mm-dd` format. */
  end_date: string;
  /** Year the event data is for. */
  year: number;
  /** Same as `name` but doesn't include event specifiers, such as 'Regional' or 'District'. May be null. */
  short_name: string | null;
  /** Event Type, eg Regional, District, or Offseason. */
  event_type_string: string;
  /** Week of the event relative to the first official season event, zero-indexed. Only valid for Regionals, Districts, and District Championships. Null otherwise. (Eg. A season with a week 0 'preseason' event does not count, and week 1 events will show 0 here. Seasons with a week 0.5 regional event will show week 0 for those event(s) and week 1 for week 1 events and so on.) */
  week: number | null;
  /** Address of the event's venue, if available. */
  address: string | null;
  /** Postal code from the event address. */
  postal_code: string | null;
  /** Google Maps Place ID for the event address. */
  gmaps_place_id: string | null;
  /** Link to address location on Google Maps. */
  gmaps_url: string | null;
  /** Latitude for the event address. */
  lat: number | null;
  /** Longitude for the event address. */
  lng: number | null;
  /** Name of the location at the address for the event, eg. Blue Alliance High School. */
  location_name: string | null;
  /** Timezone name. */
  timezone: string;
  /** The event's website, if any. */
  website: string | null;
  /** The FIRST internal Event ID, used to link to the event on the FRC webpage. */
  first_event_id: string | null;
  /** Public facing event code used by FIRST (on frc-events.firstinspires.org, for example) */
  first_event_code: string | null;
  webcasts: Webcast[];
  /** An array of event keys for the divisions at this event. */
  division_keys: string[];
  /** The TBA Event key that represents the event's parent. Used to link back to the event from a division event. It is also the inverse relation of `divison_keys`. */
  parent_event_key: string | null;
  /** Playoff Type, as defined here: https://github.com/the-blue-alliance/the-blue-alliance/blob/master/consts/playoff_type.py#L4, or null. */
  playoff_type: number | null;
  /** String representation of the `playoff_type`, or null. */
  playoff_type_string: string | null;
};
export type AwardRecipient = {
  /** The TBA team key for the team that was given the award. May be null. */
  team_key: string | null;
  /** The name of the individual given the award. May be null. */
  awardee: string | null;
};
export type Award = {
  /** The name of the award as provided by FIRST. May vary for the same award type. */
  name: string;
  /** Type of award given. See https://github.com/the-blue-alliance/the-blue-alliance/blob/master/consts/award_type.py#L6 */
  award_type: number;
  /** The event_key of the event the award was won at. */
  event_key: string;
  /** A list of recipients of the award at the event. May have either a team_key or an awardee, both, or neither (in the case the award wasn't awarded at the event). */
  recipient_list: AwardRecipient[];
  /** The year this award was won. */
  year: number;
};
export type History = {
  events: Event[];
  awards: Award[];
};
export type TeamRobot = {
  /** Year this robot competed in. */
  year: number;
  /** Name of the robot as provided by the team. */
  robot_name: string;
  /** Internal TBA identifier for this robot. */
  key: string;
  /** TBA team key for this robot. */
  team_key: string;
};
export type EventSimple = {
  /** TBA event key with the format yyyy[EVENT_CODE], where yyyy is the year, and EVENT_CODE is the event code of the event. */
  key: string;
  /** Official name of event on record either provided by FIRST or organizers of offseason event. */
  name: string;
  /** Event short code, as provided by FIRST. */
  event_code: string;
  /** Event Type, as defined here: https://github.com/the-blue-alliance/the-blue-alliance/blob/master/consts/event_type.py#L2 */
  event_type: number;
  district: DistrictList | null;
  /** City, town, village, etc. the event is located in. */
  city: string | null;
  /** State or Province the event is located in. */
  state_prov: string | null;
  /** Country the event is located in. */
  country: string | null;
  /** Event start date in `yyyy-mm-dd` format. */
  start_date: string;
  /** Event end date in `yyyy-mm-dd` format. */
  end_date: string;
  /** Year the event data is for. */
  year: number;
};
export type WltRecord = {
  /** Number of losses. */
  losses: number;
  /** Number of wins. */
  wins: number;
  /** Number of ties. */
  ties: number;
};
export type TeamEventStatusRank = {
  /** Number of teams ranked. */
  num_teams?: number;
  ranking?: {
    /** Number of matches played. */
    matches_played?: number;
    /** For some years, average qualification score. Can be null. */
    qual_average?: number;
    /** Ordered list of values used to determine the rank. See the `sort_order_info` property for the name of each value. */
    sort_orders?: number[];
    record?: WltRecord | null;
    /** Relative rank of this team. */
    rank?: number;
    /** Number of matches the team was disqualified for. */
    dq?: number;
    /** TBA team key for this rank. */
    team_key?: string;
  };
  /** Ordered list of names corresponding to the elements of the `sort_orders` array. */
  sort_order_info?: {
    /** The number of digits of precision used for this value, eg `2` would correspond to a value of `101.11` while `0` would correspond to `101`. */
    precision?: number;
    /** The descriptive name of the value used to sort the ranking. */
    name?: string;
  }[];
  status?: string;
};
export type TeamEventStatusAllianceBackup = {
  /** TBA key for the team replaced by the backup. */
  out?: string;
  /** TBA key for the backup team called in. */
  in?: string;
} | null;
export type TeamEventStatusAlliance = {
  /** Alliance name, may be null. */
  name?: string | null;
  /** Alliance number. */
  number: number;
  backup?: TeamEventStatusAllianceBackup;
  /** Order the team was picked in the alliance from 0-2, with 0 being alliance captain. */
  pick: number;
};
export type TeamEventStatusPlayoff = {
  /** The highest playoff level the team reached. */
  level?: 'qm' | 'ef' | 'qf' | 'sf' | 'f';
  current_level_record?: WltRecord | null;
  record?: WltRecord | null;
  /** Current competition status for the playoffs. */
  status?: 'won' | 'eliminated' | 'playing';
  /** The average match score during playoffs. Year specific. May be null if not relevant for a given year. */
  playoff_average?: number | null;
} | null;
export type TeamEventStatus = {
  qual?: TeamEventStatusRank;
  alliance?: TeamEventStatusAlliance;
  playoff?: TeamEventStatusPlayoff;
  /** An HTML formatted string suitable for display to the user containing the team's alliance pick status. */
  alliance_status_str?: string;
  /** An HTML formatter string suitable for display to the user containing the team's playoff status. */
  playoff_status_str?: string;
  /** An HTML formatted string suitable for display to the user containing the team's overall status summary of the event. */
  overall_status_str?: string;
  /** TBA match key for the next match the team is scheduled to play in at this event, or null. */
  next_match_key?: string;
  /** TBA match key for the last match the team played in at this event, or null. */
  last_match_key?: string;
};
export type MatchAlliance = {
  /** Score for this alliance. Will be null or -1 for an unplayed match. */
  score: number;
  team_keys: string[];
  /** TBA team keys (eg `frc254`) of any teams playing as a surrogate. */
  surrogate_team_keys: string[];
  /** TBA team keys (eg `frc254`) of any disqualified teams. */
  dq_team_keys: string[];
};
export type MatchScoreBreakdown2015Alliance = {
  auto_points?: number;
  teleop_points?: number;
  container_points?: number;
  tote_points?: number;
  litter_points?: number;
  foul_points?: number;
  adjust_points?: number;
  total_points?: number;
  foul_count?: number;
  tote_count_far?: number;
  tote_count_near?: number;
  tote_set?: boolean;
  tote_stack?: boolean;
  container_count_level1?: number;
  container_count_level2?: number;
  container_count_level3?: number;
  container_count_level4?: number;
  container_count_level5?: number;
  container_count_level6?: number;
  container_set?: boolean;
  litter_count_container?: number;
  litter_count_landfill?: number;
  litter_count_unprocessed?: number;
  robot_set?: boolean;
};
export type MatchScoreBreakdown2015 = {
  blue: MatchScoreBreakdown2015Alliance;
  red: MatchScoreBreakdown2015Alliance;
  coopertition: 'None' | 'Unknown' | 'Stack';
  coopertition_points: number;
};
export type MatchScoreBreakdown2016Alliance = {
  autoPoints?: number;
  teleopPoints?: number;
  breachPoints?: number;
  foulPoints?: number;
  capturePoints?: number;
  adjustPoints?: number;
  totalPoints?: number;
  robot1Auto?: 'Crossed' | 'Reached' | 'None';
  robot2Auto?: 'Crossed' | 'Reached' | 'None';
  robot3Auto?: 'Crossed' | 'Reached' | 'None';
  autoReachPoints?: number;
  autoCrossingPoints?: number;
  autoBouldersLow?: number;
  autoBouldersHigh?: number;
  autoBoulderPoints?: number;
  teleopCrossingPoints?: number;
  teleopBouldersLow?: number;
  teleopBouldersHigh?: number;
  teleopBoulderPoints?: number;
  teleopDefensesBreached?: boolean;
  teleopChallengePoints?: number;
  teleopScalePoints?: number;
  teleopTowerCaptured?: number;
  towerFaceA?: string;
  towerFaceB?: string;
  towerFaceC?: string;
  towerEndStrength?: number;
  techFoulCount?: number;
  foulCount?: number;
  position2?: string;
  position3?: string;
  position4?: string;
  position5?: string;
  position1crossings?: number;
  position2crossings?: number;
  position3crossings?: number;
  position4crossings?: number;
  position5crossings?: number;
};
export type MatchScoreBreakdown2016 = {
  blue: MatchScoreBreakdown2016Alliance;
  red: MatchScoreBreakdown2016Alliance;
};
export type MatchScoreBreakdown2017Alliance = {
  autoPoints?: number;
  teleopPoints?: number;
  foulPoints?: number;
  adjustPoints?: number;
  totalPoints?: number;
  robot1Auto?: 'Unknown' | 'Mobility' | 'None';
  robot2Auto?: 'Unknown' | 'Mobility' | 'None';
  robot3Auto?: 'Unknown' | 'Mobility' | 'None';
  rotor1Auto?: boolean;
  rotor2Auto?: boolean;
  autoFuelLow?: number;
  autoFuelHigh?: number;
  autoMobilityPoints?: number;
  autoRotorPoints?: number;
  autoFuelPoints?: number;
  teleopFuelPoints?: number;
  teleopFuelLow?: number;
  teleopFuelHigh?: number;
  teleopRotorPoints?: number;
  kPaRankingPointAchieved?: boolean;
  teleopTakeoffPoints?: number;
  kPaBonusPoints?: number;
  rotorBonusPoints?: number;
  rotor1Engaged?: boolean;
  rotor2Engaged?: boolean;
  rotor3Engaged?: boolean;
  rotor4Engaged?: boolean;
  rotorRankingPointAchieved?: boolean;
  techFoulCount?: number;
  foulCount?: number;
  touchpadNear?: string;
  touchpadMiddle?: string;
  touchpadFar?: string;
};
export type MatchScoreBreakdown2017 = {
  blue: MatchScoreBreakdown2017Alliance;
  red: MatchScoreBreakdown2017Alliance;
};
export type MatchScoreBreakdown2018Alliance = {
  adjustPoints?: number;
  autoOwnershipPoints?: number;
  autoPoints?: number;
  autoQuestRankingPoint?: boolean;
  autoRobot1?: string;
  autoRobot2?: string;
  autoRobot3?: string;
  autoRunPoints?: number;
  autoScaleOwnershipSec?: number;
  autoSwitchAtZero?: boolean;
  autoSwitchOwnershipSec?: number;
  endgamePoints?: number;
  endgameRobot1?: string;
  endgameRobot2?: string;
  endgameRobot3?: string;
  faceTheBossRankingPoint?: boolean;
  foulCount?: number;
  foulPoints?: number;
  rp?: number;
  techFoulCount?: number;
  teleopOwnershipPoints?: number;
  teleopPoints?: number;
  teleopScaleBoostSec?: number;
  teleopScaleForceSec?: number;
  teleopScaleOwnershipSec?: number;
  teleopSwitchBoostSec?: number;
  teleopSwitchForceSec?: number;
  teleopSwitchOwnershipSec?: number;
  totalPoints?: number;
  vaultBoostPlayed?: number;
  vaultBoostTotal?: number;
  vaultForcePlayed?: number;
  vaultForceTotal?: number;
  vaultLevitatePlayed?: number;
  vaultLevitateTotal?: number;
  vaultPoints?: number;
  /** Unofficial TBA-computed value of the FMS provided GameData given to the alliance teams at the start of the match. 3 Character String containing `L` and `R` only. The first character represents the near switch, the 2nd the scale, and the 3rd the far, opposing, switch from the alliance's perspective. An `L` in a position indicates the platform on the left will be lit for the alliance while an `R` will indicate the right platform will be lit for the alliance. See also [WPI Screen Steps](https://wpilib.screenstepslive.com/s/currentCS/m/getting_started/l/826278-2018-game-data-details). */
  tba_gameData?: string;
};
export type MatchScoreBreakdown2018 = {
  blue: MatchScoreBreakdown2018Alliance;
  red: MatchScoreBreakdown2018Alliance;
};
export type MatchScoreBreakdown2019Alliance = {
  adjustPoints?: number;
  autoPoints?: number;
  bay1?: string;
  bay2?: string;
  bay3?: string;
  bay4?: string;
  bay5?: string;
  bay6?: string;
  bay7?: string;
  bay8?: string;
  cargoPoints?: number;
  completeRocketRankingPoint?: boolean;
  completedRocketFar?: boolean;
  completedRocketNear?: boolean;
  endgameRobot1?: string;
  endgameRobot2?: string;
  endgameRobot3?: string;
  foulCount?: number;
  foulPoints?: number;
  habClimbPoints?: number;
  habDockingRankingPoint?: boolean;
  habLineRobot1?: string;
  habLineRobot2?: string;
  habLineRobot3?: string;
  hatchPanelPoints?: number;
  lowLeftRocketFar?: string;
  lowLeftRocketNear?: string;
  lowRightRocketFar?: string;
  lowRightRocketNear?: string;
  midLeftRocketFar?: string;
  midLeftRocketNear?: string;
  midRightRocketFar?: string;
  midRightRocketNear?: string;
  preMatchBay1?: string;
  preMatchBay2?: string;
  preMatchBay3?: string;
  preMatchBay6?: string;
  preMatchBay7?: string;
  preMatchBay8?: string;
  preMatchLevelRobot1?: string;
  preMatchLevelRobot2?: string;
  preMatchLevelRobot3?: string;
  rp?: number;
  sandStormBonusPoints?: number;
  techFoulCount?: number;
  teleopPoints?: number;
  topLeftRocketFar?: string;
  topLeftRocketNear?: string;
  topRightRocketFar?: string;
  topRightRocketNear?: string;
  totalPoints?: number;
};
export type MatchScoreBreakdown2019 = {
  blue: MatchScoreBreakdown2019Alliance;
  red: MatchScoreBreakdown2019Alliance;
};
export type MatchScoreBreakdown2020Alliance = {
  initLineRobot1?: string;
  endgameRobot1?: string;
  initLineRobot2?: string;
  endgameRobot2?: string;
  initLineRobot3?: string;
  endgameRobot3?: string;
  autoCellsBottom?: number;
  autoCellsOuter?: number;
  autoCellsInner?: number;
  teleopCellsBottom?: number;
  teleopCellsOuter?: number;
  teleopCellsInner?: number;
  stage1Activated?: boolean;
  stage2Activated?: boolean;
  stage3Activated?: boolean;
  stage3TargetColor?: string;
  endgameRungIsLevel?: string;
  autoInitLinePoints?: number;
  autoCellPoints?: number;
  autoPoints?: number;
  teleopCellPoints?: number;
  controlPanelPoints?: number;
  endgamePoints?: number;
  teleopPoints?: number;
  shieldOperationalRankingPoint?: boolean;
  shieldEnergizedRankingPoint?: boolean;
  /** Unofficial TBA-computed value that indicates whether the shieldEnergizedRankingPoint was earned normally or awarded due to a foul. */
  tba_shieldEnergizedRankingPointFromFoul?: boolean;
  /** Unofficial TBA-computed value that counts the number of robots who were hanging at the end of the match. */
  tba_numRobotsHanging?: number;
  foulCount?: number;
  techFoulCount?: number;
  adjustPoints?: number;
  foulPoints?: number;
  rp?: number;
  totalPoints?: number;
};
export type MatchScoreBreakdown2020 = {
  blue: MatchScoreBreakdown2020Alliance;
  red: MatchScoreBreakdown2020Alliance;
};
export type MatchScoreBreakdown2022Alliance = {
  taxiRobot1?: 'Yes' | 'No';
  endgameRobot1?: 'Traversal' | 'High' | 'Mid' | 'Low' | 'None';
  taxiRobot2?: 'Yes' | 'No';
  endgameRobot2?: 'Traversal' | 'High' | 'Mid' | 'Low' | 'None';
  taxiRobot3?: 'Yes' | 'No';
  endgameRobot3?: 'Traversal' | 'High' | 'Mid' | 'Low' | 'None';
  autoCargoLowerNear?: number;
  autoCargoLowerFar?: number;
  autoCargoLowerBlue?: number;
  autoCargoLowerRed?: number;
  autoCargoUpperNear?: number;
  autoCargoUpperFar?: number;
  autoCargoUpperBlue?: number;
  autoCargoUpperRed?: number;
  autoCargoTotal?: number;
  teleopCargoLowerNear?: number;
  teleopCargoLowerFar?: number;
  teleopCargoLowerBlue?: number;
  teleopCargoLowerRed?: number;
  teleopCargoUpperNear?: number;
  teleopCargoUpperFar?: number;
  teleopCargoUpperBlue?: number;
  teleopCargoUpperRed?: number;
  teleopCargoTotal?: number;
  matchCargoTotal?: number;
  autoTaxiPoints?: number;
  autoCargoPoints?: number;
  autoPoints?: number;
  quintetAchieved?: boolean;
  teleopCargoPoints?: number;
  endgamePoints?: number;
  teleopPoints?: number;
  cargoBonusRankingPoint?: boolean;
  hangarBonusRankingPoint?: boolean;
  foulCount?: number;
  techFoulCount?: number;
  adjustPoints?: number;
  foulPoints?: number;
  rp?: number;
  totalPoints?: number;
};
export type MatchScoreBreakdown2022 = {
  blue: MatchScoreBreakdown2022Alliance;
  red: MatchScoreBreakdown2022Alliance;
};
export type MatchScoreBreakdown2023Alliance = {
  activationBonusAchieved?: boolean;
  adjustPoints?: number;
  autoBridgeState?: 'NotLevel' | 'Level';
  autoChargeStationPoints?: number;
  autoChargeStationRobot1?: 'None' | 'Docked';
  autoChargeStationRobot2?: 'None' | 'Docked';
  autoChargeStationRobot3?: 'None' | 'Docked';
  autoDocked?: boolean;
  autoCommunity?: {
    B: ('None' | 'Cone' | 'Cube')[];
    M: ('None' | 'Cone' | 'Cube')[];
    T: ('None' | 'Cone' | 'Cube')[];
  };
  autoGamePieceCount?: number;
  autoGamePiecePoints?: number;
  autoMobilityPoints?: number;
  mobilityRobot1?: 'Yes' | 'No';
  mobilityRobot2?: 'Yes' | 'No';
  mobilityRobot3?: 'Yes' | 'No';
  autoPoints?: number;
  coopGamePieceCount?: number;
  coopertitionCriteriaMet?: boolean;
  endGameBridgeState?: 'NotLevel' | 'Level';
  endGameChargeStationPoints?: number;
  endGameChargeStationRobot1?: 'None' | 'Docked';
  endGameChargeStationRobot2?: 'None' | 'Docked';
  endGameChargeStationRobot3?: 'None' | 'Docked';
  endGameParkPoints?: number;
  extraGamePieceCount?: number;
  foulCount?: number;
  foulPoints?: number;
  techFoulCount?: number;
  linkPoints?: number;
  links?: {
    nodes: ('None' | 'Cone' | 'Cube')[];
    row: 'Bottom' | 'Mid' | 'Top';
  }[];
  sustainabilityBonusAchieved?: boolean;
  teleopCommunity?: {
    B: ('None' | 'Cone' | 'Cube')[];
    M: ('None' | 'Cone' | 'Cube')[];
    T: ('None' | 'Cone' | 'Cube')[];
  };
  teleopGamePieceCount?: number;
  teleopGamePiecePoints?: number;
  totalChargeStationPoints?: number;
  teleopPoints?: number;
  rp?: number;
  totalPoints?: number;
};
export type MatchScoreBreakdown2023 = {
  blue: MatchScoreBreakdown2023Alliance;
  red: MatchScoreBreakdown2023Alliance;
};
export type MatchScoreBreakdown2024Alliance = {
  adjustPoints?: number;
  autoAmpNoteCount?: number;
  autoAmpNotePoints?: number;
  autoLeavePoints?: number;
  autoLineRobot1?: string;
  autoLineRobot2?: string;
  autoLineRobot3?: string;
  autoPoints?: number;
  autoSpeakerNoteCount?: number;
  autoSpeakerNotePoints?: number;
  autoTotalNotePoints?: number;
  coopNotePlayed?: boolean;
  coopertitionBonusAchieved?: boolean;
  coopertitionCriteriaMet?: boolean;
  endGameHarmonyPoints?: number;
  endGameNoteInTrapPoints?: number;
  endGameOnStagePoints?: number;
  endGameParkPoints?: number;
  endGameRobot1?: string;
  endGameRobot2?: string;
  endGameRobot3?: string;
  endGameSpotLightBonusPoints?: number;
  endGameTotalStagePoints?: number;
  ensembleBonusAchieved?: boolean;
  ensembleBonusOnStageRobotsThreshold?: number;
  ensembleBonusStagePointsThreshold?: number;
  foulCount?: number;
  foulPoints?: number;
  g206Penalty?: boolean;
  g408Penalty?: boolean;
  g424Penalty?: boolean;
  melodyBonusAchieved?: boolean;
  melodyBonusThreshold?: number;
  melodyBonusThresholdCoop?: number;
  melodyBonusThresholdNonCoop?: number;
  micCenterStage?: boolean;
  micStageLeft?: boolean;
  micStageRight?: boolean;
  rp?: number;
  techFoulCount?: number;
  teleopAmpNoteCount?: number;
  teleopAmpNotePoints?: number;
  teleopPoints?: number;
  teleopSpeakerNoteAmplifiedCount?: number;
  teleopSpeakerNoteAmplifiedPoints?: number;
  teleopSpeakerNoteCount?: number;
  teleopSpeakerNotePoints?: number;
  teleopTotalNotePoints?: number;
  totalPoints?: number;
  trapCenterStage?: boolean;
  trapStageLeft?: boolean;
  trapStageRight?: boolean;
};
export type MatchScoreBreakdown2024 = {
  blue: MatchScoreBreakdown2024Alliance;
  red: MatchScoreBreakdown2024Alliance;
};
export type Match = {
  /** TBA match key with the format `yyyy[EVENT_CODE]_[COMP_LEVEL]m[MATCH_NUMBER]`, where `yyyy` is the year, and `EVENT_CODE` is the event code of the event, `COMP_LEVEL` is (qm, ef, qf, sf, f), and `MATCH_NUMBER` is the match number in the competition level. A set number may be appended to the competition level if more than one match in required per set. */
  key: string;
  /** The competition level the match was played at. */
  comp_level: 'qm' | 'ef' | 'qf' | 'sf' | 'f';
  /** The set number in a series of matches where more than one match is required in the match series. */
  set_number: number;
  /** The match number of the match in the competition level. */
  match_number: number;
  /** A list of alliances, the teams on the alliances, and their score. */
  alliances: {
    red: MatchAlliance;
    blue: MatchAlliance;
  };
  /** The color (red/blue) of the winning alliance. Will contain an empty string in the event of no winner, or a tie. */
  winning_alliance: 'red' | 'blue' | '';
  /** Event key of the event the match was played at. */
  event_key: string;
  /** UNIX timestamp (seconds since 1-Jan-1970 00:00:00) of the scheduled match time, as taken from the published schedule. */
  time: number | null;
  /** UNIX timestamp (seconds since 1-Jan-1970 00:00:00) of actual match start time. */
  actual_time: number | null;
  /** UNIX timestamp (seconds since 1-Jan-1970 00:00:00) of the TBA predicted match start time. */
  predicted_time: number | null;
  /** UNIX timestamp (seconds since 1-Jan-1970 00:00:00) when the match result was posted. */
  post_result_time: number | null;
  /** Score breakdown for auto, teleop, etc. points. Varies from year to year. May be null. */
  score_breakdown:
    | (
        | MatchScoreBreakdown2015
        | MatchScoreBreakdown2016
        | MatchScoreBreakdown2017
        | MatchScoreBreakdown2018
        | MatchScoreBreakdown2019
        | MatchScoreBreakdown2020
        | MatchScoreBreakdown2022
        | MatchScoreBreakdown2023
        | MatchScoreBreakdown2024
      )
    | null;
  /** Array of video objects associated with this match. */
  videos: {
    /** Can be one of 'youtube' or 'tba' */
    type: string;
    /** Unique key representing this video */
    key: string;
  }[];
};
export type MatchSimple = {
  /** TBA match key with the format `yyyy[EVENT_CODE]_[COMP_LEVEL]m[MATCH_NUMBER]`, where `yyyy` is the year, and `EVENT_CODE` is the event code of the event, `COMP_LEVEL` is (qm, ef, qf, sf, f), and `MATCH_NUMBER` is the match number in the competition level. A set number may append the competition level if more than one match in required per set. */
  key: string;
  /** The competition level the match was played at. */
  comp_level: 'qm' | 'ef' | 'qf' | 'sf' | 'f';
  /** The set number in a series of matches where more than one match is required in the match series. */
  set_number: number;
  /** The match number of the match in the competition level. */
  match_number: number;
  /** A list of alliances, the teams on the alliances, and their score. */
  alliances: {
    red: MatchAlliance;
    blue: MatchAlliance;
  };
  /** The color (red/blue) of the winning alliance. Will contain an empty string in the event of no winner, or a tie. */
  winning_alliance: 'red' | 'blue' | '';
  /** Event key of the event the match was played at. */
  event_key: string;
  /** UNIX timestamp (seconds since 1-Jan-1970 00:00:00) of the scheduled match time, as taken from the published schedule. */
  time: number | null;
  /** UNIX timestamp (seconds since 1-Jan-1970 00:00:00) of the TBA predicted match start time. */
  predicted_time: number | null;
  /** UNIX timestamp (seconds since 1-Jan-1970 00:00:00) of actual match start time. */
  actual_time: number | null;
};
export type Media = {
  /** String type of the media element. */
  type:
    | 'youtube'
    | 'cdphotothread'
    | 'imgur'
    | 'facebook-profile'
    | 'youtube-channel'
    | 'twitter-profile'
    | 'github-profile'
    | 'instagram-profile'
    | 'periscope-profile'
    | 'gitlab-profile'
    | 'grabcad'
    | 'instagram-image'
    | 'external-link'
    | 'avatar';
  /** The key used to identify this media on the media site. */
  foreign_key: string;
  /** If required, a JSON dict of additional media information. */
  details?: {
    [key: string]: any;
  };
  /** True if the media is of high quality. */
  preferred?: boolean;
  /** List of teams that this media belongs to. Most likely length 1. */
  team_keys: string[];
  /** Direct URL to the media. */
  direct_url?: string;
  /** The URL that leads to the full web page for the media, if one exists. */
  view_url?: string;
};
export type EliminationAlliance = {
  /** Alliance name, may be null. */
  name?: string | null;
  /** Backup team called in, may be null. */
  backup?: {
    /** Team key that was called in as the backup. */
    in: string;
    /** Team key that was replaced by the backup team. */
    out: string;
  } | null;
  /** List of teams that declined the alliance. */
  declines: string[];
  /** List of team keys picked for the alliance. First pick is captain. */
  picks: string[];
  status?: {
    playoff_average?: number;
    level?: string;
    record?: WltRecord | null;
    current_level_record?: WltRecord | null;
    status?: string;
  };
};
export type EventInsights = {
  /** Inights for the qualification round of an event */
  qual?: {};
  /** Insights for the playoff round of an event */
  playoff?: {};
};
export type EventOpRs = {
  /** A key-value pair with team key (eg `frc254`) as key and OPR as value. */
  oprs?: {
    [key: string]: number;
  };
  /** A key-value pair with team key (eg `frc254`) as key and DPR as value. */
  dprs?: {
    [key: string]: number;
  };
  /** A key-value pair with team key (eg `frc254`) as key and CCWM as value. */
  ccwms?: {
    [key: string]: number;
  };
};
export type EventCopRs = {
  [key: string]: {
    [key: string]: number;
  };
};
export type EventPredictions = object;
export type EventRanking = {
  /** List of rankings at the event. */
  rankings: {
    /** Number of matches played by this team. */
    matches_played: number;
    /** The average match score during qualifications. Year specific. May be null if not relevant for a given year. */
    qual_average: number | null;
    /** Additional special data on the team's performance calculated by TBA. */
    extra_stats: number[];
    /** Additional year-specific information, may be null. See parent `sort_order_info` for details. */
    sort_orders: number[] | null;
    record: WltRecord | null;
    /** The team's rank at the event as provided by FIRST. */
    rank: number;
    /** Number of times disqualified. */
    dq: number;
    /** The team with this rank. */
    team_key: string;
  }[];
  /** List of special TBA-generated values provided in the `extra_stats` array for each item. */
  extra_stats_info: {
    /** Integer expressing the number of digits of precision in the number provided in `sort_orders`. */
    precision: number;
    /** Name of the field used in the `extra_stats` array. */
    name: string;
  }[];
  /** List of year-specific values provided in the `sort_orders` array for each team. */
  sort_order_info: {
    /** Integer expressing the number of digits of precision in the number provided in `sort_orders`. */
    precision: number;
    /** Name of the field used in the `sort_order` array. */
    name: string;
  }[];
};
export type EventDistrictPoints = {
  /** Points gained for each team at the event. Stored as a key-value pair with the team key as the key, and an object describing the points as its value. */
  points: {
    [key: string]: {
      /** Total points awarded at this event. */
      total: number;
      /** Points awarded for alliance selection */
      alliance_points: number;
      /** Points awarded for elimination match performance. */
      elim_points: number;
      /** Points awarded for event awards. */
      award_points: number;
      /** Points awarded for qualification match performance. */
      qual_points: number;
    };
  };
  /** Tiebreaker values for each team at the event. Stored as a key-value pair with the team key as the key, and an object describing the tiebreaker elements as its value. */
  tiebreakers?: {
    [key: string]: {
      highest_qual_scores?: number[];
      qual_wins?: number;
    };
  };
};
export type ZebraTeam = {
  /** The TBA team key for the Zebra MotionWorks data. */
  team_key: string;
  /** A list containing doubles and nulls representing a teams X position in feet at the corresponding timestamp. A null value represents no tracking data for a given timestamp. */
  xs: number[];
  /** A list containing doubles and nulls representing a teams Y position in feet at the corresponding timestamp. A null value represents no tracking data for a given timestamp. */
  ys: number[];
};
export type Zebra = {
  /** TBA match key with the format `yyyy[EVENT_CODE]_[COMP_LEVEL]m[MATCH_NUMBER]`, where `yyyy` is the year, and `EVENT_CODE` is the event code of the event, `COMP_LEVEL` is (qm, ef, qf, sf, f), and `MATCH_NUMBER` is the match number in the competition level. A set number may be appended to the competition level if more than one match in required per set. */
  key: string;
  /** A list of relative timestamps for each data point. Each timestamp will correspond to the X and Y value at the same index in a team xs and ys arrays. `times`, all teams `xs` and all teams `ys` are guarenteed to be the same length. */
  times: number[];
  alliances: {
    /** Zebra MotionWorks data for teams on the red alliance */
    red?: ZebraTeam[];
    /** Zebra data for teams on the blue alliance */
    blue?: ZebraTeam[];
  };
};
export type DistrictRanking = {
  /** TBA team key for the team. */
  team_key: string;
  /** Numerical rank of the team, 1 being top rank. */
  rank: number;
  /** Any points added to a team as a result of the rookie bonus. */
  rookie_bonus?: number;
  /** Total district points for the team. */
  point_total: number;
  /** List of events that contributed to the point total for the team. */
  event_points?: {
    /** `true` if this event is a District Championship event. */
    district_cmp: boolean;
    /** Total points awarded at this event. */
    total: number;
    /** Points awarded for alliance selection. */
    alliance_points: number;
    /** Points awarded for elimination match performance. */
    elim_points: number;
    /** Points awarded for event awards. */
    award_points: number;
    /** TBA Event key for this event. */
    event_key: string;
    /** Points awarded for qualification match performance. */
    qual_points: number;
  }[];
};
export type LeaderboardInsight = {
  data: {
    rankings: {
      /** Value of the insight that the corresponding team/event/matches have, e.g. number of blue banners, or number of matches played. */
      value: number;
      /** Team/Event/Match keys that have the corresponding value. */
      keys: string[];
    }[];
    /** What type of key is used in the rankings; either 'team', 'event', or 'match'. */
    key_type: 'team' | 'event' | 'match';
  };
  /** Name of the insight. */
  name: string;
  /** Year the insight was measured in (year=0 for overall insights). */
  year: number;
};
/**
 * Returns API status, and TBA status information.
 */
export function getStatus(
  {
    ifNoneMatch,
  }: {
    ifNoneMatch?: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: ApiStatus;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >('/status', {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of `Team` objects, paginated in groups of 500.
 */
export function getTeams(
  {
    ifNoneMatch,
    pageNum,
  }: {
    ifNoneMatch?: string;
    pageNum: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Team[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/teams/${encodeURIComponent(pageNum)}`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of short form `Team_Simple` objects, paginated in groups of 500.
 */
export function getTeamsSimple(
  {
    ifNoneMatch,
    pageNum,
  }: {
    ifNoneMatch?: string;
    pageNum: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: TeamSimple[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/teams/${encodeURIComponent(pageNum)}/simple`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of Team keys, paginated in groups of 500. (Note, each page will not have 500 teams, but will include the teams within that range of 500.)
 */
export function getTeamsKeys(
  {
    ifNoneMatch,
    pageNum,
  }: {
    ifNoneMatch?: string;
    pageNum: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/teams/${encodeURIComponent(pageNum)}/keys`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of `Team` objects that competed in the given year, paginated in groups of 500.
 */
export function getTeamsByYear(
  {
    ifNoneMatch,
    year,
    pageNum,
  }: {
    ifNoneMatch?: string;
    year: number;
    pageNum: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Team[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/teams/${encodeURIComponent(year)}/${encodeURIComponent(pageNum)}`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of short form `Team_Simple` objects that competed in the given year, paginated in groups of 500.
 */
export function getTeamsByYearSimple(
  {
    ifNoneMatch,
    year,
    pageNum,
  }: {
    ifNoneMatch?: string;
    year: number;
    pageNum: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: TeamSimple[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/teams/${encodeURIComponent(year)}/${encodeURIComponent(pageNum)}/simple`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a list Team Keys that competed in the given year, paginated in groups of 500.
 */
export function getTeamsByYearKeys(
  {
    ifNoneMatch,
    year,
    pageNum,
  }: {
    ifNoneMatch?: string;
    year: number;
    pageNum: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/teams/${encodeURIComponent(year)}/${encodeURIComponent(pageNum)}/keys`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a `Team` object for the team referenced by the given key.
 */
export function getTeam(
  {
    ifNoneMatch,
    teamKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Team;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a `Team_Simple` object for the team referenced by the given key.
 */
export function getTeamSimple(
  {
    ifNoneMatch,
    teamKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: TeamSimple;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/simple`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets the history for the team referenced by the given key, including their events and awards.
 */
export function getTeamHistory(
  {
    ifNoneMatch,
    teamKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: History;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/history`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of years in which the team participated in at least one competition.
 */
export function getTeamYearsParticipated(
  {
    ifNoneMatch,
    teamKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: number[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/years_participated`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets an array of districts representing each year the team was in a district. Will return an empty array if the team was never in a district.
 */
export function getTeamDistricts(
  {
    ifNoneMatch,
    teamKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: DistrictList[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/districts`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of year and robot name pairs for each year that a robot name was provided. Will return an empty array if the team has never named a robot.
 */
export function getTeamRobots(
  {
    ifNoneMatch,
    teamKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: TeamRobot[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/robots`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of all events this team has competed at.
 */
export function getTeamEvents(
  {
    ifNoneMatch,
    teamKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Event[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/events`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a short-form list of all events this team has competed at.
 */
export function getTeamEventsSimple(
  {
    ifNoneMatch,
    teamKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EventSimple[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/events/simple`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of the event keys for all events this team has competed at.
 */
export function getTeamEventsKeys(
  {
    ifNoneMatch,
    teamKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/events/keys`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of events this team has competed at in the given year.
 */
export function getTeamEventsByYear(
  {
    ifNoneMatch,
    teamKey,
    year,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Event[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/events/${encodeURIComponent(year)}`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a short-form list of events this team has competed at in the given year.
 */
export function getTeamEventsByYearSimple(
  {
    ifNoneMatch,
    teamKey,
    year,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EventSimple[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/events/${encodeURIComponent(year)}/simple`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a list of the event keys for events this team has competed at in the given year.
 */
export function getTeamEventsByYearKeys(
  {
    ifNoneMatch,
    teamKey,
    year,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/events/${encodeURIComponent(year)}/keys`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a key-value list of the event statuses for events this team has competed at in the given year.
 */
export function getTeamEventsStatusesByYear(
  {
    ifNoneMatch,
    teamKey,
    year,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: {
          [key: string]: TeamEventStatus | null;
        };
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/events/${encodeURIComponent(year)}/statuses`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a list of matches for the given team and event.
 */
export function getTeamEventMatches(
  {
    ifNoneMatch,
    teamKey,
    eventKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Match[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/event/${encodeURIComponent(eventKey)}/matches`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a short-form list of matches for the given team and event.
 */
export function getTeamEventMatchesSimple(
  {
    ifNoneMatch,
    teamKey,
    eventKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Match[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/event/${encodeURIComponent(eventKey)}/matches/simple`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a list of match keys for matches for the given team and event.
 */
export function getTeamEventMatchesKeys(
  {
    ifNoneMatch,
    teamKey,
    eventKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/event/${encodeURIComponent(eventKey)}/matches/keys`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a list of awards the given team won at the given event.
 */
export function getTeamEventAwards(
  {
    ifNoneMatch,
    teamKey,
    eventKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Award[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/event/${encodeURIComponent(eventKey)}/awards`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets the competition rank and status of the team at the given event.
 */
export function getTeamEventStatus(
  {
    ifNoneMatch,
    teamKey,
    eventKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: TeamEventStatus | null;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/event/${encodeURIComponent(eventKey)}/status`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a list of awards the given team has won.
 */
export function getTeamAwards(
  {
    ifNoneMatch,
    teamKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Award[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/awards`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of awards the given team has won in a given year.
 */
export function getTeamAwardsByYear(
  {
    ifNoneMatch,
    teamKey,
    year,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Award[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/awards/${encodeURIComponent(year)}`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of matches for the given team and year.
 */
export function getTeamMatchesByYear(
  {
    ifNoneMatch,
    teamKey,
    year,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Match[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/matches/${encodeURIComponent(year)}`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a short-form list of matches for the given team and year.
 */
export function getTeamMatchesByYearSimple(
  {
    ifNoneMatch,
    teamKey,
    year,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: MatchSimple[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/matches/${encodeURIComponent(year)}/simple`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a list of match keys for matches for the given team and year.
 */
export function getTeamMatchesByYearKeys(
  {
    ifNoneMatch,
    teamKey,
    year,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/matches/${encodeURIComponent(year)}/keys`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a list of Media (videos / pictures) for the given team and year.
 */
export function getTeamMediaByYear(
  {
    ifNoneMatch,
    teamKey,
    year,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Media[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/media/${encodeURIComponent(year)}`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of Media (videos / pictures) for the given team and tag.
 */
export function getTeamMediaByTag(
  {
    ifNoneMatch,
    teamKey,
    mediaTag,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    mediaTag: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Media[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/media/tag/${encodeURIComponent(mediaTag)}`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a list of Media (videos / pictures) for the given team, tag and year.
 */
export function getTeamMediaByTagYear(
  {
    ifNoneMatch,
    teamKey,
    mediaTag,
    year,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
    mediaTag: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Media[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(
    `/team/${encodeURIComponent(teamKey)}/media/tag/${encodeURIComponent(mediaTag)}/${encodeURIComponent(year)}`,
    {
      ...opts,
      headers: oazapfts.mergeHeaders(opts?.headers, {
        'If-None-Match': ifNoneMatch,
      }),
    },
  );
}
/**
 * Gets a list of Media (social media) for the given team.
 */
export function getTeamSocialMedia(
  {
    ifNoneMatch,
    teamKey,
  }: {
    ifNoneMatch?: string;
    teamKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Media[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/team/${encodeURIComponent(teamKey)}/social_media`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of events in the given year.
 */
export function getEventsByYear(
  {
    ifNoneMatch,
    year,
  }: {
    ifNoneMatch?: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Event[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/events/${encodeURIComponent(year)}`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a short-form list of events in the given year.
 */
export function getEventsByYearSimple(
  {
    ifNoneMatch,
    year,
  }: {
    ifNoneMatch?: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EventSimple[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/events/${encodeURIComponent(year)}/simple`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of event keys in the given year.
 */
export function getEventsByYearKeys(
  {
    ifNoneMatch,
    year,
  }: {
    ifNoneMatch?: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/events/${encodeURIComponent(year)}/keys`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets an Event.
 */
export function getEvent(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Event;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a short-form Event.
 */
export function getEventSimple(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EventSimple;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/simple`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of Elimination Alliances for the given Event.
 */
export function getEventAlliances(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EliminationAlliance[] | null;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/alliances`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a set of Event-specific insights for the given Event.
 */
export function getEventInsights(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EventInsights | null;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/insights`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a set of Event OPRs (including OPR, DPR, and CCWM) for the given Event.
 */
export function getEventOpRs(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EventOpRs | null;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/oprs`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a set of Event Component OPRs for the given Event.
 */
export function getEventCopRs(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EventCopRs | null;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/coprs`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets information on TBA-generated predictions for the given Event. Contains year-specific information. *WARNING* This endpoint is currently under development and may change at any time.
 */
export function getEventPredictions(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EventPredictions | null;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/predictions`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of team rankings for the Event.
 */
export function getEventRankings(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EventRanking | null;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/rankings`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of team rankings for the Event.
 */
export function getEventDistrictPoints(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EventDistrictPoints | null;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/district_points`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of `Team` objects that competed in the given event.
 */
export function getEventTeams(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Team[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/teams`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a short-form list of `Team` objects that competed in the given event.
 */
export function getEventTeamsSimple(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: TeamSimple[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/teams/simple`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of `Team` keys that competed in the given event.
 */
export function getEventTeamsKeys(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/teams/keys`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a key-value list of the event statuses for teams competing at the given event.
 */
export function getEventTeamsStatuses(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: {
          [key: string]: TeamEventStatus | null;
        };
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/teams/statuses`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of matches for the given event.
 */
export function getEventMatches(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Match[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/matches`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a short-form list of matches for the given event.
 */
export function getEventMatchesSimple(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: MatchSimple[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/matches/simple`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of match keys for the given event.
 */
export function getEventMatchesKeys(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/matches/keys`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets an array of Match Keys for the given event key that have timeseries data. Returns an empty array if no matches have timeseries data.
 * *WARNING:* This is *not* official data, and is subject to a significant possibility of error, or missing data. Do not rely on this data for any purpose. In fact, pretend we made it up.
 * *WARNING:* This endpoint and corresponding data models are under *active development* and may change at any time, including in breaking ways.
 */
export function getEventMatchTimeseries(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/matches/timeseries`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of awards from the given event.
 */
export function getEventAwards(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Award[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/awards`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of media objects that correspond to teams at this event.
 */
export function getEventTeamMedia(
  {
    ifNoneMatch,
    eventKey,
  }: {
    ifNoneMatch?: string;
    eventKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Media[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/event/${encodeURIComponent(eventKey)}/team_media`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a `Match` object for the given match key.
 */
export function getMatch(
  {
    ifNoneMatch,
    matchKey,
  }: {
    ifNoneMatch?: string;
    matchKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Match;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/match/${encodeURIComponent(matchKey)}`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a short-form `Match` object for the given match key.
 */
export function getMatchSimple(
  {
    ifNoneMatch,
    matchKey,
  }: {
    ifNoneMatch?: string;
    matchKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: MatchSimple;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/match/${encodeURIComponent(matchKey)}/simple`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets an array of game-specific Match Timeseries objects for the given match key or an empty array if not available.
 * *WARNING:* This is *not* official data, and is subject to a significant possibility of error, or missing data. Do not rely on this data for any purpose. In fact, pretend we made it up.
 * *WARNING:* This endpoint and corresponding data models are under *active development* and may change at any time, including in breaking ways.
 */
export function getMatchTimeseries(
  {
    ifNoneMatch,
    matchKey,
  }: {
    ifNoneMatch?: string;
    matchKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: {}[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/match/${encodeURIComponent(matchKey)}/timeseries`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets Zebra MotionWorks data for a Match for the given match key.
 */
export function getMatchZebra(
  {
    ifNoneMatch,
    matchKey,
  }: {
    ifNoneMatch?: string;
    matchKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Zebra;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/match/${encodeURIComponent(matchKey)}/zebra_motionworks`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of districts and their corresponding district key, for the given year.
 */
export function getDistrictsByYear(
  {
    ifNoneMatch,
    year,
  }: {
    ifNoneMatch?: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: DistrictList[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/districts/${encodeURIComponent(year)}`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of events in the given district.
 */
export function getDistrictEvents(
  {
    ifNoneMatch,
    districtKey,
  }: {
    ifNoneMatch?: string;
    districtKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Event[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/district/${encodeURIComponent(districtKey)}/events`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a short-form list of events in the given district.
 */
export function getDistrictEventsSimple(
  {
    ifNoneMatch,
    districtKey,
  }: {
    ifNoneMatch?: string;
    districtKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: EventSimple[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/district/${encodeURIComponent(districtKey)}/events/simple`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of event keys for events in the given district.
 */
export function getDistrictEventsKeys(
  {
    ifNoneMatch,
    districtKey,
  }: {
    ifNoneMatch?: string;
    districtKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/district/${encodeURIComponent(districtKey)}/events/keys`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of `Team` objects that competed in events in the given district.
 */
export function getDistrictTeams(
  {
    ifNoneMatch,
    districtKey,
  }: {
    ifNoneMatch?: string;
    districtKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: Team[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/district/${encodeURIComponent(districtKey)}/teams`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a short-form list of `Team` objects that competed in events in the given district.
 */
export function getDistrictTeamsSimple(
  {
    ifNoneMatch,
    districtKey,
  }: {
    ifNoneMatch?: string;
    districtKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: TeamSimple[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/district/${encodeURIComponent(districtKey)}/teams/simple`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of `Team` objects that competed in events in the given district.
 */
export function getDistrictTeamsKeys(
  {
    ifNoneMatch,
    districtKey,
  }: {
    ifNoneMatch?: string;
    districtKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: string[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/district/${encodeURIComponent(districtKey)}/teams/keys`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of team district rankings for the given district.
 */
export function getDistrictRankings(
  {
    ifNoneMatch,
    districtKey,
  }: {
    ifNoneMatch?: string;
    districtKey: string;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: DistrictRanking[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/district/${encodeURIComponent(districtKey)}/rankings`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
/**
 * Gets a list of `LeaderboardInsight` objects from a specific year. Use year=0 for overall.
 */
export function getInsightsLeaderboardsYear(
  {
    ifNoneMatch,
    year,
  }: {
    ifNoneMatch?: string;
    year: number;
  },
  opts?: Oazapfts.RequestOpts,
) {
  return oazapfts.fetchJson<
    | {
        status: 200;
        data: LeaderboardInsight[];
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          /** Authorization error description. */
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >(`/insights/leaderboards/${encodeURIComponent(year)}`, {
    ...opts,
    headers: oazapfts.mergeHeaders(opts?.headers, {
      'If-None-Match': ifNoneMatch,
    }),
  });
}
