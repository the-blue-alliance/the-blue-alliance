import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import EventWizardFrame from "../EventWizardFrame";

// Mock child components
jest.mock("../EventWizardTabFrame", () => () => (
  <div data-testid="event-wizard-tab-frame" />
));
jest.mock("../SetupFrame", () => () => <div data-testid="setup-frame" />);

describe("EventWizardFrame", () => {
  it("renders the main container", () => {
    const html = renderToStaticMarkup(<EventWizardFrame />);
    expect(html).toContain('id="eventwizard"');
    expect(html).toContain("container");
  });

  it("renders the header", () => {
    const html = renderToStaticMarkup(<EventWizardFrame />);
    expect(html).toContain("TBA Event Wizard");
    expect(html).toContain("endheader");
  });

  it("renders description with links", () => {
    const html = renderToStaticMarkup(<EventWizardFrame />);
    expect(html).toContain("A tool to input FRC event data");
    expect(html).toContain("/add-data");
    expect(html).toContain("/contact");
  });

  it("renders link to user guide", () => {
    const html = renderToStaticMarkup(<EventWizardFrame />);
    expect(html).toContain("User Guide");
    expect(html).toContain(
      "https://docs.google.com/document/d/1RWcsehMDXzlAyv4p5srwofknYvdNt6noejpMSYZMmeA/pub"
    );
  });

  it("renders SetupFrame component", () => {
    const html = renderToStaticMarkup(<EventWizardFrame />);
    expect(html).toContain('data-testid="setup-frame"');
  });

  it("renders EventWizardTabFrame component", () => {
    const html = renderToStaticMarkup(<EventWizardFrame />);
    expect(html).toContain('data-testid="event-wizard-tab-frame"');
  });
});
