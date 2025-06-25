# Supabase Edge Functions Documentation

This document outlines all the Supabase Edge Functions used in the medical content platform. These functions handle various aspects of user communication, payment processing, and notifications.

## Overview

The platform uses 8 edge functions organized into three main categories:

## 📧 Email & Notification Functions

These functions handle user communication through SendGrid email service.

1. [**Send Daily Notification**](./supabase_functions/send-daily-notification.md)
   - *Automated batch processing of daily notifications to all eligible users*

2. [**Send Notification**](./supabase_functions/send-notification.md)
   - *Single user notification for manual or triggered notifications*

3. [**Send Email to All Users**](./supabase_functions/send-email-to-all-users.md)
   - *Bulk email sending for announcements and marketing campaigns*

4. [**Send Welcome Email**](./supabase_functions/send-welcome-email.md)
   - *Automated welcome email for new user registrations*

## 💳 Payment & Subscription Functions

These functions handle Stripe payment processing and subscription management.

5. [**Stripe Donation Webhook**](./supabase_functions/stripe-donation-webhook.md)
   - *Processes one-time donation payments from Stripe webhooks*

6. [**Stripe Recurring Handler**](./supabase_functions/stripe-recurring-handler.md)
   - *Handles recurring subscription payments (production)*

7. [**Stripe Recurring Handler Test Mode**](./supabase_functions/stripe-recurring-handler-test-mode.md)
   - *Handles recurring subscription payments (development/testing)*

8. [**Stripe Webhook Handler Monthly**](./supabase_functions/stripe-webhook-handler-monthly.md)
   - *Specialized handler for monthly subscription processing*

## 🔧 Shared Utilities

- [**Utils**](./supabase_functions/utils.md)
  - *Shared utility functions for Supabase client initialization*

## Key Features

- **🔐 Secure Authentication**: All functions use service role keys for database access
- **📧 Email Integration**: Comprehensive SendGrid integration with templates
- **💰 Payment Processing**: Full Stripe webhook handling for donations and subscriptions
- **🔄 Batch Processing**: Efficient batch operations for large user bases
- **📊 Error Handling**: Robust error handling and logging throughout
- **🔒 Webhook Security**: Proper webhook signature verification for all payment functions

## Environment Variables

All functions require specific environment variables for:
- **Supabase**: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- **SendGrid**: `SENDGRID_API_KEY`
- **Stripe**: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SIGNING_SECRET`

## Integration Architecture

These edge functions serve as the serverless backend for:
- User onboarding and communication
- Payment and subscription management
- Automated content delivery notifications
- Admin tools for user management

---
*This documentation is split into multiple files. You can `Ctrl+Click` (or `Cmd+Click` on Mac) on the links above to navigate between sections in VS Code.* 