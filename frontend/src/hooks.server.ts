// hooks.server.js
import { createServerClient } from '@supabase/ssr';
import { type Handle } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';

import { PUBLIC_SUPABASE_ANON_KEY, PUBLIC_SUPABASE_URL } from '$env/static/public';

// Log environment variables on the server
console.log('Server-side PUBLIC_SUPABASE_URL:', PUBLIC_SUPABASE_URL);
console.log('Server-side PUBLIC_SUPABASE_ANON_KEY:', PUBLIC_SUPABASE_ANON_KEY);
console.log('Server-side NODE_ENV:', process.env.NODE_ENV);
console.log('Full process.env:', process.env);

const supabase: Handle = async ({ event, resolve }) => {
  // Determine production environment based on hostname
  const isProduction = !event.url.hostname.includes('localhost');
  console.log('isProduction:', isProduction);
  console.log('Request URL:', event.url.hostname);

  event.locals.supabase = createServerClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => {
        const cookies = event.cookies.getAll();
        console.log('Cookies getAll:', cookies);
        return cookies;
      },
      setAll: (cookiesToSet) => {
        console.log('Cookies to set:', cookiesToSet);
        cookiesToSet.forEach(({ name, value, options }) => {
          const cookieOptions = {
            ...options,
            path: '/',
            httpOnly: true, // Revert to true for security
            secure: isProduction,
            sameSite: isProduction ? 'none' : 'lax',
            domain: isProduction ? '.veillemedicale.fr' : 'localhost', // Use leading dot for production
          };
          console.log(`Setting cookie: ${name}=${value}, options:`, cookieOptions);
          event.cookies.set(name, value, cookieOptions);
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
    } = await event.locals.supabase.auth.getUser();

    if (userError) {
      console.error('Server-side error getting user:', userError);
      return { session: null, user: null };
    }

    console.log('Server-side session retrieved:', session);
    console.log('Server-side user retrieved:', user);

    return { session, user };
  };

  return resolve(event, {
    filterSerializedResponseHeaders(name) {
      return name === 'content-range' || name === 'x-supabase-api-version';
    },
  });
};

export const handle: Handle = sequence(supabase);