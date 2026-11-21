import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { Badge, badgeVariants } from '~/components/ui/badge';

describe('Badge', () => {
  test('uses the default variant and merges classes', () => {
    render(<Badge className="mt-2">New</Badge>);

    const badge = screen.getByText('New');
    expect(badge.className).toContain('bg-primary');
    expect(badge.className).toContain('mt-2');
  });

  test('applies the requested variant', () => {
    render(<Badge variant="success">Done</Badge>);

    expect(screen.getByText('Done').className).toContain('bg-green-500');
    expect(badgeVariants({ variant: 'outline' })).toContain('text-foreground');
  });
});
