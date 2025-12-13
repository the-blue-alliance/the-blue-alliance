import React from "react";

interface TeamMappingItemProps {
  fromTeamKey: string;
  toTeamKey: string;
  removeTeamMap: (fromTeamKey: string) => void;
}

const TeamMappingItem: React.FC<TeamMappingItemProps> = ({
  fromTeamKey,
  toTeamKey,
  removeTeamMap,
}) => {
  const onRemoveClick = () => {
    removeTeamMap(fromTeamKey);
  };

  return (
    <p>
      {fromTeamKey.substr(3)}{" "}
      <span className="glyphicon glyphicon-arrow-right" aria-hidden="true" />{" "}
      {toTeamKey.substr(3)} &nbsp;
      <button className="btn btn-danger" onClick={onRemoveClick}>
        Remove
      </button>
    </p>
  );
};

export default TeamMappingItem;
