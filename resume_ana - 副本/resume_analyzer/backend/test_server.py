from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/upload/file")
async def upload_file(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    job_title: str = Form(...)
):
    return {
        "status": "success",
        "match_result": {
            "overall_match_score": 0.75,
            "skill_match": {
                "match_rate": 0.8,
                "matched_skills": ["Python", "JavaScript"],
                "missing_skills": ["React"]
            },
            "experience_match": {"match_score": 0.7},
            "education_match": {"match_score": 0.8},
            "tfidf_similarity": 0.72,
            "topic_similarity": 0.68,
            "ai_assessment": {
                "technical_skills": 0.75,
                "learning_potential": 0.85,
                "summary": "测试结果"
            },
            "recommendations": ["继续学习"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
