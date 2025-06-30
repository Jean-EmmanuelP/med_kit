## `get_daily_read_stats`

Calculates and returns key read-activity statistics for a single, specified day from the `article_read` table.

### Parameters

| Parameter  | Type   | Required/Optional | Description                                                              |
| ---------- | ------ | ----------------- | ------------------------------------------------------------------------ |
| `query_date` | `DATE` | **Required**      | The specific date (in `YYYY-MM-DD` format) for which to calculate the statistics. |

### Returns

A single record containing the aggregated statistics for the queried date. If no reads occurred on that day, it returns a single record with counts of `0`.

-   `read_day`: `date` - The date for which the statistics were calculated (echoes the `query_date` input).
-   `total_reads_per_day`: `bigint` - The **total number of read events** on that day. If one user reads 5 articles, this count increases by 5.
-   `unique_users_per_day`: `bigint` - The **total number of distinct users** who read at least one article on that day. If one user reads 5 articles, this count only increases by 1.

### Logic

1.  **Filtering**: The function filters the `article_read` table to include only records where the `read_at` timestamp falls on the exact `query_date`. It achieves this by casting `read_at` (a `timestamp`) to a `date`, effectively ignoring the time component.
2.  **Aggregation**: It performs two separate counts on the filtered records:
    -   `COUNT(*)` calculates the total number of rows, representing every single read action.
    -   `COUNT(DISTINCT ar.user_id)` calculates the number of unique users who performed those read actions.
3.  **Result**: The function returns a single row with these two aggregated counts, providing a snapshot of read activity for the specified day.

### Example Client-Side Usage

This function would typically be called from a secure, server-side context or an authenticated admin dashboard.

```javascript
// Example from frontend/src/routes/7zKw193hzWSMiAnhUnYbcNWS706lqGvZ/+page.svelte
async function fetchStatsForDate(dateString) { // dateString in 'YYYY-MM-DD' format
  const { data, error } = await supabase.rpc(
    'get_daily_read_stats',
    {
      query_date: dateString
    }
  );

  if (error) {
    console.error("Error fetching daily stats:", error);
    return null;
  }
  
  // The RPC returns an array, but we expect only one element
  // which might be null if the function had no rows to return (though this one always returns one row).
  const stats = data && data.length > 0 ? data[0] : null;
  console.log(stats);
  // Expected output: { read_day: '...', total_reads_per_day: 123, unique_users_per_day: 45 }
  return stats;
}
```