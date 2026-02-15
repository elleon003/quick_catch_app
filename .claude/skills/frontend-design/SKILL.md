---
name: frontend-design
description: |
  Applies Tailwind CSS v4 and DaisyUI 5.x components for responsive UI design.
  Use when: Styling templates, implementing responsive layouts, customizing DaisyUI themes, or applying Tailwind utility classes.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Frontend-design Skill

This project uses **Tailwind CSS v4** with CSS-based configuration (not JavaScript) and **DaisyUI 5.x** component library. All styling lives in `theme/static_src/src/styles.css` using new v4 directives (`@source`, `@theme`, `@plugin`). Django templates are in `theme/templates/` with partials in `theme/templates/partials/`.

## Quick Start

### Applying Tailwind Utilities in Templates

```django
{% extends 'base.html' %}

{% block content %}
<div class="container mx-auto px-4 py-8">
  <h1 class="text-3xl font-bold mb-6">Dashboard</h1>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- Cards -->
  </div>
</div>
{% endblock %}
```

### Using DaisyUI Components

```django
<!-- Button variants -->
<button class="btn btn-primary">Primary Action</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-ghost">Ghost</button>

<!-- Card component -->
<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <h2 class="card-title">Card Title</h2>
    <p>Card content here.</p>
    <div class="card-actions justify-end">
      <button class="btn btn-primary">Action</button>
    </div>
  </div>
</div>
```

### Customizing Tailwind v4 Configuration

```css
/* theme/static_src/src/styles.css */
@import "tailwindcss";

@source "../../../**/*.{html,py,js}";

@theme {
  --color-brand-primary: oklch(0.6 0.2 240);
  --font-sans: "Inter", system-ui, sans-serif;
  --spacing-section: 6rem;
}

@layer components {
  .section-padding {
    padding-block: var(--spacing-section);
  }
}
```

## Key Concepts

| Concept | Usage | Example |
|---------|-------|---------|
| **@source** | Content scanning for Tailwind | `@source "../../../**/*.{html,py,js}"` |
| **@theme** | CSS-based theme config | `@theme { --color-primary: #3b82f6; }` |
| **data-theme** | DaisyUI theme switching | `<html data-theme="synthwave">` |
| **@layer** | CSS layer organization | `@layer components { .btn-custom { ... } }` |
| **Responsive prefixes** | Mobile-first breakpoints | `md:grid-cols-2 lg:grid-cols-3` |

## Common Patterns

### Responsive Grid Layout

**When:** Building dashboard, card grids, or multi-column layouts

```django
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  {% for item in items %}
    <div class="card bg-base-100 shadow-lg">
      <!-- card content -->
    </div>
  {% endfor %}
</div>
```

### Form with DaisyUI Styling

**When:** Creating registration, login, or settings forms

```django
<form method="post" class="space-y-4">
  {% csrf_token %}
  <div class="form-control">
    <label class="label">
      <span class="label-text">Email</span>
    </label>
    <input type="email" name="email" class="input input-bordered" required>
  </div>
  <div class="form-control">
    <label class="label">
      <span class="label-text">Password</span>
    </label>
    <input type="password" name="password" class="input input-bordered" required>
  </div>
  <button type="submit" class="btn btn-primary w-full">Submit</button>
</form>
```

### Conditional Styling with Django Template Logic

**When:** Showing different styles based on user state

```django
<div class="alert {{ 'alert-success' if success else 'alert-error' }}">
  {{ message }}
</div>

<button class="btn {% if user.is_authenticated %}btn-secondary{% else %}btn-primary{% endif %}">
  {% if user.is_authenticated %}Dashboard{% else %}Sign Up{% endif %}
</button>
```

## See Also

- [aesthetics](references/aesthetics.md) - Typography, color, visual identity
- [components](references/components.md) - DaisyUI component patterns
- [layouts](references/layouts.md) - Responsive layout patterns
- [motion](references/motion.md) - CSS transitions and animations
- [patterns](references/patterns.md) - Design anti-patterns and best practices

## Related Skills

- **tailwind** - Tailwind CSS utility framework
- **daisyui** - DaisyUI component library
- **postcss** - PostCSS configuration and plugins
- **django** - Django template syntax and template tags
- **node-npm** - Installing and managing frontend dependencies