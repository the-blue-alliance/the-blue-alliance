import type { MetaFunction } from '@remix-run/node';

export const meta: MetaFunction = () => {
  return [
    { title: 'The Blue Alliance' },
    {
      name: 'description',
      content:
        'Team information and match videos and results from the FIRST Robotics Competition',
    },
  ];
};

export default function Index() {
  return (
    <div className="p-4 font-sans">
      <h1 className="text-3xl">The Blue Alliance</h1>
      <p>
        The Blue Alliance is the best way to scout, watch, and relive the{' '}
        <i>FIRST</i> Robotics Competition.
      </p>
    </div>
  );
}
