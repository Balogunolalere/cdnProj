# Import necessary libraries
from fastapi import FastAPI, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import deta 
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

DRIVE_PROJECT_KEY = os.getenv("DRIVE_PROJECT_KEY")
DRIVE_PROJECT_NAME = os.getenv("DRIVE_PROJECT_NAME")

# Initialize FastAPI instance
app = FastAPI(
    title="CDN API 🪐",
    description="API for uploading, downloading, listing, and managing files from a CDN",
    version="1.0.0"
)

# Connect to Deta Drive
try:
    drive = deta.Deta(DRIVE_PROJECT_KEY).Drive(DRIVE_PROJECT_NAME)
except Exception as e:
    raise HTTPException(status_code=500, detail="Failed to connect to Deta Drive")

# Set maximum file size to 100 MB
MAX_FILE_SIZE = 100 * 1024 * 1024

# Set allowed file extensions.
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'ico', 'svg', 'bmp', 'webp', 'tiff', 'psd'}

# Security scheme
security = HTTPBearer()

# Dependency to check authentication (stubbed for now)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # Implement token verification logic here
    if token != "your-secure-token":  # Replace with real token validation
        raise HTTPException(status_code=403, detail="Invalid or missing token")
    return token

# Route to upload a file
@app.post("/cdn/v1/uploadfile/", dependencies=[Depends(get_current_user)])
async def upload_file(file: UploadFile):
    """
    Upload a file to the CDN.

    - **file**: The file to upload.

    Returns:
    - **filename**: The name of the uploaded file.
    - **type**: The type of the uploaded file.
    - **message**: A success message if the file was uploaded successfully.
    """
    try:
        content = await file.read()

        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        # Check file extension
        if not any(file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            raise HTTPException(status_code=400, detail="File type not allowed")

        # Check if filename already exists
        if drive.get(file.filename):
            raise HTTPException(status_code=409, detail="File already exists")

        # Save uploaded file to Deta Drive
        drive.put(file.filename, content)

        # Return success message to client
        return {"filename": file.filename, "type": file.filename.split('.')[-1], "message": "File uploaded successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Route to download a file
@app.get("/cdn/v1/files/{filename}", response_class=Response, dependencies=[Depends(get_current_user)])
async def get_file(filename: str):
    """
    Download a file from the CDN.

    - **filename**: The name of the file to download.

    Returns:
    - **response**: The file to download.
    """
    try:
        # Retrieve file data
        file_data = drive.get(filename)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")

        # Send file to client with appropriate media type
        media_type = f"image/{filename.split('.')[-1].lower()}"
        return Response(content=file_data.read(), media_type=media_type)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Route to get all file names
@app.get("/cdn/v1/files/", dependencies=[Depends(get_current_user)])
async def get_files_name():
    """
    Get a list of all files in the CDN.

    Returns:
    - **response**: A dictionary containing a list of all files in the CDN and pagination information.
    """
    try:
        all_files = []
        last = None

        while True:
            result = drive.list(last=last)
            all_files.extend(result.get("names", []))
            last = result.get("paging", {}).get("last")
            if not last:
                break

        size = len(all_files)
        return {"response": {"names": all_files, "paging": {"size": size, "last": last}}}

    except HTTPException as e:
        raise e
    except ConnectionError:
        raise HTTPException(status_code=500, detail="Error connecting to storage")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Route to delete a file
@app.delete("/cdn/v1/files/{filename}", dependencies=[Depends(get_current_user)])
async def delete_file(filename: str):
    """
    Delete a file from the CDN.

    - **filename**: The name of the file to delete.

    Returns:
    - **message**: A success message if the file was deleted successfully.
    """
    try:
        # Check if file exists
        if not drive.get(filename):
            raise HTTPException(status_code=404, detail="File not found")

        # Delete file from Deta Drive
        drive.delete(filename)

        # Return success message to client
        return {"message": "File deleted successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Route to get API home page
@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Home page for the API.
    """
    html_content = """
    <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                }
                h1 {
                    color: #2F80ED;
                }
                p {
                    font-size: 20px;
                }
            </style>
        </head>
        <body>
            <h1>Welcome! 👋</h1>
            <p>This is the home page for my awesome API!</p>
            <p>Check out the docs below to get started ⬇️</p>
            <a href="/docs">Documentation</a>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
