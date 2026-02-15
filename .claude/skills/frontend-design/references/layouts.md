# Layouts Reference

## Contents
- Container and Max-Width Patterns
- Grid Systems
- Responsive Breakpoints
- Flexbox Layouts
- Spacing Scale
- Page Layout Templates

---

## Container and Max-Width Patterns

### Container Usage

**DO:** Use container for centered, max-width content.

```django
{% extends 'base.html' %}

{% block content %}
<div class="container mx-auto px-4 py-8">
  <h1 class="text-3xl font-bold mb-6">Page Title</h1>
  <!-- Content -->
</div>
{% endblock %}
```

**Why:** Centers content, adds horizontal padding, and prevents text from spanning full viewport width on large screens.

### Max-Width Constraints

**DO:** Use semantic max-width classes for different content types.

```django
<!-- Narrow content (forms, reading) -->
<div class="max-w-md mx-auto">
  <form>...</form>
</div>

<!-- Medium content (articles, cards) -->
<div class="max-w-2xl mx-auto">
  <article>...</article>
</div>

<!-- Wide content (dashboards, grids) -->
<div class="max-w-6xl mx-auto">
  <div class="grid grid-cols-3">...</div>
</div>

<!-- Full width (hero sections, images) -->
<div class="w-full">
  <img src="hero.jpg" class="w-full h-auto">
</div>
```

**Max-Width Reference:**

| Class | Width | Use Case |
|-------|-------|----------|
| `max-w-sm` | 24rem (384px) | Narrow modals, toasts |
| `max-w-md` | 28rem (448px) | Forms, login boxes |
| `max-w-lg` | 32rem (512px) | Simple content |
| `max-w-xl` | 36rem (576px) | Standard content |
| `max-w-2xl` | 42rem (672px) | Articles, blog posts |
| `max-w-4xl` | 56rem (896px) | Wide content |
| `max-w-6xl` | 72rem (1152px) | Dashboards |
| `max-w-7xl` | 80rem (1280px) | Full layouts |

---

## Grid Systems

### Responsive Grid Layouts

**DO:** Use mobile-first grid with responsive breakpoints.

```django
<!-- Auto-fit grid with responsive columns -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
  {% for item in items %}
    <div class="card bg-base-100 shadow-lg">
      <div class="card-body">
        <h3 class="card-title">{{ item.title }}</h3>
        <p>{{ item.description }}</p>
      </div>
    </div>
  {% endfor %}
</div>
```

**Why This Works:**
1. **Mobile-first**: Starts with 1 column on small screens
2. **Progressive enhancement**: Adds columns as screen size increases
3. **Consistent gaps**: `gap-6` applies uniform spacing between items
4. **Predictable wrapping**: Items naturally flow to next row

**DON'T:** Use fixed column counts that break on small screens.

```django
<!-- BAD - Forces 4 columns on mobile, causes horizontal scroll -->
<div class="grid grid-cols-4 gap-6">
  {% for item in items %}
    <div class="card">...</div>
  {% endfor %}
</div>
```

### Asymmetric Grid Layouts

**DO:** Use `col-span` for featured content.

```django
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
  <!-- Featured item spans 2 columns on large screens -->
  <div class="lg:col-span-2">
    <div class="card bg-base-100 shadow-xl h-full">
      <figure><img src="featured.jpg" alt="Featured"></figure>
      <div class="card-body">
        <h2 class="card-title">Featured Article</h2>
        <p>Longer description for featured content...</p>
      </div>
    </div>
  </div>
  
  <!-- Sidebar content takes 1 column -->
  <div class="lg:col-span-1">
    <div class="card bg-base-100 shadow-lg">
      <div class="card-body">
        <h3 class="card-title">Sidebar</h3>
        <p>Additional info...</p>
      </div>
    </div>
  </div>
</div>
```

### Grid Gap Spacing

```django
<!-- Tight spacing -->
<div class="grid grid-cols-3 gap-2">...</div>

<!-- Standard spacing -->
<div class="grid grid-cols-3 gap-4">...</div>

<!-- Generous spacing -->
<div class="grid grid-cols-3 gap-8">...</div>

<!-- Different horizontal/vertical gaps -->
<div class="grid grid-cols-3 gap-x-6 gap-y-12">...</div>
```

---

## Responsive Breakpoints

Tailwind uses mobile-first breakpoints. Styles apply from that breakpoint **up**.

### Breakpoint Reference

| Prefix | Min Width | Example |
|--------|-----------|---------|
| `sm:` | 640px | `sm:grid-cols-2` |
| `md:` | 768px | `md:flex-row` |
| `lg:` | 1024px | `lg:grid-cols-3` |
| `xl:` | 1280px | `xl:grid-cols-4` |
| `2xl:` | 1536px | `2xl:max-w-7xl` |

### Responsive Layout Example

**DO:** Show/hide elements based on screen size.

```django
<!-- Mobile: stacked layout, Desktop: sidebar layout -->
<div class="flex flex-col lg:flex-row gap-6">
  <!-- Main content -->
  <main class="flex-1">
    <h1 class="text-2xl lg:text-4xl font-bold">Dashboard</h1>
    <!-- Content -->
  </main>
  
  <!-- Sidebar (hidden on mobile, shown on large screens) -->
  <aside class="hidden lg:block w-64 flex-shrink-0">
    <div class="card bg-base-200">
      <div class="card-body">
        <h3 class="card-title">Filters</h3>
        <!-- Filters -->
      </div>
    </div>
  </aside>
</div>
```

**Mobile menu pattern:**

```django
<!-- Hamburger menu for mobile, full menu on desktop -->
<nav class="navbar bg-base-100">
  <!-- Mobile menu button (hidden on lg+) -->
  <div class="lg:hidden">
    <label for="menu-drawer" class="btn btn-ghost">
      <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </label>
  </div>
  
  <!-- Desktop menu (hidden on mobile) -->
  <div class="hidden lg:flex">
    <ul class="menu menu-horizontal">
      <li><a href="#">Home</a></li>
      <li><a href="#">About</a></li>
    </ul>
  </div>
</nav>
```

---

## Flexbox Layouts

### Horizontal Layouts

**DO:** Use flexbox for horizontal alignment patterns.

```django
<!-- Navbar-style layout: logo left, nav right -->
<div class="flex items-center justify-between p-4">
  <div class="text-xl font-bold">Logo</div>
  <nav class="flex gap-4">
    <a href="#" class="btn btn-ghost">Home</a>
    <a href="#" class="btn btn-ghost">About</a>
  </nav>
</div>

<!-- Button group with spacing -->
<div class="flex gap-2">
  <button class="btn btn-primary">Save</button>
  <button class="btn btn-secondary">Cancel</button>
</div>

<!-- Split layout: content left, actions right -->
<div class="flex items-center justify-between">
  <div>
    <h2 class="text-lg font-semibold">Article Title</h2>
    <p class="text-sm text-base-content/70">Published 2 days ago</p>
  </div>
  <button class="btn btn-sm btn-ghost">Edit</button>
</div>
```

### Vertical Stacking

**DO:** Use flexbox for vertical layouts with consistent spacing.

```django
<!-- Form with vertical spacing -->
<form class="flex flex-col gap-4 max-w-md">
  <div class="form-control">
    <label class="label"><span class="label-text">Email</span></label>
    <input type="email" class="input input-bordered">
  </div>
  <div class="form-control">
    <label class="label"><span class="label-text">Password</span></label>
    <input type="password" class="input input-bordered">
  </div>
  <button type="submit" class="btn btn-primary">Submit</button>
</form>
```

### Centering Content

**DO:** Use flexbox for true vertical/horizontal centering.

```django
<!-- Center content vertically and horizontally -->
<div class="flex items-center justify-center min-h-screen">
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title">Centered Card</h2>
      <p>This card is perfectly centered.</p>
    </div>
  </div>
</div>

<!-- Center text in a container -->
<div class="flex items-center justify-center h-64 bg-base-200">
  <p class="text-2xl font-bold">Centered Text</p>
</div>
```

---

## Spacing Scale

Django starter uses Tailwind's default spacing scale (1 unit = 0.25rem = 4px).

### Common Spacing Values

| Class | Value | Use Case |
|-------|-------|----------|
| `p-2` | 0.5rem (8px) | Tight padding (badges, small buttons) |
| `p-4` | 1rem (16px) | Standard padding (cards, forms) |
| `p-6` | 1.5rem (24px) | Generous padding (sections) |
| `p-8` | 2rem (32px) | Large padding (hero sections) |
| `gap-4` | 1rem (16px) | Standard grid/flex gap |
| `gap-6` | 1.5rem (24px) | Generous gap |
| `space-y-4` | 1rem (16px) | Vertical spacing between children |
| `mb-6` | 1.5rem (24px) | Bottom margin for headings |

### Consistent Section Spacing

**DO:** Use consistent vertical rhythm across pages.

```django
{% extends 'base.html' %}

{% block content %}
<!-- Top-level container -->
<div class="container mx-auto px-4 py-8">
  
  <!-- Page header -->
  <header class="mb-8">
    <h1 class="text-4xl font-bold mb-2">Page Title</h1>
    <p class="text-base-content/70">Page description</p>
  </header>
  
  <!-- Main content section -->
  <section class="mb-12">
    <h2 class="text-2xl font-semibold mb-6">Section Title</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Cards -->
    </div>
  </section>
  
  <!-- Another section -->
  <section class="mb-12">
    <h2 class="text-2xl font-semibold mb-6">Another Section</h2>
    <!-- Content -->
  </section>
  
</div>
{% endblock %}
```

**Why This Works:**
1. **py-8**: Vertical padding around entire content
2. **mb-8**: Space after page header
3. **mb-12**: Larger space between sections
4. **mb-6**: Consistent space between section title and content
5. **gap-6**: Uniform spacing in grids