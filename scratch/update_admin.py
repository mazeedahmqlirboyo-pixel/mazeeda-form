import re

with open('src/routes/admin/+page.svelte', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add reset and delete functions to script
script_funcs = """  async function resetSiswiForm(siswiId) {
    if (!confirm('Yakin ingin mereset formulir siswi ini? Semua data yang diisi (foto, WA, hobi, dll) akan dihapus, tetapi nama dan NIS tetap ada di database.')) return;
    
    const { error } = await supabase
      .from('siswi')
      .update({
        whatsapp_number: null,
        whatsapp_provider: null,
        blood_type: null,
        residence: null,
        travel_route: null,
        email: null,
        instagram: null,
        tiktok: null,
        twitter: null,
        hobbies: null,
        aspirations: null,
        favorite_food: null,
        favorite_drink: null,
        favorite_music: null,
        favorite_color: null,
        quote: null,
        impression: null,
        message: null,
        paper_form_url: null,
        paper_form_url_2: null,
        is_completed: false,
        updated_at: null
      })
      .eq('id', siswiId);
      
    if (error) {
      alert('Gagal mereset data: ' + error.message);
    } else {
      alert('Formulir berhasil direset!');
      selectedSiswiDetail = null;
      await fetchSiswiList();
    }
  }

  async function deleteSiswiData(siswiId) {
    if (!confirm('PERINGATAN BAHAYA: Yakin ingin menghapus siswi ini secara PERMANEN dari database? Data nama dan NIS akan hilang selamanya.')) return;
    
    const { error } = await supabase
      .from('siswi')
      .delete()
      .eq('id', siswiId);
      
    if (error) {
      alert('Gagal menghapus data: ' + error.message);
    } else {
      alert('Data siswi berhasil dihapus permanen!');
      selectedSiswiDetail = null;
      await fetchSiswiList();
    }
  }

  // Helper untuk menentukan status Kelengkapan"""

content = content.replace("  // Helper untuk menentukan status Kelengkapan", script_funcs)

# 2. Update Modal to show second photo and add Reset/Delete buttons
# Find the end of Modal Body
old_modal_end = """          </div>
        </div>
      </div>
    </div>
  </div>
{/if}"""

new_modal_end = """          </div>
        </div>
        
        <!-- Action Buttons (Reset / Hapus) -->
        <div class="border-t border-slate-100 p-4 bg-slate-50 flex justify-end gap-3">
          <button type="button" onclick={() => resetSiswiForm(selectedSiswiDetail.id)} class="px-4 py-2 bg-orange-100 text-orange-700 hover:bg-orange-200 font-bold text-xs rounded-xl transition-colors border border-orange-200">
            Reset Formulir
          </button>
          <button type="button" onclick={() => deleteSiswiData(selectedSiswiDetail.id)} class="px-4 py-2 bg-red-100 text-red-700 hover:bg-red-200 font-bold text-xs rounded-xl transition-colors border border-red-200">
            Hapus Siswi Permanen
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}"""

content = content.replace(old_modal_end, new_modal_end)

# 3. Update Kiri: Foto / Status to show 2 photos if available
old_kiri_foto = """          <!-- Kiri: Foto / Status -->
          <div class="flex flex-col items-center sm:items-start sm:w-1/3">
            <div class="w-full aspect-[3/4] bg-slate-100 rounded-2xl border-4 border-white shadow-md flex items-center justify-center overflow-hidden mb-4 cursor-pointer hover:opacity-90 transition-opacity" title="Klik untuk perbesar" onclick={() => { if(selectedSiswiDetail.paper_form_url) previewImageUrl = selectedSiswiDetail.paper_form_url; }}>
              {#if selectedSiswiDetail.paper_form_url}
                <img src={selectedSiswiDetail.paper_form_url} class="w-full h-full object-cover" alt="Foto Arsip Kertas" />
              {:else}
                <div class="flex flex-col items-center text-slate-300">
                  <FileImage class="w-12 h-12 mb-2" />
                  <span class="text-xs font-semibold">Tidak ada arsip</span>
                </div>
              {/if}
            </div>"""

new_kiri_foto = """          <!-- Kiri: Foto / Status -->
          <div class="flex flex-col items-center sm:items-start sm:w-1/3 gap-4">
            <div class="w-full aspect-[3/4] bg-slate-100 rounded-2xl border-4 border-white shadow-md flex items-center justify-center overflow-hidden cursor-pointer hover:opacity-90 transition-opacity" title="Klik untuk perbesar Halaman 1" onclick={() => { if(selectedSiswiDetail.paper_form_url) previewImageUrl = selectedSiswiDetail.paper_form_url; }}>
              {#if selectedSiswiDetail.paper_form_url}
                <img src={selectedSiswiDetail.paper_form_url} class="w-full h-full object-cover" alt="Foto Arsip Halaman 1" />
              {:else}
                <div class="flex flex-col items-center text-slate-300">
                  <FileImage class="w-12 h-12 mb-2" />
                  <span class="text-xs font-semibold text-center px-2">Halaman 1 Kosong</span>
                </div>
              {/if}
            </div>
            
            {#if selectedSiswiDetail.paper_form_url_2}
            <div class="w-full aspect-[3/4] bg-slate-100 rounded-2xl border-4 border-white shadow-md flex items-center justify-center overflow-hidden cursor-pointer hover:opacity-90 transition-opacity" title="Klik untuk perbesar Halaman 2" onclick={() => { previewImageUrl = selectedSiswiDetail.paper_form_url_2; }}>
              <img src={selectedSiswiDetail.paper_form_url_2} class="w-full h-full object-cover" alt="Foto Arsip Halaman 2" />
            </div>
            {/if}
            
            <div class="w-full mt-2">"""

# Replace and fix up the closing tags properly since I injected a <div class="w-full mt-2">
content = content.replace(old_kiri_foto, new_kiri_foto)
# Find the end of the Kiri part (which used to be right after the avatar div)
# Wait, let's look at the original code after the avatar div.
old_status_pills = """            </div>
            
            <!-- Badge Status -->
            <div class="w-full space-y-2 mb-6 sm:mb-0">
              {#if getStatusType(selectedSiswiDetail) === 'Lengkap'}"""

new_status_pills = """            </div>
            
            <!-- Badge Status -->
            <div class="w-full space-y-2 mb-6 sm:mb-0">
              {#if getStatusType(selectedSiswiDetail) === 'Lengkap'}"""

content = content.replace("            </div>\n            \n            <!-- Badge Status -->", "            <!-- Badge Status -->")

with open('src/routes/admin/+page.svelte', 'w', encoding='utf-8') as f:
    f.write(content)
