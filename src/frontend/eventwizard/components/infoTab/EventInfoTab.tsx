import React, { Component, ChangeEvent } from "react";
import PlayoffTypeDropdown from "./PlayoffTypeDropdown";
import SyncCodeInput from "./SyncCodeInput";
import AddRemoveWebcast from "./AddRemoveWebcast";
import AddRemoveTeamMap from "./AddRemoveTeamMap";
import { ApiEvent } from "../../constants/ApiEvent";
import ensureRequestSuccess from "../../net/EnsureRequestSuccess";

interface EventInfoTabProps {
  selectedEvent: string | null;
  makeTrustedRequest: (
    path: string,
    body: string,
    successCallback: (response: any) => void,
    errorCallback: (error: any) => void
  ) => void;
}

interface EventInfoTabState {
  eventInfo: ApiEvent | null;
  status: string;
  buttonClass: string;
}

interface PlayoffType {
  label: string;
  value: number;
}

class EventInfoTab extends Component<EventInfoTabProps, EventInfoTabState> {
  constructor(props: EventInfoTabProps) {
    super(props);
    this.state = {
      eventInfo: null,
      status: "",
      buttonClass: "btn-primary",
    };

    this.loadEventInfo = this.loadEventInfo.bind(this);
    this.setPlayoffType = this.setPlayoffType.bind(this);
    this.updateEventInfo = this.updateEventInfo.bind(this);
    this.onFirstCodeChange = this.onFirstCodeChange.bind(this);
    this.addWebcast = this.addWebcast.bind(this);
    this.removeWebcast = this.removeWebcast.bind(this);
    this.addTeamMap = this.addTeamMap.bind(this);
    this.removeTeamMap = this.removeTeamMap.bind(this);
  }

  UNSAFE_componentWillReceiveProps(newProps: EventInfoTabProps): void {
    if (newProps.selectedEvent === null) {
      this.setState({ eventInfo: null, buttonClass: "btn-primary" });
    } else if (newProps.selectedEvent !== this.props.selectedEvent) {
      this.loadEventInfo(newProps.selectedEvent);
      this.setState({ buttonClass: "btn-primary" });
    }
  }

  onFirstCodeChange(event: ChangeEvent<HTMLInputElement>): void {
    const currentInfo = this.state.eventInfo;
    if (currentInfo !== null) {
      currentInfo.first_event_code = event.target.value;
      this.setState({ eventInfo: currentInfo });
    }
  }

  setPlayoffType(newType: PlayoffType | null): void {
    const currentInfo = this.state.eventInfo;
    if (currentInfo !== null && newType !== null) {
      currentInfo.playoff_type = newType.value;
      currentInfo.playoff_type_string = newType.label;
      this.setState({ eventInfo: currentInfo });
    }
  }

  loadEventInfo(newEventKey: string): void {
    this.setState({ status: "Loading event info..." });
    fetch(`/api/v3/event/${newEventKey}`, {
      credentials: "same-origin",
    })
      .then(ensureRequestSuccess)
      .then((response) => response.json())
      .then(
        (data1: ApiEvent) =>
          // Merge in remap_teams
          fetch(`/_/remap_teams/${newEventKey}`)
            .then(ensureRequestSuccess)
            .then((response) => response.json())
            .then((data2: Record<string, string>) => {
              const data = Object.assign({}, data1);
              data.remap_teams = data2;
              return data;
            })
      )
      .then((data: ApiEvent) => this.setState({ eventInfo: data, status: "" }));
  }

  addWebcast(webcastUrl: string, webcastDate: string): void {
    const currentInfo = this.state.eventInfo;
    if (currentInfo !== null) {
      currentInfo.webcasts.push({
        type: "",
        channel: "",
        url: webcastUrl,
        date: webcastDate ? webcastDate : undefined,
      });
      this.setState({ eventInfo: currentInfo });
    }
  }

  removeWebcast(indexToRemove: number): void {
    const currentInfo = this.state.eventInfo;
    if (currentInfo !== null) {
      currentInfo.webcasts.splice(indexToRemove, 1);
      this.setState({ eventInfo: currentInfo });
    }
  }

  addTeamMap(fromTeamKey: string, toTeamKey: string): void {
    const currentInfo = this.state.eventInfo;
    if (currentInfo !== null) {
      currentInfo.remap_teams[fromTeamKey] = toTeamKey;
      this.setState({ eventInfo: currentInfo });
    }
  }

  removeTeamMap(keyToRemove: string): void {
    const currentInfo = this.state.eventInfo;
    if (currentInfo !== null) {
      delete currentInfo.remap_teams[keyToRemove];
      this.setState({ eventInfo: currentInfo });
    }
  }

  updateEventInfo(): void {
    this.setState({ buttonClass: "btn-warning" });
    this.props.makeTrustedRequest(
      `/api/trusted/v1/event/${this.props.selectedEvent}/info/update`,
      JSON.stringify(this.state.eventInfo),
      () => {
        this.setState({ buttonClass: "btn-success" });
      },
      (error) => alert(`Error: ${error}`)
    );
  }

  render(): React.ReactNode {
    return (
      <div className="tab-pane active col-xs-12" id="info">
        <h3>Event Info</h3>
        {this.state.status && <p>{this.state.status}</p>}
        <div className="row" style={{ marginInline: "0" }}>
          <PlayoffTypeDropdown
            eventInfo={this.state.eventInfo}
            setType={this.setPlayoffType}
          />

          <SyncCodeInput
            eventInfo={this.state.eventInfo}
            setSyncCode={this.onFirstCodeChange}
          />

          <AddRemoveWebcast
            eventInfo={this.state.eventInfo}
            addWebcast={this.addWebcast}
            removeWebcast={this.removeWebcast}
          />

          <AddRemoveTeamMap
            eventInfo={this.state.eventInfo}
            addTeamMap={this.addTeamMap}
            removeTeamMap={this.removeTeamMap}
          />

          <button
            className={`btn ${this.state.buttonClass}`}
            onClick={this.updateEventInfo}
            disabled={this.state.eventInfo === null}
          >
            Publish Changes
          </button>
        </div>
      </div>
    );
  }
}

export default EventInfoTab;
