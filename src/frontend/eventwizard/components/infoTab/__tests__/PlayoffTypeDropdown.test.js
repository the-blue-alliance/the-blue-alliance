import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import PlayoffTypeDropdown from "../PlayoffTypeDropdown";

// Mock react-select/async
jest.mock("react-select/async", () => (props) => (
  <div
    data-testid="async-select"
    data-name={props.name}
    data-placeholder={props.placeholder}
    data-disabled={props.isDisabled ? "true" : "false"}
    onClick={() =>
      props.onChange &&
      props.onChange({ value: 1, label: "Double Elimination" })
    }
  >
    {props.value && props.value.label}
  </div>
));

describe("PlayoffTypeDropdown", () => {
  const mockSetType = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders the form group with label", () => {
    const html = renderToStaticMarkup(
      <PlayoffTypeDropdown eventInfo={null} setType={mockSetType} />
    );
    expect(html).toContain("form-group row");
    expect(html).toContain("Playoff Type");
  });

  it("renders AsyncSelect component", () => {
    const html = renderToStaticMarkup(
      <PlayoffTypeDropdown eventInfo={null} setType={mockSetType} />
    );
    expect(html).toContain('data-testid="async-select"');
    expect(html).toContain('data-name="selectType"');
  });

  it("shows correct placeholder", () => {
    const html = renderToStaticMarkup(
      <PlayoffTypeDropdown eventInfo={null} setType={mockSetType} />
    );
    expect(html).toContain("Choose playoff type...");
  });

  it("disables select when eventInfo is null", () => {
    const html = renderToStaticMarkup(
      <PlayoffTypeDropdown eventInfo={null} setType={mockSetType} />
    );
    expect(html).toContain('data-disabled="true"');
  });

  it("enables select when eventInfo is provided", () => {
    const eventInfo = {
      playoff_type: 0,
      playoff_type_string: "Standard Bracket",
    };
    const html = renderToStaticMarkup(
      <PlayoffTypeDropdown eventInfo={eventInfo} setType={mockSetType} />
    );
    expect(html).toContain('data-disabled="false"');
  });

  it("displays current playoff type when eventInfo exists", () => {
    const eventInfo = {
      playoff_type: 0,
      playoff_type_string: "Standard Bracket",
    };
    const html = renderToStaticMarkup(
      <PlayoffTypeDropdown eventInfo={eventInfo} setType={mockSetType} />
    );
    expect(html).toContain("Standard Bracket");
  });

  it("uses proper Bootstrap classes", () => {
    const html = renderToStaticMarkup(
      <PlayoffTypeDropdown eventInfo={null} setType={mockSetType} />
    );
    expect(html).toContain("col-sm-2");
    expect(html).toContain("col-sm-10");
    expect(html).toContain("control-label");
  });
});
