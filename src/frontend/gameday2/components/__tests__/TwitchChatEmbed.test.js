/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";
import TwitchChatEmbed from "../TwitchChatEmbed";

describe("TwitchChatEmbed", () => {
  it("embeds the channel's chat with the current hostname as parent", () => {
    const { container } = render(
      <TwitchChatEmbed channel="firstinspires" visible />
    );
    const iframe = container.querySelector("iframe");
    expect(iframe.id).toBe("twich-chat-firstinspires");
    expect(iframe.getAttribute("src")).toBe(
      `https://twitch.tv/embed/firstinspires/chat?parent=${document.location.hostname}`
    );
    expect(container.firstChild.style.display).toBe("");
  });

  it("hides the embed when not visible", () => {
    const { container } = render(
      <TwitchChatEmbed channel="firstinspires" visible={false} />
    );
    expect(container.firstChild.style.display).toBe("none");
  });
});
