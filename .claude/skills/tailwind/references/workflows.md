# Tailwind CSS v4 Workflows

## Contents
- Development Workflow
- Adding New Styles
- Debugging Missing Styles
- Production Build Process
- Theme Switching Implementation
- Migration from v3 to v4

---

## Development Workflow

### Starting Tailwind Development Server

```bash
# RECOMMENDED: Start both Django and Tailwind together
python manage.py tailwind dev

# Access application at http://127.0.0.1:8000/
# Tailwind will watch for changes and rebuild automatically
```

**What this does:**
1. Starts Django development server on port 8000
2. Starts Tailwind watcher in parallel
3. Rebuilds CSS on any template or Python file changes
4. Injects browser-reload script for instant updates

### Alternative: Run Separately (Two Terminals)

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Tailwind watcher
python manage.py tailwind start
```

**When to use separate terminals:**
- Debugging Django server issues (logs are clearer)
- Testing production build without watcher
- Working on backend-only changes (no CSS needed)

---

## Adding New Styles

### Workflow: Adding Custom Utility Classes

Copy this checklist and track progress:
- [ ] Step 1: Identify repeated pattern in templates (3+ occurrences)
- [ ] Step 2: Add utility to `theme/static_src/src/styles.css` in `@layer utilities`
- [ ] Step 3: Verify Tailwind watcher rebuilds CSS (check terminal output)
- [ ] Step 4: Use new class in template and refresh browser
- [ ] Step 5: Check if style applies (inspect element in DevTools)

**Example: Adding a custom gradient utility**

```css
/* theme/static_src/src/styles.css */
@layer utilities {
  .bg-gradient-radial {
    background-image: radial-gradient(circle, var(--tw-gradient-stops));
  }
}
```

```html
<!-- Use in template -->
<div class="bg-gradient-radial from-blue-500 to-purple-600">
  Radial gradient background
</div>
```

**Validation:**
1. Check terminal for rebuild output: `Rebuilding... Done in 150ms`
2. Inspect element in browser DevTools
3. If style missing, ensure `@source` directive includes template path

### Workflow: Adding Custom Theme Colors

Copy this checklist and track progress:
- [ ] Step 1: Define color in `@theme` block with semantic name
- [ ] Step 2: Use color via Tailwind utility (`bg-*`, `text-*`, `border-*`)
- [ ] Step 3: Verify color appears in browser
- [ ] Step 4: Test color in dark mode if applicable

```css
/* theme/static_src/src/styles.css */
@theme {
  --color-brand: #3b82f6;
  --color-brand-dark: #1e40af;
}
```

```html
<!-- Use custom color -->
<button class="bg-brand text-white hover:bg-brand-dark">
  Brand Button
</button>
```

**Validation:**
- Inspect computed styles: `background-color` should be `rgb(59, 130, 246)`
- Test hover state works correctly
- If color doesn't apply, check for typos in CSS variable name

---

## WARNING: Debugging Missing Styles

**The Problem:**

```html
<!-- Template uses class but style doesn't apply -->
<div class="bg-custom-blue text-lg">
  Text appears unstyled in browser
</div>
```

**Why Styles Go Missing:**
1. **Class not scanned** - Template path not in `@source` directive
2. **Typo in class name** - `bg-custm-blue` vs `bg-custom-blue`
3. **CSS variable undefined** - `@theme` block missing `--color-custom-blue`
4. **Specificity conflict** - Another CSS rule overriding Tailwind
5. **Build cache stale** - Need to restart Tailwind watcher

**Debugging Workflow:**

```bash
# Step 1: Check Tailwind watcher is running
# Look for terminal output: "Watching for changes..."

# Step 2: Inspect @source directive
# Edit theme/static_src/src/styles.css
```

```css
/* Verify template path is scanned */
@source "../../../**/*.{html,py,js}";  /* Should match template location */
```

```bash
# Step 3: Restart Tailwind watcher
# Press Ctrl+C in terminal running `python manage.py tailwind start`
python manage.py tailwind start

# Step 4: Hard refresh browser
# Chrome/Firefox: Ctrl+Shift+R (Cmd+Shift+R on Mac)

# Step 5: Inspect element in DevTools
# Right-click element → Inspect
# Check "Computed" tab for applied styles
# If class is crossed out, another rule is overriding it
```

**Iterate until resolved:**
1. Make configuration changes
2. Restart Tailwind watcher
3. Hard refresh browser
4. Inspect computed styles
5. If still broken, check browser console for errors

**Common Fixes:**

```css
/* Fix 1: Expand @source to catch all templates */
@source "../../../**/*.{html,py,js}";

/* Fix 2: Define missing CSS variable */
@theme {
  --color-custom-blue: #3b82f6;
}

/* Fix 3: Increase specificity for overrides */
@layer components {
  .force-bg-custom {
    background-color: var(--color-custom-blue) !important;
  }
}
```

---

## Production Build Process

### Workflow: Building Optimized CSS for Production

Copy this checklist and track progress:
- [ ] Step 1: Set production environment (`DJANGO_ENV=production`)
- [ ] Step 2: Build Tailwind CSS (`python manage.py tailwind build`)
- [ ] Step 3: Collect static files (`python manage.py collectstatic`)
- [ ] Step 4: Verify CSS file size is optimized (check build output)
- [ ] Step 5: Test critical pages load with production CSS

```bash
# Set production environment
export DJANGO_ENV=production
export DEBUG=False

# Build optimized Tailwind CSS (purges unused classes)
python manage.py tailwind build

# Expected output:
# Building Tailwind CSS...
# Done in 1.2s
# Output: theme/static/css/styles.css (42.3 KB)

# Collect all static files to STATIC_ROOT
python manage.py collectstatic --noinput

# Expected output:
# 127 static files copied to '/app/staticfiles'
```

**Validation:**

```bash
# Check compiled CSS size (should be <100KB for most projects)
ls -lh theme/static/css/styles.css

# Verify static files collected
ls staticfiles/css/

# Test production server serves CSS correctly
python manage.py runserver --settings=config.settings.production
# Visit http://127.0.0.1:8000/ and inspect page source
# <link> tag should reference /static/css/styles.css
```

**If production CSS is too large (>200KB):**
1. Unused classes aren't being purged (check `@source` directive)
2. Too many DaisyUI components included (review imports)
3. Custom CSS bloat in `@layer` blocks (audit for unused rules)

---

## Theme Switching Implementation

### Workflow: Adding Dark Mode Toggle

Copy this checklist and track progress:
- [ ] Step 1: Add theme toggle button to base template
- [ ] Step 2: Write JavaScript to switch `data-theme` attribute
- [ ] Step 3: Save preference to localStorage
- [ ] Step 4: Load saved preference on page load
- [ ] Step 5: Test all DaisyUI components in both themes

```html
<!-- theme/templates/base.html -->
<html lang="en" data-theme="light">
<head>
  <!-- Load theme preference before render to prevent flash -->
  <script>
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
  </script>
</head>
<body>
  <!-- Theme toggle button -->
  <button id="theme-toggle" class="btn btn-ghost btn-circle">
    <svg class="swap-on w-6 h-6"><!-- sun icon --></svg>
    <svg class="swap-off w-6 h-6"><!-- moon icon --></svg>
  </button>

  <script>
    const toggle = document.getElementById('theme-toggle');
    toggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
    });
  </script>
</body>
</html>
```

**Validation:**
1. Click theme toggle button
2. Verify all UI elements update colors immediately
3. Refresh page - theme should persist
4. Check localStorage in DevTools: Application → Local Storage → `theme` key

**Available DaisyUI themes:**
- `light` (default)
- `dark`
- `cupcake`
- `bumblebee`
- `emerald`
- `corporate`
- `synthwave`
- `retro`
- `cyberpunk`
- `valentine`
- `halloween`
- `garden`
- `forest`
- `aqua`
- `lofi`
- `pastel`
- `fantasy`
- `wireframe`
- `black`
- `luxury`
- `dracula`

### Custom Theme Configuration

```css
/* theme/static_src/src/styles.css */

/* Override light theme colors */
[data-theme="light"] {
  --color-primary: #3b82f6;
  --color-primary-content: #ffffff;
  --color-base-100: #ffffff;
  --color-base-content: #1f2937;
}

/* Override dark theme colors */
[data-theme="dark"] {
  --color-primary: #60a5fa;
  --color-primary-content: #1e3a8a;
  --color-base-100: #1f2937;
  --color-base-content: #f3f4f6;
}
```

---

## Migration from v3 to v4

### Workflow: Converting tailwind.config.js to CSS

If you find a `tailwind.config.js` file in older project versions:

Copy this checklist and track progress:
- [ ] Step 1: Read existing `tailwind.config.js` configuration
- [ ] Step 2: Convert `content` to `@source` directive
- [ ] Step 3: Convert `theme.extend` to `@theme` block
- [ ] Step 4: Convert `plugins` array to `@plugin` directives
- [ ] Step 5: Delete `tailwind.config.js`
- [ ] Step 6: Test all pages render correctly

**v3 Configuration (OLD):**

```javascript
// tailwind.config.js - DELETE THIS FILE
module.exports = {
  content: [
    './templates/**/*.html',
    './users/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        secondary: '#8b5cf6',
      },
      fontFamily: {
        display: ['Inter', 'sans-serif'],
      },
      spacing: {
        '18': '4.5rem',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('daisyui'),
  ],
  daisyui: {
    themes: ['light', 'dark'],
  },
}
```

**v4 Configuration (NEW):**

```css
/* theme/static_src/src/styles.css */
@import "tailwindcss";

/* Convert content → @source */
@source "../../../**/*.{html,py,js}";

/* Convert plugins → @plugin */
@plugin "@tailwindcss/forms";
@plugin "daisyui";

/* Convert theme.extend → @theme */
@theme {
  --color-primary: #3b82f6;
  --color-secondary: #8b5cf6;
  --font-family-display: "Inter", sans-serif;
  --spacing-18: 4.5rem;
}
```

**DaisyUI configuration (if needed):**

```javascript
// theme/static_src/postcss.config.js
export default {
  plugins: {
    'tailwindcss': {},
    'autoprefixer': {},
    'daisyui': {
      themes: ['light', 'dark'],
    },
  },
}
```

**Validation:**
1. Delete `tailwind.config.js`
2. Restart Tailwind watcher: `python manage.py tailwind start`
3. Check terminal for build errors
4. Visit all pages and verify styles apply correctly
5. If styles break, check browser console for missing CSS variables

---

## Docker Workflow

### Building Tailwind in Docker

```bash
# Start Docker with Tailwind development profile
docker compose --profile dev up --build

# This runs:
# 1. PostgreSQL container (db)
# 2. Redis container (redis)
# 3. Django web container (web)
# 4. Tailwind watcher container (tailwind) - only with --profile dev

# Watch Tailwind logs
docker compose logs -f tailwind

# Rebuild CSS in running container
docker compose exec tailwind npm run build
```

**Production Docker build:**

```dockerfile
# Dockerfile already includes Tailwind build step
RUN python manage.py tailwind install
RUN python manage.py tailwind build
RUN python manage.py collectstatic --noinput
```

**No manual intervention needed** - Docker build handles Tailwind compilation automatically.