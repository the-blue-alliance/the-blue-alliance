import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { type Award, AwardType, type Event, EventType } from '~/api/tba/read';
import { AwardBanner, Banner } from '~/components/tba/banner';

function spans() {
  const banner = screen.getByTestId('award-banner');
  return Array.from(banner.querySelectorAll(':scope > div > span'));
}

describe('Banner', () => {
  test('renders an empty banner without a title, year, or description', () => {
    render(<Banner className="w-80" />);
    const banner = screen.getByTestId('award-banner');
    expect(banner.className).toContain('w-80');
    const [title, event] = spans();
    expect(title.textContent).toBe('');
    expect(title.className).toContain('text-[12cqw]');
    expect(event.textContent).toBe('');
    expect(event.className).toContain('text-[8.5cqw]');
  });

  test('italicizes FIRST and sizes text by length', () => {
    render(
      <Banner
        title="FIRST Impact Award"
        description="Silicon Valley Regional presented by Some Very Long Sponsor"
        year={2026}
      />,
    );
    const [title, year, event] = spans();
    expect(title.querySelector('em')?.textContent).toBe('FIRST');
    expect(title.querySelector('br')).toBeTruthy();
    expect(title.textContent).toBe('FIRSTIMPACT AWARD');
    expect(title.className).toContain('text-[8.5cqw]');
    expect(year.textContent).toBe('2026');
    expect(event.textContent).toBe(
      'SILICON VALLEY REGIONAL PRESENTED BY SOME VERY LONG SPONSOR',
    );
    expect(event.className).toContain('text-[7cqw]');
  });

  test.each([
    ['Winner', 'text-[12cqw]'],
    ['Engineering', 'text-[10cqw]'],
    ['Engineering Inspiration', 'text-[7cqw]'],
  ])('sizes a %s title', (title, size) => {
    render(<Banner title={title} description="Silicon Valley Regional Evt" />);
    const [titleSpan, event] = spans();
    expect(titleSpan.className).toContain(size);
    expect(event.className).toContain('text-[7.5cqw]');
  });
});

describe('AwardBanner', () => {
  test('names the award and event', () => {
    render(
      <AwardBanner
        award={{ award_type: AwardType.WINNER } as Award}
        event={
          {
            key: '2026casj',
            name: 'Silicon Valley Regional',
            short_name: 'Silicon Valley',
            event_type: EventType.REGIONAL,
            year: 2026,
            city: 'San Jose',
          } as Event
        }
      />,
    );
    const [title, year, event] = spans();
    expect(title.textContent).toBe('WINNER');
    expect(year.textContent).toBe('2026');
    expect(event.textContent).toBe('SILICON VALLEY REGIONAL');
  });
});
