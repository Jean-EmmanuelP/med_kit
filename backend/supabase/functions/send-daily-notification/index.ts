import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

// --- Supabase Client Setup (Unchanged) ---
const env = (key: string) => Deno.env.get(key);

export function getSupabaseClient() {
  const supabase = createClient(
    env("SUPABASE_URL")!,
    env("SUPABASE_SERVICE_ROLE_KEY")!
  );
  if (!supabase) {
    throw new Error("Supabase failed to initialize");
  }
  return supabase;
}

// --- Constants (Unchanged) ---
const USERS_BATCH_SIZE = 10;
const SENDGRID_BATCH_SIZE = 10;
const TWO_YEARS_AGO = new Date(Date.now() - 2 * 365 * 24 * 60 * 60 * 1000).toISOString();


// --- Main Function ---
Deno.serve(async (req: Request) => {
  try {
    console.time('total-execution');
    const supabase = getSupabaseClient();
    const usersToNotify: Array<{
      id: string;
      email: string;
      first_name: string;
      articles: any[]; // Structure defined later
    }> = [];

    let totalUsersQueried = 0;
    let totalUsersEligible = 0;
    let hasMoreUsers = true;
    let lastUserId: string | null = null;
    const now = new Date(); // Get current time once for consistency

    console.time('users-processing');
    while (hasMoreUsers) {
      console.time('user-batch-query');
      const query = supabase
        .from('user_profiles')
        .select('id, email, first_name, disciplines, notification_frequency, last_notification_sent_date')
        .order('id')
        // .eq('email', "alexis.chatelain123@gmail.com") // Testing filter
        // .eq('email', "jperrama@gmail.com") // Testing filter
        .limit(USERS_BATCH_SIZE);

      if (lastUserId) {
        query.gt('id', lastUserId);
      }

      const { data: userProfiles, error: userError } = await query;
      console.timeEnd('user-batch-query');

      if (userError) throw userError;

      if (!userProfiles || userProfiles.length === 0) {
        hasMoreUsers = false;
        continue;
      }

      totalUsersQueried += userProfiles.length;
      console.log(`Fetched batch of ${userProfiles.length} users`);

      for (const user of userProfiles) {
        console.time(`user-${user.id}-processing`);

        // 1. Check if eligible based on time passed since last send (Unchanged)
        if (!shouldSendNotification(user.notification_frequency, user.last_notification_sent_date, now)) {
           console.log(`Skipping user ${user.email}: Too soon or wrong day for frequency ${user.notification_frequency}`);
           console.timeEnd(`user-${user.id}-processing`);
           continue;
        }

        totalUsersEligible++;
        // --- MODIFICATION START: Rename limit variable ---
        const maxArticlesPerCategory = getMaxArticlesForFrequency(user.notification_frequency);
        // --- MODIFICATION END ---
        const lookbackDays = getFrequencyLookbackDays(user.notification_frequency);

        if (maxArticlesPerCategory === 0 || lookbackDays === 0) {
            console.log(`Skipping user ${user.email}: Frequency ${user.notification_frequency} results in 0 limit or 0 lookback`);
            console.timeEnd(`user-${user.id}-processing`);
            continue;
        }
        if (!user.disciplines || user.disciplines.length === 0) {
             console.log(`Skipping user ${user.email}: No disciplines selected`);
             console.timeEnd(`user-${user.id}-processing`);
             continue;
        }

        // 2. Calculate the start date for the article query (Unchanged)
        const articleStartDate = new Date(now.getTime() - lookbackDays * 24 * 60 * 60 * 1000);
        const articleStartDateISO = articleStartDate.toISOString();

        // --- MODIFICATION START: Per-category article query ---
        let allUserArticles: any[] = []; // Array to hold articles from all categories for this user

        console.time(`user-${user.id}-all-article-queries`);
        console.log(`Starting article fetch for user ${user.email}. Lookback: ${lookbackDays} days (${articleStartDateISO}), Limit per category: ${maxArticlesPerCategory}`);

        for (const discipline of user.disciplines) {
            console.time(`user-${user.id}-article-query-${discipline}`);
            const articleQuery = supabase
              .from('showed_articles')
              .select(`
                article_id,
                discipline,
                added_at,
                link,
                articles!inner (
                  id,
                  title,
                  content,
                  journal,
                  published_at
                )
              `)
              .eq('discipline', discipline) // Filter by current discipline
              .gte('articles.published_at', TWO_YEARS_AGO)
              .gte('added_at', articleStartDateISO)
              .order('added_at', { ascending: false })
              .limit(maxArticlesPerCategory); // Apply limit per category

            // console.log(`Querying articles for user ${user.email}, discipline: ${discipline}`); // Optional: more verbose logging

            const { data: articlesForDiscipline, error: articleError } = await articleQuery;
            console.timeEnd(`user-${user.id}-article-query-${discipline}`);

            if (articleError) {
                console.error(`Error fetching articles for user ${user.email}, discipline ${discipline}: ${articleError.message}`);
                // Continue to the next discipline even if one fails
            } else if (articlesForDiscipline && articlesForDiscipline.length > 0) {
                console.log(`Found ${articlesForDiscipline.length} articles for user ${user.email} in discipline: ${discipline}`);
                allUserArticles.push(...articlesForDiscipline); // Add found articles to the main list
            } else {
                 console.log(`No articles found for user ${user.email} in discipline: ${discipline} within lookback period.`);
            }
        }
        console.timeEnd(`user-${user.id}-all-article-queries`);
        console.log(`Finished querying all ${user.disciplines.length} disciplines for user ${user.email}. Found a total of ${allUserArticles.length} articles.`);

        // 4. Add user to notification list ONLY if articles were found across ANY relevant discipline
        if (allUserArticles.length > 0) {
           // Optional: Sort all collected articles by added_at date descending
           allUserArticles.sort((a, b) => new Date(b.added_at).getTime() - new Date(a.added_at).getTime());

           const articlesJson = allUserArticles.map(article => ({
              id: article.articles.id,
              title: article.articles.title,
              journal: article.articles.journal || 'Inconnu',
              discipline: article.discipline,
              added_at: article.added_at,
              link: article.link || ''
            }));

          usersToNotify.push({
            id: user.id,
            email: user.email,
            first_name: user.first_name,
            articles: articlesJson
          });
          console.log(`Added user ${user.email} to notification list with ${articlesJson.length} articles from ${user.disciplines.length} checked disciplines.`);
        } else {
            console.log(`No articles found across any specified disciplines within the last ${lookbackDays} days for user ${user.email}. Skipping notification.`);
        }
        // --- MODIFICATION END ---
        console.timeEnd(`user-${user.id}-processing`);
      } // End user loop

      if (userProfiles.length > 0) {
        lastUserId = userProfiles[userProfiles.length - 1].id;
      }
      hasMoreUsers = userProfiles.length === USERS_BATCH_SIZE;
    } // End while(hasMoreUsers) loop
    console.timeEnd('users-processing');
    console.log(`Finished processing users. Eligible for check today: ${totalUsersEligible}, Found articles for: ${usersToNotify.length}`);

    // 5. Send notifications (Unchanged)
    let emailsSentSuccessfully = 0;
    const successfullyNotifiedUserIds: string[] = [];
    const currentTimestamp = new Date().toISOString();

    console.time('sendgrid-processing');
    for (let i = 0; i < usersToNotify.length; i += SENDGRID_BATCH_SIZE) {
        const batch = usersToNotify.slice(i, i + SENDGRID_BATCH_SIZE);
        const batchUserIds = batch.map(user => user.id);

        try {
            console.time(`sendgrid-batch-${i}`);
            const response = await fetch("https://api.sendgrid.com/v3/mail/send", {
            method: "POST",
            headers: {
                Authorization: `Bearer ${Deno.env.get("SENDGRID_API_KEY")}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                personalizations: batch.map(user => ({
                to: [{ email: user.email }],
                dynamic_template_data: {
                    first_name: user.first_name,
                    articles: user.articles.map((article) => ({
                      id: article.id,
                      title: article.title,
                      journal: article.journal || "Inconnu",
                      discipline: article.discipline || "Non spécifié",
                      link: article.link
                    })),
                },
                })),
                from: {
                email: "contact@veillemedicale.fr",
                name: "Veille Médicale",
                },
                template_id: "d-27f89a4f0faa4df1ab83b9fbc7be19a1",
            }),
            });
            console.timeEnd(`sendgrid-batch-${i}`);

            if (!response.ok) {
            console.error(`Failed SendGrid batch. Status: ${response.status}, ${await response.text()}`);
            } else {
            console.log(`Successfully sent SendGrid request for batch of ${batch.length} users`);
            emailsSentSuccessfully += batch.length;
            successfullyNotifiedUserIds.push(...batchUserIds);
            }
        } catch (error) {
            console.timeEnd(`sendgrid-batch-${i}`);
            console.error(`Error sending SendGrid batch: ${error.message}`);
        }
    }
    console.timeEnd('sendgrid-processing');

    // 6. Update last notification date ONLY for successfully notified users (Unchanged)
    if (successfullyNotifiedUserIds.length > 0) {
        console.log(`Updating last_notification_sent_date to ${currentTimestamp} for ${successfullyNotifiedUserIds.length} users.`);
        console.time('update-last-notification-date');
        const { error: updateError } = await supabase
          .from('user_profiles')
          .update({ last_notification_sent_date: currentTimestamp })
          .in('id', successfullyNotifiedUserIds);

        if (updateError) {
            console.error(`Error updating last_notification_sent_date: ${updateError.message}`);
        }
        console.timeEnd('update-last-notification-date');
    } else {
        console.log("No users were successfully notified, skipping date update.");
    }

    // --- Response (Unchanged) ---
    console.timeEnd('total-execution');
    return new Response(JSON.stringify({
      success: true,
      stats: {
        totalUsersQueried,
        totalUsersEligibleForCheck: totalUsersEligible,
        usersNotified: successfullyNotifiedUserIds.length,
        totalArticlesSent: usersToNotify
            .filter(u => successfullyNotifiedUserIds.includes(u.id))
            .reduce((acc, user) => acc + user.articles.length, 0),
      }
    }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    });

  } catch (error) {
    console.error("Function error:", error);
    console.timeEnd('total-execution');
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { 'Content-Type': 'application/json' },
      status: 500,
    });
  }
});

// --- Helper Functions (Unchanged) ---

/**
 * Determines the lookback period in days based on frequency.
 */
function getFrequencyLookbackDays(frequency: string): number {
  switch (frequency) {
    case 'tous_les_jours':
      return 1; // Look back 1 day
    case 'tous_les_2_jours':
      return 2; // Look back 2 days
    case 'tous_les_3_jours':
      return 3; // Look back 3 days
    case '1_fois_par_semaine':
      return 7; // Look back 7 days
    case 'tous_les_15_jours':
      return 15;
    case '1_fois_par_mois':
      return 30;
    default:
      return 0; // Don't look back for unknown frequency
  }
}

/**
 * Checks if enough time has passed OR if it's the designated day/date
 * to send a notification based on frequency.
 * Accepts 'now' parameter for consistency.
 */
function shouldSendNotification(frequency: string, lastNotificationDate: string | null, now: Date): boolean {
  // Always send if never sent before, the article query will handle the lookback.
  if (!lastNotificationDate) return true;

  const lastNotification = new Date(lastNotificationDate);
  const startOfLastNotificationDay = new Date(lastNotification);
  startOfLastNotificationDay.setHours(0, 0, 0, 0);

  // Use the 'now' passed into the function
  const startOfToday = new Date(now);
  startOfToday.setHours(0, 0, 0, 0);

  const hoursSinceLastNotification = Math.floor(
    (now.getTime() - lastNotification.getTime()) / (1000 * 60 * 60)
  );

  const daysSinceLastNotification = Math.floor(
    (startOfToday.getTime() - startOfLastNotificationDay.getTime()) / (1000 * 60 * 60 * 24)
  );

  const currentDayOfWeek = now.getDay(); // 0=Sun, 1=Mon
  const currentDayOfMonth = now.getDate(); // 1-31

  switch (frequency) {
    case 'tous_les_jours':
      return daysSinceLastNotification >= 1 || hoursSinceLastNotification >= 16;
    case 'tous_les_2_jours':
      return daysSinceLastNotification >= 2;
    case 'tous_les_3_jours':
      return daysSinceLastNotification >= 3;
    case 'tous_les_15_jours':
         return daysSinceLastNotification >= 15;
    case '1_fois_par_semaine':
      return daysSinceLastNotification >= 7 && currentDayOfWeek === 1;
    case '1_fois_par_mois':
      return daysSinceLastNotification >= 30 && currentDayOfMonth === 1;
    default:
      console.warn(`Unknown frequency in shouldSendNotification: ${frequency}`);
      return false;
  }
}

/**
 * Returns the maximum number of articles to FETCH PER CATEGORY for a given frequency.
 * (Name is slightly misleading now, but function logic matches requirement)
 */
function getMaxArticlesForFrequency(frequency: string): number {
  switch (frequency) {
    case 'tous_les_jours':
      return 1;
    case 'tous_les_2_jours':
      return 1;
    case 'tous_les_3_jours':
      return 1;
    case '1_fois_par_semaine':
      return 7;
    case 'tous_les_15_jours':
      return 15;
    case '1_fois_par_mois':
      return 30;
    default:
      return 0;
  }
}