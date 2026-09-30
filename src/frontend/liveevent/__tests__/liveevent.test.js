/* @jest-environment jsdom */

const mockCreateRoot = jest.fn();

jest.mock("react-dom/client", () => ({
  createRoot: (el) => mockCreateRoot(el),
}));
jest.mock("../components/LiveEventPanel", () => () => null);

describe("liveevent entry point", () => {
  it("renders a LiveEventPanel into every liveevent-content element", () => {
    document.body.innerHTML = `
      <div class="liveevent-content" data-eventkey="2024casj"></div>
      <div class="liveevent-content" data-eventkey="2024nyny" data-simple></div>`;
    const renders = [];
    mockCreateRoot.mockImplementation((el) => ({
      render: (element) => renders.push({ el, element }),
    }));

    require("../liveevent");

    const els = document.getElementsByClassName("liveevent-content");
    expect(renders.map(({ el }) => el)).toEqual([els[0], els[1]]);
    expect(renders.map(({ element }) => element.props)).toEqual([
      { eventKey: "2024casj", simple: false },
      { eventKey: "2024nyny", simple: true },
    ]);
  });
});
