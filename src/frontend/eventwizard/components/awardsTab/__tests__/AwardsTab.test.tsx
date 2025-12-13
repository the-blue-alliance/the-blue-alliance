/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import AwardsTab from "../AwardsTab";

describe("AwardsTab", () => {
  beforeEach(() => {
    // default fetch mock; tests will override as needed
    global.fetch = jest.fn() as jest.Mock;
    window.alert = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
    delete (global as any).fetch;
    delete (window as any).alert;
  });

  test("fetchAwards loads awards and enables Save Edits", async () => {
    const makeTrustedRequest = jest.fn();

    const rawAwards = [
      {
        award_type: 2,
        name: "Excellence Award",
        recipient_list: [{ team_key: "frc254", awardee: "Alice" }],
      },
    ];

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(rawAwards),
    });

    render(
      <AwardsTab
        selectedEvent={"2020test"}
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    const fetchButton = screen.getByText(/Fetch Awards/i);
    expect(fetchButton).toBeEnabled();

    fireEvent.click(fetchButton);

    // Wait for table row to appear with award name
    await waitFor(() =>
      expect(screen.getByText(/Excellence Award/i)).toBeInTheDocument()
    );

    // Save Edits should now be enabled (awardsFetched true)
    const saveButton = screen.getByRole("button", { name: /Save Edits/i });
    expect(saveButton).toBeEnabled();
  });

  test("addAward appends new award and shows team key conversion", async () => {
    const makeTrustedRequest = jest.fn();

    // Ensure fetch invoked by component (to set awardsFetched) returns empty
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });

    render(
      <AwardsTab
        selectedEvent={"2020test"}
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    // Fill inputs
    const typeInput = screen.getByPlaceholderText("3");
    const nameInput = screen.getByPlaceholderText(
      "Woodie Flowers Finalist Award"
    );
    const teamInput = screen.getByPlaceholderText("604");
    const awardeeInput = screen.getByPlaceholderText("Helen Arrington");

    fireEvent.change(typeInput, { target: { value: "3" } });
    fireEvent.change(nameInput, { target: { value: "Woodie Flowers" } });
    fireEvent.change(teamInput, { target: { value: "604" } });
    fireEvent.change(awardeeInput, { target: { value: "Bob" } });

    const addButton = screen.getByRole("button", { name: /Add Award/i });
    fireEvent.click(addButton);

    // New row should appear
    await waitFor(() =>
      expect(screen.getByText(/Woodie Flowers/i)).toBeInTheDocument()
    );
    expect(screen.getByText(/frc604/i)).toBeInTheDocument();
    expect(screen.getByText(/Bob/i)).toBeInTheDocument();
  });

  test("toggleDeletion marks and unmarks a row", async () => {
    const makeTrustedRequest = jest.fn();

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });

    render(
      <AwardsTab
        selectedEvent={"2020test"}
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    // Add two awards
    const nameInput = screen.getByPlaceholderText(
      "Woodie Flowers Finalist Award"
    );
    const teamInput = screen.getByPlaceholderText("604");
    const awardeeInput = screen.getByPlaceholderText("Helen Arrington");
    const addButton = screen.getByRole("button", { name: /Add Award/i });

    fireEvent.change(nameInput, { target: { value: "Award One" } });
    fireEvent.change(teamInput, { target: { value: "111" } });
    fireEvent.change(awardeeInput, { target: { value: "Alice" } });
    fireEvent.click(addButton);

    fireEvent.change(nameInput, { target: { value: "Award Two" } });
    fireEvent.change(teamInput, { target: { value: "222" } });
    fireEvent.change(awardeeInput, { target: { value: "Bob" } });
    fireEvent.click(addButton);

    // Find the row for 'Award One'
    const row = await screen.findByText("Award One");
    const tr = row.closest("tr")!;
    const { getByText: getByTextWithin } = within(tr);
    const keepButton = getByTextWithin(/Keep/i);
    expect(keepButton).toBeInTheDocument();

    // Toggle deletion
    fireEvent.click(keepButton);
    expect(getByTextWithin(/Will be deleted/i)).toBeInTheDocument();
    expect(getByTextWithin(/Will be deleted/i).className).toContain(
      "btn-danger"
    );

    // Toggle back
    fireEvent.click(getByTextWithin(/Will be deleted/i));
    expect(getByTextWithin(/Keep/i)).toBeInTheDocument();
  });

  test("saveEdits calls makeTrustedRequest excluding deleted awards", async () => {
    const makeTrustedRequest = jest.fn(() => Promise.resolve({} as Response));

    // start with no awards fetched
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });

    render(
      <AwardsTab
        selectedEvent={"2020test"}
        makeTrustedRequest={makeTrustedRequest}
      />
    );

    // Add two awards

    // Ensure awardsFetched true by clicking Fetch Awards (no-op)
    const fetchButton = screen.getByText(/Fetch Awards/i);
    fireEvent.click(fetchButton);
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());

    // Add two awards
    const nameInput = screen.getByPlaceholderText(
      "Woodie Flowers Finalist Award"
    );
    const teamInput = screen.getByPlaceholderText("604");
    const awardeeInput = screen.getByPlaceholderText("Helen Arrington");
    const addButton = screen.getByRole("button", { name: /Add Award/i });

    fireEvent.change(nameInput, { target: { value: "Keep Me" } });
    fireEvent.change(teamInput, { target: { value: "10" } });
    fireEvent.change(awardeeInput, { target: { value: "Alice" } });
    fireEvent.click(addButton);

    fireEvent.change(nameInput, { target: { value: "Delete Me" } });
    fireEvent.change(teamInput, { target: { value: "20" } });
    fireEvent.change(awardeeInput, { target: { value: "Bob" } });
    fireEvent.click(addButton);

    // Mark second row for deletion
    const deleteRow = await screen.findByText("Delete Me");
    const tr = deleteRow.closest("tr")!;
    const { getByText: getByTextWithin } = within(tr);
    fireEvent.click(getByTextWithin(/Keep/i));

    const saveButton = screen.getByRole("button", { name: /Save Edits/i });
    await waitFor(() => expect(saveButton).toBeEnabled());

    fireEvent.click(saveButton);

    await waitFor(() => expect(makeTrustedRequest).toHaveBeenCalledTimes(1));
    const [path, body] = makeTrustedRequest.mock.calls[0];
    expect(path).toContain("/api/trusted/v1/event/2020test/awards/update");
    const parsed = JSON.parse(body);
    // Only one award should remain (Keep Me)
    expect(parsed.length).toBe(1);
    expect(parsed[0].name_str).toBe("Keep Me");
  });
});
