import { ApiReferenceReact } from '@scalar/api-reference-react';
import '@scalar/api-reference-react/style.css';
import { useLoaderData } from 'react-router';

import { Route } from '.react-router/types/app/routes/+types/apidocs.$doc.($version)';

function loadData(params: Route.LoaderArgs['params']) {
  if (!params.doc) {
    throw new Response(null, {
      status: 404,
    });
  } else if (params.doc === 'v3') {
    return { path: '/swagger/api_v3.json' };
  } else if (params.doc === 'trusted' && params.version === 'v1') {
    return { path: '/swagger/api_trusted_v1.json' };
  } else {
    throw new Response(null, {
      status: 404,
    });
  }
}
export function loader({ params }: Route.LoaderArgs) {
  return loadData(params);
}

export function clientLoader({ params }: Route.ClientLoaderArgs) {
  return loadData(params);
}

export default function ApiDocsV3(): React.JSX.Element {
  const { path } = useLoaderData<typeof loader>();

  return (
    <>
      <div
        style={
          {
            '--scalar-custom-header-height': '56px',
          } as React.CSSProperties
        }
      >
        <ApiReferenceReact
          configuration={{
            hideDarkModeToggle: true,
            url: path,
          }}
        />
      </div>
    </>
  );
}
