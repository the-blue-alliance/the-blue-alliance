import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import AddRemoveTeamMap from "../AddRemoveTeamMap";

// Mock TeamMappingsList component
jest.mock("../TeamMappingsList", () => (props) => (
  <div
    data-testid="team-mappings-list"
    data-mapping-count={Object.keys(props.teamMappings).length}
  />
));

describe("AddRemoveTeamMap", () => {
  const mockAddTeamMap = jest.fn();
  const mockRemoveTeamMap = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders the form group with label", () => {
    const html = renderToStaticMarkup(
      <AddRemoveTeamMap
        eventInfo={null}
        addTeamMap={mockAddTeamMap}
        removeTeamMap={mockRemoveTeamMap}
      />
    );
    expect(html).toContain("form-group row");
    expect(html).toContain("Team Mappings");
  });

  it("shows warning note about removing mappings", () => {
    const html = renderToStaticMarkup(
      <AddRemoveTeamMap
        eventInfo={null}
        addTeamMap={mockAddTeamMap}
        removeTeamMap={mockRemoveTeamMap}
      />
    );
    expect(html).toContain("Removing a mapping will not unmap existing data!");
  });

  it("shows 'No team mappings found' when eventInfo is null", () => {
    const html = renderToStaticMarkup(
      <AddRemoveTeamMap
        eventInfo={null}
        addTeamMap={mockAddTeamMap}
        removeTeamMap={mockRemoveTeamMap}
      />
    );
    expect(html).toContain("No team mappings found");
  });

  it("shows 'No team mappings found' when remap_teams is empty", () => {
    const eventInfo = {
      remap_teams: {},
    };
    const html = renderToStaticMarkup(
      <AddRemoveTeamMap
        eventInfo={eventInfo}
        addTeamMap={mockAddTeamMap}
        removeTeamMap={mockRemoveTeamMap}
      />
    );
    expect(html).toContain("No team mappings found");
  });

  it("renders TeamMappingsList when mappings exist", () => {
    const eventInfo = {
      remap_teams: {
        frc9254: "frc254",
        frc9971: "frc971",
      },
    };
    const html = renderToStaticMarkup(
      <AddRemoveTeamMap
        eventInfo={eventInfo}
        addTeamMap={mockAddTeamMap}
        removeTeamMap={mockRemoveTeamMap}
      />
    );
    expect(html).toContain('data-testid="team-mappings-list"');
    expect(html).toContain('data-mapping-count="2"');
  });

  it("renders input fields for adding team mappings", () => {
    const html = renderToStaticMarkup(
      <AddRemoveTeamMap
        eventInfo={null}
        addTeamMap={mockAddTeamMap}
        removeTeamMap={mockRemoveTeamMap}
      />
    );
    expect(html).toContain('placeholder="9254"');
    expect(html).toContain('placeholder="254B"');
  });

  it("disables input fields when eventInfo is null", () => {
    const html = renderToStaticMarkup(
      <AddRemoveTeamMap
        eventInfo={null}
        addTeamMap={mockAddTeamMap}
        removeTeamMap={mockRemoveTeamMap}
      />
    );
    expect(html).toContain("disabled");
  });

  it("renders arrow icon between input fields", () => {
    const html = renderToStaticMarkup(
      <AddRemoveTeamMap
        eventInfo={null}
        addTeamMap={mockAddTeamMap}
        removeTeamMap={mockRemoveTeamMap}
      />
    );
    expect(html).toContain("glyphicon-arrow-right");
    expect(html).toContain("input-group-addon");
  });

  it("renders Add Mapping button", () => {
    const html = renderToStaticMarkup(
      <AddRemoveTeamMap
        eventInfo={null}
        addTeamMap={mockAddTeamMap}
        removeTeamMap={mockRemoveTeamMap}
      />
    );
    expect(html).toContain("Add Mapping");
  });

  it("uses proper Bootstrap classes", () => {
    const html = renderToStaticMarkup(
      <AddRemoveTeamMap
        eventInfo={null}
        addTeamMap={mockAddTeamMap}
        removeTeamMap={mockRemoveTeamMap}
      />
    );
    expect(html).toContain("col-sm-2");
    expect(html).toContain("col-sm-10");
    expect(html).toContain("control-label");
    expect(html).toContain("form-control");
  });

  it("renders input-group for team number inputs", () => {
    const html = renderToStaticMarkup(
      <AddRemoveTeamMap
        eventInfo={null}
        addTeamMap={mockAddTeamMap}
        removeTeamMap={mockRemoveTeamMap}
      />
    );
    expect(html).toContain("input-group");
  });

  it("calls addTeamMap with formatted team keys", () => {
    const eventInfo = { remap_teams: {} };
    const component = new AddRemoveTeamMap({
      eventInfo,
      addTeamMap: mockAddTeamMap,
      removeTeamMap: mockRemoveTeamMap,
    });

    // Set state directly instead of calling setState
    component.state.nextFromTeam = "9254";
    component.state.nextToTeam = "254";
    component.onAddTeamMapClick();

    expect(mockAddTeamMap).toHaveBeenCalledWith("frc9254", "frc254");
  });

  it("clears state after adding team mapping", () => {
    const eventInfo = { remap_teams: {} };
    const component = new AddRemoveTeamMap({
      eventInfo,
      addTeamMap: mockAddTeamMap,
      removeTeamMap: mockRemoveTeamMap,
    });

    // Spy on setState to verify it's called with empty values
    const setStateSpy = jest.spyOn(component, "setState");

    // Set state directly
    component.state.nextFromTeam = "9254";
    component.state.nextToTeam = "254";
    component.onAddTeamMapClick();

    expect(setStateSpy).toHaveBeenCalledWith({
      nextFromTeam: "",
      nextToTeam: "",
      fromError: false,
      toError: false,
    });
  });

  it("validates fromTeam input and sets error for invalid values", () => {
    const eventInfo = { remap_teams: {} };
    const component = new AddRemoveTeamMap({
      eventInfo,
      addTeamMap: mockAddTeamMap,
      removeTeamMap: mockRemoveTeamMap,
    });

    const setStateSpy = jest.spyOn(component, "setState");
    component.onNextFromTeamChange({ target: { value: "invalid" } });

    expect(setStateSpy).toHaveBeenCalledWith({
      nextFromTeam: "invalid",
      fromError: true,
    });
  });

  it("validates fromTeam input and clears error for valid values", () => {
    const eventInfo = { remap_teams: {} };
    const component = new AddRemoveTeamMap({
      eventInfo,
      addTeamMap: mockAddTeamMap,
      removeTeamMap: mockRemoveTeamMap,
    });

    const setStateSpy = jest.spyOn(component, "setState");
    component.onNextFromTeamChange({ target: { value: "9254" } });

    expect(setStateSpy).toHaveBeenCalledWith({
      nextFromTeam: "9254",
      fromError: false,
    });
  });

  it("validates toTeam input and accepts letters", () => {
    const eventInfo = { remap_teams: {} };
    const component = new AddRemoveTeamMap({
      eventInfo,
      addTeamMap: mockAddTeamMap,
      removeTeamMap: mockRemoveTeamMap,
    });

    const setStateSpy = jest.spyOn(component, "setState");
    component.onNextToTeamChange({ target: { value: "254B" } });

    expect(setStateSpy).toHaveBeenCalledWith({
      nextToTeam: "254B",
      toError: false,
    });
  });

  it("validates toTeam input and sets error for invalid values", () => {
    const eventInfo = { remap_teams: {} };
    const component = new AddRemoveTeamMap({
      eventInfo,
      addTeamMap: mockAddTeamMap,
      removeTeamMap: mockRemoveTeamMap,
    });

    const setStateSpy = jest.spyOn(component, "setState");
    component.onNextToTeamChange({ target: { value: "invalid!@#" } });

    expect(setStateSpy).toHaveBeenCalledWith({
      nextToTeam: "invalid!@#",
      toError: true,
    });
  });
});
