import { Webcast } from "./ApiWebcast";

export interface Event {
  key: string;
  playoff_type?: number;
  playoff_type_string?: string;
  first_event_code?: string;
  webcasts?: Webcast[];
  remap_teams?: Record<string, string>;
}

export type ApiEvent = Event;
