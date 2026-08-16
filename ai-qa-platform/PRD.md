# Project Requirement Document (PRD)
## QA Test Platform - Web Application for Automated Test Case Generation

### Version: 1.0
### Date: June 3, 2026

---

## 1. Executive Summary

The QA Test Platform is a feature-rich web application designed specifically to serve as a target application for AI-driven automated test case generation. The application includes authentication (User/Admin roles), product management, order management, user management, profile settings, and preference configuration. It provides a realistic testing ground with multiple user roles, CRUD operations, state management, form validations, and role-based access control — all essential elements for comprehensive test coverage.

## 2. Project Overview

### 2.1 Purpose
The primary purpose of this application is to act as a Subject Under Test (SUT) for:
- Auto-generating automation test cases (Selenium, Playwright, Cypress)
- Auto-generating manual test cases with step-by-step instructions
- Validating test coverage completeness across multiple features
- Testing newly added features for regression detection

### 2.2 Technology Stack
| Component | Technology |
|-----------|-----------|
| Frontend Framework | React 18 |
| Build Tool | Vite 5 |
| Routing | React Router v6 |
| State Management | React Context API |
| Styling | Plain CSS (no external UI library) |
| Language | JavaScript (ES Modules) |
| Package Manager | npm |

### 2.3 Target Users
1. **Admin Users**: Platform administrators with full access to all features including user management, product CRUD, order management
2. **Regular Users**: End users who can browse products, create orders, manage their profile, and configure settings

## 3. Functional Requirements

### 3.1 Authentication System (FR-001)

| ID | Requirement | Priority |
|----|------------|----------|
| FR-001.1 | Users shall be able to log in using a username and password | High |
| FR-001.2 | System shall support two roles: 'user' and 'admin' | High |
| FR-001.3 | Invalid credentials shall display an error message | High |
| FR-001.4 | Deactivated accounts shall show a specific error message | High |
| FR-001.5 | Empty username/password shall trigger client-side validation | Medium |
| FR-001.6 | Successful login shall redirect to the dashboard | High |
| FR-001.7 | Session shall persist via localStorage across page refreshes | High |
| FR-001.8 | Users shall be able to log out from the sidebar | High |
| FR-001.9 | Logout shall clear session and redirect to login page | High |

### 3.2 Role-Based Access Control (FR-002)

| ID | Requirement | Priority |
|----|------------|----------|
| FR-002.1 | Regular users shall not access the Users management page | High |
| FR-002.2 | Admin-only navigation links shall be hidden from regular users | High |
| FR-002.3 | Only admins can add/edit/delete products | Medium |
| FR-002.4 | Only admins can update order statuses (process, ship, deliver, cancel) | Medium |
| FR-002.5 | Both roles can view products and orders (filtered by ownership for users) | High |
| FR-002.6 | Unauthorized page access shall redirect to dashboard | High |

### 3.3 Dashboard (FR-003)

| ID | Requirement | Priority |
|----|------------|----------|
| FR-003.1 | Dashboard shall display key statistics as cards | High |
| FR-003.2 | Admin users shall see: Active Products, Total Orders, Pending Orders, Total Users, Total Revenue, Low Stock Items | High |
| FR-003.3 | Regular users shall see: Active Products, Total Orders, Pending Orders, My Total Spent | Medium |
| FR-003.4 | Dashboard shall display a Recent Orders table (last 5 orders) | High |
| FR-003.5 | Dashboard shall display a Recent Activity feed (last 6 activities) | Medium |
| FR-003.6 | Activities shall show different colored dots based on type (order, product, user) | Low |
| FR-003.7 | Admin dashboard shall show Quick Actions buttons: Add Product, Manage Orders, Manage Users, Inventory | Medium |
| FR-003.8 | Admin dashboard shall show a Low Stock Alerts widget listing products with stock <= 10 | Medium |
| FR-003.9 | Admin dashboard shall show Order Distribution chart with status bars | Low |
| FR-003.10 | Admin dashboard shall show Recent Registrations widget (last 5 users) | Low |
| FR-003.11 | Dashboard welcome message shall include the logged-in user's name | Low |

### 3.4 Product Management (FR-004)

| ID | Requirement | Priority |
|----|------------|----------|
| FR-004.1 | Products page shall list all products in a card grid layout | High |
| FR-004.2 | Users shall search products by name or description | High |
| FR-004.3 | Users shall filter products by category | High |
| FR-004.4 | Clicking a product card shall open a detail modal | Medium |
| FR-004.5 | Admins shall be able to add new products via a form modal | High |
| FR-004.6 | Admins shall be able to edit existing products | High |
| FR-004.7 | Admins shall be able to delete products (with confirmation) | High |
| FR-004.8 | Product form shall include: name, description, price, category, stock, status | High |
| FR-004.9 | Product price shall accept decimal values | Medium |
| FR-004.10 | Products shall display status badges (active/inactive) | Medium |
| FR-004.11 | Out-of-stock products (stock=0) shall still be viewable | Low |

### 3.5 Order Management (FR-005)

| ID | Requirement | Priority |
|----|------------|----------|
| FR-005.1 | Orders page shall display all orders for admin; user's own orders for regular users | High |
| FR-005.2 | Users shall filter orders by status (pending, processing, shipped, delivered, cancelled) | High |
| FR-005.3 | Users shall search orders by Order ID | Medium |
| FR-005.4 | Users shall create new orders with multiple items | High |
| FR-005.5 | Order creation form shall include: shipping address, payment method, item selection | High |
| FR-005.6 | Users can add/remove multiple line items in an order | Medium |
| FR-005.7 | Clicking an order shall open a detail modal | Medium |
| FR-005.8 | Admin shall update order status with contextual buttons (pending->processing->shipped->delivered) | Medium |
| FR-005.9 | Admin shall cancel orders from the detail view | Medium |
| FR-005.10 | Order total shall be auto-calculated from line items | Medium |

### 3.6 User Management (Admin Only) (FR-006)

| ID | Requirement | Priority |
|----|------------|----------|
| FR-006.1 | Users page shall display all registered users in a table | High |
| FR-006.2 | Admin shall search users by name, username, or email | Medium |
| FR-006.3 | Admin shall add new users with: username, password, name, email, role, status | High |
| FR-006.4 | Admin shall edit existing users (username, name, email, role, status) | High |
| FR-006.5 | Admin shall toggle user status (active/inactive) with one click | Medium |
| FR-006.6 | Admin shall delete users (with confirmation) | High |
| FR-006.7 | Duplicate username validation on user creation | Medium |
| FR-006.8 | User table shall display: avatar, name, username, email, role badge, status badge, joined date | Medium |

### 3.7 Profile Management (FR-007)

| ID | Requirement | Priority |
|----|------------|----------|
| FR-007.1 | Profile page shall display current user information | Medium |
| FR-007.2 | Users shall edit their name and email | Medium |
| FR-007.3 | Profile edit form shall have validation (non-empty fields) | Medium |
| FR-007.4 | Successful profile update shall show a success message | Low |
| FR-007.5 | Profile page shall display: avatar, name, username, email, role, member since date | Medium |

### 3.8 Settings (FR-008)

| ID | Requirement | Priority |
|----|------------|----------|
| FR-008.1 | Settings page shall have an Appearance section with theme selection | Low |
| FR-008.2 | Settings page shall have a Notifications section with toggles | Low |
| FR-008.3 | Settings page shall have a Preferences section (language, entries per page) | Low |
| FR-008.4 | Settings form shall save and show a success message | Low |
| FR-008.5 | Theme options: Light, Dark, System Default | Low |
| FR-008.6 | Notification toggles: Email, Push, SMS | Low |
| FR-008.7 | Language options: English, Spanish, French, German, Japanese | Low |
| FR-008.8 | Entries per page: 10, 20, 50, 100 | Low |

### 3.9 Navigation & Layout (FR-009)

| ID | Requirement | Priority |
|----|------------|----------|
| FR-009.1 | Application shall have a fixed sidebar navigation | High |
| FR-009.2 | Sidebar shall show current user avatar, name, and role badge | Medium |
| FR-009.3 | Navigation links shall highlight the active page | Medium |
| FR-009.4 | Sidebar shall have a logout button at the bottom | Medium |
| FR-009.5 | 404 page shall be shown for unknown routes | Medium |
| FR-009.6 | Root path ("/") shall redirect to dashboard | Medium |

## 4. Non-Functional Requirements

| ID | Requirement | Priority |
|----|------------|----------|
| NFR-001 | Application shall be responsive for desktop screens (1024px+) | Medium |
| NFR-002 | Page load time shall be under 3 seconds on modern hardware | Medium |
| NFR-003 | Application shall use mock/local data — no external API dependencies | High |
| NFR-004 | Session data shall persist in localStorage across browser refreshes | Medium |
| NFR-005 | Form inputs shall have proper labels and accessibility attributes | Low |
| NFR-006 | Error states shall be clearly communicated to users | Medium |

## 5. User Roles & Permissions Matrix

| Feature | Admin | Regular User |
|---------|-------|-------------|
| Login | Yes | Yes |
| View Dashboard (full stats with admin widgets) | Yes | Limited |
| View Products | Yes | Yes |
| Add/Edit/Delete Products | Yes | No (View Only) |
| View All Orders | Yes | Own Orders Only |
| Create Orders | Yes | Yes |
| Update Order Status | Yes | No |
| Cancel Orders | Yes | No |
| View All Users | Yes | No |
| Add/Edit/Delete Users | Yes | No |
| Edit Profile | Yes | Yes |
| Configure Settings | Yes | Yes |
| Access 404 Page | Yes | Yes |

## 6. Page Routes

| Route | Page | Access | Description |
|-------|------|--------|-------------|
| `/login` | Login | Public | Authentication page |
| `/dashboard` | Dashboard | Authenticated | Home page with stats |
| `/products` | Products | Authenticated | Product catalog |
| `/orders` | Orders | Authenticated | Order management |
| `/users` | Users | Admin Only | User management |
| `/profile` | Profile | Authenticated | User profile |
| `/settings` | Settings | Authenticated | App preferences |
| `/*` | 404 | All | Not found page |

## 7. Mock Data

The application ships with pre-seeded mock data:

- **Users**: 8 users (2 admins, 6 regular; 6 active, 2 inactive)
- **Products**: 15 products across 7 categories
- **Orders**: 12 orders with various statuses
- **Activities**: 8 recent activity entries

### Demo Credentials
- **Admin**: username: `admin`, password: `admin123`
- **User**: username: `john`, password: `john123`

## 8. Upcoming Features (v2.0)

The following features are planned for future releases. These are intentionally NOT implemented yet so that the test generator can demonstrate test case generation for newly added features:

### F-001: Shopping Cart
- Add products to a persistent shopping cart
- View cart with quantity adjustments
- Checkout flow converting cart to order
- Cart badge indicator in navigation

### F-002: Product Reviews & Ratings
- Users can rate products (1-5 stars)
- Users can write text reviews
- Reviews display with username and date
- Average rating on product cards

### F-003: Inventory Management
- Low stock alerts (threshold configurable)
- Bulk stock update interface
- Stock movement history log
- Auto-disable products when stock reaches zero

### F-004: Reporting & Analytics
- Sales reports with date range picker
- Most sold products chart
- Revenue by category pie chart
- Export reports as CSV

### F-005: Multi-language Support (i18n)
- Full internationalization support
- Language switcher in sidebar
- Right-to-left (RTL) layout support for Arabic/Hebrew

### F-006: Email Notification System
- Email templates for order confirmation
- Email templates for shipping updates
- In-app notification center
- Notification read/unread status

### F-007: Payment Gateway Integration
- Credit card payment form with validation
- Multiple payment methods (stripe, PayPal)
- Payment history per order
- Refund processing for cancelled orders

### F-008: Export Functionality
- Export products list to CSV/PDF
- Export orders report to CSV/PDF
- Export user list to CSV
- Configurable export columns

## 9. Data Dictionary

### User Object
| Field | Type | Description |
|-------|------|-------------|
| id | Number | Unique identifier |
| username | String | Login username (unique) |
| password | String | Login password |
| name | String | Display name |
| email | String | Email address |
| role | Enum: 'admin'/'user' | User role |
| status | Enum: 'active'/'inactive' | Account status |
| avatar | String/null | Avatar URL |
| joinedAt | String (date) | Registration date |

### Product Object
| Field | Type | Description |
|-------|------|-------------|
| id | Number | Unique identifier |
| name | String | Product name |
| description | String | Product description |
| price | Number (decimal) | Product price |
| category | String | Product category |
| stock | Number | Available stock count |
| status | Enum: 'active'/'inactive' | Product status |
| image | String/null | Product image URL |
| createdAt | String (date) | Creation date |
| updatedAt | String (date) | Last update date |

### Order Object
| Field | Type | Description |
|-------|------|-------------|
| id | String (ORD-xxx) | Unique order ID |
| userId | Number | Ordering user ID |
| items | Array | Array of { productId, quantity } |
| total | Number (decimal) | Order total |
| status | Enum: pending/processing/shipped/delivered/cancelled | Order status |
| shippingAddress | String | Shipping address |
| paymentMethod | String | Payment method |
| createdAt | String (date) | Order date |
| updatedAt | String (date) | Last update |

### Activity Object
| Field | Type | Description |
|-------|------|-------------|
| id | Number | Unique identifier |
| type | Enum: 'order'/'product'/'user' | Activity type |
| message | String | Activity description |
| timestamp | String (datetime) | Activity time |
| userId | Number | Related user ID |

## 10. Assumptions & Constraints

1. **No Backend**: All data is stored in-memory and in localStorage. Changes are lost on page refresh unless persisted via localStorage (only session data is persisted).
2. **No Real API**: The application uses mock data loaded from JavaScript modules.
3. **Single Browser Tab**: No cross-tab synchronization for auth state.
4. **Desktop-First**: The UI is optimized for desktop screens (1024px+). Tablet/mobile support is limited.
5. **No Image Uploads**: Product and user images are placeholder text avatars only.
6. **No Password Hashing**: Passwords are stored in plaintext in mock data (for testing purposes only).

## 11. Glossary

| Term | Definition |
|------|------------|
| SUT | Subject Under Test — the application being tested |
| CRUD | Create, Read, Update, Delete — basic data operations |
| RBAC | Role-Based Access Control |
| PRD | Project Requirement Document |
| FR | Functional Requirement |
| NFR | Non-Functional Requirement |
| SUT | System Under Test |
