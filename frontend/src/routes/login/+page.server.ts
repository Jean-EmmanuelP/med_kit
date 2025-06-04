// /routes/login/+page.server.ts
import type { Actions } from '@sveltejs/kit';
import { fail, redirect } from '@sveltejs/kit';

export const actions: Actions = {
	default: async ({ request, locals: { supabase } }) => {
		console.log('Login action started');

		const formData = await request.formData();
		const email = formData.get('email')?.toString();
		const password = formData.get('password')?.toString();

		// Validate required fields
		if (!email || !password) {
			console.log('Validation failed: Missing email or password');
			return fail(400, { error: 'Veuillez remplir tous les champs.' });
		}

		// Connexion via Supabase Auth
		console.log('Attempting Supabase signInWithPassword');
		const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
			email,
			password
		});

		if (signInError) {
			console.error('SignIn error:', JSON.stringify(signInError, null, 2));
			return fail(400, { error: signInError.message });
		}

		// Vérifier que l'utilisateur est connecté
		if (!signInData.user) {
			console.error('No user returned by signIn');
			return fail(500, { error: 'Erreur lors de la connexion de l’utilisateur' });
		}

		// Récupérer le profil utilisateur
		console.log('Fetching user profile');
		const { data: profileData, error: profileError } = await supabase
			.from('user_profiles')
			.select('*')
			.eq('id', signInData.user.id)
			.single();

		if (profileError) {
			console.error('Profile fetch error:', JSON.stringify(profileError, null, 2));
			return fail(500, { error: profileError.message });
		}

		console.log('User logged in successfully:', JSON.stringify(profileData, null, 2));
		console.log('Throwing redirect to /ma-veille');
		throw redirect(302, '/ma-veille');
	}
};
