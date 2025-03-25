import { createClient } from "jsr:@supabase/supabase-js@2";

const env = (key: string) => Deno.env.get(key);

export function getSupabaseClient() {
  const supabase = createClient(
    env("SUPABASE_URL")!,
    env("SUPABASE_SERVICE_ROLE_KEY")!
  );
  if (!supabase) {
    throw new Error("Supabase failed to initialize");
  }
  return supabase;
}