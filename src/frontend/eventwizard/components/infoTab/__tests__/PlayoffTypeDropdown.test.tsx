/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import PlayoffTypeDropdown from "../PlayoffTypeDropdown";
import { ApiEvent } from "../../../constants/ApiEvent";

describe("PlayoffTypeDropdown", () => {
  let mockSetType: jest.Mock;
  let mockFetch: jest.Mock;

  const mockEventData: ApiEvent = {
    key: "2020test",
    playoff_type: 0,
    playoff_type_string: "Bracket: 8 Alliances",
  };

  const mockPlayoffTypes = [
    { label: "Bracket: 8 Alliances", value: 0 },
    { label: "Bracket: 16 Alliances", value: 1 },
    { label: "Double Elimination (8 Alliances)", value: 8 },
  ];

  beforeEach(() => {
    mockSetType = jest.fn();
    mockFetch = jest.fn();
    global.fetch = mockFetch;
  });

  afterEach(() => {
    jest.clearAllMocks();
    delete (global as any).fetch;
  });

  describe("Rendering", () => {
    test("renders label correctly", () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      render(
        <PlayoffTypeDropdown eventInfo={mockEventData} setType={mockSetType} />
      );

      expect(screen.getByText("Playoff Type")).toBeInTheDocument();
    });

    test("renders dropdown with placeholder when no event info", () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      render(<PlayoffTypeDropdown eventInfo={null} setType={mockSetType} />);

      expect(screen.getByText("Choose playoff type...")).toBeInTheDocument();
    });

    test("renders dropdown with current value when event info exists", () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      render(
        <PlayoffTypeDropdown eventInfo={mockEventData} setType={mockSetType} />
      );

      expect(screen.getByText("Bracket: 8 Alliances")).toBeInTheDocument();
    });

    test("renders dropdown with empty string when playoff_type_string is undefined", () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      const eventWithoutPlayoffString: ApiEvent = {
        key: "2020test",
      };

      render(
        <PlayoffTypeDropdown
          eventInfo={eventWithoutPlayoffString}
          setType={mockSetType}
        />
      );

      // Should render without crashing
      expect(screen.getByText("Playoff Type")).toBeInTheDocument();
    });
  });

  describe("Disabled State", () => {
    test("dropdown is disabled when eventInfo is null", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      const { container } = render(<PlayoffTypeDropdown eventInfo={null} setType={mockSetType} />);

      // Look for the disabled input element that react-select creates
      await waitFor(() => {
        const disabledInput = container.querySelector('input[disabled]');
        expect(disabledInput).toBeInTheDocument();
      });
    });

    test("dropdown is enabled when eventInfo is provided", () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      const { container } = render(
        <PlayoffTypeDropdown eventInfo={mockEventData} setType={mockSetType} />
      );

      // Look for an enabled input element (no disabled attribute)
      const enabledInput = container.querySelector('input:not([disabled])');
      expect(enabledInput).toBeInTheDocument();
    });
  });

  describe("Loading Playoff Types", () => {
    test("fetches playoff types from correct endpoint", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      render(
        <PlayoffTypeDropdown eventInfo={mockEventData} setType={mockSetType} />
      );

      // Wait for the fetch to be called
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith("/_/playoff_types", {
          credentials: "same-origin",
        });
      });
    });

    test("handles fetch with credentials", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      render(
        <PlayoffTypeDropdown eventInfo={mockEventData} setType={mockSetType} />
      );

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            credentials: "same-origin",
          })
        );
      });
    });
  });

  describe("Value Display", () => {
    test("displays value with both playoff_type and playoff_type_string", () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      const eventWithBothFields: ApiEvent = {
        key: "2020test",
        playoff_type: 8,
        playoff_type_string: "Double Elimination (8 Alliances)",
      };

      render(
        <PlayoffTypeDropdown
          eventInfo={eventWithBothFields}
          setType={mockSetType}
        />
      );

      expect(
        screen.getByText("Double Elimination (8 Alliances)")
      ).toBeInTheDocument();
    });

    test("displays value with only playoff_type", () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      const eventWithOnlyType: ApiEvent = {
        key: "2020test",
        playoff_type: 1,
      };

      render(
        <PlayoffTypeDropdown
          eventInfo={eventWithOnlyType}
          setType={mockSetType}
        />
      );

      // Should render without crashing
      expect(screen.getByText("Playoff Type")).toBeInTheDocument();
    });

    test("displays value with only playoff_type_string", () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      const eventWithOnlyString: ApiEvent = {
        key: "2020test",
        playoff_type_string: "Bracket: 16 Alliances",
      };

      render(
        <PlayoffTypeDropdown
          eventInfo={eventWithOnlyString}
          setType={mockSetType}
        />
      );

      expect(screen.getByText("Bracket: 16 Alliances")).toBeInTheDocument();
    });
  });

  describe("Select Props", () => {
    test("renders with correct select properties", () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlayoffTypes),
      });

      render(
        <PlayoffTypeDropdown eventInfo={mockEventData} setType={mockSetType} />
      );

      // The component should render the value
      expect(screen.getByText("Bracket: 8 Alliances")).toBeInTheDocument();
      
      // Should have the label
      expect(screen.getByText("Playoff Type")).toBeInTheDocument();
    });
  });
});
