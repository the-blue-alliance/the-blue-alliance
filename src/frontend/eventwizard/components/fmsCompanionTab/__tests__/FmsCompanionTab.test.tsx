/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import FmsCompanionTab from "../FmsCompanionTab";
import { calculateFileDigest } from "../../../utils/fileDigest";

jest.mock("../../../utils/fileDigest");

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

describe("FmsCompanionTab uploads and job polling", () => {
  const mockCalculateFileDigest = calculateFileDigest as jest.Mock;
  const selectedEvent = "2025nysu";
  const file = new File(["sqlite"], "companion.db");

  const jsonResponse = (payload: unknown, ok = true, status = 200) =>
    ({ ok, status, statusText: ok ? "OK" : "Server Error", json: async () => payload }) as Response;

  const renderTab = (makeTrustedRequest: jest.Mock, event: string | null = selectedEvent) =>
    render(
      <FmsCompanionTab
        selectedEvent={event}
        makeTrustedRequest={makeTrustedRequest}
      />
    );

  const fileInput = () =>
    screen.getByLabelText(/Select FMS Companion Database Export/i) as HTMLInputElement;

  const submitForm = () => fireEvent.submit(document.querySelector("form")!);

  // The status text lives in the alert wrapping the "Import Job Status:" label.
  const expectJobStatus = (text: string) =>
    waitFor(() => {
      expect(
        screen.getByText(/Import Job Status/).parentElement
      ).toHaveTextContent(text);
    });

  beforeEach(() => {
    mockCalculateFileDigest.mockResolvedValue("digest123");
    jest.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    jest.restoreAllMocks();
    jest.clearAllMocks();
    jest.useRealTimers();
  });

  test("refuses to upload when no event is selected", () => {
    const makeTrustedRequest = jest.fn();
    renderTab(makeTrustedRequest, null);

    submitForm();

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Please select an event first"
    );
    expect(screen.getByRole("alert")).toHaveClass("alert-danger");
    expect(makeTrustedRequest).not.toHaveBeenCalled();
  });

  test("refuses to upload when no file is selected", () => {
    const makeTrustedRequest = jest.fn();
    renderTab(makeTrustedRequest);

    submitForm();

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Please select a file to upload"
    );
    expect(makeTrustedRequest).not.toHaveBeenCalled();
  });

  test("uploads the database with its digest and reports the server message", async () => {
    const makeTrustedRequest = jest
      .fn()
      .mockResolvedValue(jsonResponse({ Success: "Database queued" }));
    renderTab(makeTrustedRequest);
    fireEvent.change(fileInput(), { target: { files: [file] } });

    submitForm();

    expect(await screen.findByText("Database queued")).toHaveClass("alert-success");
    expect(mockCalculateFileDigest).toHaveBeenCalledWith(file);
    expect(makeTrustedRequest).toHaveBeenCalledTimes(1);
    const [path, body] = makeTrustedRequest.mock.calls[0];
    expect(path).toBe("/api/_eventwizard/event/2025nysu/fms_companion_db");
    expect(body).toBeInstanceOf(FormData);
    expect((body as FormData).get("companionDb")).toBe(file);
    expect((body as FormData).get("fileDigest")).toBe("digest123");
    expect(screen.queryByText(/Selected file/)).not.toBeInTheDocument();
    expect(fileInput().value).toBe("");
    expect(screen.queryByText(/Import Job Status/)).not.toBeInTheDocument();
  });

  test("falls back to a default success message when the server sends none", async () => {
    const makeTrustedRequest = jest.fn().mockResolvedValue(jsonResponse({}));
    renderTab(makeTrustedRequest);
    fireEvent.change(fileInput(), { target: { files: [file] } });

    submitForm();

    expect(
      await screen.findByText("FMS Companion database successfully uploaded")
    ).toBeInTheDocument();
  });

  test("polls the import job every five seconds until it completes", async () => {
    jest.useFakeTimers();
    const makeTrustedRequest = jest
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({ Success: "Queued", job_name: "job-1", execution_id: "exec-1" })
      )
      .mockResolvedValueOnce(jsonResponse({}))
      .mockResolvedValueOnce(
        jsonResponse({
          status: { state: "RUNNING", message: "importing", is_complete: false },
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          status: { state: "SUCCEEDED", message: "done", is_complete: true },
        })
      );
    renderTab(makeTrustedRequest);
    fireEvent.change(fileInput(), { target: { files: [file] } });

    submitForm();

    // The first poll happens as soon as the job details arrive; a response
    // without a status block leaves the PENDING placeholder in place.
    await expectJobStatus("PENDING");
    await waitFor(() => {
      expect(makeTrustedRequest).toHaveBeenCalledTimes(2);
    });
    expect(makeTrustedRequest).toHaveBeenLastCalledWith(
      "/api/_eventwizard/_cloudrun/status/2025nysu/job-1/exec-1",
      ""
    );

    act(() => {
      jest.advanceTimersByTime(5000);
    });
    await expectJobStatus("Job State: RUNNING - importing");

    act(() => {
      jest.advanceTimersByTime(5000);
    });
    await expectJobStatus("Job State: SUCCEEDED - done");
    expect(makeTrustedRequest).toHaveBeenCalledTimes(4);

    // The terminal state clears the job, which stops the interval.
    act(() => {
      jest.advanceTimersByTime(15000);
    });
    expect(makeTrustedRequest).toHaveBeenCalledTimes(4);
  });

  test("stops polling and shows ERROR when the status endpoint returns a non-2xx response", async () => {
    jest.useFakeTimers();
    const makeTrustedRequest = jest
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({ job_name: "job-1", execution_id: "exec-1" })
      )
      .mockResolvedValueOnce(jsonResponse({}, false, 500));
    renderTab(makeTrustedRequest);
    fireEvent.change(fileInput(), { target: { files: [file] } });

    submitForm();

    await expectJobStatus("ERROR");
    expect(console.error).toHaveBeenCalledWith(
      "Failed to fetch job status: HTTP 500"
    );
    act(() => {
      jest.advanceTimersByTime(15000);
    });
    expect(makeTrustedRequest).toHaveBeenCalledTimes(2);
  });

  test("stops polling and shows ERROR when the status request throws", async () => {
    jest.useFakeTimers();
    const makeTrustedRequest = jest
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({ job_name: "job-1", execution_id: "exec-1" })
      )
      .mockRejectedValueOnce(new Error("network down"));
    renderTab(makeTrustedRequest);
    fireEvent.change(fileInput(), { target: { files: [file] } });

    submitForm();

    await expectJobStatus("ERROR");
    expect(console.error).toHaveBeenCalledWith(
      "Error fetching job status:",
      expect.any(Error)
    );
    act(() => {
      jest.advanceTimersByTime(15000);
    });
    expect(makeTrustedRequest).toHaveBeenCalledTimes(2);
  });

  test("reports an upload that the server rejects", async () => {
    const makeTrustedRequest = jest
      .fn()
      .mockResolvedValue(jsonResponse({}, false, 400));
    renderTab(makeTrustedRequest);
    fireEvent.change(fileInput(), { target: { files: [file] } });

    submitForm();

    const alert = await screen.findByText(/Error uploading file: Error: Server Error/);
    expect(alert).toHaveClass("alert-danger");
    expect(screen.getByRole("button", { name: "Upload Database" })).toBeEnabled();
  });
});
