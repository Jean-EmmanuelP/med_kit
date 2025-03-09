// hooks.server.ts
import { createServerClient } from '@supabase/ssr';
import { redirect, type Handle } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';
import { PUBLIC_SUPABASE_ANON_KEY, PUBLIC_SUPABASE_URL } from '$env/static/public';

const supabase: Handle = async ({ event, resolve }) => {
  const isProduction = !event.url.hostname.includes('localhost');
  console.log('isProduction:', isProduction);

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
            httpOnly: true,
            secure: isProduction, // Désactivé en local (pas de HTTPS)
            sameSite: isProduction ? 'lax' : 'lax', // 'none' nécessite HTTPS
            domain: isProduction ? '.veillemedicale.fr' : undefined, // Pas de domaine en local
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
      console.error('Session error:', sessionError);
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
      console.error('User error:', userError);
      return { session: null, user: null };
    }

    console.log('Session:', session);
    console.log('User:', user);
    return { session, user };
  };

  return resolve(event, {
    filterSerializedResponseHeaders(name) {
      return name === 'content-range' || name === 'x-supabase-api-version';
    },
  });
};

const authGuard: Handle = async ({ event, resolve }) => {
  const { session, user } = await event.locals.safeGetSession();
  event.locals.session = session;
  event.locals.user = user;

  if (event.url.pathname.startsWith('/ma-veille') && !session) {
    throw redirect(303, '/login');
  }

  return resolve(event);
};

export const handle: Handle = sequence(supabase, authGuard);