import { LoaderFunctionArgs } from '@remix-run/node';
import {
  ClientLoaderFunctionArgs,
  Params,
  json,
  useLoaderData,
} from '@remix-run/react';
import { useNavigate } from '@remix-run/react';
import { ApiReferenceReact } from '@scalar/api-reference-react';
import '@scalar/api-reference-react/style.css';
import { useEffect, useRef } from 'react';

function useDelegatedReactRouterLinks(nodeRef: React.RefObject<HTMLElement>) {
  let navigate = useNavigate();

  useEffect(() => {
    let node = nodeRef.current;
    let handler = (event: MouseEvent) => {
      if (!nodeRef.current) return;

      if (!(event.target instanceof HTMLElement)) return;

      let a = event.target.closest('a');

      if (
        a && // is anchor or has anchor parent
        a.hasAttribute('href') && // has an href
        a.host === window.location.host && // is internal
        event.button === 0 && // left click
        (!a.target || a.target === '_self') && // Let browser handle "target=_blank" etc.
        !(event.metaKey || event.altKey || event.ctrlKey || event.shiftKey) // not modified
      ) {
        event.preventDefault();
        let { pathname, search, hash } = a;
        navigate({ pathname, search, hash });
      }
    };

    if (!node) return;
    node.addEventListener('click', handler);

    return () => {
      node?.removeEventListener('click', handler);
    };
  }, [navigate, nodeRef]);
}
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
  let ref = useRef<HTMLDivElement>(null);

  useDelegatedReactRouterLinks(ref);

  return (
    <>
      <div ref={ref} style={{
        "--scalar-custom-header-height": "56px"
      } as React.CSSProperties}>
        <ApiReferenceReact
          configuration={{
            hideDarkModeToggle: true,
            spec: {
              url: path,
            },
          }}
        />
      </div>
    </>
  );
}
