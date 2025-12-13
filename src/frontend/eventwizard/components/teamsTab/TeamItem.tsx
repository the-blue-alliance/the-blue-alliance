import React from "react";

interface TeamItemProps {
  team_number: number;
  nickname: string;
}

const TeamItem: React.FC<TeamItemProps> = ({ team_number, nickname }) => (
  <p>
    Team {team_number} -{" "}
    <a href={`/team/${team_number}`}>{nickname}</a>
  </p>
);

export default TeamItem;
