# Motion Reference

## Contents
- CSS Transitions
- Hover and Focus States
- Loading States and Animations
- Micro-interactions
- Scroll Animations
- Animation Performance

---

## CSS Transitions

Tailwind provides `transition` utilities for smooth property changes.

### Basic Transitions

**DO:** Use transitions for interactive elements.

```django
<!-- Button with hover transition -->
<button class="btn btn-primary transition-colors duration-200 
               hover:bg-primary-focus active:scale-95">
  Click Me
</button>

<!-- Card with hover elevation -->
<div class="card bg-base-100 shadow-lg transition-shadow duration-300 
            hover:shadow-2xl">
  <div class="card-body">
    <h2 class="card-title">Hover for effect</h2>
  </div>
</div>

<!-- Link with underline transition -->
<a href="#" class="relative inline-block transition-colors duration-200 
              hover:text-primary after:absolute after:bottom-0 after:left-0 
              after:h-0.5 after:w-0 after:bg-primary after:transition-all 
              after:duration-300 hover:after:w-full">
  Animated Underline
</a>
```

### Transition Properties

```django
<!-- All properties (default, avoid for performance) -->
<div class="transition-all duration-300">...</div>

<!-- Specific properties (preferred) -->
<div class="transition-colors duration-200">Colors only</div>
<div class="transition-opacity duration-300">Opacity only</div>
<div class="transition-transform duration-200">Transform only</div>
<div class="transition-shadow duration-300">Shadow only</div>

<!-- Multiple properties -->
<div class="transition-[color,background-color,transform] duration-300">...</div>
```

**Why Specific Properties Matter:**
1. **Performance**: Browser only animates specified properties
2. **Predictability**: Prevents unintended animations
3. **Smoother**: Fewer properties = better frame rate

### Transition Durations

```django
<button class="transition-colors duration-75">Very fast (75ms)</button>
<button class="transition-colors duration-150">Fast (150ms)</button>
<button class="transition-colors duration-200">Standard (200ms)</button>
<button class="transition-colors duration-300">Moderate (300ms)</button>
<button class="transition-colors duration-500">Slow (500ms)</button>
```

**Recommended durations:**
- **75-150ms**: Micro-interactions (hover color changes)
- **200-300ms**: Standard transitions (cards, buttons)
- **500ms+**: Emphasis animations (modals, drawers)

---

## Hover and Focus States

### Button Interactions

**DO:** Provide clear hover and active states.

```django
<!-- Primary button with states -->
<button class="btn btn-primary 
               transition-all duration-200 
               hover:scale-105 hover:shadow-lg 
               active:scale-95 
               focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2">
  Interactive Button
</button>

<!-- Ghost button with hover fill -->
<button class="btn btn-ghost 
               transition-colors duration-200 
               hover:bg-base-200">
  Ghost Button
</button>

<!-- Icon button with rotation -->
<button class="btn btn-circle btn-ghost 
               transition-transform duration-300 
               hover:rotate-90">
  <svg>...</svg>
</button>
```

### Link Hover Effects

**DO:** Provide visual feedback on link hover.

```django
<!-- Underline on hover -->
<a href="#" class="hover:underline transition-all duration-200">Simple Link</a>

<!-- Color change -->
<a href="#" class="text-base-content/70 hover:text-primary 
              transition-colors duration-200">
  Hover to change color
</a>

<!-- Background highlight -->
<a href="#" class="px-2 py-1 rounded transition-colors duration-200 
              hover:bg-base-200">
  Highlighted Link
</a>
```

### Card Hover Effects

**DO:** Use subtle hover effects to indicate interactivity.

```django
<a href="#" class="block">
  <div class="card bg-base-100 shadow-lg 
              transition-all duration-300 
              hover:shadow-2xl hover:-translate-y-1 
              hover:border-primary border-2 border-transparent">
    <div class="card-body">
      <h3 class="card-title">Clickable Card</h3>
      <p>Hover for subtle lift effect</p>
    </div>
  </div>
</a>
```

**DON'T:** Overdo animations that distract or annoy.

```django
<!-- BAD - Too aggressive -->
<div class="card hover:scale-125 hover:rotate-12 hover:skew-x-12 
            transition-all duration-1000">
  Overly dramatic hover effect
</div>
```

---

## Loading States and Animations

### Loading Spinners

DaisyUI provides loading spinner variants.

```django
<!-- Spinner sizes -->
<span class="loading loading-spinner loading-xs"></span>
<span class="loading loading-spinner loading-sm"></span>
<span class="loading loading-spinner loading-md"></span>
<span class="loading loading-spinner loading-lg"></span>

<!-- Spinner with color -->
<span class="loading loading-spinner text-primary"></span>
<span class="loading loading-spinner text-secondary"></span>

<!-- Button with loading state -->
<button class="btn btn-primary" disabled>
  <span class="loading loading-spinner loading-sm"></span>
  Processing...
</button>
```

### Skeleton Loaders

**DO:** Use skeleton loaders for content placeholders.

```django
<!-- Card skeleton -->
<div class="card bg-base-100 shadow-lg">
  <div class="card-body">
    <div class="h-6 bg-base-300 rounded animate-pulse mb-4"></div>
    <div class="space-y-2">
      <div class="h-4 bg-base-300 rounded animate-pulse"></div>
      <div class="h-4 bg-base-300 rounded animate-pulse w-5/6"></div>
      <div class="h-4 bg-base-300 rounded animate-pulse w-4/6"></div>
    </div>
  </div>
</div>
```

### Pulse Animation

```css
/* theme/static_src/src/styles.css */
@layer utilities {
  .animate-pulse-slow {
    animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
}
```

```django
<div class="bg-primary/20 animate-pulse-slow rounded-lg p-4">
  Pulsing background
</div>
```

---

## Micro-interactions

### Input Focus Rings

**DO:** Show clear focus states for accessibility.

```django
<input type="text" class="input input-bordered 
                           focus:outline-none 
                           focus:ring-2 focus:ring-primary 
                           focus:border-transparent 
                           transition-all duration-200">
```

### Toggle Switches with Animation

```django
<input type="checkbox" class="toggle toggle-primary 
                               transition-all duration-300">
```

### Badge Entrance Animation

**DO:** Animate badges when they appear.

```django
<span class="badge badge-primary 
             animate-[fadeIn_0.3s_ease-in]">
  New
</span>
```

### Custom Keyframe Animation

```css
/* theme/static_src/src/styles.css */
@layer utilities {
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .animate-fade-in {
    animation: fadeIn 0.3s ease-in;
  }
}
```

```django
<div class="alert alert-success animate-fade-in">
  Success message with entrance animation
</div>
```

---

## Scroll Animations

### Smooth Scroll Behavior

```css
/* theme/static_src/src/styles.css */
@layer base {
  html {
    scroll-behavior: smooth;
  }
}
```

```django
<!-- Anchor link with smooth scroll -->
<a href="#section-2" class="btn btn-primary">Jump to Section</a>

<div id="section-2" class="min-h-screen pt-20">
  <h2 class="text-3xl font-bold">Section 2</h2>
</div>
```

### Scroll-Triggered Animations (Intersection Observer)

**DO:** Fade in elements as they scroll into view.

```django
<!-- Add to base.html -->
<script>
  document.addEventListener('DOMContentLoaded', () => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-in');
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);
    
    document.querySelectorAll('.scroll-reveal').forEach(el => {
      observer.observe(el);
    });
  });
</script>
```

```django
<!-- Cards that fade in on scroll -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
  {% for item in items %}
    <div class="card bg-base-100 shadow-lg scroll-reveal opacity-0">
      <div class="card-body">
        <h3 class="card-title">{{ item.title }}</h3>
      </div>
    </div>
  {% endfor %}
</div>
```

---

## Animation Performance

### WARNING: Don't Animate Expensive Properties

**The Problem:**

```django
<!-- BAD - Animates layout properties, causes reflow -->
<div class="transition-all duration-300 hover:w-96 hover:h-96 hover:p-12">
  Expensive animation
</div>
```

**Why This Breaks:**
1. **Layout thrashing**: Browser recalculates layout every frame
2. **Janky animations**: Drops below 60fps on slower devices
3. **Battery drain**: Forces GPU to work harder

**The Fix:**

```django
<!-- GOOD - Only animates transform and opacity (GPU-accelerated) -->
<div class="transition-transform duration-300 hover:scale-110">
  Smooth animation
</div>
```

### Prefer Transform Over Position

**DON'T:**

```django
<!-- BAD - Animates top/left, triggers layout -->
<div class="absolute top-0 left-0 transition-all duration-300 hover:top-10">
  Moves down slowly
</div>
```

**DO:**

```django
<!-- GOOD - Uses transform, GPU-accelerated -->
<div class="transition-transform duration-300 hover:translate-y-10">
  Moves down smoothly
</div>
```

### GPU-Accelerated Properties

**Safe to animate (no layout recalculation):**
- `transform` (translate, scale, rotate, skew)
- `opacity`
- `filter` (blur, brightness, etc.)

**Avoid animating:**
- `width`, `height`
- `padding`, `margin`
- `top`, `left`, `right`, `bottom`
- `border-width`

### Reduce Motion for Accessibility

**DO:** Respect user's motion preferences.

```css
/* theme/static_src/src/styles.css */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}