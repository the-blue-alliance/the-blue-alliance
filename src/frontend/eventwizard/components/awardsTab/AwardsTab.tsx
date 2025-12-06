import React, { useState, ChangeEvent } from "react";

interface Award {
  type_enum: number | null;
  name_str: string;
  team_key: string | null;
  awardee: string | null;
}

interface AwardsTabProps {
  selectedEvent: string;
  makeTrustedRequest: (
    requestPath: string,
    requestBody: string
  ) => Promise<Response>;
}

const getAwardKey = (
  type_enum: number | null,
  name_str: string,
  team_key: string | null,
  awardee: string | null
): string => {
  return `${type_enum}_${name_str}_${team_key}_${awardee}`;
};

function AwardsTab({ selectedEvent, makeTrustedRequest }: AwardsTabProps): React.ReactElement {
  const [updating, setUpdating] = useState(false);
  const [awards, setAwards] = useState<Award[]>([]);
  const [awardsFetched, setAwardsFetched] = useState(false);
  const [awardsToDelete, setAwardsToDelete] = useState(new Set<string>());

  const [newAwardType, setNewAwardType] = useState("");
  const [newAwardName, setNewAwardName] = useState("");
  const [newAwardTeamNumber, setNewAwardTeamNumber] = useState("");
  const [newAwardAwardee, setNewAwardAwardee] = useState("");

  const fetchAwards = async (): Promise<void> => {
    setUpdating(true);
    const response = await fetch(`/api/v3/event/${selectedEvent}/awards`, {
      credentials: "same-origin",
    });
    const rawAwards: Array<{
      award_type: number;
      name: string;
      recipient_list: Array<{ team_key: string | null; awardee: string | null }>;
    }> = await response.json();

    // Store awards flattened, in the format for the trusted API.
    const awards: Award[] = [];
    rawAwards.forEach(({ award_type, name, recipient_list }) => {
      recipient_list.forEach(({ team_key, awardee }) => {
        awards.push({
          type_enum: award_type,
          name_str: name,
          team_key,
          awardee,
        });
      });
    });

    setAwards(awards);
    setUpdating(false);
    setAwardsFetched(true);
  };

  const addAward = (): void => {
    const newAward: Award = {
      type_enum: newAwardType !== "" ? Number(newAwardType) : null,
      name_str: newAwardName,
      team_key: newAwardTeamNumber !== "" ? `frc${newAwardTeamNumber}` : null,
      awardee: newAwardAwardee !== "" ? newAwardAwardee : null,
    };
    setAwards((prevAwards) => [...prevAwards, newAward]);
  };

  const toggleDeletion = (awardKey: string): void => {
    setAwardsToDelete((prevAwardsToDelete) => {
      const newAwardsToDelete = new Set(prevAwardsToDelete);
      if (newAwardsToDelete.has(awardKey)) {
        newAwardsToDelete.delete(awardKey);
      } else {
        newAwardsToDelete.add(awardKey);
      }
      return newAwardsToDelete;
    });
  };

  const saveEdits = async (): Promise<void> => {
    setUpdating(true);
    const awardsToSave = awards.filter(
      (award) =>
        !awardsToDelete.has(
          getAwardKey(
            award.type_enum,
            award.name_str,
            award.team_key,
            award.awardee
          )
        )
    );

    try {
      await makeTrustedRequest(
        `/api/trusted/v1/event/${selectedEvent}/awards/update`,
        JSON.stringify(awardsToSave)
      );
      setUpdating(false);
    } catch (error) {
      alert(`There was an error: ${error}`);
      setUpdating(false);
    }
  };

  const sortedAwards = [...awards].sort((a, b) => (a.type_enum || 0) - (b.type_enum || 0));

  return (
    <div className="tab-pane" id="awards">
      <h3>Awards</h3>
      <p>Note: Be sure to fetch existing awards before making edits.</p>
      <button
        className="btn btn-info"
        onClick={fetchAwards}
        disabled={updating}
      >
        Fetch Awards
      </button>

      <hr />

      <h4>Add Award</h4>
      <p>
        If an award type is not specified, we will automatically try to
        determine it from the award name. Note that this is not guaranteed to
        work, especially for offseason events.
      </p>
      <p>
        For a list of award type enums, see{" "}
        <a
          href="https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/common/consts/award_type.py"
          target="_blank"
          rel="noopener noreferrer"
        >
          here
        </a>
        .
      </p>

      <div className="form-group">
        <label htmlFor="award_type" className="col-sm-4 control-label">
          Award Type
        </label>
        <div className="col-sm-8">
          <input
            type="text"
            className="form-control"
            id="award_type"
            value={newAwardType}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setNewAwardType(e.target.value)}
            placeholder="3"
          />
        </div>

        <label htmlFor="award_name" className="col-sm-4 control-label">
          Award Name (Required)
        </label>
        <div className="col-sm-8">
          <input
            type="text"
            className="form-control"
            id="award_name"
            value={newAwardName}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setNewAwardName(e.target.value)}
            placeholder="Woodie Flowers Finalist Award"
          />
        </div>

        <label htmlFor="award_team" className="col-sm-4 control-label">
          Team Number
        </label>
        <div className="col-sm-8">
          <input
            type="text"
            className="form-control"
            id="award_team"
            value={newAwardTeamNumber}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setNewAwardTeamNumber(e.target.value)}
            placeholder="604"
          />
        </div>

        <label htmlFor="award_awardee" className="col-sm-4 control-label">
          Awardee
        </label>
        <div className="col-sm-8">
          <input
            type="text"
            className="form-control"
            id="award_awardee"
            value={newAwardAwardee}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setNewAwardAwardee(e.target.value)}
            placeholder="Helen Arrington"
          />
        </div>
      </div>
      <button className="btn btn-info" onClick={addAward} disabled={updating}>
        Add Award
      </button>

      <hr />

      <h4>Award List</h4>
      <table className="table">
        <thead>
          <tr>
            <th>Award Type</th>
            <th>Name</th>
            <th>Team</th>
            <th>Awardee</th>
            <th>Keep/Delete</th>
          </tr>
        </thead>
        <tbody>
          {sortedAwards.map(({ type_enum, name_str, team_key, awardee }) => {
            const awardKey = getAwardKey(
              type_enum,
              name_str,
              team_key,
              awardee
            );
            const toDelete = awardsToDelete.has(awardKey);
            return (
              <tr key={awardKey}>
                <td>{type_enum}</td>
                <td>{name_str}</td>
                <td>{team_key}</td>
                <td>{awardee}</td>
                <td>
                  <button
                    className={toDelete ? "btn btn-danger" : "btn"}
                    onClick={() => toggleDeletion(awardKey)}
                  >
                    {toDelete ? "Will be deleted" : "Keep"}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <hr />

      <h4>Save Edits</h4>
      <p>All existing awards will be overwritten with the awards above!</p>
      <p>
        Please ensure that you have fetched existing awards before submitting!
      </p>
      <button
        className="btn btn-danger"
        onClick={saveEdits}
        disabled={updating || !awardsFetched}
      >
        Save Edits
      </button>
    </div>
  );
}

export default AwardsTab;
