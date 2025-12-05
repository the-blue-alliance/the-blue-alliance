import React, { Component, ChangeEvent } from "react";
import AsyncSelect from "react-select/async";

interface EventOption {
  value: string;
  label: string;
}

interface EventSelectorProps {
  manualEvent: boolean;
  selectedEvent?: string;
  setEvent: (eventKey: string) => void;
  setManualEvent: (manualEvent: boolean) => void;
  clearAuth: () => void;
}

interface EventSelectorState {
  eventSelectLabel: string;
}

class EventSelector extends Component<EventSelectorProps, EventSelectorState> {
  static eventsCache: EventOption[] | null;
  debounceTimer: NodeJS.Timeout | null = null;

  static async loadEvents(search: string): Promise<EventOption[]> {
    if (!EventSelector.eventsCache) {
      EventSelector.eventsCache = await fetch("/_/account/apiwrite_events", {
        credentials: "same-origin",
      })
        .then((response) => {
          if (response.status === 401) {
            // If we're not logged in, return no events
            return [];
          }
          return response.json();
        })
        .then((events: EventOption[]) => {
          events.push({ value: "_other", label: "Other" });
          return events;
        });
    }

    return (EventSelector.eventsCache || []).filter((e) =>
      e.label.toLowerCase().includes(search.toLowerCase())
    );
  }

  constructor(props: EventSelectorProps) {
    super(props);
    this.state = {
      eventSelectLabel: "",
    };
    this.onEventSelected = this.onEventSelected.bind(this);
    this.onManualEventChange = this.onManualEventChange.bind(this);
  }

  componentWillUnmount(): void {
    // Clean up timer on unmount
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
  }

  onEventSelected(newEvent: EventOption | null): void {
    if (!newEvent) return;

    this.props.clearAuth();
    this.setState({ eventSelectLabel: newEvent.label });

    if (newEvent.value === "_other") {
      this.props.setManualEvent(true);
      this.props.setEvent("");
    } else {
      this.props.setManualEvent(false);
      this.props.setEvent(newEvent.value);
    }
  }

  onManualEventChange(event: ChangeEvent<HTMLInputElement>): void {
    const value = event.target.value;

    // Clear existing timer
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }

    // Set new timer to update after 500ms of no typing
    this.debounceTimer = setTimeout(() => {
      this.props.setEvent(value);
    }, 500);
  }

  render(): React.ReactNode {
    let eventKeyBox: React.ReactNode;
    if (this.props.manualEvent) {
      eventKeyBox = (
        <input
          type="text"
          className="form-control"
          id="event_key"
          placeholder="Event Key"
          onChange={this.onManualEventChange}
        />
      );
    }

    return (
      <div className="form-group">
        <label htmlFor="event_key_select" className="col-sm-2 control-label">
          Select Event
        </label>
        <div className="col-sm-10">
          <AsyncSelect<EventOption>
            name="selectEvent"
            placeholder="Select an Event..."
            value={
              this.state.eventSelectLabel
                ? {
                    label: this.state.eventSelectLabel,
                    value: this.props.selectedEvent || "",
                  }
                : null
            }
            loadOptions={EventSelector.loadEvents}
            onChange={this.onEventSelected}
            defaultOptions
          />
          {eventKeyBox}
        </div>
      </div>
    );
  }
}

export default EventSelector;
