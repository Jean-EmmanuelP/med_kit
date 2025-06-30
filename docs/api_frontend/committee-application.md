# POST `/api/committee-application`

Submits a committee application form to join the medical committee.

## Authentication

**Not Required:** This endpoint accepts applications from both authenticated and unauthenticated users.

## Request Body

```typescript
{
  prenom: string,           // First name (required)
  nom: string,              // Last name (required)
  statut: string,           // Professional status (required)
  specialite: string,       // Specialty (required)
  surSpecialite?: string,   // Sub-specialty (optional)
  centre: string            // Practice center (required)
}
```

## Response

### Success (201)
```typescript
{
  message: "Votre candidature a bien été envoyée. Merci !"
}
```

## Usage in Frontend

Used in the committee application page (`/comite`) when users fill out and submit the application form.

**Location:** `src/routes/comite/+page.svelte:161`

## Behavior

1. Validates required fields in the request body
2. Inserts application data into the `committee_applications` table
3. Maps frontend field names to database column names:
   - `prenom` → `first_name`
   - `nom` → `last_name`
   - `statut` → `status`
   - `specialite` → `specialty`
   - `surSpecialite` → `sub_specialty`
   - `centre` → `practice_center`

## Error Handling

- **400**: Missing required fields or invalid JSON format
- **500**: Database insertion error 