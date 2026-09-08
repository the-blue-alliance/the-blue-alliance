export function shouldForceTokenRefresh(
  visibilityState: DocumentVisibilityState,
  hasUser: boolean,
): boolean {
  return hasUser && visibilityState === 'visible';
}
