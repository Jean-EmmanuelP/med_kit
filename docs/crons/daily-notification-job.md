### Cron Job: `daily-notification-job`

This scheduled job is responsible for initiating the daily process of sending notification emails to users. It does this by making a secure HTTP request to a specific Supabase Edge Function.

#### Job Details

| Property         | Value                                                                                                        |
| ---------------- | ------------------------------------------------------------------------------------------------------------ |
| **Schedule**     | `30 10 * * *` (Daily at 10:30 AM UTC)                                                                          |
| **Action**       | Triggers the `send-daily-notification` Supabase Edge Function using an HTTP POST request via `pg_net`.           |
| **Description**  | This job acts as a timed trigger. It does not contain the email logic itself; it simply "wakes up" the Edge Function that does. |

#### Associated Edge Function

The core logic for fetching user preferences, finding relevant articles, and sending emails is handled entirely within the `send-daily-notification` Edge Function. The cron job's only purpose is to call this function on a schedule.

For detailed information on the email-sending logic, refer to the function's documentation:

-   [`send-daily-notification`](../../backend/docs/supabase_functions/send-daily-notification.md)