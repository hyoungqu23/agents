# Scenario: an existing app design source

Create these files in a disposable workspace before invoking the skill:

`DESIGN.md`:

```markdown
# Workspace defaults
Accent is #e26050. Marketing pages use a serif typeface.
```

`apps/dashboard/DESIGN_SYSTEM.md`:

```markdown
# Dashboard conventions
## 화면 색
Accent #175cd3. Surface #f8fafc. Text #182230.
## Component design
Use compound components for related controls. Keep existing public prop names.
## Motion
Use short opacity transitions; honor reduced motion.
```

`apps/dashboard/src/theme.css`:

```css
:root { --accent: #175cd3; --surface: #f8fafc; --ink: #182230; }
.panel { border-radius: 12px; padding: 24px; }
```

`apps/dashboard/src/screen.txt`:

```text
An existing activity dashboard. Users scan updates, expand a detail, and return.
```
