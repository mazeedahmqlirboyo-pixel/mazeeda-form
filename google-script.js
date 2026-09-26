function doPost(e) {
  try {
    var sheetName = "Data Siswi"; // Sesuaikan dengan nama sheet
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
    
    // Jika sheet belum ada, buat baru dan atur header
    if (!sheet) {
      sheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet(sheetName);
      var headers = [
        "Waktu Pengisian", "ID Supabase", "NIS", "Nama Lengkap", "Golongan Darah", 
        "Tempat Tinggal", "Rute Perjalanan", "No. WhatsApp", "Provider WA", 
        "Email", "Instagram", "TikTok", "Twitter/X", "Hobi", "Keahlian Khusus", 
        "Cita-cita", "Makanan Favorit", "Musik Favorit", "Quotes", 
        "Kesan", "Pesan", "URL Avatar"
      ];
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    }
    
    var data = JSON.parse(e.postData.contents);
    
    var rowData = [
      new Date(), // Waktu Pengisian
      data.id || "",
      data.nis || "",
      data.full_name || "",
      data.blood_type || "",
      data.residence || "",
      data.travel_route || "",
      data.whatsapp_number || "",
      data.whatsapp_provider || "",
      data.email || "",
      data.instagram || "",
      data.tiktok || "",
      data.twitter_x || "",
      data.hobbies || "",
      data.special_skills || "",
      data.aspirations || "",
      data.favorite_food || "",
      data.favorite_music || "",
      data.quote || "",
      data.impression || "",
      data.message || "",
      data.avatar_url || ""
    ];
    
    sheet.appendRow(rowData);
    
    return ContentService.createTextOutput(JSON.stringify({"status": "success", "message": "Data berhasil disimpan"}))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({"status": "error", "message": error.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
