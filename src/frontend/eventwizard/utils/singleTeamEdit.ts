export type SingleTeamEditAction = "add" | "remove";

export interface SingleTeamEditRequest {
  eventKey: string | null;
  teamKey: string;
  currentTeamKeys: string[];
  hasFetchedTeams: boolean;
}

/**
 * Validates adding or removing one team from an event's attending list and,
 * if the edit is valid, calls `onValid` with the new list of team keys.
 * Otherwise calls `onInvalid` with a message explaining why.
 *
 * The UI disables the Add/Remove buttons in the invalid cases, but this
 * still guards against acting on an unfetched or stale team list.
 */
export function editSingleTeam(
  action: SingleTeamEditAction,
  { eventKey, teamKey, currentTeamKeys, hasFetchedTeams }: SingleTeamEditRequest,
  onValid: (teamKeys: string[]) => void,
  onInvalid: (message: string) => void
): void {
  if (!hasFetchedTeams) {
    onInvalid(
      "Please fetch teams before modification to ensure up to date data"
    );
    return;
  }

  const keyIndex = currentTeamKeys.indexOf(teamKey);
  const isAttending = keyIndex >= 0;
  if (action === "add") {
    if (isAttending) {
      onInvalid(
        `Team ${teamKey} is already attending ${eventKey}. Re-fetch the team list if you know this is wrong.`
      );
      return;
    }
    onValid([...currentTeamKeys, teamKey]);
    return;
  }

  if (!isAttending) {
    onInvalid(
      `Team ${teamKey} is already not attending ${eventKey}. Re-fetch the team list if you know this is wrong.`
    );
    return;
  }
  const remainingTeamKeys = [...currentTeamKeys];
  remainingTeamKeys.splice(keyIndex, 1);
  onValid(remainingTeamKeys);
}
