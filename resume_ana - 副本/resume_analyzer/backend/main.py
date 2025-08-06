from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import tempfile
from typing import List, Optional
import json
from resume_processor import ResumeProcessor
from job_matcher import JobMatcher

app = FastAPI(title="智能简历分析系统", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化处理器
resume_processor = ResumeProcessor()
job_matcher = JobMatcher()

@app.get("/")
async def root():
    return {"message": "智能简历分析系统 API"}

@app.post("/upload/file")
async def upload_file(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    job_title: str = Form(...)
):
    """
    上传文件并分析简历与岗位匹配度
    支持格式：PDF、Word、Markdown
    """
    try:
        # 检查文件格式
        allowed_extensions = {'.pdf', '.docx', '.doc', '.md', '.txt'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持的格式: {', '.join(allowed_extensions)}"
            )
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 处理简历
            resume_data = await resume_processor.process_file(temp_file_path, file_extension)
            
            # 计算匹配度
            match_result = await job_matcher.calculate_match(
                resume_data, job_description, job_title
            )
            
            result = {
                "status": "success",
                "resume_data": resume_data,
                "match_result": match_result,
                "file_info": {
                    "filename": file.filename,
                    "size": len(content),
                    "type": file_extension
                }
            }
            
            return JSONResponse(content=result)
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@app.post("/upload/url")
async def upload_url(
    url: str = Form(...),
    job_description: str = Form(...),
    job_title: str = Form(...)
):
    """
    通过URL分析网页简历与岗位匹配度
    """
    try:
        # 处理网页简历
        resume_data = await resume_processor.process_url(url)
        
        # 计算匹配度
        match_result = await job_matcher.calculate_match(
            resume_data, job_description, job_title
        )
        
        result = {
            "status": "success",
            "resume_data": resume_data,
            "match_result": match_result,
            "url_info": {
                "url": url,
                "type": "webpage"
            }
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@app.post("/analyze/batch")
async def analyze_batch(
    files: List[UploadFile] = File(...),
    job_description: str = Form(...),
    job_title: str = Form(...)
):
    """
    批量分析多个简历文件
    """
    try:
        results = []
        
        for file in files:
            # 检查文件格式
            allowed_extensions = {'.pdf', '.docx', '.doc', '.md', '.txt'}
            file_extension = os.path.splitext(file.filename)[1].lower()
            
            if file_extension not in allowed_extensions:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": f"不支持的文件格式: {file_extension}"
                })
                continue
            
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # 处理简历
                resume_data = await resume_processor.process_file(temp_file_path, file_extension)
                
                # 计算匹配度
                match_result = await job_matcher.calculate_match(
                    resume_data, job_description, job_title
                )
                
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "resume_data": resume_data,
                    "match_result": match_result
                })
                
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": str(e)
                })
            finally:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        return JSONResponse(content={
            "status": "success",
            "total_files": len(files),
            "results": results
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "智能简历分析系统"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
