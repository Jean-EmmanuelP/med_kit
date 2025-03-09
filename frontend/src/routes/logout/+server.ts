import { json, redirect } from '@sveltejs/kit';

export const POST = async ({ locals, cookies, url }) => {
  console.log('Starting logout process...');

  // Vérifier si locals.supabase est défini
  if (!locals.supabase) {
    console.error('Supabase client not initialized in locals');
    return json({ error: 'Supabase client not initialized' }, { status: 500 });
  }

  // Déconnexion via Supabase
  console.log('Calling supabase.auth.signOut()...');
  const { error } = await locals.supabase.auth.signOut();
  if (error) {
    console.error('Server-side logout error:', error);
    return json({ error: error.message }, { status: 500 });
  }

  // Vérifier l'URL pour les options de cookie
  console.log('Request URL:', url);
  const isLocalhost = url.hostname.includes('localhost');
  console.log('Is localhost:', isLocalhost);

  // Supprimer manuellement le cookie d'authentification
  const cookieName = 'sb-etxelhjnqbrgwuitltyk-auth-token';
  console.log('Cookies before deletion:', cookies.getAll());
  cookies.delete(cookieName, {
    path: '/',
    httpOnly: true,
    secure: !isLocalhost,
    sameSite: isLocalhost ? 'lax' : 'none',
    domain: isLocalhost ? 'localhost' : '.veillemedicale.fr',
  });
  console.log('Cookies after deletion:', cookies.getAll());

  console.log('Cookie deleted successfully, redirecting...');
  throw redirect(303, '/'); // La redirection doit être en dehors du try-catch
};