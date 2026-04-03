from fastapi import FastAPI, UploadFile, File
import requests

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()

        response = requests.post(
            "http://127.0.0.1:5001/api/v0/add",
            files={"file": content}
        )

        result = response.json()
        cid = result["Hash"]

        return {
            "filename": file.filename,
            "cid": cid,
            "ipfs_url": f"https://ipfs.io/ipfs/{cid}"
        }

    except Exception as e:
        return {"error": str(e)}