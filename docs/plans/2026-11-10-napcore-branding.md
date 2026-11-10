# Plan: NAPCORE branding for the Helpdesk UI (#377)

Andrej Tibaut, 2026-11-10, against 0.97.163. Issue #377 (Sara Guerra de
Oliveira, 2026-11-09) is NAPCORE's consent to use its identity (confirmed by Andrej, 2026-11-10), so the result is
an ordinary PR that is merged and deployed. Claims are labelled **verified** (checked here, against the file or the
source named), **believed** or **assumed**.

## 1. What the issue asks

1. The NAPCORE logo and the "Co-funded by the European Union" emblem in the **header and the footer**.
2. Colours harmonised to a dark blue and a yellow: blue `#003399`, yellow `#FFCD00`.

Not asked, so not in scope: a new layout, a new font, dark mode, changes to the answer area's structure.

## 2. Rules the EU emblem brings (verified)

Source: European Commission, *The use of the EU emblem in the context of EU programmes 2021–2027. Operational
guidelines for recipients of EU funding*, March 2021
(https://www.eeas.europa.eu/sites/default/files/documents/2023/eu-emblem-rules.pdf), pp. 4–12.

- **Colours (p. 9):** EU corporate blue `#003399` (RGB 0/51/153); yellow `#FFCC00` (RGB 255/204/0).
  The issue's yellow `#FFCD00` is one step off the official `#FFCC00`. **Proposal:** use `#FFCC00` for the
  brand yellow, so the page and the emblem use the same yellow. Ask Sara in the PR; if she wants `#FFCD00` it is a
  one-token change.
- **Statement (p. 5):** "Co-funded by the European Union", spelled out in full (never "EU", never all capitals), next
  to the emblem, in Arial (or Auto, Calibri, Garamond, Tahoma, Trebuchet, Ubuntu, Verdana), in Reflex Blue, white or
  black, no underlining or effects, size in proportion to the emblem.
- **Do not re-typeset it:** use the ready-made emblem + statement files from the Commission's download centre
  (https://ec.europa.eu/regional_policy/en/information/logos_downloadcenter, p. 4), horizontal version (recommended
  for small sizes, p. 9). Positive version on white; the negative version (white text, white border around the
  flag) on blue.
- **Coloured background (p. 5):** if the flag sits on a coloured background, it needs a white border 1/25 of its
  height. The negative files already have it.
- **Prominence (pp. 4, 12):** the emblem must be at least as large as the largest other logo shown with it, must
  not be merged with another logo, and should stand at a distance from the beneficiary's logo. It must have a clear
  protection area (p. 9). Websites, including the mobile version, must show it prominently (p. 11).
- **Minimum size (p. 9):** flag height at least 1 cm, which is about 38 CSS px at 96 dpi. **Assumed:** we use
  40 px as the minimum on every screen width.

## 3. Current state (verified against `main`, 0.97.163)

- **Header:** `frontend/src/components/SharedAppLayout.tsx` renders a title, subtitle and version line. There is no
  logo and **no footer** anywhere in the app.
- **Styles:** a single `frontend/src/styles.css` (1,313 lines). `:root` defines 9 tokens (`--accent: #0f766e` teal,
  warm paper backgrounds). There are 77 distinct colour literals. The teal `#0f766e` is hard-coded 9 more times
  outside `:root`, beside `var(--accent)`. Teal/green gradients are used for the hero (`.hero`, line 136), the progress bar (line 1069), the
  panels (lines 185–241) and a button (line 447). The page background has a green/peach radial gradient (lines 36–37).
- **Inline colour:** `QuestionDetailPage.tsx:144` (`#5a9080`) and a border `#e0e0e0` at line 138.
- **Favicon:** `frontend/public/favicon.svg`, a white "N" on `#1a4f8a`.
- **Maintenance page:** `frontend/maintenance.html` has its own neutral palette (light and dark).
- **Font:** Space Grotesk (Google Fonts), IBM Plex Mono for code.

## 4. Design

### 4.1 Colour tokens

Replace the teal family with tokens and use them everywhere. No colour literals outside `:root` except
neutrals (white, greys, red for errors).

| Token | Value | Use |
|---|---|---|
| `--brand-blue` | `#003399` | title, links, primary buttons, header band, footer band |
| `--brand-blue-strong` | `#002266` (**assumed**, a darker shade for hover/active) | hover, pressed |
| `--brand-yellow` | `#FFCC00` | accents only: header rule, active nav marker, progress bar, focus ring |
| `--brand-tint` | `#eef2fb` (**assumed**) | panel and highlight backgrounds (replaces the mint tints) |
| `--accent`, `--accent-strong` | aliases of the two blues | existing rules keep working |

Contrast (WCAG 2.x, computed here; **verified**):

| Pair | Ratio | Allowed use |
|---|---|---|
| `#003399` on white | 10.9:1 | body text, links |
| white on `#003399` | 10.9:1 | header/footer text, button labels |
| `#003399` on `#FFCC00`-ish yellow | 7.2:1 | text on a yellow badge |
| dark ink `#1f2b26` on yellow | 9.8:1 | text on yellow |
| **white on yellow** | **1.5:1** | **never** |
| yellow on white | 1.5:1 | never as text; only as a bar or rule next to blue |

The page background becomes plain `--bg` (a light neutral). The warm paper colours stay for the reading area
(`--paper`), so answers keep their readability.

### 4.2 Header

```
┌──────────────────────────────────────────────────────────────────────┐
│ [NAPCORE logo]  NAPCORE Helpdesk                 [EU flag] Co-funded │  white
│                 Knowledge-Grounded, Multilingual…          by the EU…│
│                 v0.97.x · About this project                         │
├══════════════════════════════════════════════════════════════════════┤  4 px yellow rule
```

- White header, so both logos use their **positive** files and no white border is needed.
- NAPCORE logo on the left, before the title (the title stays a link to `/`). The EU emblem with the statement is
  on the right, at a distance from the NAPCORE logo (p. 4/11). Its flag is at least as tall as the NAPCORE logo, and
  at least 40 px.
- Title in `--brand-blue`, a 4 px `--brand-yellow` rule under the header.
- **Narrow screens (≤ 700 px, existing breakpoint):** logos on one row above the title. The emblem keeps its 40 px
  flag height; the NAPCORE logo shrinks to the same height. The emblem is never hidden on mobile (p. 11).

### 4.3 Footer (new)

```
┌──────────────────────────────────────────────────────────────────────┐
│ [NAPCORE logo, white]   About · Source code · Licence  [EU flag]     │  --brand-blue band
│                                                         Co-funded by │
│                                                         the European │
└──────────────────────────────────────────────────────────────────────┘
```

- `SharedAppLayout` gets a `<footer className="app-footer">` after `<Outlet />`, so every route has it.
- Blue band (`--brand-blue`), white text. The EU emblem uses the **negative** horizontal file (white statement,
  white border). The NAPCORE logo uses a white/negative version **if NAPCORE has one**; otherwise it sits on a white
  rounded box inside the band.
- Links: About this project; the GitHub repository and the licence (AGPL-3.0-only), both already linked from the
  About page (`AboutPage.tsx` lines 359–376). No new pages.

### 4.4 Other surfaces

- **Hero, progress bar, panels, primary button:** the teal gradients become `--brand-blue` (flat or a subtle
  blue→strong-blue gradient), the progress bar `--brand-blue`→`--brand-yellow`, the mint panel tints `--brand-tint`.
- **`QuestionDetailPage.tsx`:** the inline `#5a9080` button moves to a class using `--brand-blue`.
- **Favicon:** white "N" on `#003399` (keep the shape). **Optional:** the NAPCORE mark, if NAPCORE provides a
  square variant.
- **`maintenance.html`:** title colour `#003399` and the NAPCORE logo inline (it is served when the app is down, so
  it must not depend on the app's assets: inline SVG or a data URI).
- **About page:** no change to its content. It already describes the project; the footer carries the funding.
- **Font:** keep Space Grotesk (not asked). The EU statement comes as an image in Arial, as the rules require.

## 5. Assets

| Asset | Source | Notes |
|---|---|---|
| NAPCORE logo (SVG; positive and, if any, negative) | **ask Sara/NAPCORE** for the official files; napcore.eu shows the logo but a scraped copy may be outdated (**believed**) | goes to `frontend/src/assets/brand/` |
| "Co-funded by the European Union", horizontal, positive and negative, English | Commission download centre (§2) | SVG preferred, PNG at 2× otherwise; do not edit the files |

Only English for now; the UI is English. **Assumed:** no bilingual version (p. 8: needs a 2 cm flag, not
recommended small).

## 6. Steps (one PR)

1. **Assets:** add the four files under `frontend/src/assets/brand/` with a `README.md` that names their source and
   date.
2. **Tokens:** rework `:root` in `styles.css` (§4.1); replace the 9 `#0f766e` literals outside `:root`, the teal/mint gradients and
   the radial background with tokens. Check with `grep -nE '#[0-9a-fA-F]{3,6}' styles.css` that only neutrals and
   `:root` remain.
3. **Header:** logos in `SharedAppLayout.tsx`, CSS for the header row and the yellow rule, the 700 px layout.
4. **Footer:** the new `<footer>`, its CSS and links.
5. **Inline colours, favicon, maintenance page** (§4.4).
6. **Tests:** a Vitest test that the layout renders both logos with `alt` text ("NAPCORE", "Co-funded by the European
   Union") in the header and the footer. The existing frontend tests must stay green.
7. **Check by eye:** screenshots at 1280 px and 390 px of the start page, a question with an answer and a generated
   example, the About page and the editor console, before and after, attached to the PR. Check that the emblem's
   flag is ≥ 40 px at both widths (DevTools).
8. **Full cycle:** PR → CI → merge → version bump → deploy → check the live site at both widths. Close #377 with the
   screenshots.

Estimate (**assumed**): half a day once the NAPCORE logo files are in hand.

## 7. Open questions for Sara (put in the PR description)

1. Yellow: official EU `#FFCC00` (proposed) or `#FFCD00` as written in the issue?
2. The official NAPCORE logo files: SVG, and a version for dark backgrounds?
3. Is "Co-funded by the European Union" the right statement for the Helpdesk itself (NAPCORE is CEF co-funded), or
   should the footer also carry a disclaimer sentence? The guidelines do not require one. **Believed:** the grant
   agreement is the place to check.

## 8. Risks

- **Rule breaches are visible and public.** The emblem rules in §2 are checked item by item in the PR checklist
  (size, spacing, statement spelled out, official file unchanged, white border on blue).
- **Colour regressions in less visited views** (editor console, harvest panel, legal context). Step 2's grep and the
  screenshots of the editor console cover them.
- **Logo files late.** Steps 2, 4 (without logos), 5 and 6 can go ahead with placeholders. The PR is not merged with
  placeholders.
