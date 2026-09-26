import { createClient } from '@supabase/supabase-js';

// Hardcoded untuk *bypass* Vercel Environment Variables 2FA!
const PUBLIC_SUPABASE_URL = "https://ijqgvmtiboqmmtvljoud.supabase.co";
const PUBLIC_SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlqcWd2bXRpYm9xbW10dmxqb3VkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg0MTkxNjcsImV4cCI6MjEwMzk5NTE2N30.Ca5LPwnUSwSqNXQX5DFj7Pd0W8yJsQ-hUHM8agVZuAY";

if (!PUBLIC_SUPABASE_URL || !PUBLIC_SUPABASE_ANON_KEY) {
    throw new Error('Supabase URL atau Anon Key kosong.');
}

export const supabase = createClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY);
