import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import ScoutingExport from '~/components/tba/scoutingExport';

const {
  copyCsvToClipboardMock,
  downloadCsvMock,
  toastErrorMock,
  toastSuccessMock,
} = vi.hoisted(() => ({
  copyCsvToClipboardMock: vi.fn<(csv: string) => Promise<void>>(),
  downloadCsvMock: vi.fn<(csv: string, filename: string) => void>(),
  toastErrorMock: vi.fn<(message: string) => void>(),
  toastSuccessMock: vi.fn<(message: string) => void>(),
}));

vi.mock('~/lib/csvUtils', () => ({
  copyCsvToClipboard: copyCsvToClipboardMock,
  downloadCsv: downloadCsvMock,
}));

vi.mock('sonner', () => ({
  toast: {
    error: toastErrorMock,
    success: toastSuccessMock,
  },
}));

const csvData = 'Team,Score\r\n254,100';

function renderScoutingExport() {
  render(
    <ScoutingExport
      title="Scouting Data"
      csvData={csvData}
      filename="scouting.csv"
    />,
  );
}

describe('ScoutingExport', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  test('renders the export title', () => {
    renderScoutingExport();

    expect(screen.getByRole('heading', { name: 'Scouting Data' })).toBeTruthy();
  });

  test('shows the CSV data in a disabled textarea', () => {
    renderScoutingExport();

    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    expect({ disabled: textarea.disabled, value: textarea.value }).toEqual({
      disabled: true,
      value: 'Team,Score\n254,100',
    });
  });

  test('copies the CSV data when Copy is clicked', async () => {
    copyCsvToClipboardMock.mockResolvedValue(undefined);
    renderScoutingExport();

    fireEvent.click(screen.getByRole('button', { name: 'Copy' }));

    await waitFor(() => {
      expect(copyCsvToClipboardMock).toHaveBeenCalledWith(csvData);
      expect(toastSuccessMock).toHaveBeenCalledWith('Copied to clipboard!');
    });
  });

  test('suggests downloading when the clipboard is not available', async () => {
    copyCsvToClipboardMock.mockRejectedValue(
      new Error('Clipboard API not available'),
    );
    renderScoutingExport();

    fireEvent.click(screen.getByRole('button', { name: 'Copy' }));

    await waitFor(() =>
      expect(toastErrorMock).toHaveBeenCalledWith(
        'Clipboard requires HTTPS. Use Download button.',
      ),
    );
  });

  test('suggests downloading when clipboard access is denied', async () => {
    copyCsvToClipboardMock.mockRejectedValue(
      new Error('Clipboard write permission denied'),
    );
    renderScoutingExport();

    fireEvent.click(screen.getByRole('button', { name: 'Copy' }));

    await waitFor(() =>
      expect(toastErrorMock).toHaveBeenCalledWith(
        'Clipboard access denied. Please use Download instead.',
      ),
    );
  });

  test('shows a generic error for a non-Error clipboard failure', async () => {
    copyCsvToClipboardMock.mockRejectedValue('Clipboard failed');
    renderScoutingExport();

    fireEvent.click(screen.getByRole('button', { name: 'Copy' }));

    await waitFor(() =>
      expect(toastErrorMock).toHaveBeenCalledWith(
        'Failed to copy to clipboard.',
      ),
    );
  });

  test('downloads the CSV data when Download is clicked', () => {
    renderScoutingExport();

    fireEvent.click(screen.getByRole('button', { name: 'Download' }));

    expect(downloadCsvMock).toHaveBeenCalledWith(csvData, 'scouting.csv');
    expect(toastSuccessMock).toHaveBeenCalledWith('Download started!');
  });

  test('shows an error when downloading fails', () => {
    downloadCsvMock.mockImplementation(() => {
      throw new Error('Download failed');
    });
    renderScoutingExport();

    fireEvent.click(screen.getByRole('button', { name: 'Download' }));

    expect(toastErrorMock).toHaveBeenCalledWith('Failed to download CSV.');
  });
});
