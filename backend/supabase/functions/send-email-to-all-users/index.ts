import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const env = (key: string) => Deno.env.get(key);
const USERS_BATCH_SIZE = 1000;

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
Deno.serve(async (req: Request) => {
  try {
    const body = await req.json();
    const supabase = getSupabaseClient();
    const { template_id } = body as { template_id: string };

    const apiKey = Deno.env.get("SENDGRID_API_KEY");
    if (!apiKey) {
      console.error("Clé API SendGrid manquante");
      return new Response(
        JSON.stringify({ error: "Clé API SendGrid manquante" }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      );
    }

    // Fetch users in batches
    let from = 0;
    let hasMore = true;
    let totalEmailsSent = 0;

    while (hasMore) {
      const { data: users, error } = await supabase
        .from("user_profiles")
        .select("email")
        .range(from, from + USERS_BATCH_SIZE - 1);

      if (error) {
        throw new Error(`Error fetching users: ${error.message}`);
      }

      if (!users || users.length === 0) {
        hasMore = false;
        break;
      }

      // Prepare SendGrid payload for this batch
      const sendgridPayload = {
        personalizations: users.map(user => ({
          to: [{ email: user.email }],
          dynamic_template_data: {
            base_url: "https://veillemedicale.fr",
          },
        })),
        from: {
          email: "contact@veillemedicale.fr",
          name: "Équipe Veille Médicale",
        },
        template_id: template_id,
      };

      // Send emails for this batch
      const response = await fetch("https://api.sendgrid.com/v3/mail/send", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(sendgridPayload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Erreur SendGrid: ${response.statusText} - ${errorText}`);
      }

      totalEmailsSent += users.length;
      from += USERS_BATCH_SIZE;
    }

    return new Response(
      JSON.stringify({ 
        message: "Emails envoyés avec succès", 
        totalEmailsSent 
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );

  } catch (error) {
    console.error("Erreur:", error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
});