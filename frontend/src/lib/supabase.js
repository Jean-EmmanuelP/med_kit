import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://etxelhjnqbrgwuitltyk.supabase.co';
const supabaseKey =
	'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV0eGVsaGpucWJyZ3d1aXRsdHlrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MDY5MTk3MCwiZXhwIjoyMDU2MjY3OTcwfQ.TO7tce7MfQLM3k-N7ju3_unGBFEk0OIWEU2TvB4-n_4';
export const supabase = createClient(supabaseUrl, supabaseKey, {
	auth: {
		persistSession: true,
		autoRefreshToken: true,
		detectSessionInUrl: true
	}
});
