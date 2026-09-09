// @vitest-environment jsdom
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import type { ModelType } from '~/api/tba/mobile/types.gen';
import FavoriteButton from '~/components/tba/favoriteButton';

const { toggleFavoriteMock, useAuthMock, useMyTBAMock } = vi.hoisted(() => ({
  toggleFavoriteMock: vi.fn<() => void>(),
  useAuthMock: vi.fn<() => { user: object | null }>(),
  useMyTBAMock: vi.fn<
    (
      modelKey: string,
      modelType: number,
    ) => {
      isFavorite: boolean;
      toggleFavorite: () => void;
      isPending: boolean;
    }
  >(),
}));

vi.mock('~/components/tba/auth/auth', () => ({
  useAuth: useAuthMock,
}));

vi.mock('~/lib/hooks/useMyTBA', () => ({
  useMyTBA: useMyTBAMock,
}));

vi.mock('~/components/tba/auth/signInWithGoogleButton', () => ({
  default: () => <button>Sign in with Google</button>,
}));

vi.mock('~/components/tba/auth/signInWithAppleButton', () => ({
  default: () => <button>Sign in with Apple</button>,
}));

vi.mock('~icons/bi/star', () => ({
  default: () => <svg data-testid="outline-star" />,
}));

vi.mock('~icons/bi/star-fill', () => ({
  default: () => <svg data-testid="filled-star" />,
}));

vi.mock('~/components/ui/credenza', () => ({
  Credenza: ({ children, open }: { children: ReactNode; open?: boolean }) =>
    open ? children : null,
  CredenzaBody: ({ children }: { children: ReactNode }) => children,
  CredenzaContent: ({ children }: { children: ReactNode }) => (
    <dialog open>{children}</dialog>
  ),
  CredenzaDescription: ({ children }: { children: ReactNode }) => (
    <p>{children}</p>
  ),
  CredenzaHeader: ({ children }: { children: ReactNode }) => children,
  CredenzaTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
}));

const teamModelType: ModelType = 1;

function renderFavoriteButton() {
  render(<FavoriteButton modelKey="frc254" modelType={teamModelType} />);
}

describe('FavoriteButton', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    useAuthMock.mockReturnValue({ user: {} });
    useMyTBAMock.mockReturnValue({
      isFavorite: false,
      toggleFavorite: toggleFavoriteMock,
      isPending: false,
    });
  });

  afterEach(() => {
    cleanup();
  });

  test('loads myTBA state for the requested model', () => {
    renderFavoriteButton();

    expect(useMyTBAMock).toHaveBeenCalledWith('frc254', teamModelType);
  });

  test('shows the add action when the model is not a favorite', () => {
    renderFavoriteButton();

    expect(
      screen
        .getByRole('button', { name: 'Add to favorites' })
        .contains(screen.getByTestId('outline-star')),
    ).toBe(true);
  });

  test('shows the remove action when the model is a favorite', () => {
    useMyTBAMock.mockReturnValue({
      isFavorite: true,
      toggleFavorite: toggleFavoriteMock,
      isPending: false,
    });
    renderFavoriteButton();

    expect(
      screen
        .getByRole('button', { name: 'Remove from favorites' })
        .contains(screen.getByTestId('filled-star')),
    ).toBe(true);
  });

  test('disables the action while the favorite change is pending', () => {
    useMyTBAMock.mockReturnValue({
      isFavorite: false,
      toggleFavorite: toggleFavoriteMock,
      isPending: true,
    });
    renderFavoriteButton();

    const button = screen.getByRole('button', {
      name: 'Add to favorites',
    }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  test('toggles the favorite for an authenticated user', () => {
    renderFavoriteButton();

    fireEvent.click(screen.getByRole('button', { name: 'Add to favorites' }));

    expect(toggleFavoriteMock).toHaveBeenCalledOnce();
  });

  test('prompts an unauthenticated user to sign in', () => {
    useAuthMock.mockReturnValue({ user: null });
    renderFavoriteButton();

    fireEvent.click(screen.getByRole('button', { name: 'Add to favorites' }));

    expect(
      screen.getByRole('heading', { name: 'Sign in to use myTBA' }),
    ).toBeTruthy();
  });

  test('does not toggle the favorite for an unauthenticated user', () => {
    useAuthMock.mockReturnValue({ user: null });
    renderFavoriteButton();

    fireEvent.click(screen.getByRole('button', { name: 'Add to favorites' }));

    expect(toggleFavoriteMock).not.toHaveBeenCalled();
  });

  test('offers Google and Apple sign-in options', () => {
    useAuthMock.mockReturnValue({ user: null });
    renderFavoriteButton();

    fireEvent.click(screen.getByRole('button', { name: 'Add to favorites' }));

    expect(
      within(screen.getByRole('dialog'))
        .getAllByRole('button')
        .map((button) => button.textContent),
    ).toEqual(['Sign in with Google', 'Sign in with Apple']);
  });
});
