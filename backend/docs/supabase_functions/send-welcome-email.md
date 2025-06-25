# Send Welcome Email

**Location**: `supabase/functions/send-welcome-email/index.ts`

**Purpose**: Automated welcome email sent to new users upon registration, providing onboarding information and platform introduction.

## Function Overview

This function is typically triggered by user registration events and sends a personalized welcome email using a dedicated SendGrid template.

## Request Format

**Method**: `POST`

**Required Fields**:
```json
{
  "user_id": "uuid-string",
  "email": "user@example.com",
  "first_name": "John"
}
```

## Validation

All three fields are strictly required:

```typescript
if (!user_id || !email || !first_name) {
  return new Response(
    JSON.stringify({
      error: "Les champs user_id, email et first_name sont requis",
    }),
    { status: 400 }
  );
}
```

## SendGrid Integration

### Template Configuration
- **Template ID**: `d-da9d98610ccf4169874f4b2d648a24c8`
- **Template Type**: Welcome/Onboarding template
- **Personalization**: Uses user's first name

### Email Structure
```typescript
const sendgridPayload = {
  personalizations: [{
    to: [{ email }],
    dynamic_template_data: {
      first_name,
      base_url: "https://veillemedicale.fr"
    }
  }],
  asm: {
    group_id: 303981,
    groups_to_display: [303981]
  },
  from: {
    email: "contact@veillemedicale.fr",
    name: "Équipe Veille Médicale"
  },
  template_id: "d-da9d98610ccf4169874f4b2d648a24c8"
};
```

### Template Variables
- **`first_name`**: User's first name for personalization
- **`base_url`**: Platform URL for links and references

## Email Content Features

The welcome email template typically includes:
- Personal greeting using first name
- Platform introduction and benefits
- Getting started guide
- Important links and resources
- Contact information
- Unsubscribe options

## Response Format

**Success** (200):
```json
{
  "message": "Email de bienvenue envoyé avec succès"
}
```

**Error** (400):
```json
{
  "error": "Les champs user_id, email et first_name sont requis"
}
```

**Error** (500):
```json
{
  "error": "Échec de l'envoi de l'email",
  "details": "Detailed SendGrid error message"
}
```

## Error Handling

### Input Validation
- Validates all required fields are present
- Returns descriptive error messages
- Prevents processing with incomplete data

### SendGrid API Errors
- Catches and logs SendGrid API failures
- Returns detailed error information
- Includes original SendGrid error messages

### Missing API Key
- Validates SendGrid API key is configured
- Returns 500 error if key is missing
- Prevents function execution without proper setup

## Integration Points

### User Registration Flow
Typically called during user registration:

```typescript
// After successful user creation
const { error } = await supabase.functions.invoke('send-welcome-email', {
  body: {
    user_id: newUser.id,
    email: newUser.email,
    first_name: newUser.user_metadata.first_name
  }
});
```

### Database Triggers
Can be triggered by Supabase database functions:

```sql
-- Example trigger function
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger AS $$
BEGIN
  -- Call the edge function
  PERFORM net.http_post(
    url := 'https://your-project.supabase.co/functions/v1/send-welcome-email',
    headers := '{"Content-Type": "application/json", "Authorization": "Bearer YOUR_ANON_KEY"}'::jsonb,
    body := json_build_object(
      'user_id', NEW.id,
      'email', NEW.email,
      'first_name', NEW.raw_user_meta_data->>'first_name'
    )::jsonb
  );
  RETURN NEW;
END;
$$ language plpgsql security definer;
```

## Testing

### Manual Testing
```bash
curl -X POST https://your-project.supabase.co/functions/v1/send-welcome-email \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-uuid",
    "email": "test@example.com",
    "first_name": "Test User"
  }'
```

### Automated Testing
```javascript
const testWelcomeEmail = async () => {
  const response = await fetch('/functions/v1/send-welcome-email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + supabaseKey
    },
    body: JSON.stringify({
      user_id: 'test-id',
      email: 'developer@test.com',
      first_name: 'Developer'
    })
  });
  
  const result = await response.json();
  console.log('Welcome email test:', result);
};
```

## Environment Variables Required

```env
SENDGRID_API_KEY=your_sendgrid_api_key
```

## Monitoring

Monitor for:
- **Email Delivery**: Track successful sends vs failures
- **Template Performance**: Monitor SendGrid template analytics
- **User Experience**: Ensure emails arrive promptly after registration
- **Error Rates**: Watch for API failures or configuration issues

## Best Practices

- **Timing**: Send immediately after registration confirmation
- **Content**: Keep welcome content engaging and informative
- **Testing**: Regularly test with real email addresses
- **Compliance**: Ensure unsubscribe options are clear
- **Analytics**: Track email open rates and engagement 