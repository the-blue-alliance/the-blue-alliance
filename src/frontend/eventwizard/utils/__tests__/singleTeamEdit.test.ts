import { editSingleTeam, SingleTeamEditRequest } from "../singleTeamEdit";

describe("editSingleTeam", () => {
  const request: SingleTeamEditRequest = {
    eventKey: "2025nysu",
    teamKey: "frc254",
    currentTeamKeys: ["frc1678", "frc254", "frc971"],
    hasFetchedTeams: true,
  };
  const onValid = jest.fn();
  const onInvalid = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it.each(["add", "remove"] as const)(
    "refuses to %s before the team list is fetched",
    (action) => {
      editSingleTeam(
        action,
        { ...request, hasFetchedTeams: false },
        onValid,
        onInvalid
      );

      expect(onValid).not.toHaveBeenCalled();
      expect(onInvalid).toHaveBeenCalledWith(
        "Please fetch teams before modification to ensure up to date data"
      );
    }
  );

  it("appends a team that is not attending", () => {
    editSingleTeam(
      "add",
      { ...request, teamKey: "frc118" },
      onValid,
      onInvalid
    );

    expect(onInvalid).not.toHaveBeenCalled();
    expect(onValid).toHaveBeenCalledWith([
      "frc1678",
      "frc254",
      "frc971",
      "frc118",
    ]);
  });

  it("refuses to add a team that is already attending", () => {
    editSingleTeam("add", request, onValid, onInvalid);

    expect(onValid).not.toHaveBeenCalled();
    expect(onInvalid).toHaveBeenCalledWith(
      "Team frc254 is already attending 2025nysu. Re-fetch the team list if you know this is wrong."
    );
  });

  it("removes an attending team without mutating the input", () => {
    editSingleTeam("remove", request, onValid, onInvalid);

    expect(onInvalid).not.toHaveBeenCalled();
    expect(onValid).toHaveBeenCalledWith(["frc1678", "frc971"]);
    expect(request.currentTeamKeys).toEqual(["frc1678", "frc254", "frc971"]);
  });

  it("refuses to remove a team that is not attending", () => {
    editSingleTeam(
      "remove",
      { ...request, teamKey: "frc118" },
      onValid,
      onInvalid
    );

    expect(onValid).not.toHaveBeenCalled();
    expect(onInvalid).toHaveBeenCalledWith(
      "Team frc118 is already not attending 2025nysu. Re-fetch the team list if you know this is wrong."
    );
  });
});
