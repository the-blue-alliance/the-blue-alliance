/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import AddRemoveTeamMap from "../AddRemoveTeamMap";
import { ApiEvent } from "../../../constants/ApiEvent";

describe("AddRemoveTeamMap", () => {
  let mockAddTeamMap: jest.Mock;
  let mockRemoveTeamMap: jest.Mock;

  const mockEventWithMappings: ApiEvent = {
    key: "2020test",
    remap_teams: {
      frc123: "frc456",
      frc789: "frc101",
    },
  };

  const mockEventWithoutMappings: ApiEvent = {
    key: "2020test",
    remap_teams: {},
  };

  beforeEach(() => {
    mockAddTeamMap = jest.fn();
    mockRemoveTeamMap = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    test("renders label correctly", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("Team Mappings")).toBeInTheDocument();
    });

    test("renders warning note about removing mappings", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(
        screen.getByText("Note: Removing a mapping will not unmap existing data!")
      ).toBeInTheDocument();
    });

    test("renders team mappings list when mappings exist", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("2 team mappings found")).toBeInTheDocument();
    });

    test("renders 'No team mappings found' when mappings object is empty", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithoutMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("No team mappings found")).toBeInTheDocument();
    });

    test("renders 'No team mappings found' when remap_teams is undefined", () => {
      const eventWithoutMappings: ApiEvent = {
        key: "2020test",
      };

      render(
        <AddRemoveTeamMap
          eventInfo={eventWithoutMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("No team mappings found")).toBeInTheDocument();
    });

    test("renders 'No team mappings found' when eventInfo is null", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={null}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("No team mappings found")).toBeInTheDocument();
    });

    test("renders from team input with placeholder", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByPlaceholderText("9254")).toBeInTheDocument();
    });

    test("renders to team input with placeholder", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByPlaceholderText("254B")).toBeInTheDocument();
    });

    test("renders Add Mapping button", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("Add Mapping")).toBeInTheDocument();
    });

    test("renders arrow icon between inputs", () => {
      const { container } = render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const arrow = container.querySelector(".glyphicon-arrow-right");
      expect(arrow).toBeInTheDocument();
    });
  });

  describe("Input Fields", () => {
    test("both inputs have form-control class", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254");
      const toInput = screen.getByPlaceholderText("254B");

      expect(fromInput).toHaveClass("form-control");
      expect(toInput).toHaveClass("form-control");
    });

    test("inputs have correct type", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254");
      const toInput = screen.getByPlaceholderText("254B");

      expect(fromInput).toHaveAttribute("type", "text");
      expect(toInput).toHaveAttribute("type", "text");
    });
  });

  describe("Disabled State", () => {
    test("inputs are disabled when eventInfo is null", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={null}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254");
      const toInput = screen.getByPlaceholderText("254B");

      expect(fromInput).toBeDisabled();
      expect(toInput).toBeDisabled();
    });

    test("button is disabled when eventInfo is null", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={null}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const button = screen.getByText("Add Mapping");
      expect(button).toBeDisabled();
    });

    test("inputs are enabled when eventInfo is provided", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254");
      const toInput = screen.getByPlaceholderText("254B");

      expect(fromInput).not.toBeDisabled();
      expect(toInput).not.toBeDisabled();
    });
  });

  describe("Input Validation - From Team", () => {
    test("accepts valid numeric team number", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText(
        "9254"
      ) as HTMLInputElement;

      fireEvent.change(fromInput, { target: { value: "254" } });

      expect(fromInput.value).toBe("254");
      expect(fromInput.closest(".input-group")).not.toHaveClass("has-error");
    });

    test("shows error for invalid from team (contains letters)", () => {
      const { container } = render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254");

      fireEvent.change(fromInput, { target: { value: "254B" } });

      const inputGroup = container.querySelector(".input-group");
      expect(inputGroup).toHaveClass("has-error");
    });

    test("shows error for invalid from team (special characters)", () => {
      const { container } = render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254");

      fireEvent.change(fromInput, { target: { value: "254!" } });

      const inputGroup = container.querySelector(".input-group");
      expect(inputGroup).toHaveClass("has-error");
    });

    test("button is disabled when from team has error", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254");
      const button = screen.getByText("Add Mapping");

      fireEvent.change(fromInput, { target: { value: "254A" } });

      expect(button).toBeDisabled();
    });
  });

  describe("Input Validation - To Team", () => {
    test("accepts valid numeric team number", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const toInput = screen.getByPlaceholderText("254B") as HTMLInputElement;

      fireEvent.change(toInput, { target: { value: "254" } });

      expect(toInput.value).toBe("254");
      expect(toInput.closest(".input-group")).not.toHaveClass("has-error");
    });

    test("accepts team number with single letter suffix", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const toInput = screen.getByPlaceholderText("254B") as HTMLInputElement;

      fireEvent.change(toInput, { target: { value: "254B" } });

      expect(toInput.value).toBe("254B");
      expect(toInput.closest(".input-group")).not.toHaveClass("has-error");
    });

    test("accepts team number with lowercase letter suffix", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const toInput = screen.getByPlaceholderText("254B") as HTMLInputElement;

      fireEvent.change(toInput, { target: { value: "254c" } });

      expect(toInput.value).toBe("254c");
      expect(toInput.closest(".input-group")).not.toHaveClass("has-error");
    });

    test("rejects team number with 'A' suffix (reserved)", () => {
      const { container } = render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const toInput = screen.getByPlaceholderText("254B");

      fireEvent.change(toInput, { target: { value: "254A" } });

      const inputGroup = container.querySelector(".input-group");
      expect(inputGroup).toHaveClass("has-error");
    });

    test("shows error for invalid to team (multiple letters)", () => {
      const { container } = render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const toInput = screen.getByPlaceholderText("254B");

      fireEvent.change(toInput, { target: { value: "254BC" } });

      const inputGroup = container.querySelector(".input-group");
      expect(inputGroup).toHaveClass("has-error");
    });

    test("shows error for invalid to team (special characters)", () => {
      const { container } = render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const toInput = screen.getByPlaceholderText("254B");

      fireEvent.change(toInput, { target: { value: "254!" } });

      const inputGroup = container.querySelector(".input-group");
      expect(inputGroup).toHaveClass("has-error");
    });

    test("button is disabled when to team has error", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const toInput = screen.getByPlaceholderText("254B");
      const button = screen.getByText("Add Mapping");

      fireEvent.change(toInput, { target: { value: "254ABC" } });

      expect(button).toBeDisabled();
    });
  });

  describe("Add Team Mapping Functionality", () => {
    test("calls addTeamMap with frc prefix when button clicked", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254");
      const toInput = screen.getByPlaceholderText("254B");
      const button = screen.getByText("Add Mapping");

      fireEvent.change(fromInput, { target: { value: "123" } });
      fireEvent.change(toInput, { target: { value: "456" } });
      fireEvent.click(button);

      expect(mockAddTeamMap).toHaveBeenCalledTimes(1);
      expect(mockAddTeamMap).toHaveBeenCalledWith("frc123", "frc456");
    });

    test("converts team numbers to uppercase", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254");
      const toInput = screen.getByPlaceholderText("254B");
      const button = screen.getByText("Add Mapping");

      fireEvent.change(fromInput, { target: { value: "123" } });
      fireEvent.change(toInput, { target: { value: "456b" } });
      fireEvent.click(button);

      expect(mockAddTeamMap).toHaveBeenCalledWith("frc123", "frc456B");
    });

    test("clears inputs after adding mapping", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254") as HTMLInputElement;
      const toInput = screen.getByPlaceholderText("254B") as HTMLInputElement;
      const button = screen.getByText("Add Mapping");

      fireEvent.change(fromInput, { target: { value: "123" } });
      fireEvent.change(toInput, { target: { value: "456" } });
      fireEvent.click(button);

      expect(fromInput.value).toBe("");
      expect(toInput.value).toBe("");
    });

    test("clears error states after adding mapping", () => {
      const { container } = render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254");
      const button = screen.getByText("Add Mapping");

      // Create error state
      fireEvent.change(fromInput, { target: { value: "123A" } });
      
      // Fix and add
      fireEvent.change(fromInput, { target: { value: "123" } });
      fireEvent.click(button);

      const inputGroup = container.querySelector(".input-group");
      expect(inputGroup).not.toHaveClass("has-error");
    });

    test("can add multiple mappings", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const fromInput = screen.getByPlaceholderText("9254");
      const toInput = screen.getByPlaceholderText("254B");
      const button = screen.getByText("Add Mapping");

      fireEvent.change(fromInput, { target: { value: "123" } });
      fireEvent.change(toInput, { target: { value: "456" } });
      fireEvent.click(button);

      fireEvent.change(fromInput, { target: { value: "789" } });
      fireEvent.change(toInput, { target: { value: "101" } });
      fireEvent.click(button);

      expect(mockAddTeamMap).toHaveBeenCalledTimes(2);
    });
  });

  describe("Button Styling", () => {
    test("Add Mapping button has correct class", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const button = screen.getByText("Add Mapping");
      expect(button).toHaveClass("btn", "btn-info");
    });
  });

  describe("Form Group Structure", () => {
    test("renders within form-group row", () => {
      const { container } = render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const formGroup = container.querySelector(".form-group.row");
      expect(formGroup).toBeInTheDocument();
    });

    test("label has correct column class", () => {
      render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const label = screen.getByText("Team Mappings");
      expect(label).toHaveClass("col-sm-2", "control-label");
    });

    test("team mappings list has correct id", () => {
      const { container } = render(
        <AddRemoveTeamMap
          eventInfo={mockEventWithMappings}
          addTeamMap={mockAddTeamMap}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const teamMappingsList = container.querySelector("#team_mappings_list");
      expect(teamMappingsList).toBeInTheDocument();
      expect(teamMappingsList).toHaveClass("col-sm-10");
    });
  });
});
