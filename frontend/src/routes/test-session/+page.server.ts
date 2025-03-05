// /routes/test-session/+page.server.ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
  console.log('Test-session load started');

  const {
    data: { session },
    error: sessionError,
  } = await locals.supabase.auth.getSession();
  console.log('Server-side getSession result:', { session, sessionError });

  if (sessionError) {
    console.error('Server-side error getting session:', sessionError);
    return { session: null, user: null };
  }

  if (!session) {
    console.log('Server-side: No session found');
    return { session: null, user: null };
  }

  const {
    data: { user },
    error: userError,
  } = await locals.supabase.auth.getUser();
  console.log('Server-side getUser result:', { user, userError });

  if (userError) {
    console.error('Server-side error getting user:', userError);
    return { session: null, user: null };
  }

  return { session, user };
};