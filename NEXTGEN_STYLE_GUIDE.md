# NextGen Design System & Style Guide

Use this document as a master reference to replicate the "NextGen" product aesthetic. The design is characterized as **"Premium Corporate"**—professional, high-contrast, and clean, with a focus on luxury travel and management.

## 1. Core Visual Identity

### Color Palette (HSL)
The system uses a specific set of HSL variables for consistency.

| Name | HSL Value | Description |
| :--- | :--- | :--- |
| **Primary (Royal Blue)** | `220 67% 19%` | Core brand color. Used for headers, primary buttons, and sidebars. |
| **Accent (Premium Gold)** | `43 82% 49%` | Action color. Used for highlights, active states, and CTAs. |
| **Midnight** | `224 47% 11%` | Deepest neutral. Used for text and dark backgrounds. |
| **Background** | `0 0% 98%` | Lightest neutral. Main app background. |
| **Foreground** | `224 47% 11%` | Standard text color (Midnight). |
| **Secondary** | `214 32% 91%` | Light blue-gray for subtle backgrounds/hover states. |
| **Muted** | `220 14% 96%` | Very light gray for disabled or secondary text containers. |
| **Border** | `214 32% 91%` | Subtle borders for cards and inputs. |

### Typography
- **Font Family:** `Inter`, sans-serif (Standard system fonts as fallback).
- **Weights:** 300 (Light), 400 (Regular), 500 (Medium), 600 (Semi-bold), 700 (Bold), 900 (Black).
- **Headings:** Always `font-bold` and `tracking-tight`.
- **Body:** `antialiased`.

### Geometry & Spacing
- **Border Radius:** `0.125rem` (2px). The design favors sharp, professional corners over rounded ones.
- **Max Width:** Standard container is `max-w-7xl` (1280px).
- **Page Padding:** `px-4 md:px-6` (16px to 24px).

---

## 2. Key Components & Patterns

### Buttons
- **Primary:** Background: Royal Blue (`--primary`), Text: White. Sharp corners.
- **Accent/Action:** Background: Gold (`--gold`), Text: Royal Blue (`--gold-foreground`).
- **Ghost/Outline:** Border: `--border`, Text: `--foreground`. Hover: `--secondary`.

### Cards (Stat Cards)
- **Style:** Background: `--card` (White), Border: `--border`, Padding: `p-5`.
- **Hover:** Border color shifts to `hsl(var(--gold) / 0.4)`.
- **Stat Value:** `text-2xl font-semibold tracking-tight`.
- **Stat Label:** `text-xs uppercase tracking-wider font-medium text-muted-foreground`.

### Sidebars & Navigation
- **Theme:** Uses the **Midnight** or **Royal Blue** background.
- **Active State:** Uses **Gold** for the indicator or icon highlight.
- **Text:** White (`--primary-foreground`).

### Gradients
- **Gold Gradient:** `linear-gradient(135deg, hsl(43 82% 49%), hsl(43 82% 60%))`
- **Royal Gradient:** `linear-gradient(135deg, hsl(220 67% 19%), hsl(224 47% 11%))`

---

## 3. Implementation Hints (Tailwind CSS v3/v4)

When implementing, use these CSS variables in your `tailwind.config` or globals:

```css
:root {
  --primary: 220 67% 19%;
  --primary-foreground: 0 0% 98%;
  --gold: 43 82% 49%;
  --gold-foreground: 220 67% 19%;
  --midnight: 224 47% 11%;
  --background: 0 0% 98%;
  --foreground: 224 47% 11%;
  --secondary: 214 32% 91%;
  --border: 214 32% 91%;
  --radius: 0.125rem;
}
```

### Layout Strategy
- **Portals (Admin/Agent):** Sidebar + Top Header layout. The Sidebar is usually dark (`Midnight` or `Royal Blue`).
- **Search & Explore:** A two-column layout with a **Filter Sidebar** (25% width) and a **Results List/Grid** (75% width).
- **Public Trip Planner:** Sticky navigation bar, a large Hero section with a **Royal Gradient**, followed by a clean, white-background content area with large spacing (`py-12` to `py-20`).

### Common UI Patterns
- **Loading States:** Use skeletons (`bg-muted animate-pulse`) that mimic the shape of the final cards.
- **Empty States:** Centered content with a muted icon, a `text-xl font-bold` heading, and a primary CTA button.
- **Search Bars:** Rounded-sm (`radius-sm`) inputs with a `Gold` search button on the right.

---

## 4. Prompting Instruction for AI
"Replicate the design from this style guide. Focus on the **Royal Blue** and **Gold** contrast. Ensure all corners have a very small radius (**0.125rem**) for a sharp, premium look. Use **Inter** for typography with tight tracking on headings. The aesthetic should feel like a high-end travel management platform."
