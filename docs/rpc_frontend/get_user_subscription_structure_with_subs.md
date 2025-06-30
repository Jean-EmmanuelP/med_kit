## `get_user_subscription_structure_with_subs`

Fetches a structured list of a user's discipline and sub-discipline subscriptions. For each main discipline the user is subscribed to, it returns the discipline's details along with a JSON array of any specific sub-disciplines they have also subscribed to within that parent discipline.

### Parameters

| Parameter | Type   | Required/Optional | Description                                          |
| --------- | ------ | ----------------- | ---------------------------------------------------- |
| `p_user_id` | `uuid` | **Required**      | The ID of the user whose subscription structure is being fetched. |

### Returns

A `SETOF` a custom record containing the following fields for each main discipline the user is subscribed to:

-   `id`: `integer` - The unique ID of the main discipline.
-   `name`: `text` - The name of the main discipline.
-   `subscribed_sub_disciplines`: `jsonb` - A JSON array of objects. Each object represents a specifically subscribed sub-discipline and has the shape `{ "id": integer, "name": "text" }`. If the user is subscribed to the main discipline but has not selected any specific sub-disciplines under it, this will be an empty array (`[]`).

**Example Returned Row:**

```json
{
  "id": 15,
  "name": "Cardiologie",
  "subscribed_sub_disciplines": [
    { "id": 120, "name": "Rythmologie" },
    { "id": 122, "name": "Cardiologie interventionnelle" }
  ]
}
```

### Logic

1.  **Identify Main Disciplines**: The function first finds all unique main discipline IDs that the user is subscribed to in any capacity (either directly to the main discipline or to one of its sub-disciplines).
2.  **Retrieve Main Discipline Details**: It then fetches the `id` and `name` for each of these main disciplines from the `disciplines` table.
3.  **Aggregate Sub-Disciplines**: For each main discipline row, it runs a correlated subquery that:
    -   Looks for entries in `user_subscriptions` where `sub_discipline_id` is NOT `NULL` and matches the current main discipline.
    -   Joins with `sub_disciplines` to get the names.
    -   Aggregates the results into a single `jsonb` array of objects, sorted alphabetically by sub-discipline name.
    -   Uses `COALESCE` to ensure an empty array `[]` is returned instead of `NULL` if no specific sub-disciplines are subscribed.
4.  **Sort and Return**: The final result set, containing one row for each main discipline the user follows, is sorted alphabetically by the main discipline's name.

### Example Client-Side Usage

This function is called in `frontend/src/routes/ma-veille/+page.server.ts` to build the filter options for the user's personal feed.

```javascript
// Example from frontend/src/routes/ma-veille/+page.server.ts
async function fetchUserStructure(userId) {
  const { data: userSubscriptionStructure, error } = await supabase.rpc(
    'get_user_subscription_structure_with_subs',
    { p_user_id: userId }
  );

  if (error) {
    console.error("Error fetching user subscription structure:", error);
    return [];
  }
  
  // The data is then sorted and used to populate the dropdowns on the page.
  return userSubscriptionStructure;
}
```