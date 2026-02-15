# DaisyUI Component Patterns

## Contents
- Authentication Forms
- Component Composition
- Responsive Layouts
- State Management
- Theme Integration
- Anti-Patterns

---

## Authentication Forms

### Registration Form Pattern

This pattern from `theme/templates/registration/register.html` combines DaisyUI form controls with Django form rendering:

```html
<div class="card bg-base-100 shadow-2xl w-full max-w-md">
    <div class="card-body">
        <h2 class="card-title text-2xl font-bold text-center justify-center mb-6">
            Create Account
        </h2>
        
        <form method="post">
            {% csrf_token %}
            
            <!-- Email field -->
            <div class="form-control">
                <label class="label">
                    <span class="label-text">Email</span>
                </label>
                {{ form.email }}
                {% if form.email.errors %}
                    <label class="label">
                        <span class="label-text-alt text-error">
                            {{ form.email.errors.0 }}
                        </span>
                    </label>
                {% endif %}
            </div>
            
            <!-- Submit button -->
            <div class="form-control mt-6">
                <button type="submit" class="btn btn-primary">
                    Register
                </button>
            </div>
        </form>
    </div>
</div>
```

**Why this works:**
- `form-control` provides consistent spacing and alignment
- `label-text-alt text-error` for validation messages aligns with DaisyUI design
- Card wrapper creates visual container with shadow

### Social Login Buttons

From `theme/templates/registration/login.html`:

```html
<div class="divider">OR</div>

<div class="space-y-3">
    <a href="{% url 'social:begin' 'google-oauth2' %}" 
       class="btn btn-outline w-full">
        <svg class="w-5 h-5 mr-2"><!-- Google icon --></svg>
        Continue with Google
    </a>
    
    <a href="{% url 'social:begin' 'linkedin-oauth2' %}" 
       class="btn btn-outline w-full">
        <svg class="w-5 h-5 mr-2"><!-- LinkedIn icon --></svg>
        Continue with LinkedIn
    </a>
</div>
```

**Pattern:**
- `btn-outline` for secondary actions
- `w-full` for full-width buttons in vertical stack
- `space-y-3` (Tailwind) for consistent vertical spacing
- `divider` component provides semantic separator

---

## Component Composition

### Nested Card with Actions

Pattern for dashboard widgets:

```html
<div class="card bg-base-200">
    <div class="card-body">
        <div class="flex items-center justify-between">
            <h2 class="card-title">Settings</h2>
            <div class="badge badge-primary">New</div>
        </div>
        
        <p>Manage your account settings and preferences.</p>
        
        <div class="card-actions justify-end mt-4">
            <button class="btn btn-ghost btn-sm">Cancel</button>
            <button class="btn btn-primary btn-sm">Save</button>
        </div>
    </div>
</div>
```

**Component breakdown:**
- `card-title` for heading (already has proper font-weight/size)
- `badge` for status indicators
- `card-actions` with `justify-end` for right-aligned buttons
- `btn-sm` for compact buttons in cards

### Dropdown Menu with Authentication

From `theme/templates/partials/_header.html`:

```html
<div class="dropdown dropdown-end">
    <label tabindex="0" class="btn btn-ghost btn-circle avatar">
        <div class="w-10 rounded-full">
            <img src="https://ui-avatars.com/api/?name={{ user.email }}" 
                 alt="User avatar">
        </div>
    </label>
    
    <ul tabindex="0" 
        class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52">
        <li><a href="{% url 'dashboard' %}">Dashboard</a></li>
        <li><a href="{% url 'user_settings' %}">Settings</a></li>
        <li><a href="{% url 'logout' %}">Logout</a></li>
    </ul>
</div>
```

**Key details:**
- `dropdown-end` aligns dropdown to right edge
- `tabindex="0"` required for keyboard accessibility
- `menu-sm` for compact menu items
- `z-[1]` ensures dropdown appears above other content

---

## Responsive Layouts

### Grid with Responsive Cards

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {% for item in items %}
    <div class="card bg-base-100 shadow-xl">
        <figure class="px-10 pt-10">
            <img src="{{ item.image }}" 
                 class="rounded-xl" 
                 alt="{{ item.title }}">
        </figure>
        <div class="card-body items-center text-center">
            <h2 class="card-title">{{ item.title }}</h2>
            <p>{{ item.description }}</p>
            <div class="card-actions">
                <button class="btn btn-primary">View</button>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
```

**Responsive strategy:**
- 1 column mobile, 2 tablet, 3 desktop
- `gap-6` provides consistent spacing at all breakpoints
- `figure` element for semantic image containers

### Hero Section

Pattern for landing pages:

```html
<div class="hero min-h-screen bg-base-200">
    <div class="hero-content flex-col lg:flex-row-reverse">
        <img src="/static/hero.png" 
             class="max-w-sm rounded-lg shadow-2xl">
        <div>
            <h1 class="text-5xl font-bold">Welcome!</h1>
            <p class="py-6">Get started with our platform today.</p>
            <a href="{% url 'register' %}" 
               class="btn btn-primary">
                Get Started
            </a>
        </div>
    </div>
</div>
```

**Layout behavior:**
- `flex-col` on mobile (stacked)
- `lg:flex-row-reverse` on desktop (side-by-side, image right)
- `hero-content` provides max-width and centering

---

## State Management

### Tab Navigation

```html
<div class="tabs tabs-boxed">
    <a class="tab {% if active_tab == 'profile' %}tab-active{% endif %}" 
       href="?tab=profile">
        Profile
    </a>
    <a class="tab {% if active_tab == 'security' %}tab-active{% endif %}" 
       href="?tab=security">
        Security
    </a>
</div>

<div class="mt-6">
    {% if active_tab == 'profile' %}
        <!-- Profile content -->
    {% elif active_tab == 'security' %}
        <!-- Security content -->
    {% endif %}
</div>
```

**Pattern:**
- `tab-active` class controlled by Django view context
- URL query params maintain state on page reload
- `tabs-boxed` provides bordered container

### Form Validation States

**GOOD - Server-side validation feedback:**

```html
<div class="form-control">
    <label class="label">
        <span class="label-text">Password</span>
    </label>
    <input type="password" 
           name="password"
           class="input input-bordered {% if form.password.errors %}input-error{% elif form.is_bound and not form.password.errors %}input-success{% endif %}"
           value="{{ form.password.value|default:'' }}">
    {% if form.password.errors %}
        <label class="label">
            <span class="label-text-alt text-error">
                {{ form.password.errors.0 }}
            </span>
        </label>
    {% endif %}
</div>
```

**Why this works:**
- `input-error` for failed validation
- `input-success` for valid inputs on re-submission
- Error messages use `label-text-alt` for smaller font
- `text-error` utility provides semantic color

---

## Theme Integration

### Dynamic Theme Switching

In `theme/templates/base.html`:

```html
<html lang="en" data-theme="light">
<head>
    <script>
        // Load theme preference before render
        const theme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', theme);
    </script>
</head>
```

Theme toggle button:

```html
<label class="swap swap-rotate">
    <input type="checkbox" 
           id="theme-toggle"
           onchange="toggleTheme()">
    
    <!-- Sun icon -->
    <svg class="swap-on fill-current w-6 h-6">...</svg>
    
    <!-- Moon icon -->
    <svg class="swap-off fill-current w-6 h-6">...</svg>
</label>

<script>
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
}

// Initialize toggle state
const toggle = document.getElementById('theme-toggle');
toggle.checked = localStorage.getItem('theme') === 'dark';
</script>
```

**Implementation notes:**
- Load theme in `<head>` to prevent flash of wrong theme
- `swap` component animates icon transition
- `localStorage` persists preference

---

## Anti-Patterns

### WARNING: Overriding Component Styles

**The Problem:**

```html
<!-- BAD - Fighting DaisyUI defaults -->
<button class="btn btn-primary" 
        style="background: #ff0000 !important; border-radius: 0;">
    Submit
</button>
```

**Why This Breaks:**
1. **Theme consistency destroyed** - Overrides break when user switches themes
2. **Maintenance nightmare** - Inline styles scattered across templates
3. **Specificity wars** - `!important` required everywhere, CSS becomes unmaintainable

**The Fix:**

```html
<!-- GOOD - Extend via Tailwind utilities -->
<button class="btn btn-primary rounded-none">
    Submit
</button>
```

Or create custom component class in `theme/static_src/src/styles.css`:

```css
@layer components {
  .btn-custom {
    @apply btn btn-primary;
    background: var(--custom-color);
    border-radius: 0;
  }
}
```

**When You Might Be Tempted:**
When client demands specific colors/sizes that don't match DaisyUI defaults. Instead, customize DaisyUI theme variables (see **tailwind** skill).

### WARNING: Using div Instead of Semantic HTML

**The Problem:**

```html
<!-- BAD - Non-semantic markup -->
<div class="btn" onclick="submitForm()">
    Submit
</div>
```

**Why This Breaks:**
1. **Accessibility failure** - Screen readers don't recognize as button
2. **Keyboard navigation broken** - Can't tab to or activate with Enter/Space
3. **Form submission fails** - `div` doesn't trigger submit events

**The Fix:**

```html
<!-- GOOD - Semantic HTML with DaisyUI classes -->
<button type="submit" class="btn btn-primary">
    Submit
</button>
```

### WARNING: Missing form-control Wrapper

**The Problem:**

```html
<!-- BAD - No wrapper, inconsistent spacing -->
<label>Email</label>
<input type="email" class="input input-bordered">
<span class="text-error">{{ error }}</span>
```

**Why This Breaks:**
1. **Inconsistent spacing** - Manual margins required everywhere
2. **Label not connected** - Screen readers can't associate label with input
3. **Alignment issues** - Error messages don't align with input

**The Fix:**

```html
<!-- GOOD - Proper form-control structure -->
<div class="form-control">
    <label class="label">
        <span class="label-text">Email</span>
    </label>
    <input type="email" class="input input-bordered">
    <label class="label">
        <span class="label-text-alt text-error">{{ error }}</span>
    </label>
</div>