# Cron Job: `add_daily_articles_job`

This scheduled job is the core engine for populating and curating the "Article of the Day" (AotD) feature for each discipline. It runs daily to ensure fresh content is highlighted.

## Job Details

| Property        | Value                                                           |
| --------------- | --------------------------------------------------------------- |
| **Schedule**    | `0 10 * * *` (Daily at 10:00 AM UTC)                              |
| **Action**      | `SELECT public.add_daily_articles_and_mark_article_of_the_day();` |
| **Description** | Runs the daily process to update the "Article of the Day" for each discipline. |

## Associated Function

This job executes a single PostgreSQL function. For detailed information on its logic, refer to the function's documentation:

-   [`add_daily_articles_and_mark_article_of_the_day()`](./add_daily_articles_and_mark_article_of_the_day.md) 