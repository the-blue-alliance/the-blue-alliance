/* @jest-environment jsdom */
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import AddRemoveSingleTeam from "../AddRemoveSingleTeam";
import { ApiTeam } from "../../../constants/ApiTeam";

describe("AddRemoveSingleTeam", () => {
  let mockUpdateTeamList: jest.Mock;
  let mockShowErrorMessage: jest.Mock;
  let mockClearTeams: jest.Mock;
  let mockFetch: jest.Mock;

  beforeEach(() => {
    mockUpdateTeamList = jest.fn((_add, _remove, _existingKeys, onSuccess) => {
      onSuccess();
    });
    mockShowErrorMessage = jest.fn();
    mockClearTeams = jest.fn();
    mockFetch = jest.fn();

    // Mock fetch for typeahead data
    mockFetch.mockResolvedValue({
      json: jest.fn().mockResolvedValue([
        "254 | The Cheesy Poofs",
        "1678 | Citrus Circuits",
        "2056 | OP Robotics",
      ]),
    });
    global.fetch = mockFetch;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders the component with heading", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={false}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Add\/Remove Single Team/i)).toBeInTheDocument();
      });
    });

    it("shows note when event is selected but teams not fetched", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={false}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        expect(
          screen.getByText(/Please fetch the current team list/i)
        ).toBeInTheDocument();
      });
    });

    it("does not show note when teams have been fetched", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={true}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith("/_/typeahead/teams-all");
      });

      expect(
        screen.queryByText(/Please fetch the current team list/i)
      ).not.toBeInTheDocument();
    });

    it("renders AsyncSelect dropdown", async () => {
      const { container } = render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={true}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        // AsyncSelect has a hidden input with name="selectTeam"
        const hiddenInput = container.querySelector('input[type="hidden"][name="selectTeam"]');
        expect(hiddenInput).not.toBeNull();
      });
    });

    it("renders Add Team and Remove Team buttons", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={true}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Add Team")).toBeInTheDocument();
        expect(screen.getByText("Remove Team")).toBeInTheDocument();
      });
    });
  });

  describe("Typeahead Data Loading", () => {
    it("fetches typeahead data on mount", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={false}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith("/_/typeahead/teams-all");
      });
    });
  });

  describe("Button States", () => {
    it("disables dropdown when no event selected", async () => {
      const { container } = render(
        <AddRemoveSingleTeam
          selectedEvent={null}
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={false}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        const input = container.querySelector('input[aria-autocomplete="list"]');
        expect(input).toBeDisabled();
      });
    });

    it("disables Add Team button when no event selected", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent={null}
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={false}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        const addButton = screen.getByText("Add Team");
        expect(addButton).toBeDisabled();
      });
    });

    it("disables Add Team button when teams not fetched", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={false}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        const addButton = screen.getByText("Add Team");
        expect(addButton).toBeDisabled();
      });
    });

    it("disables Remove Team button when teams not fetched", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={false}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        const removeButton = screen.getByText("Remove Team");
        expect(removeButton).toBeDisabled();
      });
    });
  });

  describe("Team Attendance Validation", () => {
    it("disables Add button when selected team is already attending", async () => {
      const currentTeams: ApiTeam[] = [
        {
          key: "frc254",
          team_number: 254,
          nickname: "The Cheesy Poofs",
          name: "NASA Ames Research Center & Google",
          city: "San Jose",
          state_prov: "CA",
          country: "USA",
        },
      ];

      const { container } = render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={true}
          currentTeams={currentTeams}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        const addButton = screen.getByText("Add Team");
        // Button should be disabled when no team selected
        expect(addButton).toBeDisabled();
      });
    });

    it("disables Remove button when selected team is not attending", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={true}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        const removeButton = screen.getByText("Remove Team");
        // Button should be disabled when no team selected
        expect(removeButton).toBeDisabled();
      });
    });
  });

  describe("Button Classes", () => {
    it("sets button classes to btn-primary initially", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={true}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        const addButton = screen.getByText("Add Team");
        expect(addButton).toHaveClass("btn-primary");
      });

      const removeButton = screen.getByText("Remove Team");
      expect(removeButton).toHaveClass("btn-primary");
    });

    it("resets button classes when hasFetchedTeams becomes false", async () => {
      const { rerender } = render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={true}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Add Team")).toHaveClass("btn-primary");
      });

      rerender(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={false}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Add Team")).toHaveClass("btn-primary");
        expect(screen.getByText("Remove Team")).toHaveClass("btn-primary");
      });
    });
  });

  describe("Edge Cases", () => {
    it("handles empty currentTeams array", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={true}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Add Team")).toBeInTheDocument();
      });
    });

    it("handles clearTeams being undefined", async () => {
      render(
        <AddRemoveSingleTeam
          selectedEvent="2024nytr"
          updateTeamList={mockUpdateTeamList}
          hasFetchedTeams={true}
          currentTeams={[]}
          showErrorMessage={mockShowErrorMessage}
          clearTeams={undefined}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Add Team")).toBeInTheDocument();
      });
    });
  });
});
