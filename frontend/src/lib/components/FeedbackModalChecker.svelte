<!-- src/lib/components/FeedbackModalChecker.svelte -->
<script lang="ts">
	import userProfileStore from '$lib/stores/user';
	import FeedbackModal from '../../components/FeedbackModal.svelte';

	let isFeedbackModalOpen = $state(false);
    let hasCheckedInitialNull = $state(false); // Prevent multiple init calls

	/**
	 * Checks if the feedback_modal timestamp is older than one month.
	 * Returns FALSE if the timestamp is NULL or not older than a month.
     * Returns TRUE only if the timestamp EXISTS and is older than one month.
	 */
	function isTimestampOlderThanOneMonth(feedbackModalTimestamp: string | null): boolean {
        if (!feedbackModalTimestamp) {
            // If timestamp is null, it's not older than a month, so don't show yet.
            // The initialization call will happen separately.
            return false;
        }

		try {
			const lastShown = new Date(feedbackModalTimestamp);
			if (isNaN(lastShown.getTime())) {
				console.warn("Feedback Check: Invalid feedback_modal timestamp:", feedbackModalTimestamp, "Treating as needing check/reset, but not showing yet.");
				// If invalid, we might want the backend to reset it, but don't open modal now.
                return false;
			}

            const now = new Date();
			const oneMonthAgo = new Date(now);
			oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

            const show = lastShown < oneMonthAgo;
            // console.log(`Feedback Check (isTimestampOlderThanOneMonth): LastShown=${lastShown.toISOString()}, OneMonthAgo=${oneMonthAgo.toISOString()}, ShouldShow=${show}`);
			return show;

		} catch (err) {
			console.error('Feedback Check: Error parsing feedback_modal timestamp:', err);
			return false; // Don't show modal on error
		}
	}

    // Function to silently call the API to initialize/update the timestamp
    async function triggerTimestampUpdateAPI() {
        // console.log("Feedback Checker: Triggering background API call to /api/update-feedback-modal");
        try {
            // This API call (from the previous correct version) handles the logic:
            // - If timestamp was NULL, it sets it to 23 days ago.
            // - If timestamp existed, it sets it to now().
            const response = await fetch('/api/update-feedback-modal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
             if (!response.ok) {
                 const errorData = await response.json().catch(() => ({ message: 'Failed to parse error response' }));
                //  console.error('Feedback Checker: Background API update failed:', response.status, errorData.message || response.statusText);
            } else {
                //  console.log("Feedback Checker: Background API timestamp update successful.");
            }
        } catch(err) {
            // console.error('Feedback Checker: Network error during background API update:', err);
        }
    }

    // Function called when the modal signals it's closing or submitted
	function handleModalClose() {
		isFeedbackModalOpen = false;
        // The API call to update timestamp to NOW() happens inside the FeedbackModal component's $effect
        // OR alternatively, trigger the update *here* explicitly after closing.
        // Let's assume the FeedbackModal's own effect handles the update-to-now() call.
	}

    // Effect to check when the user profile changes
	$effect(() => {
		const profile = $userProfileStore;

		if (profile) {
            const timestamp = profile.feedback_modal;
            // console.log("Feedback Checker $effect: Profile loaded, checking timestamp:", timestamp);

            if (timestamp === null && !hasCheckedInitialNull) {
                // --- Scenario 1: Timestamp is NULL (First time) ---
                // console.log("Feedback Checker: Timestamp is NULL. Triggering background initialization.");
                hasCheckedInitialNull = true; // Prevent re-triggering initialization immediately
                triggerTimestampUpdateAPI(); // Call API to set date to -23 days
                // **DO NOT** open the modal here
                isFeedbackModalOpen = false;

            } else if (timestamp !== null) {
                // --- Scenario 2: Timestamp EXISTS ---
                 hasCheckedInitialNull = true; // Mark as checked once a timestamp exists
                 // Check if it's time to show the modal (> 1 month old)
                if (isTimestampOlderThanOneMonth(timestamp)) {
                    // console.log("Feedback Checker: Timestamp is older than 1 month. Scheduling modal open.");
                    // Use setTimeout to avoid immediate opening on load/profile update
                    const timer = setTimeout(() => {
                        if ($userProfileStore) { // Re-check user is still logged in
                             // console.log("Feedback Checker: Timer fired, opening modal.");
                             isFeedbackModalOpen = true;
                        } else {
                              // console.log("Feedback Checker: User logged out before modal timer fired.");
                        }
                    }, 1500); // Shorter delay might be okay now

                    return () => {
                        clearTimeout(timer);
                    };
                } else {
                    // console.log("Feedback Checker: Timestamp exists but is not older than 1 month.");
                    isFeedbackModalOpen = false; // Ensure modal is closed if condition isn't met
                }
            } else {
                 // Timestamp is null, but we already checked/triggered init this session
                 // console.log("Feedback Checker: Timestamp is NULL, but initial check already done this session.");
                 isFeedbackModalOpen = false;
            }
		} else {
            // console.log("Feedback Checker $effect: Profile not yet loaded or user logged out.");
            hasCheckedInitialNull = false; // Reset check flag if user logs out
             isFeedbackModalOpen = false; // Ensure modal is closed
        }
	});

</script>

<!-- Pass the close handler -->
<FeedbackModal bind:isOpen={isFeedbackModalOpen} on:close={handleModalClose} />