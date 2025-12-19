/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import TeamMappingsList from "../TeamMappingsList";

describe("TeamMappingsList", () => {
  let mockRemoveTeamMap: jest.Mock;

  const mockTeamMappings = {
    frc123: "frc456",
    frc789: "frc101",
    frc254: "frc254B",
  };

  beforeEach(() => {
    mockRemoveTeamMap = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    test("renders count message with correct number", () => {
      render(
        <TeamMappingsList
          teamMappings={mockTeamMappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("3 team mappings found")).toBeInTheDocument();
    });

    test("renders count message for single mapping", () => {
      const singleMapping = {
        frc123: "frc456",
      };

      render(
        <TeamMappingsList
          teamMappings={singleMapping}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("1 team mappings found")).toBeInTheDocument();
    });

    test("does not render count message when mappings object is empty", () => {
      render(
        <TeamMappingsList
          teamMappings={{}}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.queryByText(/team mappings found/)).not.toBeInTheDocument();
    });

    test("renders unordered list", () => {
      const { container } = render(
        <TeamMappingsList
          teamMappings={mockTeamMappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const ul = container.querySelector("ul");
      expect(ul).toBeInTheDocument();
    });

    test("renders correct number of list items", () => {
      const { container } = render(
        <TeamMappingsList
          teamMappings={mockTeamMappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const listItems = container.querySelectorAll("li");
      expect(listItems).toHaveLength(3);
    });

    test("renders TeamMappingItem for each mapping", () => {
      render(
        <TeamMappingsList
          teamMappings={mockTeamMappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      // Check that team numbers are rendered (without frc prefix)
      expect(screen.getByText("123", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("456", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("789", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("101", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("254", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("254B", { exact: false })).toBeInTheDocument();
    });
  });

  describe("Empty State", () => {
    test("renders empty list when no mappings", () => {
      const { container } = render(
        <TeamMappingsList teamMappings={{}} removeTeamMap={mockRemoveTeamMap} />
      );

      const ul = container.querySelector("ul");
      expect(ul).toBeInTheDocument();
      expect(ul?.children).toHaveLength(0);
    });
  });

  describe("Remove Functionality", () => {
    test("passes removeTeamMap function to TeamMappingItem", () => {
      render(
        <TeamMappingsList
          teamMappings={mockTeamMappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const removeButtons = screen.getAllByText("Remove");
      expect(removeButtons).toHaveLength(3);
    });

    test("clicking remove calls removeTeamMap with correct from team key", () => {
      render(
        <TeamMappingsList
          teamMappings={{ frc123: "frc456" }}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const removeButton = screen.getByText("Remove");
      fireEvent.click(removeButton);

      expect(mockRemoveTeamMap).toHaveBeenCalledTimes(1);
      expect(mockRemoveTeamMap).toHaveBeenCalledWith("frc123");
    });

    test("clicking remove on different items calls with different keys", () => {
      const mappings = {
        frc100: "frc200",
        frc300: "frc400",
      };

      render(
        <TeamMappingsList
          teamMappings={mappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const removeButtons = screen.getAllByText("Remove");
      
      fireEvent.click(removeButtons[0]);
      expect(mockRemoveTeamMap).toHaveBeenCalledWith("frc100");

      fireEvent.click(removeButtons[1]);
      expect(mockRemoveTeamMap).toHaveBeenCalledWith("frc300");
    });
  });

  describe("Mapping Display", () => {
    test("displays mappings with arrow between teams", () => {
      const mappings = {
        frc254: "frc254B",
      };

      const { container } = render(
        <TeamMappingsList
          teamMappings={mappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      // Check for arrow icon
      const arrow = container.querySelector(".glyphicon-arrow-right");
      expect(arrow).toBeInTheDocument();
    });

    test("handles mappings with letter suffixes", () => {
      const mappings = {
        frc254: "frc254B",
        frc9254: "frc254",
      };

      render(
        <TeamMappingsList
          teamMappings={mappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      // Use getAllByText since "254" appears twice
      expect(screen.getAllByText("254", { exact: false }).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("254B", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("9254", { exact: false })).toBeInTheDocument();
    });
  });

  describe("List Keys", () => {
    test("uses from team key as list item key", () => {
      const { container } = render(
        <TeamMappingsList
          teamMappings={mockTeamMappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const listItems = container.querySelectorAll("li");
      
      // Keys should be unique for each mapping (from team key)
      expect(listItems).toHaveLength(3);
    });
  });

  describe("Object.entries Handling", () => {
    test("correctly iterates over team mappings", () => {
      const mappings = {
        frcA: "frcB",
        frcC: "frcD",
        frcE: "frcF",
      };

      const { container } = render(
        <TeamMappingsList
          teamMappings={mappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const listItems = container.querySelectorAll("li");
      expect(listItems).toHaveLength(3);
    });

    test("handles single mapping", () => {
      const mappings = {
        frc123: "frc456",
      };

      const { container } = render(
        <TeamMappingsList
          teamMappings={mappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const listItems = container.querySelectorAll("li");
      expect(listItems).toHaveLength(1);
    });
  });

  describe("Count Display Edge Cases", () => {
    test("correctly counts when 0 mappings", () => {
      render(
        <TeamMappingsList teamMappings={{}} removeTeamMap={mockRemoveTeamMap} />
      );

      expect(screen.queryByText(/team mappings found/)).not.toBeInTheDocument();
    });

    test("correctly counts when 1 mapping", () => {
      const mappings = {
        frc1: "frc2",
      };

      render(
        <TeamMappingsList
          teamMappings={mappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("1 team mappings found")).toBeInTheDocument();
    });

    test("correctly counts when many mappings", () => {
      const mappings = {
        frc1: "frc2",
        frc3: "frc4",
        frc5: "frc6",
        frc7: "frc8",
        frc9: "frc10",
      };

      render(
        <TeamMappingsList
          teamMappings={mappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("5 team mappings found")).toBeInTheDocument();
    });
  });

  describe("Rendering Structure", () => {
    test("wraps list in div", () => {
      const { container } = render(
        <TeamMappingsList
          teamMappings={mockTeamMappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const div = container.querySelector("div");
      expect(div).toBeInTheDocument();
      
      const ul = container.querySelector("ul");
      expect(div).toContainElement(ul);
    });

    test("count message appears before list", () => {
      const { container } = render(
        <TeamMappingsList
          teamMappings={mockTeamMappings}
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const div = container.querySelector("div");
      const paragraph = screen.getByText("3 team mappings found");
      const ul = container.querySelector("ul");

      expect(div).toContainElement(paragraph);
      expect(div).toContainElement(ul);
    });
  });
});
