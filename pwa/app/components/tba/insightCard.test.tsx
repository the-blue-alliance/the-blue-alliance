import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { InsightCard } from '~/components/tba/insightCard';

function Icon({ className }: { className?: string }) {
  return <svg data-testid="icon" className={className} />;
}

describe('InsightCard', () => {
  test('renders the header and toggles the expanded state', () => {
    render(
      <InsightCard icon={Icon} title="Most Wins" subtitle="All time">
        {(expanded) => <p>{expanded ? 'expanded' : 'collapsed'}</p>}
      </InsightCard>,
    );
    expect(screen.getByTestId('icon')).toBeTruthy();
    expect(screen.getByText('Most Wins')).toBeTruthy();
    expect(screen.getByText('All time')).toBeTruthy();
    expect(screen.getByText('collapsed')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Toggle' }));
    expect(screen.getByText('expanded')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Toggle' }));
    expect(screen.getByText('collapsed')).toBeTruthy();
  });

  test('omits the subtitle when absent', () => {
    const { container } = render(
      <InsightCard icon={Icon} title="Most Wins">
        {() => null}
      </InsightCard>,
    );
    expect(container.textContent).toBe('Most WinsToggle');
  });
});
