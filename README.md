CDN API 🪐
=======

This project implements a basic CDN (Content Delivery Network) API using FastAPI and Deta Drive for file storage.

Overview
--------

The API exposes endpoints for uploading, downloading, listing, and deleting files from a Deta Drive instance used for storage. FastAPI is used to create the web service with Python.

Some key features:

*   Upload files up to 100MB
*   Downloads files on demand
*   Lists all uploaded files
*   Deletes files by name
*   Validates allowed file extensions
*   Logging for diagnostics

Usage
-----

The API can be deployed locally or to a web host. The following environment variables need to be configured:

*   `DRIVE_PROJECT_KEY` - Deta project key
*   `DRIVE_PROJECT_NAME` - Deta Drive name

Install dependencies:

Copy code

`pip install fastapi deta python-dotenv`

Run the service:

Copy code

`uvicorn main:app`

The API will then be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

The following endpoints are exposed:

*   `POST /uploadfile/` - Upload a file
*   `GET /files/{filename}` - Download a file
*   `GET /files/` - List all files
*   `DELETE /files/{filename}` - Delete a file

Contributing
------------

Pull requests are welcome. Feel free to open issues for any bugs or enhancements.

This project is intended to demonstrate a basic CDN API implementation. There is room to expand with caching, access controls, etc.