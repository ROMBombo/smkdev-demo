# Webservice Demo SMKDEV

Webservice ini dirancang untuk memvalidasi dan mengevaluasi dokumen seperti CV, Ijazah, dan Transkrip menggunakan Google Gemini API dan teknologi FastAPI. Selain itu, webservice ini dapat memeriksa kecocokan kandidat dengan persyaratan pekerjaan yang diberikan.

---

## Fitur

1. **Ekstraksi Data Dokumen**: Menggunakan model Google Gemini untuk mengekstrak data dari dokumen PDF.
2. **Validasi Data Dokumen**:
   - Memeriksa kesesuaian nama antara CV, Ijazah, dan Transkrip.
   - Validasi kesesuaian NIM.
   - Validasi kesesuaian nama perguruan tinggi.
3. **Evaluasi Kecocokan Kandidat dengan Job Requirement**:
   - Menggunakan prompt untuk menilai kecocokan kandidat berdasarkan data dokumen dan persyaratan pekerjaan.
4. **Respons Terstruktur dalam Format JSON**.

---

## Persyaratan

- **Python**: Versi 3.11.4 atau lebih baru
- **Pustaka Python**:
  - `fastapi`
  - `google-generativeai`
  - `python-dotenv`
  - `uvicorn`
- **Lingkungan**:
  - File `.env` untuk menyimpan API key dari Google Gemini.

---

## Instalasi

1. **Clone Repository**:

   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Instalasi Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Buat File .env:**
    Tambahkan API key Google Gemini:

    ```env
    GOOGLE_API_KEY=your-google-api-key
    ```

4. **Jalankan Server:**

    ```bash
    uvicorn main:app --reload
    ```