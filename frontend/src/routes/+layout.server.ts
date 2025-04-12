// +layout.server.ts
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals: { safeGetSession }, cookies }) => {
  const { session, user } = await safeGetSession();
  // console.log('Layout server session:', session);
  // console.log('Layout server user:', user);

  return {
    session,
    user,
    cookies: cookies.getAll(),
  };
};