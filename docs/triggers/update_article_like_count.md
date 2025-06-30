# `update_article_like_count`

This trigger function maintains an accurate, denormalized count of likes for each article in the `articles.like_count` column. It is a performance optimization that avoids costly `COUNT(*)` aggregations when displaying like counts.

## Trigger Details

| Property         | Value                 |
| ---------------- | --------------------- |
| **Event**        | `INSERT`, `DELETE`    |
| **Timing**       | `AFTER`               |
| **Target Table** | `public.article_likes` |

## Logic

The function is executed `AFTER` a row is inserted into or deleted from the `article_likes` table.

1.  **On `INSERT`**:
    -   This occurs when a user likes an article.
    -   The function identifies the relevant article via `NEW.article_id`.
    -   It then increments the `like_count` column by `1` for that specific article in the `articles` table.

2.  **On `DELETE`**:
    -   This occurs when a user unlikes an article.
    -   The function identifies the article via `OLD.article_id`.
    -   It decrements the `like_count` column by `1` for that article.

## Benefit

-   **Performance**: Drastically improves the performance of fetching like counts. Instead of a `JOIN` and `COUNT` for every article in a list, the application can simply read the pre-calculated integer from the `articles.like_count` column. This is essential for features like article lists and feeds.