
### `sync_article_sub_discipline_ids`

This trigger function is identical in purpose and logic to `sync_article_discipline_ids`, but it operates on the **sub-discipline** level. It maintains a denormalized array of sub-discipline IDs (`sub_discipline_ids`) on the `articles` table to accelerate queries that filter by sub-disciplines.

#### Trigger Details

| Property      | Value                             |
| ------------- | --------------------------------- |
| **Event**     | `INSERT`, `UPDATE`, `DELETE`      |
| **Timing**    | `AFTER`                           |
| **Target Table** | `public.article_sub_disciplines`  |

#### Logic

The function is fired *after* any row-level change on the `article_sub_disciplines` table.

1.  **On `INSERT` or `UPDATE`**:
    -   When a link is created between an article and a sub-discipline, the trigger uses `NEW.article_id`.
    -   It aggregates all `sub_discipline_id`s for that article from the `article_sub_disciplines` table into a new array.
    -   It updates the `sub_discipline_ids` column in the corresponding `articles` row with this new array.

2.  **On `DELETE` or `UPDATE`**:
    -   When a link is removed or changed, the trigger uses `OLD.article_id` to perform the same refresh operation, ensuring the array remains consistent.

#### Benefit

This significantly speeds up queries filtering by sub-discipline, avoiding a `JOIN` to the `article_sub_disciplines` table.