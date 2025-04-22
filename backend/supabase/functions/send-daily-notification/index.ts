import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
// --- Supabase Client Setup ---
const env = (key)=>{
  const value = Deno.env.get(key);
  if (!value) throw new Error(`Environment variable ${key} not set!`);
  return value;
};
function getSupabaseClient() {
  const supabase = createClient(env("SUPABASE_URL"), env("SUPABASE_SERVICE_ROLE_KEY"));
  if (!supabase) throw new Error("Supabase client failed to initialize");
  return supabase;
}
// --- Constants ---
const USERS_BATCH_SIZE = 50;
const SENDGRID_BATCH_SIZE = 100;
// --- Main Function ---
Deno.serve(async (_req)=>{
  const overallStartTime = performance.now();
  console.log("Notification function started (V4 - RPC handles subscriptions)...");
  try {
    const supabase = getSupabaseClient();
    const usersToNotify = [];
    let totalUsersQueried = 0;
    let totalUsersEligibleForCheck = 0;
    let hasMoreUsers = true;
    let lastUserId = null;
    const now = new Date();
    console.time('users-processing-total');
    while(hasMoreUsers){
      const batchFetchStartTime = performance.now();
      console.time(`user-batch-fetch-${lastUserId || 'initial'}`);
      // Fetch user profiles (no disciplines needed)
      const query = supabase.from('user_profiles').select('id, email, first_name, notification_frequency, last_notification_sent_date')//.eq("email", "alexis.chatelain123@gmail.com") // Uncomment for testing specific users
      .order('id').limit(USERS_BATCH_SIZE);
      if (lastUserId) query.gt('id', lastUserId);
      const { data: userProfiles, error: userError } = await query;
      console.timeEnd(`user-batch-fetch-${lastUserId || 'initial'}`);
      if (userError) throw userError;
      if (!userProfiles || userProfiles.length === 0) {
        hasMoreUsers = false;
        continue;
      }
      totalUsersQueried += userProfiles.length;
      const batchFetchEndTime = performance.now();
      console.log(`Fetched batch of ${userProfiles.length}. Time: ${(batchFetchEndTime - batchFetchStartTime).toFixed(2)}ms. Processing...`);
      console.time(`user-batch-processing-${lastUserId || 'initial'}`);
      const batchProcessingPromises = userProfiles.map(async (user)=>{
        // 1. Check eligibility
        if (!shouldSendNotification(user.notification_frequency, user.last_notification_sent_date, now)) {
          return null;
        }
        const maxArticlesPerCategory = getMaxArticlesForFrequency(user.notification_frequency);
        const lookbackDays = getFrequencyLookbackDays(user.notification_frequency);
        if (maxArticlesPerCategory === 0 || lookbackDays === 0) {
          return 'eligible_no_articles';
        }
        // 2. Calculate start date
        const articleStartDate = new Date(now.getTime() - lookbackDays * 24 * 60 * 60 * 1000);
        const articleStartDateISO = articleStartDate.toISOString();
        // 3. Call the MODIFIED RPC function with user ID
        let articlesForUser = null;
        try {
          console.time(`user-${user.id}-rpc-call`);
          const { data: rpcData, error: rpcError } = await supabase.rpc('get_ranked_articles_for_user_notification', {
            p_user_id: user.id,
            p_start_date: articleStartDateISO,
            p_articles_per_category: maxArticlesPerCategory // Pass the limit
          });
          console.timeEnd(`user-${user.id}-rpc-call`);
          if (rpcError) {
            console.error(`RPC Error for user ${user.email} (ID: ${user.id}): ${rpcError.message}`);
            return null;
          }
          articlesForUser = rpcData;
        } catch (e) {
          console.error(`Exception during RPC call for user ${user.email} (ID: ${user.id}): ${e.message}`);
          console.timeEnd(`user-${user.id}-rpc-call`);
          return null;
        }
        // 4. Process RPC results
        if (articlesForUser && articlesForUser.length > 0) {
          // Map RPC output, using matched_category_name for display
          const articlesJson = articlesForUser.map((article)=>({
              id: article.article_id_out,
              title: article.title_out || 'Titre inconnu',
              journal: article.journal_out || 'Journal inconnu',
              discipline: article.matched_category_name || 'Non spécifié',
              link: article.link_out || ''
            }));
          // Deduplicate based on article ID *within this user's result*
          const seenArticleIds = new Set();
          const uniqueArticlesJson = articlesJson.filter((a)=>{
            if (seenArticleIds.has(a.id)) return false;
            seenArticleIds.add(a.id);
            return true;
          });
          if (uniqueArticlesJson.length === 0) {
            // console.log(`No unique articles found via RPC for user ${user.email} after dedupe.`);
            return 'eligible_no_articles';
          }
          return {
            id: user.id,
            email: user.email,
            first_name: user.first_name || 'Cher utilisateur',
            articles: uniqueArticlesJson
          };
        } else {
          // console.log(`No articles returned by RPC for user ${user.email}.`);
          return 'eligible_no_articles';
        }
      }); // End map
      // Process batch results
      const batchResults = await Promise.all(batchProcessingPromises);
      console.timeEnd(`user-batch-processing-${lastUserId || 'initial'}`);
      let batchAddedToNotify = 0;
      let batchEligibleCount = 0;
      for (const result of batchResults){
        if (result === 'eligible_no_articles') batchEligibleCount++;
        else if (result) {
          batchEligibleCount++;
          usersToNotify.push(result);
          batchAddedToNotify++;
        }
      }
      totalUsersEligibleForCheck += batchEligibleCount;
      console.log(`Finished batch processing. Eligible: ${batchEligibleCount}, Added to notify: ${batchAddedToNotify}`);
      if (userProfiles.length > 0) lastUserId = userProfiles[userProfiles.length - 1].id;
      hasMoreUsers = userProfiles.length === USERS_BATCH_SIZE;
    } // End while
    console.timeEnd('users-processing-total');
    console.log(`Finished user processing. Total Eligible: ${totalUsersEligibleForCheck}, To Notify: ${usersToNotify.length}`);
    // --- Send notifications via SendGrid (Batched) ---
    let emailsSentSuccessfully = 0;
    const successfullyNotifiedUserIds = [];
    const currentTimestamp = new Date().toISOString();
    console.time('sendgrid-processing');
    if (usersToNotify.length > 0) {
      for(let i = 0; i < usersToNotify.length; i += SENDGRID_BATCH_SIZE){
        const batch = usersToNotify.slice(i, i + SENDGRID_BATCH_SIZE);
        const batchToSend = batch.filter((user)=>user.articles.length > 0);
        const finalBatchUserIds = batchToSend.map((user)=>user.id);
        if (batchToSend.length === 0) continue;
        const sendGridPayload = {
          personalizations: batchToSend.map((user)=>({
              to: [
                {
                  email: user.email
                }
              ],
              dynamic_template_data: {
                first_name: user.first_name,
                articles: user.articles.map((a)=>({
                    id: a.id,
                    title: a.title,
                    journal: a.journal,
                    discipline: a.discipline,
                    link: a.link
                  }))
              }
            })),
          from: {
            email: "contact@veillemedicale.fr",
            name: "Veille Médicale"
          },
          asm: {
            group_id: 303981,
            groups_to_display: [
              303981
            ]
          },
          template_id: "d-27f89a4f0faa4df1ab83b9fbc7be19a1"
        };
        try {
          console.time(`sendgrid-batch-${i}`);
          const response = await fetch("https://api.sendgrid.com/v3/mail/send", {
            method: "POST",
            headers: {
              Authorization: `Bearer ${env("SENDGRID_API_KEY")}`,
              "Content-Type": "application/json"
            },
            body: JSON.stringify(sendGridPayload)
          });
          console.timeEnd(`sendgrid-batch-${i}`);
          if (!response.ok) {
            const errorBody = await response.text();
            console.error(`Failed SendGrid batch ${i}. Status: ${response.status}, Body: ${errorBody}`);
          } else {
            console.log(`Sent SendGrid batch ${i} for ${batchToSend.length} users. Status: ${response.status}`);
            emailsSentSuccessfully += batchToSend.length;
            successfullyNotifiedUserIds.push(...finalBatchUserIds);
          }
        } catch (error) {
          console.timeEnd(`sendgrid-batch-${i}`);
          console.error(`Error sending SendGrid batch ${i}: ${error.message}`);
        }
      }
    } else {
      console.log("No users to notify.");
    }
    console.timeEnd('sendgrid-processing');
    // --- Update last notification date ---
    if (successfullyNotifiedUserIds.length > 0) {
      console.log(`Updating last_notification_sent_date for ${successfullyNotifiedUserIds.length} users.`);
      console.time('update-last-notification-date');
      const { error: updateError } = await supabase.from('user_profiles').update({
        last_notification_sent_date: currentTimestamp
      }).in('id', successfullyNotifiedUserIds);
      if (updateError) console.error(`CRITICAL Error updating dates: ${updateError.message}`);
      console.timeEnd('update-last-notification-date');
    } else {
      console.log("No date updates needed.");
    }
    // --- Final Response ---
    const overallEndTime = performance.now();
    const totalDuration = (overallEndTime - overallStartTime).toFixed(2);
    console.log(`Notification function finished successfully. Total time: ${totalDuration}ms`);
    return new Response(JSON.stringify({
      success: true,
      message: `Processed notifications in ${totalDuration}ms.`,
      stats: {
        totalUsersQueried,
        totalUsersEligibleForCheck,
        usersSuccessfullyNotified: successfullyNotifiedUserIds.length,
        totalArticlesSent: usersToNotify.filter((u)=>successfullyNotifiedUserIds.includes(u.id)).reduce((acc, user)=>acc + user.articles.length, 0)
      }
    }), {
      headers: {
        'Content-Type': 'application/json'
      },
      status: 200
    });
  } catch (error) {
    const overallEndTime = performance.now();
    const totalDuration = (overallEndTime - overallStartTime).toFixed(2);
    console.error("Unhandled Function Error:", error);
    console.log(`Notification function failed after ${totalDuration}ms.`);
    return new Response(JSON.stringify({
      success: false,
      error: "Internal server error.",
      details: error.message
    }), {
      headers: {
        'Content-Type': 'application/json'
      },
      status: 500
    });
  }
});
// --- Helper Functions (Unchanged) ---
function getFrequencyLookbackDays(frequency) {
  switch(frequency){
    case 'tous_les_jours':
      return 1;
    case 'tous_les_2_jours':
      return 2;
    case 'tous_les_3_jours':
      return 3;
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
function shouldSendNotification(frequency, lastNotificationDate, now) {
  if (!lastNotificationDate) return true;
  try {
    const lastNotification = new Date(lastNotificationDate);
    const startOfLastNotificationDay = new Date(lastNotification);
    startOfLastNotificationDay.setUTCHours(0, 0, 0, 0);
    const startOfToday = new Date(now);
    startOfToday.setUTCHours(0, 0, 0, 0);
    const msPerDay = 1000 * 60 * 60 * 24;
    const daysSinceLastNotification = Math.floor((startOfToday.getTime() - startOfLastNotificationDay.getTime()) / msPerDay);
    const hoursSinceLastNotification = (now.getTime() - lastNotification.getTime()) / (1000 * 60 * 60);
    switch(frequency){
      case 'tous_les_jours':
        return daysSinceLastNotification >= 1 || hoursSinceLastNotification >= 16;
      case 'tous_les_2_jours':
        return daysSinceLastNotification >= 2;
      case 'tous_les_3_jours':
        return daysSinceLastNotification >= 3;
      case '1_fois_par_semaine':
        return daysSinceLastNotification >= 7;
      case 'tous_les_15_jours':
        return daysSinceLastNotification >= 15;
      case '1_fois_par_mois':
        return daysSinceLastNotification >= 30;
      default:
        return false;
    }
  } catch (e) {
    console.error(`Error parsing date ${lastNotificationDate} in shouldSendNotification: ${e.message}`);
    return false;
  }
}
function getMaxArticlesForFrequency(frequency) {
  switch(frequency){
    case 'tous_les_jours':
      return 1;
    case 'tous_les_2_jours':
      return 1;
    case 'tous_les_3_jours':
      return 1;
    case '1_fois_par_semaine':
      return 7; // Allow fetching more for less frequent sends
    case 'tous_les_15_jours':
      return 15;
    case '1_fois_par_mois':
      return 30;
    default:
      return 0;
  }
}
