---
name: tailwind
description: |
  Configures Tailwind CSS v4 with @source, @theme, and @plugin directives
  Use when: Styling templates, adding custom CSS utilities, configuring design tokens, or working with theme/static_src files
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Tailwind CSS v4 Skill

This project uses Tailwind CSS v4 with **CSS-based configuration** instead of JavaScript config files. All configuration happens in `theme/static_src/src/styles.css` using `@import`, `@source`, `@theme`, and `@plugin` directives. No `tailwind.config.js` exists.

## Quick Start

### CSS-Based Configuration (v4 Syntax)

```css
/* theme/static_src/src/styles.css */
@import "tailwindcss";

/* Scan Django templates and Python files for classes */
@source "../../../**/*.{html,py,js}";

/* Load plugins directly in CSS */
@plugin "@tailwindcss/forms";

/* Custom theme configuration */
@theme {
  --color-primary: #3b82f6;
  --font-family-display: "Inter", sans-serif;
}
```

### DaisyUI Integration

```html
<!-- theme/templates/base.html -->
<html data-theme="light">
  <body>
    <button class="btn btn-primary">DaisyUI Button</button>
  </body>
</html>
```

## Key Concepts

| Concept | Usage | Example |
|---------|-------|---------|
| `@source` | Define content paths to scan | `@source "../../../**/*.html"` |
| `@theme` | Define CSS variables for theme | `@theme { --color-brand: #ff0000; }` |
| `@plugin` | Load Tailwind plugins in CSS | `@plugin "@tailwindcss/forms"` |
| `data-theme` | Switch DaisyUI themes | `<html data-theme="dark">` |

## Common Patterns

### Starting Development Server

**When:** Making CSS changes or styling templates

```bash
# Start both Django and Tailwind watcher
python manage.py tailwind dev

# Or run separately in two terminals
python manage.py runserver  # Terminal 1
python manage.py tailwind start  # Terminal 2
```

### Adding Custom Utilities

**When:** Need project-specific utility classes

```css
/* theme/static_src/src/styles.css */
@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
  
  .scrollbar-none {
    scrollbar-width: none;
  }
}
```

### Using DaisyUI Components

**When:** Building UI elements quickly

```html
<!-- Alert component -->
<div class="alert alert-warning">
  <svg class="h-6 w-6"><!-- icon --></svg>
  <span>Warning message</span>
</div>

<!-- Card component -->
<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <h2 class="card-title">Card Title</h2>
    <p>Card content</p>
  </div>
</div>
```

### Theme Switching

**When:** Implementing dark mode or theme preferences

```html
<!-- JavaScript theme switcher -->
<script>
  document.documentElement.setAttribute('data-theme', 'dark');
</script>

<!-- Available themes: light, dark, cupcake, synthwave, etc. -->
```

## Production Build

```bash
# Build optimized CSS for production
python manage.py tailwind build

# Collect all static files
python manage.py collectstatic --noinput
```

## See Also

- [patterns](references/patterns.md) - Configuration patterns and DaisyUI usage
- [workflows](references/workflows.md) - Development workflows and debugging

## Related Skills

- **daisyui** - UI component library built on Tailwind
- **postcss** - CSS processing pipeline configuration
- **node-npm** - Node.js dependency management for Tailwind
- **django** - Template integration and static file handling
- **frontend-design** - Overall UI/UX patterns