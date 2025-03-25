import "jsr:@supabase/functions-js/edge-runtime.d.ts";

Deno.serve(async (req: Request) => {
  const body = await req.json();
  const { emails, template_id } = body as { emails: string[], template_id: string };

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
    personalizations: emails.map(email => ({
      to: [{ email }],
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
    console.error("Erreur lors de l'envoi de l'email :", error);
    return new Response(
      JSON.stringify({
        error: "Échec de l'envoi de l'email",
        details: error.message,
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
})