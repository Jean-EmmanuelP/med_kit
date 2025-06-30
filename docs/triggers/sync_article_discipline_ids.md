### `sync_article_discipline_ids`

This trigger function is a performance optimization designed to keep a denormalized array of discipline IDs (`discipline_ids`) on the `articles` table in sync with the `article_disciplines` join table. By doing this, querying articles by one or more disciplines becomes much faster, as it can use array operators instead of requiring a more expensive `JOIN` operation.

#### Trigger Details

| Property      | Value                          |
| ------------- | ------------------------------ |
| **Event**     | `INSERT`, `UPDATE`, `DELETE`   |
| **Timing**    | `AFTER`                        |
| **Target Table** | `public.article_disciplines`   |

#### Logic

The function is fired *after* any row-level change on the `article_disciplines` table. It ensures that the `articles.discipline_ids` array is always an accurate reflection of the relationships in the join table.

1.  **On `INSERT` or `UPDATE`**:
    -   When a new link is created between an article and a discipline, or an existing link is modified, the trigger uses the `NEW.article_id` (the ID of the article in the just-inserted/updated row).
    -   It then runs a query to find **all** `discipline_id`s associated with that `article_id` in the `article_disciplines` table.
    -   It aggregates these IDs into a new array using `array_agg()`.
    -   Finally, it updates the `discipline_ids` column in the corresponding `articles` table row with this newly generated array.

2.  **On `DELETE` or `UPDATE`**:
    -   When a link is removed, the trigger uses the `OLD.article_id` (the ID of the article in the just-deleted row).
    -   It performs the same aggregation and update process as above. This ensures that if a discipline is unlinked from an article, the ID is correctly removed from the `articles.discipline_ids` array.
    -   This block is also essential for `UPDATE` operations where the `article_id` of a link might be changed, ensuring the *old* article's array is also refreshed.

#### Benefit

This approach significantly speeds up queries that need to filter articles by discipline, such as:

```sql
-- This query is much faster than one with a JOIN
SELECT * FROM articles WHERE discipline_ids @> ARRAY[15, 22]; -- Find articles with BOTH discipline 15 AND 22
```