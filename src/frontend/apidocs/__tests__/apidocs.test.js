/* @jest-environment jsdom */

import React from "react";
import { render } from "@testing-library/react";

const mockSwaggerUi = jest.fn();
jest.mock("swagger-ui", () => (options) => mockSwaggerUi(options));

// Testing Library's render also calls createRoot, so pass through to the
// real implementation unless a test swaps in a stub.
const mockCreateRoot = jest.fn();
jest.mock("react-dom/client", () => {
  const actual = jest.requireActual("react-dom/client");
  return {
    ...actual,
    createRoot: (el, options) =>
      mockCreateRoot.getMockImplementation()
        ? mockCreateRoot(el)
        : actual.createRoot(el, options),
  };
});
jest.mock("../apidocs.less", () => ({}), { virtual: true });

describe("ApiDocsFrame", () => {
  const ApiDocsFrame = require("../ApiDocsFrame").default;

  beforeEach(() => mockSwaggerUi.mockClear());

  it("mounts Swagger UI into its container with the given spec URL", () => {
    const { container } = render(<ApiDocsFrame url="/swagger/api_v3.json" />);

    expect(container.querySelector("#swaggerContainer")).not.toBeNull();
    expect(mockSwaggerUi).toHaveBeenCalledWith({
      dom_id: "#swaggerContainer",
      url: "/swagger/api_v3.json",
    });
  });

  it("defaults to the production APIv3 spec", () => {
    expect(ApiDocsFrame.defaultProps.url).toBe(
      "https://www.thebluealliance.com/swagger/api_v3.json"
    );
  });
});

describe("apidocs entry point", () => {
  it("renders the frame into #content with the URL from #swagger_url", () => {
    document.body.innerHTML = `
      <div id="swagger_url">/swagger/api_trusted_v1.json</div>
      <div id="content"></div>`;
    const renders = [];
    mockCreateRoot.mockImplementation((el) => ({
      render: (element) => renders.push({ el, element }),
    }));

    jest.isolateModules(() => {
      require("../apidocs");
    });

    expect(renders).toHaveLength(1);
    expect(renders[0].el).toBe(document.getElementById("content"));
    expect(renders[0].element.props.url).toBe("/swagger/api_trusted_v1.json");
  });
});
