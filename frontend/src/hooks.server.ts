// hooks.server.js
import { createServerClient } from '@supabase/ssr';
import { type Handle } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';

import { PUBLIC_SUPABASE_ANON_KEY, PUBLIC_SUPABASE_URL } from '$env/static/public';

const supabase: Handle = async ({ event, resolve }) => {
  event.locals.supabase = createServerClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => {
        const cookies = event.cookies.getAll();
        console.log('Cookies getAll:', cookies);
        return cookies;
      },
      setAll: (cookiesToSet) => {
        cookiesToSet.forEach(({ name, value, options }) => {
          console.log(`Cookie set: ${name}=${value}`);
          event.cookies.set(name, value, { ...options, path: '/', httpOnly: true, secure: true, sameSite: 'strict' });
        });
      },
    },
  });

  event.locals.safeGetSession = async () => {
    const {
      data: { session },
      error: sessionError,
    } = await event.locals.supabase.auth.getSession();

    if (sessionError) {
      console.error('Error getting session:', sessionError);
      return { session: null, user: null };
    }

    if (!session) {
      console.log('No session found');
      return { session: null, user: null };
    }

    const {
      data: { user },
      error: userError,
    } = await event.locals.supabase.auth.getUser();

    if (userError) {
      console.error('Error getting user:', userError);
      return { session: null, user: null };
    }

    console.log('Session retrieved:', session);
    console.log('User retrieved:', user);

    return { session, user };
  };

  return resolve(event, {
    filterSerializedResponseHeaders(name) {
      return name === 'content-range' || name === 'x-supabase-api-version';
    },
  });
};

export const handle: Handle = sequence(supabase);