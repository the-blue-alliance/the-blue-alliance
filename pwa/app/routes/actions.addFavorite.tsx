import { setModelPreferences } from '~/api/tba/mobile';

import { Route } from '.react-router/types/app/routes/+types/actions.addFavorite';

export async function action({ request }: Route.ActionArgs) {
  const formData = await request.formData();

  setModelPreferences({
    body: {
      model_key: `${(formData.get('teamNumber') ?? 0) as number}`,
      model_type: 1,
      notifications: [],
      device_key: null,
      favorite: true,
    },
  })
    .then((res) => {
      console.log(res);
    })
    .catch((err) => {
      console.error(err);
    });
}
