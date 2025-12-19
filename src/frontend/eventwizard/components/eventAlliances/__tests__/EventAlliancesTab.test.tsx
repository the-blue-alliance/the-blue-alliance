/**
 * @jest-environment jsdom
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import EventAlliancesTab from "../EventAlliancesTab";

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
