import { Webcast } from "./ApiWebcast";

export interface Event {
  key: string;
  playoff_type?: number;
  first_event_code?: string;
  webcasts?: Webcast[];
  remap_teams?: Record<string, string>;
}
