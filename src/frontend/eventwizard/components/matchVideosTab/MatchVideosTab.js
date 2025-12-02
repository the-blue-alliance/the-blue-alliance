import React, { useState } from "react";

export default function MatchVideosTab({ selectedEvent, makeTrustedRequest }) {
  const [videos, setVideos] = useState([]);
  const [updating, setUpdating] = useState(false);

  const onInputChange = (event) => {
    const lines = event.target.value.split("\n");
    const parsed = lines.map((line) =>
      line.split(",").map((item) => item.trim())
    );
    setVideos(parsed);
  };

  const addMatchVideos = () => {
    makeTrustedRequest(
      `/api/trusted/v1/event/${selectedEvent}/match_videos/add`,
      JSON.stringify(Object.fromEntries(videos)),
      () => {
        setUpdating(false);
      },
      (error) => {
        alert(`There was an error: ${error}`);
        setUpdating(false);
      }
    );
  };

  return (
    <div className="tab-pane" id="match-videos">
      <h4>Add Multiple Videos</h4>
      <p>Enter a list of match_key, YouTube ID (one pair per line).</p>
      <textarea className="form-control" onChange={onInputChange} />
      <button
        className={`btn btn-primary`}
        onClick={addMatchVideos}
        disabled={updating || !selectedEvent}
      >
        Add Videos
      </button>

      <h4>Parsed Videos</h4>
      {videos.map((video) => (
        <div key={`${video[0]}-${video[1]}`}>
          <p>{video[0]}</p>
          <iframe
            width="560"
            height="315"
            src={`https://www.youtube.com/embed/${video[1].replace("t=", "start=")}`}
          ></iframe>
        </div>
      ))}
    </div>
  );
}
