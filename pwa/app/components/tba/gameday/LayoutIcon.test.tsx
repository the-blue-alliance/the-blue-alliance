import { render } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { LayoutIcon } from '~/components/tba/gameday/LayoutIcon';
import { Layout, getLayoutById } from '~/lib/gameday/layouts';

describe('LayoutIcon', () => {
  test('draws the layout outline in the current color by default', () => {
    const { container } = render(
      <LayoutIcon layoutId={Layout.QUAD_VIEW} className="h-4" />,
    );

    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('fill')).toBe('currentColor');
    expect(svg?.getAttribute('class')).toBe('inline-block h-4');
    expect(container.querySelector('path')?.getAttribute('d')).toBe(
      getLayoutById(Layout.QUAD_VIEW)?.svgPath,
    );
  });

  test('accepts a fill color', () => {
    const { container } = render(
      <LayoutIcon layoutId={Layout.SINGLE_VIEW} color="white" />,
    );

    expect(container.querySelector('svg')?.getAttribute('fill')).toBe('white');
  });

  test('renders nothing for an unknown layout', () => {
    const { container } = render(<LayoutIcon layoutId={99} />);

    expect(container.innerHTML).toBe('');
  });
});
