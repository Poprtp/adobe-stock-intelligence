# Adobe Stock Studio Design System

## Direction

Adobe Stock Studio uses a minimal monotone creative-software interface. The
style should feel closer to Linear, Notion, Arc Browser, Raycast, Adobe
Lightroom, and Figma than a themed analytics dashboard.

Rules:

- Use monochrome only.
- Use top navigation only.
- Do not use colorful accents.
- Do not use gradients.
- Do not use decorative shadows.
- Prefer whitespace, thin borders, and restrained typography.

## Color Tokens

- `--studio-bg`: `#0f0f10`
- `--studio-surface`: `#171717`
- `--studio-surface-2`: `#1f1f1f`
- `--studio-border`: `#303030`
- `--studio-text`: `#f2f2f2`
- `--studio-muted`: `#a3a3a3`
- `--studio-subtle`: `#737373`

## Typography Scale

- Font stack: `Inter`, `Geist`, system UI, sans-serif.
- Prompt font stack: `JetBrains Mono`, `Cascadia Code`, monospace.
- Page title: restrained `h1`, no oversized hero treatment.
- Section title: compact `h2` or `h3`.
- Small labels: uppercase, muted, used sparingly.
- Letter spacing remains `0`.

## Spacing System

- Base spacing unit: `8px`.
- Page max width: 1440-1600px, currently `1520px`.
- Page side padding: `40px`.
- Cards: `20px` internal padding.
- Section rhythm: use clear vertical spacing before headings and cards.

## Card Rules

- Background: `--studio-surface`.
- Border: 1px solid `--studio-border`.
- Radius: approximately `16px`.
- No decorative shadows.
- Character cards must be compact and include:
  - Assistant name
  - Role
  - Next recommendation
  - Current task

## Button Rules

- Buttons use `--studio-surface-2`.
- Buttons use thin neutral borders.
- No colorful primary states.
- Labels should be direct actions, such as `Mark Generated`, `Mark Selected`,
  and `Next Image`.

## Form Controls

- Inputs and text areas use `--studio-surface`.
- Borders use `--studio-border`.
- Prompt text areas use monospace typography.
- Controls should support production workflow without visual noise.

## Status States

Prompt status values:

- `Todo`
- `Generated`
- `Selected`
- `Uploaded`

Status indicators stay monochrome. Progress is shown with a neutral progress
bar and text such as `0 / 10 completed`.

## Empty States

Empty states should tell the user the next concrete step, usually:

- Run `python src/main.py`.
- Generate production prompt files.
- Start with Image 01.

Avoid decorative empty-state illustrations.

## Layout Rules

- Navigation is horizontal top navigation via tabs.
- Sidebar navigation is not used.
- Content is centered with readable max width.
- Production Studio uses:

```text
Image List | Prompt Workspace | Actions / Notes
```

- Prompt Workspace must be the largest area.
- The app keeps these rooms:
  - CEO Office
  - Strategy Room
  - Art Department
  - Production Studio
  - QA Room
  - Upload Center
  - Portfolio Room
