// account/+page.server.ts
import { redirect } from '@sveltejs/kit';

export async function load({ locals }) {
  const { session, user } = await locals.safeGetSession();

  console.log('Session in account:', session);
  console.log('User in account:', user);

  if (!session || !user) {
    throw redirect(302, '/login');
  }

  // Fetch user profile
  const { data: userProfile, error: profileError } = await locals.supabase
    .from('user_profiles')
    .select('id, first_name, last_name, notification_frequency, disciplines, date_of_birth, status, specialty')
    .eq('id', user.id)
    .single();

  if (profileError || !userProfile) {
    console.error('Error fetching user profile:', profileError);
    return { error: profileError ? profileError.message : 'Profil non trouvé.' };
  }

  // Fetch all disciplines
  const { data: disciplinesList, error: disciplinesError } = await locals.supabase
    .from('disciplines')
    .select('name')
    .order('name', { ascending: true });

  if (disciplinesError) {
    console.error('Error fetching disciplines:', disciplinesError);
    return { error: disciplinesError.message };
  }

  return {
    userPreferences: {
      disciplines: userProfile.disciplines || [],
      notificationFrequency: userProfile.notification_frequency || 'tous_les_jours',
      date_of_birth: userProfile.date_of_birth,
    },
    disciplinesList: disciplinesList.map(d => d.name),
    userProfile,
    session,
    user,
  };
}