/* @jest-environment jsdom */

const mockCreateRoot = jest.fn();

jest.mock("react-dom/client", () => ({
  createRoot: (el) => mockCreateRoot(el),
}));
jest.mock("../components/ZebraMotionWorksVisualizer", () => () => null);

describe("zebramotionworks entry point", () => {
  it("renders a visualizer with the parsed data into every container", () => {
    const data = { times: [0, 0.1], alliances: { red: [], blue: [] } };
    document.body.innerHTML = `
      <div class="zebramotionworks-content" data-year="2019"
        data-zebramotionworks='${JSON.stringify(data)}'></div>
      <div class="zebramotionworks-content" data-year="2020"
        data-zebramotionworks="null"></div>`;
    const renders = [];
    mockCreateRoot.mockImplementation((el) => ({
      render: (element) => renders.push({ el, element }),
    }));

    require("../zebramotionworks");

    const els = document.getElementsByClassName("zebramotionworks-content");
    expect(renders.map(({ el }) => el)).toEqual([els[0], els[1]]);
    expect(renders.map(({ element }) => element.props)).toEqual([
      { data, year: 2019 },
      { data: null, year: 2020 },
    ]);
  });
});
