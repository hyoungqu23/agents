# Host browser / Playwright MCP / DevTools MCP

Use the host's actual browser API documentation or exposed tool schema, not a
copied external QA skill. Inventory available sessions only when needed. Bind the
user's named tab/browser; otherwise reuse an appropriate authorized session or own
QA tab. Record the actual provider/tab/context and unexposed version as unknown.

Inspect current DOM/accessibility state to select supported locator/ref input.
After acting, wait for a meaningful URL/element/text/state and observe again.
Screenshot through the exposed capture API, save the actual bytes and deliver/open
the image with the host image-view tool. A screenshot response containing only a
file path is not an image inspection. Record the tool trace that exposed the image.

Use available console/network observations without intercepting or replacing responses.
If the schema lacks network inspection or modifier/native input, report that limit
for those checks. Do not invoke hidden APIs, inject app state or install packages
as an automatic fallback. Preserve borrowed browser sessions and only close owned tabs.
