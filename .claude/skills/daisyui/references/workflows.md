# DaisyUI Workflows

## Contents
- New Component Integration
- Theme Customization
- Form Building
- Responsive Layout Development
- Component Testing
- Production Build

---

## New Component Integration

### Adding a DaisyUI Component to Existing Template

**Workflow:**

1. **Browse DaisyUI documentation** to find component:
   ```bash
   # Visit https://daisyui.com/components/
   # Example: Adding a "stat" component for dashboard metrics
   ```

2. **Create template or edit existing**:
   ```bash
   # Edit dashboard template
   vim theme/templates/dashboard.html
   ```

3. **Integrate component with Django context**:
   ```html
   <div class="stats shadow">
       <div class="stat">
           <div class="stat-title">Total Users</div>
           <div class="stat-value">{{ user_count }}</div>
           <div class="stat-desc">{{ new_users_today }} new today</div>
       </div>
       
       <div class="stat">
           <div class="stat-title">Active Sessions</div>
           <div class="stat-value">{{ active_sessions }}</div>
           <div class="stat-desc">↗︎ {{ session_growth }}% growth</div>
       </div>
   </div>
   ```

4. **Update view to provide context data** (`users/views.py`):
   ```python
   from django.contrib.auth.decorators import login_required
   from django.shortcuts import render
   from users.models import CustomUser
   
   @login_required
   def dashboard_view(request):
       context = {
           'user_count': CustomUser.objects.count(),
           'new_users_today': CustomUser.objects.filter(
               date_joined__date=timezone.now().date()
           ).count(),
           'active_sessions': Session.objects.filter(
               expire_date__gte=timezone.now()
           ).count(),
       }
       return render(request, 'dashboard.html', context)
   ```

5. **Test rendering**:
   ```bash
   python manage.py runserver
   # Visit http://127.0.0.1:8000/users/dashboard/
   ```

6. **Validate responsive behavior**:
   - Resize browser window
   - Check mobile breakpoint (< 768px)
   - Verify stats stack vertically on small screens

**Common Issues:**

- **Component looks unstyled**: Ensure Tailwind dev server is running (`python manage.py tailwind start`)
- **Django context not rendering**: Check view returns correct context dictionary
- **Layout breaks on mobile**: Wrap stats in `<div class="stats stats-vertical lg:stats-horizontal">`

---

## Theme Customization

### Creating Custom Color Scheme

**Workflow:**

1. **Identify required theme variables**:
   ```bash
   # DaisyUI v5 theme variables:
   # - primary, secondary, accent
   # - neutral, base-100, base-200, base-300
   # - info, success, warning, error
   ```

2. **Edit Tailwind CSS config** in `theme/static_src/src/styles.css`:
   ```css
   @import "tailwindcss";
   
   @plugin "daisyui";
   
   @theme {
     --color-primary: oklch(0.65 0.25 250);
     --color-primary-content: oklch(1 0 0);
     --color-secondary: oklch(0.55 0.20 200);
     --color-accent: oklch(0.75 0.15 150);
     --color-neutral: oklch(0.30 0.02 250);
     --color-base-100: oklch(1 0 0);
   }
   
   @layer base {
     :root {
       /* Additional custom properties */
       --custom-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
     }
   }
   ```

3. **Rebuild CSS**:
   ```bash
   # If dev server running, it auto-rebuilds
   # Otherwise:
   python manage.py tailwind build
   ```

4. **Test theme in browser**:
   - Check buttons, cards, inputs with new colors
   - Verify contrast ratios (use browser DevTools)
   - Test light/dark mode switching if implemented

5. **Validate accessibility**:
   ```bash
   # Use browser extension like axe DevTools
   # Check WCAG AA contrast ratios (4.5:1 for text)
   ```

**Checklist for custom themes:**

Copy this checklist and track progress:
- [ ] Define all required color variables (primary, secondary, accent, neutral, base colors)
- [ ] Test contrast ratios for text on backgrounds
- [ ] Verify hover/focus states are visible
- [ ] Check form validation colors (error, success)
- [ ] Test in both light and dark mode if supported
- [ ] Validate with accessibility tools

---

## Form Building

### Creating Multi-Step Registration Form

**Workflow:**

1. **Plan form structure**:
   ```
   Step 1: Email + Password
   Step 2: Profile information
   Step 3: Preferences
   ```

2. **Create Django form class** (`users/forms.py`):
   ```python
   from django import forms
   from users.models import CustomUser
   
   class RegistrationStep1Form(forms.Form):
       email = forms.EmailField(
           widget=forms.EmailInput(attrs={
               'class': 'input input-bordered w-full',
               'placeholder': 'you@example.com'
           })
       )
       password = forms.CharField(
           widget=forms.PasswordInput(attrs={
               'class': 'input input-bordered w-full'
           })
       )
       
       def clean_email(self):
           email = self.cleaned_data['email']
           if CustomUser.objects.filter(email=email).exists():
               raise forms.ValidationError('Email already registered')
           return email
   ```

3. **Create template** (`theme/templates/registration/register_step1.html`):
   ```html
   {% extends 'base.html' %}
   
   {% block content %}
   <div class="flex justify-center items-center min-h-screen">
       <div class="card bg-base-100 shadow-2xl w-full max-w-md">
           <div class="card-body">
               <ul class="steps w-full mb-6">
                   <li class="step step-primary">Account</li>
                   <li class="step">Profile</li>
                   <li class="step">Preferences</li>
               </ul>
               
               <h2 class="card-title justify-center text-2xl mb-6">
                   Create Account
               </h2>
               
               <form method="post">
                   {% csrf_token %}
                   
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
                   
                   <div class="form-control mt-4">
                       <label class="label">
                           <span class="label-text">Password</span>
                       </label>
                       {{ form.password }}
                       {% if form.password.errors %}
                           <label class="label">
                               <span class="label-text-alt text-error">
                                   {{ form.password.errors.0 }}
                               </span>
                           </label>
                       {% endif %}
                   </div>
                   
                   <div class="form-control mt-6">
                       <button type="submit" class="btn btn-primary">
                           Continue
                       </button>
                   </div>
               </form>
           </div>
       </div>
   </div>
   {% endblock %}
   ```

4. **Create view with session state** (`users/views.py`):
   ```python
   from django.shortcuts import render, redirect
   from django.views.decorators.http import require_http_methods
   
   @require_http_methods(["GET", "POST"])
   def register_step1_view(request):
       if request.method == 'POST':
           form = RegistrationStep1Form(request.POST)
           if form.is_valid():
               # Store in session
               request.session['registration_email'] = form.cleaned_data['email']
               request.session['registration_password'] = form.cleaned_data['password']
               return redirect('register_step2')
       else:
           form = RegistrationStep1Form()
       
       return render(request, 'registration/register_step1.html', {
           'form': form,
       })
   ```

5. **Test form validation**:
   ```bash
   python manage.py runserver
   # Navigate to registration
   # Test cases:
   # - Submit empty form (should show validation errors)
   # - Submit invalid email (should reject)
   # - Submit existing email (should show "already registered")
   # - Submit valid data (should proceed to step 2)
   ```

6. **Iterate until validation passes**:
   - If errors appear, fix in form class or template
   - Retest all validation scenarios
   - Only proceed when all cases work correctly

**Form Building Checklist:**

Copy this checklist and track progress:
- [ ] Create Django form class with validation
- [ ] Add DaisyUI classes to form widgets
- [ ] Build template with form-control wrappers
- [ ] Implement error message display
- [ ] Add CSRF token to form
- [ ] Create view with GET/POST handling
- [ ] Test empty submission (validation errors)
- [ ] Test invalid data (field-specific errors)
- [ ] Test valid submission (success flow)
- [ ] Verify responsive layout on mobile

---

## Responsive Layout Development

### Building Responsive Dashboard Grid

**Workflow:**

1. **Design mobile-first layout**:
   ```html
   <!-- Start with single column (mobile) -->
   <div class="grid grid-cols-1 gap-4 p-4">
       <div class="card bg-base-100 shadow-xl">...</div>
       <div class="card bg-base-100 shadow-xl">...</div>
       <div class="card bg-base-100 shadow-xl">...</div>
   </div>
   ```

2. **Add tablet breakpoint** (md: 768px+):
   ```html
   <div class="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
       <!-- Now 2 columns on tablets -->
   </div>
   ```

3. **Add desktop breakpoint** (lg: 1024px+):
   ```html
   <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
       <!-- 3 columns on desktop -->
   </div>
   ```

4. **Test at each breakpoint**:
   ```bash
   # Use browser DevTools responsive mode
   # Test widths: 375px (mobile), 768px (tablet), 1024px (desktop)
   ```

5. **Adjust card content responsiveness**:
   ```html
   <div class="card bg-base-100 shadow-xl">
       <div class="card-body">
           <!-- Stack title and action on mobile, inline on desktop -->
           <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between">
               <h2 class="card-title">Statistics</h2>
               <button class="btn btn-sm btn-primary mt-2 lg:mt-0">
                   View Details
               </button>
           </div>
       </div>
   </div>
   ```

6. **Validate accessibility at all sizes**:
   - Touch targets ≥ 44px on mobile
   - Text remains readable (min 16px body text)
   - Interactive elements not too close together

**Responsive Testing Checklist:**

Copy this checklist and track progress:
- [ ] Test at 375px width (mobile)
- [ ] Test at 768px width (tablet)
- [ ] Test at 1024px width (desktop)
- [ ] Verify grid columns collapse correctly
- [ ] Check button sizes are touch-friendly (mobile)
- [ ] Ensure text doesn't overflow containers
- [ ] Test landscape orientation on mobile
- [ ] Validate with real device if possible

---

## Component Testing

### Testing Modal Component Integration

**Workflow:**

1. **Create modal template**:
   ```html
   <!-- theme/templates/partials/_confirm_modal.html -->
   <dialog id="confirm_delete_modal" class="modal">
       <div class="modal-box">
           <h3 class="font-bold text-lg">Confirm Deletion</h3>
           <p class="py-4">Are you sure you want to delete this item?</p>
           <div class="modal-action">
               <form method="dialog">
                   <button class="btn">Cancel</button>
               </form>
               <button class="btn btn-error" 
                       onclick="handleDelete()">
                   Delete
               </button>
           </div>
       </div>
   </dialog>
   ```

2. **Add modal trigger**:
   ```html
   <button class="btn btn-error" 
           onclick="confirm_delete_modal.showModal()">
       Delete Item
   </button>
   ```

3. **Test modal functionality**:
   ```
   Test cases:
   1. Click trigger button → Modal opens
   2. Click Cancel → Modal closes
   3. Click Delete → handleDelete() called, modal closes
   4. Click outside modal → Modal closes (default behavior)
   5. Press Escape key → Modal closes
   ```

4. **Test with keyboard navigation**:
   ```
   1. Tab to trigger button
   2. Press Enter → Modal opens
   3. Tab through modal elements
   4. Press Escape → Modal closes
   ```

5. **Validate ARIA attributes** (DaisyUI adds these automatically):
   ```html
   <!-- Verify in browser DevTools: -->
   <dialog role="dialog" aria-modal="true">
   ```

6. **Iterate until all tests pass**:
   - If modal doesn't open, check JavaScript console for errors
   - If backdrop click doesn't close, verify `<form method="dialog">` wrapper
   - If keyboard nav fails, check tabindex and focus states

**Component Testing Checklist:**

Copy this checklist and track progress:
- [ ] Modal opens on trigger click
- [ ] Modal closes on Cancel button
- [ ] Modal closes on outside click
- [ ] Modal closes on Escape key
- [ ] Keyboard navigation works (Tab key)
- [ ] Enter key activates buttons
- [ ] Screen reader announces modal (test with NVDA/JAWS)
- [ ] Focus returns to trigger after close

---

## Production Build

### Optimizing DaisyUI for Production

**Workflow:**

1. **Build production CSS**:
   ```bash
   python manage.py tailwind build
   ```

2. **Verify purged CSS size**:
   ```bash
   # Check compiled CSS size
   ls -lh theme/static/css/dist/styles.css
   # Should be < 50KB after purging unused classes
   ```

3. **Collect static files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Test production build locally**:
   ```bash
   export DJANGO_ENV=production
   export DEBUG=False
   python manage.py runserver
   ```

5. **Validate styling in production mode**:
   - Check all pages render correctly
   - Verify DaisyUI components still styled
   - Confirm no missing CSS classes

6. **Check Lighthouse performance**:
   ```bash
   # Use Chrome DevTools Lighthouse
   # Target scores:
   # - Performance: > 90
   # - Accessibility: 100
   # - Best Practices: 100
   ```

7. **Deploy to production**:
   ```bash
   # See django skill for deployment steps
   # Ensure CSS build runs before deployment
   ```

**Production Build Checklist:**

Copy this checklist and track progress:
- [ ] Run `tailwind build` for production CSS
- [ ] Verify CSS file size (should be minified)
- [ ] Run `collectstatic` to gather all static files
- [ ] Test site with DEBUG=False locally
- [ ] Check all pages render correctly
- [ ] Verify no console errors in browser
- [ ] Run Lighthouse audit (Performance > 90)
- [ ] Test on real mobile device
- [ ] Validate accessibility (axe DevTools)
- [ ] Deploy to production environment

---

## Adding Custom DaisyUI Component

### Creating Reusable Alert Component

**Workflow:**

1. **Create partial template** (`theme/templates/partials/_alert.html`):
   ```html
   {# Usage: {% include 'partials/_alert.html' with type='error' message='Error text' dismissible=True %} #}
   
   <div class="alert alert-{{ type|default:'info' }} {% if dismissible %}pr-12{% endif %}">
       <svg xmlns="http://www.w3.org/2000/svg" 
            class="stroke-current shrink-0 h-6 w-6" 
            fill="none" viewBox="0 0 24 24">
         <path stroke-linecap="round" 
               stroke-linejoin="round" 
               stroke-width="2" 
               d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
       </svg>
       <span>{{ message }}</span>
       
       {% if dismissible %}
       <button class="btn btn-sm btn-ghost btn-circle absolute right-2" 
               onclick="this.parentElement.remove()">
           ✕
       </button>
       {% endif %}
   </div>
   ```

2. **Use in templates**:
   ```html
   {% include 'partials/_alert.html' with type='success' message='Profile updated!' dismissible=True %}
   
   {% include 'partials/_alert.html' with type='error' message='Invalid credentials' %}
   ```

3. **Test all variants**:
   ```bash
   # Test: info, success, warning, error types
   # Test: dismissible and non-dismissible
   # Test: long message text wrapping
   ```

4. **Document component usage** in template comments:
   ```html
   {# 
     Alert Component
     
     Parameters:
     - type: info|success|warning|error (default: info)
     - message: Text to display (required)
     - dismissible: Boolean, adds close button (default: False)
     
     Example:
     {% include 'partials/_alert.html' with type='error' message='Error text' dismissible=True %}
   #}
   ```

This pattern ensures consistent alert styling across all templates and simplifies maintenance. See **django** skill for more template patterns.