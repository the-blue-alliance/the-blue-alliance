import { render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { describe, expect, test } from 'vitest';

import { Input } from '~/components/ui/input';

describe('Input', () => {
  test('forwards its ref, type, and merged classes', () => {
    const ref = createRef<HTMLInputElement>();
    render(
      <Input ref={ref} type="email" className="mt-2" placeholder="Email" />,
    );

    const input = screen.getByPlaceholderText('Email');
    expect(ref.current).toBe(input);
    expect(input.getAttribute('type')).toBe('email');
    expect(input.className).toContain('rounded-md');
    expect(input.className).toContain('mt-2');
    expect(Input.displayName).toBe('Input');
  });
});
