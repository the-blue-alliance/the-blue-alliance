import { redirect } from 'react-router';

import { destroySession, getSession } from '~/lib/session.server';

import { Route } from '.react-router/types/app/routes/+types/auth.logout';

export async function action({ request }: Route.ActionArgs) {
  const session = await getSession(request.headers.get('Cookie'));

  return redirect('/', {
    headers: {
      'Set-Cookie': await destroySession(session),
    },
  });
}
