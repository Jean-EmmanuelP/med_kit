<!-- /routes/test-session/+page.svelte -->
<script>
  import { supabase } from '$lib/supabase';
  import { onMount } from 'svelte';

  let session = null;
  let user = null;
  let sessionError = null;
  let userError = null;
  let serverCookies = null;
  let manualSession = null;
  export let data;

  console.log('Server-side session from data:', data.session);
  console.log('Server-side user from data:', data.user);

  onMount(async () => {
    // Test cookie transmission via same-origin request
    console.log('Fetching cookies from /api/cookies');
    const cookieResponse = await fetch('/api/cookies');
    serverCookies = await cookieResponse.json();
    console.log('Server cookies received:', serverCookies);

    // Manual fetch to Supabase Auth API
    console.log('Attempting manual fetch to Supabase Auth API');
    try {
      const manualResponse = await fetch(`${PUBLIC_SUPABASE_URL}/auth/v1/session`, {
        method: 'GET',
        headers: {
          'apikey': PUBLIC_SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${serverCookies.accessToken}`,
        },
        credentials: 'include',
      });
      manualSession = await manualResponse.json();
      console.log('Manual fetch session response:', manualSession);
    } catch (err) {
      console.error('Manual fetch error:', err);
    }

    // Client-side session retrieval
    console.log('Attempting client-side session retrieval');
    const { data: sessionData, error: sessError } = await supabase.auth.getSession();
    if (sessError) {
      console.error('Client-side session retrieval error:', sessError);
      sessionError = sessError.message;
    }
    session = sessionData.session;
    console.log('Client-side session:', session);

    // Client-side user retrieval
    console.log('Attempting client-side user retrieval');
    const { data: userData, error: usrError } = await supabase.auth.getUser();
    if (usrError) {
      console.error('Client-side user retrieval error:', usrError);
      userError = usrError.message;
    }
    user = userData.user;
    console.log('Client-side user:', user);
  });
</script>

<h1>Test Session</h1>
<p>Server-side session: {data.session ? 'Present' : 'Missing'}</p>
<p>Server-side user: {data.user ? 'Present' : 'Missing'}</p>
<p>Server cookies: {serverCookies ? JSON.stringify(serverCookies) : 'Loading...'}</p>
<p>Manual fetch session: {manualSession ? JSON.stringify(manualSession) : 'Not fetched'}</p>
<p>Client-side session: {session ? 'Present' : 'Missing'}</p>
<p>Client-side user: {user ? 'Present' : 'Missing'}</p>
{#if sessionError}
  <p>Session Error: {sessionError}</p>
{/if}
{#if userError}
  <p>User Error: {userError}</p>
{/if}