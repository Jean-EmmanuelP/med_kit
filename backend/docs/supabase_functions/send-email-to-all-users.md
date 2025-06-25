# Send Email to All Users

**Location**: `supabase/functions/send-email-to-all-users/index.ts`

**Purpose**: Bulk email sending function for marketing campaigns, announcements, and administrative communications to all platform users.

## Function Overview

This function enables sending the same email template to all registered users efficiently using batch processing and SendGrid's bulk email capabilities.

## Key Features

### 📨 Bulk Processing
- Processes users in batches of 250
- Memory-efficient for large user bases
- Automatic pagination through user database

### 🎯 Template-Based
- Uses configurable SendGrid templates
- No dynamic content per user (static templates only)
- Suitable for announcements, updates, marketing

### 🔒 Unsubscribe Management
- Automatic unsubscribe group integration
- Respects user preferences and legal requirements
- Group ID: `303981`

## Request Format

**Method**: `POST`

**Required Fields**:
```json
{
  "template_id": "d-your-template-id-here"
}
```

## Workflow Process

### 1. Template Validation
```typescript
if (!template_id) {
  return new Response(
    JSON.stringify({ error: "Template ID manquant" }),
    { status: 400 }
  );
}
```

### 2. Batch User Processing
```typescript
const USERS_BATCH_SIZE = 250;
let from = 0;
let hasMore = true;
let totalEmailsSent = 0;

while (hasMore) {
  const { data: users } = await supabase
    .from("user_profiles")
    .select("email")
    .range(from, from + USERS_BATCH_SIZE - 1);
}
```

### 3. SendGrid Bulk Send
```typescript
const sendgridPayload = {
  personalizations: users.map(user => ({
    to: [{ email: user.email }]
  })),
  from: {
    email: "contact@veillemedicale.fr",
    name: "Veille Médicale"
  },
  asm: {
    group_id: 303981,
    groups_to_display: [303981]
  },
  template_id: template_id
};
```

## Configuration

### Batch Size
- **User Batch**: 250 users per database query
- **Email Batch**: All users in batch sent in single SendGrid call
- **Memory Efficient**: Prevents timeout on large user bases

### Email Settings
- **From Address**: `contact@veillemedicale.fr`
- **From Name**: `Veille Médicale`
- **Unsubscribe Group**: `303981`

## Response Format

**Success** (200):
```json
{
  "message": "Emails envoyés avec succès",
  "totalEmailsSent": 1250
}
```

**Error** (400/500):
```json
{
  "error": "Error description"
}
```

## Error Handling

### Template Validation
- Validates template ID is provided
- Returns 400 for missing template

### Database Errors
- Catches Supabase query errors
- Returns 500 with error details

### SendGrid Errors
- Validates SendGrid API responses
- Returns 500 for email sending failures
- Includes detailed error messages

### Batch Processing
- Continues processing even if one batch fails
- Tracks total successful sends
- Logs progress for monitoring

## Usage Examples

### Admin Panel
```javascript
const sendBulkEmail = async (templateId) => {
  const response = await fetch('/functions/v1/send-email-to-all-users', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + supabase.auth.session().access_token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      template_id: templateId
    })
  });
  
  const result = await response.json();
  console.log(`Sent to ${result.totalEmailsSent} users`);
};
```

### Marketing Campaign
```bash
curl -X POST https://your-project.supabase.co/functions/v1/send-email-to-all-users \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"template_id": "d-marketing-campaign-template"}'
```

## SendGrid Template Requirements

Templates used with this function should:
- Be static (no dynamic personalization needed)
- Include unsubscribe links
- Be compliant with email marketing regulations
- Have appropriate subject lines

## Monitoring

Monitor for:
- **Processing Time**: Large user bases may take several minutes
- **Success Rate**: Track `totalEmailsSent` vs expected user count
- **SendGrid Status**: Monitor 202 responses from SendGrid
- **Error Patterns**: Watch for consistent batch failures

## Environment Variables Required

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SENDGRID_API_KEY=your_sendgrid_api_key
```

## Use Cases

- **Product Updates**: New features, platform changes
- **Marketing Campaigns**: Promotional content, events
- **System Announcements**: Maintenance, policy changes
- **Newsletter**: Regular updates to all users
- **Emergency Communications**: Critical platform notifications

## Considerations

⚠️ **Important Notes**:
- No user targeting or segmentation
- All active users receive the email
- Cannot personalize content per user
- Respects unsubscribe preferences automatically
- Should be used sparingly to avoid spam complaints 