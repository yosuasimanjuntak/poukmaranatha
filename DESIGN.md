# Design system

This is the locked design system for poukmaranatha. Tokens live in `theme/static_src/src/styles.css` (`@theme` block); semantic component classes live in `@layer components` of the same file. Compiled output: `theme/static/css/dist/styles.css`. Future variants must reference these tokens, not hard-coded values.

## Theme decision

**Light only.** Scene that forced the answer: an Indonesian volunteer at home on a Sunday morning, 7:00 AM, light streaming through a window, checking which role they're on for second service. A dark theme would feel out of register with that moment — institutional, after-hours, "tech." Light maps to the hour and the act.

No automatic dark-mode toggle. If the OS is in dark mode, this app stays light by design. Locking this is the decision; revisiting it requires a real reason, not aesthetic drift.

## Color

**Strategy: Restrained.** Tinted neutrals carry the surfaces; one brand primary handles emphasis (primary actions, current selection, sticky-header label color); one accent appears in moments (badges, asterisks, in-place state markers). Not Committed — the app does not need a saturated wash to communicate its identity, and a Committed strategy would fight the volunteer's attention every time they check a quick fact.

All values are OKLCH. Hex is for the front-matter, not the source. Chroma reduced as lightness approaches the extremes.

```css
@theme {
  /* Surfaces (tinted toward 290° violet — never pure white, never pure black) */
  --color-surface:        oklch(0.975 0.008 290);  /* page background */
  --color-card:           oklch(0.995 0.004 290);  /* card background — barely off-white */
  --color-ink:            oklch(0.20  0.030 290);  /* primary text */
  --color-ink-muted:      oklch(0.48  0.025 290);  /* secondary text, meta */
  --color-divider:        oklch(0.92  0.012 290);  /* hairlines and 1px borders */

  /* Primary — deeper violet, less candy-SaaS than the original #7E30E1 */
  --color-primary:        oklch(0.46  0.17  295);
  --color-primary-dark:   oklch(0.32  0.14  295);  /* hover, sticky header label */
  --color-primary-50:     oklch(0.94  0.04  295);  /* tinted background washes */

  /* Accent — orchid, used sparingly */
  --color-accent:         oklch(0.70  0.16  340);
  --color-accent-50:      oklch(0.95  0.03  340);

  /* Semantic */
  --color-danger:         oklch(0.55  0.20  25);
  --color-danger-50:      oklch(0.96  0.03  25);
  --color-success:        oklch(0.60  0.16  150);
  --color-success-50:     oklch(0.96  0.04  150);
  --color-warn:           oklch(0.68  0.16  60);
  --color-warn-50:        oklch(0.96  0.04  60);
}
```

Color rules:
- **Never `#000` or `#fff`** — every neutral has chroma ≥ 0.005 toward 290°.
- **Accent ≤ 10% of any surface.** Empty-state asterisks, badge backgrounds, transient state markers.
- **State is not carried by color alone.** Filled vs empty assignment slot uses both background tint and a label, not just hue.
- **Contrast targets** verified against `--color-surface` and `--color-card`:
  - `ink` on `surface` ≥ 7:1 (AAA body)
  - `ink-muted` on `surface` ≥ 4.5:1 (AA 14 px)
  - `primary-dark` on `surface` ≥ 4.5:1
  - `white` on `primary` ≥ 4.5:1
  - `primary` on `primary-50` ≥ 3:1 (large text / icons only)

## Typography

**Family: Inter (variable, self-hosted).** A UI-tuned sans with full Indonesian Latin coverage. Self-hosted at `theme/static/vendor/InterVariable.woff2` to avoid third-party CDN dependency and FOUT. One family for headings, body, labels, data — product UI does not need a display/body pairing.

```css
@font-face {
  font-family: "Inter";
  src: url("/static/vendor/InterVariable.woff2") format("woff2-variations");
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
```

**Scale** (1.125–1.20 ratios, product norm):

| Token        | Size       | Use |
|--------------|------------|-----|
| `--text-2xs` | 0.6875rem  | meta, badge text |
| `--text-xs`  | 0.75rem    | captions, helper text |
| `--text-sm`  | 0.875rem   | body small, list rows |
| `--text-base`| 1rem       | body |
| `--text-lg`  | 1.125rem   | section headings |
| `--text-xl`  | 1.3125rem  | page subheadings |
| `--text-2xl` | 1.5rem     | page H1 |
| `--text-3xl` | 1.875rem   | display H1 (login, error pages) |

**Weights:**
- 400 — body, secondary text
- 500 — buttons, labels, nav
- 600 — headings, sticky day labels
- 700 — badges (only place 700 is used)

**Body line length:** capped at 65 ch via `.prose-narrow` for any block of paragraph text. Dense rows (assignment lists, schedule cards) are exempt.

**Tracking:** `tracking-tight` (-0.025em) on display sizes (text-2xl+). `tracking-wider` (0.05em) on uppercase sticky day headers and badges. Otherwise normal.

**Numerals:** `font-variant-numeric: tabular-nums` on time strings (`{{ schedule.start_at|date:"H:i" }}`) so digits column-align inside list rows.

## Spacing

Standard Tailwind spacing scale (`0.25rem` base). Block-spacing rhythm utilities:

- `.stack-tight` — 0.5 rem between children. List rows, dense detail blocks.
- default `space-y-3` — 0.75 rem. Cards, generic stacks.
- `.stack-loose` — 1.25 rem. Forms with multiple fields, sections that need breath.

Lists tight; forms loose. No uniform rhythm across the app — pages should feel different in density depending on read vs write.

## Elevation

```css
--shadow-card:       0 1px 2px oklch(0.32 0.14 295 / 0.06), 0 8px 24px oklch(0.32 0.14 295 / 0.08);
--shadow-card-hover: 0 2px 4px oklch(0.32 0.14 295 / 0.08), 0 16px 40px oklch(0.32 0.14 295 / 0.14);
--shadow-pop:        0 12px 32px oklch(0.32 0.14 295 / 0.18);
```

All shadow tints use `primary-dark` so cards lift on a tinted background, not a generic gray fog. Three steps only: resting card, interactive hover, popover/toast.

## Motion

Locked from the prior design-engineering pass. Custom easings only — never raw `ease`/`ease-in`/`ease-out` for UI:

```css
--ease-out-strong:    cubic-bezier(0.22, 1, 0.36, 1);   /* releases */
--ease-out-soft:      cubic-bezier(0.16, 1, 0.3, 1);    /* entries */
--ease-in-out-strong: cubic-bezier(0.65, 0, 0.35, 1);
--ease-drawer:        cubic-bezier(0.32, 0.72, 0, 1);   /* sheet */
--ease-press:         cubic-bezier(0.4, 0, 0.6, 1);     /* tactile press */

--dur-instant: 80ms;   /* press feedback */
--dur-fast:    150ms;  /* color, hover */
--dur-base:    220ms;  /* swap, stagger */
--dur-page:    260ms;  /* page enter */
```

Rules:
- Only animate `transform` and `opacity`.
- Press feedback is `scale(0.97)` at 80 ms via `--ease-press` on every interactive element (`.btn:active`, `.press:active`).
- Modal entry: 300 ms `--ease-drawer` from `translateY(2rem) scale(0.95) opacity 0` → settled. Exit: 200 ms `--ease-out-strong`. Asymmetric.
- Stagger: 40 ms delay between siblings, capped at 8 items so item-N never feels late.
- `prefers-reduced-motion: reduce` kills transforms; preserves opacity/color.

## Components

Implemented in `@layer components` of `theme/static_src/src/styles.css`:

- **Button** — `.btn` with variants `.btn-primary` `.btn-secondary` `.btn-ghost` `.btn-danger` `.btn-danger-soft` `.btn-dashed`; sizes `.btn-sm` `.btn-lg` `.btn-icon` `.btn-block`. Press scale, hover gated by `(hover: hover) and (pointer: fine)`, `aria-busy` reveals in-button spinner.
- **Card** — `.card` with `.card-tight` / `.card-roomy` density; `.card-interactive` adds hover lift.
- **Input** — `.input`, `.select`, `.textarea`, `.input-sm` / `.select-sm`. Native form fields share polish via `@layer base`.
- **Badge** — `.badge`, `.badge-primary`, `.badge-success`, `.badge-danger`. Pill-shape, 700 weight, 0.625rem.
- **Modal** — `.modal-backdrop` + `.modal-panel`. Mobile bottom-sheet (`flex-end`), desktop centered.
- **Toast** — `.toast` + variants, region positioned bottom-center, Alpine store backed, Django messages bridge.
- **Spinner** — `.spinner` + `.spinner-sm` / `.spinner-lg`. Slowed under reduced-motion.
- **Skeleton** — `.skeleton`, `.skeleton-text`, `.skeleton-title`, `.skeleton-avatar`. Static under reduced-motion.
- **Tab link** — `.tab-link` for bottom nav with sliding accent indicator.
- **Segmented control** — `.segmented` + `.segmented-pill` + `.segmented-option`.
- **Empty state** — `.empty-state` with dashed border. Copy must teach (see Copy below), not just say "no X."

## Layout patterns

- **App shell:** sticky top bar (`templates/components/top_bar.html`), main content (`max-w-5xl`), bottom tabs on mobile (`templates/components/bottom_tabs.html`).
- **List + detail:** standard list views (e.g., `schedule_list`) use card rows in a `.stagger-children` container. Detail views use a header card + un-carded sections.
- **Forms:** wrapped in a single card. Required fields marked with `<span aria-hidden="true" class="text-accent">*</span>` after the label. Submit + Cancel pair, primary on left.
- **Modals:** for in-context selections only (user picker). Not for confirmations — those are dedicated pages (`user_confirm_delete`).

## Copy rules

- **Buttons / nav / tab labels:** Title Case. No trailing period.
- **Section headings, page H1:** Title Case.
- **Field labels, helper text:** Sentence case. No trailing period unless full sentence.
- **Empty-state copy, error messages:** full sentences with terminal punctuation.
- **No em dashes anywhere** (use commas, colons, parens). Also not `--`.
- **Indonesian terminology** is the canonical source; English follows. Words like "Pelayanan" stay in Indonesian even in the English UI — they're the proper noun for the concept.

## Anti-bans (project-specific reminders)

On top of the impeccable shared bans:

- **No nested cards.** A card inside a card is always wrong here.
- **No identical-card grids.** When >3 entries point to similar destinations, vary visual weight (size, label position, count vs. action).
- **No hero-metric template.** This product has no metrics worth watching.
- **No decorative gradients.** Solid colors only. Gradients are reserved for the page-enter blur mask and the sticky-header scrim.

## Slop test

Per-page question: "Could AI have made this without thinking?" If the answer is yes, the page failed. The token system, Inter at non-default weights, OKLCH color decisions, the un-carded layout choices, and the empty-state copy all exist to make the answer no.
