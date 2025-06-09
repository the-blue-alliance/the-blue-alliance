import { createCookieSessionStorage } from 'react-router';

export const sessionStorage = createCookieSessionStorage({
  cookie: {
    name: '__session',
    secure: process.env.NODE_ENV === 'production',
    secrets: [import.meta.env.VITE_SESSION_SECRET],
    sameSite: 'lax',
    path: '/',
    httpOnly: true,
  },
});

export const { getSession, commitSession, destroySession } = sessionStorage;
