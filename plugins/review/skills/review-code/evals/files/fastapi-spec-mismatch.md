# PR context

Title: Add workspace API key rotation endpoint

Acceptance criteria:

1. Only members with the `admin` workspace role can rotate an API key.
2. A caller who is not a workspace member receives the existing not-found response.
3. The old key must be revoked in the same transaction that creates the replacement.

# Patch

```diff
diff --git a/app/api/workspace_keys.py b/app/api/workspace_keys.py
--- a/app/api/workspace_keys.py
+++ b/app/api/workspace_keys.py
@@ -18,1 +18,14 @@ router = APIRouter()
     return await service.list_keys(workspace_id, actor.user_id)
+
+@router.post("/workspaces/{workspace_id}/keys/{key_id}/rotate")
+async def rotate_workspace_key(
+    workspace_id: UUID,
+    key_id: UUID,
+    actor: User = Depends(current_user),
+    service: WorkspaceKeyService = Depends(get_workspace_key_service),
+):
+    membership = await service.get_membership(workspace_id, actor.id)
+    if membership is None:
+        raise WorkspaceNotFound()
+
+    return await service.rotate(workspace_id, key_id)
diff --git a/app/services/workspace_keys.py b/app/services/workspace_keys.py
--- a/app/services/workspace_keys.py
+++ b/app/services/workspace_keys.py
@@ -44,1 +44,6 @@ class WorkspaceKeyService:
         return await self.repository.list_for_workspace(workspace_id)
+
+    async def rotate(self, workspace_id: UUID, key_id: UUID) -> ApiKey:
+        async with self.repository.transaction():
+            await self.repository.revoke(workspace_id, key_id)
+            return await self.repository.create(workspace_id)
```

Stack evidence: `pyproject.toml` configures FastAPI, pytest, Ruff, and mypy. Assume no tests or other changed files exist. The fixture is not a runnable checkout.
