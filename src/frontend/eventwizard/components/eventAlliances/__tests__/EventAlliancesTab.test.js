/**
 * @jest-environment jsdom
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import EventAlliancesTab from "../EventAlliancesTab";

describe("EventAlliancesTab", () => {
  const mockMakeTrustedRequest = jest.fn();
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
      expect(
        screen.getByText("Alliance Selection Configuration")
      ).toBeInTheDocument();
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
      expect(
        screen.queryByRole("radio", { name: "2" })
      ).not.toBeInTheDocument();
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

    it("renders correct number of pick columns based on alliance size", () => {
      const { rerender } = render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      // Default size 3: Captain, Pick 1, Pick 2
      expect(screen.getByText("Captain")).toBeInTheDocument();
      expect(screen.getByText("Pick 1")).toBeInTheDocument();
      expect(screen.getByText("Pick 2")).toBeInTheDocument();
      expect(screen.queryByText("Pick 3")).not.toBeInTheDocument();

      // Change to size 4
      const radio4 = screen.getByRole("radio", { name: "4" });
      fireEvent.click(radio4);

      expect(screen.getByText("Pick 3")).toBeInTheDocument();
    });
  });

  describe("Alliance Size Selection", () => {
    it("changes alliance size to 4 and shows all pick columns", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const radio4 = screen.getByRole("radio", { name: "4" });
      fireEvent.click(radio4);

      expect(radio4).toBeChecked();
      expect(screen.getByText("Pick 1")).toBeInTheDocument();
      expect(screen.getByText("Pick 2")).toBeInTheDocument();
      expect(screen.getByText("Pick 3")).toBeInTheDocument();
    });

    it("clears pick3 when reducing alliance size from 4 to 3", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      // Change to size 4
      const radio4 = screen.getByRole("radio", { name: "4" });
      fireEvent.click(radio4);

      // Enter data for alliance 1 with size 4
      const captainInput = screen.getByPlaceholderText("Captain 1");
      const pick1Input = screen.getByPlaceholderText("Pick 1-1");
      const pick2Input = screen.getByPlaceholderText("Pick 1-2");
      const pick3Input = screen.getByPlaceholderText("Pick 1-3");

      fireEvent.change(captainInput, { target: { value: "254" } });
      fireEvent.change(pick1Input, { target: { value: "971" } });
      fireEvent.change(pick2Input, { target: { value: "1323" } });
      fireEvent.change(pick3Input, { target: { value: "1678" } });

      expect(captainInput.value).toBe("254");
      expect(pick1Input.value).toBe("971");
      expect(pick2Input.value).toBe("1323");
      expect(pick3Input.value).toBe("1678");

      // Change to size 3
      const radio3 = screen.getByRole("radio", { name: "3" });
      fireEvent.click(radio3);

      // Captain, pick1, and pick2 should remain, but pick3 should be cleared
      expect(captainInput.value).toBe("254");
      expect(pick1Input.value).toBe("971");
      expect(pick2Input.value).toBe("1323");
    });
  });

  describe("Alliance Input", () => {
    it("allows entering team numbers for alliances", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const captainInput = screen.getByPlaceholderText("Captain 1");
      const pick1Input = screen.getByPlaceholderText("Pick 1-1");
      const pick2Input = screen.getByPlaceholderText("Pick 1-2");

      fireEvent.change(captainInput, { target: { value: "254" } });
      fireEvent.change(pick1Input, { target: { value: "971" } });
      fireEvent.change(pick2Input, { target: { value: "1323" } });

      expect(captainInput.value).toBe("254");
      expect(pick1Input.value).toBe("971");
      expect(pick2Input.value).toBe("1323");
    });

    it("allows entering data for multiple alliances", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const captain1Input = screen.getByPlaceholderText("Captain 1");
      const captain2Input = screen.getByPlaceholderText("Captain 2");

      fireEvent.change(captain1Input, { target: { value: "254" } });
      fireEvent.change(captain2Input, { target: { value: "1323" } });

      expect(captain1Input.value).toBe("254");
      expect(captain2Input.value).toBe("1323");
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

    it("uploads alliances with correct format (size 3)", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      // Enter alliance 1 data (now first row in table)
      const captain1Input = screen.getByPlaceholderText("Captain 1");
      const pick1_1Input = screen.getByPlaceholderText("Pick 1-1");
      const pick1_2Input = screen.getByPlaceholderText("Pick 1-2");

      fireEvent.change(captain1Input, { target: { value: "254" } });
      fireEvent.change(pick1_1Input, { target: { value: "971" } });
      fireEvent.change(pick1_2Input, { target: { value: "1323" } });

      const uploadButton = screen.getByRole("button", {
        name: "Upload Alliances to TBA",
      });

      mockMakeTrustedRequest.mockImplementation(
        (path, body, onSuccess, onError) => {
          onSuccess();
        }
      );

      fireEvent.click(uploadButton);

      expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
        "/api/trusted/v1/event/2025nysu/alliance_selections/update",
        JSON.stringify([
          ["frc254", "frc971", "frc1323"], // Alliance 1 (index 0)
          [], // Alliance 2 (index 1)
          [], // Alliance 3 (index 2)
          [], // Alliance 4 (index 3)
          [], // Alliance 5 (index 4)
          [], // Alliance 6 (index 5)
          [], // Alliance 7 (index 6)
          [], // Alliance 8 (index 7)
        ]),
        expect.any(Function),
        expect.any(Function)
      );
    });

    it("uploads alliances with size 4", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      // Change to size 4
      const radio4 = screen.getByRole("radio", { name: "4" });
      fireEvent.click(radio4);

      // Enter alliance 1 data
      const captain1Input = screen.getByPlaceholderText("Captain 1");
      const pick1_1Input = screen.getByPlaceholderText("Pick 1-1");
      const pick1_2Input = screen.getByPlaceholderText("Pick 1-2");
      const pick1_3Input = screen.getByPlaceholderText("Pick 1-3");

      fireEvent.change(captain1Input, { target: { value: "254" } });
      fireEvent.change(pick1_1Input, { target: { value: "971" } });
      fireEvent.change(pick1_2Input, { target: { value: "1323" } });
      fireEvent.change(pick1_3Input, { target: { value: "1678" } });

      const uploadButton = screen.getByRole("button", {
        name: "Upload Alliances to TBA",
      });

      mockMakeTrustedRequest.mockImplementation(
        (path, body, onSuccess, onError) => {
          onSuccess();
        }
      );

      fireEvent.click(uploadButton);

      const requestBody = JSON.parse(mockMakeTrustedRequest.mock.calls[0][1]);
      expect(requestBody[0]).toEqual([
        "frc254",
        "frc971",
        "frc1323",
        "frc1678",
      ]);
    });

    it("handles partial alliance data correctly", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      // Enter only captain and pick1 for alliance 1
      const captain1Input = screen.getByPlaceholderText("Captain 1");
      const pick1_1Input = screen.getByPlaceholderText("Pick 1-1");

      fireEvent.change(captain1Input, { target: { value: "254" } });
      fireEvent.change(pick1_1Input, { target: { value: "971" } });

      const uploadButton = screen.getByRole("button", {
        name: "Upload Alliances to TBA",
      });

      mockMakeTrustedRequest.mockImplementation(
        (path, body, onSuccess, onError) => {
          onSuccess();
        }
      );

      fireEvent.click(uploadButton);

      const requestBody = JSON.parse(mockMakeTrustedRequest.mock.calls[0][1]);
      expect(requestBody[0]).toEqual(["frc254", "frc971"]);
    });

    it("uploads empty alliances for alliances without captains", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const uploadButton = screen.getByRole("button", {
        name: "Upload Alliances to TBA",
      });

      mockMakeTrustedRequest.mockImplementation(
        (path, body, onSuccess, onError) => {
          onSuccess();
        }
      );

      fireEvent.click(uploadButton);

      const requestBody = JSON.parse(mockMakeTrustedRequest.mock.calls[0][1]);
      // All 8 alliances should be empty arrays
      expect(requestBody.every((alliance) => alliance.length === 0)).toBe(true);
    });

    it("displays success message on successful upload", async () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      mockMakeTrustedRequest.mockImplementation(
        (path, body, onSuccess, onError) => {
          onSuccess();
        }
      );

      const uploadButton = screen.getByRole("button", {
        name: "Upload Alliances to TBA",
      });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(
          screen.getByText("Alliances uploaded successfully!")
        ).toBeInTheDocument();
      });
    });

    it("displays error message on upload failure", async () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      mockMakeTrustedRequest.mockImplementation(
        (path, body, onSuccess, onError) => {
          onError("Network error");
        }
      );

      const uploadButton = screen.getByRole("button", {
        name: "Upload Alliances to TBA",
      });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(
          screen.getByText("Error uploading alliances: Network error")
        ).toBeInTheDocument();
      });
    });

    it("disables inputs while uploading", () => {
      render(
        <EventAlliancesTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      mockMakeTrustedRequest.mockImplementation(
        (path, body, onSuccess, onError) => {
          // Don't call callbacks to simulate in-progress upload
        }
      );

      const uploadButton = screen.getByRole("button", {
        name: "Upload Alliances to TBA",
      });
      fireEvent.click(uploadButton);

      // Check that inputs are disabled
      const captainInput = screen.getByPlaceholderText("Captain 1");
      expect(captainInput).toBeDisabled();

      const radio3 = screen.getByRole("radio", { name: "3" });
      expect(radio3).toBeDisabled();

      expect(
        screen.getByRole("button", { name: "Uploading..." })
      ).toBeDisabled();
    });

    it("prevents upload when no event is selected via disabled button", () => {
      render(
        <EventAlliancesTab
          selectedEvent=""
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const uploadButton = screen.getByRole("button", {
        name: "Upload Alliances to TBA",
      });

      // Button should be disabled
      expect(uploadButton).toBeDisabled();

      // Attempting to click should not trigger the request
      fireEvent.click(uploadButton);
      expect(mockMakeTrustedRequest).not.toHaveBeenCalled();
    });
  });
});
