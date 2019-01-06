# The Blue Alliance Notification Serivce (TBANS)

TBANS is the service in The Blue Alliance that manages dispatching notifications, queueing notifications, and handling errors or retries for notifications.

## About TBANS

TBANS is built as a [microservice](https://cloud.google.com/appengine/docs/standard/python/microservices-on-app-engine) inside of the TBA monorepo. Running TBANS as a microservice has a few benefits. TBANS is easier to test locally and deploy to a test instance, since developers do not need to understand how the TBA codebase as a whole works, and do not need to get the entire TBA codebase up-and-running in order to work with the notification service. Additionally, running TBANS independently of the TBA service allows us to draw strict boundaries between TBA's responsibility with notifications. TBA should not need to construct notification objects, manage the sending or retrying of notifications, etc. This is all of the responsibility of TBANS.

TBANS is not a publicly facing service, and requests to TBANS should only be made from other TBA services.

## The API

The TBANS API is built using the [Google Proto RPC library](https://cloud.google.com/appengine/docs/standard/python/tools/protorpc/). This allows us to explicitly define a RPC service with endpoints, along with typed and validated request and response objects. This takes some of the heavy lifting off of the API - request objects get a base level of validation for free, and response objects are serialized properly when returning.

When working with notifications, services should interact with TBANS via it's defined API. You can see the full list of API endpoints in `tbans/tbans_service.py`. Services are able to call the TBANS API via a [ProtoRPC Transport](https://cloud.google.com/appengine/docs/standard/python/tools/protorpc/transport/transport). A wrapper around a ProtoRPC Transport for TBANS has been written and is available in the TBA monorepo in `helpers/tbans_helper.py`.

Any authorization surrounding notifications (ex: a Ping can only be dispatched for the caller, not for another user) should done by the calling service before calling TBANS.

The TBANS API is available at `{project-id}.appspot.com/tbans`, or at `tbans-dot-{project-id}.appspot.com`.

### API Endpoints

API endpoints are defined in the `TBANSService` class (in `tbans/tbans_service.py`). All endpoints must be defined with a request and response object that the endpoint expects. All TBANS endpoints should return a TBANSResponse-like object (more on this in the [Response Messages](#response-messages) section). We can look at the `ping` endpoint as an example.

```python
class TBANSService(remote.Service):
  ...
  @remote.method(PingRequest, TBANSResponse)
  def ping(self, request):
    ...
```

The `ping` endpoint expects a `PingRequest` (this will be the type of that `request` variable), and is expected to return a `TBANSResponse`. Validation that requests are sending the proper object, as well as some base object validation (required fields, types, etc.) is managed via the protorpc library. Additional validation outside of required fields and types should be handled in the API endpoint logic. For more information, see the [protorpc documentation](https://cloud.google.com/appengine/docs/standard/python/tools/protorpc/).

Endpoints are namespaced via their method name. All endpoints from the TBANS API are prefixed with `tbans.`. As a result, the ping endpoint path would be `/tbans.ping`.

### Request Messages

Request messages (in `tbans/models/service/messages.py`) should pass, at minimum, some delivery recipients. This might be FCM, a single webhook, multiple webhooks, or some combination. For convenience, the `FCM` and `Webhook` messages exist to represent these recipients. Messages should define their delivery recipients in a standard way via a field named `fcm`, a field named `webhook` or a repeated field named `webhooks`. Again, these delivery options aren't mutually exclusive and may be combined in one request message.

```python
class MulticastRequest(messages.Message):
  """ Send to FCM and several webhooks """
  fcm = messages.MessageField(FCM, 1)
  webhooks = messages.MessageField(Webhook, 2, repeated=True)
```

Any additional information for the endpoint should be sent with the request. In our example above, maybe we want to send a match key to clients. We should send the match key in the request.

```python
class MulticastRequest(messages.Message):
  ...
  match_key = messages.StringField(3, required=True)
```

We can then use these values in our service like normal Python objects.

```python
@remote.method(MulticastRequest, TBANSResponse)
def multicast(self, request):
  match_key = request.match_key
  ...
```

These request/response messages are [protorpc Message subclasses](https://cloud.google.com/appengine/docs/standard/python/tools/protorpc/messages/messageclass), and their fields are [protorpc Message Fields](https://cloud.google.com/appengine/docs/standard/python/tools/protorpc/messages/fieldclass).

### Response Messages

Response messages (in `tbans/models/service/messages.py`) should have a `code` and `message` field. For convenience, a base response object `TBANSResponse` is available. Response messages must be returned from API endpoints, unless an exception is thrown during the execution of the endpoint.

```python
...
@remote.method(PingRequest, TBANSResponse)
def ping(self, request):
  ...
  return TBANSResponse(code=200, message='Ping sent successfully')
```

If a response message needs to send more than just a `code`/`message`, a custom response message can be defined. Messages cannot subclass one another, which means it's the responsibility of the custom response message to replicate the functionality of a base response message. The custom response message must have `code`/`message` fields and may supply additional fields.

An example of a custom response message is a `VerificationResponse`.

```python
class VerificationResponse(messages.Message):
    code = messages.IntegerField(1, default=200, required=True)
    message = messages.StringField(2)
    verification_key = messages.StringField(3, required=True)
```

As mentioned above, the `VerificationResponse` defines a `code` and `message` field, but adds a third field, the `verification_key` field.

## Structure of a Notification

All `Notification` objects are subclasses of the base `Notification` object. A `Notification` manages a notification's data payload, it's human-readable title/message, and any platform-specific configuration options. The same `Notification` objects are used for push notifications as well as webhooks.

For more details on FCM notification payloads, see the [FCM v1 HTTP message documentation](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages). For more details on webhook notification payloads, see [The Blue Alliance's webhook documentation](https://www.thebluealliance.com/apidocs/webhooks).

### Notification Type

At minimum, a `Notification` should implement `_type()` (a `NotificationType`). This type will be sent in a push notification's data payload, or as a webhook payload's `message_type` field. The payloads will look like this.

```python
class TypeNotification(BaseNotification):
  ...
  @staticmethod
  def _type():
    return NotificationType.UPCOMING_MATCH
```

```jsonc
// an FCM payload for a Notification with only a type
{
  "message": {
    "data": {
      "message_type": "upcoming_match"
    }
  }
}

// a webhook payload for a Notification with only a type
{
  "message_type": "upcoming_match"
}
```

When adding a new Notification, make sure there's a `NotificationType` to match it.

### Notification Message

Push notifications might also want to a human-readable title/message combo. This is done by implementing `notification_payload`, which should return a `NotificationPayload` object. This field will be ignored for webhooks.

```python
class MessageNotification(BaseNotification):
  ...
  @property
  def notification_payload(self):
    return NotificationPayload(title='Some Title', body='Some body message')
```

```jsonc
// an FCM payload for a Notification with a title/message
{
  "message": {
    "notification": {
      "title": "Some Title",
      "body": "Some body message"
    },
    "data": {
      "message_type": "..."
    }
  }
}

// a webhook payload for a Notification with a title/message
{
  "message_type": "..."
}
```

### Notification Data

A notification may want to send some data along with it. This is done by implementing `data_payload`, which should return a dictionary. This payload will be sent in the push notification in the `data` field, in a webhook payload's `message_data` field.

Although the dictionary does not have to be flat, complexity should be avoided. All keys should be strings.

```python
class DataNotification(BaseNotification):
  ...
  @property
  def data_payload(self):
      return {
        'match_key': '2018miketqm1',
        'event_key': '2018miket'
      }
```

```jsonc
// an FCM payload for a Notification with a data payload
{
  "message": {
    "data": {
      "match_key": "2018miketqm1",
      "event_key": "2018miket"
      "message_type": "..."
    }
  }
}

// a webhook payload for a Notification with a data payload
{
  "message_data": {
    "match_key": "2018miketqm1",
    "event_key": "2018miket"
  },
  "message_type": "..."
}
```

### Varying Notification Data and Webhook Data

To send a different data payload for a push notification and a webhook notification, implement the `webhook_payload` function to return a dictionary to be sent to webhooks. By default, this `webhook_payload` will return a notification's `data_payload`.

An example of where data payloads should differ would be for a `update_favorite` notification. After a client updates its account's favorites, TBANS dispatches notifications to all the other clients for an account telling them to update their favorites. The client that caused this notification doesn't need to take any action, as it's data should be correct. In the push notification payload, we send the client token that caused this update to occur, so client-side we can either take action or ignore the notification.

However, webhooks don't need to be concerned with what mobile client caused this notification to be fired. As such, the notification can be built to exclude that information from the webhook payload.

```python
class UpdateFavoritesNotification(BaseNotification):
  ...
  @property
  def data_payload(self):
      return {
          'sending_device_key': self.sending_device_key
      }

  @property
  def webhook_payload(self):
      return None
```

```jsonc
// an FCM payload for a Notification with a data payload
{
  "message": {
    "data": {
      "sending_device_key": "some_token_here",
      "message_type": "..."
    }
  }
}

// a webhook payload for a Notification with a webhook payload, different from the data payload
{
  "message_type": "..."
}
```

### Client Platform Payloads

Push notification clients (ex: Android, iOS, web) use different platform-specific configurations when sending push notifications. These payloads are abstracted to `PlatformPayload` objects. This allows for general configuration of notifications, along with override points for platform-specific configuration payloads. Note: Webhooks do not use platform payloads, so these methods will be ignored when sending to webhooks.

To send a notification to all clients with a general configuration, implement `platform_payload` and return a `PlatformPayload`. For instance, we might want to send a notification that is viewed as high priority by all clients.

```python
class HighPriorityNotification(BaseNotification):
  ...
  @property
  def notification_payload(self):
    return PlatformPayload(priority=PlatformPayloadPriority.HIGH)
```

```jsonc
// an FCM payload for a notification with a platform payload
{
  "apns": {
    "apns-priority": "10"
  },
  "android": {
    "priority": "HIGH"
  },
  "webpush": {
    "Urgency": "high"
  },
  "message": {
    "data": {
      "message_type": "..."
    }
  }
}

// a webhook payload for a notification with a platform payload
{
  "message_type": "..."
}
```

The `PlatformPayload`s render methods will handle setting the appropriate keys/values for platform configurations. Above, you can see that every platform has a different key/value for priority, but our `PlatformPayload` manages setting it properly for each platform. This allows notifications to be built in a general way, but still take advantage of platform-specific configuration values.

Notifications can have platform-specific configurations that differ from the `platform_payload` as well. These override points are exposed as the `android_payload`, `apns_payload`, and `webpush_payload` methods. These methods should return a `PlatformPayload` initialized with a `PlatformPayloadType` for the platform.

For instance, maybe in our example above, maybe we want to send a high priority notification to every platform except the web, where we'll send the notification as normal priority. We can override the web's platform payload configuration.

```python
class HighPriorityNotification(BaseNotification):
  ...
  @property
  def notification_payload(self):
    return PlatformPayload(priority=PlatformPayloadPriority.HIGH)

  @property
  def webpush_payload(self):
    return PlatformPayload(platform_type=PlatformPayloadType.WEBPUSH, priority=PlatformPayloadPriority.NORMAL)
```

```jsonc
// an FCM payload for a notification with a platform payload and a platform-specific payload
{
  "apns": {
    "apns-priority": "10"
  },
  "android": {
    "priority": "HIGH"
  },
  "webpush": {
    "Urgency": "normal"
  },
  "message": {
    "data": {
      "message_type": "..."
    }
  }
}

// a webhook payload for a notification with a platform payload and a platform-specific payload
{
  "message_type": "..."
}
```

## Running TBANS Locally

TBANS will start with the Docker container (usually running on port 8084). Otherwise, you can start TBANS on port 8080 using paver.

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
}' http://localhost:8084/tbans.ping
```

Notifications are best tested via the web notifications or webhooks. This documentation will be updated when the web supports notifications to provide instructions on how to test. Webhooks can be tested via [ngrok](https://ngrok.com/download), or the steps outlined in the [testing section of our webhook documentation](https://www.thebluealliance.com/apidocs/webhooks#testing).

As a note, until https://issuetracker.google.com/issues/35901176 is solved, only hit HTTP webhooks, unless you're able to do the suggested workaround.
