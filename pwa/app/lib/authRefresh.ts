interface TokenRefreshUser {
  getIdToken: () => Promise<string>;
}

export function shouldRefreshToken(
  visibilityState: DocumentVisibilityState,
  hasUser: boolean,
): boolean {
  return hasUser && visibilityState === 'visible';
}

export function createTokenRefresher(
  getUser: () => TokenRefreshUser | null,
): () => Promise<string> | null {
  let pendingRefresh: Promise<string> | null = null;

  return () => {
    const user = getUser();
    if (!user) return null;

    pendingRefresh ??= user.getIdToken().finally(() => {
      pendingRefresh = null;
    });
    return pendingRefresh;
  };
}
