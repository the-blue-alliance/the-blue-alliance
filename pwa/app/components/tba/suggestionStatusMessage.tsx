import type { JSX } from 'react';

export default function SuggestionStatusMessage({
  children,
  title,
  tone,
}: {
  children: React.ReactNode;
  title: string;
  tone: 'success' | 'info' | 'error';
}): JSX.Element {
  const colors = {
    success:
      'border-green-300 bg-green-50 text-green-900 dark:border-green-800 dark:bg-green-950 dark:text-green-100',
    info: 'border-blue-300 bg-blue-50 text-blue-900 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-100',
    error:
      'border-red-300 bg-red-50 text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-100',
  };
  return (
    <div role="alert" className={`rounded-lg border p-4 ${colors[tone]}`}>
      <p className="font-semibold">{title}</p>
      <p className="text-sm">{children}</p>
    </div>
  );
}
