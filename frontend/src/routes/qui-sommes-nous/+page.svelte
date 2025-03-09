<script>
    import { page } from '$app/stores';
    import { i18n } from '$lib/i18n'; // Importation comme vous l'utilisez

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
        }
    ];

    // Préparer le contenu de suggestion avec des classes Tailwind
    const suggestionHtml = $i18n.us.suggestion.replace(
        '<a href="mailto:contact@veillemedicale.fr">contact@veillemedicale.fr</a>',
        '<a href="mailto:contact@veillemedicale.fr" class="text-black font-semibold hover:underline hover:text-gray-700">contact@veillemedicale.fr</a>'
    );
</script>

<svelte:head>
    <title>{$i18n.us.title} - Veille Médicale</title>
    <meta name="description" content="Découvrez l'équipe derrière Veille Médicale, un outil conçu pour les médecins par Baptiste Mazas et Jean-Emmanuel Perramant." />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
</svelte:head>

<div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 text-gray-800 leading-relaxed">
    <!-- En-tête -->
    <header class="text-center py-10">
        <h1 class="text-4xl sm:text-5xl font-bold text-black mb-4">{$i18n.us.title}</h1>
    </header>

    <!-- Contenu principal -->
    <main class="space-y-12">
        {#each founders as founder}
            <section class="flex flex-col md:flex-row items-center bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-transform hover:-translate-y-1">
                <img src={founder.photo} alt="{founder.name} photo" class="w-32 h-32 sm:w-40 sm:h-40 object-cover rounded-full border-4 border-black mb-6 md:mb-0 md:mr-6" loading="lazy" />
                <div class="flex-1 text-center md:text-left">
                    <h2 class="text-2xl sm:text-3xl font-semibold text-black mb-2">{founder.name}</h2>
                    <p class="text-gray-600 text-base sm:text-lg font-normal">{@html founder.description}</p>
                </div>
            </section>
        {/each}

        <section class="text-center bg-white p-6 rounded-lg shadow-md">
            <p class="text-lg sm:text-xl font-medium text-gray-800">{@html suggestionHtml}</p>
        </section>
    </main>
</div>