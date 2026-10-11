export function remapTeamKeys(
  keys: string[],
  remapTeams: Record<string, string> | null | undefined,
): string[] {
  if (!remapTeams) return keys;
  return [...new Set(keys.map((key) => remapTeams[key] ?? key))];
}
