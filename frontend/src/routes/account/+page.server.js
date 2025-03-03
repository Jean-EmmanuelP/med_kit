// account/+page.server.js
export async function load({ locals }) {
  const { session, user } = await locals.safeGetSession();

  console.log('Session in account:', session);
  console.log('User in account:', user);

  if (!session || !user) {
    return { error: 'Vous devez être connecté pour accéder à cette page.' };
  }

  // Fetch user profile
  const { data: userProfile, error: profileError } = await locals.supabase
    .from('user_profiles')
    .select('id, first_name, last_name, notification_frequency, disciplines, date_of_birth, education, status, specialty')
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
    userPreferences: userProfile,
    disciplinesList: disciplinesList.map(d => d.name),
    userProfile // Pass the user profile to the client
  };
}

export const actions = {
  updateDisciplines: async ({ request, locals }) => {
    const { session, user } = await locals.safeGetSession();
    if (!session || !user) {
      return { success: false, error: 'Vous devez être connecté pour modifier vos disciplines.', action: 'updateDisciplines' };
    }

    const formData = await request.formData();
    const disciplines = JSON.parse(formData.get('disciplines'));

    // Update the user's disciplines and specialty (first discipline)
    const specialty = disciplines.length > 0 ? disciplines[0] : null;
    const { error } = await locals.supabase
      .from('user_profiles')
      .update({
        disciplines,
        specialty
      })
      .eq('id', user.id);

    if (error) {
      console.error('Error updating disciplines:', error);
      return { success: false, error: error.message, action: 'updateDisciplines' };
    }

    return { success: true, updatedDisciplines: disciplines, action: 'updateDisciplines' };
  },

  updateNotificationFrequency: async ({ request, locals }) => {
    const { session, user } = await locals.safeGetSession();
    if (!session || !user) {
      return { success: false, error: 'Vous devez être connecté pour modifier la fréquence des notifications.', action: 'updateNotificationFrequency' };
    }

    const formData = await request.formData();
    const notificationFrequency = formData.get('notificationFrequency');

    const { error } = await locals.supabase
      .from('user_profiles')
      .update({ notification_frequency: notificationFrequency })
      .eq('id', user.id);

    if (error) {
      console.error('Error updating notification frequency:', error);
      return { success: false, error: error.message, action: 'updateNotificationFrequency' };
    }

    return { success: true, updatedNotificationFrequency: notificationFrequency, action: 'updateNotificationFrequency' };
  }
};