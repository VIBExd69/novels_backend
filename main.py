import os
from fastapi import FastAPI, HTTPException, Body, Query, Response, status, Depends
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from bson import ObjectId
from typing import Dict, Any, Optional
import traceback

API_TOKEN = "elytecode@#$2025"
MONGO_URL = "mongodb+srv://asbah1234:asbah1234@cluster0.vx5ta.mongodb.net/?appName=Cluster0"

app = FastAPI(title="Universal Flexible Backend (Secured)")

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("Connected to MongoDB Atlas Successfully!")
except Exception as e:
    print(f"Connection Failed: {e}")

db = client["urdu_novels_db"]

def verify_token(token: str = Query(...)):
    if token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied: Invalid Token"
        )
    return token

def get_filter(col, doc_id_str):
    if ObjectId.is_valid(doc_id_str):
        if col.find_one({"_id": ObjectId(doc_id_str)}):
            return {"_id": ObjectId(doc_id_str)}
    if col.find_one({"_id": doc_id_str}):
        return {"_id": doc_id_str}
    if col.find_one({"doc_id": doc_id_str}):
        return {"doc_id": doc_id_str}
    if col.find_one({"_doc_id": doc_id_str}):
        return {"_doc_id": doc_id_str}
    return None

def clean_doc(doc):
    if not doc: return None
    doc_id_val = str(doc.get("_id"))
    doc["doc_id"] = doc_id_val
    if "_id" in doc: del doc["_id"]
    if "_doc_id" in doc: del doc["_doc_id"]
    return doc

@app.get("/collection")
def get_data(
    response: Response,
    collectionName: str = Query(...),
    document: Optional[str] = Query(None),
    token: str = Depends(verify_token) 
):
    try:
        col = db[collectionName]
        if document:
            query = get_filter(col, document)
            if not query:
                return JSONResponse(status_code=404, content={"error": "Document not found"})
            doc = col.find_one(query)
            return clean_doc(doc)
        else:
            cursor = col.find().limit(50)
            results = [clean_doc(d) for d in cursor]
            return results
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/collection")
def save_data(
    response: Response,
    collectionName: str = Query(...),
    document: str = Query(...),
    data: Dict[str, Any] = Body(...),
    token: str = Depends(verify_token)
):
    try:
        col = db[collectionName]
        query = get_filter(col, document)
        if query:
            col.update_one(query, {"$set": data})
            return {"status": "success", "message": "Updated", "doc_id": document}
        else:
            new_doc = data
            new_doc["_id"] = document
            new_doc["doc_id"] = document
            col.insert_one(new_doc)
            response.status_code = status.HTTP_201_CREATED
            return {"status": "success", "message": "Created", "doc_id": document}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.delete("/collection")
def delete_data(
    collectionName: str = Query(...), 
    document: Optional[str] = Query(None),
    token: str = Depends(verify_token)
):
    try:
        col = db[collectionName]
        if document:
            query = get_filter(col, document)
            if not query:
                return JSONResponse(status_code=404, content={"error": "Not found"})
            col.delete_one(query)
            return {"status": "success", "message": "Deleted"}
        else:
            col.delete_many({})
            return {"status": "success", "message": "All Deleted"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)