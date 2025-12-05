import React, { Component, ChangeEvent } from "react";
import WebcastList from "./WebcastList";
import { ApiEvent } from "../../constants/ApiEvent";

interface AddRemoveWebcastProps {
  eventInfo: ApiEvent | null;
  addWebcast: (url: string, date: string) => void;
  removeWebcast: (index: number) => void;
}

interface AddRemoveWebcastState {
  newWebcastUrl: string;
  newWebcastDate: string;
}

class AddRemoveWebcast extends Component<
  AddRemoveWebcastProps,
  AddRemoveWebcastState
> {
  constructor(props: AddRemoveWebcastProps) {
    super(props);
    this.state = {
      newWebcastUrl: "",
      newWebcastDate: "",
    };

    this.onNewWebcastUrlChange = this.onNewWebcastUrlChange.bind(this);
    this.onNewWebcastDateChange = this.onNewWebcastDateChange.bind(this);
    this.onAddWebcastClick = this.onAddWebcastClick.bind(this);
  }

  onNewWebcastUrlChange(event: ChangeEvent<HTMLInputElement>): void {
    this.setState({ newWebcastUrl: event.target.value });
  }

  onNewWebcastDateChange(event: ChangeEvent<HTMLInputElement>): void {
    this.setState({ newWebcastDate: event.target.value });
  }

  onAddWebcastClick(): void {
    this.props.addWebcast(this.state.newWebcastUrl, this.state.newWebcastDate);
    this.setState({
      newWebcastUrl: "",
      newWebcastDate: "",
    });
  }

  render(): React.ReactNode {
    let webcastList: React.ReactNode = null;
    if (this.props.eventInfo && this.props.eventInfo.webcasts.length > 0) {
      webcastList = (
        <WebcastList
          webcasts={this.props.eventInfo.webcasts}
          removeWebcast={this.props.removeWebcast}
        />
      );
    } else {
      webcastList = <p>No webcasts found</p>;
    }

    return (
      <div className="form-group row">
        <label htmlFor="webcast_list" className="col-sm-2 control-label">
          Webcasts
        </label>
        <div className="col-sm-10" id="webcast_list">
          {webcastList}

          <div style={{ display: "flex", gap: "0.5em" }}>
            <input
              type="text"
              className="form-control"
              id="webcast_url"
              placeholder="https://youtu.be/abc123"
              disabled={this.props.eventInfo === null}
              onChange={this.onNewWebcastUrlChange}
              value={this.state.newWebcastUrl}
            />
            <input
              type="text"
              className="form-control"
              id="webcast_date"
              placeholder="2025-03-02 (optional)"
              disabled={this.props.eventInfo === null}
              onChange={this.onNewWebcastDateChange}
              value={this.state.newWebcastDate}
            />
            <button
              className="btn btn-info"
              onClick={this.onAddWebcastClick}
              disabled={this.props.eventInfo === null}
            >
              Add Webcast
            </button>
          </div>
        </div>
      </div>
    );
  }
}

export default AddRemoveWebcast;
