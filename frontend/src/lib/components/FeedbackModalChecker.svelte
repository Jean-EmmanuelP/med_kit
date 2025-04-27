<script lang="ts">
    import userProfileStore from '$lib/stores/user';
    import { onMount } from 'svelte';
    import FeedbackModal from '../../components/FeedbackModal.svelte';

    let isFeedbackModalOpen = $state(false);

    function shouldShowFeedbackModal(feedbackModalTimestamp: string | null): boolean {
        // If timestamp is null or empty string, show the modal
        if (!feedbackModalTimestamp) return true;
        
        try {
            const lastShown = new Date(feedbackModalTimestamp);
            // If the date is invalid, show the modal
            if (isNaN(lastShown.getTime())) return true;
            
            const now = new Date();
            const oneMonthAgo = new Date();
            oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
            
            return lastShown < oneMonthAgo;
        } catch (err) {
            console.error('Error parsing feedback modal timestamp:', err);
            return true; // Show modal if there's any error parsing the date
        }
    }

    onMount(() => {
        const unsubscribe = userProfileStore.subscribe(profile => {
            if (profile && shouldShowFeedbackModal(profile.feedback_modal)) {
                // Add a small delay to ensure the page is fully loaded
                setTimeout(() => {
                    isFeedbackModalOpen = true;
                }, 1000); // Show after 5 seconds
            }
        });

        return () => unsubscribe();
    });
</script>

<FeedbackModal bind:isOpen={isFeedbackModalOpen} on:close={() => isFeedbackModalOpen = false} /> 