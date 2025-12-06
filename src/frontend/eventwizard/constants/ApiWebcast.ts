export interface Webcast {
  type: string;
  channel: string;
  file?: string;
  date?: string;
  url?: string;
}

export type ApiWebcast = Webcast;
