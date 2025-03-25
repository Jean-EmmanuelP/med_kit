import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

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

const USERS_BATCH_SIZE = 10; // Adjust this number based on your needs

Deno.serve(async (req: Request) => {
  try {
    console.time('total-execution');
    const supabase = getSupabaseClient();
    const usersToNotify: Array<{
      email: string;
      first_name: string;
      articles: any[];
    }> = [];

    let totalUsersQueried = 0;
    let hasMoreUsers = true;
    let lastUserId: string | null = null;

    console.time('users-processing');
    while (hasMoreUsers) {
      console.time('user-batch-query');
      // Get users in batches
      const query = supabase
        .from('user_profiles')
        .select('*')
        .order('id')
        // .eq('email', "alexis.chatelain123@gmail.com")
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
      console.log(`Processing batch of ${userProfiles.length} users`);

      // Process each batch of users
      for (const user of userProfiles) {
        console.time(`user-${user.id}-processing`);
        const articlesJson: any[] = [];
        let articleCount = 0;
        const articleLimit = getArticleLimit(user.notification_frequency, user.last_notification_sent_date);

        // Process each discipline for the user
        console.log(`Processing ${user.disciplines.length} disciplines for user ${user.email}`);
        for (const discipline of user.disciplines) {
          console.time(`discipline-${discipline}-query`);
          const { data: articles, error: articleError } = await supabase
            .from('showed_articles')
            .select(`
              article_id,
              added_at,
              link,
              articles!inner (
                id,
                title,
                content,
                journal,
                disciplines!inner(name)
              )
            `)
            .eq('discipline', discipline)
            .eq('articles.disciplines.name', discipline)
            .gte('articles.published_at', new Date(Date.now() - 2 * 365 * 24 * 60 * 60 * 1000).toISOString())
            .order('added_at', { ascending: false })
            .limit(articleLimit);

          console.timeEnd(`discipline-${discipline}-query`);
          
          if (articleError) throw articleError;
          console.log(`Found ${articles.length} articles for discipline ${discipline}`);

          articles.forEach(article => {
            articlesJson.push({
              id: article.articles.id,
              title: article.articles.title,
              content: article.articles.content,
              journal: article.articles.journal || 'Inconnu',
              discipline: discipline,
              added_at: article.added_at,
              link: article.link || ''
            });
            articleCount++;
          });
        }

        if (articleCount > 0) {
          usersToNotify.push({
            email: user.email,
            first_name: user.first_name,
            articles: articlesJson
          });
        }
        console.timeEnd(`user-${user.id}-processing`);
        console.log(`Processed ${articleCount} total articles for user ${user.email}`);
      }

      lastUserId = userProfiles[userProfiles.length - 1].id;
      hasMoreUsers = userProfiles.length === USERS_BATCH_SIZE;
    }
    console.timeEnd('users-processing');

    // Comment 
    let emailsSentSuccessfully = 0;
    // Send notifications in batches
    const SENDGRID_BATCH_SIZE = 10;
    for (let i = 0; i < usersToNotify.length; i += SENDGRID_BATCH_SIZE) {
      const batch = usersToNotify.slice(i, i + SENDGRID_BATCH_SIZE);
      
      try {
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
              name: "Dr Baptiste Mazas - Veille Médicale",
            },
            template_id: "d-27f89a4f0faa4df1ab83b9fbc7be19a1",
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to send email via SendGrid. Status: ${response.status}, ${await response.text()}`);
        }

        // Update last notification date for this batch
        const { error: updateError } = await supabase
          .from('user_profiles')
          .update({ last_notification_sent_date: new Date().toISOString() })
          .in('email', batch.map(user => user.email));

        if (updateError) throw updateError;

        emailsSentSuccessfully += batch.length;
        console.log(`Successfully sent emails to batch of ${batch.length} users`);

      } catch (error) {
        throw new Error(`Error sending batch email: ${error.message}`);
      }
    }

    console.timeEnd('total-execution');
    return new Response(JSON.stringify({ 
      success: true,
      stats: {
        totalUsersQueried,
        totalArticlesProcessed: usersToNotify.reduce((acc, user) => acc + user.articles.length, 0),
        usersWithArticles: usersToNotify.length
      }
    }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    });

  } catch (error) {
    console.timeEnd('total-execution');
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { 'Content-Type': 'application/json' },
      status: 500,
    });
  }
});

function getArticleLimit(frequency: string, lastNotificationDate: string | null): number {
  if (!lastNotificationDate) return 1; // First time notification

  const lastNotification = new Date(lastNotificationDate);
  const now = new Date();
  const hoursSinceLastNotification = Math.floor(
    (now.getTime() - lastNotification.getTime()) / (1000 * 60 * 60)
  );
  
  const daysSinceLastNotification = Math.floor(
    (now.setHours(0,0,0,0) - lastNotification.setHours(0,0,0,0)) / (1000 * 60 * 60 * 24)
  );

  const currentDay = new Date().getDay();

  switch (frequency) {
    case 'tous_les_jours':
      return hoursSinceLastNotification >= 16 ? 1 : 0;

    case 'tous_les_2_jours':
      return (daysSinceLastNotification >= 2) ? 1 : 0;

    case 'tous_les_3_jours':
      return (daysSinceLastNotification >= 3) ? 1 : 0;

    case '1_fois_par_semaine':
      return (daysSinceLastNotification >= 7 && currentDay === 1) ? 7 : 0;

    case 'tous_les_15_jours':
      return (daysSinceLastNotification >= 15) ? 15 : 0;

    case '1_fois_par_mois':
      return (daysSinceLastNotification >= 30 && new Date().getDate() === 1) ? 30 : 0;

    default:
      return 0;
  }
}
