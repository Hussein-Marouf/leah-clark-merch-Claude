# UI/UX Audit

Date: 2026-04-27

## Current State

Leah Clark Merch is a focused convention ordering system with three user-facing surfaces:

- Customer order page: `/`
- Staff dashboard: `/admin`
- QR sign generator: `/qr`

The core idea is strong for a booth workflow: customers scan, select prints while waiting, save by email, and staff retrieve the order at checkout.

## What Works Well

- The visual identity is memorable and matches a convention/fandom merch context.
- The customer flow is short and easy to understand.
- The sticky cart makes the current selection visible while browsing.
- The admin dashboard gives staff useful booth-level metrics: pending orders, item count, and estimated revenue.
- QR generation is built in, which removes a common deployment friction point.

## Highest-Impact Improvements

1. Let customers browse before email capture.
   - Current flow asks for email before showing prints.
   - Recommended flow: browse first, then ask for email when saving/reviewing the order.
   - Benefit: less friction for fans scanning from a line or while passing the table.

2. Add print filtering.
   - Add filters for character, size, product type, and availability once inventory grows.
   - Benefit: faster selection on mobile and better support for larger catalogs.

3. Improve mobile cart behavior.
   - The fixed bottom cart is helpful, but it can cover the lower content.
   - Add body spacing when the cart is open and keep cart rows compact.
   - Benefit: fewer accidental missed prints on small screens.

4. Add pickup identifiers.
   - Confirmation should include an order ID or short pickup code.
   - Benefit: staff can find orders faster than searching only by email.

5. Add an inventory/admin print manager.
   - Currently, print inventory is edited in `server.js` or `db.json`.
   - A staff-only add/edit/hide-print page would reduce code edits before events.

## Accessibility Improvements

- Add visible labels for form fields.
- Announce toasts with `aria-live`.
- Make print cards keyboard selectable.
- Escape database-provided text before rendering it into HTML.
- Add reduced-motion CSS for visitors who disable animation.
- Add image fallback states for missing print assets.

## Reliability Improvements

- Validate order payloads on the server.
- Reject unknown or inactive print IDs.
- Keep generated `db.json` out of GitHub.
- Add a deployment note explaining that Render free instances may sleep.
- Back up `db.json` during conventions if orders are business-critical.

## Suggested Next Design Pass

1. Move email capture to the final save/review step.
2. Add an order review modal with selected items and total.
3. Add order ID to confirmation and admin cards.
4. Add print category/filter controls.
5. Add an admin inventory editor.
