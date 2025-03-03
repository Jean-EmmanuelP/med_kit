// /routes/login/+page.server.ts
import type { Actions } from '@sveltejs/kit';
import { fail } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';

export const actions: Actions = {
  default: async ({ request, locals: { supabase, safeGetSession } }) => {
    const formData = await request.formData();
    const email = formData.get('email')?.toString();
    const password = formData.get('password')?.toString();

    // Validate required fields
    if (!email || !password) {
      return fail(400, { error: 'Veuillez remplir tous les champs.' });
    }

    // Connexion via Supabase Auth
    const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (signInError) {
      console.error('Erreur de connexion :', JSON.stringify(signInError, null, 2));
      return fail(400, { error: signInError.message });
    }

    // Vérifier que l'utilisateur est connecté
    if (!signInData.user) {
      console.error('Aucun utilisateur retourné par signIn');
      return fail(500, { error: 'Erreur lors de la connexion de l’utilisateur' });
    }

    // Récupérer le profil utilisateur
    const { data: profileData, error: profileError } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('id', signInData.user.id)
      .single();

    if (profileError) {
      console.error('Erreur de récupération du profil :', JSON.stringify(profileError, null, 2));
      return fail(500, { error: profileError.message });
    }

    // Vérifier la session actuelle
    const { session, user } = await safeGetSession();
    if (!session || !user) {
      console.error('Session non mise à jour après connexion');
      return fail(500, { error: 'Erreur lors de la mise à jour de la session' });
    }

    console.log('Utilisateur connecté avec succès :', JSON.stringify(profileData, null, 2));
    return { success: true, profileData, redirectTo: '/articles' };
  },
};