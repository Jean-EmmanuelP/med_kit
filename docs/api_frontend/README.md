# Frontend API Documentation

This directory contains documentation for all the frontend API endpoints in the medical watch application.

## Overview

The application provides RESTful API endpoints for various functionalities including user management, article interactions, payment processing, and content retrieval.

## API Categories

### Payment & Subscriptions
- [`cancel-stripe-subscription`](./cancel-stripe-subscription.md) - Cancel user subscriptions
- [`create-customer-portal-session`](./create-customer-portal-session.md) - Access Stripe billing portal
- [`create-donation-intent`](./create-donation-intent.md) - Process one-time donations
- [`create-subscription`](./create-subscription.md) - Create new subscriptions
- [`create-payment-intent`](./create-payment-intent.md) - Legacy subscription creation

### Article Interactions
- [`get_articles_my_veille`](./get_articles_my_veille.md) - Retrieve personalized articles
- [`get-liked-articles`](./get-liked-articles.md) - Get user's liked articles
- [`mark-article-read`](./mark-article-read.md) - Mark articles as read (upsert)
- [`toggle-article-like`](./toggle-article-like.md) - Toggle article like status
- [`toggle-article-read`](./toggle-article-read.md) - Toggle article read status
- [`toggle-article-thumbs-up`](./toggle-article-thumbs-up.md) - Toggle article thumbs-up status

### User Management & Preferences
- [`update-profile-and-subscriptions`](./update-profile-and-subscriptions.md) - Update user profile and preferences
- [`get_sub_disciplines`](./get_sub_disciplines.md) - Get discipline sub-categories
- [`dismiss-feature-notice`](./dismiss-feature-notice.md) - Hide UI notifications

### Feedback & Applications
- [`submit-feedback`](./submit-feedback.md) - Submit user feedback
- [`update-feedback-modal`](./update-feedback-modal.md) - Control feedback modal timing
- [`committee-application`](./committee-application.md) - Submit committee applications

## Authentication

Most endpoints require user authentication through Supabase sessions. The authentication requirement is clearly marked in each endpoint's documentation.

## Common Response Patterns

### Success Responses
- **200**: Successful operation
- **201**: Resource created successfully
- **204**: No content (successful operation with no response body)

### Error Responses
- **400**: Bad request (invalid input)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (access denied)
- **404**: Not found (resource doesn't exist)
- **500**: Internal server error

## Usage in Frontend

Each endpoint documentation includes specific information about:
- Where it's used in the frontend codebase
- File locations and line numbers
- Component context and user interactions

## Database Triggers

Many article interaction endpoints trigger database functions that maintain denormalized counts (likes, reads, thumbs-ups) for performance optimization.

## Environment Variables

Several endpoints require environment configuration for Stripe integration and other external services. These are documented in the respective endpoint files. 