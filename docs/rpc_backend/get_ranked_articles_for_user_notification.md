Of course. Here is the detailed documentation for the `get_ranked_articles_for_user_notification` RPC function, formatted for its own markdown file.

---

### `get_ranked_articles_for_user_notification`

Fetches a ranked and personalized list of the newest articles for a specific user, tailored to their subscriptions. This function is designed to be called by an automated process, like the daily notification Edge Function, to gather relevant content for a user's email.

#### Parameters

| Parameter                 | Type          | Required/Optional | Description                                                                                             |
| ------------------------- | ------------- | ----------------- | ------------------------------------------------------------------------------------------------------- |
| `p_user_id`               | `uuid`        | **Required**      | The ID of the user for whom to generate the notification content.                                         |
| `p_start_date`            | `timestamptz` | **Required**      | The start date of the lookback period. The function will find articles added to the system on or after this date. |
| `p_articles_per_category` | `integer`     | **Required**      | The maximum number of articles to return *for each* of the user's subscribed disciplines/sub-disciplines.   |

#### Returns

A `SETOF` a custom record containing the following fields for each selected article:

| Column                       | Type                      | Description                                                                                                    |
| ---------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `article_id`                 | `integer`                 | The unique ID of the article.                                                                                  |
| `matched_category_name`      | `text`                    | The name of the specific discipline or sub-discipline that caused this article to be included in the results.    |
| `triggering_discipline_id`   | `integer`                 | The ID of the main discipline that triggered the match. Useful for grouping articles in the notification email. |
| `added_at`                   | `timestamp with time zone`| The timestamp when the article was added to the `showed_articles` table. Used for ranking.                       |
| `link`                       | `text`                    | The URL to the original article.                                                                               |
| `title`                      | `text`                    | The article's title.                                                                                           |
| `journal`                    | `text`                    | The journal in which the article was published.                                                                |
| `published_at`               | `timestamp with time zone`| The original publication date of the article.                                                                  |
| `grade`                      | `text`                    | The recommendation grade of the article (e.g., 'A', 'B', 'C').                                                 |

#### Logic

This function executes a multi-step process to build a highly relevant list of articles for a user's notification.

1.  **Define Scope**: It first identifies the user's complete subscription profile (all main disciplines and specific sub-disciplines they follow).
2.  **Filter by Date**: It narrows down the potential pool of articles by selecting only those added to the `showed_articles` table on or after the `p_start_date`, and filters out articles published more than two years ago to maintain relevance.
3.  **Match to Subscriptions**: It then finds all articles from this date-filtered pool that match the user's subscriptions. This logic is nuanced:
    -   If a user subscribes to a **specific sub-discipline** (e.g., "Rythmologie"), it matches articles linked to that sub-discipline.
    -   If a user subscribes to a **main discipline** (e.g., "Cardiologie") but has *not* selected any specific sub-disciplines under it, it treats this as a "catch-all" and matches all articles within that main discipline.
4.  **Rank per Category**: For each of the user's subscribed categories (e.g., for "Rythmologie", for "Oncologie", etc.), the function ranks the matched articles. The newest articles (based on `added_at`) in each category receive the highest rank.
5.  **Limit per Category**: It then takes the top `N` articles from each category's ranked list, where `N` is the `p_articles_per_category` parameter.
6.  **Deduplicate and Return**: Since a single article might match multiple user subscriptions (e.g., belongs to two sub-disciplines a user follows), the final step uses `DISTINCT ON (article_id)` to ensure each article is returned only once, preventing duplicates in the notification email.

#### Example Usage

This function is designed to be called by a server-side process, such as the `send-daily-notification` Supabase Edge Function.