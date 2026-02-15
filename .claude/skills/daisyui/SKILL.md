---
name: daisyui
description: |
  Applies pre-built DaisyUI components and theme customization
  Use when: Building UI with Tailwind CSS, implementing forms/buttons/modals, customizing themes
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# DaisyUI Skill

DaisyUI provides semantic component classes on top of Tailwind CSS. This project uses DaisyUI 5.x with Tailwind CSS v4's new CSS-based configuration. Components are applied via class names in Django templates, and theme customization happens in `theme/static_src/src/styles.css`.

## Quick Start

### Button Component

```html
<!-- theme/templates/registration/login.html -->
<button type="submit" class="btn btn-primary w-full">
    Sign In
</button>

<!-- With loading state -->
<button class="btn btn-primary" disabled>
    <span class="loading loading-spinner"></span>
    Processing...
</button>
```

### Form Input with Label

```html
<!-- theme/templates/registration/register.html -->
<div class="form-control">
    <label class="label">
        <span class="label-text">Email</span>
    </label>
    <input type="email" name="email" 
           class="input input-bordered" 
           required>
</div>
```

### Alert Messages

```html
<!-- theme/templates/partials/_messages.html -->
{% if messages %}
    {% for message in messages %}
        <div class="alert alert-{{ message.tags }} mb-4">
            <span>{{ message }}</span>
        </div>
    {% endfor %}
{% endif %}
```

### Card Layout

```html
<!-- theme/templates/dashboard.html -->
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title">Welcome</h2>
        <p>Your dashboard content here</p>
        <div class="card-actions justify-end">
            <button class="btn btn-primary">Action</button>
        </div>
    </div>
</div>
```

## Key Concepts

| Concept | Usage | Example |
|---------|-------|---------|
| Component Classes | Semantic class names for UI elements | `btn`, `card`, `modal`, `input` |
| Modifiers | Size/color/state variations | `btn-primary`, `btn-lg`, `btn-disabled` |
| Theme Attribute | Apply theme to HTML element | `data-theme="light"` or `data-theme="dark"` |
| Form Controls | Wrapper for form inputs | `<div class="form-control">` |
| Responsive Modifiers | Breakpoint-specific styling | `btn-wide lg:btn-block` |

## Common Patterns

### Form with Validation States

**When:** Building registration, login, or settings forms

```html
<!-- Success state -->
<div class="form-control">
    <input type="text" class="input input-bordered input-success">
    <label class="label">
        <span class="label-text-alt text-success">Valid input</span>
    </label>
</div>

<!-- Error state -->
<div class="form-control">
    <input type="text" class="input input-bordered input-error">
    <label class="label">
        <span class="label-text-alt text-error">{{ error_message }}</span>
    </label>
</div>
```

### Modal Dialog

**When:** Confirmation dialogs, forms in overlays

```html
<!-- Trigger button -->
<button class="btn" onclick="my_modal.showModal()">
    Open Modal
</button>

<!-- Modal -->
<dialog id="my_modal" class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg">Confirmation</h3>
        <p class="py-4">Are you sure?</p>
        <div class="modal-action">
            <form method="dialog">
                <button class="btn">Cancel</button>
                <button class="btn btn-primary">Confirm</button>
            </form>
        </div>
    </div>
</dialog>
```

### Navigation with Active States

**When:** Building header navigation (see `theme/templates/partials/_header.html`)

```html
<ul class="menu menu-horizontal px-1">
    <li><a href="/" class="{% if request.path == '/' %}active{% endif %}">Home</a></li>
    <li><a href="/dashboard/" class="{% if '/dashboard/' in request.path %}active{% endif %}">Dashboard</a></li>
</ul>
```

### Loading States

**When:** Async operations, form submissions

```html
<!-- Spinner -->
<span class="loading loading-spinner loading-lg"></span>

<!-- Dots -->
<span class="loading loading-dots loading-md"></span>

<!-- Button with loading -->
<button class="btn btn-primary">
    <span class="loading loading-spinner"></span>
    Saving...
</button>
```

## Theme Customization

Themes are switched via `data-theme` attribute on `<html>` tag in `base.html`. Available themes: light, dark, cupcake, synthwave, cyberpunk, and more.

See **tailwind** skill for Tailwind v4 CSS configuration and **patterns** reference for component integration patterns.

## See Also

- [patterns](references/patterns.md) - Component integration and form patterns
- [workflows](references/workflows.md) - Theme setup and component development

## Related Skills

- **tailwind** - DaisyUI is built on Tailwind CSS v4
- **frontend-design** - UI design patterns and responsive layouts
- **django** - Template integration and form rendering