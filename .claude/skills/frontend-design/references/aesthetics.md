# Aesthetics Reference

## Contents
- Typography System
- Color Palette and Semantic Tokens
- Visual Identity
- Dark Mode and Theme Switching
- Design Tokens Configuration

---

## Typography System

This project uses **system font stack** by default through DaisyUI. Custom fonts can be added via CSS variables.

### Default Font Stack

```css
/* theme/static_src/src/styles.css */
@theme {
  /* Override DaisyUI font stack */
  --font-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: "JetBrains Mono", "Fira Code", Consolas, monospace;
}
```

### Typography Scale

**DO:** Use Tailwind's semantic text sizes for consistent hierarchy.

```django
<!-- GOOD - Clear visual hierarchy -->
<h1 class="text-4xl font-bold mb-2">Main Heading</h1>
<h2 class="text-2xl font-semibold mb-4">Subheading</h2>
<p class="text-base leading-relaxed">Body text with comfortable line-height.</p>
<small class="text-sm text-base-content/70">Helper text</small>
```

**DON'T:** Use arbitrary values that break consistency.

```django
<!-- BAD - Inconsistent sizing -->
<h1 class="text-[37px] font-[650]">Heading</h1>
<p class="text-[17px] leading-[1.43]">Body</p>
```

**Why This Breaks:**
1. Custom pixel values bypass the design system
2. Non-standard font weights create visual noise
3. Hard to maintain across the codebase
4. Breaks responsive scaling

### Readable Line Lengths

**DO:** Constrain text width for readability (45-75 characters per line).

```django
<!-- GOOD - Comfortable reading width -->
<article class="max-w-2xl mx-auto prose prose-lg">
  <p class="leading-relaxed">Long-form content here...</p>
</article>
```

**DON'T:** Let text span full viewport width.

```django
<!-- BAD - Eye strain on wide screens -->
<div class="w-full">
  <p>Text that stretches across a 2560px monitor...</p>
</div>
```

---

## Color Palette and Semantic Tokens

DaisyUI provides semantic color tokens that adapt to theme switching.

### Semantic Color Usage

**DO:** Use DaisyUI semantic tokens for theme-aware colors.

```django
<!-- GOOD - Theme-adaptive colors -->
<div class="bg-base-100 text-base-content border-base-300">
  <button class="btn btn-primary">Primary Action</button>
  <span class="text-success">Success message</span>
  <span class="text-error">Error message</span>
</div>
```

**DON'T:** Hardcode color values that break in dark mode.

```django
<!-- BAD - Breaks in dark themes -->
<div class="bg-white text-gray-900 border-gray-300">
  <button class="bg-blue-600 text-white">Action</button>
</div>
```

**Why This Breaks:**
1. White backgrounds blind users in dark mode
2. Hardcoded colors ignore theme switching
3. Lacks semantic meaning (what is "blue-600"?)
4. Harder to rebrand or customize

### DaisyUI Color Tokens

| Token | Purpose | Example |
|-------|---------|---------|
| `base-100` | Main background | Page backgrounds |
| `base-200` | Secondary background | Cards, panels |
| `base-300` | Borders, dividers | `border-base-300` |
| `base-content` | Text on base colors | `text-base-content` |
| `primary` | Brand primary actions | `btn-primary`, `bg-primary` |
| `secondary` | Secondary actions | `btn-secondary` |
| `accent` | Highlights, CTAs | `badge-accent` |
| `success` | Positive feedback | `alert-success` |
| `warning` | Caution messages | `alert-warning` |
| `error` | Error states | `text-error` |

### Custom Brand Colors

**DO:** Define brand colors in Tailwind v4 theme config.

```css
/* theme/static_src/src/styles.css */
@theme {
  --color-brand-primary: oklch(0.6 0.2 240);
  --color-brand-accent: oklch(0.7 0.25 350);
  --color-brand-neutral: oklch(0.5 0.05 240);
}

@layer components {
  .btn-brand {
    background-color: var(--color-brand-primary);
    color: white;
  }
}
```

**Usage:**
```django
<button class="btn-brand">Custom Brand Button</button>
```

---

## Visual Identity

### Consistent Component Styling

**DO:** Use DaisyUI variants consistently across the app.

```django
<!-- GOOD - Consistent button styling -->
<button class="btn btn-primary">Primary Action</button>
<button class="btn btn-secondary">Secondary Action</button>
<button class="btn btn-ghost">Tertiary Action</button>
```

**DON'T:** Mix custom styling with DaisyUI haphazardly.

```django
<!-- BAD - Inconsistent visual language -->
<button class="btn btn-primary">Action 1</button>
<button class="bg-blue-500 px-4 py-2 rounded">Action 2</button>
<a href="#" class="underline text-blue-600">Action 3</a>
```

### Border Radius Consistency

**DO:** Stick to DaisyUI's border radius scale.

```css
/* DaisyUI default border radius */
@theme {
  --rounded-box: 1rem;  /* Cards, containers */
  --rounded-btn: 0.5rem; /* Buttons */
  --rounded-badge: 1.9rem; /* Pills */
}
```

```django
<!-- Use DaisyUI classes -->
<div class="card">...</div> <!-- Uses --rounded-box -->
<button class="btn">...</button> <!-- Uses --rounded-btn -->
```

---

## Dark Mode and Theme Switching

DaisyUI handles dark mode via the `data-theme` attribute on `<html>`.

### Theme Switching Implementation

**DO:** Set theme via `data-theme` attribute.

```django
<!-- theme/templates/base.html -->
<html lang="en" data-theme="light">
  <!-- or data-theme="dark", "synthwave", "cyberpunk", etc. -->
</html>
```

**JavaScript theme toggler:**

```javascript
// Toggle between light and dark
const toggleTheme = () => {
  const html = document.documentElement;
  const currentTheme = html.getAttribute('data-theme');
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
};

// Load saved theme on page load
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
});
```

### Available DaisyUI Themes

```django
<!-- Choose from 30+ built-in themes -->
data-theme="light"       <!-- Default light theme -->
data-theme="dark"        <!-- Default dark theme -->
data-theme="synthwave"   <!-- Neon retro -->
data-theme="cyberpunk"   <!-- High contrast -->
data-theme="forest"      <!-- Green palette -->
data-theme="luxury"      <!-- Gold accents -->
```

See full list: https://daisyui.com/docs/themes/

---

## Design Tokens Configuration

### Tailwind v4 Theme Customization

**DO:** Define design tokens in `@theme` block.

```css
/* theme/static_src/src/styles.css */
@import "tailwindcss";

@theme {
  /* Spacing scale */
  --spacing-section: 6rem;
  --spacing-card: 2rem;
  
  /* Typography */
  --font-sans: "Inter", system-ui, sans-serif;
  --font-display: "Poppins", sans-serif;
  
  /* Shadows */
  --shadow-card: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-elevated: 0 20px 25px -5px rgb(0 0 0 / 0.1);
  
  /* Border radius */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 1rem;
}
```

**Usage:**

```django
<div class="p-[--spacing-card] rounded-[--radius-lg] shadow-[--shadow-card]">
  Custom spacing and shadows
</div>
```

### CSS Layers for Organization

```css
@layer base {
  /* Reset and base styles */
  body {
    @apply bg-base-100 text-base-content;
  }
}

@layer components {
  /* Custom component styles */
  .card-custom {
    @apply bg-base-200 rounded-lg p-6 shadow-lg;
  }
}

@layer utilities {
  /* Custom utility classes */
  .text-balance {
    text-wrap: balance;
  }
}
```

**Why Layers Matter:**
1. Proper CSS specificity order
2. Tailwind can optimize and purge correctly
3. Prevents utility class overrides
4. Cleaner compiled CSS