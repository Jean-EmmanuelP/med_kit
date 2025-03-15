import { serve } from "https://deno.land/std@0.224.0/http/server.ts";

console.log('Edge Function "send-notification" démarrée');

serve(async (req) => {
  const body = await req.json();

  const { user_id, email, first_name, articles, headers } = body;

  if (!email || !first_name || !articles || !Array.isArray(articles)) {
    return new Response(
      JSON.stringify({
        error: "Les champs email, first_name et articles (tableau) sont requis",
      }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  const apiKey = Deno.env.get("SENDGRID_API_KEY");
  console.log("Clé API SendGrid :", apiKey);
  if (!apiKey) {
    console.error("Clé API SendGrid manquante");
    return new Response(
      JSON.stringify({ error: "Clé API SendGrid manquante" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  const requestHeaders = headers || {
    Authorization: `Bearer ${
      Deno.env.get("SUPABASE_ANON_KEY") ||
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }`, // Replace with actual key
    "Content-Type": "application/json",
  };

  try {
    const response = await fetch("https://api.sendgrid.com/v3/mail/send", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        personalizations: [
          {
            to: [{ email }],
            dynamic_template_data: {
              first_name: first_name,
              articles: articles.map((article) => ({
                id: article.id,
                title: article.title,
                journal: article.journal || "Inconnu", // Ajout du journal
              })),
            },
          },
        ],
        from: {
          email: "contact@veillemedicale.fr",
          name: "Dr Baptiste Mazas - Veille Médicale",
        },
        template_id: "d-27f89a4f0faa4df1ab83b9fbc7be19a1",
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Erreur SendGrid: ${response.statusText} - ${errorText}`);
    }

    return new Response(
      JSON.stringify({ message: "Notification envoyée avec succès" }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  } catch (error) {
    console.error("Erreur lors de l’envoi :", error);
    return new Response(
      JSON.stringify({
        error: "Échec de l’envoi",
        details: error.message,
        status: error.status || 500,
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
});
