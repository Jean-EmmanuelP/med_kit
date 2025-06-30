# Send Daily Notification

**Location**: `supabase/functions/send-daily-notification/index.ts`

**Purpose**: Automated daily processing system that identifies eligible users and sends personalized medical content notifications based on their preferences and subscription status.

## Function Overview

This is the most complex edge function, handling the complete workflow for daily notifications across all platform users.

## Key Features

### 🔄 Batch Processing
- Processes users in batches of 50 for memory efficiency
- Handles large user bases without timeouts
- Resumes processing from where it left off if interrupted

### 🤖 Smart User Eligibility
- Checks notification frequency preferences (daily, weekly, monthly)
- Respects last notification sent dates
- Validates user subscription status

### 📊 Personalized Content Selection
- Uses RPC function `get_ranked_articles_for_user_notification`  ([../../../docs/rpc_backend/get_ranked_articles_for_user_notification.md](../../../docs/rpc_backend/get_ranked_articles_for_user_notification.md))
- Retrieves articles based on user's discipline preferences
- Applies intelligent ranking and filtering
- Respects article limits per frequency setting

### 📧 Bulk Email Processing
- SendGrid batch processing (100 emails per batch)
- Dynamic template with personalized content
- Unsubscribe management integration
- Comprehensive error handling

## Workflow Steps

### 1. User Processing Loop
```typescript
// Batch processing with resume capability
while (hasMoreUsers) {
  // Fetch 50 users at a time
  const userProfiles = await supabase
    .from('user_profiles')
    .select('id, email, first_name, notification_frequency, last_notification_sent_date')
    .order('id')
    .limit(USERS_BATCH_SIZE);
}
```

### 2. Eligibility Check
For each user:
- Validates notification frequency (daily/weekly/monthly)
- Checks if enough time has passed since last notification
- Determines article limits based on frequency

### 3. Content Retrieval
```typescript
// Call specialized RPC function
const { data: rpcData } = await supabase.rpc(
  'get_ranked_articles_for_user_notification',
  {
    p_user_id: user.id,
    p_start_date: articleStartDateISO,
    p_articles_per_category: maxArticlesPerCategory
  }
);
```

### 4. Email Sending
- Groups users into SendGrid batches
- Applies dynamic template with articles
- Tracks successful sends for database updates

### 5. Database Updates
- Updates `last_notification_sent_date` for successful sends
- Maintains processing statistics
- Logs comprehensive metrics

## Configuration Constants

```typescript
const USERS_BATCH_SIZE = 50;           // Users processed per batch
const SENDGRID_BATCH_SIZE = 100;       // Emails sent per SendGrid call
const API_CALL_LIMIT = 1000;          // Maximum RPC calls per run
```

## Frequency Settings

| Frequency | Articles Per Category | Lookback Days |
|-----------|----------------------|---------------|
| Daily     | 3                    | 1             |
| Weekly    | 5                    | 7             |
| Monthly   | 10                   | 30            |

## SendGrid Integration

**Template ID**: `d-27f89a4f0faa4df1ab83b9fbc7be19a1`

**Template Data**:
```typescript
{
  first_name: "John",
  articles: [
    {
      id: 12345,
      title: "Article Title",
      journal: "Medical Journal",
      discipline: "Cardiology",
      link: "https://pubmed.ncbi.nlm.nih.gov/..."
    }
  ]
}
```

## Performance Metrics

The function tracks and logs:
- Total users queried and processed
- Eligible users vs. users with available content
- Email sending success rates
- Processing time per batch
- RPC call performance

## Error Handling

- **Database Errors**: Continues processing, logs errors
- **RPC Failures**: Skips user, continues with next
- **SendGrid Errors**: Logs batch failures, continues
- **Memory Management**: Batch processing prevents memory issues

## Environment Variables Required

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SENDGRID_API_KEY=your_sendgrid_api_key
```

## Usage

Typically called via cron job or scheduled task:
```bash
curl -X POST https://your-project.supabase.co/functions/v1/send-daily-notification \
  -H "Authorization: Bearer YOUR_ANON_KEY"
```

## Monitoring

Monitor function logs for:
- Processing completion times
- Email delivery success rates
- User eligibility statistics
- Any database or API errors 