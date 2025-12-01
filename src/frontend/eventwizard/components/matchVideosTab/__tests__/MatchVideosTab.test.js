/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import MatchVideosTab from "../MatchVideosTab";

describe("MatchVideosTab", () => {
  test("Add Videos button is disabled when no selectedEvent", () => {
    const makeTrustedRequest = jest.fn();
    render(
      <MatchVideosTab
        selectedEvent={""}
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    const btn = screen.getByRole("button", { name: /Add Videos/i });
    expect(btn).toBeDisabled();
  });

  test("parses textarea lines and renders parsed videos with iframe src", () => {
    const makeTrustedRequest = jest.fn();
    const { container } = render(
      <MatchVideosTab
        selectedEvent={"evt1"}
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, {
      target: { value: "match1, abc\nmatch2, def?t=20" },
    });

    // Parsed match keys are displayed
    expect(screen.getByText("match1")).toBeInTheDocument();
    expect(screen.getByText("match2")).toBeInTheDocument();

    const iframes = container.querySelectorAll("iframe");
    expect(iframes.length).toBe(2);
    expect(iframes[0].src).toContain("https://www.youtube.com/embed/abc");
    // Ensure t= was replaced with start=
    expect(iframes[1].src).toContain(
      "https://www.youtube.com/embed/def?start=20"
    );
  });

  test("clicking Add Videos calls makeTrustedRequest with expected payload", () => {
    const makeTrustedRequest = jest.fn();
    render(
      <MatchVideosTab
        selectedEvent={"evX"}
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "m1,vid1\nm2,vid2" } });

    const btn = screen.getByRole("button", { name: /Add Videos/i });
    expect(btn).toBeEnabled();
    fireEvent.click(btn);

    expect(makeTrustedRequest).toHaveBeenCalledTimes(1);
    const [url, body, onSuccess, onError] = makeTrustedRequest.mock.calls[0];
    expect(url).toBe("/api/trusted/v1/event/evX/match_videos/add");
    expect(body).toBe(JSON.stringify({ m1: "vid1", m2: "vid2" }));
    expect(typeof onSuccess).toBe("function");
    expect(typeof onError).toBe("function");
  });
});
