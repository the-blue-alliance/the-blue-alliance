import type { MetaFunction } from "@remix-run/node";

export const meta: MetaFunction = () => {
  return [
    { title: "New Remix App" },
    { name: "description", content: "Welcome to Remix!" },
  ];
};

export default function Index() {
  return (
    <div className="font-sans p-4">
      <h1 className="text-3xl">The Blue Alliance</h1>
      <p>
        The Blue Alliance is the best way to scout, watch, and relive the{" "}
        <i>FIRST</i> Robotics Competition.
      </p>
    </div>
  );
}
