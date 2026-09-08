# Firebase Realtime Database rules

`database.rules.json` is the source of truth for the production Realtime Database
(`tbatv-prod-hrd`) security rules. Nothing outside these paths is readable or
writable by clients; the backend writes through the Admin SDK, which bypasses rules.

Changes merged to `main` are deployed by the `deploy-firebase-rules` job in
`.github/workflows/push.yml`. To deploy by hand (needs a Firebase-enabled login):

```
cd ops/firebase && firebase deploy --only database --project tbatv-prod-hrd
```

The local emulator (`ops/dev/firebase/`) runs without rules and is unaffected.
