TBA uses the ndb library from the [Appengine Standard Runtime](https://github.com/GoogleCloudPlatform/appengine-python-standard) to interface with the [Google Cloud Datastore](https://cloud.google.com/datastore)

Datastore is highly scalable document based NoSQL database. On top of the datastore itself, the NDB library acts as an [ORM](https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping) and provides interfaces to manage the data's schema and manipulate the data stored.

[This page](https://cloud.google.com/appengine/docs/standard/python/ndb) describes an overview of the NDB library. We continue to use the legacy library to avoid breaking changes with the py2 runtime, as well as to continue using builtin memcache.

The core models of the site are:
 - `Team`, which represents the most up to date info about a given FRC team. The primary key for these is of the format `frc<team number>`
 - `Event`, which represents a single event. The primary key for these is of the formt `<year><event short code>`
 - `Match`, which represents a single match at a single event. The primary key is like `<event key>_<match ID>`

To link "attendence" for a team at an event, we have a small `EventTeam` model, which has indexed properties for both Event and Team keys, which lets us query the data cheaply from both directions. This "join model" pattern is commonly used elsewhere in the code, as well.

There are many other models, which store districts, their teams/rankings, linked media to teams/events/matches, user contributed suggestions, and more.
