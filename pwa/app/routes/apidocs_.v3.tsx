import { ApiReferenceReact } from '@scalar/api-reference-react';
import '@scalar/api-reference-react/style.css';
import { ReactRenderer } from '@scalar/react-renderer';
import type { ApiReferencePlugin } from '@scalar/types/api-reference';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/apidocs_/v3')({
  loader: async () => {
    const response = await fetch(
      'https://raw.githubusercontent.com/the-blue-alliance/the-blue-alliance/refs/heads/main/src/backend/web/static/swagger/api_v3.json',
    );
    const json = await response.json();
    return { json };
  },
  head: () => {
    return {
      meta: [
        {
          title: 'Read API (v3) - The Blue Alliance',
        },
        {
          name: 'description',
          content: 'Read API (v3) documentation for The Blue Alliance',
        },
      ],
    };
  },
  component: ApiDocsV3,
});

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

function ApiDocsV3(): React.JSX.Element {
  const { json } = Route.useLoaderData();

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
