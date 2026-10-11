# Review context

Review the supplied working-tree refactor, report only. It moves a request to the
current API client and gives an internal duration a name with correct units.
Behavior and the wire protocol must stay unchanged. This snapshot is the whole
review scope and is not a runnable checkout.

## Repository authority: docs/api-migration.md

The installed API client `apiClient.get<T>(path)` returns the parsed body and
applies the existing authentication and error behavior. New and changed calls
must use it. The old `legacyGet<T>(path)` also returned the parsed body; untouched
files can remain on it during migration. Most neighboring files still use
`legacyGet`; this does not change the migration direction.

The external v1 response field `retry_seconds` is a historical wire name whose
documented unit is milliseconds. The response schema and fixtures are generated
from the provider specification. Preserve that key until a coordinated v2 change;
internal code should name the value `retryDelayMs`. The client validates the
response before returning it. The existing `sleep` function takes milliseconds.

## Patch

```diff
diff --git a/src/jobs/waitForRetry.ts b/src/jobs/waitForRetry.ts
--- a/src/jobs/waitForRetry.ts
+++ b/src/jobs/waitForRetry.ts
@@ -1,3 +1,3 @@
-import { legacyGet } from "../api/legacyGet";
+import { apiClient } from "../api/apiClient";
 import { sleep } from "../retry/sleep";
 import type { RetryResponse } from "../api/generated/RetryResponse";
@@ -5,5 +5,5 @@
 export async function waitForRetry(): Promise<void> {
-  const response = await legacyGet<RetryResponse>("/retry");
-  const retrySeconds = response.retry_seconds;
-  await sleep(retrySeconds);
+  const response = await apiClient.get<RetryResponse>("/retry");
+  const retryDelayMs = response.retry_seconds;
+  await sleep(retryDelayMs);
 }
```

## Verification evidence

The existing integration tests assert that a response with `retry_seconds: 30000`
results in a 30,000-millisecond delay and that a response without the field is
rejected by the client schema. Provider generation owns the wire type; it was
not reimplemented in this change. Both clients' source and contract tests confirm
the body-returning behavior described above. No other changed or untracked files
exist. The reviewer cannot execute checks against this text snapshot.
