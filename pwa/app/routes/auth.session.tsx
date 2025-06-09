import { ActionFunction, redirect } from 'react-router';

import { adminAuth } from '~/firebase/firebase.server';
import { commitSession, getSession } from '~/lib/session.server';

export const action: ActionFunction = async ({ request }) => {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader?.startsWith('Bearer ')) {
    return Response.json({ error: 'No token provided' }, { status: 401 });
  }

  const token = authHeader.split(' ')[1];

  try {
    if (!adminAuth) {
      return Response.json({ error: 'No admin auth' }, { status: 401 });
    }

    const decoded = await adminAuth.verifyIdToken(token);

    const session = await getSession();
    session.set('uid', decoded.uid);
    session.set('email', decoded.email);
    session.set('token', token);

    return redirect('/account', {
      headers: {
        'Set-Cookie': await commitSession(session),
      },
    });
  } catch (err) {
    console.error(err);
    return Response.json({ error: 'Invalid token' }, { status: 403 });
  }
};
