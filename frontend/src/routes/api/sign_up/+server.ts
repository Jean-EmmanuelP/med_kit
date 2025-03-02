import { json } from '@sveltejs/kit';

export async function POST({ request, locals: { supabase, safeGetSession } }) {
  const { first_name, last_name, email, password, disciplines, notification_frequency } = await request.json();

  // Inscription via Supabase Auth
  const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
    email,
    password
  });

  if (signUpError) {
    console.error('Erreur d’inscription :', JSON.stringify(signUpError, null, 2));
    return json({ error: signUpError.message }, { status: 400 });
  }

  if (!signUpData.user) {
    console.error('Aucun utilisateur retourné par signUp');
    return json({ error: 'Erreur lors de la création de l’utilisateur' }, { status: 500 });
  }

  // Vérifier si l'utilisateur est connecté automatiquement
  const { session } = signUpData;
  if (!session) {
    // Si aucune session n’est retournée, l’utilisateur doit confirmer son email
    console.log('Utilisateur inscrit, en attente de confirmation par email.');
    return json({ 
      message: 'Inscription réussie. Veuillez vérifier votre email pour confirmer votre compte.' 
    }, { status: 200 });
  }

  // Création du profil utilisateur
  const newUserProfile = {
    id: signUpData.user.id,
    first_name,
    last_name,
    email,
    disciplines,
    notification_frequency,
    article_ids: []
  };

  const { data: profileData, error: profileError } = await supabase
    .from('user_profiles')
    .insert(newUserProfile)
    .select('*')
    .single();

  if (profileError) {
    console.error('Erreur d’insertion du profil :', JSON.stringify(profileError, null, 2));
    return json({ error: profileError.message }, { status: 500 });
  }

  // Si une session est retournée, l'utilisateur est déjà connecté
  // Vérifier la session actuelle
  const { session: currentSession, user } = await safeGetSession();
  if (!currentSession || !user) {
    console.error('Session non mise à jour après inscription');
    return json({ error: 'Erreur lors de la mise à jour de la session' }, { status: 500 });
  }

  console.log('Utilisateur inscrit et connecté avec succès :', JSON.stringify(profileData, null, 2));
  return json({ data: profileData });
}