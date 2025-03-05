<script>
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { goto } from '$app/navigation';

	// Function to handle the "Ma veille" or "S'inscrire" button click
	function handleVeilleClick(event) {
		event.preventDefault();
		if (!$userProfileStore) {
			goto('/signup');
		} else {
			goto('/ma-veille');
		}
	}
</script>

<main class="relative flex min-h-screen flex-col bg-gradient-to-br from-black to-gray-900 text-white">
	<!-- Hero Section -->
	<div class="relative flex-auto space-y-10 px-6 py-12 md:px-20 md:py-16 lg:px-32 lg:py-20">
		<!-- Main content -->
		<div
			class="flex max-w-full flex-col items-center gap-8 text-center md:max-w-[70%] md:items-start md:text-left"
		>
			<!-- Title with gradient effect inspired by Livana -->
			<h1
				class="font-display text-4xl font-bold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-green-400 md:text-5xl lg:text-6xl"
			>
				{$i18n.home.title}
			</h1>

			<!-- Subtitle with subtle animation -->
			<p class="font-sans text-lg font-light text-gray-300 md:text-xl animate-fade-in">
				{$i18n.home.subtitle}
			</p>

			<!-- Question with emoji -->
			<p class="flex items-center justify-center gap-3 text-base md:justify-start md:text-lg text-gray-200">
				<span class="text-yellow-400 text-2xl animate-bounce">🧑‍🎓</span>
				{$i18n.home.phrase1}
			</p>

			<!-- Highlighted section: Veille vous livre l’essentiel -->
			<div class="flex w-full flex-col gap-6">
				<p
					class="flex items-center justify-center gap-3 text-xl font-semibold md:justify-start md:text-2xl text-white"
				>
					<span class="text-yellow-400 text-2xl">⚡</span>
					{$i18n.home.phrase2}
				</p>
				<ul class="space-y-3">
					{#each $i18n.home.arguments.list as argument}
						<li class="flex items-start justify-center gap-3 text-base md:justify-start md:text-lg text-gray-300">
							<span class="text-green-400 text-xl">✔</span>
							{argument}
						</li>
					{/each}
				</ul>
			</div>

			<!-- Timing note with emoji -->
			<p class="flex items-center justify-center gap-3 text-base md:justify-start md:text-lg text-gray-200">
				<span class="text-red-400 text-2xl">📧</span>
				{$i18n.home.arguments.cta}
			</p>

			<!-- CTA Button with Livana-inspired styling -->
			<div class="mt-6">
				<a
					href={$userProfileStore ? '/articles' : '/signup'}
					on:click={handleVeilleClick}
					class="inline-block w-[50vw] md:w-auto rounded-full bg-gradient-to-r from-blue-500 to-green-500 px-8 py-3 text-center text-base font-semibold text-white shadow-lg transition-all duration-300 hover:from-blue-600 hover:to-green-600 hover:shadow-xl md:px-10 md:py-4 md:text-lg"
				>
					{$userProfileStore ? $i18n.home.hero.viewArticles : $i18n.home.hero.signupForVeille}
				</a>
			</div>
		</div>
	</div>

	<!-- Optional decorative element inspired by Livana -->
	<div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-green-500 opacity-50"></div>
</main>

<style>
	/* Fade-in animation for subtitle */
	@keyframes fade-in {
		0% { opacity: 0; transform: translateY(10px); }
		100% { opacity: 1; transform: translateY(0); }
	}
	.animate-fade-in {
		animation: fade-in 1s ease-out;
	}

	/* Bounce animation for emojis */
	@keyframes bounce {
		0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
		40% { transform: translateY(-10px); }
		60% { transform: translateY(-5px); }
	}
	.animate-bounce {
		animation: bounce 2s infinite;
	}
</style>