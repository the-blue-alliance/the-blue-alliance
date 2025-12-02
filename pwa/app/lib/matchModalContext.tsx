import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import { useBlocker } from 'react-router';

import { Event, Match } from '~/api/tba/read';

type MatchModalState = {
  match: Match;
  event: Event;
} | null;

const MatchModalContext = createContext<{
  state: MatchModalState;
  openMatch: (match: Match, event: Event) => void;
  closeMatch: () => void;
} | null>(null);

export function MatchModalProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [state, setState] = useState<MatchModalState>(null);

  const openMatch = useCallback((match: Match, event: Event) => {
    setState({ match, event });
    window.history.pushState(null, '', `/match/${match.key}`);
  }, []);

  // Close modal and go back when user explicitly closes (via X button or overlay click)
  const closeMatch = useCallback(() => {
    if (state !== null) {
      window.history.back();
    }
  }, [state]);

  // Listen for browser back navigation
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      setState(null);
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  return (
    <MatchModalContext.Provider value={{ state, openMatch, closeMatch }}>
      {children}
    </MatchModalContext.Provider>
  );
}

export function useMatchModal() {
  const context = useContext(MatchModalContext);
  if (!context) {
    throw new Error('useMatchModal must be used within a MatchModalProvider');
  }
  return context;
}
