import { serve } from "https://deno.land/std@0.224.0/http/server.ts";

console.log('Edge Function "send-welcome-email" démarrée');

serve(async (req) => {
  const body = await req.json();
  const { user_id, email, first_name } = body;

  // Validation des champs requis
  if (!user_id || !email || !first_name) {
    return new Response(
      JSON.stringify({
        error: "Les champs user_id, email et first_name sont requis",
      }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  const apiKey = Deno.env.get("SENDGRID_API_KEY");
  if (!apiKey) {
    console.error("Clé API SendGrid manquante");
    return new Response(
      JSON.stringify({ error: "Clé API SendGrid manquante" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  // Corps de la requête pour SendGrid
  const sendgridPayload = {
    personalizations: [
      {
        to: [{ email }],
        dynamic_template_data: {
          first_name,
          base_url: "https://veillemedicale.fr",
        },
      },
    ],
    from: {
      email: "contact@veillemedicale.fr",
      name: "Équipe Veille Médicale",
    },
    template_id: "d-da9d98610ccf4169874f4b2d648a24c8",
  };

  try {
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

    return new Response(
      JSON.stringify({ message: "Email de bienvenue envoyé avec succès" }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  } catch (error) {
    console.error("Erreur lors de l’envoi de l’email :", error);
    return new Response(
      JSON.stringify({
        error: "Échec de l’envoi de l’email",
        details: error.message,
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
});