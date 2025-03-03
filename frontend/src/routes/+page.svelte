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
			goto('/articles');
		}
	}
</script>

<main class="relative flex min-h-screen flex-col bg-black text-white">
	<!-- Veille Section -->
	<div class="relative flex-auto space-y-8 px-4 py-8 md:px-16 md:py-12">
		<!-- Main content -->
		<div
			class="flex max-w-full flex-col items-center gap-6 text-center md:max-w-[70%] md:items-start md:text-left"
		>
			<!-- Title -->
			<h1
				class="font-display text-4xl font-thin tracking-tight drop-shadow-lg md:text-5xl lg:text-6xl"
			>
				{$i18n.home.title}
			</h1>

			<!-- Subtitle -->
			<p class="font-serif text-lg font-light drop-shadow-md md:text-xl">
				{$i18n.home.subtitle}
			</p>

			<!-- Question with emoji -->
			<p class="flex items-center justify-center gap-2 text-base md:justify-start md:text-lg">
				<span class="text-yellow-400">🧑‍🎓</span>
				{$i18n.home.phrase1}
			</p>

			<!-- Highlighted section: Veille vous livre l’essentiel -->
			<div class="flex w-full flex-col gap-4">
				<p
					class="flex items-center justify-center gap-2 text-xl font-semibold md:justify-start md:text-2xl"
				>
					<span class="text-yellow-400">⚡</span>
					{$i18n.home.phrase2}
				</p>
				<ul class="space-y-2">
					{#each $i18n.home.arguments.list as argument}
						<li class="flex items-start justify-center gap-2 text-base md:justify-start md:text-lg">
							<span class="text-green-400">✔</span>
							{argument}
						</li>
					{/each}
				</ul>
			</div>

			<!-- Timing note with emoji -->
			<p class="flex items-center justify-center gap-2 text-base md:justify-start md:text-lg">
				<span class="text-red-400">📧</span>
				{$i18n.home.arguments.cta}
			</p>
			<!-- Top-right button (Ma veille or S'inscrire) -->
			<div class="">
				<a
					href={$userProfileStore ? '/articles' : '/signup'}
					on:click={handleVeilleClick}
					class="inline-block w-[30vw] rounded-full bg-gray-700 px-4 py-2 text-center text-sm font-medium text-white transition-colors duration-200 hover:bg-gray-600 md:px-6 md:py-3 md:text-base"
				>
					{$userProfileStore ? $i18n.home.hero.viewArticles : $i18n.home.hero.signupForVeille}
				</a>
			</div>
		</div>
	</div>
</main>
