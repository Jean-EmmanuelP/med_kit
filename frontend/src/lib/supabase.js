import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://etxelhjnqbrgwuitltyk.supabase.co';
const supabaseKey =
	'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV0eGVsaGpucWJyZ3d1aXRsdHlrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDA2OTE5NzAsImV4cCI6MjA1NjI2Nzk3MH0.EvaK9bCSYaBVaVOIgakKTAVoM8UrDYg2HX7Z-iyWoD4';
export const supabase = createClient(supabaseUrl, supabaseKey, {
	auth: {
		persistSession: true,
		autoRefreshToken: true,
		detectSessionInUrl: true
	}
});
