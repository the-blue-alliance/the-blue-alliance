/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import TeamMappingItem from "../TeamMappingItem";

describe("TeamMappingItem", () => {
  let mockRemoveTeamMap: jest.Mock;

  beforeEach(() => {
    mockRemoveTeamMap = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering Team Numbers", () => {
    test("renders from team number without frc prefix", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc254"
          toTeamKey="frc254B"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("254", { exact: false })).toBeInTheDocument();
    });

    test("renders to team number without frc prefix", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc254"
          toTeamKey="frc254B"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("254B", { exact: false })).toBeInTheDocument();
    });

    test("handles team numbers with letter suffixes", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc9254"
          toTeamKey="frc254B"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("9254", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("254B", { exact: false })).toBeInTheDocument();
    });

    test("handles large team numbers", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc99999"
          toTeamKey="frc88888"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("99999", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("88888", { exact: false })).toBeInTheDocument();
    });

    test("handles small team numbers", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc1"
          toTeamKey="frc2"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("1", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("2", { exact: false })).toBeInTheDocument();
    });
  });

  describe("Arrow Icon", () => {
    test("renders arrow icon between team numbers", () => {
      const { container } = render(
        <TeamMappingItem
          fromTeamKey="frc123"
          toTeamKey="frc456"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const arrow = container.querySelector(".glyphicon-arrow-right");
      expect(arrow).toBeInTheDocument();
    });

    test("arrow icon has aria-hidden attribute", () => {
      const { container } = render(
        <TeamMappingItem
          fromTeamKey="frc123"
          toTeamKey="frc456"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const arrow = container.querySelector(".glyphicon-arrow-right");
      expect(arrow).toHaveAttribute("aria-hidden", "true");
    });

    test("arrow icon is a span element", () => {
      const { container } = render(
        <TeamMappingItem
          fromTeamKey="frc123"
          toTeamKey="frc456"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const arrow = container.querySelector(".glyphicon-arrow-right");
      expect(arrow?.tagName).toBe("SPAN");
    });
  });

  describe("Remove Button", () => {
    test("renders Remove button", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc123"
          toTeamKey="frc456"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const button = screen.getByText("Remove");
      expect(button).toBeInTheDocument();
    });

    test("Remove button has correct classes", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc123"
          toTeamKey="frc456"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const button = screen.getByText("Remove");
      expect(button).toHaveClass("btn", "btn-danger");
    });

    test("clicking Remove button calls removeTeamMap with fromTeamKey", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc123"
          toTeamKey="frc456"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const button = screen.getByText("Remove");
      fireEvent.click(button);

      expect(mockRemoveTeamMap).toHaveBeenCalledTimes(1);
      expect(mockRemoveTeamMap).toHaveBeenCalledWith("frc123");
    });

    test("clicking Remove button multiple times calls removeTeamMap each time", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc789"
          toTeamKey="frc101"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const button = screen.getByText("Remove");
      fireEvent.click(button);
      fireEvent.click(button);
      fireEvent.click(button);

      expect(mockRemoveTeamMap).toHaveBeenCalledTimes(3);
      expect(mockRemoveTeamMap).toHaveBeenCalledWith("frc789");
    });

    test("calls removeTeamMap with correct key for different teams", () => {
      const { rerender } = render(
        <TeamMappingItem
          fromTeamKey="frc100"
          toTeamKey="frc200"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      fireEvent.click(screen.getByText("Remove"));
      expect(mockRemoveTeamMap).toHaveBeenCalledWith("frc100");

      mockRemoveTeamMap.mockClear();

      rerender(
        <TeamMappingItem
          fromTeamKey="frc300"
          toTeamKey="frc400"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      fireEvent.click(screen.getByText("Remove"));
      expect(mockRemoveTeamMap).toHaveBeenCalledWith("frc300");
    });
  });

  describe("Rendering Structure", () => {
    test("wraps content in paragraph tag", () => {
      const { container } = render(
        <TeamMappingItem
          fromTeamKey="frc123"
          toTeamKey="frc456"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const paragraph = container.querySelector("p");
      expect(paragraph).toBeInTheDocument();
      expect(paragraph).toHaveTextContent("123");
      expect(paragraph).toHaveTextContent("456");
    });

    test("button is inside paragraph", () => {
      const { container } = render(
        <TeamMappingItem
          fromTeamKey="frc123"
          toTeamKey="frc456"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const paragraph = container.querySelector("p");
      const button = screen.getByText("Remove");

      expect(paragraph).toContainElement(button);
    });

    test("content order is: fromTeam, arrow, toTeam, button", () => {
      const { container } = render(
        <TeamMappingItem
          fromTeamKey="frc123"
          toTeamKey="frc456"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      const paragraph = container.querySelector("p");
      const textContent = paragraph?.textContent || "";

      // Check that elements appear in order
      const fromIndex = textContent.indexOf("123");
      const toIndex = textContent.indexOf("456");
      const removeIndex = textContent.indexOf("Remove");

      expect(fromIndex).toBeLessThan(toIndex);
      expect(toIndex).toBeLessThan(removeIndex);
    });
  });

  describe("substr Edge Cases", () => {
    test("handles fromTeamKey with exactly 'frc' prefix", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc"
          toTeamKey="frc"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      // substr(3) on "frc" returns empty string
      const paragraph = screen.getByRole("paragraph");
      expect(paragraph).toBeInTheDocument();
    });

    test("handles fromTeamKey shorter than 3 characters", () => {
      render(
        <TeamMappingItem
          fromTeamKey="fr"
          toTeamKey="c"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      // substr(3) on "fr" returns empty string
      const paragraph = screen.getByRole("paragraph");
      expect(paragraph).toBeInTheDocument();
    });

    test("handles team keys with no prefix", () => {
      render(
        <TeamMappingItem
          fromTeamKey="123"
          toTeamKey="456"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      // substr(3) on "123" returns empty string
      const paragraph = screen.getByRole("paragraph");
      expect(paragraph).toBeInTheDocument();
    });
  });

  describe("Different Team Mapping Scenarios", () => {
    test("maps regular team to backup team", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc9254"
          toTeamKey="frc254"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("9254", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("254", { exact: false })).toBeInTheDocument();
    });

    test("maps team to team with letter suffix", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc254"
          toTeamKey="frc254B"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("254", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("254B", { exact: false })).toBeInTheDocument();
    });

    test("maps team with letter to another team", () => {
      render(
        <TeamMappingItem
          fromTeamKey="frc254C"
          toTeamKey="frc254"
          removeTeamMap={mockRemoveTeamMap}
        />
      );

      expect(screen.getByText("254C", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("254", { exact: false })).toBeInTheDocument();
    });
  });
});
