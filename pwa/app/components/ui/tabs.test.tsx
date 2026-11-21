import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';

function renderTabs() {
  return render(
    <Tabs defaultValue="results">
      <TabsList className="group/list">
        <TabsTrigger value="results" className="group/trigger">
          Results
        </TabsTrigger>
        <TabsTrigger value="rankings">Rankings</TabsTrigger>
      </TabsList>
      <TabsContent value="results" className="group/content">
        Results panel
      </TabsContent>
      <TabsContent value="rankings">Rankings panel</TabsContent>
    </Tabs>,
  );
}

describe('Tabs', () => {
  test('renders the default tab and merges classes', () => {
    renderTabs();

    expect(screen.getByRole('tablist').className).toContain('group/list');
    const results = screen.getByRole('tab', { name: 'Results' });
    expect(results.className).toContain('group/trigger');
    expect(results.getAttribute('aria-selected')).toBe('true');
    expect(screen.getByText('Results panel').className).toContain(
      'group/content',
    );
    expect(screen.queryByText('Rankings panel')).toBeNull();
  });

  test('switches panels when another tab is clicked', () => {
    renderTabs();

    fireEvent.click(screen.getByRole('tab', { name: 'Rankings' }));

    expect(screen.getByText('Rankings panel')).toBeTruthy();
    expect(screen.queryByText('Results panel')).toBeNull();
  });
});
