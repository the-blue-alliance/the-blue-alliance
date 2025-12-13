/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import {
  render,
  screen,
  fireEvent,
  waitFor,
} from "@testing-library/react";
import FmsCompanionTab from "../FmsCompanionTab";

describe("FmsCompanionTab", () => {
  test("renders the upload form", () => {
    const makeTrustedRequest = jest.fn();
    render(
      <FmsCompanionTab
        selectedEvent={null}
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    expect(screen.getAllByText(/FMS Companion/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Upload FMS Companion Database/i)
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText(/Select FMS Companion Database Export/i)
    ).toBeInTheDocument();
  });

  test("file input is disabled when no event is selected", () => {
    const makeTrustedRequest = jest.fn();
    render(
      <FmsCompanionTab
        selectedEvent={null}
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    const fileInput = screen.getByLabelText(
      /Select FMS Companion Database Export/i
    ) as HTMLInputElement;
    expect(fileInput).toBeDisabled();
  });

  test("file input is enabled when event is selected", () => {
    const makeTrustedRequest = jest.fn();
    render(
      <FmsCompanionTab
        selectedEvent="2024test"
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    const fileInput = screen.getByLabelText(
      /Select FMS Companion Database Export/i
    ) as HTMLInputElement;
    expect(fileInput).not.toBeDisabled();
  });

  test("displays file name and size when file is selected", async () => {
    const makeTrustedRequest = jest.fn();
    render(
      <FmsCompanionTab
        selectedEvent="2024test"
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    const file = new File(
      ["dummy content with some size"],
      "companion.db",
      { type: "application/octet-stream" }
    );

    const fileInput = screen.getByLabelText(
      /Select FMS Companion Database Export/i
    ) as HTMLInputElement;

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/Selected file:/i)).toBeInTheDocument();
      expect(screen.getByText(/companion.db/)).toBeInTheDocument();
    });
  });

  test("upload button is disabled when no file is selected", () => {
    const makeTrustedRequest = jest.fn();
    render(
      <FmsCompanionTab
        selectedEvent="2024test"
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    const uploadButton = screen.getByRole("button", {
      name: /Upload Database/i,
    }) as HTMLButtonElement;
    expect(uploadButton).toBeDisabled();
  });

  test("upload button is enabled when file is selected", async () => {
    const makeTrustedRequest = jest.fn();
    render(
      <FmsCompanionTab
        selectedEvent="2024test"
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    const file = new File(
      ["dummy content"],
      "companion.db",
      { type: "application/octet-stream" }
    );

    const fileInput = screen.getByLabelText(
      /Select FMS Companion Database Export/i
    ) as HTMLInputElement;

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      const uploadButton = screen.getByRole("button", {
        name: /Upload Database/i,
      }) as HTMLButtonElement;
      expect(uploadButton).not.toBeDisabled();
    });
  });

  test("clears file selection when file input changes", async () => {
    const makeTrustedRequest = jest.fn();
    render(
      <FmsCompanionTab
        selectedEvent="2024test"
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    const file1 = new File(["content1"], "companion1.db");
    const file2 = new File(["content2"], "companion2.db");
    const fileInput = screen.getByLabelText(
      /Select FMS Companion Database Export/i
    ) as HTMLInputElement;

    fireEvent.change(fileInput, { target: { files: [file1] } });

    await waitFor(() => {
      expect(screen.getByText(/companion1.db/)).toBeInTheDocument();
    });

    fireEvent.change(fileInput, { target: { files: [file2] } });

    await waitFor(() => {
      expect(screen.getByText(/companion2.db/)).toBeInTheDocument();
      expect(screen.queryByText(/companion1.db/)).not.toBeInTheDocument();
    });
  });

  test("renders error alert when error occurs", async () => {
    // Mock crypto.subtle.digest
    Object.defineProperty(global, "crypto", {
      value: {
        subtle: {
          digest: jest.fn().mockResolvedValue(new ArrayBuffer(32)),
        },
      },
      configurable: true,
    });

    const makeTrustedRequest = jest.fn().mockRejectedValue(
      new Error("Test error message")
    );

    render(
      <FmsCompanionTab
        selectedEvent="2024test"
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    const file = new File(["content"], "companion.db");
    const fileInput = screen.getByLabelText(
      /Select FMS Companion Database Export/i
    ) as HTMLInputElement;

    fireEvent.change(fileInput, { target: { files: [file] } });

    const uploadButton = screen.getByRole("button", {
      name: /Upload Database/i,
    });

    fireEvent.click(uploadButton);

    await waitFor(() => {
      const alert = screen.getByRole("alert");
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveClass("alert-danger");
    });
  });
});
