import { serve } from 'https://deno.land/std@0.224.0/http/server.ts';

console.log('Edge Function "send-notification" démarrée');

serve(async (req) => {
  const { user_id, email, body } = await req.json();

  // Vérifier que les champs requis sont présents
  if (!email || !body) {
    return new Response(
      JSON.stringify({ error: 'Les champs email et body sont requis' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  // Récupérer la clé API SendGrid et vérifier qu'elle est présente
  const apiKey = Deno.env.get('SENDGRID_API_KEY');
  console.log('Clé API SendGrid :', apiKey); // Pour le débogage
  if (!apiKey) {
    console.error('Clé API SendGrid manquante');
    return new Response(
      JSON.stringify({ error: 'Clé API SendGrid manquante' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }

  try {
    const response = await fetch('https://api.sendgrid.com/v3/mail/send', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        personalizations: [{ to: [{ email }] }],
        from: {
          email: 'contact@veillemedicale.fr',
          name: 'Dr Baptiste Mazas - Veille Médicale'
        },
        subject: 'Vos articles quotidiens - Veille',
        content: [
          {
            type: 'text/html',
            value: `<p style="font-family: Arial, sans-serif; color: #333;">${body.replace(/\n/g, '<br>')}</p>`
          }
        ]
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Erreur SendGrid: ${response.statusText} - ${errorText}`);
    }

    return new Response(
      JSON.stringify({ message: 'Notification envoyée avec succès' }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    console.error('Erreur lors de l’envoi de la notification :', error);
    return new Response(
      JSON.stringify({ 
        error: 'Échec de l’envoi de la notification',
        details: error.message,
        status: error.status || 500
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
});