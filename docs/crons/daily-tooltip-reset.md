## Cron Job: `daily-tooltip-reset`

This scheduled job is responsible for periodically resetting a "feature notice" flag for users, allowing them to be shown the notice again after a certain amount of time has passed. This is useful for re-engaging users with important site features or announcements.

### Job Details

| Property         | Value                          |
| ---------------- | ------------------------------ |
| **Schedule**     | `0 0 * * *` (Daily at midnight UTC) |
| **Action**       | `SELECT public.reset_expired_tooltips();` |
| **Description**  | Resets the `has_seen_tooltip` flag for users whose last viewing was more than 14 days ago. |

### Associated Function: `reset_expired_tooltips()`

This function performs the core logic for the cron job. It identifies and updates user profiles where the feature notice can be shown again.

#### Function Definition

```sql
CREATE OR REPLACE FUNCTION public.reset_expired_tooltips()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  UPDATE public.user_profiles
  SET
    has_seen_tooltip = false,
    tooltip_time = NULL
  WHERE
    has_seen_tooltip = true
    AND tooltip_time < (now() - interval '14 days');
END;
$$;
```

#### Logic

1.  **Target Selection**: The `UPDATE` statement targets rows in the `user_profiles` table that meet **both** of the following conditions:
    -   `has_seen_tooltip = true`: The user has previously seen and dismissed the notice.
    -   `tooltip_time < (now() - interval '14 days')`: The timestamp of their last dismissal (`tooltip_time`) is more than 14 days in the past.

2.  **Action**: For all matching user profiles, the function performs two actions:
    -   It sets `has_seen_tooltip` back to `false`. This makes the user eligible to see the notice again on their next visit.
    -   It sets `tooltip_time` to `NULL`. This cleans up the old timestamp and prepares the row for a new one when the user next dismisses the notice.

#### Client-Side Interaction

-   **`Header.svelte`**: This component fetches the `has_seen_tooltip` flag for the current user. If the flag is `false`, it displays the `<NewFeatureNotice>` component.
-   **`NewFeatureNotice.svelte`**: When the user dismisses this notice, it triggers an event that calls the `/api/dismiss-feature-notice` API endpoint.
-   **`/api/dismiss-feature-notice`**: This API endpoint sets `has_seen_tooltip` to `true` and records the current timestamp in `tooltip_time` for the logged-in user.

This cron job completes the cycle by ensuring that the `true` flag is not permanent, allowing for periodic re-notification.