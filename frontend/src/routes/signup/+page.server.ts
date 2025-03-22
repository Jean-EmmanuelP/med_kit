import { PUBLIC_SUPABASE_ANON_KEY } from '$env/static/public';
import type { Actions } from '@sveltejs/kit';
import { fail, redirect } from '@sveltejs/kit';

export const actions: Actions = {
    default: async ({ request, locals: { supabase } }) => {
        console.log('Signup action started');

        const formData = await request.formData();
        const first_name = formData.get('first_name')?.toString();
        const last_name = formData.get('last_name')?.toString() || '';
        const email = formData.get('email')?.toString();
        const password = formData.get('password')?.toString();
        const disciplines = formData.getAll('disciplines[]') as string[];
        const notification_frequency = formData
            .get('notification_frequency')
            ?.toString()
            ?.toLowerCase();
        const date_of_birth = formData.get('date_of_birth')?.toString() || null;

        // Validation
        if (!first_name || !email || !password || !notification_frequency) {
            console.log('Validation failed: Missing required fields');
            return fail(400, { error: 'Tous les champs obligatoires doivent être remplis.' });
        }

        if (!disciplines || disciplines.length === 0) {
            console.log('Validation failed: No disciplines selected');
            return fail(400, { error: 'Veuillez sélectionner au moins une discipline.' });
        }

        console.log('Attempting Supabase signUp');
        const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
            email,
            password,
        });

        if (signUpError) {
            console.error('SignUp error:', JSON.stringify(signUpError, null, 2));
            return fail(400, { error: signUpError.message });
        }

        if (!signUpData.user) {
            console.error('No user returned by signUp');
            return fail(500, { error: 'Erreur lors de la création de l’utilisateur' });
        }

        const { session } = signUpData;
        if (!session) {
            console.log('User signed up, awaiting email confirmation');
            return fail(400, {
                error: 'Inscription réussie. Veuillez vérifier votre email pour confirmer votre compte.',
            });
        }

        console.log('Creating user profile');
        const newUserProfile = {
            id: signUpData.user.id,
            first_name,
            last_name,
            email,
            disciplines,
            notification_frequency,
            date_of_birth,
        };

        const { data: profileData, error: profileError } = await supabase
            .from('user_profiles')
            .insert(newUserProfile)
            .select('*')
            .single();

        if (profileError) {
            console.error('Profile insertion error:', JSON.stringify(profileError, null, 2));
            if (profileError.code === '23505') {
                return fail(400, { error: 'Cet utilisateur existe déjà.' });
            } else if (profileError.code === '23502') {
                return fail(500, { error: 'Un champ requis est manquant ou invalide.' });
            } else {
                return fail(500, { error: profileError.message });
            }
        }

        // 1. Trigger send-welcome-email Edge Function
        try {
            console.log('Triggering send-welcome-email Edge Function');
            const welcomeEdgeUrl =
                'https://etxelhjnqbrgwuitltyk.supabase.co/functions/v1/send-welcome-email';
            const welcomeResponse = await fetch(welcomeEdgeUrl, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${PUBLIC_SUPABASE_ANON_KEY}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: signUpData.user.id,
                    email,
                    first_name, // Required by the Edge Function, even if not used in the template
                }),
            });

            if (!welcomeResponse.ok) {
                const errorText = await welcomeResponse.text();
                console.error('Error triggering send-welcome-email:', errorText);
            } else {
                console.log('send-welcome-email triggered successfully');
            }
        } catch (e) {
            console.error('Exception in send-welcome-email:', e);
        }

        // 2. Fetch one article per discipline for the user using database function
        let selectedArticles: { id: number; title: string; journal: string; discipline: string }[] = [];
        try {
            // change this logic
            console.log('Fetching articles using database function for disciplines:', disciplines);
            const { data, error } = await supabase.rpc('fetch_articles_by_disciplines', {
                p_user_id: signUpData.user.id,
                p_disciplines: disciplines,
            });

            if (error) {
                console.error('Error calling fetch_articles_by_disciplines:', JSON.stringify(error, null, 2));
            } else if (data) {
                // Parse the JSON array returned by the function
                const articlesArray = Array.isArray(data) ? data : (data as any).fetch_articles_by_disciplines || [];
                selectedArticles = articlesArray.map((article: any) => ({
                    id: article.id,
                    title: article.title,
                    journal: article.journal,
                    discipline: article.discipline,
                }));
                selectedArticles.forEach((article, index) => {
                    console.log(`Selected article ${index + 1} for discipline ${article.discipline}:`, article);
                });
            } else {
                console.log('No articles returned by fetch_articles_by_disciplines');
            }
        } catch (e) {
            console.error('Exception in fetching articles:', e);
        }

        // 3. Trigger send-notification Edge Function and insert into user_sent_articles
        if (selectedArticles.length > 0) {
            // Insert into user_sent_articles for each selected article
            for (const article of selectedArticles) {
                const { error: sentArticleError } = await supabase
                    .from('user_sent_articles')
                    .insert({
                        user_id: signUpData.user.id,
                        article_id: article.id,
                        sent_at: new Date().toISOString(),
                        discipline: article.discipline, // Include discipline as per schema
                    });

                if (sentArticleError) {
                    console.error(
                        `Error inserting article ${article.id} into user_sent_articles:`,
                        sentArticleError
                    );
                } else {
                    console.log(
                        `Inserted article ${article.id} into user_sent_articles for discipline ${article.discipline}`
                    );
                }
            }

            // Trigger send-notification Edge Function
            try {
                console.log('Triggering send-notification Edge Function with articles:', selectedArticles);
                const notificationEdgeUrl =
                    'https://etxelhjnqbrgwuitltyk.supabase.co/functions/v1/send-notification';
                const notificationResponse = await fetch(notificationEdgeUrl, {
                    method: 'POST',
                    headers: {
                        Authorization: `Bearer ${PUBLIC_SUPABASE_ANON_KEY}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: signUpData.user.id,
                        email,
                        first_name, // Required by the Edge Function, even if not used in the template
                        articles: selectedArticles,
                    }),
                });

                if (!notificationResponse.ok) {
                    const errorText = await notificationResponse.text();
                    console.error('Error triggering send-notification:', errorText);
                } else {
                    console.log('send-notification triggered successfully with articles:', selectedArticles);
                }
            } catch (e) {
                console.error('Exception in send-notification:', e);
            }
        } else {
            console.log('No articles selected, skipping send-notification');
        }

        console.log('User signed up successfully:', JSON.stringify(profileData, null, 2));
        console.log('Throwing redirect to /ma-veille');
        throw redirect(302, '/ma-veille');
    },
};