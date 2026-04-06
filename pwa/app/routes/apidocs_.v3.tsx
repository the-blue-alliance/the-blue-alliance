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
import { useTheme } from '~/lib/theme';

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
      links: [{ rel: 'stylesheet', href: scalarCSS }],
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
    <div className="my-4 rounded-lg bg-(--scalar-background-2) p-4">
      <Accordion type="single" collapsible>
        <AccordionItem value="changelog">
          <AccordionTrigger
            className="text-lg font-semibold text-(--scalar-color-1)"
          >
            API Changelog
          </AccordionTrigger>
          <AccordionContent>
            <div className="flex flex-col gap-3">
              {entries.map((entry, index) => (
                <div
                  key={index}
                  className="rounded bg-(--scalar-background-1) p-2"
                >
                  <strong className="text-(--scalar-color-1)">
                    {entry.version}
                  </strong>
                  <div className="mt-1 text-(--scalar-color-2)">
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
  const { resolvedTheme } = useTheme();
  return (
    // key forces a remount when the theme changes; Scalar's Vue internals don't
    // treat darkMode as reactive after initialization, so updateConfiguration
    // won't apply theme changes without a full remount.
    <ApiReferenceReact
      key={resolvedTheme}
      configuration={{
        url: 'https://raw.githubusercontent.com/the-blue-alliance/the-blue-alliance/refs/heads/main/src/backend/web/static/swagger/api_v3.json',
        hideClientButton: true,
        hideDarkModeToggle: true,
        darkMode: resolvedTheme === 'dark',
        showDeveloperTools: 'localhost',
        operationsSorter: 'alpha',
        plugins: [XChangesPlugin()],
        searchHotKey: 'l', // to not conflict with the navbar search hotkey
        telemetry: false,
        agent: { disabled: true },
        mcp: { disabled: true },
        authentication: {
          preferredSecurityScheme: 'apiKey',
          securitySchemes: {
            apiKey: {
              value: '',
            },
          },
        },
        defaultOpenAllTags: true,
        persistAuth: true,
        showOperationId: true,
      }}
    />
  );
}
