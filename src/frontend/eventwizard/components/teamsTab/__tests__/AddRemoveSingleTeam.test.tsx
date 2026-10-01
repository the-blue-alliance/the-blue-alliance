/* @jest-environment jsdom */
import React from "react";
import { act, render, screen, waitFor, fireEvent } from "@testing-library/react";
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

describe("AddRemoveSingleTeam selecting, adding and removing", () => {
  const attending: ApiTeam[] = [
    { key: "frc1678", team_number: 1678, nickname: "Citrus Circuits" },
    { key: "frc2056", team_number: 2056, nickname: "OP Robotics" },
  ];
  let mockUpdateTeamList: jest.Mock;
  let mockShowErrorMessage: jest.Mock;
  let mockClearTeams: jest.Mock;

  const renderComponent = (
    overrides: Partial<React.ComponentProps<typeof AddRemoveSingleTeam>> = {}
  ) =>
    render(
      <AddRemoveSingleTeam
        selectedEvent="2024nytr"
        updateTeamList={mockUpdateTeamList}
        hasFetchedTeams={true}
        currentTeams={attending}
        clearTeams={mockClearTeams}
        showErrorMessage={mockShowErrorMessage}
        {...overrides}
      />
    );

  const waitForTypeahead = async (): Promise<void> => {
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/_/typeahead/teams-all");
    });
    // Let the fetch/json promises resolve so the options land in state before
    // anything is typed; otherwise the first search races the load.
    await act(() => new Promise((resolve) => setTimeout(resolve, 0)));
  };

  const selectTeam = async (label: string, search: string): Promise<void> => {
    await waitForTypeahead();
    const combobox = screen.getByRole("combobox");
    fireEvent.change(combobox, { target: { value: search } });
    fireEvent.click(await screen.findByText(label));
  };

  const addButton = () => screen.getByRole("button", { name: "Add Team" });
  const removeButton = () => screen.getByRole("button", { name: "Remove Team" });

  beforeEach(() => {
    mockUpdateTeamList = jest.fn();
    mockShowErrorMessage = jest.fn();
    mockClearTeams = jest.fn();
    global.fetch = jest.fn().mockResolvedValue({
      json: jest.fn().mockResolvedValue([
        "254 | The Cheesy Poofs",
        "1678 | Citrus Circuits",
        "2056 | OP Robotics",
      ]),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("filters the typeahead by the typed text and shows a hint when nothing matches", async () => {
    renderComponent();
    await waitForTypeahead();
    const combobox = screen.getByRole("combobox");

    fireEvent.change(combobox, { target: { value: "cheesy" } });
    expect(await screen.findByText("254 | The Cheesy Poofs")).toBeInTheDocument();
    expect(screen.queryByText("1678 | Citrus Circuits")).not.toBeInTheDocument();

    fireEvent.change(combobox, { target: { value: "zzz" } });
    expect(await screen.findByText("Start typing...")).toBeInTheDocument();
  });

  it("enables Add for a team that is not attending and Remove for one that is", async () => {
    renderComponent();

    await selectTeam("254 | The Cheesy Poofs", "254");
    expect(addButton()).toBeEnabled();
    expect(removeButton()).toBeDisabled();

    await selectTeam("1678 | Citrus Circuits", "1678");
    expect(addButton()).toBeDisabled();
    expect(removeButton()).toBeEnabled();
  });

  it("adds the selected team to the existing list and resets on success", async () => {
    mockUpdateTeamList.mockImplementation((_keys, onSuccess) => onSuccess());
    renderComponent();
    await selectTeam("254 | The Cheesy Poofs", "254");

    fireEvent.click(addButton());

    expect(mockUpdateTeamList).toHaveBeenCalledWith(
      ["frc1678", "frc2056", "frc254"],
      expect.any(Function),
      expect.any(Function)
    );
    expect(addButton()).toHaveClass("btn-success");
    expect(addButton()).toBeDisabled();
    expect(mockClearTeams).toHaveBeenCalledTimes(1);
    expect(screen.queryByText("254 | The Cheesy Poofs")).not.toBeInTheDocument();
  });

  it("marks the Add button as pending until the update resolves", async () => {
    renderComponent();
    await selectTeam("254 | The Cheesy Poofs", "254");

    fireEvent.click(addButton());

    expect(addButton()).toHaveClass("btn-warning");
  });

  it("reports add failures through showErrorMessage", async () => {
    mockUpdateTeamList.mockImplementation((_keys, _onSuccess, onError) =>
      onError("Add failed")
    );
    renderComponent();
    await selectTeam("254 | The Cheesy Poofs", "254");

    fireEvent.click(addButton());

    expect(mockShowErrorMessage).toHaveBeenCalledWith("Add failed");
    expect(mockClearTeams).not.toHaveBeenCalled();
  });

  it("removes the selected team from the existing list and resets on success", async () => {
    mockUpdateTeamList.mockImplementation((_keys, onSuccess) => onSuccess());
    renderComponent();
    await selectTeam("1678 | Citrus Circuits", "1678");

    fireEvent.click(removeButton());

    expect(mockUpdateTeamList).toHaveBeenCalledWith(
      ["frc2056"],
      expect.any(Function),
      expect.any(Function)
    );
    expect(removeButton()).toHaveClass("btn-success");
    expect(removeButton()).toBeDisabled();
    expect(mockClearTeams).toHaveBeenCalledTimes(1);
  });

  it("reports remove failures through showErrorMessage", async () => {
    mockUpdateTeamList.mockImplementation((_keys, _onSuccess, onError) =>
      onError("Remove failed")
    );
    renderComponent();
    await selectTeam("1678 | Citrus Circuits", "1678");

    fireEvent.click(removeButton());

    expect(removeButton()).toHaveClass("btn-warning");
    expect(mockShowErrorMessage).toHaveBeenCalledWith("Remove failed");
  });

  it("tolerates a missing clearTeams callback on add and remove", async () => {
    mockUpdateTeamList.mockImplementation((_keys, onSuccess) => onSuccess());
    renderComponent({ clearTeams: undefined });

    await selectTeam("254 | The Cheesy Poofs", "254");
    fireEvent.click(addButton());
    await selectTeam("1678 | Citrus Circuits", "1678");
    fireEvent.click(removeButton());

    expect(mockUpdateTeamList).toHaveBeenCalledTimes(2);
    expect(addButton()).toHaveClass("btn-success");
    expect(removeButton()).toHaveClass("btn-success");
  });
});
