import { render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { describe, expect, test } from 'vitest';

import { Divider } from '~/components/ui/divider';

describe('Divider', () => {
  test('renders its label over a centered rule and forwards the ref', () => {
    const ref = createRef<HTMLSpanElement>();

    render(
      <Divider ref={ref} className="my-4">
        or
      </Divider>,
    );

    expect(ref.current).not.toBeNull();
    expect(ref.current?.className).toContain('my-4');
    expect(ref.current?.className).toContain('justify-center');
    expect(screen.getByText('or').className).toContain('bg-background');
  });
});
