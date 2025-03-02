// /api/sign_in/+server.ts
import { json } from '@sveltejs/kit';

export async function POST({ request, locals: { supabase, safeGetSession } }) {
  const { email, password } = await request.json();

  // Connexion via Supabase Auth
  const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
    email,
    password
  });

  if (signInError) {
    console.error('Erreur de connexion :', JSON.stringify(signInError, null, 2));
    return json({ error: signInError.message }, { status: 400 });
  }

  // Vérifier que l'utilisateur est connecté
  if (!signInData.user) {
    console.error('Aucun utilisateur retourné par signIn');
    return json({ error: 'Erreur lors de la connexion de l’utilisateur' }, { status: 500 });
  }

  // Récupérer le profil utilisateur
  const { data: profileData, error: profileError } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('id', signInData.user.id)
    .single();

  if (profileError) {
    console.error('Erreur de récupération du profil :', JSON.stringify(profileError, null, 2));
    return json({ error: profileError.message }, { status: 500 });
  }

  // Vérifier la session actuelle
  const { session, user } = await safeGetSession();
  if (!session || !user) {
    console.error('Session non mise à jour après connexion');
    return json({ error: 'Erreur lors de la mise à jour de la session' }, { status: 500 });
  }

  console.log('Utilisateur connecté avec succès :', JSON.stringify(profileData, null, 2));
  return json({ data: profileData });
}