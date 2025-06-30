# Function: `add_daily_articles_and_mark_article_of_the_day()`

This function iterates through every discipline in the database to introduce a new, unseen article and then designate the most recently published article as the new "Article of the Day" (AotD) for that discipline.

## Parameters

This function takes no parameters.

## Returns

This function returns `void`.

## Logic

The function loops through every discipline and performs the following steps for each one:

1.  **Add New Content**: It identifies the most recently published article that belongs to the current discipline but has **not yet been introduced** into the `showed_articles` table. If one is found, it's inserted into `showed_articles`, ensuring a steady stream of new content enters the AotD rotation pool.

2.  **Reset Previous AotD**: It finds the article that was previously the "Article of the Day" for the **current discipline** and sets its `is_article_of_the_day` flag to `false`. This clears the slate for the new AotD.

3.  **Select New AotD**: It searches through all articles in `showed_articles` that belong to the current discipline and selects the one with the most recent `published_at` date to be the new AotD.

4.  **Mark New AotD**: It updates the selected article's `is_article_of_the_day` flag to `true`. A safety update is also performed to ensure no other article for that discipline is flagged as the AotD.