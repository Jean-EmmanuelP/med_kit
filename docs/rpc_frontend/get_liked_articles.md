## `get_liked_articles`

Retrieves a paginated list of articles that a specific user has liked, with optional filtering by discipline, sub-discipline, and a search term.

### Parameters

| Parameter                 | Type      | Required/Optional | Description                                                                                             |
| ------------------------- | --------- | ----------------- | ------------------------------------------------------------------------------------------------------- |
| `p_user_id`               | `uuid`    | **Required**      | The ID of the user whose liked articles are being fetched. The function will return nothing if this is `NULL`. |
| `p_discipline_name`       | `text`    | Optional          | The name of a main discipline to filter the liked articles.                                             |
| `p_sub_discipline_name`   | `text`    | Optional          | The name of a sub-discipline to further filter the results. Only effective if `p_discipline_name` is also provided. |
| `p_search_term`           | `text`    | Optional          | A search term to perform a full-text search on the article's `title` and `content`.                     |
| `p_offset`                | `integer` | Optional          | The number of articles to skip, used for pagination. Defaults to `0`.                                     |

### Returns

A `SETOF` a custom record containing the following fields for each liked article:

-   `article_id`: `integer` - The unique ID of the article.
-   `title`: `text`
-   `content`: `text` (summary content)
-   `published_at`: `timestamp with time zone`
-   `link`: `text` (URL to the original article)
-   `grade`: `text` (e.g., 'A', 'B', 'C')
-   `journal`: `text`
-   `is_recommandation`: `boolean`
-   `is_read`: `boolean` - `true` if the calling user (`p_user_id`) has read this article, otherwise `false`.
-   `is_liked`: `boolean` - Always returns `true` for this function.
-   `like_count`: `bigint` - The **total** number of likes this article has received from all users.

### Logic

1.  **Starts with the User**: The function begins by finding all `article_id`s associated with the provided `p_user_id` from the `article_likes` table.
2.  **Filters Results**: It then joins these IDs with the `articles` table and applies the optional filters:
    -   If `p_discipline_name` is provided, it filters for articles in that discipline.
    -   If `p_sub_discipline_name` is provided, it adds a filter for that sub-discipline.
    -   If `p_search_term` is provided, it performs a full-text search against the title and content.
3.  **Enriches Data**: For the final, filtered list, it calculates and appends:
    -   `is_read`: A boolean flag indicating if the specific `p_user_id` has marked the article as read.
    -   `like_count`: The total number of likes from all users for that article.
4.  **Sorts and Paginates**: The final results are ordered by the date the user liked the article (most recent first) and then paginated using the `p_offset` and a fixed `LIMIT` of 10.

### Example Client-Side Usage

```javascript
// Example from frontend/src/lib/components/articles/ArticleListView.svelte
async function fetchLikedArticles(userId, offset, specialty, subDiscipline, searchTerm) {
  const { data, error } = await supabase.rpc(
    'get_liked_articles',
    {
      p_user_id: userId,
      p_discipline_name: specialty, // e.g., 'Cardiologie' or null for all
      p_sub_discipline_name: subDiscipline, // e.g., 'Rythmologie' or null for all
      p_search_term: searchTerm, // e.g., 'atrial fibrillation' or null
      p_offset: offset
    }
  );

  if (error) {
    console.error("Error fetching liked articles:", error);
    return [];
  }
  return data;
}
```