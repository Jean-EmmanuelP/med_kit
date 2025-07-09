// /lib/auth.js
import { supabase } from '$lib/supabase';

export async function syncSession() {
  const { data: sessionData, error } = await supabase.auth.getSession();
  if (error) {
    console.error('Error getting session client-side:', error);
    return null;
  }

  if (!sessionData?.session) {
    console.log('No session found client-side, attempting to refresh');
    const { data: refreshedSession, error: refreshError } = await supabase.auth.refreshSession();
    if (refreshError || !refreshedSession?.session) {
      console.error('Error refreshing session client-side:', refreshError);
      return null;
    }
    return refreshedSession.session;
  }

  return sessionData.session;
}

export async function getUserProfile(userId) {
  const { data: profile, error } = await supabase
    .from('user_profiles')
    .select('id, first_name, last_name, notification_frequency, disciplines, date_of_birth, status, specialty, is_admin')
    .eq('id', userId)
    .single();

  if (error) {
    console.error('Error fetching user profile:', error);
    return null;
  }

  return profile;
}