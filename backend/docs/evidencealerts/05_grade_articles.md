# Step 5: Article Grading (`grade_articles/pubmed_grading.py`)

This final script evaluates the level of evidence for new articles, providing a crucial quality metric for users.

[**← Back to Main Index**](../pipeline.md)

-   **Input**:
    -   Operates directly on the Supabase database, querying for articles where the `graded_yet` flag is `FALSE`.
    -   Supabase and Google API credentials from the `.env` file.

-   **Process**:
    1.  Fetches a batch of ungraded articles from the database.
    2.  For each article, it uses the `link` to visit the PubMed page and scrape the full abstract text.
    3.  It uses the Gemini API with a double-check and arbitration workflow similar to the classification step.
    4.  The prompt asks the model to assign a grade (A, B, C, or Accord d'experts) based on the study's methodology as described in the abstract, according to a predefined evidence-level framework.
    5.  The final, validated grade is determined.

-   **Output**:
    -   Updates the `grade` and `graded_yet` columns for the processed articles in the Supabase `articles` table. The `graded_yet` flag is set to `TRUE` on success or `ERROR` on failure, preventing the article from being picked up again unnecessarily.