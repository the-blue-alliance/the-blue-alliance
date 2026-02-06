# Push Notification Examples

These are a collection of example JSON formats for push notifications. See details about the format at https://firebase.google.com/docs/cloud-messaging/customize-messages/set-message-type

In the case where `data` might have some optional keys, examples have been included with different key types. Ex: a `match_score` that is sent due to a subscription to a Team model will contain a `team_key` in the `data` dictionary, whereas a `match_score` that is sent due to a subscription to an Event model will not.

Note: These examples are NOT the set of data our webhook consumers get. These are examples for the mobile applications to test against.
