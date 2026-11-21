/**
 * The user's display name with a shared fallback, so the navbar menu and
 * the account page always show the same thing.
 */
export function getDisplayName(user: { displayName: string | null }): string {
  return user.displayName?.trim() ? user.displayName : 'TBA Account';
}

/**
 * Initials for the avatar fallback: "Greg Marra" → "GM", falling back to
 * the first letter of the email, then "?".
 */
export function getInitials(
  displayName: string | null | undefined,
  email: string | null | undefined,
): string {
  const names = (displayName ?? '').trim().split(/\s+/).filter(Boolean);
  if (names.length >= 2) {
    return `${names[0][0]}${names[names.length - 1][0]}`.toUpperCase();
  }
  if (names.length === 1) {
    return names[0][0].toUpperCase();
  }
  const emailFirst = (email ?? '').trim()[0];
  return emailFirst ? emailFirst.toUpperCase() : '?';
}
