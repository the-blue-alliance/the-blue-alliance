# The Blue Alliance Notification Serivce (TBANS)

TBANS is the service in The Blue Alliance that manages dispatching notifications and managing client subscription state with Firebase. Details about TBANS can be found in the [TBANS Eng Design Doc](https://docs.google.com/document/d/16ZdyL3WOJ1B4HmRAP6Qsl8DarZ29oYOul1Hv7PJuJOw/edit?usp=sharing).

## Running TBANS Locally

TBANS will start with the Docker container (usually running on port 8087). Otherwise, you can start TBANS on port 8080 using paver.

```
$ paver run_tbans
```

You can curl the TBANS service to test endpoints.

```bash
$ curl -X POST -H 'Content-Type: application/json' -d '{
  "webhook": {
    "url": "http://mysite.com",
    "secret": "some_secret"
  }
}' http://localhost:8087/tbans.ping
```

Notifications are best tested via the web notifications or webhooks. This documentation will be updated when the web supports notifications to provide instructions on how to test. Webhooks can be tested via [ngrok](https://ngrok.com/download), or the steps outlined in the [testing section of our webhook documentation](https://www.thebluealliance.com/apidocs/webhooks#testing).

As a note, until https://issuetracker.google.com/issues/35901176 is solved, only hit HTTP webhooks, unless you're able to do the suggested workaround.

## Structure of a Notification

All `Notification` objects are subclasses of the base `Notification` object. A `Notification` manages a notification's data payload, it's human-readable title/message, and any platform-specific configuration options. The same `Notification` objects are used for push notifications as well as webhooks.

For more details on FCM notification payloads, see the [FCM v1 HTTP message documentation](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages). For more details on webhook notification payloads, see [The Blue Alliance's webhook documentation](https://www.thebluealliance.com/apidocs/webhooks).

### Notification Type

```jsonc
// an FCM payload for a Notification with only a type
{
  "message": {
    "notification": {
      "title": "Some Title",
      "body": "Some body message"
    },
    "data": {
      "event_key": "2018miket",
      "match_key": "2018miketqm1",
      "notification_type": "upcoming_match"
    }
  }
}

// a webhook payload for a Notification with only a type
{
  "message_data": {
    "event_key": "2018miket",
    "match_key": "2018miketqm1"
  }
  "message_type": "upcoming_match"
}
```
