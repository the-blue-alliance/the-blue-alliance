import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import SetupFrame from "../SetupFrame";

// Mock container components
jest.mock("../../containers/EventSelectorContainer", () => () => (
  <div data-testid="event-selector-container" />
));
jest.mock("../../containers/AuthToolsContainer", () => () => (
  <div data-testid="auth-tools-container" />
));
jest.mock("../../containers/AuthInputContainer", () => () => (
  <div data-testid="auth-input-container" />
));

describe("SetupFrame", () => {
  it("renders the setup section", () => {
    const html = renderToStaticMarkup(<SetupFrame />);
    expect(html).toContain('id="setup"');
    expect(html).toContain("Setup");
  });

  it("renders a form with horizontal layout", () => {
    const html = renderToStaticMarkup(<SetupFrame />);
    expect(html).toContain("form-horizontal");
    expect(html).toContain('role="form"');
  });

  it("renders EventSelectorContainer", () => {
    const html = renderToStaticMarkup(<SetupFrame />);
    expect(html).toContain('data-testid="event-selector-container"');
  });

  it("renders AuthToolsContainer", () => {
    const html = renderToStaticMarkup(<SetupFrame />);
    expect(html).toContain('data-testid="auth-tools-container"');
  });

  it("renders AuthInputContainer", () => {
    const html = renderToStaticMarkup(<SetupFrame />);
    expect(html).toContain('data-testid="auth-input-container"');
  });
});
