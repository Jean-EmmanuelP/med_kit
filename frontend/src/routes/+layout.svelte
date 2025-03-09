<script lang="ts">
	import '../app.css';
	import Header from '$lib/components/Header.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import userProfile from '$lib/stores/user';
	import { invalidate } from '$app/navigation';
	import { supabaseStore } from '$lib/stores/supabase';
	import { onMount } from 'svelte';
	import NProgress from 'nprogress';
	import { navigating } from '$app/stores';
	import 'nprogress/nprogress.css';

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

	$effect(() => {
		if (user?.id) {
			if (!$userProfile || $userProfile?.id !== user.id) {
				getUserProfile(supabase, user.id).then((profile) => {
					if (!profile) userProfile.set({ id: user.id, ...user }); // Fallback avec les données de l'utilisateur
				});
			}
		} else {
			userProfile.set(null);
		}
	});

	onMount(() => {
		console.log('User Profile on mount:', $userProfile);

		const { data: subscription } = supabase.auth.onAuthStateChange((event, newSession) => {
			console.log('Auth state changed:', event, newSession);
			if (event === 'SIGNED_OUT') {
				userProfile.set(null);
				invalidate('supabase:auth');
			} else if (newSession?.expires_at !== session?.expires_at) {
				invalidate('supabase:auth');
			}
		});

		return () => subscription.subscription.unsubscribe();
	});

	$effect(() => {
		if ($navigating) {
			NProgress.start();
		} else {
			NProgress.done();
		}
	});
</script>

<svelte:head>
	<link rel="stylesheet" href="/fonts.css" />
</svelte:head>

<div class="font-display relative flex flex-col">
	<Header />
	<div class="mt-[15%] sm:mt-[3.5%]">
		{@render children()}
	</div>
	<Footer />
</div>

<style>
	.app {
		min-height: 100vh;
	}
	/* Personnaliser NProgress pour une barre bleue comme YouTube */
	#nprogress .bar {
		background: #1a73e8; /* Couleur bleue */
		height: 4px;
	}
	#nprogress .peg {
		box-shadow:
			0 0 10px #1a73e8,
			0 0 5px #1a73e8;
	}
</style>
