import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import DetailEntity from '~/components/tba/detailEntity';

describe('DetailEntity', () => {
  test('renders the icon, children, and extra classes', () => {
    const { container } = render(
      <DetailEntity icon={<svg data-testid="icon" />} className="mt-7">
        Flint, MI
      </DetailEntity>,
    );
    expect(screen.getByTestId('icon')).toBeTruthy();
    expect(screen.getByText('Flint, MI').tagName).toBe('SPAN');
    expect(container.firstElementChild?.className).toContain('mt-7');
  });
});
