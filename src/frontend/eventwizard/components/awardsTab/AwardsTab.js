import React, { useState } from "react";



function AwardsTab({selectedEvent}) {
  selectedEvent = "2023casj"
  const [updating, setUpdating] = useState(false);
  const [awards, setAwards] = useState([]);

  const [newAwardType, setNewAwardType] = useState("");
  const [newAwardName, setNewAwardName] = useState("");
  const [newAwardTeamNumber, setNewAwardTeamNumber] = useState("");
  const [newAwardAwardee, setNewAwardAwardee] = useState("");

  const fetchAwards = async () => {
    setUpdating(true);
    const response = await fetch(`/api/v3/event/${selectedEvent}/awards`, {
      credentials: "same-origin",
    })
    const rawAwards = await response.json();

    // Store awards flattened, in the format for the trusted API.
    const awards = [];
    rawAwards.forEach(({award_type, name, recipient_list}) => {
      recipient_list.forEach(({team_key, awardee}) => {
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
  }

  const addAward = () => {
    const newAward = {
      type_enum: Number(newAwardType),
      name_str: newAwardName,
      team_key: `frc${newAwardTeamNumber}`,
      awardee: newAwardAwardee,
    };
    setAwards(prevAwards => [...prevAwards, newAward]);
  }

  const sortedAwards = awards.sort((a, b) => a.type_enum - b.type_enum);

  return <div className="tab-pane" id="awards">
    <h3>Awards</h3>
    <p>Note: Fetch existing awards before making edits.</p>
    <button className="btn btn-info" onClick={fetchAwards} disabled={updating}>Fetch Awards</button>

    <hr />

    <h4>Add Award</h4>
    <div className="form-group">
      <label htmlFor="award_type" className="col-sm-2 control-label">
        Award Type
      </label>
      <div className="col-sm-10">
        <input
          type="text"
          className="form-control"
          id="award_type"
          value={newAwardType}
          onChange={e => setNewAwardType(e.target.value)}
        />
      </div>

      <label htmlFor="award_name" className="col-sm-2 control-label">
        Name
      </label>
      <div className="col-sm-10">
        <input
          type="text"
          className="form-control"
          id="award_name"
          value={newAwardName}
          onChange={e => setNewAwardName(e.target.value)}
        />
      </div>

      <label htmlFor="award_team" className="col-sm-2 control-label">
        Team Number
      </label>
      <div className="col-sm-10">
        <input
          type="text"
          className="form-control"
          id="award_team"
          value={newAwardTeamNumber}
          onChange={e => setNewAwardTeamNumber(e.target.value)}
        />
      </div>

      <label htmlFor="award_awardee" className="col-sm-2 control-label">
        Awardee
      </label>
      <div className="col-sm-10">
        <input
          type="text"
          className="form-control"
          id="award_awardee"
          value={newAwardAwardee}
          onChange={e => setNewAwardAwardee(e.target.value)}
        />
      </div>
    </div>
    <button className="btn btn-info" onClick={addAward}>Add Award</button>

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
        {sortedAwards.map(({type_enum, name_str, team_key, awardee}) => {
          return (
            <tr key={`${type_enum}_${team_key}_${awardee}`}>
              <td>{type_enum}</td>
              <td>{name_str}</td>
              <td>{team_key}</td>
              <td>{awardee}</td>
              <td><button className="btn">Keep</button></td>
            </tr>
          );
        })}
      </tbody>
    </table>
  </div>
}

export default AwardsTab;
