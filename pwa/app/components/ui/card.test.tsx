import { render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { describe, expect, test } from 'vitest';

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';

describe('Card', () => {
  test('renders every section with merged classes and forwarded refs', () => {
    const cardRef = createRef<HTMLDivElement>();
    const titleRef = createRef<HTMLParagraphElement>();

    render(
      <Card ref={cardRef} className="group/card" data-testid="card">
        <CardHeader className="group/header" data-testid="header">
          <CardTitle ref={titleRef} className="group/title">
            Team 254
          </CardTitle>
          <CardDescription className="group/description">
            The Cheesy Poofs
          </CardDescription>
        </CardHeader>
        <CardContent className="group/content" data-testid="content">
          Body
        </CardContent>
        <CardFooter className="group/footer" data-testid="footer">
          Footer
        </CardFooter>
      </Card>,
    );

    expect(cardRef.current).toBe(screen.getByTestId('card'));
    expect(screen.getByTestId('card').className).toContain('group/card');
    expect(screen.getByTestId('card').className).toContain('rounded-xl');
    expect(screen.getByTestId('header').className).toContain('group/header');

    const title = screen.getByRole('heading', { level: 3, name: 'Team 254' });
    expect(titleRef.current).toBe(title);
    expect(title.className).toContain('group/title');

    const description = screen.getByText('The Cheesy Poofs');
    expect(description.tagName).toBe('P');
    expect(description.className).toContain('group/description');

    expect(screen.getByTestId('content').className).toContain('group/content');
    expect(screen.getByTestId('footer').className).toContain('group/footer');
  });
});
