# Components Reference

## Contents
- DaisyUI Component Patterns
- Form Components
- Navigation Components
- Feedback Components
- Data Display Components
- Custom Component Styling

---

## DaisyUI Component Patterns

DaisyUI provides pre-styled components that work out of the box with minimal markup.

### Button Variants

**DO:** Use semantic button classes for different actions.

```django
<!-- Primary action -->
<button class="btn btn-primary">Sign Up</button>

<!-- Secondary/cancel action -->
<button class="btn btn-secondary">Cancel</button>

<!-- Destructive action -->
<button class="btn btn-error">Delete Account</button>

<!-- Ghost/subtle action -->
<button class="btn btn-ghost">Skip</button>

<!-- Link-style button -->
<button class="btn btn-link">Learn More</button>

<!-- Loading state -->
<button class="btn btn-primary loading">Processing...</button>

<!-- Disabled state -->
<button class="btn btn-primary" disabled>Unavailable</button>
```

**Button Sizes:**

```django
<button class="btn btn-xs">Extra Small</button>
<button class="btn btn-sm">Small</button>
<button class="btn btn-md">Medium (default)</button>
<button class="btn btn-lg">Large</button>
```

**DON'T:** Mix custom button styles with DaisyUI classes.

```django
<!-- BAD - Inconsistent with design system -->
<button class="btn btn-primary bg-red-500 px-8">
  Mixed styles that override each other
</button>
```

---

## Form Components

### Form Control Structure

**DO:** Use DaisyUI form-control wrapper for consistent spacing.

```django
<form method="post" class="space-y-4 max-w-md">
  {% csrf_token %}
  
  <!-- Text input -->
  <div class="form-control">
    <label class="label">
      <span class="label-text">Email address</span>
    </label>
    <input type="email" name="email" placeholder="you@example.com" 
           class="input input-bordered" required>
    <label class="label">
      <span class="label-text-alt text-error">{{ form.email.errors.0 }}</span>
    </label>
  </div>
  
  <!-- Password input -->
  <div class="form-control">
    <label class="label">
      <span class="label-text">Password</span>
      <span class="label-text-alt">
        <a href="{% url 'password_reset' %}" class="link link-hover">Forgot?</a>
      </span>
    </label>
    <input type="password" name="password" class="input input-bordered" required>
  </div>
  
  <!-- Checkbox -->
  <div class="form-control">
    <label class="label cursor-pointer justify-start gap-4">
      <input type="checkbox" name="remember" class="checkbox">
      <span class="label-text">Remember me</span>
    </label>
  </div>
  
  <button type="submit" class="btn btn-primary w-full">Sign In</button>
</form>
```

### Input States

```django
<!-- Normal -->
<input type="text" class="input input-bordered">

<!-- Focused (automatic) -->
<input type="text" class="input input-bordered" autofocus>

<!-- Error state -->
<input type="text" class="input input-bordered input-error" 
       aria-invalid="true" aria-describedby="error-msg">
<span id="error-msg" class="text-error text-sm">Invalid email format</span>

<!-- Success state -->
<input type="text" class="input input-bordered input-success">

<!-- Disabled -->
<input type="text" class="input input-bordered" disabled>
```

### Select and Textarea

```django
<!-- Select dropdown -->
<select class="select select-bordered w-full">
  <option disabled selected>Choose an option</option>
  <option>Option 1</option>
  <option>Option 2</option>
</select>

<!-- Textarea -->
<textarea class="textarea textarea-bordered h-24" 
          placeholder="Enter your message..."></textarea>
```

---

## Navigation Components

### Navbar Pattern

**DO:** Use DaisyUI navbar with responsive menu.

```django
<!-- theme/templates/partials/_header.html -->
<div class="navbar bg-base-100 shadow-lg">
  <div class="navbar-start">
    <div class="dropdown">
      <!-- Mobile menu button -->
      <label tabindex="0" class="btn btn-ghost lg:hidden">
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </label>
      <!-- Mobile menu -->
      <ul tabindex="0" class="menu menu-compact dropdown-content mt-3 p-2 
                               shadow bg-base-100 rounded-box w-52">
        <li><a href="{% url 'dashboard' %}">Dashboard</a></li>
        <li><a href="{% url 'user_settings' %}">Settings</a></li>
      </ul>
    </div>
    <a href="{% url 'home' %}" class="btn btn-ghost normal-case text-xl">YourApp</a>
  </div>
  
  <div class="navbar-center hidden lg:flex">
    <ul class="menu menu-horizontal px-1">
      <li><a href="{% url 'dashboard' %}">Dashboard</a></li>
      <li><a href="{% url 'user_settings' %}">Settings</a></li>
    </ul>
  </div>
  
  <div class="navbar-end">
    {% if user.is_authenticated %}
      <div class="dropdown dropdown-end">
        <label tabindex="0" class="btn btn-ghost btn-circle avatar">
          <div class="w-10 rounded-full bg-primary text-primary-content 
                      flex items-center justify-center">
            {{ user.first_name.0|upper }}
          </div>
        </label>
        <ul tabindex="0" class="menu menu-compact dropdown-content mt-3 p-2 
                                 shadow bg-base-100 rounded-box w-52">
          <li><a href="{% url 'logout' %}">Logout</a></li>
        </ul>
      </div>
    {% else %}
      <a href="{% url 'login' %}" class="btn btn-ghost">Login</a>
      <a href="{% url 'register' %}" class="btn btn-primary">Sign Up</a>
    {% endif %}
  </div>
</div>
```

### Breadcrumbs

```django
<div class="text-sm breadcrumbs">
  <ul>
    <li><a href="{% url 'home' %}">Home</a></li>
    <li><a href="{% url 'dashboard' %}">Dashboard</a></li>
    <li>Settings</li>
  </ul>
</div>
```

---

## Feedback Components

### Alert Messages

**DO:** Use semantic alert types with proper icons.

```django
<!-- Success alert -->
<div class="alert alert-success shadow-lg">
  <div>
    <svg class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <span>Account created successfully!</span>
  </div>
</div>

<!-- Error alert -->
<div class="alert alert-error shadow-lg">
  <div>
    <svg class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <span>Authentication failed. Please try again.</span>
  </div>
</div>

<!-- Warning alert -->
<div class="alert alert-warning shadow-lg">
  <div>
    <svg class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
    <span>Your trial expires in 3 days.</span>
  </div>
</div>
```

### Modal Dialogs

```django
<!-- Modal trigger -->
<label for="delete-modal" class="btn btn-error">Delete</label>

<!-- Modal -->
<input type="checkbox" id="delete-modal" class="modal-toggle" />
<div class="modal">
  <div class="modal-box">
    <h3 class="font-bold text-lg">Confirm Deletion</h3>
    <p class="py-4">Are you sure you want to delete this item? This action cannot be undone.</p>
    <div class="modal-action">
      <label for="delete-modal" class="btn btn-ghost">Cancel</label>
      <button class="btn btn-error">Delete</button>
    </div>
  </div>
</div>
```

### Loading Spinner

```django
<!-- Inline spinner -->
<span class="loading loading-spinner loading-sm"></span>

<!-- Button with loading -->
<button class="btn btn-primary loading">Processing</button>

<!-- Full page loading state -->
<div class="flex items-center justify-center min-h-screen">
  <span class="loading loading-spinner loading-lg"></span>
</div>
```

---

## Data Display Components

### Card Component

**DO:** Use card for grouped content with consistent spacing.

```django
<div class="card bg-base-100 shadow-xl">
  <figure>
    <img src="/images/example.jpg" alt="Example" class="w-full h-48 object-cover">
  </figure>
  <div class="card-body">
    <h2 class="card-title">Card Title</h2>
    <p>Card description text goes here.</p>
    <div class="card-actions justify-end">
      <button class="btn btn-primary">Action</button>
    </div>
  </div>
</div>
```

### Badge Component

```django
<span class="badge">Default</span>
<span class="badge badge-primary">Primary</span>
<span class="badge badge-secondary">Secondary</span>
<span class="badge badge-accent">Accent</span>
<span class="badge badge-ghost">Ghost</span>

<!-- Outline badges -->
<span class="badge badge-outline">Outline</span>
<span class="badge badge-outline badge-primary">Primary Outline</span>
```

### Stats Display

```django
<div class="stats shadow">
  <div class="stat">
    <div class="stat-title">Total Users</div>
    <div class="stat-value">31K</div>
    <div class="stat-desc">↗︎ 400 (22%)</div>
  </div>
  
  <div class="stat">
    <div class="stat-title">Active Now</div>
    <div class="stat-value text-secondary">4,200</div>
    <div class="stat-desc text-secondary">↗︎ 40 (2%)</div>
  </div>
</div>