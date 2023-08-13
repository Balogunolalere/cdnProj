# Import FastAPI and Deta Drive libraries
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
import  deta 
import os
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

DRIVE_PROJECT_KEY = os.getenv("DRIVE_PROJECT_KEY")
DRIVE_PROJECT_NAME = os.getenv("DRIVE_PROJECT_NAME")

# Initialize FastAPI instance
app = FastAPI(
    title="CDN API 🪐",
    description="API for uploading, downloading and listing files from a CDN",
    version="1.0.0"
)  

# Connect to Deta Drive
drive = deta.Deta(DRIVE_PROJECT_KEY).Drive(DRIVE_PROJECT_NAME)

# Set maximum file size to 100 MB
MAX_FILE_SIZE = 100 * 1024 * 1024

# Set allowed file extensions. 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'ico', 'svg', 'bmp', 'webp', 'tiff', 'psd'}

# Route to upload file 
@app.post("/cdn/v1/uploadfile/")
async def upload_file(file: UploadFile):
    """
    Upload a file to the CDN.

    - **file**: The file to upload.

    Returns:
    - **message**: A success message if the file was uploaded successfully.
    - **error**: An error message if the file could not be uploaded.
    """
    try:
        content = await file.read()

        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Check file extension
        if not file.filename.endswith(tuple(ALLOWED_EXTENSIONS)):
            raise HTTPException(status_code=400, detail="File type not allowed")

        # Check if filename already exists
        if drive.get(file.filename):
            return {"error": "File already exists"}
        
        # Save uploaded file to Deta Drive 
        name = file.filename
        drive.put(name, content)

        # get file type
        file_type = file.filename.split('.')[-1]

        # Return success message to client
        return {"filename": name, "type": file_type, "message": "File uploaded successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to download file
@app.get("/cdn/v1/files/{filename}") 
async def get_file(filename: str):
    """
    Download a file from the CDN.

    - **filename**: The name of the file to download.

    Returns:
    - **response**: The file to download.
    - **error**: An error message if the file could not be downloaded.
    """
    try:
        # Check if file exists
        if not drive.get(filename):
            raise HTTPException(status_code=404, detail="File not found")

        # Retrieve file data without sending to client yet
        file_data = drive.get(filename).read()

        # Send file to client with appropriate media type eg, image/png or image/jpeg etc
        media_type = f"image/{filename.split('.')[-1]}"
        return Response(content=file_data, media_type=media_type)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# Route to get all files
@app.get("/cdn/v1/files/")
async def get_files_name():
    """
    Get a list of all files in the CDN.

    Returns:
    - **response**: A dictionary containing a list of all files in the CDN and pagination information.
    - **error**: An error message if the file list could not be retrieved.
    """
    try:
        all_files = []
        last = None

        while True:
            result = drive.list(last=last)
            all_files += result.get("names")
            last = result.get("paging", {}).get("last")
            if not last:
                break

        size = len(all_files)
        response = {"names": all_files, "paging": {"size": size, "last": last}}
        return {"response": response}

    except ConnectionError:
        raise HTTPException(status_code=500, detail="Error connecting to storage")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Route to delete file
@app.delete("/cdn/v1/files/{filename}")
async def delete_file(filename: str):
    """
    Delete a file from the CDN.

    - **filename**: The name of the file to delete.

    Returns:
    - **message**: A success message if the file was deleted successfully.
    - **error**: An error message if the file could not be deleted.
    """
    try:
        # Check if file exists
        if not drive.get(filename):
            raise HTTPException(status_code=404, detail="File not found")

        # Delete file from Deta Drive
        drive.delete(filename)

        # Return success message to client
        return {"message": "File deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Route to get file metadata    
@app.get("/")
async def root():
    '''
    Home page for API
    '''
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