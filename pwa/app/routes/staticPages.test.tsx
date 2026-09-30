import { describe, expect, test } from 'vitest';

import { Route as AboutRoute } from '~/routes/about';
import { Route as AccountRoute } from '~/routes/account.index';
import { Route as MyTbaRoute } from '~/routes/account.mytba';
import { Route as AddDataRoute } from '~/routes/add-data';
import { Route as ContactRoute } from '~/routes/contact';
import { Route as DonateRoute } from '~/routes/donate';
import { Route as PrivacyRoute } from '~/routes/privacy';
import { Route as ThanksRoute } from '~/routes/thanks';

// These route modules only declare a page component (plus server-only cache
// headers, which the client build strips). The pages themselves are covered by
// Playwright in tests/.
describe('component-only routes', () => {
  test('about route declares its page component', () => {
    expect(AboutRoute.options.component).toBeTypeOf('function');
  });

  test('add-data route declares its page component', () => {
    expect(AddDataRoute.options.component).toBeTypeOf('function');
  });

  test('contact route declares its page component', () => {
    expect(ContactRoute.options.component).toBeTypeOf('function');
  });

  test('donate route declares its page component', () => {
    expect(DonateRoute.options.component).toBeTypeOf('function');
  });

  test('privacy route declares its page component', () => {
    expect(PrivacyRoute.options.component).toBeTypeOf('function');
  });

  test('thanks route declares its page component', () => {
    expect(ThanksRoute.options.component).toBeTypeOf('function');
  });

  test('account route declares its page component', () => {
    expect(AccountRoute.options.component).toBeTypeOf('function');
  });

  test('myTBA route declares its page component', () => {
    expect(MyTbaRoute.options.component).toBeTypeOf('function');
  });
});
