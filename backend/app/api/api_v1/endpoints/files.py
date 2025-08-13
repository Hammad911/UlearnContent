from fastapi import APIRouter, HTTPException
from typing import List
import os
from datetime import datetime

from app.core.config import settings

router = APIRouter()

@router.get("/list")
async def list_uploaded_files():
    """
    List all uploaded files in the upload directory
    """
    try:
        if not os.path.exists(settings.UPLOAD_DIR):
            return {"files": [], "total": 0}
        
        files = []
        for filename in os.listdir(settings.UPLOAD_DIR):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime)
                })
        
        return {
            "files": files,
            "total": len(files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.delete("/{filename}")
async def delete_file(filename: str):
    """
    Delete a specific uploaded file
    """
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=400, detail="Not a file")
        
        os.remove(file_path)
        
        return {"success": True, "message": f"File {filename} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.get("/info/{filename}")
async def get_file_info(filename: str):
    """
    Get information about a specific uploaded file
    """
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=400, detail="Not a file")
        
        stat = os.stat(file_path)
        
        return {
            "filename": filename,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "modified_at": datetime.fromtimestamp(stat.st_mtime),
            "file_type": os.path.splitext(filename)[1].lower()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_files():
    """
    Clean up old uploaded files (older than 24 hours)
    """
    try:
        if not os.path.exists(settings.UPLOAD_DIR):
            return {"deleted": 0, "message": "No files to clean up"}
        
        current_time = datetime.now()
        deleted_count = 0
        
        for filename in os.listdir(settings.UPLOAD_DIR):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                time_diff = current_time - file_time
                
                # Delete files older than 24 hours
                if time_diff.total_seconds() > 24 * 3600:
                    os.remove(file_path)
                    deleted_count += 1
        
        return {
            "deleted": deleted_count,
            "message": f"Cleaned up {deleted_count} old files"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup files: {str(e)}") 