Sitevars are database-backed configurations that are used to store configurations that need to be updated, or keys that will change from production to development. An example of a Sitevar being used for configuration is the [landing page configuration Sitevar](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/common/sitevars/landing_config.py). An example of a Sitevar being used for keys is the [Google API secrets Sitevar](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/common/sitevars/google_api_secret.py).

As mentioned, a Sitevar is backed by a database model called [Sitevar](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/common/models/sitevar.py) that is stored in ndb. However, these database models are wrapped via Sitevar classes to abstract away implementation details, such as referencing the Sitevar model by key, providing explicit methods for typed data access, etc.

## Sitevar Usage

### Creating a Sitevar

A Sitevar must extend `Sitevar` and specify some generic content type. Generally this content type will be a typed dictionary, but may also be a simple data type, like an integer or a boolean. At minimum the Sitevar must define a `key` string, `description` string, and a `default_value` of the generic content type via static method overrides. Sitevars should also define class methods to access their data to allow for explicit, typed data access.

#### (Example) Dictionary Sitevar

```python
from typing_extensions import TypedDict

from backend.common.sitevars.base import Sitevar


class ContentType(TypedDict):
    config_value: str


class DictionaryConfig(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "dictionary_config"

    @staticmethod
    def description() -> str:
        return "A dictionary of configuration data"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            config_value="",
        )

    @classmethod
    def config_value(cls) -> str:
        return cls.get().get("config_value")
```

#### (Example) Boolean Sitevar

```python
from backend.common.sitevars.base import Sitevar


class BooleanConfig(Sitevar[bool]):
    @staticmethod
    def key() -> str:
        return "boolean_config"

    @staticmethod
    def description() -> str:
        return "A boolean configuration value"

    @staticmethod
    def default_value() -> bool:
        return False

    @classmethod
    def config_value(cls) -> bool:
        return cls.get()
```

### Using a Sitevar

Sitevar data can be accessed via the Sitevar classes without much overhead. Accessing a Sitevar via the Sitevar classes guarentees a Sitevar object is always returned with some data, the data being accessed will exist, and the data being access has a known type.

```
from backend.common.sitevars import dictionary_config
from backend.common.sitevars.dictionary_config import DictionaryConfig

config_value = DictionaryConfig.config_value()
# The Sitevar will always exist in the database, config_value will always be a str

DictionaryConfig.put(dictionary_config.ContentType(config_value="new_config_value"))
```

## (Design) Why wrapper Sitevar classes?

If a Sitevar is just an ndb-backed model, why not interface with ndb Sitevar objects directly?

Each Sitevar model needs to be fetched via a key, which will be used several times throughout the codebase. Keep in mind - this fetch may fail if a Sitevar with the given ID does not exist.

```python
apistatus = Sitevar.get_by_id("apistatus")

if apistatus is None:
    # Sitevar might be None if the Sitevar does not exist yet
    return

# Do something with the Sitevar...
```

Once we have a Sitevar object, the API is unclear. A Sitevar exposes a `contents` dictionary and makes no guarantees around the contents of the `contents` dictionary. All

```python
is_contbuild_enabled = status_sitevar.contents.get("contbuild_enabled")
# Is `is_contbuild_enabled` None, True, or False, or some other object?
```

Finally, updates (or possibly initial inserts) all need to handle their own logic. Sometimes Sitevars do not necessarily need to be updated, if their value is not changing from the previous value.

```python
should_enable_notifications = True

notifications_enable = Sitevar.get_by_id("notifications.enable")

if notifications_enable.contents != should_enable_notifications:
    notifications_enable.contents = should_enable_notifications
    notifications_enable.put()
```

The [`Sitevar`](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/common/sitevars/sitevar.py) class is used to fix all of these issues. A Sitevar class that extends `Sitevar` specifies a key local to the file. If the Sitevar key changes, this value only needs to change in one file, as opposed to everywhere in the codebase.

A Sitevar class defines a `default_value`, which conforms to a typed `SVType`. The first upside to this approach is having a typed definition of what can exist in a Sitevar. The `SVType` might be a boolean, or an integer, or a typed dictionary. No matter the data, the type is known and able to be enforced by the type-checker. The second upside is defining a default value for a Sitevar allows interfacing with ndb using `get_or_insert` as opposed to `get_by_id`. This ensures that a Sitevar will never a `None` and will always exist in the database. This simplifies local development by automatically creating the necessary Sitevars in the database to be filled in by the user later.

Finally, Sitevar classes expose an `update` method which allows Sitevar classes to update their contents via the result of a lambda, as well as determine if they should be updated via the results of a lambda. This allows users to have a sophisticated yet DRY API for updating Sitevars. A simplier API is available via the `put` method, which will always update the Sitevar with the passed value.
