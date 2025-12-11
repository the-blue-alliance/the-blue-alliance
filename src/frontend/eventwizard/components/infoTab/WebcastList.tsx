import React from "react";
import WebcastItem from "./WebcastItem";
import { ApiWebcast } from "../../constants/ApiWebcast";

interface WebcastListProps {
  webcasts: ApiWebcast[];
  removeWebcast: (index: number) => void;
}

const WebcastList: React.FC<WebcastListProps> = ({
  webcasts,
  removeWebcast,
}) => (
  <div>
    {webcasts.length > 0 && <p>{webcasts.length} webcasts found</p>}
    <ul>
      {webcasts.map((webcast, index) => (
        <li key={JSON.stringify(webcast)}>
          <WebcastItem
            webcast={webcast}
            removeWebcast={removeWebcast}
            index={index}
          />
        </li>
      ))}
    </ul>
  </div>
);

export default WebcastList;
