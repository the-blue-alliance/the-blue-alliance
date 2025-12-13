import { ApiReferenceReact } from '@scalar/api-reference-react';
import scalarCSS from '@scalar/api-reference-react/style.css?url';
import { ReactRenderer } from '@scalar/react-renderer';
import { createFileRoute } from '@tanstack/react-router';
import { useMemo } from 'react';

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '~/components/ui/accordion';

export const Route = createFileRoute('/apidocs_/v3')({
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

const ChangelogDisplay = ({ xChanges }: { xChanges: string }) => {
  const entries = useMemo(() => {
    // Match version + description pairs like "3.11.0: Description text"
    // Versions can look like "3.11.0" or "3.11.0 - 3.12.0"
    const pattern =
      /(\d+\.\d+(?:\.\d+)?(?:\s*-\s*\d+\.\d+(?:\.\d+)?)?)\s*:\s*([^]*?)(?=\s+\d+\.\d+|\s*$)/g;
    return Array.from(xChanges.matchAll(pattern), (match) => ({
      version: match[1].trim(),
      description: match[2].trim(),
    }));
  }, [xChanges]);

  return (
    <div
      style={{
        background: 'var(--scalar-background-2)',
        borderRadius: '8px',
        padding: '16px',
        margin: '16px 0',
      }}
    >
      <Accordion type="single" collapsible>
        <AccordionItem value="changelog">
          <AccordionTrigger
            style={{
              fontSize: '18px',
              fontWeight: 600,
              color: 'var(--scalar-color-1)',
            }}
          >
            API Changelog
          </AccordionTrigger>
          <AccordionContent>
            <div
              style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}
            >
              {entries.map((entry, index) => (
                <div
                  key={index}
                  style={{
                    padding: '8px',
                    background: 'var(--scalar-background-1)',
                    borderRadius: '4px',
                  }}
                >
                  <strong style={{ color: 'var(--scalar-color-1)' }}>
                    {entry.version}
                  </strong>
                  <div
                    style={{ marginTop: '4px', color: 'var(--scalar-color-2)' }}
                  >
                    {entry.description}
                  </div>
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
};

const XChangesPlugin = () => {
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
  return (
    <>
      <ApiReferenceReact
        configuration={{
          url: 'https://raw.githubusercontent.com/the-blue-alliance/the-blue-alliance/refs/heads/main/src/backend/web/static/swagger/api_v3.json',
          hideClientButton: true,
          hideDarkModeToggle: true,
          showDeveloperTools: 'never',
          operationsSorter: 'alpha',
          plugins: [XChangesPlugin()],
          searchHotKey: 'l', // to not conflict with the navbar search hotkey
          telemetry: false,
        }}
      />
      <link rel="stylesheet" href={scalarCSS} />
    </>
  );
}
