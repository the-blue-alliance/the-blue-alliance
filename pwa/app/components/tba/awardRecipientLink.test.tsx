import { render } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import AwardRecipientLink from '~/components/tba/awardRecipientLink';

vi.mock(
  '~/components/tba/teamTooltip',
  () => import('~/testing/mocks/teamTooltip'),
);

describe('AwardRecipientLink', () => {
  test.each([
    [{ awardee: 'Jane Doe', team_key: 'frc254' }, 'Jane Doe (254)'],
    [{ awardee: 'Jane Doe', team_key: null }, 'Jane Doe'],
    [{ awardee: null, team_key: 'frc254' }, '254'],
    [{ awardee: null, team_key: null }, 'n/a'],
  ])('renders %o', (recipient, text) => {
    const { container } = render(
      <AwardRecipientLink recipient={recipient} year={2026} />,
    );
    expect(container.textContent).toBe(text);
  });
});
