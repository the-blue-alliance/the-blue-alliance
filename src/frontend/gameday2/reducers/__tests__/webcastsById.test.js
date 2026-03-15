import { SET_WEBCASTS_RAW } from "../../constants/ActionTypes";
import { webcastsById, specialWebcastIds } from "../webcastsById";

describe("webcastsById reducer", () => {
  it("maps scheduled_start_time_utc to scheduledStartTimeUtc", () => {
    const action = {
      type: SET_WEBCASTS_RAW,
      webcasts: {
        special_webcasts: [
          {
            key_name: "special_webcast",
            name: "Special Webcast",
            type: "youtube",
            channel: "channel_1",
            status: "offline",
            scheduled_start_time_utc: "2026-03-14T15:30:00Z",
          },
        ],
        ongoing_events_w_webcasts: [
          {
            key: "2026casj",
            name: "San Jose Regional",
            short_name: "San Jose",
            webcasts: [
              {
                type: "youtube",
                channel: "channel_2",
                status: "offline",
                scheduled_start_time_utc: "2026-03-14T16:00:00Z",
              },
            ],
          },
        ],
      },
    };

    const state = webcastsById({}, action);

    expect(state["special_webcast-0"].scheduledStartTimeUtc).toEqual(
      "2026-03-14T15:30:00Z"
    );
    expect(state["2026casj-0"].scheduledStartTimeUtc).toEqual(
      "2026-03-14T16:00:00Z"
    );
  });
});

describe("specialWebcastIds reducer", () => {
  it("tracks special webcast IDs", () => {
    const action = {
      type: SET_WEBCASTS_RAW,
      webcasts: {
        special_webcasts: [
          {
            key_name: "special_webcast",
            name: "Special Webcast",
            type: "youtube",
            channel: "channel_1",
          },
        ],
      },
    };

    const state = specialWebcastIds({}, action);

    expect(state.has("special_webcast-0")).toEqual(true);
  });
});
