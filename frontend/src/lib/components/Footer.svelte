<script>
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';

	// Fonction pour gérer la déconnexion (si nécessaire)
	function handleLogout() {
		// Logique de déconnexion (à implémenter selon votre système d’authentification)
		userProfileStore.set(null); // Simulé ici, remplacez par votre logique de déconnexion
	}
</script>

<footer class="bg-blue-900 py-12 text-white">
	<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<div class="grid grid-cols-1 gap-8 md:grid-cols-3">
			<!-- Slogan -->
			<div>
				<h3 class="mb-4 text-lg font-semibold">{$i18n.footer.slogan}</h3>
			</div>

			<!-- Liens de navigation -->
			<div>
				<h3 class="mb-4 text-lg font-semibold">Navigation</h3>
				<ul class="space-y-3">
					<li>
						<a href="/my-articles" class="hover:underline">{$i18n.footer.myArticles}</a>
					</li>
					<li>
						<a href="/articles" class="hover:underline">{$i18n.footer.articles}</a>
					</li>
					<li>
						{#if $userProfileStore}
							<a href="/account" class="hover:underline">{$i18n.footer.account}</a>
							<!-- Vous pouvez ajouter un lien/bouton de déconnexion ici si nécessaire -->
							<!-- <button on:click={handleLogout} class="hover:underline">Déconnexion</button> -->
						{/if}
					</li>
				</ul>
			</div>

			<!-- Bouton S'inscrire (si non connecté) -->
			<div>
				{#if !$userProfileStore}
					<h3 class="mb-4 text-lg font-semibold">Rejoignez-nous</h3>
					<a
						href="/signup"
						class="inline-block rounded-full border-2 border-white px-6 py-2 text-white transition-colors duration-200 hover:bg-white hover:text-blue-900"
					>
						{$i18n.footer.signup}
					</a>
				{/if}
			</div>
		</div>

		<!-- Ligne de séparation -->
		<hr class="my-8 border-gray-600" />

		<!-- Mention de droits d’auteur -->
		<div class="text-center text-sm text-gray-400">
			&copy; {new Date().getFullYear()} Veille Médicale. Tous droits réservés.
		</div>
	</div>
</footer>
