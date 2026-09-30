/* @jest-environment jsdom */

import React from "react";
import { render, screen } from "@testing-library/react";
import LastMatchesTable from "../LastMatchesTable";

describe("LastMatchesTable", () => {
  it("shows a spinner while loading", () => {
    const { container } = render(
      <LastMatchesTable year={2018} matches={null} />
    );
    expect(container.querySelector(".glyphicon-refresh")).not.toBeNull();
  });

  it("shows a message when no matches have been played", () => {
    render(<LastMatchesTable year={2018} matches={[]} />);
    expect(screen.getByText("No matches have been played")).toBeTruthy();
  });

  it("renders played matches and highlights the winner", () => {
    const matches = [
      {
        key: "2018casj_qm1",
        c: "qm",
        s: 1,
        m: 1,
        rt: ["frc254", "frc604", "frc1678"],
        bt: ["frc971", "frc973", "frc1323"],
        r: 300,
        b: 200,
        w: "red",
      },
      {
        key: "2018casj_sf1m1",
        c: "sf",
        s: 1,
        m: 1,
        rt: ["frc1", "frc2", "frc3"],
        bt: ["frc4", "frc5", "frc6"],
        r: 100,
        b: 150,
        w: "blue",
      },
    ];
    const { container } = render(
      <LastMatchesTable year={2018} matches={matches} />
    );
    expect(container.querySelectorAll("tbody tr")).toHaveLength(4);
    expect(
      container.querySelector('a[href="/match/2018casj_sf1m1"]').textContent
    ).toBe("Semis1 - 1");
    expect(
      container.querySelector('a[href="/team/254/2018"]').parentElement
        .className
    ).toBe("red winner");
    expect(
      container.querySelector('a[href="/team/971/2018"]').parentElement
        .className
    ).toBe("blue ");
    expect(
      container.querySelector('a[href="/team/4/2018"]').parentElement.className
    ).toBe("blue winner");
    expect(
      Array.from(
        container.querySelectorAll(".redScore.winner, .blueScore.winner")
      ).map((el) => el.textContent)
    ).toEqual(["300", "150"]);
  });
});
