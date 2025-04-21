<script lang="ts">
	// Define the referent data directly in the script
	// Pre-sorted alphabetically by specialty for easier rendering
	const referents = [
        {
            specialty: 'Chirurgie orthopédique',
            name: 'Dr Félix Barbier',
            title: 'Docteur Junior en chirurgie orthopédique',
            affiliation: 'AP-HP',
            focus: 'Spécialiste en chirurgie de la main'
        },
		{
			specialty: 'Chirurgie pédiatrique',
			name: 'Dr Camille Girardin',
			title: 'Docteur Junior en chirurgie pédiatrique',
            affiliation: 'CHU de Lille',
			focus: 'Spécialiste en chirurgie ortho-pédiatrique'
		},
		{
			specialty: 'Endocrinologie – Diabétologie – Nutrition',
			name: 'Dr Baptiste Mazas',
			title: 'Interne en Endocrinologie-Diabétologie-Nutrition',
            affiliation: 'AP-HP',
			focus: 'Diabétologie, Nutrition, Prévention Cardiovasculaire, Médecine du Sport'
		},
        {
			specialty: 'Endocrinologie – Diabétologie – Nutrition',
			name: 'Dr Flora Lambert',
			title: 'Interne en Endocrinologie-Diabétologie-Nutrition',
            affiliation: 'AP-HP',
			focus: null // No specific focus listed
		},
        {
			specialty: 'Hématologie',
			name: 'Dr Alexis Talbot',
			title: 'MCU-PH, service d\'Immuno-Hématologie',
            affiliation: 'Hôpital Saint-Louis (AP-HP)',
			focus: 'Spécialiste en myélome multiple, immunothérapie, CAR-T cells'
		},
		{
			specialty: 'Neurochirurgie',
			name: 'Dr Gonzague Defrance',
			title: 'Docteur Junior en neurochirurgie',
            affiliation: 'AP-HP',
			focus: 'Spécialiste en chirurgie fonctionnelle'
		},
		{
			specialty: 'Rhumatologie',
			name: 'Dr Elisabetta Lanciano',
			title: 'Rhumatologie',
            affiliation: 'CH d\'Angoulême',
			focus: null // No specific focus listed
		},
		{
			specialty: 'Urgences',
			name: 'Dr Benjamin Chevallier',
			title: 'Médecine d\'urgence',
            affiliation: 'SAMU de Paris – SMUR Necker – Urgences adultes Paris Saint-Joseph, AP-HP',
			focus: null // No specific focus listed
		},
		{
			specialty: 'Urologie',
			name: 'Dr Maxime Pattou',
			title: 'Docteur Junior en urologie',
            affiliation: 'AP-HP',
			focus: 'Spécialiste en uro-oncologie'
		}
	];

    // Define the missions
    const missions = [
        "Être référent(e) d\'une spécialité ou sous-spécialité",
        "Proposer des articles scientifiques pertinents à relayer",
        "Apporter des corrections aux synthèses générées par notre IA",
        "Valoriser votre engagement académique (mention sur le site, etc.)",
        "Rejoindre un réseau interdisciplinaire et engagé"
    ];

    // Helper to group referents by specialty for rendering headings correctly
    let currentSpecialty = '';
    let showForm = false;
    let showModal = false;
    let modalContent = '';
    let formData = {
        prenom: '',
        nom: '',
        statut: '',
        specialite: '',
        surSpecialite: '',
        centre: ''
    };

    function handleSubmit() {
        const subject = "Candidature au comité scientifique";
        const body = `Bonjour,

Je souhaite rejoindre le comité scientifique de Veille Médicale.

Informations :
- Prénom : ${formData.prenom}
- Nom : ${formData.nom}
- Statut : ${formData.statut}
- Spécialité : ${formData.specialite}
- Sur-spécialité : ${formData.surSpecialite}
- Centre d'exercice : ${formData.centre}

Cordialement,
${formData.prenom} ${formData.nom}`;

        const mailtoLink = `mailto:contact@veillemedicale.fr?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
        
        // Try to open mailto link
        const mailtoWindow = window.open(mailtoLink, '_blank');
        
        // If mailto fails to open (window is null or closed), show modal
        if (!mailtoWindow || mailtoWindow.closed) {
            modalContent = `Adresse email : contact@veillemedicale.fr\n\nSujet : ${subject}\n\nMessage :\n${body}`;
            showModal = true;
        }
    }

    function closeModal() {
        showModal = false;
        modalContent = '';
    }

    // Function to get specialty-specific emoji
    function getSpecialtyEmoji(specialty: string): string {
        const emojiMap: Record<string, string> = {
            'Chirurgie orthopédique': '🦴',
            'Chirurgie pédiatrique': '👶',
            'Endocrinologie – Diabétologie – Nutrition': '⚖️',
            'Hématologie': '🩸',
            'Neurochirurgie': '🧠',
            'Rhumatologie': '🦵',
            'Urgences': '🚑',
            'Urologie': '💧'
        };
        return emojiMap[specialty] || '⚕️';
    }
</script>

<svelte:head>
	<title>Comité Scientifique - Veille Médicale</title>
	<meta
		name="description"
		content="Découvrez les médecins référents par spécialité du comité scientifique de Veille Médicale."
	/>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
	<link
		href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

<div class="min-h-screen bg-black px-4 py-12 pt-20 text-white font-sans">
	<div class="mx-auto max-w-4xl">
		<!-- En-tête -->
		<header class="mb-12 text-center">
			<h1 class="mb-4 text-4xl font-bold text-white sm:text-5xl">
                🏥 Référents par spécialité
            </h1>
            <!-- <p class="text-lg text-gray-400">(classés par ordre alphabétique de spécialité)</p> -->
		</header>

        <!-- Section Missions -->
        <section class="mb-16 rounded-lg bg-gray-800 p-6 shadow-lg">
            <h2 class="mb-6 text-center text-2xl font-semibold text-white sm:text-3xl">
                📋 Les missions des membres
            </h2>
            <ul class="list-disc space-y-3 pl-6 text-gray-300">
                {#each missions as mission}
                    <li>{mission}</li>
                {/each}
            </ul>
            <div class="mt-6 text-center">
                <button 
                    on:click={() => showForm = !showForm}
                    class="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                    {showForm ? 'Masquer le formulaire' : 'Rejoindre le comité'}
                </button>
            </div>
        </section>

        {#if showForm}
            <!-- Section Formulaire -->
            <section class="mb-16 rounded-lg bg-gray-800 p-6 shadow-lg">
                <h2 class="mb-6 text-center text-2xl font-semibold text-white sm:text-3xl">
                    ✍️ Formulaire d'inscription
                </h2>

                <form on:submit|preventDefault={handleSubmit} class="space-y-4">
                    <div>
                        <label for="prenom" class="block text-gray-300 mb-1">Prénom</label>
                        <input
                            type="text"
                            id="prenom"
                            bind:value={formData.prenom}
                            class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
                            required
                        />
                    </div>

                    <div>
                        <label for="nom" class="block text-gray-300 mb-1">Nom</label>
                        <input
                            type="text"
                            id="nom"
                            bind:value={formData.nom}
                            class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
                            required
                        />
                    </div>

                    <div>
                        <label for="statut" class="block text-gray-300 mb-1">Statut</label>
                        <input
                            type="text"
                            id="statut"
                            bind:value={formData.statut}
                            placeholder="Interne, Docteur, Professeur…"
                            class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
                            required
                        />
                    </div>

                    <div>
                        <label for="specialite" class="block text-gray-300 mb-1">Spécialité</label>
                        <input
                            type="text"
                            id="specialite"
                            bind:value={formData.specialite}
                            class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
                            required
                        />
                    </div>

                    <div>
                        <label for="surSpecialite" class="block text-gray-300 mb-1">Sur-spécialité (optionnelle)</label>
                        <input
                            type="text"
                            id="surSpecialite"
                            bind:value={formData.surSpecialite}
                            class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
                        />
                    </div>

                    <div>
                        <label for="centre" class="block text-gray-300 mb-1">Centre d'exercice</label>
                        <input
                            type="text"
                            id="centre"
                            bind:value={formData.centre}
                            placeholder="CHU, hôpital, clinique, cabinet…"
                            class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
                            required
                        />
                    </div>

                    <div class="bg-gray-700 p-4 rounded-lg mb-4">
                        <p class="text-gray-300 mb-2">📝 Exemple :</p>
                        <p class="text-gray-300 italic">
                            Dr Xavier Montjou, Chirurgie orthopédique, Spécialiste en chirurgie de la main, AP-HP
                        </p>
                    </div>

                    <button
                        type="submit"
                        class="w-full bg-teal-500 hover:bg-teal-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                    >
                        Envoyer ma candidature
                    </button>
                </form>
            </section>
        {/if}

        <!-- Modal for email content -->
        {#if showModal}
            <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div class="bg-gray-800 p-6 rounded-lg max-w-2xl w-full mx-4">
                    <h3 class="text-xl font-bold text-white mb-4">Email non envoyé</h3>
                    <p class="text-gray-300 mb-4">Veuillez copier le contenu ci-dessous et l'envoyer manuellement :</p>
                    <div class="bg-gray-700 p-4 rounded-lg mb-4">
                        <pre class="text-gray-300 whitespace-pre-wrap">{modalContent}</pre>
                    </div>
                    <div class="flex justify-end">
                        <button 
                            on:click={closeModal}
                            class="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                        >
                            Fermer
                        </button>
                    </div>
                </div>
            </div>
        {/if}

        <!-- Liste des Référents -->
        <section>
            {#each referents as referent (referent.name)}
                <!-- Afficher le titre de la spécialité seulement si elle change -->
                {#if referent.specialty !== currentSpecialty}
                    {@const _ = currentSpecialty = referent.specialty}
                    <h2 class="mt-10 mb-6 border-b border-gray-700 pb-2 text-2xl font-semibold text-teal-400 sm:text-3xl">
                        {getSpecialtyEmoji(referent.specialty)} {referent.specialty}
                    </h2>
                {/if}

                <div class="mb-6 rounded-lg bg-gray-800 p-5 shadow-md transition-shadow hover:shadow-lg">
                    <h3 class="text-xl font-bold text-white">{referent.name}</h3>
                    <p class="text-md text-gray-300">{referent.title}</p>
                    {#if referent.affiliation}
                        <p class="text-sm text-gray-400">{referent.affiliation}</p>
                    {/if}
                    {#if referent.focus}
                        <p class="mt-1 text-sm text-gray-400 italic">{referent.focus}</p>
                    {/if}
                </div>
            {/each}
        </section>

	</div>
</div>

<style>
    /* Add any page-specific styles here if needed */
    h1, h2, h3 {
        font-family: 'Montserrat', sans-serif; /* Example: Use Montserrat */
    }
</style>