# Tailwind CSS v4 Patterns

## Contents
- Tailwind v4 Configuration Syntax
- Content Source Scanning
- Custom Theme Configuration
- DaisyUI Component Patterns
- Template Integration Patterns
- Anti-Patterns and Warnings

---

## Tailwind v4 Configuration Syntax

Tailwind v4 uses **CSS-based configuration** instead of JavaScript `tailwind.config.js` files.

### DO: Use CSS Directives for Configuration

```css
/* theme/static_src/src/styles.css - CORRECT v4 syntax */
@import "tailwindcss";

/* Scan template files for class names */
@source "../../../**/*.{html,py,js}";

/* Load first-party plugins */
@plugin "@tailwindcss/forms";
@plugin "@tailwindcss/typography";

/* Custom theme values as CSS variables */
@theme {
  --color-primary-50: #eff6ff;
  --color-primary-500: #3b82f6;
  --color-primary-900: #1e3a8a;
  
  --font-family-display: "Inter", system-ui, sans-serif;
  --font-size-xxl: 3rem;
  
  --spacing-18: 4.5rem;
}
```

**Why this works:**
- Native CSS syntax, no JavaScript build config needed
- CSS variables are runtime-modifiable (dark mode, theming)
- Explicit `@source` directive prevents missing scanned files
- Plugins loaded directly in CSS, not separate config

### DON'T: Look for tailwind.config.js

```javascript
// tailwind.config.js - DOES NOT EXIST IN V4 PROJECTS
module.exports = {
  content: ['./templates/**/*.html'],  // Wrong syntax for v4
  theme: {
    extend: {
      colors: { primary: '#3b82f6' }  // Use @theme in CSS instead
    }
  }
}
```

**Why this breaks:**
- This project uses Tailwind v4, which doesn't use JavaScript config
- JavaScript config patterns from v3 documentation won't work
- All configuration must be in `styles.css` using `@theme`, `@source`, `@plugin`

---

## WARNING: Content Source Scanning

**The Problem:**

```css
/* BAD - Missing Django template paths */
@source "../templates/**/*.html";  /* Only scans theme/templates */
```

**Why This Breaks:**
1. Django templates can be in multiple apps (users/, theme/, etc.)
2. Class names in Python view code (messages framework) won't be detected
3. Missing glob patterns cause unused class purging in production
4. Results in broken styles when classes aren't detected during build

**The Fix:**

```css
/* GOOD - Comprehensive path scanning */
@source "../../../**/*.{html,py,js}";  /* Scans entire project */

/* Alternative: Explicit multi-path scanning */
@source "../../../theme/templates/**/*.html";
@source "../../../users/templates/**/*.html";
@source "../../../**/views.py";
@source "../../../**/forms.py";
```

**When You Might Be Tempted:**
- Copying examples from Tailwind documentation (they assume simple project structures)
- Optimizing build times by reducing scanned files (this causes production bugs)
- Following v3 patterns where content is defined in JavaScript config

---

## Custom Theme Configuration

### DO: Use CSS Variables in @theme Block

```css
@theme {
  /* Color palette with semantic names */
  --color-brand-primary: #3b82f6;
  --color-brand-secondary: #8b5cf6;
  --color-danger: #ef4444;
  --color-success: #10b981;
  
  /* Typography scale */
  --font-size-xs: 0.75rem;
  --font-size-base: 1rem;
  --font-size-2xl: 1.5rem;
  
  /* Custom spacing for design system */
  --spacing-4_5: 1.125rem;  /* Between 4 and 5 */
  
  /* Shadow tokens */
  --shadow-glow: 0 0 20px rgba(59, 130, 246, 0.3);
}

/* Use in custom components */
@layer components {
  .btn-brand {
    background-color: var(--color-brand-primary);
    box-shadow: var(--shadow-glow);
  }
}
```

### DO: Extend DaisyUI Theme Variables

```css
/* Override DaisyUI theme colors */
@theme {
  --color-primary: #3b82f6;
  --color-primary-content: #ffffff;
  --color-secondary: #8b5cf6;
  --color-accent: #f59e0b;
  --color-neutral: #3d4451;
  --color-base-100: #ffffff;
}
```

**Why this works:**
- DaisyUI reads CSS variables for theming
- Values cascade to all DaisyUI components automatically
- Dark mode can override these with `[data-theme="dark"]` selector

---

## DaisyUI Component Patterns

### DO: Use Semantic Component Classes

```html
<!-- Button variants -->
<button class="btn btn-primary">Primary Action</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-outline">Outline</button>
<button class="btn btn-ghost">Ghost</button>
<button class="btn btn-link">Link Style</button>

<!-- Size modifiers -->
<button class="btn btn-xs">Tiny</button>
<button class="btn btn-sm">Small</button>
<button class="btn btn-lg">Large</button>

<!-- States -->
<button class="btn btn-primary loading">Loading...</button>
<button class="btn btn-disabled">Disabled</button>
```

### DO: Compose DaisyUI with Tailwind Utilities

```html
<!-- Card with custom spacing and shadows -->
<div class="card bg-base-100 shadow-xl hover:shadow-2xl transition-shadow duration-300">
  <figure class="px-10 pt-10">
    <img src="image.jpg" alt="Photo" class="rounded-xl" />
  </figure>
  <div class="card-body items-center text-center">
    <h2 class="card-title text-2xl font-bold">Card Title</h2>
    <p class="text-base-content/70">Description text</p>
    <div class="card-actions justify-end mt-4">
      <button class="btn btn-primary">Buy Now</button>
    </div>
  </div>
</div>
```

**Why this works:**
- DaisyUI components are Tailwind utilities under the hood
- Can mix DaisyUI semantic classes with Tailwind utilities
- No JavaScript required, pure CSS component system

### WARNING: Don't Mix Conflicting Style Classes

**The Problem:**

```html
<!-- BAD - Conflicting button styles -->
<button class="btn btn-primary bg-red-500 text-white">
  <!-- bg-red-500 conflicts with btn-primary's color -->
</button>

<!-- BAD - Redundant padding on DaisyUI components -->
<div class="card p-8">
  <div class="card-body p-4">  <!-- card-body already has padding -->
    Content
  </div>
</div>
```

**Why This Breaks:**
1. CSS specificity battles cause unpredictable rendering
2. DaisyUI components have built-in spacing that you're overriding
3. Maintenance nightmare when DaisyUI updates change defaults
4. Violates single responsibility - component OR utility, not both

**The Fix:**

```html
<!-- GOOD - Use component variants OR custom utilities -->
<button class="btn btn-error">Error Button</button>  <!-- Use DaisyUI variant -->
<!-- OR -->
<button class="bg-red-500 text-white px-4 py-2 rounded">Custom Button</button>

<!-- GOOD - Respect component structure -->
<div class="card">
  <div class="card-body">  <!-- Use default spacing -->
    <div class="space-y-4">  <!-- Add spacing to children instead -->
      Content
    </div>
  </div>
</div>
```

---

## Template Integration Patterns

### DO: Load Static Files in Base Template

```html
<!-- theme/templates/base.html -->
{% load static tailwind_tags %}
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Django Starter{% endblock %}</title>
  
  {% tailwind_css %}  <!-- Loads compiled Tailwind CSS -->
  
  {% block extra_css %}{% endblock %}
</head>
<body>
  {% block content %}{% endblock %}
  {% block extra_js %}{% endblock %}
</body>
</html>
```

### DO: Use Tailwind Classes in Django Forms

```python
# users/forms.py
from django import forms

class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'you@example.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'John'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '••••••••'
            }),
        }
```

**Why this works:**
- DaisyUI `input` class provides consistent form styling
- Tailwind utilities (`w-full`) adjust layout
- `input-bordered` adds visual boundaries matching DaisyUI theme
- Classes are scanned by `@source` directive during build

### DO: Use Template Partials for Reusable Components

```html
<!-- theme/templates/partials/_alert.html -->
<div class="alert alert-{{ type|default:'info' }} shadow-lg">
  <div>
    {% if icon %}
      <svg class="w-6 h-6">{{ icon|safe }}</svg>
    {% endif %}
    <span>{{ message }}</span>
  </div>
</div>

<!-- Usage in other templates -->
{% include 'partials/_alert.html' with type='warning' message='Session expires in 5 minutes' %}
```

---

## Custom Utility Layers

### DO: Use @layer for Custom Utilities

```css
/* theme/static_src/src/styles.css */

@layer base {
  /* Global element styles */
  body {
    @apply font-sans antialiased;
  }
  
  h1, h2, h3 {
    @apply font-bold tracking-tight;
  }
}

@layer components {
  /* Reusable component classes */
  .btn-custom {
    @apply px-4 py-2 rounded-lg font-medium transition-all;
  }
  
  .card-hover {
    @apply hover:shadow-xl hover:-translate-y-1 transition-transform duration-200;
  }
}

@layer utilities {
  /* Custom utility classes */
  .text-balance {
    text-wrap: balance;
  }
  
  .scrollbar-thin {
    scrollbar-width: thin;
  }
}
```

**Why this works:**
- `@layer` ensures proper CSS cascade order (base → components → utilities)
- Custom utilities can be used with modifiers: `hover:text-balance`
- Separation of concerns: base resets, components for repeated patterns, utilities for one-offs