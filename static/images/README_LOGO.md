# ShopCloud Logo & Icons

## Files Created

1. **logo.svg** - Full logo with text (200x60px)
   - Use for: Header, landing page, marketing materials
   - Contains: Cloud shape + Shopping cart + "ShopCloud" text

2. **logo-icon.svg** - Icon only (48x48px)
   - Use for: Sidebar, small spaces, app icons
   - Contains: Cloud shape + Shopping cart (no text)

3. **favicon.svg** - Browser favicon (64x64px)
   - Use for: Browser tab icon
   - Contains: Circular logo with cloud and cart

## Design Elements

- **Colors**: 
  - Primary Blue: #2563eb (Cloud)
  - Green: #10b981 (Shopping Cart)
  - Dark Gray: #1f2937 (Text)

- **Theme**: Cloud + Shopping Cart = ShopCloud
  - Represents cloud-based POS system
  - Shopping cart represents retail/shop

## Usage in Templates

### In base.html (Already Added):
```html
<!-- Favicon -->
<link rel="icon" type="image/svg+xml" href="{% static 'images/favicon.svg' %}">

<!-- Logo in Navbar -->
<img src="{% static 'images/logo-icon.svg' %}" alt="ShopCloud Logo">
```

### In Other Templates:
```django
{% load static %}
<img src="{% static 'images/logo.svg' %}" alt="ShopCloud">
```

## Customization

All logos are in SVG format, so you can:
- Scale to any size without quality loss
- Edit colors in any SVG editor
- Modify shapes and elements

## File Locations

- `/static/images/logo.svg`
- `/static/images/logo-icon.svg`
- `/static/images/favicon.svg`

---

**Created**: December 2024  
**Format**: SVG (Scalable Vector Graphics)  
**License**: For ShopCloud project use

