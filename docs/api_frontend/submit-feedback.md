# POST `/api/submit-feedback`

Submits user feedback about the platform, including content usefulness, format suitability, and payment willingness.

## Authentication

**Required:** User must be authenticated with a valid session.

## Request Body

```typescript
{
  contentUseful?: string,      // User's opinion on content usefulness
  formatSuitable?: string,     // User's opinion on format suitability
  desiredFeatures?: string,    // Features the user would like to see
  willingToPay?: string,       // "Oui" or "Non" - willingness to pay
  priceSuggestion?: string,    // Price suggestion (only if willingToPay is "Oui")
  reasonNotToPay?: string,     // Reason for not paying (only if willingToPay is "Non")
  improvements?: string        // Suggestions for improvements
}
```

## Response

### Success (201)
```typescript
{
  message: "Merci, votre retour a bien été envoyé !"
}
```

## Usage in Frontend

Used in the `FeedbackModal.svelte` component when users submit the feedback form.

**Location:** `src/components/FeedbackModal.svelte:92`

## Behavior

1. Validates user authentication
2. Processes the feedback data and maps it to database fields:
   - `contentUseful` → `content_useful`
   - `formatSuitable` → `format_suitable`
   - `desiredFeatures` → `desired_features`
   - `willingToPay` → `willing_to_pay`
   - `priceSuggestion` → `price_suggestion` (only stored if willing to pay)
   - `reasonNotToPay` → `reason_not_to_pay` (only stored if not willing to pay)
   - `improvements` → `improvements`
3. Inserts the feedback into the `feedback` table with the user's ID
4. Returns a success message in French

## Error Handling

- **401**: User not authenticated
- **400**: Invalid JSON format in request body
- **500**: Database insertion error

## Notes

- The payment-related fields are conditionally stored based on the `willingToPay` response
- All feedback fields are optional, allowing partial feedback submission
- The response message is in French: "Thank you, your feedback has been sent!" 