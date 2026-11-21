import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, renderHook } from '@testing-library/react';
import { type PropsWithChildren, type ReactNode, Suspense } from 'react';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={queryClient}>
        <Suspense fallback="loading">{children}</Suspense>
      </QueryClientProvider>
    );
  }
  return { queryClient, wrapper: Wrapper };
}

export function renderWithClient(ui: ReactNode) {
  const { queryClient, wrapper } = createWrapper();
  return { ...render(ui, { wrapper }), queryClient };
}

export function renderHookWithClient<T>(hook: () => T) {
  const { queryClient, wrapper } = createWrapper();
  return { ...renderHook(hook, { wrapper }), queryClient };
}
