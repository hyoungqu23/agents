# PR context

Title: Cache tenant feature lookups

Body: Cache feature lookup results for the life of the process. Concurrent HTTP requests must remain safe.

Stack evidence:

```text
module example.com/tenant-api

go 1.24
```

# Patch

```diff
diff --git a/internal/features/service.go b/internal/features/service.go
--- a/internal/features/service.go
+++ b/internal/features/service.go
@@ -11,3 +11,4 @@ type Repository interface {
 type Service struct {
     repository Repository
+    cache map[string][]string
 }
@@ -15,3 +16,3 @@ type Service struct {
 func NewService(repository Repository) *Service {
-    return &Service{repository: repository}
+    return &Service{repository: repository, cache: make(map[string][]string)}
 }
@@ -19,3 +20,11 @@ func NewService(repository Repository) *Service {
 func (s *Service) Features(ctx context.Context, tenantID string) ([]string, error) {
-    return s.repository.Features(ctx, tenantID)
+    if cached, ok := s.cache[tenantID]; ok {
+        return cached, nil
+    }
+
+    features, err := s.repository.Features(ctx, tenantID)
+    if err == nil {
+        s.cache[tenantID] = features
+    }
+    return features, err
 }
```

The service is a singleton shared by HTTP handlers. Assume no tests or other changed files exist. The fixture is not a runnable checkout.
