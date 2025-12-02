import { ApiReferenceReact } from '@scalar/api-reference-react';
import '@scalar/api-reference-react/style.css';
import { ReactRenderer } from '@scalar/react-renderer';
import type { ApiReferencePlugin } from '@scalar/types/api-reference';
import { useLoaderData } from 'react-router';

export async function loader() {
  const response = await fetch(
    'https://www.thebluealliance.com/swagger/api_v3.json',
  );
  const json: unknown = await response.json();

  return new Response(JSON.stringify(json as Record<string, unknown>), {
    headers: {
      'Content-Type': 'application/json',
    },
  });
}

function ChangelogDisplay({ xChanges }: { xChanges: string }) {
  return (
    <div
      style={{
        background: 'var(--scalar-background-2)',
        borderRadius: '8px',
        padding: '16px',
        margin: '16px 0',
      }}
    >
      <h3 style={{ margin: '0 0 12px 0', fontSize: '18px', fontWeight: 600 }}>
        API Changelog
      </h3>
      <pre
        style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', margin: 0 }}
      >
        {JSON.stringify(xChanges, null, 2)}
      </pre>
    </div>
  );
}

const XChangesPlugin = (): ApiReferencePlugin => {
  return () => {
    return {
      name: 'changelog-plugin',
      extensions: [
        {
          name: 'x-changes',
          component: ChangelogDisplay,
          renderer: ReactRenderer,
        },
      ],
    };
  };
};

export default function ApiDocsV3(): React.JSX.Element {
  const json = useLoaderData<typeof loader>();

  return (
    <>
      <ApiReferenceReact
        configuration={{
          content: json,
          hideClientButton: true,
          hideDarkModeToggle: true,
          showDeveloperTools: 'never',
          operationsSorter: 'alpha',
          plugins: [XChangesPlugin()],
        }}
      />
    </>
  );
}
