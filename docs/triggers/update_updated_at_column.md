# `update_updated_at_column`

This is a generic utility function designed to automatically update an `updated_at` timestamp column whenever a row in a table is modified. It is functionally very similar to `trigger_set_timestamp` but uses `CURRENT_TIMESTAMP`.

## Trigger Details

| Property         | Value                                                  |
| ---------------- | ------------------------------------------------------ |
| **Event**        | `UPDATE`                                               |
| **Timing**       | `BEFORE`                                               |
| **Target Table** | Any table with an `updated_at` column (e.g., `articles`). |

## Logic

This function is designed to be executed `BEFORE` an `UPDATE` operation occurs on a row.

1.  It receives the `NEW` record, which represents the row's state *after* the `UPDATE` statement is applied.
2.  It sets the `updated_at` field of this `NEW` record to the current statement's timestamp using `CURRENT_TIMESTAMP`.
3.  It returns the modified `NEW` record, which is then written to the table.

This guarantees that any update to a row will also refresh its `updated_at` timestamp.

## Benefit

-   **Data Integrity & Automation**: Ensures that the `updated_at` field is always accurate without requiring the application layer to manage it, reducing errors and simplifying client-side code.