<script lang="ts">
	import { i18n } from '$lib/i18n';

	interface Founder {
		name: string;
		photo: string;
		description: string;
		linkedin?: string;
	}

	const founders: Founder[] = [
		{
			name: $i18n.us.baptiste.name,
			photo: $i18n.us.baptiste.photo,
			description: $i18n.us.baptiste.description,
			linkedin: $i18n.us.baptiste.linkedin
		},
		{
			name: $i18n.us.jeanemmanuel.name,
			photo: $i18n.us.jeanemmanuel.photo,
			description: $i18n.us.jeanemmanuel.description,
			linkedin: $i18n.us.jeanemmanuel.linkedin
		}
	];

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
			{#each founders as founder (founder.name)}
				<section
					class="flex flex-col items-center rounded-lg bg-gray-800 p-6 shadow-md transition-all duration-300 hover:shadow-lg md:flex-row md:items-start"
				>
					<img
						src={founder.photo}
						alt="{founder.name} photo"
						class="mb-6 h-32 w-32 flex-shrink-0 rounded-lg border-2 border-teal-500 object-cover md:h-40 md:w-40 md:mr-6 md:mb-0"
						loading="lazy"
					/>
					<div class="flex-1 text-center md:text-left">
						<!-- Name and Inline LinkedIn Icon -->
						<h2 class="mb-3 text-xl font-semibold text-white sm:text-2xl lg:text-3xl">
							{founder.name}
							{#if founder.linkedin}
								<a
									href={founder.linkedin}
									target="_blank"
									rel="noopener noreferrer"
									aria-label="Profil LinkedIn de {founder.name}"
									title="Profil LinkedIn de {founder.name}"
									class="linkedin-badge ml-2 inline-block transform translate-y-[-2px] rounded bg-gray-700 p-[3px] align-middle transition-colors duration-200 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-gray-800"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-5 w-5 text-gray-300"
										fill="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"
										/>
									</svg>
								</a>
							{/if}
						</h2>
						<!-- Description -->
						<p class="text-base font-normal leading-relaxed text-gray-300 sm:text-lg">
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
