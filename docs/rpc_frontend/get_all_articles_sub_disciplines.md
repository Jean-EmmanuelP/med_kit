## `get_all_articles_sub_disciplines`

This is the primary workhorse RPC function responsible for fetching, filtering, and ranking a paginated list of articles. It is highly versatile and serves multiple purposes, including the user's personalized "Ma Veille" feed, the general "Tous les articles" view, and handling searches and filters across the platform.

### Parameters

| Parameter                   | Type      | Required/Optional | Description                                                                                                                              |
| --------------------------- | --------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `p_user_id`                 | `uuid`    | Optional          | The ID of the currently logged-in user. Required for personalizing results (`is_read`, `is_liked`, filtering by subscriptions, etc.).         |
| `p_discipline_name`         | `text`    | Optional          | The name of a main discipline to filter by.                                                                                              |
| `p_sub_discipline_name`     | `text`    | Optional          | The name of a sub-discipline to filter by. Only effective if `p_discipline_name` is also provided.                                       |
| `p_offset`                  | `integer` | Optional          | The number of articles to skip for pagination. Defaults to `0`.                                                                            |
| `p_search_term`             | `text`    | Optional          | A search term for full-text search against article titles and content.                                                                   |
| `p_filter_by_user_subs`     | `boolean` | Optional          | If `true`, filters articles based on the `p_user_id`'s subscriptions. If `false` (default), it ignores user subscriptions.                 |
| `p_allowed_grades`          | `text[]`  | Optional          | An array of grades (e.g., `['A', 'B']`) to filter articles. If not provided, the function determines grades based on user preferences or defaults. |
| `p_only_recommendations`    | `boolean` | Optional          | If `true`, returns only articles where `is_recommandation` is true. Defaults to `false`.                                                   |

### Returns

A `SETOF` a custom record containing the following fields for each article:

-   `article_id`: `integer` - The unique ID of the article.
-   `title`: `text`
-   `content`: `text`
-   `published_at`: `timestamp with time zone`
-   `link`: `text`
-   `grade`: `text`
-   `journal`: `text`
-   `is_read`: `boolean` - `true` if the `p_user_id` has read the article.
-   `is_liked`: `boolean` - `true` if the `p_user_id` has liked the article.
-   `like_count`: `bigint` - Total like count for the article across all users.
-   `read_count`: `bigint` - Total read count for the article across all users.
-   `is_thumbed_up`: `boolean` - `true` if the `p_user_id` has thumbed-up the article.
-   `thumbs_up_count`: `bigint` - Total thumbs-up count for the article.
-   `is_recommandation`: `boolean`
-   `is_article_of_the_day`: `boolean` - `true` if the article is identified as the "Article of the Day" for the current filter context.

### Logic

This function executes a sophisticated, multi-step process to deliver the most relevant articles.

1.  **Parameter Processing**:
    -   It resolves `p_discipline_name` and `p_sub_discipline_name` to their respective IDs.
    -   It cleans and converts `p_search_term` into a `tsquery` for full-text search.
2.  **Grade Filtering Logic**: It determines which article grades to show based on a hierarchy:
    -   **Priority 1**: If `p_allowed_grades` is provided, it uses that array directly.
    -   **Priority 2**: If `p_filter_by_user_subs` is `true` and a `p_user_id` is present, it fetches the user's preferences from the `user_grade_preferences` table.
    -   **Default**: If neither of the above conditions is met, it defaults to showing all grades (`['A', 'B', 'C']`).
3.  **"Article of the Day" (AotD) Identification**:
    -   This logic runs **only** on the first page of results (`p_offset = 0`) and when there is **no active search**.
    -   It looks in the `showed_articles` table for the most recent article added in the last 24 hours that matches the current discipline (or sub-discipline) filter.
    -   If found, its ID is stored to be prioritized in the results.
4.  **Core Filtering & Ranking (CTE `ranked_articles`)**:
    -   It first filters all articles based on the determined **allowed grades**.
    -   It then applies the discipline, sub-discipline, and search filters.
    -   Crucially, it **ranks** the matching articles to determine the order.
5.  **Sorting & Ranking Order**: The results are sorted with the following priority:
    -   **1. AotD First**: The "Article of the Day" (if identified) is always the very first result.
    -   **2. Perfect Title Match**: Articles where the title perfectly matches the search term are ranked higher.
    -   **3. Search Relevance**: Articles are ranked by their full-text search score (`ts_rank_cd`).
    -   **4. Publication Date**: Newer articles are ranked higher.
    -   **5. Article ID**: A final tie-breaker for consistent ordering.
6.  **Final Enrichment & Pagination**:
    -   The top-ranked article IDs are selected.
    -   The function joins back to the main `articles` table to get the full details.
    -   It calculates user-specific flags (`is_read`, `is_liked`, `is_thumbed_up`) for the provided `p_user_id`.
    -   Finally, it applies the `LIMIT 10` and `OFFSET` for pagination.

### Example Client-Side Usage

This function is the backend for the API endpoint `/api/get_articles_my_veille`, which is called by the `ArticleListView` component.

```javascript
// Example from frontend/src/routes/api/get_articles_my_veille/+server.js
// This API route translates URL query params into RPC parameters.

export const GET = async ({ url, locals: { supabase, safeGetSession } }) => {
    // ... read params from url ...
    const specialty = url.searchParams.get('specialty');
    const search = url.searchParams.get('search');
    const userId = (await safeGetSession()).user?.id;
    // ... and so on for other params

    const { data, error } = await supabase.rpc(
        'get_all_articles_sub_disciplines',
        {
            p_user_id: userId,
            p_discipline_name: specialty,
            p_search_term: search,
            p_filter_by_user_subs: true, // Example for 'Ma Veille' page
            // other params...
        }
    );
    // ... handle response ...
}
```