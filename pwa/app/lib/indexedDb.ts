import { get, set } from 'idb-keyval';

import { Team, getTeams } from '~/api/v3';

interface IndexedDbDataInstance<T> {
  dateModified: string;
  data: T;
}

export interface IndexedDbData {
  teams: IndexedDbDataInstance<Team[]>;
}

export async function dbSetTeams(teams: Team[]) {
  return set('teams', { dateModified: new Date().toISOString(), data: teams });
}

export async function dbGetTeams(): Promise<Team[] | undefined> {
  return get<IndexedDbDataInstance<Team[]>>('teams').then((x) => x?.data);
}

export async function dbHasTeams(): Promise<boolean> {
  return dbGetTeams().then((x) => x !== undefined);
}

export async function dbPopulateTeams() {
  const allTeams: Team[] = [];

  let i = 0;
  while (i < 30) {
    const teams = await getTeams({ pageNum: i++ });
    if (teams.status !== 200) {
      break;
    }

    allTeams.push(...teams.data);
  }

  return dbSetTeams(allTeams);
}
