import { User } from 'firebase/auth';
import { createContext, useContext, useState } from 'react';

import { auth } from '~/firebase/firebaseConfig';

const AuthContext = createContext<{
  user?: User;
}>({
  user: undefined,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | undefined>(undefined);

  auth.onAuthStateChanged((user) => {
    if (user) {
      setUser(user);
    } else {
      setUser(undefined);
    }
  });

  return (
    <AuthContext.Provider value={{ user }}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
