# `update_article_read_count`

This trigger function is analogous to `update_article_like_count` but is responsible for maintaining the denormalized `read_count` on the `articles` table.

## Trigger Details

| Property         | Value                |
| ---------------- | -------------------- |
| **Event**        | `INSERT`, `DELETE`   |
| **Timing**       | `AFTER`              |
| **Target Table** | `public.article_read` |

## Logic

The function is executed `AFTER` a row is inserted into or deleted from the `article_read` join table.

1.  **On `INSERT`**:
    -   This occurs when a user reads an article for the first time, creating a record in `article_read`.
    -   The function identifies the article via `NEW.article_id`.
    -   It increments the `read_count` column by `1` for that article in the `articles` table.

2.  **On `DELETE`**:
    -   This would occur if a "mark as unread" feature were implemented, which would delete the corresponding row from `article_read`.
    -   The function identifies the article via `OLD.article_id`.
    -   It decrements the `read_count` column by `1`.

## Benefit

-   **Performance**: Just like with likes, this avoids expensive `COUNT` operations when displaying how many times an article has been read, making the UI faster and more responsive.