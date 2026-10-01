/**
 * @jest-environment jsdom
 */

import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import EventAlliancesTab from "../EventAlliancesTab";
import FMSAllianceImport from "../FMSAllianceImport";

// The FMS import child has its own tests; stub it so its callbacks can be
// driven directly here.
jest.mock("../FMSAllianceImport", () => jest.fn(() => null));

describe("EventAlliancesTab", () => {
  const mockMakeTrustedRequest = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({}),
  } as Response);
  const mockSelectedEvent = "2025nysu";

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders the main tab structure", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(screen.getByText("Alliance Selection")).toBeInTheDocument();
      expect(screen.getByText("FMS Alliance Import")).toBeInTheDocument();
      expect(screen.getByText("Manual Alliance Entry")).toBeInTheDocument();
      expect(screen.getByText("Alliance Selection Data")).toBeInTheDocument();
    });

    it("renders alliance size options", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const radio3 = screen.getByRole("radio", { name: "3" });
      const radio4 = screen.getByRole("radio", { name: "4" });

      expect(radio3).toBeInTheDocument();
      expect(radio4).toBeInTheDocument();
      expect(radio3).toBeChecked(); // Default is 3
    });

    it("renders 8 alliance rows", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      for (let i = 1; i <= 8; i++) {
        expect(screen.getByText(`Alliance ${i}`)).toBeInTheDocument();
      }
    });
  });

  describe("Alliance Upload", () => {
    it("disables upload button when no event is selected", () => {
      render(
        <EventAlliancesTab
          selectedEvent=""
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const uploadButton = screen.getByRole("button", {
        name: "Upload Alliances to TBA",
      });
      expect(uploadButton).toBeDisabled();
    });

    it("enables upload button when event is selected", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const uploadButton = screen.getByRole("button", {
        name: "Upload Alliances to TBA",
      });
      expect(uploadButton).not.toBeDisabled();
    });
  });
});

describe("EventAlliancesTab interactions", () => {
  const mockMakeTrustedRequest = jest.fn();
  const mockFMSAllianceImport = FMSAllianceImport as unknown as jest.Mock;
  const selectedEvent = "2025nysu";

  const renderTab = () =>
    render(
      <EventAlliancesTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

  const typeInto = (placeholder: string, value: string) =>
    fireEvent.change(screen.getByPlaceholderText(placeholder), {
      target: { value },
    });

  const uploadButton = () =>
    screen.getByRole("button", { name: "Upload Alliances to TBA" });

  beforeEach(() => {
    mockMakeTrustedRequest.mockResolvedValue({ ok: true } as Response);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Manual entry", () => {
    it("shows the Pick 3 column only for four-team alliances and clears it on the way back", () => {
      renderTab();
      expect(screen.queryByText("Pick 3")).not.toBeInTheDocument();

      fireEvent.click(screen.getByRole("radio", { name: "4" }));
      expect(screen.getByText("Pick 3")).toBeInTheDocument();
      typeInto("Pick 1-3", "9999");
      expect(screen.getByPlaceholderText("Pick 1-3")).toHaveValue("9999");

      fireEvent.click(screen.getByRole("radio", { name: "3" }));
      expect(screen.queryByPlaceholderText("Pick 1-3")).not.toBeInTheDocument();

      fireEvent.click(screen.getByRole("radio", { name: "4" }));
      expect(screen.getByPlaceholderText("Pick 1-3")).toHaveValue("");
    });

    it("keeps each alliance's fields independent as they are edited", () => {
      renderTab();

      typeInto("Captain 1", "254");
      typeInto("Pick 1-1", "1114");
      typeInto("Pick 2-2", "2056");

      expect(screen.getByPlaceholderText("Captain 1")).toHaveValue("254");
      expect(screen.getByPlaceholderText("Pick 1-1")).toHaveValue("1114");
      expect(screen.getByPlaceholderText("Pick 2-2")).toHaveValue("2056");
      expect(screen.getByPlaceholderText("Captain 2")).toHaveValue("");
    });

    it("uploads the entered alliances, sending empty arrays for unfilled alliances", async () => {
      renderTab();
      fireEvent.click(screen.getByRole("radio", { name: "4" }));
      typeInto("Captain 1", "254");
      typeInto("Pick 1-1", "1114");
      typeInto("Pick 1-2", "2056");
      typeInto("Pick 1-3", "1678");
      typeInto("Captain 2", "148");
      typeInto("Pick 2-2", "118");

      fireEvent.click(uploadButton());

      expect(
        await screen.findByText("Alliances uploaded successfully!")
      ).toHaveClass("alert-success");
      expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
        "/api/trusted/v1/event/2025nysu/alliance_selections/update",
        JSON.stringify([
          ["frc254", "frc1114", "frc2056", "frc1678"],
          ["frc148", "frc118"],
          [],
          [],
          [],
          [],
          [],
          [],
        ])
      );
      expect(uploadButton()).toBeEnabled();
    });

    it("omits the fourth pick when three-team alliances are selected", async () => {
      renderTab();
      typeInto("Captain 1", "254");
      typeInto("Pick 1-1", "1114");

      fireEvent.click(uploadButton());

      await screen.findByText("Alliances uploaded successfully!");
      expect(JSON.parse(mockMakeTrustedRequest.mock.calls[0][1])[0]).toEqual([
        "frc254",
        "frc1114",
      ]);
    });

    it("shows the upload error and re-enables the button", async () => {
      mockMakeTrustedRequest.mockRejectedValueOnce(new Error("boom"));
      renderTab();
      typeInto("Captain 1", "254");

      fireEvent.click(uploadButton());

      expect(
        await screen.findByText("Error uploading alliances: Error: boom")
      ).toHaveClass("alert-danger");
      expect(uploadButton()).toBeEnabled();
    });
  });

  describe("FMS import", () => {
    const importProps = () =>
      mockFMSAllianceImport.mock.calls[mockFMSAllianceImport.mock.calls.length - 1][0];

    it("passes the event and request helper to the import component", () => {
      renderTab();

      expect(importProps()).toMatchObject({
        selectedEvent,
        makeTrustedRequest: mockMakeTrustedRequest,
      });
    });

    it("uploads imported alliances and reports success", async () => {
      renderTab();
      const onSuccess = jest.fn();
      const onError = jest.fn();

      await act(async () => {
        await importProps().updateAlliances(
          [["frc254", "frc1114"], ["frc148"]],
          onSuccess,
          onError
        );
      });

      expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
        "/api/trusted/v1/event/2025nysu/alliance_selections/update",
        JSON.stringify([["frc254", "frc1114"], ["frc148"]])
      );
      expect(onSuccess).toHaveBeenCalledTimes(1);
      expect(onError).not.toHaveBeenCalled();
    });

    it("reports upload failures through the error callback", async () => {
      mockMakeTrustedRequest.mockRejectedValueOnce(new Error("boom"));
      renderTab();
      const onSuccess = jest.fn();
      const onError = jest.fn();

      await act(async () => {
        await importProps().updateAlliances([["frc254"]], onSuccess, onError);
      });

      expect(onSuccess).not.toHaveBeenCalled();
      expect(onError).toHaveBeenCalledWith("Error: boom");
    });
  });
});
