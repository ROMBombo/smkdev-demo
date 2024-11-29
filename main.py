import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
import json
from fastapi import FastAPI, HTTPException, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from similarity_checker import compute_similarity
from cv_prompt import cv_prompt
from ijazah_prompt import ijazah_prompt
from transkrip_prompt import transkrip_prompt
from job_requirements import job_requirements

load_dotenv()

app = FastAPI(
    title='Webservice Demo SMKDEV',
    version="1.0.0"
)

app.config = {
    "max_upload_size": "50MB"
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
)

def upload_to_gemini(path, mime_type=None):
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def wait_for_files_active(files):
  print("Waiting for file processing...")
  for name in (file.name for file in files):
    file = genai.get_file(name)
    while file.state.name == "PROCESSING":
      print(".", end="", flush=True)
      time.sleep(10)
      file = genai.get_file(name)
    if file.state.name != "ACTIVE":
      raise Exception(f"File {file.name} failed to process")
  print("...all files ready")
  print()

def save_file(file, filename):
  with open(filename, "wb") as f:
    f.write(file)

def extract_document_by_prompt(file_path, prompt):
  files = [
    upload_to_gemini(file_path, mime_type="application/pdf"),
  ]

  wait_for_files_active(files)

  chat_session = model.start_chat(
    history=[
      {
        "role": "user",
        "parts": [
          files[0],
        ],
      },
    ]
  )

  response = chat_session.send_message(prompt)

  return json.loads(response.text)

@app.post("/document-check")
async def document_check(file_cv: UploadFile, file_ijazah: UploadFile, file_transkrip: UploadFile):
  # Ekstraksi file CV
  contents = await file_cv.read()
  try:
      save_file(contents, file_cv.filename)
  except Exception as e:
      raise HTTPException(status_code=500, detail={"code": 500, "message": f"Error saving file: {e}"})
  
  try:
    print("Extracting data from CV...")
    data_cv = extract_document_by_prompt(file_cv.filename, cv_prompt)
  except Exception as e:
    raise HTTPException(status_code=500, detail={"code": 500, "message": f"Error extracting data from CV: {e}"})
  
  os.remove(file_cv.filename)
  print("CV Extracted")
  # Ekstranksi file CV selesai

  # Ekstraksi file Ijazah
  contents = await file_ijazah.read()
  try:
      save_file(contents, file_ijazah.filename)
  except Exception as e:
      raise HTTPException(status_code=500, detail={"code": 500, "message": f"Error saving file: {e}"})
  
  try:
    print("Extracting data from Ijazah...")
    data_ijazah = extract_document_by_prompt(file_ijazah.filename, ijazah_prompt)
  except Exception as e:
    raise HTTPException(status_code=500, detail={"code": 500, "message": f"Error extracting data from Ijazah: {e}"})
  
  os.remove(file_ijazah.filename)
  print("Ijazah Extracted")
  # Ekstraksi file Ijazah selesai

  # Ekstraksi file Transkrip
  contents = await file_transkrip.read()
  try:
      save_file(contents, file_transkrip.filename)
  except Exception as e:
      raise HTTPException(status_code=500, detail={"code": 500, "message": f"Error saving file: {e}"})
  
  try:
    print("Extracting data from Transkrip...")
    data_transkrip = extract_document_by_prompt(file_transkrip.filename, transkrip_prompt)
  except Exception as e:
    raise HTTPException(status_code=500, detail={"code": 500, "message": f"Error extracting data from Transkrip: {e}"})
  
  os.remove(file_transkrip.filename)
  print("Transkrip Extracted")
  # Ekstraksi file Transkrip selesai

  # Validasi data
  validation_result = {
    "name": {
      "status": True,
      "message": "Data valid"
    },
    "nim": {
      "status": True,
      "message": "Data valid"
    },
    "nama_perguruan_tinggi": {
      "status": True,
      "message": "Data valid"
    }
  }
  
  nama_cv = f"{data_cv['user']['first_name']} {data_cv['user']['last_name']}"
  status = True
  message_not_valid = "Data is not valid."
  
  kemiripan_cv_ijazah = compute_similarity(nama_cv.lower(), data_ijazah['nama'].lower())
  kemiripan_cv_transkrip = compute_similarity(nama_cv.lower(), data_transkrip['nama'].lower())
  kemiripian_ijazah_transkrip = compute_similarity(data_ijazah['nama'].lower(), data_transkrip['nama'].lower())

  if kemiripan_cv_ijazah < 1:
    status = False 
    message_not_valid += f"Nama CV dan Ijazah tidak cocok dengan tingkat kemiripan 1."
  if kemiripan_cv_transkrip < 1:
    status = False
    message_not_valid += f"Nama CV dan Transkrip tidak cocok dengan tingkat kemiripan 1."
  if kemiripian_ijazah_transkrip < 1:
    status = False
    message_not_valid += f"Ijazah dan Transkrip tidak cocok dengan tingkat kemiripan 1."

  if not status:
    validation_result["name"]["status"] = status
    validation_result["name"]["message"] = message_not_valid

  if data_ijazah['nim'] != data_transkrip['nim']:
    validation_result["nim"]["status"] = False
    validation_result["nim"]["message"] = "NIM tidak cocok"
  
  if compute_similarity(data_ijazah['nama_perguruan_tinggi'].lower(), data_transkrip['nama_perguruan_tinggi'].lower()) < 1:
    validation_result["nama_perguruan_tinggi"]["status"] = False
    validation_result["nama_perguruan_tinggi"]["message"] = "Nama perguruan tinggi tidak cocok"
  # Validasi data selesai

  # Penilaian kecocokan data CV dengan job requirement dengan gemini
  prompt = f"""
<CV candidate>
{json.dumps(data_cv)}
</CV candidate>

<Ijazah candidate>
{json.dumps(data_ijazah)}
</Ijazah candidate>

<Transkrip candidate>
{json.dumps(data_transkrip)}
</Transkrip candidate>

<Job Requirement>
{job_requirements}
</Job Requirement>

You are HR specialist. Based on the above data, you should evaluate the candidate's fit for the job. Please response in JSON format with the following structure:
{{
  "fit": true or false,
  "score": 1-10,
  "reason": "Reason for fit or not fit"
}}
"""
  
  try:
    print("Candidate suitability assessment with Gemini...")
    response = model.generate_content(prompt)
    matching_result = json.loads(response.text)
  except Exception as e:
    raise HTTPException(status_code=500, detail={"code": 500, "message": f"Error generating response from Gemini: {e}"})
  
  return {
    "code": 200,
    "message": "Document successfully checked",
    "data": {
       "cv": data_cv,
       "ijazah": data_ijazah,
       "transkrip": data_transkrip,
       "validation": validation_result,
       "matching": matching_result
    }
  }