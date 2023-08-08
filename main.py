# Import FastAPI and Deta Drive libraries
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import Response
import  deta 
import logging
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

# Set allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Initialize logger
logging.basicConfig(filename='app.log', level=logging.DEBUG)

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
        if file.filename.split('.')[-1] not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="File type not allowed")

        # Check if filename already exists
        existing = drive.get(file.filename)
        if existing:
            return {"error": "File already exists"}
        
        # Save uploaded file to Deta Drive 
        name = file.filename
        drive.put(name, content)

        # Log file upload event
        logging.info(f"File uploaded: {name}")

        # Return success message to client
        return {"message": "File uploaded successfully"}
    
    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Route to download file
@app.get("/cdn/v1/files/{filename}") 
async def download_file(filename):

    try:
        # Check if image file
        if filename.split('.')[-1] in {'png', 'jpg', 'jpeg', 'gif'}:
            
            # Retrieve file data without sending to client yet
            file = drive.get(filename)
            image_data = file.read()
            
            # Send file to client with appropriate media type eg, image/png or image/jpeg etc
            return Response(content=image_data, media_type=f"image/{filename.split('.')[-1]}")

        else:
            # For non-image files, download normally
            file = drive.get(filename)
            contents = file.read()

            headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'application/octet-stream'
            }

            return Response(content=contents, headers=headers)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to get all files
@app.get("/cdn/v1/files/")
async def get_files():
    """
    Get a list of all files in the CDN.

    Returns:
    - **response**: A dictionary containing a list of all files in the CDN and pagination information.
    - **error**: An error message if the file list could not be retrieved.
    """
    try:
    
        # Get all files from Deta Drive
        result = drive.list()
        all_files = result.get("names")
        paging = result.get("paging", {})
        size = len(all_files)
        last = paging.get("last", None)

        while last:
            # Provide "last" from previous call.
            result = drive.list(last=last)
            all_files += result.get("names")
            paging = result.get("paging", {})
            size += len(result.get("names"))
            last = paging.get("last", None)

        # Create response dictionary
        response = {"names": all_files, "paging": {"size": size, "last": last}}

        # Log file list event
        logging.info("File list retrieved")

        # Return response to client
        return {"response": response}

    except ConnectionError:
        logging.error("Error connecting to storage")
        raise HTTPException(status_code=500, detail="Error connecting to storage")

    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
# Route to delete file
@app.delete("/cdn/v1/files/{filename}")
async def delete_file(filename):
    """
    Delete a file from the CDN.

    - **filename**: The name of the file to delete.

    Returns:
    - **message**: A success message if the file was deleted successfully.
    - **error**: An error message if the file could not be deleted.
    """
    try:
        # Check if file exists
        existing = drive.get(filename)
        if not existing:
            raise HTTPException(status_code=404, detail="File not found")

        # Delete file from Deta Drive
        drive.delete(filename)

        # Log file deletion event
        logging.info(f"File deleted: {filename}")

        # Return success message to client
        return {"message": "File deleted successfully"}

    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))