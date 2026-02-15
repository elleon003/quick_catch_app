# Patterns Reference

## Contents
- DO/DON'T Visual Design Patterns
- Anti-Patterns: Generic AI Aesthetics
- Django Template Design Patterns
- Responsive Design Patterns
- Accessibility Patterns

---

## DO/DON'T Visual Design Patterns

### Spacing and Visual Rhythm

**DO:** Use consistent spacing scale for visual hierarchy.

```django
<!-- GOOD - Clear hierarchy with consistent spacing -->
<section class="py-16">
  <div class="container mx-auto px-4">
    <h2 class="text-3xl font-bold mb-8">Section Title</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Cards with consistent internal spacing -->
      <div class="card bg-base-100 shadow-lg">
        <div class="card-body">
          <h3 class="card-title mb-4">Card Title</h3>
          <p class="mb-4">Description text with breathing room.</p>
          <button class="btn btn-primary">Action</button>
        </div>
      </div>
    </div>
  </div>
</section>
```

**DON'T:** Use random spacing that breaks visual rhythm.

```django
<!-- BAD - Inconsistent spacing creates visual chaos -->
<section class="py-3">
  <div class="px-2">
    <h2 class="text-3xl font-bold mb-2">Title</h2>
    <div class="grid grid-cols-3 gap-1">
      <div class="p-8">
        <h3 class="mb-1">Card</h3>
        <p class="mb-6">Text</p>
      </div>
    </div>
  </div>
</section>
```

**Why This Breaks:**
1. Uneven spacing disorients users
2. No clear visual grouping
3. Looks unprofessional and rushed
4. Hard to scan and read

---

### Color Contrast and Readability

**DO:** Ensure sufficient contrast for text readability.

```django
<!-- GOOD - High contrast, readable text -->
<div class="bg-base-100 text-base-content p-6">
  <p class="text-base leading-relaxed">
    This text has sufficient contrast and comfortable line-height for easy reading.
  </p>
</div>

<!-- GOOD - Semantic colors with proper contrast -->
<div class="alert alert-error">
  <span class="text-error-content">Error message is clearly readable</span>
</div>
```

**DON'T:** Use low-contrast color combinations.

```django
<!-- BAD - Poor contrast, hard to read -->
<div class="bg-gray-200 text-gray-300 p-6">
  <p>This text is nearly invisible</p>
</div>

<!-- BAD - Colored text on colored background -->
<div class="bg-purple-500 text-pink-400">
  <p>Hurts to read</p>
</div>
```

**Why This Breaks:**
1. Fails WCAG accessibility standards (minimum 4.5:1 contrast ratio)
2. Unreadable for users with visual impairments
3. Difficult to read in bright sunlight
4. Looks unprofessional

---

### Button Hierarchy

**DO:** Use visual weight to indicate button importance.

```django
<!-- GOOD - Clear primary/secondary/tertiary hierarchy -->
<div class="flex gap-2">
  <button class="btn btn-primary">Save Changes</button>
  <button class="btn btn-secondary">Preview</button>
  <button class="btn btn-ghost">Cancel</button>
</div>
```

**DON'T:** Make all buttons equally prominent.

```django
<!-- BAD - No hierarchy, user doesn't know primary action -->
<div class="flex gap-2">
  <button class="btn btn-primary">Save</button>
  <button class="btn btn-primary">Preview</button>
  <button class="btn btn-primary">Cancel</button>
  <button class="btn btn-primary">Help</button>
</div>
```

**Why This Breaks:**
1. User can't identify the primary action
2. Increases cognitive load
3. Higher chance of accidental destructive actions
4. Poor UX for keyboard navigation

---

## Anti-Patterns: Generic AI Aesthetics

### WARNING: Overused Gradient Backgrounds

**The Problem:**

```django
<!-- BAD - Generic purple/blue gradient, seen everywhere -->
<section class="bg-gradient-to-r from-purple-500 via-pink-500 to-blue-500 py-20">
  <h1 class="text-white text-5xl font-bold text-center">
    Welcome to Our Platform
  </h1>
</section>
```

**Why This Breaks:**
1. Cliché aesthetic associated with generic SaaS products
2. Often poor text contrast (especially with white text)
3. Looks dated and uninspired
4. Doesn't differentiate your product

**The Fix:**

```django
<!-- GOOD - Subtle, brand-appropriate background -->
<section class="bg-base-100 py-20">
  <div class="container mx-auto px-4">
    <h1 class="text-4xl font-bold text-base-content mb-4">
      Welcome to Our Platform
    </h1>
    <div class="w-20 h-1 bg-primary"></div>
  </div>
</section>
```

---

### WARNING: Excessive Drop Shadows

**The Problem:**

```django
<!-- BAD - Overly dramatic shadows on everything -->
<div class="card shadow-2xl hover:shadow-[0_35px_60px_-15px_rgba(0,0,0,0.5)]">
  <img src="image.jpg" class="shadow-2xl">
  <div class="card-body shadow-2xl">
    <h3 class="shadow-lg">Title</h3>
    <p class="shadow-md">Text</p>
  </div>
</div>
```

**Why This Breaks:**
1. Creates visual clutter and hierarchy confusion
2. Looks amateurish and heavy
3. Performance impact from excessive shadows
4. Shadows should indicate elevation, not decorate

**The Fix:**

```django
<!-- GOOD - Minimal, purposeful shadows -->
<div class="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow duration-300">
  <figure>
    <img src="image.jpg" alt="Description">
  </figure>
  <div class="card-body">
    <h3 class="card-title">Title</h3>
    <p>Text content</p>
  </div>
</div>
```

**When You Might Be Tempted:**
- Trying to make elements "pop" without clear hierarchy
- Copying popular SaaS landing pages
- Compensating for weak content or layout

---

### WARNING: Over-Rounded Corners

**The Problem:**

```django
<!-- BAD - Excessive border radius everywhere -->
<div class="rounded-[50px] p-8 bg-base-200">
  <img src="avatar.jpg" class="rounded-[99px] w-20 h-20">
  <button class="btn rounded-[40px]">Click</button>
  <input type="text" class="input rounded-[30px]">
</div>
```

**Why This Breaks:**
1. Inconsistent with DaisyUI's design language
2. Makes UI elements look childish or toy-like
3. Reduces usable space in corners
4. Arbitrary values break design system

**The Fix:**

```django
<!-- GOOD - Consistent border radius from design system -->
<div class="card bg-base-200">
  <div class="card-body">
    <div class="avatar">
      <div class="w-20 rounded-full">
        <img src="avatar.jpg" alt="Avatar">
      </div>
    </div>
    <button class="btn btn-primary">Click</button>
    <input type="text" class="input input-bordered">
  </div>
</div>
```

---

## Django Template Design Patterns

### Template Inheritance for Consistency

**DO:** Use template inheritance to maintain consistent layouts.

```django
<!-- theme/templates/base.html -->
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Django Starter{% endblock %}</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'css/dist/styles.css' %}">
  {% block extra_css %}{% endblock %}
</head>
<body class="bg-base-100 text-base-content">
  {% include 'partials/_header.html' %}
  
  <main class="min-h-screen">
    {% block content %}{% endblock %}
  </main>
  
  {% include 'partials/_footer.html' %}
  
  {% block extra_js %}{% endblock %}
</body>
</html>
```

```django
<!-- theme/templates/dashboard.html -->
{% extends 'base.html' %}

{% block title %}Dashboard - Django Starter{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
  <h1 class="text-3xl font-bold mb-6">Dashboard</h1>
  <!-- Dashboard content -->
</div>
{% endblock %}
```

---

### Reusable Partials for Components

**DO:** Extract repeated UI components into partials.

```django
<!-- theme/templates/partials/_card.html -->
<div class="card bg-base-100 shadow-lg">
  <div class="card-body">
    <h3 class="card-title">{{ title }}</h3>
    <p>{{ description }}</p>
    {% if link_url %}
      <div class="card-actions justify-end">
        <a href="{{ link_url }}" class="btn btn-primary">{{ link_text|default:"View" }}</a>
      </div>
    {% endif %}
  </div>
</div>
```

**Usage:**

```django
{% include 'partials/_card.html' with title="Feature 1" description="Description text" link_url="/feature-1" %}
```

---

## Responsive Design Patterns

### Mobile-First Form Layouts

**DO:** Stack form elements on mobile, optimize for larger screens.

```django
<form method="post" class="max-w-4xl mx-auto p-4">
  {% csrf_token %}
  
  <!-- Single column on mobile, two columns on desktop -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div class="form-control">
      <label class="label"><span class="label-text">First Name</span></label>
      <input type="text" name="first_name" class="input input-bordered">
    </div>
    
    <div class="form-control">
      <label class="label"><span class="label-text">Last Name</span></label>
      <input type="text" name="last_name" class="input input-bordered">
    </div>
  </div>
  
  <!-- Full width on all screens -->
  <div class="form-control mt-4">
    <label class="label"><span class="label-text">Email</span></label>
    <input type="email" name="email" class="input input-bordered">
  </div>
  
  <button type="submit" class="btn btn-primary w-full md:w-auto mt-6">
    Submit
  </button>
</form>
```

---

### Responsive Image Handling

**DO:** Serve appropriately sized images with proper aspect ratios.

```django
<!-- Responsive image with aspect ratio constraint -->
<figure class="aspect-video w-full overflow-hidden rounded-lg">
  <img src="{{ image_url }}" alt="{{ image_alt }}" 
       class="w-full h-full object-cover">
</figure>

<!-- Responsive avatar -->
<div class="avatar">
  <div class="w-12 h-12 md:w-16 md:h-16 lg:w-20 lg:h-20 rounded-full">
    <img src="{{ user.avatar_url }}" alt="{{ user.name }}">
  </div>
</div>
```

---

## Accessibility Patterns

### Semantic HTML Structure

**DO:** Use proper semantic HTML elements.

```django
<!-- GOOD - Semantic structure -->
<article class="card bg-base-100 shadow-lg">
  <header class="card-body border-b border-base-300">
    <h2 class="card-title">Article Title</h2>
    <time datetime="2026-02-03">February 3, 2026</time>
  </header>
  <div class="card-body">
    <p>Article content...</p>
  </div>
  <footer class="card-body border-t border-base-300">
    <button class="btn btn-primary">Read More</button>
  </footer>
</article>
```

**DON'T:** Use divs for everything.

```django
<!-- BAD - No semantic meaning -->
<div class="card">
  <div class="card-body">
    <div class="text-xl font-bold">Title</div>
    <div>Content</div>
    <div><div class="btn">Read More</div></div>
  </div>
</div>
```

---

### Keyboard Navigation

**DO:** Ensure all interactive elements are keyboard accessible.

```django
<!-- GOOD - Proper focus states and tab order -->
<nav class="navbar bg-base-100">
  <a href="/" class="btn btn-ghost focus:outline-none focus:ring-2 focus:ring-primary">
    Home
  </a>
  <a href="/about" class="btn btn-ghost focus:outline-none focus:ring-2 focus:ring-primary">
    About
  </a>
</nav>

<!-- GOOD - Modal with focus trap -->
<div class="modal" role="dialog" aria-labelledby="modal-title" aria-modal="true">
  <div class="modal-box">
    <h3 id="modal-title" class="font-bold text-lg">Confirm Action</h3>
    <p class="py-4">Are you sure?</p>
    <div class="modal-action">
      <button class="btn btn-ghost" autofocus>Cancel</button>
      <button class="btn btn-error">Confirm</button>
    </div>
  </div>
</div>
```

---

### ARIA Labels for Screen Readers

**DO:** Provide context for non-text elements.

```django
<!-- Icon button with label -->
<button class="btn btn-circle btn-ghost" aria-label="Close menu">
  <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" 
       aria-hidden="true">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M6 18L18 6M6 6l12 12" />
  </svg>
</button>

<!-- Loading state announcement -->
<button class="btn btn-primary" aria-busy="true" aria-live="polite">
  <span class="loading loading-spinner loading-sm"></span>
  <span class="sr-only">Processing your request</span>
  Processing...
</button>