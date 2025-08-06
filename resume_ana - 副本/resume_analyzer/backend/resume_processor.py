import os
import asyncio
from typing import Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
import PyPDF2
import docx
import markdown
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import CustomLLM
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, CompletionResponse, LLMMetadata
import requests
from pydantic import BaseModel
import re
import json
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class DoubaoEmbedding(BaseEmbedding, BaseModel):
    api_key: str
    model: str = "doubao-embedding-text-240715"
    api_url: str = "https://ark.cn-beijing.volces.com/api/v3/embeddings"

    def _get_query_embedding(self, query: str):
        return self._get_text_embedding(query)
    
    async def _aget_query_embedding(self, query: str):
        return self._get_text_embedding(query)
    
    def _get_text_embedding(self, text: str):
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "encoding_format": "float",
                    "input": [text],
                    "model": self.model
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["data"][0]["embedding"]
            else:
                print(f"豆包嵌入API错误: {response.status_code}")
                return [0.0] * 768
        except Exception as e:
            print(f"嵌入请求失败: {e}")
            return [0.0] * 768
    
    async def _aget_text_embedding(self, text: str):
        return self._get_text_embedding(text)
    
    def _get_text_embeddings(self, texts):
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "encoding_format": "float",
                    "input": texts,
                    "model": self.model
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return [item["embedding"] for item in result["data"]]
            else:
                return [[0.0] * 768 for _ in texts]
        except Exception as e:
            return [[0.0] * 768 for _ in texts]
    
    async def _aget_text_embeddings(self, texts):
        return self._get_text_embeddings(texts)

class DoubaoLLM(CustomLLM):
    api_key: str
    model: str = "doubao-1-5-pro-32k-250115"
    api_url: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    
    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=32000,
            num_output=4000,
            model_name=self.model
        )
    
    def _complete(self, prompt: str, **kwargs) -> CompletionResponse:
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return CompletionResponse(text=content)
            else:
                return CompletionResponse(text="生成失败")
        except Exception as e:
            return CompletionResponse(text="生成失败")
    
    def _chat(self, messages, **kwargs) -> ChatResponse:
        try:
            api_messages = []
            for msg in messages:
                api_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": self.model,
                    "messages": api_messages
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return ChatResponse(
                    message=ChatMessage(role="assistant", content=content)
                )
            else:
                return ChatResponse(
                    message=ChatMessage(role="assistant", content="生成失败")
                )
        except Exception as e:
            return ChatResponse(
                message=ChatMessage(role="assistant", content="生成失败")
            )
    
    async def acomplete(self, prompt: str, **kwargs) -> CompletionResponse:
        return self._complete(prompt, **kwargs)
    
    async def achat(self, messages, **kwargs) -> ChatResponse:
        return self._chat(messages, **kwargs)
    
    async def astream_complete(self, prompt: str, **kwargs):
        raise NotImplementedError("astream_complete is not implemented")
    
    async def astream_chat(self, messages, **kwargs):
        raise NotImplementedError("astream_chat is not implemented")
    
    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        return self._complete(prompt, **kwargs)
    
    def chat(self, messages, **kwargs) -> ChatResponse:
        return self._chat(messages, **kwargs)
    
    def stream_complete(self, prompt: str, **kwargs):
        raise NotImplementedError("stream_complete is not implemented")
    
    def stream_chat(self, messages, **kwargs):
        raise NotImplementedError("stream_chat is not implemented")
    
    def _as_query_component(self):
        raise NotImplementedError("_as_query_component is not implemented")

class ResumeProcessor:
    def __init__(self):
        # 获取豆包API密钥
        self.api_key = os.getenv("DOUBAO_API_KEY")
        if not self.api_key:
            raise ValueError("请设置环境变量 DOUBAO_API_KEY")
        
        # 配置LlamaIndex
        Settings.embed_model = DoubaoEmbedding(api_key=self.api_key)
        Settings.llm = DoubaoLLM(api_key=self.api_key)
        Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    
    async def process_file(self, file_path: str, file_extension: str) -> Dict[str, Any]:
        """处理上传的文件"""
        try:
            # 根据文件类型提取文本
            if file_extension == '.pdf':
                text = self._extract_pdf_text(file_path)
            elif file_extension in ['.docx', '.doc']:
                text = self._extract_word_text(file_path)
            elif file_extension == '.md':
                text = self._extract_markdown_text(file_path)
            elif file_extension == '.txt':
                text = self._extract_txt_text(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")
            
            #分析简历
            resume_data = await self._analyze_resume_with_ai(text)
            
            #关键词
            keywords = self._extract_keywords(text)
            
            resume_data.update({
                'raw_text': text,
                'keywords': keywords,
                'text_length': len(text)
            })
            
            return resume_data
            
        except Exception as e:
            raise Exception(f"文件处理失败: {str(e)}")
    
    async def process_url(self, url: str) -> Dict[str, Any]:
        """处理网页URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        text = self._extract_html_text(html_content)
                    else:
                        raise Exception(f"无法访问URL: {response.status}")
            
            # 使用AI分析简历
            resume_data = await self._analyze_resume_with_ai(text)
            
            # 提取关键词
            keywords = self._extract_keywords(text)
            
            resume_data.update({
                'raw_text': text,
                'keywords': keywords,
                'text_length': len(text),
                'source_url': url
            })
            
            return resume_data
            
        except Exception as e:
            raise Exception(f"URL处理失败: {str(e)}")
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """提取PDF文本"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            raise Exception(f"PDF解析失败: {str(e)}")
    
    def _extract_word_text(self, file_path: str) -> str:
        """提取Word文档文本"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Word文档解析失败: {str(e)}")
    
    def _extract_markdown_text(self, file_path: str) -> str:
        """提取Markdown文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                md_content = file.read()
                # 转换为HTML然后提取纯文本
                html = markdown.markdown(md_content)
                soup = BeautifulSoup(html, 'html.parser')
                return soup.get_text()
        except Exception as e:
            raise Exception(f"Markdown解析失败: {str(e)}")
    
    def _extract_txt_text(self, file_path: str) -> str:
        """提取纯文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"文本文件解析失败: {str(e)}")
    
    def _extract_html_text(self, html_content: str) -> str:
        """提取HTML文本"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 获取文本
        text = soup.get_text()
        
        # 清理文本
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    async def _analyze_resume_with_ai(self, text: str) -> Dict[str, Any]:
        """使用AI分析简历内容"""
        try:
            llm = DoubaoLLM(api_key=self.api_key)
            
            prompt = f"""
            请分析以下简历内容，提取关键信息并以JSON格式返回：

            简历内容：
            {text}

            请提取以下信息（如果没有相关信息，请设置为null）：
            1. 个人信息：姓名、联系方式、邮箱等
            2. 教育背景：学校、专业、学历、毕业时间等
            3. 工作经验：公司、职位、工作时间、职责描述等
            4. 技能：专业技能、编程语言、工具等
            5. 项目经验：项目名称、描述、技术栈等
            6. 证书/奖项：相关认证和获奖情况

            请以以下JSON格式返回：
            {{
                "personal_info": {{
                    "name": "姓名",
                    "contact": "联系方式",
                    "email": "邮箱"
                }},
                "education": [
                    {{
                        "school": "学校名称",
                        "major": "专业",
                        "degree": "学历",
                        "graduation_year": "毕业年份"
                    }}
                ],
                "work_experience": [
                    {{
                        "company": "公司名称",
                        "position": "职位",
                        "duration": "工作时间",
                        "description": "工作描述"
                    }}
                ],
                "skills": ["技能1", "技能2", "技能3"],
                "projects": [
                    {{
                        "name": "项目名称",
                        "description": "项目描述",
                        "technologies": ["技术1", "技术2"]
                    }}
                ],
                "certificates": ["证书1", "证书2"]
            }}
            """
            
            response = llm.complete(prompt)
            result_text = response.text
            
            # 尝试解析JSON
            try:
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    return json.loads(json_str)
                else:
                    # 如果没有找到JSON，返回基本结构
                    return self._create_basic_structure(text)
            except json.JSONDecodeError:
                return self._create_basic_structure(text)
                
        except Exception as e:
            print(f"AI分析失败: {e}")
            return self._create_basic_structure(text)
    
    def _create_basic_structure(self, text: str) -> Dict[str, Any]:
        """创建基本的简历结构"""
        return {
            "personal_info": {
                "name": self._extract_name(text),
                "contact": None,
                "email": self._extract_email(text)
            },
            "education": [],
            "work_experience": [],
            "skills": self._extract_basic_skills(text),
            "projects": [],
            "certificates": []
        }
    
    def _extract_name(self, text: str) -> Optional[str]:
        """简单的姓名提取"""
        lines = text.split('\n')
        for line in lines[:5]:  # 检查前5行
            line = line.strip()
            if len(line) > 0 and len(line) < 20 and not '@' in line:
                return line
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """提取邮箱"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None
    
    def _extract_basic_skills(self, text: str) -> list:
        """提取基本技能关键词"""
        skill_keywords = [
            'python', 'java', 'javascript', 'react', 'vue', 'angular', 'node.js',
            'django', 'flask', 'spring', 'mysql', 'postgresql', 'mongodb',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 'linux',
            'machine learning', 'deep learning', 'ai', 'data analysis'
        ]
        
        found_skills = []
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_keywords(self, text: str) -> list:
        """使用TF-IDF提取关键词"""
        try:
            # 分句
            sentences = re.split(r'[.!?。！？\n]', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            
            if len(sentences) < 2:
                return []
            
            # TF-IDF向量化
            vectorizer = TfidfVectorizer(
                max_features=20,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.8
            )
            
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            
            # 计算平均TF-IDF分数
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # 获取分数最高的关键词
            top_indices = mean_scores.argsort()[-10:][::-1]
            keywords = [feature_names[i] for i in top_indices]
            
            return keywords
        except Exception as e:
            print(f"关键词提取失败: {e}")
            return []
