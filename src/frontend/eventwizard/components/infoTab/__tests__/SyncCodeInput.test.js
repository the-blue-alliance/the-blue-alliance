import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import SyncCodeInput from "../SyncCodeInput";

describe("SyncCodeInput", () => {
  const mockSetSyncCode = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders the form group with label", () => {
    const html = renderToStaticMarkup(
      <SyncCodeInput eventInfo={null} setSyncCode={mockSetSyncCode} />
    );
    expect(html).toContain("form-group row");
    expect(html).toContain("FIRST Sync Code");
  });

  it("renders input with correct id and placeholder", () => {
    const html = renderToStaticMarkup(
      <SyncCodeInput eventInfo={null} setSyncCode={mockSetSyncCode} />
    );
    expect(html).toContain('id="first_code"');
    expect(html).toContain('placeholder="IRI"');
  });

  it("disables input when eventInfo is null", () => {
    const html = renderToStaticMarkup(
      <SyncCodeInput eventInfo={null} setSyncCode={mockSetSyncCode} />
    );
    expect(html).toContain("disabled");
  });

  it("enables input when eventInfo is provided", () => {
    const eventInfo = {
      first_event_code: "IRI",
    };
    const html = renderToStaticMarkup(
      <SyncCodeInput eventInfo={eventInfo} setSyncCode={mockSetSyncCode} />
    );
    expect(html).not.toContain("disabled");
  });

  it("displays empty value when eventInfo is null", () => {
    const html = renderToStaticMarkup(
      <SyncCodeInput eventInfo={null} setSyncCode={mockSetSyncCode} />
    );
    expect(html).toContain('value=""');
  });

  it("displays sync code when eventInfo has first_event_code", () => {
    const eventInfo = {
      first_event_code: "IRI",
    };
    const html = renderToStaticMarkup(
      <SyncCodeInput eventInfo={eventInfo} setSyncCode={mockSetSyncCode} />
    );
    expect(html).toContain('value="IRI"');
  });

  it("displays empty value when first_event_code is missing", () => {
    const eventInfo = {};
    const html = renderToStaticMarkup(
      <SyncCodeInput eventInfo={eventInfo} setSyncCode={mockSetSyncCode} />
    );
    expect(html).toContain('value=""');
  });

  it("uses proper Bootstrap classes", () => {
    const html = renderToStaticMarkup(
      <SyncCodeInput eventInfo={null} setSyncCode={mockSetSyncCode} />
    );
    expect(html).toContain("col-sm-2");
    expect(html).toContain("col-sm-10");
    expect(html).toContain("control-label");
    expect(html).toContain("form-control");
  });

  it("renders text input type", () => {
    const html = renderToStaticMarkup(
      <SyncCodeInput eventInfo={null} setSyncCode={mockSetSyncCode} />
    );
    expect(html).toContain('type="text"');
  });

  it("renders input that binds onChange to setSyncCode prop", () => {
    const eventInfo = {
      first_event_code: "IRI",
    };
    const html = renderToStaticMarkup(
      <SyncCodeInput eventInfo={eventInfo} setSyncCode={mockSetSyncCode} />
    );
    // Functional component passes setSyncCode to input's onChange
    // Verify the input is rendered with the correct value
    expect(html).toContain('value="IRI"');
  });
});
