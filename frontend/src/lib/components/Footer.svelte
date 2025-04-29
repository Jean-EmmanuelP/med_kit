<script>
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { supabase } from '$lib/supabase'; // Import supabase client
	import { goto } from '$app/navigation'; // Import goto for navigation

	async function handleLogout() {
		try {
			const { error } = await supabase.auth.signOut();
			if (error) throw error;
			userProfileStore.set(null); // Clear local store
			goto('/'); // Redirect to home after logout
		} catch (error) {
			console.error('Error logging out:', error.message);
			// Optionally display an error message to the user
		}
	}
</script>

<footer class="bg-black py-12 text-white">
	<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<div class="grid grid-cols-1 gap-y-8 gap-x-6 md:grid-cols-5">
			<!-- Slogan -->
			<div>
				<h3 class="mb-4 text-lg font-semibold">{$i18n.footer.slogan}</h3>
			</div>

			<!-- Liens de navigation -->
			<div>
				<h3 class="mb-4 text-lg font-semibold">Navigation</h3>
				<ul class="space-y-3">
					<li>
						<a href="/ma-veille" class="hover:underline">{$i18n.footer.myArticles}</a>
					</li>
					<li>
						<a href="/articles" class="hover:underline">{$i18n.footer.articles}</a>
					</li>
					<li>
						<a href="/favoris" class="hover:underline">Favoris</a>
					</li>
					<li>
						<a href="/qui-sommes-nous" class="hover:underline">Qui sommes-nous ?</a>
					</li>
					<li>
						<a href="/comite" class="hover:underline">Comité scientifique</a>
					</li>
					<li>
						{#if $userProfileStore}
							<a href="/account" class="hover:underline">{$i18n.footer.account}</a>
						{/if}
					</li>
				</ul>
			</div>

			<!-- Section Soutenez-nous -->
			<div>
				<h3 class="mb-4 text-lg font-semibold">Soutenez-nous</h3>
				<a
					href="/donations"
					class="inline-block rounded-full border-2 border-white px-6 py-2 text-sm text-white transition-colors duration-200 hover:bg-white hover:text-black focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-black"
				>
					Faire un don
				</a>
			</div>

			<!-- Section Réseaux Sociaux / Rejoignez-nous -->
			<div>
				{#if !$userProfileStore}
					<!-- Show Signup Button if not logged in -->
					<h3 class="mb-4 text-lg font-semibold">Rejoignez-nous</h3>
					<a
						href="/signup"
						class="inline-block rounded-full border-2 border-white px-6 py-2 text-sm text-white transition-colors duration-200 hover:bg-white hover:text-black focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-black"
					>
						{$i18n.footer.signup}
					</a>
				{:else}
					<!-- Show LinkedIn Icon if logged in (or always) -->
					<h3 class="mb-4 text-lg font-semibold">Suivez-nous</h3>
					<div class="flex items-center space-x-4">
						<!-- LinkedIn Icon Link -->
						<a
							href="https://www.linkedin.com/in/baptiste-mazas-577219182/"
							target="_blank"
							rel="noopener noreferrer"
							aria-label="Suivez Baptiste Mazas sur LinkedIn"
							title="Suivez Baptiste Mazas sur LinkedIn"
							class="text-gray-400 transition-colors duration-200 hover:text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-black rounded-full"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-7 w-7"
								fill="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"
								/>
							</svg>
						</a>
						<!-- Add other social icons here if needed -->
					</div>
				{/if}
			</div>

			<!-- Section Contact -->
			<div>
				<h3 class="mb-4 text-lg font-semibold">Contact</h3>
				<a
					href="mailto:contact@veillemedicale.fr"
					class="mt-1 inline-block text-base text-gray-300 hover:text-white hover:underline"
				>
					contact@veillemedicale.fr
				</a>
			</div>
		</div>

		<!-- Ligne de séparation -->
		<hr class="my-8 border-gray-600" />

		<!-- Mention de droits d'auteur et Déconnexion -->
		<div class="flex flex-col items-center justify-between gap-4 text-sm text-gray-400 sm:flex-row">
			<span>© {new Date().getFullYear()} Veille Médicale. Tous droits réservés.</span>
			{#if $userProfileStore}
				<button
					on:click={handleLogout}
					class="text-gray-400 transition-colors duration-200 hover:text-white hover:underline focus:outline-none focus:ring-1 focus:ring-white focus:ring-offset-1 focus:ring-offset-black rounded"
				>
					Déconnexion
				</button>
			{/if}
		</div>
	</div>
</footer>