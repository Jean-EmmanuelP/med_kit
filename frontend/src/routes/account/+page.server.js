import { supabase } from '$lib/supabase';
import { redirect } from '@sveltejs/kit';

export async function load({ locals }) {
  const user = locals.user; // Remplacez par votre méthode d'authentification

  // Rediriger vers /login si l'utilisateur n'est pas connecté
  if (!user) {
    throw redirect(302, '/login');
  }

  // Récupérer les informations de l'utilisateur (fréquence des notifications et disciplines)
  const { data: userData, error: userError } = await supabase
    .from('user_profiles')
    .select('notification_frequency, disciplines')
    .eq('id', user.id)
    .single();

  if (userError || !userData) {
    return { userPreferences: null, disciplinesList: [], error: userError ? userError.message : 'Utilisateur non trouvé' };
  }

  // Récupérer la liste complète des disciplines disponibles
  const { data: disciplinesData, error: disciplinesError } = await supabase
    .from('disciplines')
    .select('name')
    .order('name', { ascending: true });

  if (disciplinesError) {
    return { userPreferences: null, disciplinesList: [], error: disciplinesError.message };
  }

  return {
    userPreferences: {
      notificationFrequency: userData.notification_frequency,
      disciplines: userData.disciplines || []
    },
    disciplinesList: disciplinesData.map(d => d.name)
  };
}

export const actions = {
  updateNotificationFrequency: async ({ request, locals }) => {
    const user = locals.user;
    if (!user) {
      throw redirect(302, '/login');
    }

    const formData = await request.formData();
    const notificationFrequency = formData.get('notificationFrequency');

    if (!notificationFrequency) {
      return { success: false, error: 'La fréquence des notifications est requise.', action: 'updateNotificationFrequency' };
    }

    // Mettre à jour la fréquence des notifications
    const { error } = await supabase
      .from('user_profiles')
      .update({ notification_frequency: notificationFrequency })
      .eq('id', user.id);

    if (error) {
      return { success: false, error: error.message, action: 'updateNotificationFrequency' };
    }

    return { success: true, action: 'updateNotificationFrequency' };
  },

  updateDisciplines: async ({ request, locals }) => {
    const user = locals.user;
    if (!user) {
      throw redirect(302, '/login');
    }

    const formData = await request.formData();
    const selectedDisciplines = formData.getAll('disciplines'); // Récupère toutes les disciplines cochées

    // Mettre à jour les disciplines
    const { error } = await supabase
      .from('user_profiles')
      .update({ disciplines: selectedDisciplines })
      .eq('id', user.id);

    if (error) {
      return { success: false, error: error.message, action: 'updateDisciplines' };
    }

    return { success: true, action: 'updateDisciplines', updatedDisciplines: selectedDisciplines };
  }
};