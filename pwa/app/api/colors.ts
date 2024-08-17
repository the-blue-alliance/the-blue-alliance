export interface EventColors {
  teams: Record<string, TeamWithColor>;
}

export interface TeamWithColor {
  colors: TeamColors | null;
  teamNumber: number;
}

export interface TeamColors {
  primaryHex: string;
  secondaryHex: string;
  verified: boolean;
}

type Response<T> = { status: number; data: T } | { status: 500 };

export function getEventColors(
  eventKey: string,
): Promise<Response<EventColors>> {
  return fetch(`https://api.frc-colors.com/v1/event/${eventKey}`, {
    method: 'GET',
  })
    .then((r) => r.json())
    .then((data) => ({ status: 200, data: data as EventColors }))
    .catch(() => ({ status: 500 }));
}
