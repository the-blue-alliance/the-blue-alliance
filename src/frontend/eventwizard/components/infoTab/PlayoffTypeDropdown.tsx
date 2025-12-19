import React from "react";
import AsyncSelect from "react-select/async";
import { ApiEvent } from "../../constants/ApiEvent";

interface PlayoffType {
  label: string;
  value: number;
}

interface PlayoffTypeDropdownProps {
  eventInfo: ApiEvent | null;
  setType: (option: PlayoffType | null) => void;
}

const PlayoffTypeDropdown: React.FC<PlayoffTypeDropdownProps> = ({
  eventInfo,
  setType,
}) => {
  const loadPlayoffTypes = async (): Promise<PlayoffType[]> => {
    const response = await fetch("/_/playoff_types", {
      credentials: "same-origin",
    });
    return response.json();
  };

  return (
    <div className="form-group row">
      <label htmlFor="selectType" className="col-sm-2 control-label">
        Playoff Type
      </label>
      <div className="col-sm-10">
        <AsyncSelect<PlayoffType>
          name="selectType"
          placeholder="Choose playoff type..."
          // @ts-ignore - react-select v2 loadingPlaceholder prop
          loadingPlaceholder="Loading playoff types..."
          controlShouldRenderValue={true}
          isClearable={false}
          isSearchable={false}
          value={
            eventInfo
              ? {
                  label: eventInfo.playoff_type_string || '',
                  value: eventInfo.playoff_type || 0,
                }
              : null
          }
          loadOptions={loadPlayoffTypes}
          onChange={setType}
          isDisabled={eventInfo === null}
          defaultOptions
        />
      </div>
    </div>
  );
};

export default PlayoffTypeDropdown;
