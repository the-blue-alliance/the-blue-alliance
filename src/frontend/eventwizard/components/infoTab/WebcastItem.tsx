import React from "react";
import { ApiWebcast } from "../../constants/ApiWebcast";

interface WebcastItemProps {
  webcast: ApiWebcast;
  index: number;
  removeWebcast: (index: number) => void;
}

const WebcastItem: React.FC<WebcastItemProps> = ({
  webcast,
  index,
  removeWebcast,
}) => {
  const onRemoveClick = () => {
    removeWebcast(index);
  };

  let item: string;
  if (webcast.url) {
    item = webcast.url;
  } else {
    item = `${webcast.type} - ${webcast.channel}`;
  }

  if (webcast.date) {
    item += ` (${webcast.date})`;
  }

  return (
    <p>
      {item} &nbsp;
      <button className="btn btn-danger" onClick={onRemoveClick}>
        Remove
      </button>
    </p>
  );
};

export default WebcastItem;
