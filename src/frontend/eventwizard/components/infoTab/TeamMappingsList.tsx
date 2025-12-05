import React from "react";
import TeamMappingItem from "./TeamMappingItem";

interface TeamMappingsListProps {
  teamMappings: Record<string, string>;
  removeTeamMap: (fromTeamKey: string) => void;
}

const TeamMappingsList: React.FC<TeamMappingsListProps> = ({
  teamMappings,
  removeTeamMap,
}) => (
  <div>
    {Object.keys(teamMappings).length > 0 && (
      <p>{Object.keys(teamMappings).length} team mappings found</p>
    )}
    <ul>
      {Object.entries(teamMappings).map((teamKeys) => (
        <li key={teamKeys[0]}>
          <TeamMappingItem
            fromTeamKey={teamKeys[0]}
            toTeamKey={teamKeys[1]}
            removeTeamMap={removeTeamMap}
          />
        </li>
      ))}
    </ul>
  </div>
);

export default TeamMappingsList;
