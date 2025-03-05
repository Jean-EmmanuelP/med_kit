<!-- +layout.svelte -->
<script lang="ts">
	import '../app.css';
	import Header from '$lib/components/Header.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import userProfile from '$lib/stores/user';
	import { invalidate } from '$app/navigation';
	import { supabaseStore } from '$lib/stores/supabase';
	import { onMount } from 'svelte';

	const getUserProfile = async function (supabase: any, userId: string) {
		try {
			if (!userId) {
				return null;
			}
			const { data, error } = await supabase
				.from('user_profiles')
				.select('*')
				.eq('id', userId)
				.single();
			if (error) throw error;
			userProfile.set(data);
			return data;
		} catch (error) {
			console.error('Error fetching user profile:', error);
			return null;
		}
	};

	let { data, children } = $props();
	let { session, supabase, user } = $derived(data);

	supabaseStore.set(supabase);

	// Fetch user profile if user exists and userProfile is not set
	$effect(() => {
		if (user?.id && !$userProfile) {
			getUserProfile(supabase, user.id);
		}
	});

	onMount(() => {
		console.log('User Profile on mount:', $userProfile);

		const { data: subscription } = supabase.auth.onAuthStateChange((event, newSession) => {
			console.log('Auth state changed:', event, newSession);
			if (newSession?.expires_at !== session?.expires_at) {
				invalidate('supabase:auth');
			}
		});

		return () => subscription.subscription.unsubscribe();
	});
</script>

<svelte:head>
	<!-- Charger le fichier de polices personnalisées -->
	<link rel="stylesheet" href="/fonts.css" />
</svelte:head>

<div class="font-display relative flex flex-col">
	<Header />
	<div class="mt-[15%] sm:mt-[3.5%]">
		{@render children()}
	</div>
	<Footer />
</div>
