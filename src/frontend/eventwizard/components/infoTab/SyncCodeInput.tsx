import React, { ChangeEvent } from "react";
import { ApiEvent } from "../../constants/ApiEvent";

interface SyncCodeInputProps {
  eventInfo: ApiEvent | null;
  setSyncCode: (e: ChangeEvent<HTMLInputElement>) => void;
}

const SyncCodeInput: React.FC<SyncCodeInputProps> = ({
  eventInfo,
  setSyncCode,
}) => (
  <div className="form-group row">
    <label htmlFor="first_code" className="col-sm-2 control-label">
      FIRST Sync Code
    </label>
    <div className="col-sm-10">
      <input
        type="text"
        className="form-control"
        id="first_code"
        placeholder="IRI"
        value={
          eventInfo && eventInfo.first_event_code
            ? eventInfo.first_event_code
            : ""
        }
        disabled={eventInfo === null}
        onChange={setSyncCode}
      />
    </div>
  </div>
);

export default SyncCodeInput;
