import { render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { describe, expect, test } from 'vitest';

import { TitledCard } from '~/components/tba/cards';

describe('TitledCard', () => {
  test('renders the title and subtitle and forwards the ref', () => {
    const ref = createRef<HTMLDivElement>();
    render(
      <TitledCard
        ref={ref}
        cardTitle="42"
        cardSubtitle="Wins"
        className="mt-7"
        data-testid="card"
      />,
    );
    const card = screen.getByTestId('card');
    expect(ref.current).toBe(card);
    expect(card.className).toContain('mt-7');
    expect(screen.getByText('42').tagName).toBe('DD');
    expect(screen.getByText('Wins').tagName).toBe('DT');
  });
});
