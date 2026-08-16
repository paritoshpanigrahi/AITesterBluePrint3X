# User Stories - QA Test Platform

## Version 1.0 | Sprint 1

---

## Epic 1: Authentication & Access Control

### Story US-001: User Login
**As a** registered user or admin  
**I want to** log in with my username and password  
**So that** I can access the platform features

**Acceptance Criteria:**
- Login form accepts username and password inputs
- Form validates that both fields are non-empty before submission
- Valid credentials redirect the user to the dashboard
- Invalid credentials display error: "Invalid username or password"
- Deactivated account displays error: "Account is deactivated. Contact admin."
- Login form includes demo credentials hint for testing
- Successful login persists session in localStorage

**Technical Notes:**
- Route: `/login`
- Auth state managed via React Context (`AuthContext`)
- Session persisted in localStorage key `qa_current_user`

---

### Story US-002: User Logout
**As a** logged-in user  
**I want to** log out from the sidebar  
**So that** I can end my session securely

**Acceptance Criteria:**
- Logout button is visible in the sidebar footer
- Clicking logout clears the auth context state
- localStorage session data is removed
- User is redirected to the login page

---

### Story US-003: Role-Based Navigation
**As an** admin user  
**I want to** see admin-specific navigation links  
**So that** I can access admin-only features

**Acceptance Criteria:**
- Admin users see "Users" link in the sidebar
- Regular users do NOT see the "Users" link
- Regular users cannot navigate to `/users` via URL (redirect to dashboard)
- Both roles see: Dashboard, Products, Orders, Profile, Settings

---

## Epic 2: Dashboard

### Story US-004: View Dashboard
**As a** logged-in user  
**I want to** see an overview dashboard when I log in  
**So that** I can get a quick summary of platform activity

**Acceptance Criteria:**
- Dashboard is the default page after login
- Dashboard shows a personalized welcome message with the user's name
- Stats cards show different data based on role:
  - **Admin**: Active Products, Total Orders, Pending Orders, Total Users, Total Revenue, Low Stock Items
  - **User**: Active Products, Total Orders, Pending Orders, My Total Spent
- Recent Orders table shows the latest 5 orders with ID, Total, Status, Date
- Activity feed shows the latest 6 platform activities
- Activities show different colored indicators by type
- Admin sees Quick Actions buttons: Add Product, Manage Orders, Manage Users, Inventory
- Admin sees Low Stock Alerts widget for products with stock <= 10 units
- Admin sees Order Distribution bars by status
- Admin sees Recent Registrations widget showing last 5 joined users

---

## Epic 3: Product Management

### Story US-005: Browse Products
**As a** logged-in user  
**I want to** view all products in a card grid  
**So that** I can browse the product catalog

**Acceptance Criteria:**
- Products display in a responsive card grid
- Each card shows: status badge, category, name, description (truncated), price, stock
- Clicking a product card opens a detail modal with full information
- Detail modal shows: name, category, price, stock, status, description, created/updated dates

---

### Story US-006: Search & Filter Products
**As a** logged-in user  
**I want to** search and filter products  
**So that** I can quickly find specific items

**Acceptance Criteria:**
- Search input filters products by name and description (case-insensitive)
- Category dropdown filters products by selected category
- Search and filter can be used together
- "No products found" message shown when no results match

---

### Story US-007: Add Product (Admin)
**As an** admin user  
**I want to** add new products to the catalog  
**So that** I can expand the product offerings

**Acceptance Criteria:**
- "Add Product" button visible only to admin users
- Clicking opens a modal form
- Required fields: name, price, category
- Optional fields: description, stock, status
- Form validates required fields before submission
- Successful creation adds the product to the list
- New product gets auto-generated ID and timestamps

---

### Story US-008: Edit Product (Admin)
**As an** admin user  
**I want to** edit existing products  
**So that** I can update product information

**Acceptance Criteria:**
- Edit button available in product detail modal (admin only)
- Edit modal pre-fills with current product data
- All fields are editable
- Changes update the product in the list
- Timestamp is updated on save

---

### Story US-009: Delete Product (Admin)
**As an** admin user  
**I want to** delete products from the catalog  
**So that** I can remove discontinued items

**Acceptance Criteria:**
- Delete button available in product detail modal (admin only)
- Confirmation dialog appears before deletion: "Are you sure you want to delete this product?"
- Confirmed deletion removes the product from the list
- Cancelled deletion leaves the product unchanged

---

## Epic 4: Order Management

### Story US-010: View Orders
**As a** logged-in user  
**I want to** see my orders  
**So that** I can track my purchases

**Acceptance Criteria:**
- Regular users see only their own orders (filtered by userId)
- Admin users see all orders
- Orders display in a card layout with: ID, customer name, total, status, item count, date
- Clicking an order opens a detail modal with full information

---

### Story US-011: Create New Order
**As a** logged-in user  
**I want to** create a new order with multiple items  
**So that** I can purchase products

**Acceptance Criteria:**
- "New Order" button opens a creation modal
- Form includes: shipping address (required), payment method (select), order items
- Multiple line items can be added/removed
- Each line item selects a product and specifies quantity
- Only active products are shown in the item selector
- Order total is calculated from selected items and quantities
- Submission validates at least one item and shipping address
- Successful creation adds the order to the top of the list

---

### Story US-012: Update Order Status (Admin)
**As an** admin user  
**I want to** update the status of orders  
**So that** I can manage the fulfillment process

**Acceptance Criteria:**
- Status update buttons appear in order detail modal (admin only)
- Contextual buttons: Pending -> Process, Processing -> Ship, Shipped -> Deliver
- Cancel button available for non-delivered/non-cancelled orders
- Status change updates the badge in the order list
- Timestamp is updated on status change

---

## Epic 5: User Management (Admin)

### Story US-013: View & Search Users
**As an** admin user  
**I want to** view all registered users in a table  
**So that** I can manage the user base

**Acceptance Criteria:**
- Users table shows: avatar, name, username, email, role badge, status badge, joined date, actions
- Search input filters by name, username, or email
- "No users found" message for empty search results

---

### Story US-014: Add New User (Admin)
**As an** admin user  
**I want to** create new user accounts  
**So that** I can onboard new people to the platform

**Acceptance Criteria:**
- "Add User" button opens creation modal
- Form includes: username (required), password (required), name (required), email (required), role, status
- Username uniqueness is validated
- Duplicate username shows alert: "Username already exists"
- New user appears in the user table

---

### Story US-015: Edit User (Admin)
**As an** admin user  
**I want to** edit user details  
**So that** I can update user information

**Acceptance Criteria:**
- Edit button in each user row
- Edit modal pre-fills with current user data (password field blank)
- Password field is optional on edit; leaving blank keeps existing password
- Changes update the user in the table

---

### Story US-016: Toggle User Status (Admin)
**As an** admin user  
**I want to** activate or deactivate users  
**So that** I can control platform access

**Acceptance Criteria:**
- Toggle button changes between "Activate" and "Deactivate" based on current status
- Deactivating a user prevents them from logging in
- Activating a user restores their login capability
- Status badge updates immediately in the table

---

### Story US-017: Delete User (Admin)
**As an** admin user  
**I want to** delete user accounts  
**So that** I can remove users from the platform

**Acceptance Criteria:**
- Delete button in each user row
- Confirmation dialog: "Delete this user?"
- Confirmed deletion removes the user from the table
- Cancelled deletion leaves the user unchanged

---

## Epic 6: Profile Management

### Story US-018: View Profile
**As a** logged-in user  
**I want to** see my profile information  
**So that** I can review my account details

**Acceptance Criteria:**
- Profile page shows: avatar (initial), name, username, email, role badge, member since date
- Information is read-only by default

---

### Story US-019: Edit Profile
**As a** logged-in user  
**I want to** edit my name and email  
**So that** I can keep my information up to date

**Acceptance Criteria:**
- "Edit Profile" button switches to edit mode
- Name and email fields are editable
- Form validates non-empty values
- Cancel button discards changes and reverts to original values
- Save button updates the profile
- Success message: "Profile updated successfully!"
- Updated info reflects in the sidebar header

---

## Epic 7: Settings

### Story US-020: Configure Settings
**As a** logged-in user  
**I want to** customize my application preferences  
**So that** the platform works the way I want

**Acceptance Criteria:**
- Appearance section with theme selector (Light, Dark, System)
- Notifications section with toggles (Email, Push, SMS)
- Preferences section with language selector (English, Spanish, French, German, Japanese)
- Preferences section with entries per page selector (10, 20, 50, 100)
- Save button persists all settings
- Success message: "Settings saved successfully!"

---

## Epic 8: Navigation & Error Handling

### Story US-021: Sidebar Navigation
**As a** logged-in user  
**I want to** navigate the platform using a sidebar menu  
**So that** I can easily access all features

**Acceptance Criteria:**
- Sidebar is fixed on the left side
- Shows platform logo at top
- Shows user avatar (initial), name, and role badge
- Navigation links highlight the currently active page
- Logout button at the bottom of the sidebar

---

### Story US-022: 404 Page
**As a** user  
**I want to** see a 404 page for invalid routes  
**So that** I know the page doesn't exist

**Acceptance Criteria:**
- Navigating to an unknown route shows a 404 page
- 404 page displays "404", "Page Not Found", description text, and "Go to Dashboard" link
- Root path ("/") redirects to "/dashboard"

---

## Upcoming Features (Sprint 2 / v2.0)

The following stories are intentionally NOT implemented yet. They serve as candidates for testing the test generator's ability to create test cases for newly added features.

### Story US-023: Shopping Cart
**As a** logged-in user  
**I want to** add products to a shopping cart and checkout  
**So that** I can purchase multiple items in a single order

**Detailed Design:**
- Cart icon in sidebar with item count badge
- "Add to Cart" button on each product card and detail modal
- Cart page at `/cart` showing all added items with quantities
- Quantity adjustment (+/-) and remove item per line
- "Clear Cart" button to remove all items
- "Checkout" button converts cart items into an order
- Cart data persists in localStorage
- Empty cart state with "Start Shopping" CTA

### Story US-024: Product Reviews & Ratings
**As a** logged-in user  
**I want to** rate and review products  
**So that** I can share my experience with others

**Detailed Design:**
- Star rating component (1-5) below product details
- Review text area with character limit (500 chars)
- Reviews display with: username, rating stars, review text, date
- Average rating shown on product cards
- Only one review per user per product
- Admin can delete inappropriate reviews
- Sort reviews by: Most Recent, Highest Rated, Lowest Rated

### Story US-025: Inventory Management
**As an** admin user  
**I want to** manage product inventory effectively  
**So that** I can track stock levels

**Detailed Design:**
- Inventory page at `/inventory`
- Table view: product name, current stock, low stock threshold, status
- Low stock threshold configuration (global default: 10)
- Products below threshold highlighted in yellow/red
- Bulk stock update: select multiple products, add/subtract stock
- Stock movement history log per product
- Auto-set product to "inactive" when stock reaches zero

### Story US-026: Reports & Analytics
**As an** admin user  
**I want to** view sales reports and analytics  
**So that** I can make data-driven decisions

**Detailed Design:**
- Reports page at `/reports`
- Sales overview: total revenue, total orders, average order value
- Date range picker for filtering
- Bar chart: Top 10 best-selling products
- Pie chart: Revenue by category
- Line chart: Sales trend over time
- Export all reports as CSV

### Story US-027: Multi-Language Support
**As a** user  
**I want to** use the platform in my preferred language  
**So that** I can understand the interface

**Detailed Design:**
- i18n framework integration (react-i18next)
- Language switcher in settings (already partially implemented)
- Translation files for: English (en), Spanish (es), French (fr), German (de), Japanese (ja)
- Dynamic content translation (order messages, activity entries)
- RTL layout support for right-to-left languages
- Language preference stored in localStorage

### Story US-028: Email Notifications
**As a** user  
**I want to** receive email notifications for order updates  
**So that** I stay informed about my purchases

**Detailed Design:**
- Notification center accessible from sidebar bell icon
- Email notifications for: order confirmation, shipping update, delivery confirmation
- In-app notification center with read/unread status
- Notification preferences in settings (partially implemented)
- Email template rendering for different notification types

### Story US-029: Payment Gateway Integration
**As a** user  
**I want to** pay for my orders online  
**So that** I can complete purchases securely

**Detailed Design:**
- Payment method selection during checkout
- Stripe integration for credit/debit card payments
- PayPal integration as alternative payment
- Payment form with card number, expiry, CVV validation
- Payment history per order in order detail
- Refund button for admin on cancelled orders
- Payment status tracking (pending, completed, failed, refunded)

### Story US-030: Data Export
**As a** user  
**I want to** export data to CSV or PDF  
**So that** I can analyze it offline

**Detailed Design:**
- Export button on Products page (CSV, PDF)
- Export button on Orders page (CSV, PDF)
- Export button on Users page (admin only, CSV)
- Configurable column selection for export
- Filename includes date and content type
- Exports respect current search/filter state
