import os
from fastapi import FastAPI, HTTPException, Body, Query, Response, status
from pymongo import MongoClient
from bson import ObjectId
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Universal Flexible Backend")

MONGO_URL = "mongodb+srv://asbah1234:asbah1234@cluster0.vx5ta.mongodb.net/?appName=Cluster0"

try:
    client = MongoClient(MONGO_URL)
    client.admin.command('ping')
    print(f"Connected to MongoDB at: {MONGO_URL[:10]}...") 
except Exception as e:
    print(f"Connection Error: {e}")

db = client["urdu_novels_db"]

def get_filter(col, doc_id_str):
    if ObjectId.is_valid(doc_id_str):
        if col.find_one({"_id": ObjectId(doc_id_str)}):
            return {"_id": ObjectId(doc_id_str)}
    
    if col.find_one({"_id": doc_id_str}):
        return {"_id": doc_id_str}

    if col.find_one({"_doc_id": doc_id_str}):
        return {"_doc_id": doc_id_str}

    return None

def clean_doc(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

@app.get("/collection")
def get_data(
    response: Response,
    collectionName: str = Query(...),
    document: Optional[str] = Query(None)
):
    col = db[collectionName]

    if document:
        query = get_filter(col, document)
        
        if not query:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = col.find_one(query)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        return clean_doc(doc)

    else:
        cursor = col.find().limit(50)
        results = []
        for d in cursor:
            results.append(clean_doc(d))
        return results

@app.post("/collection", status_code=status.HTTP_200_OK)
def save_data(
    response: Response,
    collectionName: str = Query(...),
    document: str = Query(...),
    data: Dict[str, Any] = Body(...)
):
    col = db[collectionName]
    query = get_filter(col, document)

    if query:
        col.update_one(query, {"$set": data})
        return {
            "status": "success", 
            "message": f"Updated existing document: {document}",
            "updated_fields": data
        }
    else:
        new_doc = data
        new_doc["_id"] = document
        new_doc["_doc_id"] = document
        
        try:
            col.insert_one(new_doc)
            response.status_code = status.HTTP_201_CREATED
            return {
                "status": "success",
                "message": f"Created NEW document with ID: {document}",
                "data": new_doc
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.delete("/collection")
def delete_data(
    collectionName: str = Query(...),
    document: Optional[str] = Query(None)
):
    col = db[collectionName]

    if document:
        query = get_filter(col, document)
        if not query:
             raise HTTPException(status_code=404, detail="Document to delete not found")
             
        result = col.delete_one(query)
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
            
        return {"status": "success", "message": f"Deleted document: {document}"}

    else:
        result = col.delete_many({})
        return {
            "status": "success", 
            "message": f"Collection '{collectionName}' cleared. Deleted {result.deleted_count} documents."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)