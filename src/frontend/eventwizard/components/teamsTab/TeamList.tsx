import React from "react";
import TeamItem from "./TeamItem";
import { ApiTeam } from "../../constants/ApiTeam";

interface TeamListProps {
  teams: ApiTeam[];
}

const TeamList: React.FC<TeamListProps> = ({ teams }) => (
  <div>
    {teams.length > 0 && <p>{teams.length} teams attending</p>}
    <ul>
      {teams.map((team) => (
        <TeamItem
          key={team.key}
          team_number={team.team_number}
          nickname={team.nickname}
        />
      ))}
    </ul>
  </div>
);

export default TeamList;
