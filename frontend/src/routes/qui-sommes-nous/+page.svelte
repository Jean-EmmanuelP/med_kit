<script>
	import { i18n } from '$lib/i18n';

	// Définir les données statiques pour les co-fondateurs
	const founders = [
		{
			name: $i18n.us.baptiste.name,
			photo: $i18n.us.baptiste.photo,
			description: $i18n.us.baptiste.description
		},
		{
			name: $i18n.us.jeanemmanuel.name,
			photo: $i18n.us.jeanemmanuel.photo,
			description: $i18n.us.jeanemmanuel.description
		},
		{
			name: $i18n.us.alexis.name,
			photo: $i18n.us.alexis.photo,
			description: $i18n.us.alexis.description
		}
	];

	// Préparer le contenu de suggestion avec des classes Tailwind
	const suggestionHtml = $i18n.us.suggestion.replace(
		'<a href="mailto:contact@veillemedicale.fr">contact@veillemedicale.fr</a>',
		'<a href="mailto:contact@veillemedicale.fr" class="text-teal-400 font-semibold hover:underline hover:text-teal-300">contact@veillemedicale.fr</a>'
	);
</script>

<svelte:head>
	<title>{$i18n.us.title} - Veille Médicale</title>
	<meta
		name="description"
		content="Découvrez l'équipe derrière Veille Médicale, un outil conçu pour les médecins par Baptiste Mazas et Jean-Emmanuel Perramant."
	/>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
	<link
		href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

<div class="min-h-screen bg-black px-4 py-12 text-white">
	<div class="mx-auto max-w-4xl">
		<!-- En-tête -->
		<header class="py-10 text-center">
			<h1 class="mb-4 text-4xl font-bold text-white sm:text-5xl">{$i18n.us.title}</h1>
		</header>

		<!-- Contenu principal -->
		<main class="space-y-12">
			{#each founders as founder}
				<section
					class="flex flex-col items-center rounded-lg bg-gray-800 p-6 shadow-md transition-all duration-300 hover:shadow-lg md:flex-row"
				>
					<img
						src={founder.photo}
						alt="{founder.name} photo"
						class="mb-6 h-40 w-40 rounded-md border-2 border-teal-500 object-cover md:mr-6 md:mb-0"
						loading="lazy"
					/>
					<div class="flex-1 text-center md:text-left">
						<h2 class="mb-2 text-2xl font-semibold text-white sm:text-3xl">{founder.name}</h2>
						<p class="text-base font-normal text-gray-300 sm:text-lg">
							{@html founder.description}
						</p>
					</div>
				</section>
			{/each}

			<section class="rounded-lg bg-gray-800 p-6 text-center shadow-md">
				<p class="text-lg font-medium text-gray-200 sm:text-xl">{@html suggestionHtml}</p>
			</section>
		</main>
	</div>
</div>

<style>
	/* Style général */
	button:focus {
		outline: none;
	}
	.animate-bounce {
		animation: bounce 2s infinite;
	}

	@keyframes bounce {
		0%,
		20%,
		50%,
		80%,
		100% {
			transform: translateY(0);
		}
		40% {
			transform: translateY(-10px);
		}
		60% {
			transform: translateY(-5px);
		}
	}

	/* Animation d'entrée pour le modal (si nécessaire) */
	.modal-enter-active {
		animation: fadeIn 0.3s ease-out;
	}

	@keyframes fadeIn {
		0% {
			opacity: 0;
			transform: scale(0.95);
		}
		100% {
			opacity: 1;
			transform: scale(1);
		}
	}
</style>
