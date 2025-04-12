import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient, SupabaseClient } from "jsr:@supabase/supabase-js@2";

// --- Supabase Client Setup ---
const env = (key: string): string => {
  const value = Deno.env.get(key);
  if (!value) throw new Error(`Environment variable ${key} not set!`);
  return value;
};

function getSupabaseClient(): SupabaseClient {
  // Use explicit types for better safety
  const supabase = createClient(
    env("SUPABASE_URL"),
    env("SUPABASE_SERVICE_ROLE_KEY")
  );
  if (!supabase) {
    throw new Error("Supabase client failed to initialize");
  }
  return supabase;
}

// --- Constants ---
const USERS_BATCH_SIZE = 20; // Can potentially increase slightly with RPC/Parallel
const SENDGRID_BATCH_SIZE = 50; // SendGrid can often handle larger batches
const TWO_YEARS_AGO_INTERVAL = '2 years'; // Define interval for SQL, less critical in JS now

// --- Helper Function Types ---
type NotificationFrequency =
  | 'tous_les_jours'
  | 'tous_les_2_jours'
  | 'tous_les_3_jours'
  | '1_fois_par_semaine'
  | 'tous_les_15_jours'
  | '1_fois_par_mois'
  | string; // Allow other strings but handle defaults

interface UserProfile {
    id: string; // UUID
    email: string;
    first_name: string | null;
    disciplines: string[] | null;
    notification_frequency: NotificationFrequency;
    last_notification_sent_date: string | null; // ISO timestamp string
}

interface ArticleData {
    // Match the RPC function's output columns
    article_id_out: number;
    discipline_out: string;
    added_at_out: string; // ISO timestamp string
    link_out: string | null;
    title_out: string | null;
    journal_out: string | null;
    published_at_out: string | null; // ISO timestamp string
}

interface FormattedArticle {
    id: number;
    title: string;
    journal: string;
    discipline: string;
    link: string;
    // added_at is not directly used in template, but good for sorting/debugging
    // added_at: string;
}

interface UserToNotify {
    id: string;
    email: string;
    first_name: string;
    articles: FormattedArticle[];
}


// --- Main Function ---
Deno.serve(async (_req: Request) => {
  const overallStartTime = performance.now();
  console.log("Notification function started...");
  try {
    const supabase = getSupabaseClient();
    const usersToNotify: UserToNotify[] = [];
    let totalUsersQueried = 0;
    let totalUsersEligibleForCheck = 0;
    let hasMoreUsers = true;
    let lastUserId: string | null = null;
    const now = new Date(); // Get current time once for consistency

    console.time('users-processing-total');

    while (hasMoreUsers) {
      const batchFetchStartTime = performance.now();
      console.time(`user-batch-fetch-${lastUserId || 'initial'}`);
      const query = supabase.from('user_profiles')
          .select('id, email, first_name, disciplines, notification_frequency, last_notification_sent_date')
          // .eq("email", "alexis.chatelain123@gmail.com")
          .order('id') // Ensure consistent ordering for pagination
          .limit(USERS_BATCH_SIZE);

      if (lastUserId) {
        query.gt('id', lastUserId);
      }

      const { data: userProfiles, error: userError } = await query;
      console.timeEnd(`user-batch-fetch-${lastUserId || 'initial'}`);

      if (userError) {
          console.error("Error fetching user batch:", userError);
          throw userError; // Stop processing if we can't fetch users
      }

      if (!userProfiles || userProfiles.length === 0) {
          console.log("No more users found.");
          hasMoreUsers = false;
          continue; // Exit the loop
      }

      totalUsersQueried += userProfiles.length;
      const batchFetchEndTime = performance.now();
      console.log(`Fetched batch of ${userProfiles.length} users (starting after ID: ${lastUserId}). Time: ${(batchFetchEndTime - batchFetchStartTime).toFixed(2)}ms. Processing in parallel...`);

      // --- Parallel Processing within Batch ---
      console.time(`user-batch-processing-${lastUserId || 'initial'}`);
      const batchProcessingPromises = userProfiles.map(async (user: UserProfile): Promise<UserToNotify | 'eligible_no_articles' | null> => {
          const userProcessStartTime = performance.now();

          // 1. Check if eligible based on time/day
          if (!shouldSendNotification(user.notification_frequency, user.last_notification_sent_date, now)) {
            // console.log(`Skipping user ${user.email}: Too soon/wrong day.`); // Keep logs concise in parallel
            return null; // Not eligible today
          }

          // If eligible, increment count later based on results

          // 2. Validate user data needed for query
          const maxArticlesPerCategory = getMaxArticlesForFrequency(user.notification_frequency);
          const lookbackDays = getFrequencyLookbackDays(user.notification_frequency);

          if (maxArticlesPerCategory === 0 || lookbackDays === 0) {
              console.log(`Skipping user ${user.email}: Freq ${user.notification_frequency} -> 0 limit or lookback.`);
              return 'eligible_no_articles'; // Eligible for check, but config means no articles
          }
          if (!user.disciplines || user.disciplines.length === 0) {
              console.log(`Skipping user ${user.email}: No disciplines selected.`);
               return 'eligible_no_articles'; // Eligible for check, but no disciplines
          }

          // 3. Calculate start date for RPC query
          const articleStartDate = new Date(now.getTime() - lookbackDays * 24 * 60 * 60 * 1000);
          const articleStartDateISO = articleStartDate.toISOString();

          // 4. Call the RPC function
          let articlesForUser: ArticleData[] | null = null;
          try {
              console.time(`user-${user.id}-rpc-call`);
              const { data: rpcData, error: rpcError } = await supabase.rpc(
                  'get_ranked_articles_for_user_notification',
                  {
                      user_disciplines: user.disciplines,
                      start_date: articleStartDateISO,
                      articles_per_discipline: maxArticlesPerCategory
                  }
              );
              console.timeEnd(`user-${user.id}-rpc-call`);

              if (rpcError) {
                  console.error(`RPC Error for user ${user.email} (ID: ${user.id}): ${rpcError.message}`);
                  // Decide whether to retry or just skip the user for this run
                  return null; // Skip user on RPC error for this run
              }
              articlesForUser = rpcData; // Assign data if successful

          } catch (e) {
               console.error(`Exception during RPC call for user ${user.email} (ID: ${user.id}): ${e.message}`);
               console.timeEnd(`user-${user.id}-rpc-call`); // Ensure timer ends on exception
               return null; // Skip user on exception
          }

          // 5. Process RPC results
          if (articlesForUser && articlesForUser.length > 0) {
              // Map RPC output to the format needed for SendGrid
              const articlesJson: FormattedArticle[] = articlesForUser.map((article) => ({
                  id: article.article_id_out,
                  title: article.title_out || 'Titre inconnu', // Provide defaults
                  journal: article.journal_out || 'Journal inconnu',
                  discipline: article.discipline_out || 'Non spécifié',
                  link: article.link_out || '',
                  // added_at: article.added_at_out // Include if needed for debugging/template
              }));

              const userProcessEndTime = performance.now();
              // console.log(`User ${user.email} processed with ${articlesJson.length} articles. Time: ${(userProcessEndTime - userProcessStartTime).toFixed(2)}ms`);

              // Return the data needed for the usersToNotify list
              return {
                  id: user.id,
                  email: user.email,
                  first_name: user.first_name || 'Cher utilisateur', // Default name
                  articles: articlesJson
              };
          } else {
              // Eligible, but RPC found no matching articles within the criteria
              // console.log(`No articles found via RPC for user ${user.email} within lookback.`);
              return 'eligible_no_articles';
          }
      }); // End of userProfiles.map

      // Wait for all parallel tasks in the current batch to complete
      const batchResults = await Promise.all(batchProcessingPromises);
      console.timeEnd(`user-batch-processing-${lastUserId || 'initial'}`);

      // Process the results from the parallel execution
      let batchAddedToNotify = 0;
      let batchEligibleCount = 0;
      for (const result of batchResults) {
          if (result === 'eligible_no_articles') {
               batchEligibleCount++; // Count as eligible but not notified
          } else if (result) { // Check if it's a UserToNotify object (truthy and not the marker string)
               batchEligibleCount++; // Count as eligible AND notified
               usersToNotify.push(result);
               batchAddedToNotify++;
          }
          // Null results (from errors or skipped users) are ignored for counts
      }
      totalUsersEligibleForCheck += batchEligibleCount; // Update total eligible count

      console.log(`Finished processing batch. Eligible: ${batchEligibleCount}, Added to notify list: ${batchAddedToNotify}`);

      // --- End Parallel Processing ---

      // Update lastUserId for the next batch query
      // Ensure userProfiles is not empty before accessing the last element
      if (userProfiles.length > 0) {
        lastUserId = userProfiles[userProfiles.length - 1].id;
      }

      // Determine if there might be more users
      // Crucially, check if the number fetched was LESS than the batch size.
      // If it was equal, assume there *might* be more.
      hasMoreUsers = userProfiles.length === USERS_BATCH_SIZE;
      if (!hasMoreUsers) {
          console.log("Last batch fetched, no more users expected.");
      }


    } // End while(hasMoreUsers) loop

    console.timeEnd('users-processing-total');
    console.log(`Finished processing all users. Total Queried: ${totalUsersQueried}, Eligible for check today: ${totalUsersEligibleForCheck}, Will be notified: ${usersToNotify.length}`);

    // 5. Send notifications via SendGrid (Batched)
    let emailsSentSuccessfully = 0;
    const successfullyNotifiedUserIds: string[] = [];
    const currentTimestamp = new Date().toISOString(); // Timestamp for update

    console.time('sendgrid-processing');
    if (usersToNotify.length > 0) {
        for (let i = 0; i < usersToNotify.length; i += SENDGRID_BATCH_SIZE) {
            const batch = usersToNotify.slice(i, i + SENDGRID_BATCH_SIZE);
            const batchUserIds = batch.map((user) => user.id);
            const sendGridPayload = {
                personalizations: batch.map((user) => ({
                    to: [{ email: user.email }],
                    dynamic_template_data: {
                        first_name: user.first_name,
                        // Ensure articles are mapped correctly here again if needed
                        // The `FormattedArticle` structure should match the template's expectation
                        articles: user.articles.map(a => ({
                             id: a.id,
                             title: a.title,
                             journal: a.journal,
                             discipline: a.discipline,
                             link: a.link
                        })),
                    },
                })),
                from: {
                    email: "contact@veillemedicale.fr",
                    name: "Veille Médicale",
                },
                asm: { // Unsubscribe group
                    group_id: 303981, // Replace with your actual Group ID
                    groups_to_display: [303981],
                },
                template_id: "d-27f89a4f0faa4df1ab83b9fbc7be19a1", // Replace with your Template ID
                // "tracking_settings": { "click_tracking": { "enable": true } } // Optional: enable tracking
            };

            try {
                console.time(`sendgrid-batch-${i}`);
                const response = await fetch("https://api.sendgrid.com/v3/mail/send", {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${env("SENDGRID_API_KEY")}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(sendGridPayload),
                });
                console.timeEnd(`sendgrid-batch-${i}`);

                if (!response.ok) {
                    // Log detailed error from SendGrid if possible
                    const errorBody = await response.text();
                    console.error(`Failed SendGrid batch starting at index ${i}. Status: ${response.status}, Body: ${errorBody}`);
                    // Consider how to handle partial failures - maybe log failed user IDs?
                } else {
                    console.log(`Successfully sent SendGrid batch for ${batch.length} users (starting index ${i}). Status: ${response.status}`);
                    emailsSentSuccessfully += batch.length;
                    successfullyNotifiedUserIds.push(...batchUserIds);
                }
            } catch (error) {
                console.timeEnd(`sendgrid-batch-${i}`); // Ensure timer ends on error
                console.error(`Error sending SendGrid batch starting at index ${i}: ${error.message}`);
                // Network errors, etc.
            }
        }
    } else {
      console.log("No users to notify, skipping SendGrid calls.");
    }
    console.timeEnd('sendgrid-processing');

    // 6. Update last notification date ONLY for successfully notified users
    if (successfullyNotifiedUserIds.length > 0) {
        console.log(`Updating last_notification_sent_date to ${currentTimestamp} for ${successfullyNotifiedUserIds.length} successfully notified users.`);
        console.time('update-last-notification-date');
        const { error: updateError } = await supabase
            .from('user_profiles')
            .update({ last_notification_sent_date: currentTimestamp })
            .in('id', successfullyNotifiedUserIds);

        if (updateError) {
            // This is important to log, as it affects future runs
            console.error(`CRITICAL Error updating last_notification_sent_date: ${updateError.message}`);
        }
        console.timeEnd('update-last-notification-date');
    } else {
        console.log("No users were successfully notified, skipping date update.");
    }

    // --- Final Response ---
    const overallEndTime = performance.now();
    const totalDuration = (overallEndTime - overallStartTime).toFixed(2);
    console.log(`Notification function finished successfully. Total execution time: ${totalDuration}ms`);

    return new Response(JSON.stringify({
        success: true,
        message: `Processed notifications successfully in ${totalDuration}ms.`,
        stats: {
            totalUsersQueried,
            totalUsersEligibleForCheck,
            usersSuccessfullyNotified: successfullyNotifiedUserIds.length,
            // Calculate total articles sent based on successfully notified users
            totalArticlesSent: usersToNotify
                                 .filter(u => successfullyNotifiedUserIds.includes(u.id))
                                 .reduce((acc, user) => acc + user.articles.length, 0)
        }
    }), {
        headers: { 'Content-Type': 'application/json' },
        status: 200,
    });

  } catch (error) {
    const overallEndTime = performance.now();
    const totalDuration = (overallEndTime - overallStartTime).toFixed(2);
    console.error("Unhandled Function Error:", error);
    console.log(`Notification function failed after ${totalDuration}ms.`);
    // Avoid leaking detailed internal errors to the client if possible
    return new Response(JSON.stringify({
        success: false,
        error: "An internal server error occurred.",
        details: error.message // Optional: include message during development
    }), {
        headers: { 'Content-Type': 'application/json' },
        status: 500,
    });
  }
});

// --- Helper Functions (Unchanged logic, added types) ---

function getFrequencyLookbackDays(frequency: NotificationFrequency): number {
  switch (frequency) {
    case 'tous_les_jours': return 1;
    case 'tous_les_2_jours': return 2;
    case 'tous_les_3_jours': return 3;
    case '1_fois_par_semaine': return 7;
    case 'tous_les_15_jours': return 15;
    case '1_fois_par_mois': return 30;
    default:
        console.warn(`Unknown frequency in getFrequencyLookbackDays: ${frequency}. Defaulting to 0 days.`);
        return 0;
  }
}

function shouldSendNotification(
    frequency: NotificationFrequency,
    lastNotificationDate: string | null, // ISO string
    now: Date
): boolean {
    if (!lastNotificationDate) {
        // console.log(`User never notified (lastNotificationDate is null), eligible.`);
        return true; // Always eligible if never sent
    }

    try {
        const lastNotification = new Date(lastNotificationDate);
        const startOfLastNotificationDay = new Date(lastNotification);
        startOfLastNotificationDay.setUTCHours(0, 0, 0, 0); // Use UTC for consistency

        const startOfToday = new Date(now);
        startOfToday.setUTCHours(0, 0, 0, 0); // Use UTC

        // Calculate difference in milliseconds and convert to days (integer division)
        const msPerDay = 1000 * 60 * 60 * 24;
        const daysSinceLastNotification = Math.floor(
            (startOfToday.getTime() - startOfLastNotificationDay.getTime()) / msPerDay
        );

        // More robust check for minimum time passed (e.g., 16 hours for daily)
        const hoursSinceLastNotification = (now.getTime() - lastNotification.getTime()) / (1000 * 60 * 60);


        const currentDayOfWeek = now.getUTCDay(); // 0=Sun, 1=Mon (Use UTC day)
        const currentDayOfMonth = now.getUTCDate(); // 1-31 (Use UTC date)

        switch (frequency) {
            case 'tous_les_jours':
                // Must be at least the next day OR more than ~16 hours passed on the same day
                return daysSinceLastNotification >= 1 || hoursSinceLastNotification >= 16;
            case 'tous_les_2_jours':
                return daysSinceLastNotification >= 2;
            case 'tous_les_3_jours':
                return daysSinceLastNotification >= 3;
            case 'tous_les_15_jours':
                 return daysSinceLastNotification >= 15;
            case '1_fois_par_semaine':
                 // Must be at least 7 days AND it must be Monday (1)
                return daysSinceLastNotification >= 7 // && currentDayOfWeek === 1; // Removed day check - simple interval is often better
            case '1_fois_par_mois':
                 // Must be at least 30 days AND it must be the 1st of the month
                return daysSinceLastNotification >= 30 // && currentDayOfMonth === 1; // Removed day check
            default:
                console.warn(`Unknown frequency in shouldSendNotification: ${frequency}`);
                return false;
        }
    } catch (e) {
        console.error(`Error parsing date ${lastNotificationDate} in shouldSendNotification: ${e.message}`);
        return false; // Don't send if date is invalid
    }
}

function getMaxArticlesForFrequency(frequency: NotificationFrequency): number {
    // This determines how many articles the RPC function is ASKED to retrieve PER category
    switch (frequency) {
        case 'tous_les_jours': return 1; // Fetch slightly more in case of gaps? Adjust as needed.
        case 'tous_les_2_jours': return 1;
        case 'tous_les_3_jours': return 1;
        case '1_fois_par_semaine': return 7; // More generous limit for weekly+
        case 'tous_les_15_jours': return 15;
        case '1_fois_par_mois': return 30;
        default:
            console.warn(`Unknown frequency in getMaxArticlesForFrequency: ${frequency}. Defaulting to 0 articles.`);
            return 0;
    }
}


// import "jsr:@supabase/functions-js/edge-runtime.d.ts";
// import { createClient } from "jsr:@supabase/supabase-js@2";

// // --- Supabase Client Setup (Unchanged) ---
// const env = (key: string) => Deno.env.get(key);

// export function getSupabaseClient() {
//   const supabase = createClient(
//     env("SUPABASE_URL")!,
//     env("SUPABASE_SERVICE_ROLE_KEY")!
//   );
//   if (!supabase) {
//     throw new Error("Supabase failed to initialize");
//   }
//   return supabase;
// }

// // --- Constants (Unchanged) ---
// const USERS_BATCH_SIZE = 10;
// const SENDGRID_BATCH_SIZE = 10;
// const TWO_YEARS_AGO = new Date(Date.now() - 2 * 365 * 24 * 60 * 60 * 1000).toISOString();


// // --- Main Function ---
// Deno.serve(async (req: Request) => {
//   try {
//     console.time('total-execution');
//     const supabase = getSupabaseClient();
//     const usersToNotify: Array<{
//       id: string;
//       email: string;
//       first_name: string;
//       articles: any[]; // Structure defined later
//     }> = [];

//     let totalUsersQueried = 0;
//     let totalUsersEligible = 0;
//     let hasMoreUsers = true;
//     let lastUserId: string | null = null;
//     const now = new Date(); // Get current time once for consistency

//     console.time('users-processing');
//     while (hasMoreUsers) {
//       console.time('user-batch-query');
//       const query = supabase
//         .from('user_profiles')
//         .select('id, email, first_name, disciplines, notification_frequency, last_notification_sent_date')
//         .order('id')
//         // .eq('email', "alexis.chatelain123@gmail.com") // Testing filter
//         // .eq('email', "jperrama@gmail.com") // Testing filter
//         // .eq("email", "baptiste.mazas@gmail.com") // Testing filter
//         .limit(USERS_BATCH_SIZE);

//       if (lastUserId) {
//         query.gt('id', lastUserId);
//       }

//       const { data: userProfiles, error: userError } = await query;
//       console.timeEnd('user-batch-query');

//       if (userError) throw userError;

//       if (!userProfiles || userProfiles.length === 0) {
//         hasMoreUsers = false;
//         continue;
//       }

//       totalUsersQueried += userProfiles.length;
//       console.log(`Fetched batch of ${userProfiles.length} users`);

//       for (const user of userProfiles) {
//         console.time(`user-${user.id}-processing`);

//         // 1. Check if eligible based on time passed since last send (Unchanged)
//         if (!shouldSendNotification(user.notification_frequency, user.last_notification_sent_date, now)) {
//            console.log(`Skipping user ${user.email}: Too soon or wrong day for frequency ${user.notification_frequency}`);
//            console.timeEnd(`user-${user.id}-processing`);
//            continue;
//         }

//         totalUsersEligible++;
//         // --- MODIFICATION START: Rename limit variable ---
//         const maxArticlesPerCategory = getMaxArticlesForFrequency(user.notification_frequency);
//         // --- MODIFICATION END ---
//         const lookbackDays = getFrequencyLookbackDays(user.notification_frequency);

//         if (maxArticlesPerCategory === 0 || lookbackDays === 0) {
//             console.log(`Skipping user ${user.email}: Frequency ${user.notification_frequency} results in 0 limit or 0 lookback`);
//             console.timeEnd(`user-${user.id}-processing`);
//             continue;
//         }
//         if (!user.disciplines || user.disciplines.length === 0) {
//              console.log(`Skipping user ${user.email}: No disciplines selected`);
//              console.timeEnd(`user-${user.id}-processing`);
//              continue;
//         }

//         // 2. Calculate the start date for the article query (Unchanged)
//         const articleStartDate = new Date(now.getTime() - lookbackDays * 24 * 60 * 60 * 1000);
//         const articleStartDateISO = articleStartDate.toISOString();

//         // --- MODIFICATION START: Per-category article query ---
//         let allUserArticles: any[] = []; // Array to hold articles from all categories for this user

//         console.time(`user-${user.id}-all-article-queries`);
//         console.log(`Starting article fetch for user ${user.email}. Lookback: ${lookbackDays} days (${articleStartDateISO}), Limit per category: ${maxArticlesPerCategory}`);

//         for (const discipline of user.disciplines) {
//             console.time(`user-${user.id}-article-query-${discipline}`);
//             const articleQuery = supabase
//               .from('showed_articles')
//               .select(`
//                 article_id,
//                 discipline,
//                 added_at,
//                 link,
//                 articles!inner (
//                   id,
//                   title,
//                   content,
//                   journal,
//                   published_at
//                 )
//               `)
//               .eq('discipline', discipline) // Filter by current discipline
//               .gte('articles.published_at', TWO_YEARS_AGO)
//               .gte('added_at', articleStartDateISO)
//               .order('added_at', { ascending: false })
//               .limit(maxArticlesPerCategory); // Apply limit per category

//             // console.log(`Querying articles for user ${user.email}, discipline: ${discipline}`); // Optional: more verbose logging

//             const { data: articlesForDiscipline, error: articleError } = await articleQuery;
//             console.timeEnd(`user-${user.id}-article-query-${discipline}`);

//             if (articleError) {
//                 console.error(`Error fetching articles for user ${user.email}, discipline ${discipline}: ${articleError.message}`);
//                 // Continue to the next discipline even if one fails
//             } else if (articlesForDiscipline && articlesForDiscipline.length > 0) {
//                 console.log(`Found ${articlesForDiscipline.length} articles for user ${user.email} in discipline: ${discipline}`);
//                 allUserArticles.push(...articlesForDiscipline); // Add found articles to the main list
//             } else {
//                  console.log(`No articles found for user ${user.email} in discipline: ${discipline} within lookback period.`);
//             }
//         }
//         console.timeEnd(`user-${user.id}-all-article-queries`);
//         console.log(`Finished querying all ${user.disciplines.length} disciplines for user ${user.email}. Found a total of ${allUserArticles.length} articles.`);

//         // 4. Add user to notification list ONLY if articles were found across ANY relevant discipline
//         if (allUserArticles.length > 0) {
//            // Optional: Sort all collected articles by added_at date descending
//            allUserArticles.sort((a, b) => new Date(b.added_at).getTime() - new Date(a.added_at).getTime());

//            const articlesJson = allUserArticles.map(article => ({
//               id: article.articles.id,
//               title: article.articles.title,
//               journal: article.articles.journal || 'Inconnu',
//               discipline: article.discipline,
//               added_at: article.added_at,
//               link: article.link || ''
//             }));

//           usersToNotify.push({
//             id: user.id,
//             email: user.email,
//             first_name: user.first_name,
//             articles: articlesJson
//           });
//           console.log(`Added user ${user.email} to notification list with ${articlesJson.length} articles from ${user.disciplines.length} checked disciplines.`);
//         } else {
//             console.log(`No articles found across any specified disciplines within the last ${lookbackDays} days for user ${user.email}. Skipping notification.`);
//         }
//         // --- MODIFICATION END ---
//         console.timeEnd(`user-${user.id}-processing`);
//       } // End user loop

//       if (userProfiles.length > 0) {
//         lastUserId = userProfiles[userProfiles.length - 1].id;
//       }
//       hasMoreUsers = userProfiles.length === USERS_BATCH_SIZE;
//     } // End while(hasMoreUsers) loop
//     console.timeEnd('users-processing');
//     console.log(`Finished processing users. Eligible for check today: ${totalUsersEligible}, Found articles for: ${usersToNotify.length}`);

//     // 5. Send notifications (Unchanged)
//     let emailsSentSuccessfully = 0;
//     const successfullyNotifiedUserIds: string[] = [];
//     const currentTimestamp = new Date().toISOString();

//     console.time('sendgrid-processing');
//     for (let i = 0; i < usersToNotify.length; i += SENDGRID_BATCH_SIZE) {
//         const batch = usersToNotify.slice(i, i + SENDGRID_BATCH_SIZE);
//         const batchUserIds = batch.map(user => user.id);

//         try {
//             console.time(`sendgrid-batch-${i}`);
//             const response = await fetch("https://api.sendgrid.com/v3/mail/send", {
//             method: "POST",
//             headers: {
//                 Authorization: `Bearer ${Deno.env.get("SENDGRID_API_KEY")}`,
//                 "Content-Type": "application/json",
//             },
//             body: JSON.stringify({
//                 personalizations: batch.map(user => ({
//                 to: [{ email: user.email }],
//                 dynamic_template_data: {
//                     first_name: user.first_name,
//                     articles: user.articles.map((article) => ({
//                       id: article.id,
//                       title: article.title,
//                       journal: article.journal || "Inconnu",
//                       discipline: article.discipline || "Non spécifié",
//                       link: article.link
//                     })),
//                 },
//                 })),
//                 from: {
//                 email: "contact@veillemedicale.fr",
//                 name: "Veille Médicale",
//                 },
//                 asm: {
//                   group_id: 303981,
//                   groups_to_display: [303981],
//                 },
//                 template_id: "d-27f89a4f0faa4df1ab83b9fbc7be19a1",
//             }),
//             });
//             console.timeEnd(`sendgrid-batch-${i}`);

//             if (!response.ok) {
//             console.error(`Failed SendGrid batch. Status: ${response.status}, ${await response.text()}`);
//             } else {
//             console.log(`Successfully sent SendGrid request for batch of ${batch.length} users`);
//             emailsSentSuccessfully += batch.length;
//             successfullyNotifiedUserIds.push(...batchUserIds);
//             }
//         } catch (error) {
//             console.timeEnd(`sendgrid-batch-${i}`);
//             console.error(`Error sending SendGrid batch: ${error.message}`);
//         }
//     }
//     console.timeEnd('sendgrid-processing');

//     // 6. Update last notification date ONLY for successfully notified users (Unchanged)
//     if (successfullyNotifiedUserIds.length > 0) {
//         console.log(`Updating last_notification_sent_date to ${currentTimestamp} for ${successfullyNotifiedUserIds.length} users.`);
//         console.time('update-last-notification-date');
//         const { error: updateError } = await supabase
//           .from('user_profiles')
//           .update({ last_notification_sent_date: currentTimestamp })
//           .in('id', successfullyNotifiedUserIds);

//         if (updateError) {
//             console.error(`Error updating last_notification_sent_date: ${updateError.message}`);
//         }
//         console.timeEnd('update-last-notification-date');
//     } else {
//         console.log("No users were successfully notified, skipping date update.");
//     }

//     // --- Response (Unchanged) ---
//     console.timeEnd('total-execution');
//     return new Response(JSON.stringify({
//       success: true,
//       stats: {
//         totalUsersQueried,
//         totalUsersEligibleForCheck: totalUsersEligible,
//         usersNotified: successfullyNotifiedUserIds.length,
//         totalArticlesSent: usersToNotify
//             .filter(u => successfullyNotifiedUserIds.includes(u.id))
//             .reduce((acc, user) => acc + user.articles.length, 0),
//       }
//     }), {
//       headers: { 'Content-Type': 'application/json' },
//       status: 200,
//     });

//   } catch (error) {
//     console.error("Function error:", error);
//     console.timeEnd('total-execution');
//     return new Response(JSON.stringify({ error: error.message }), {
//       headers: { 'Content-Type': 'application/json' },
//       status: 500,
//     });
//   }
// });

// // --- Helper Functions (Unchanged) ---

// /**
//  * Determines the lookback period in days based on frequency.
//  */
// function getFrequencyLookbackDays(frequency: string): number {
//   switch (frequency) {
//     case 'tous_les_jours':
//       return 1; // Look back 1 day
//     case 'tous_les_2_jours':
//       return 2; // Look back 2 days
//     case 'tous_les_3_jours':
//       return 3; // Look back 3 days
//     case '1_fois_par_semaine':
//       return 7; // Look back 7 days
//     case 'tous_les_15_jours':
//       return 15;
//     case '1_fois_par_mois':
//       return 30;
//     default:
//       return 0; // Don't look back for unknown frequency
//   }
// }

// /**
//  * Checks if enough time has passed OR if it's the designated day/date
//  * to send a notification based on frequency.
//  * Accepts 'now' parameter for consistency.
//  */
// function shouldSendNotification(frequency: string, lastNotificationDate: string | null, now: Date): boolean {
//   // Always send if never sent before, the article query will handle the lookback.
//   if (!lastNotificationDate) return true;

//   const lastNotification = new Date(lastNotificationDate);
//   const startOfLastNotificationDay = new Date(lastNotification);
//   startOfLastNotificationDay.setHours(0, 0, 0, 0);

//   // Use the 'now' passed into the function
//   const startOfToday = new Date(now);
//   startOfToday.setHours(0, 0, 0, 0);

//   const hoursSinceLastNotification = Math.floor(
//     (now.getTime() - lastNotification.getTime()) / (1000 * 60 * 60)
//   );

//   const daysSinceLastNotification = Math.floor(
//     (startOfToday.getTime() - startOfLastNotificationDay.getTime()) / (1000 * 60 * 60 * 24)
//   );

//   const currentDayOfWeek = now.getDay(); // 0=Sun, 1=Mon
//   const currentDayOfMonth = now.getDate(); // 1-31

//   switch (frequency) {
//     case 'tous_les_jours':
//       return daysSinceLastNotification >= 1 || hoursSinceLastNotification >= 16;
//     case 'tous_les_2_jours':
//       return daysSinceLastNotification >= 2;
//     case 'tous_les_3_jours':
//       return daysSinceLastNotification >= 3;
//     case 'tous_les_15_jours':
//          return daysSinceLastNotification >= 15;
//     case '1_fois_par_semaine':
//       return daysSinceLastNotification >= 7 && currentDayOfWeek === 1;
//     case '1_fois_par_mois':
//       return daysSinceLastNotification >= 30 && currentDayOfMonth === 1;
//     default:
//       console.warn(`Unknown frequency in shouldSendNotification: ${frequency}`);
//       return false;
//   }
// }

// /**
//  * Returns the maximum number of articles to FETCH PER CATEGORY for a given frequency.
//  * (Name is slightly misleading now, but function logic matches requirement)
//  */
// function getMaxArticlesForFrequency(frequency: string): number {
//   switch (frequency) {
//     case 'tous_les_jours':
//       return 1;
//     case 'tous_les_2_jours':
//       return 1;
//     case 'tous_les_3_jours':
//       return 1;
//     case '1_fois_par_semaine':
//       return 7;
//     case 'tous_les_15_jours':
//       return 15;
//     case '1_fois_par_mois':
//       return 30;
//     default:
//       return 0;
//   }
// }