import React, { useState, useEffect, useRef, ChangeEvent } from "react";
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

let eventsCache: EventOption[] | null = null;

const EventSelector: React.FC<EventSelectorProps> = ({
  manualEvent,
  selectedEvent,
  setEvent,
  setManualEvent,
  clearAuth,
}) => {
  const [eventSelectLabel, setEventSelectLabel] = useState("");
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      // Clean up timer on unmount
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  const loadEvents = async (search: string): Promise<EventOption[]> => {
    if (!eventsCache) {
      const response = await fetch("/_/account/apiwrite_events", {
        credentials: "same-origin",
      });

      let events: EventOption[];
      if (response.status === 401) {
        // If we're not logged in, return no events
        events = [];
      } else {
        events = await response.json();
      }
      events.push({ value: "_other", label: "Other" });
      eventsCache = events;
    }

    return (eventsCache || []).filter((e) =>
      e.label.toLowerCase().includes(search.toLowerCase())
    );
  };

  const handleEventSelected = (newEvent: EventOption | null): void => {
    if (!newEvent) return;

    clearAuth();
    setEventSelectLabel(newEvent.label);

    if (newEvent.value === "_other") {
      setManualEvent(true);
      setEvent("");
    } else {
      setManualEvent(false);
      setEvent(newEvent.value);
    }
  };

  const handleManualEventChange = (event: ChangeEvent<HTMLInputElement>): void => {
    const value = event.target.value;

    // Clear existing timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Set new timer to update after 500ms of no typing
    debounceTimer.current = setTimeout(() => {
      setEvent(value);
    }, 500);
  };

  let eventKeyBox: React.ReactNode;
  if (manualEvent) {
    eventKeyBox = (
      <input
        type="text"
        className="form-control"
        id="event_key"
        placeholder="Event Key"
        onChange={handleManualEventChange}
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
            eventSelectLabel
              ? {
                  label: eventSelectLabel,
                  value: selectedEvent || "",
                }
              : null
          }
          loadOptions={loadEvents}
          onChange={handleEventSelected}
          defaultOptions
        />
        {eventKeyBox}
      </div>
    </div>
  );
};

export default EventSelector;
