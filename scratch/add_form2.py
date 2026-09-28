import re

with open('src/routes/+page.svelte', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add to formData
content = content.replace("paper_form_url: ''", "paper_form_url: '',\n    paper_form_url_2: ''")

# 2. Add second upload UI. The current UI has section 5:
# <h3 class="text-xl font-extrabold text-indigo-900 mb-2">5. Arsip Formulir (Wajib)</h3>
# ...
# <div class="bg-indigo-50/50 rounded-2xl p-6 border border-indigo-100">
# Let's find it.
old_arsip_section = """        <!-- BAGIAN 5: UPLOAD KERTAS -->
        <div>
          <h3 class="text-xl font-extrabold text-indigo-900 mb-2">5. Arsip Formulir (Wajib)</h3>
          <p class="text-sm text-indigo-600/80 mb-6 font-medium">Foto atau scan formulir fisik yang sudah disahkan.</p>
          
          <div class="bg-indigo-50/50 rounded-2xl p-6 border border-indigo-100">
            {#if !formData.paper_form_url}
              <div class="flex flex-col items-center justify-center py-6">
                <div class="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center mb-4 shadow-inner">
                  <Camera class="w-10 h-10 text-indigo-500" />
                </div>
                <p class="text-sm text-indigo-900 font-semibold mb-6">Belum ada foto formulir</p>
                
                <div class="flex gap-4 w-full justify-center">
                  <button type="button" onclick={() => { currentUploadType = 'paper_form'; showCamera = true; startCamera(); }} class="flex flex-col items-center justify-center bg-white border border-indigo-200 hover:border-indigo-400 rounded-2xl p-4 w-32 shadow-sm transition-all hover:shadow-md">
                    <Camera class="w-8 h-8 text-indigo-600 mb-2" />
                    <span class="text-xs font-bold text-indigo-900">Buka Kamera</span>
                  </button>
                  
                  <button type="button" onclick={() => { currentUploadType = 'paper_form'; document.getElementById('file-paper')?.click(); }} class="flex flex-col items-center justify-center bg-white border border-indigo-200 hover:border-indigo-400 rounded-2xl p-4 w-32 shadow-sm transition-all hover:shadow-md">
                    <FolderOpen class="w-8 h-8 text-indigo-600 mb-2" />
                    <span class="text-xs font-bold text-indigo-900">Galeri HP</span>
                  </button>
                </div>
                
                <input type="file" id="file-paper" accept="image/*" class="hidden" onchange={handleFileUpload} />
              </div>
            {:else}
              <div class="relative rounded-xl overflow-hidden shadow-lg border border-indigo-100 max-w-sm mx-auto group">
                <img src={formData.paper_form_url} alt="Arsip" class="w-full h-auto object-cover" />
                <div class="absolute inset-0 bg-indigo-900/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <button type="button" onclick={() => formData.paper_form_url = ''} class="bg-white/20 hover:bg-white/40 backdrop-blur-md text-white font-bold py-2 px-6 rounded-full transition-all">
                    Ganti Foto
                  </button>
                </div>
              </div>
            {/if}
          </div>
        </div>"""

new_arsip_section = """        <!-- BAGIAN 5: UPLOAD KERTAS -->
        <div>
          <h3 class="text-xl font-extrabold text-indigo-900 mb-2">5. Arsip Formulir</h3>
          <p class="text-sm text-indigo-600/80 mb-6 font-medium">Foto atau scan formulir fisik yang sudah disahkan.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- FOTO 1 (WAJIB) -->
            <div class="bg-indigo-50/50 rounded-2xl p-4 sm:p-6 border border-indigo-100">
              <h4 class="text-sm font-bold text-indigo-800 mb-4 text-center">Halaman 1 (Wajib)</h4>
              {#if !formData.paper_form_url}
                <div class="flex flex-col items-center justify-center py-4">
                  <div class="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mb-4 shadow-inner">
                    <Camera class="w-8 h-8 text-indigo-500" />
                  </div>
                  
                  <div class="flex gap-3 w-full justify-center">
                    <button type="button" onclick={() => { currentUploadType = 'paper_form'; showCamera = true; startCamera(); }} class="flex flex-col items-center justify-center bg-white border border-indigo-200 hover:border-indigo-400 rounded-xl p-3 w-28 shadow-sm transition-all hover:shadow-md">
                      <Camera class="w-6 h-6 text-indigo-600 mb-2" />
                      <span class="text-[10px] font-bold text-indigo-900">Kamera</span>
                    </button>
                    
                    <button type="button" onclick={() => { currentUploadType = 'paper_form'; document.getElementById('file-paper')?.click(); }} class="flex flex-col items-center justify-center bg-white border border-indigo-200 hover:border-indigo-400 rounded-xl p-3 w-28 shadow-sm transition-all hover:shadow-md">
                      <FolderOpen class="w-6 h-6 text-indigo-600 mb-2" />
                      <span class="text-[10px] font-bold text-indigo-900">Galeri</span>
                    </button>
                  </div>
                  <input type="file" id="file-paper" accept="image/*" class="hidden" onchange={handleFileUpload} />
                </div>
              {:else}
                <div class="relative rounded-xl overflow-hidden shadow-lg border border-indigo-100 max-w-sm mx-auto group">
                  <img src={formData.paper_form_url} alt="Arsip 1" class="w-full aspect-[3/4] object-cover" />
                  <div class="absolute inset-0 bg-indigo-900/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <button type="button" onclick={() => formData.paper_form_url = ''} class="bg-white/20 hover:bg-white/40 backdrop-blur-md text-white text-xs font-bold py-2 px-4 rounded-full transition-all">
                      Ganti Foto
                    </button>
                  </div>
                </div>
              {/if}
            </div>
            
            <!-- FOTO 2 (OPSIONAL) -->
            <div class="bg-slate-50/50 rounded-2xl p-4 sm:p-6 border border-slate-200">
              <h4 class="text-sm font-bold text-slate-600 mb-4 text-center">Halaman 2 (Opsional)</h4>
              {#if !formData.paper_form_url_2}
                <div class="flex flex-col items-center justify-center py-4">
                  <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4 shadow-inner">
                    <Camera class="w-8 h-8 text-slate-400" />
                  </div>
                  
                  <div class="flex gap-3 w-full justify-center">
                    <button type="button" onclick={() => { currentUploadType = 'paper_form_2'; showCamera = true; startCamera(); }} class="flex flex-col items-center justify-center bg-white border border-slate-200 hover:border-slate-300 rounded-xl p-3 w-28 shadow-sm transition-all hover:shadow-md">
                      <Camera class="w-6 h-6 text-slate-500 mb-2" />
                      <span class="text-[10px] font-bold text-slate-700">Kamera</span>
                    </button>
                    
                    <button type="button" onclick={() => { currentUploadType = 'paper_form_2'; document.getElementById('file-paper-2')?.click(); }} class="flex flex-col items-center justify-center bg-white border border-slate-200 hover:border-slate-300 rounded-xl p-3 w-28 shadow-sm transition-all hover:shadow-md">
                      <FolderOpen class="w-6 h-6 text-slate-500 mb-2" />
                      <span class="text-[10px] font-bold text-slate-700">Galeri</span>
                    </button>
                  </div>
                  <input type="file" id="file-paper-2" accept="image/*" class="hidden" onchange={handleFileUpload} />
                </div>
              {:else}
                <div class="relative rounded-xl overflow-hidden shadow-lg border border-slate-200 max-w-sm mx-auto group">
                  <img src={formData.paper_form_url_2} alt="Arsip 2" class="w-full aspect-[3/4] object-cover" />
                  <div class="absolute inset-0 bg-slate-900/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <button type="button" onclick={() => formData.paper_form_url_2 = ''} class="bg-white/20 hover:bg-white/40 backdrop-blur-md text-white text-xs font-bold py-2 px-4 rounded-full transition-all">
                      Ganti Foto
                    </button>
                  </div>
                </div>
              {/if}
            </div>
          </div>
        </div>"""

content = content.replace(old_arsip_section, new_arsip_section)

# 3. Update the handleFileUpload logic to support 'paper_form_2'
old_upload = """      if (currentUploadType === 'paper_form') {
        formData.paper_form_url = publicUrl;
      }"""
new_upload = """      if (currentUploadType === 'paper_form') {
        formData.paper_form_url = publicUrl;
      } else if (currentUploadType === 'paper_form_2') {
        formData.paper_form_url_2 = publicUrl;
      }"""
content = content.replace(old_upload, new_upload)

with open('src/routes/+page.svelte', 'w', encoding='utf-8') as f:
    f.write(content)
