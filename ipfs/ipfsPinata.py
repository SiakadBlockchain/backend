from fastapi import FastAPI, UploadFile, File
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_SECRET_API_KEY = os.getenv("PINATA_SECRET_API_KEY")

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"

        file_content = await file.read()

        files = {
            "file": (file.filename, file_content)
        }

        headers = {
            "pinata_api_key": PINATA_API_KEY,
            "pinata_secret_api_key": PINATA_SECRET_API_KEY
        }

        response = requests.post(url, files=files, headers=headers)

        result = response.json()

        cid = result["IpfsHash"]

        return {
            "filename": file.filename,
            "cid": cid,
            "ipfs_url": f"https://gateway.pinata.cloud/ipfs/{cid}"
            # ipfs_url = f"https://coral-solid-mole-207.mypinata.cloud/ipfs/{cid}"
        }

    except Exception as e:
        return {"error": str(e)}