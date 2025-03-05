// /routes/signup/+page.server.ts
import type { Actions } from '@sveltejs/kit';
import { fail } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';

export const actions: Actions = {
  default: async ({ request, locals: { supabase } }) => {
    console.log('Signup action started');

    const formData = await request.formData();
    const first_name = formData.get('first_name')?.toString();
    const last_name = formData.get('last_name')?.toString();
    const email = formData.get('email')?.toString();
    const password = formData.get('password')?.toString();
    const disciplines = formData.getAll('disciplines') as string[];
    const notification_frequency = formData.get('notification_frequency')?.toString();
    const date_of_birth = formData.get('date_of_birth')?.toString() || null;
    const specialty = formData.get('specialty')?.toString() || null;
    const status = formData.get('status')?.toString() || null;

    // Validate required fields
    if (!first_name || !last_name || !email || !password || !notification_frequency) {
      console.log('Validation failed: Missing required fields');
      return fail(400, { error: 'Tous les champs obligatoires doivent être remplis.' });
    }

    if (!disciplines || disciplines.length === 0) {
      console.log('Validation failed: No disciplines selected');
      return fail(400, { error: 'Veuillez sélectionner au moins une discipline.' });
    }

    // Inscription via Supabase Auth
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

    // Vérifier si l'utilisateur est connecté automatiquement
    const { session } = signUpData;
    if (!session) {
      console.log('User signed up, awaiting email confirmation');
      return { success: true, message: 'Inscription réussie. Veuillez vérifier votre email pour confirmer votre compte.', redirectTo: '/login' };
    }

    // Création du profil utilisateur
    console.log('Creating user profile');
    const newUserProfile = {
      id: signUpData.user.id,
      first_name,
      last_name,
      email,
      disciplines,
      notification_frequency,
      date_of_birth,
      specialty,
      status,
      sent_article_ids: [],
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

    console.log('User signed up successfully:', JSON.stringify(profileData, null, 2));
    console.log('Throwing redirect to /articles');
    throw redirect(302, '/articles');
  },
};