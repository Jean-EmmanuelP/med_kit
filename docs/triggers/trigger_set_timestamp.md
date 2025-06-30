# `trigger_set_timestamp`

This is a generic utility function designed to automatically update an `updated_at` timestamp column whenever a row in a table is modified.

## Trigger Details

| Property         | Value                                                 |
| ---------------- | ----------------------------------------------------- |
| **Event**        | `UPDATE`                                              |
| **Timing**       | `BEFORE`                                              |
| **Target Table** | Any table with an `updated_at` column (e.g., `user_profiles`). |

## Logic

This function is designed to be executed `BEFORE` an `UPDATE` operation occurs on a row.

1.  It receives the `NEW` record, which represents the row's state *after* the `UPDATE` statement is applied but *before* it's saved to the database.
2.  It sets the `updated_at` field of this `NEW` record to the current transaction's timestamp using `NOW()`.
3.  It then returns the modified `NEW` record, which is what gets written to the table.

This ensures that any update to a row, regardless of which column was changed, will also refresh the `updated_at` timestamp automatically.

## Benefit

-   **Data Integrity**: Guarantees that the `updated_at` field is always accurate.
-   **Automation**: Removes the need for the application layer to manually set this timestamp on every update, reducing code duplication and potential for error.