# `update_showed_articles`

This trigger function ensures data consistency between the primary `articles` table and a secondary `showed_articles` table. When an article's details are updated in the main table, this function propagates those changes to the corresponding entry in `showed_articles`.

## Trigger Details

| Property         | Value             |
| ---------------- | ----------------- |
| **Event**        | `UPDATE`          |
| **Timing**       | `AFTER`           |
| **Target Table** | `public.articles` |

## Logic

The function is executed `AFTER` a row in the `articles` table is updated.

1.  It takes the just-updated record (`NEW`) from the `articles` table.
2.  It finds the row in the `showed_articles` table where the `article_id` matches `NEW.id`.
3.  It updates the `title`, `content`, `journal`, `published_at`, `link`, and `grade` columns in the `showed_articles` row to match the new values from the `articles` table.

This is useful for keeping cached, logged, or featured article data in sync with the source of truth.

## Benefit

-   **Data Consistency**: Prevents stale data in the `showed_articles` table. If an article's title is corrected or its content is refined in the main `articles` table, this trigger ensures the change is automatically reflected everywhere it's being tracked or cached.