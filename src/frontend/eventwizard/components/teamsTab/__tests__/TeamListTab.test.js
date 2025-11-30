import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import TeamListTab from "../TeamListTab";

// Use real child components (don't mock) — assert on their rendered labels

describe("TeamListTab", () => {
  const mockMakeTrustedRequest = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders the main container with correct structure", () => {
    const html = renderToStaticMarkup(
      <TeamListTab
        selectedEvent={"2025myevent"}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );
    expect(html).toContain("tab-pane");
    expect(html).toContain("Team List");
    // Child components render their labels/content
    expect(html).toContain("Import FMS Report");
    expect(html).toContain("Add/Remove Single Team");
    expect(html).toContain("Add Multiple Teams");
    expect(html).toContain("Currently Attending Teams");
  });

  it("updateTeamList calls makeTrustedRequest with correct args", () => {
    const component = new TeamListTab({
      selectedEvent: "2025myevent",
      makeTrustedRequest: mockMakeTrustedRequest,
    });

    const teamKeys = ["frc254", "frc1114"];
    const onSuccess = jest.fn();
    const onError = jest.fn();

    component.updateTeamList(teamKeys, onSuccess, onError);

    expect(mockMakeTrustedRequest).toHaveBeenCalled();
    const callArgs = mockMakeTrustedRequest.mock.calls[0];
    expect(callArgs[0]).toBe(
      "/api/trusted/v1/event/2025myevent/team_list/update"
    );
    expect(callArgs[1]).toBe(JSON.stringify(teamKeys));
    expect(callArgs[2]).toBe(onSuccess);
    expect(callArgs[3]).toBe(onError);
  });

  it("showError sets showErrorDialog and errorMessage via setState", () => {
    const component = new TeamListTab({
      selectedEvent: "e",
      makeTrustedRequest: mockMakeTrustedRequest,
    });
    const setStateSpy = jest.spyOn(component, "setState");

    component.showError("boom");

    expect(setStateSpy).toHaveBeenCalledWith({
      showErrorDialog: true,
      errorMessage: "boom",
    });
  });

  it("clearError clears the error dialog via setState", () => {
    const component = new TeamListTab({
      selectedEvent: "e",
      makeTrustedRequest: mockMakeTrustedRequest,
    });
    const setStateSpy = jest.spyOn(component, "setState");

    component.clearError();

    expect(setStateSpy).toHaveBeenCalledWith({
      showErrorDialog: false,
      errorMessage: "",
    });
  });

  it("updateTeams sets teams and hasFetchedTeams via setState", () => {
    const component = new TeamListTab({
      selectedEvent: "e",
      makeTrustedRequest: mockMakeTrustedRequest,
    });
    const setStateSpy = jest.spyOn(component, "setState");

    const teams = [{ team_key: "frc254" }];
    component.updateTeams(teams);

    expect(setStateSpy).toHaveBeenCalledWith({ teams, hasFetchedTeams: true });
  });

  it("clearTeams clears teams and resets hasFetchedTeams via setState", () => {
    const component = new TeamListTab({
      selectedEvent: "e",
      makeTrustedRequest: mockMakeTrustedRequest,
    });
    const setStateSpy = jest.spyOn(component, "setState");

    component.clearTeams();

    expect(setStateSpy).toHaveBeenCalledWith({
      teams: [],
      hasFetchedTeams: false,
    });
  });

  it("clears teams when selectedEvent changes in UNSAFE_componentWillReceiveProps", () => {
    const component = new TeamListTab({
      selectedEvent: "A",
      makeTrustedRequest: mockMakeTrustedRequest,
    });
    const setStateSpy = jest.spyOn(component, "setState");

    // Simulate that teams had been fetched
    component.state.teams = [{ team_key: "frc254" }];
    component.UNSAFE_componentWillReceiveProps({ selectedEvent: "B" });

    expect(setStateSpy).toHaveBeenCalledWith({
      teams: [],
      hasFetchedTeams: false,
    });
  });
});
