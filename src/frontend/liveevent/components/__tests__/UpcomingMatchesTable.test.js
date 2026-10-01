/* @jest-environment jsdom */

import React from "react";
import { act, render, screen } from "@testing-library/react";
import UpcomingMatchesTable from "../UpcomingMatchesTable";

const NOW = 1700000000; // seconds

const makeMatch = (shortKey, extra) =>
  Object.assign(
    {
      key: `2018casj_${shortKey}`,
      c: "qm",
      s: 1,
      m: parseInt(shortKey.replace("qm", ""), 10),
      rt: ["frc254", "frc604", "frc1678"],
      bt: ["frc971", "frc973", "frc1323"],
      r: -1,
      b: -1,
    },
    extra
  );

describe("UpcomingMatchesTable", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(NOW * 1000);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("shows a spinner while loading", () => {
    const { container } = render(
      <UpcomingMatchesTable year={2018} matches={null} />
    );
    expect(container.querySelector(".glyphicon-refresh")).not.toBeNull();
  });

  it("shows a message when there are no more matches", () => {
    render(<UpcomingMatchesTable year={2018} matches={[]} />);
    expect(
      screen.getByText("There are no more scheduled matches")
    ).toBeTruthy();
  });

  it("shows ETAs for upcoming matches", () => {
    const matches = [
      makeMatch("qm1", { pt: NOW + 60, q: "Now queuing" }),
      makeMatch("qm2", { pt: NOW + 60 }),
      makeMatch("qm3", { pt: NOW + 30 * 60 }),
      makeMatch("qm4", { pt: NOW + 3 * 60 * 60 }),
      makeMatch("qm5"),
    ];
    const { container } = render(
      <UpcomingMatchesTable year={2018} matches={matches} />
    );
    const etas = Array.from(
      container.querySelectorAll('tbody td[rowspan="2"]:last-child')
    ).map((td) => td.textContent);
    expect(etas).toEqual(["Now queuing", "<2 min", "~30 min", "~3 h", "?"]);
    expect(container.querySelectorAll('a[href="/team/254/2018"]')).toHaveLength(
      5
    );
    expect(container.querySelectorAll("td.blue")).toHaveLength(15);

    // The ETA refreshes every 10 seconds
    act(() => {
      jest.setSystemTime((NOW + 30 * 60 - 60) * 1000);
      jest.advanceTimersByTime(10000);
    });
    expect(screen.getAllByText("<2 min")).toHaveLength(2);
  });

  it("clears its refresh interval on unmount", () => {
    // componentDidMount starts a 10s refresh interval.
    const { unmount } = render(
      <UpcomingMatchesTable year={2018} matches={[]} />
    );
    expect(jest.getTimerCount()).toBe(1);
    unmount();
    expect(jest.getTimerCount()).toBe(0);
  });
});
