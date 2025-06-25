# Send Notification

**Location**: `supabase/functions/send-notification/index.ts`

**Purpose**: Simple function to send a single notification email to a specific user with custom article content.

## Function Overview

This function provides a direct interface for sending individual notifications, typically used for:
- Manual notifications from admin interface
- Triggered notifications based on specific events
- Testing notification templates

## Request Format

**Method**: `POST`

**Required Fields**:
```json
{
  "user_id": "123",
  "email": "user@example.com",
  "first_name": "John",
  "articles": [
    {
      "id": 12345,
      "title": "Article Title",
      "journal": "Medical Journal",
      "discipline": "Cardiology",
      "link": "https://pubmed.ncbi.nlm.nih.gov/..."
    }
  ]
}
```

**Optional Fields**:
```json
{
  "headers": {
    "Authorization": "Bearer ...",
    "Content-Type": "application/json"
  },
  "link": "custom_link_if_needed"
}
```

## Validation

The function validates:
- **Email**: Must be provided and valid format
- **First Name**: Required for personalization
- **Articles**: Must be an array with at least one article

```typescript
if (!email || !first_name || !articles || !Array.isArray(articles)) {
  return new Response(
    JSON.stringify({
      error: "Les champs email, first_name et articles (tableau) sont requis",
    }),
    { status: 400 }
  );
}
```

## SendGrid Integration

**Template**: Uses the same template as daily notifications
**Template ID**: `d-27f89a4f0faa4df1ab83b9fbc7be19a1`

**Email Configuration**:
```typescript
{
  personalizations: [{
    to: [{ email }],
    dynamic_template_data: {
      first_name: first_name,
      articles: articles.map(article => ({
        id: article.id,
        title: article.title,
        journal: article.journal || "Inconnu",
        discipline: article.discipline || "Non spécifié",
        link: article.link
      }))
    }
  }],
  from: {
    email: "contact@veillemedicale.fr",
    name: "Veille Médicale"
  }
}
```

## Response Format

**Success** (200):
```json
{
  "message": "Notification envoyée avec succès"
}
```

**Error** (400/500):
```json
{
  "error": "Error description",
  "details": "Detailed error message",
  "status": 500
}
```

## Error Handling

- **Missing Fields**: Returns 400 with specific field requirements
- **SendGrid API Key**: Returns 500 if API key not configured
- **SendGrid Errors**: Returns 500 with detailed error information
- **Network Issues**: Catches and reports connection problems

## Usage Examples

### Admin Interface
```javascript
const response = await fetch('/functions/v1/send-notification', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + supabase.auth.session().access_token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_id: selectedUser.id,
    email: selectedUser.email,
    first_name: selectedUser.first_name,
    articles: selectedArticles
  })
});
```

### Manual Testing
```bash
curl -X POST https://your-project.supabase.co/functions/v1/send-notification \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123",
    "email": "test@example.com",
    "first_name": "Test User",
    "articles": [{
      "id": 1,
      "title": "Test Article",
      "journal": "Test Journal",
      "discipline": "Test Discipline",
      "link": "https://example.com"
    }]
  }'
```

## Environment Variables Required

```env
SENDGRID_API_KEY=your_sendgrid_api_key
SUPABASE_ANON_KEY=your_anon_key  # Optional, for default headers
```

## Integration

This function is typically called by:
- Admin dashboard for manual notifications
- Other edge functions for triggered notifications
- Testing and development workflows
- Custom notification workflows 