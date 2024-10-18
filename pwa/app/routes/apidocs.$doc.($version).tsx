import { LoaderFunctionArgs } from '@remix-run/node';
import { ClientLoaderFunctionArgs, Params, json, useLoaderData } from '@remix-run/react';
import { ApiReferenceReact } from '@scalar/api-reference-react';
import '@scalar/api-reference-react/style.css';

async function loadData(params: Params) {
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
export async function loader({ params }: LoaderFunctionArgs) {
  return json(await loadData(params));
}

export async function clientLoader({ params }: ClientLoaderFunctionArgs) {
  return await loadData(params);
}

export default function ApiDocsV3(): React.JSX.Element {
  const { path } = useLoaderData<typeof loader>();
  return (
    <>
      <ApiReferenceReact
        configuration={{
          hideDarkModeToggle: true,
          spec: {
            url: path,
          },
        }}
      />
    </>
  );
}
