from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict
from raqp import RAQP

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/query")
async def query_endpoint(request: Request):
    body = await request.json()
    input_text = body.get("query", "")
    raqp_output = RAQP.process(input_text)
    print("RAQP Output:")
    print(raqp_output.table)
    return JSONResponse(content={"text": raqp_output.text, "table": raqp_output.table})

@app.get("/")
async def root():
    return {"message": "RAQP Backend is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)