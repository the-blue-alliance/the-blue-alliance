/* @jest-environment jsdom */
import { compose } from "redux";

jest.mock("../eventwizard.less", () => ({}));
jest.mock("../components/EventWizardFrame", () => () => null);

const mockRender = jest.fn();
const mockCreateRoot = jest.fn(() => ({ render: mockRender }));
jest.mock("react-dom/client", () => ({
  createRoot: (container: Element) => mockCreateRoot(container),
}));

describe("eventwizard entry point", () => {
  beforeEach(() => {
    mockRender.mockClear();
    mockCreateRoot.mockClear();
    document.body.innerHTML = "";
    delete window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__;
  });

  const loadEntryPoint = (): void => {
    jest.isolateModules(() => {
      require("../eventwizard");
    });
  };

  it("mounts the app into #content with a store backed by the eventwizard reducer", () => {
    document.body.innerHTML = '<div id="content"></div>';

    loadEntryPoint();

    expect(mockCreateRoot).toHaveBeenCalledWith(
      document.getElementById("content")
    );
    expect(mockRender).toHaveBeenCalledTimes(1);
    const tree = mockRender.mock.calls[0][0];
    expect(tree.props.store.getState()).toEqual({
      auth: { selectedEvent: "", manualEvent: false },
    });
  });

  it("uses the Redux DevTools compose enhancer when the extension is installed", () => {
    document.body.innerHTML = '<div id="content"></div>';
    const devtoolsCompose = jest.fn(compose);
    window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ = devtoolsCompose;

    loadEntryPoint();

    expect(devtoolsCompose).toHaveBeenCalledTimes(1);
    expect(mockRender).toHaveBeenCalledTimes(1);
  });

  it("throws when the #content mount point is missing", () => {
    expect(loadEntryPoint).toThrow(
      "Could not find content element to mount React app"
    );
    expect(mockCreateRoot).not.toHaveBeenCalled();
  });
});
