import React, { useState } from "react";

const getAwardKey = (type_enum, name_str, team_key, awardee) => {
  return `${type_enum}_${name_str}_${team_key}_${awardee}`;
};

function AwardsTab({ selectedEvent, makeTrustedRequest }) {
  const [updating, setUpdating] = useState(false);
  const [awards, setAwards] = useState([]);
  const [awardsFetched, setAwardsFetched] = useState(false);
  const [awardsToDelete, setAwardsToDelete] = useState(new Set());

  const [newAwardType, setNewAwardType] = useState("");
  const [newAwardName, setNewAwardName] = useState("");
  const [newAwardTeamNumber, setNewAwardTeamNumber] = useState("");
  const [newAwardAwardee, setNewAwardAwardee] = useState("");

  const fetchAwards = async () => {
    setUpdating(true);
    const response = await fetch(`/api/v3/event/${selectedEvent}/awards`, {
      credentials: "same-origin",
    });
    const rawAwards = await response.json();

    // Store awards flattened, in the format for the trusted API.
    const awards = [];
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

  const addAward = () => {
    const newAward = {
      type_enum: newAwardType != "" ? Number(newAwardType) : null,
      name_str: newAwardName,
      team_key: newAwardTeamNumber != "" ? `frc${newAwardTeamNumber}` : null,
      awardee: newAwardAwardee != "" ? newAwardAwardee : null,
    };
    setAwards((prevAwards) => [...prevAwards, newAward]);
  };

  const toggleDeletion = (awardKey) => {
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

  const saveEdits = async () => {
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

    makeTrustedRequest(
      `/api/trusted/v1/event/${selectedEvent}/awards/update`,
      JSON.stringify(awardsToSave),
      () => {
        setUpdating(false);
      },
      (error) => {
        alert(`There was an error: ${error}`);
        setUpdating(false);
      }
    );
  };

  const sortedAwards = awards.sort((a, b) => a.type_enum - b.type_enum);

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
            onChange={(e) => setNewAwardType(e.target.value)}
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
            onChange={(e) => setNewAwardName(e.target.value)}
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
            onChange={(e) => setNewAwardTeamNumber(e.target.value)}
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
            onChange={(e) => setNewAwardAwardee(e.target.value)}
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
