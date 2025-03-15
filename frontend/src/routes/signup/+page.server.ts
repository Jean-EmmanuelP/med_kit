// /routes/signup/+page.server.ts
import type { Actions } from '@sveltejs/kit';
import { fail } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';
import { PUBLIC_SUPABASE_ANON_KEY } from '$env/static/public';

export const actions: Actions = {
	default: async ({ request, locals: { supabase } }) => {
		console.log('Signup action started');

		const formData = await request.formData();
		const first_name = formData.get('first_name')?.toString();
		const last_name = formData.get('last_name')?.toString();
		const email = formData.get('email')?.toString();
		const password = formData.get('password')?.toString();
		const disciplines = formData.getAll('disciplines[]') as string[];
		const notification_frequency = formData
			.get('notification_frequency')
			?.toString()
			?.toLowerCase();
		const date_of_birth = formData.get('date_of_birth')?.toString() || null;

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
			password
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
				error: 'Inscription réussie. Veuillez vérifier votre email pour confirmer votre compte.'
			});
		}

		console.log('Creating user profile');
		const newUserProfile = {
			id: signUpData.user.id,
			first_name,
			last_name: last_name || '',
			email,
			disciplines,
			notification_frequency,
			date_of_birth,
			sent_article_ids: []
		};

		const { data: profileData, error: profileError } = await supabase
			.from('user_profiles')
			.insert(newUserProfile)
			.select('*')
			.single();

		if (profileError) {
			console.error('Profile insertion error:', JSON.stringify(profileError, null, 2));
			return fail(500, { error: profileError.message });
		}

		// Edge Functions (welcome email et notification) restent identiques
		// [Code omis pour brièveté, mais garde-le si tu l'utilises]
		// 1. Appeler l'Edge Function send-welcome-email
		try {
			console.log('Triggering send-welcome-email Edge Function');
			const welcomeEdgeUrl =
				'https://etxelhjnqbrgwuitltyk.supabase.co/functions/v1/send-welcome-email';
			const welcomeResponse = await fetch(welcomeEdgeUrl, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${PUBLIC_SUPABASE_ANON_KEY}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					user_id: signUpData.user.id,
					email,
					first_name
				})
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

		// 2. Sélectionner un seul article maximum pour l'utilisateur
		let selectedArticle = null;
		try {
			console.log('Fetching one article for disciplines:', disciplines);
			const { data: articles, error: articlesError } = await supabase
				.from('articles')
				.select(
					`
			id,
			title,
			content,
			published_at,
			journal,
			article_disciplines (
				disciplines (
					name
				)
			)
		`
				)
				.not('id', 'in', `(${newUserProfile.sent_article_ids.join(',') || '0'})`)
				.filter(
					'article_disciplines.disciplines.name',
					'in',
					`(${disciplines.map((d) => `"${d}"`).join(',')})`
				)
				.gte('published_at', new Date(Date.now() - 2 * 365 * 24 * 60 * 60 * 1000).toISOString()) // 2 dernières années
				.order('published_at', { ascending: false })
				.limit(1);

			if (articlesError) {
				console.error('Error fetching article:', JSON.stringify(articlesError, null, 2));
			} else if (articles && articles.length > 0) {
				selectedArticle = {
					id: articles[0].id,
					title: articles[0].title,
					content: articles[0].content,
					journal: articles[0].journal || 'Inconnu'
				};
				console.log('Selected article:', selectedArticle);
			} else {
				console.log('No article found for the user');
			}
		} catch (e) {
			console.error('Exception in fetching article:', e);
		}

		// 3. Appeler l'Edge Function send-notification
		try {
			console.log('Triggering send-notification Edge Function');
			const notificationEdgeUrl =
				'https://etxelhjnqbrgwuitltyk.supabase.co/functions/v1/send-notification';
			const articlesToSend = selectedArticle ? [selectedArticle] : [];
			const notificationResponse = await fetch(notificationEdgeUrl, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${PUBLIC_SUPABASE_ANON_KEY}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					user_id: signUpData.user.id,
					email,
					first_name,
					articles: articlesToSend
				})
			});

			if (!notificationResponse.ok) {
				const errorText = await notificationResponse.text();
				console.error('Error triggering send-notification:', errorText);
			} else {
				console.log('send-notification triggered successfully');
				if (selectedArticle) {
					const { error: updateError } = await supabase
						.from('user_profiles')
						.update({ sent_article_ids: [selectedArticle.id] })
						.eq('id', signUpData.user.id);

					if (updateError) {
						console.error('Error updating sent_article_ids:', updateError);
					} else {
						console.log('Updated sent_article_ids:', [selectedArticle.id]);
					}
				}
			}
		} catch (e) {
			console.error('Exception in send-notification:', e);
		}
		console.log('User signed up successfully:', JSON.stringify(profileData, null, 2));
		console.log('Throwing redirect to /ma-veille');
		throw redirect(302, '/ma-veille');
	}
};
