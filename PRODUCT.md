# Product

## Register

product

## Users

**Volunteers** — members of an Indonesian-speaking local church who serve in worship and ministry. They check the app on a phone, often on a Sunday morning or the night before, to see what role they're playing this week. They are not technical and they are not full-time — they're checking quickly between other things.

**Admins / leaders** — a smaller group (typically a worship pastor, a tech lead, a service coordinator) who plan ahead. They build the lineup, assign people to slots, manage role definitions and recurring services. They use the app on a laptop or large phone, sometimes for an hour at a time when planning a month of services.

The app is bilingual: Bahasa Indonesia is the primary language, English is the secondary. Time zone Asia/Jakarta. Most use happens on weekday evenings (admins planning) and Sunday mornings (volunteers checking).

## Product Purpose

Coordinate who serves which role at which service. Replace the WhatsApp-and-spreadsheets workflow that most churches currently use with something that:

- Remembers the lineup template per service type (Pelayanan).
- Lets admins assign people to specific role slots quickly.
- Lets volunteers see only what's relevant to them.
- Supports recurring services without making each week a manual setup.

Success looks like: a volunteer opens the app, sees their next assignment in under three seconds, closes the app. An admin opens the app, fills the next service's empty slots in under five minutes, closes the app.

## Brand Personality

Warm, plain, reverent without being solemn. The product is for a church but it is not church furniture — it doesn't need stained-glass aesthetics, mystical purple, or Latin verbs in the UI. It needs to feel respectful of what it's organizing (people serving in worship) without dressing up.

Three words: **calm**, **plain-spoken**, **considered**.

Voice: short sentences. Indonesian first. No corporate verbs ("leverage", "empower"). No youth-pastor exclamation marks. The interface tells the truth about state — empty means empty, not "Get started by creating your first…".

## Anti-references

What this should NOT look like, and why:

- **Generic SaaS-violet dashboards** (Linear copies, gradient hero backgrounds, neon purple on dark navy). The category-reflex pull. Avoid the trained-data move.
- **Mystical / "spiritual" stock** — stained glass textures, candlelight gradients, italicized scripture pull-quotes, gold-leaf flourishes. The interface is a roster manager, not a devotional poster.
- **Hospital-cold whites** — pure white surfaces, gray dividers, zero hue temperature. The product should feel made for people, not for a clipboard.
- **Hero-metric dashboards** — big numbers + small labels + supporting stats. Not the right shape for this product. There is no metric a church staff person needs to "watch."
- **Decorative motion** — confetti, bouncy springs, page-load orchestration. Motion exists to confirm state changes, not to perform.

## Design Principles

1. **Plain over performative.** When a list of three things is the answer, ship a list of three things, not a dashboard.
2. **Mobile is the primary surface.** Most volunteer use is on a phone in someone's hand, not a 27-inch monitor. Tap targets, line lengths, and information density follow from that.
3. **Earned familiarity over invented affordances.** Forms look like forms. Tabs look like tabs. The user has limited patience for clever.
4. **The default reading is Indonesian.** Layouts must hold up when strings are 30% longer than the English source. Nothing relies on English-tight wrapping.
5. **Reverence through restraint.** The respect this product owes its subject is paid in restraint, not decoration. No accents earning their keep through volume.

## Accessibility & Inclusion

- **WCAG AA** at 14 px body minimum across all text/background pairs. AAA where the cost is small (body copy on surface).
- **Touch targets ≥ 44 × 44 px** on every interactive element. Visible size may be smaller; effective tap area grows via padding or a `::before` extension.
- **`prefers-reduced-motion`** honored — transforms and large-distance translates suppressed; opacity / color transitions kept for legibility.
- **Keyboard navigable** end to end. Visible `:focus-visible` ring on every interactive element.
- **Color-blind friendly** — state isn't carried by color alone (badge shape and label disambiguate alongside hue).
- **Bilingual layout integrity** — strings up to 200% English length must not break layout. No hard-coded widths around translatable text.
- **Light theme only.** Decision documented in DESIGN.md.
