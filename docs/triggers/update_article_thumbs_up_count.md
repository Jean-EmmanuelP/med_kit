# `update_article_thumbs_up_count`

This trigger function is responsible for maintaining an accurate, denormalized count of "thumbs up" actions for each article. It updates the `articles.thumbs_up_count` column, which serves as a performance optimization by avoiding real-time `COUNT(*)` aggregations.

## Trigger Details

| Property         | Value                          |
| ---------------- | ------------------------------ |
| **Event**        | `INSERT`, `DELETE`             |
| **Timing**       | `AFTER`                        |
| **Target Table** | `public.article_thumbs_up`     |

## Logic

The function is executed `AFTER` a row is inserted into or deleted from the `article_thumbs_up` table.

1.  **On `INSERT`**:
    -   Occurs when a user gives a "thumbs up" to an article.
    -   The function identifies the relevant article via `NEW.article_id`.
    -   It increments the `thumbs_up_count` column by `1` for that specific article in the `articles` table.

2.  **On `DELETE`**:
    -   Occurs when a user removes their "thumbs up".
    -   The function identifies the article via `OLD.article_id`.
    -   It decrements the `thumbs_up_count` column by `1` for that article.

## Benefit

-   **Performance**: Massively improves the performance of fetching and displaying "thumbs up" counts. Instead of a `JOIN` and `COUNT` for every article displayed, the application can simply read the pre-calculated integer from the `articles.thumbs_up_count` column.