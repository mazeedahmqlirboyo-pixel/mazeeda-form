-- Schema untuk Aplikasi Form SISWI MAZEEDA

-- Hapus tabel jika sudah ada (opsional, untuk clean init)
-- DROP TABLE IF EXISTS public.siswi;

CREATE TABLE public.siswi (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nis VARCHAR(20) UNIQUE,
  full_name TEXT NOT NULL,
  blood_type VARCHAR(5),
  residence TEXT,
  travel_route TEXT,
  whatsapp_number VARCHAR(20),
  whatsapp_provider VARCHAR(30),
  email TEXT,
  instagram VARCHAR(50),
  tiktok VARCHAR(50),
  twitter_x VARCHAR(50),
  hobbies TEXT,
  special_skills TEXT,
  aspirations TEXT,
  favorite_food TEXT,
  favorite_drink TEXT,
  favorite_color TEXT,
  favorite_music TEXT,
  quote TEXT,
  impression TEXT,
  message TEXT,
  avatar_url TEXT,
  is_completed BOOLEAN DEFAULT FALSE,
  paper_form_url TEXT,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trigger untuk update `updated_at` secara otomatis
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_siswi_updated
  BEFORE UPDATE ON public.siswi
  FOR EACH ROW
  EXECUTE PROCEDURE public.handle_updated_at();


-- --- ROW LEVEL SECURITY (RLS) ---
ALTER TABLE public.siswi ENABLE ROW LEVEL SECURITY;

-- 1. Mengizinkan siapa saja (anon) untuk membaca (SELECT) data
CREATE POLICY "Enable read access for all users" 
ON public.siswi FOR SELECT 
USING (true);

-- 2. Mengizinkan siapa saja (anon) untuk menyisipkan (INSERT) data (untuk fitur upload csv di admin)
CREATE POLICY "Enable insert access for all users" 
ON public.siswi FOR INSERT 
WITH CHECK (true);

-- 3. Mengizinkan siapa saja (anon) untuk memperbarui (UPDATE) data
CREATE POLICY "Enable update access for all users" 
ON public.siswi FOR UPDATE 
USING (true);


-- --- STORAGE BUCKET ---
-- Buat bucket untuk `avatars` (jika menggunakan SQL editor bisa dibuat manual juga via dashboard)
INSERT INTO storage.buckets (id, name, public) VALUES ('avatars', 'avatars', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- Kebijakan Storage: Mengizinkan siapa saja untuk mengunggah file ke bucket `avatars`
CREATE POLICY "Avatar Upload Policy" 
ON storage.objects FOR INSERT 
WITH CHECK ( bucket_id = 'avatars' );

-- Kebijakan Storage: Mengizinkan siapa saja untuk membaca file di bucket `avatars`
CREATE POLICY "Avatar Read Policy" 
ON storage.objects FOR SELECT 
USING ( bucket_id = 'avatars' );
