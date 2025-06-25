# Shared Utilities

**Location**: `supabase/utils.ts`

**Purpose**: Provides shared utility functions for Supabase client initialization across edge functions.

## Overview

This module centralizes common functionality used by multiple edge functions, ensuring consistent configuration and error handling.

## Functions

### `getSupabaseClient()`

Creates and returns a configured Supabase client with service role permissions.

#### Implementation
```typescript
export function getSupabaseClient() {
  const supabase = createClient(
    env("SUPABASE_URL")!,
    env("SUPABASE_SERVICE_ROLE_KEY")!
  );
  if (!supabase) {
    throw new Error("Supabase failed to initialize");
  }
  return supabase;
}
```

#### Features
- **Service Role Access**: Uses service role key for full database access
- **Environment Configuration**: Reads from environment variables
- **Error Handling**: Throws descriptive error if initialization fails
- **Type Safety**: TypeScript support with proper typing

#### Usage Example
```typescript
import { getSupabaseClient } from "../utils.ts";

Deno.serve(async (req) => {
  const supabase = getSupabaseClient();
  
  // Now you can use supabase with full permissions
  const { data, error } = await supabase
    .from('user_profiles')
    .select('*');
});
```

## Helper Functions

### `env(key: string)`

Simple environment variable accessor with validation.

#### Implementation
```typescript
const env = (key: string) => Deno.env.get(key);
```

#### Features
- **Simple Access**: Direct wrapper around `Deno.env.get()`
- **Type Safety**: Returns `string | undefined`
- **Consistent Interface**: Used across all functions

#### Usage
```typescript
const apiKey = env("SENDGRID_API_KEY");
const supabaseUrl = env("SUPABASE_URL");
```

## Configuration

### Required Environment Variables
All functions using these utilities require:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Service Role Key Benefits
- **Bypasses RLS**: Can read/write any table regardless of Row Level Security
- **Admin Operations**: Full administrative access to database
- **Background Jobs**: Perfect for server-side operations like webhooks
- **No User Context**: Operates independently of user authentication

## Import Pattern

### Standard Import
```typescript
import { getSupabaseClient } from "../utils.ts";
```

### With Environment Helper
```typescript
import { getSupabaseClient } from "../utils.ts";

const env = (key: string) => Deno.env.get(key);
```

## Error Handling

### Initialization Failure
```typescript
try {
  const supabase = getSupabaseClient();
} catch (error) {
  console.error("Failed to initialize Supabase:", error.message);
  return new Response("Database connection failed", { status: 500 });
}
```

### Missing Environment Variables
```typescript
const supabaseUrl = env("SUPABASE_URL");
if (!supabaseUrl) {
  throw new Error("SUPABASE_URL environment variable is required");
}
```

## Best Practices

### Early Initialization
Initialize Supabase client early in function execution:
```typescript
Deno.serve(async (req) => {
  // Initialize immediately
  const supabase = getSupabaseClient();
  
  // Continue with function logic
  // ...
});
```

### Error Boundary
Wrap Supabase operations in try-catch blocks:
```typescript
try {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase.from('table').select('*');
  
  if (error) throw error;
  
} catch (dbError) {
  console.error("Database operation failed:", dbError);
  return new Response("Database error", { status: 500 });
}
```

### Type Safety
Use TypeScript for better development experience:
```typescript
import { createClient, SupabaseClient } from "jsr:@supabase/supabase-js@2";

export function getSupabaseClient(): SupabaseClient {
  // Implementation...
}
```

## Usage Across Functions

### Email Functions
- `send-daily-notification`: User profile queries and updates
- `send-email-to-all-users`: Bulk user email retrieval
- `send-welcome-email`: Not used (simple function)
- `send-notification`: Not used (simple function)

### Payment Functions
- `stripe-donation-webhook`: Recording donation transactions
- `stripe-recurring-handler`: Subscription management
- All Stripe webhooks use service role for database writes

## Future Enhancements

### Additional Utilities
Could be extended with:
```typescript
// Database connection pooling
export function getSupabasePool() { ... }

// Common query helpers
export async function getUserById(id: string) { ... }

// Error formatting
export function formatDbError(error: any) { ... }

// Logging utilities
export function logWithContext(message: string, context: any) { ... }
```

### Configuration Management
```typescript
// Centralized config
export const config = {
  supabase: {
    url: env("SUPABASE_URL")!,
    serviceRoleKey: env("SUPABASE_SERVICE_ROLE_KEY")!
  },
  sendgrid: {
    apiKey: env("SENDGRID_API_KEY")!
  }
};
```

## Security Notes

- **Service Role Key**: Extremely powerful - handle with care
- **Environment Variables**: Never log or expose in responses
- **Error Messages**: Don't leak sensitive configuration details
- **Access Control**: Service role bypasses all security - use responsibly 