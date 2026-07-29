import {
  type AuthProvider,
  type User,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
} from 'firebase/auth';
import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import { flushSync } from 'react-dom';

import { auth } from '~/firebase/firebaseConfig';

export type AuthContextType = {
  isInitialLoading: boolean;
  login: (provider: AuthProvider) => Promise<void>;
  logout: () => Promise<void>;
  user: User | null;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthContextProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(auth?.currentUser ?? null);
  // Start loading so the initial render shows a loader instead of the signed-out
  // UI while Firebase asynchronously restores the persisted session. The server
  // renders this same loading state, so there is no hydration mismatch.
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  useEffect(() => {
    if (!auth) return;
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      flushSync(() => {
        setUser(user);
        setIsInitialLoading(false);
      });
    });
    return () => unsubscribe();
  }, []);

  const logout = useCallback(async () => {
    if (!auth) return;
    await signOut(auth);
    setUser(null);
    setIsInitialLoading(false);
  }, []);

  const login = useCallback(async (provider: AuthProvider) => {
    if (!auth) return;
    const result = await signInWithPopup(auth, provider);
    flushSync(() => {
      setUser(result.user);
      setIsInitialLoading(false);
    });
  }, []);

  return (
    <AuthContext.Provider value={{ isInitialLoading, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
