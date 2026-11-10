# Select checks appropriate to the requested product

- Functional: entry and navigation, input/validation, selection/boundaries, loading,
  meaningful empty versus error, permission, retry/cancel and relevant stale response.
- Persistence: actual request and saved values, requery/reentry, relevant downstream
  effect, authorized role context, uncertain write resolution and exact cleanup IDs.
- Visual: actually inspect captures for hierarchy, overlap/clipping, responsive layout
  within supported viewports, states, typography/CJK wrapping, alignment and adopted
  design consistency. DOM text being present does not establish visibility.
- Accessibility basics when relevant: meaningful labels/roles, actual keyboard order,
  focus visibility, actionable errors. This is not a comprehensive accessibility audit.
- Environment: target URL/build, role/org/backend, same tab and current refs, console/
  network evidence if available. Tool failure is not automatically a product defect.

Keep only relevant checks. Unsupported mobile, every state/role combination and every
screen size are not implied requirements. Unknown intent is a question with impact,
not an aesthetic preference promoted into a defect.
