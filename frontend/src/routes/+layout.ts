// +layout.ts
import { createBrowserClient, createServerClient, isBrowser } from '@supabase/ssr';
import { PUBLIC_SUPABASE_ANON_KEY, PUBLIC_SUPABASE_URL } from '$env/static/public';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ data, depends, fetch }) => {
  depends('supabase:auth');

  // Helper functions for cookie management in the browser
  const getAllCookies = () => {
    const cookies = document.cookie.split(';').map((cookie) => {
      const [name, value] = cookie.trim().split('=');
      return { name, value };
    });
    return cookies;
  };

  const setAllCookies = (cookiesToSet) => {
    cookiesToSet.forEach(({ name, value, options }) => {
      let cookieString = `${name}=${value}`;
      if (options) {
        if (options.path) cookieString += `;path=${options.path}`;
        if (options.expires) cookieString += `;expires=${options.expires.toUTCString()}`;
        if (options.sameSite) cookieString += `;SameSite=${options.sameSite}`;
        if (options.secure) cookieString += ';Secure';
      }
      document.cookie = cookieString;
    });
  };

  const supabase = isBrowser()
    ? createBrowserClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY, {
        global: {
          fetch,
        },
        cookies: {
          getAll: getAllCookies,
          setAll: setAllCookies,
        },
      })
    : createServerClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY, {
        global: {
          fetch,
        },
        cookies: {
          getAll() {
            return data.cookies;
          },
        },
      });

  // Use the session and user from the server-side data
  const session = data.session;
  const user = data.user;

  console.log('Layout client session:', session);
  console.log('Layout client user:', user);

  return { session, supabase, user };
};