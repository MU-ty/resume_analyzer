import os
import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import LatentDirichletAllocation
import re
import json
from llama_index.core.llms import CustomLLM
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, CompletionResponse, LLMMetadata
import requests
from collections import Counter

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

class JobMatcher:
    def __init__(self):
        self.api_key = os.getenv("DOUBAO_API_KEY")
        if not self.api_key:
            raise ValueError("请设置环境变量 DOUBAO_API_KEY")
        
        self.llm = DoubaoLLM(api_key=self.api_key)
        
        self.skill_weights = {
            'programming_languages': 0.25,
            'frameworks': 0.20,
            'databases': 0.15,
            'tools': 0.15,
            'soft_skills': 0.10,
            'domain_knowledge': 0.15
        }
    
    async def calculate_match(self, resume_data: Dict[str, Any], job_description: str, job_title: str) -> Dict[str, Any]:
        """
        匹配度
        """
        try:
            # 1.TF-IDF余弦相似度匹配
            tfidf_score = self._calculate_tfidf_similarity(resume_data, job_description)
            
            # 2.技能匹配分析
            skill_match = self._calculate_skill_match(resume_data, job_description)
            
            # 3.经验匹配分析
            experience_match = self._calculate_experience_match(resume_data, job_description)
            
            # 4.教育背景匹配
            education_match = self._calculate_education_match(resume_data, job_description)
            
            # 5.综合评估
            ai_assessment = await self._ai_comprehensive_assessment(resume_data, job_description, job_title)
            
            # 6.主题分析
            topic_match = self._calculate_topic_similarity(resume_data, job_description)
            
            #最终匹配度
            final_score = self._calculate_final_score({
                'tfidf_score': tfidf_score,
                'skill_match': skill_match,
                'experience_match': experience_match,
                'education_match': education_match,
                'topic_match': topic_match,
                'ai_score': ai_assessment.get('overall_score', 0.5)
            })
            
            #报告
            detailed_analysis = self._generate_detailed_analysis(
                resume_data, job_description, job_title,
                tfidf_score, skill_match, experience_match, education_match, topic_match, ai_assessment
            )
            
            return {
                'overall_match_score': final_score,
                'tfidf_similarity': tfidf_score,
                'skill_match': skill_match,
                'experience_match': experience_match,
                'education_match': education_match,
                'topic_similarity': topic_match,
                'ai_assessment': ai_assessment,
                'detailed_analysis': detailed_analysis,
                'recommendations': self._generate_recommendations(skill_match, experience_match, ai_assessment)
            }
            
        except Exception as e:
            return {
                'error': f"匹配计算失败: {str(e)}",
                'overall_match_score': 0.0
            }
    
    def _calculate_tfidf_similarity(self, resume_data: Dict[str, Any], job_description: str) -> float:
        """使用TF-IDF计算文本相似度"""
        try:
            # 构建简历文本
            resume_text = self._build_resume_text(resume_data)
            
            # TF-IDF向量化
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=1000,
                ngram_range=(1, 2),
                min_df=1
            )
            
            # 计算TF-IDF矩阵
            tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
            
            # 计算余弦相似度
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            print(f"TF-IDF计算失败: {e}")
            return 0.0
    
    def _calculate_skill_match(self, resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """计算技能匹配度"""
        try:
            # 提取岗位要求的技能
            job_skills = self._extract_job_skills(job_description)
            
            # 获取简历中的技能
            resume_skills = resume_data.get('skills', [])
            if isinstance(resume_skills, str):
                resume_skills = [resume_skills]
            
            # 添加关键词中的技能
            keywords = resume_data.get('keywords', [])
            resume_skills.extend(keywords)
            
            # 标准化技能名称
            resume_skills_normalized = [skill.lower().strip() for skill in resume_skills]
            job_skills_normalized = [skill.lower().strip() for skill in job_skills]
            
            # 计算匹配的技能
            matched_skills = []
            missing_skills = []
            
            for job_skill in job_skills_normalized:
                matched = False
                for resume_skill in resume_skills_normalized:
                    if job_skill in resume_skill or resume_skill in job_skill:
                        matched_skills.append(job_skill)
                        matched = True
                        break
                if not matched:
                    missing_skills.append(job_skill)
            
            # 计算匹配率
            match_rate = len(matched_skills) / len(job_skills_normalized) if job_skills_normalized else 0
            
            return {
                'match_rate': match_rate,
                'matched_skills': matched_skills,
                'missing_skills': missing_skills,
                'total_job_skills': len(job_skills_normalized),
                'total_resume_skills': len(resume_skills_normalized)
            }
            
        except Exception as e:
            print(f"技能匹配计算失败: {e}")
            return {'match_rate': 0.0, 'matched_skills': [], 'missing_skills': []}
    
    def _calculate_experience_match(self, resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """计算工作经验匹配度"""
        try:
            work_experience = resume_data.get('work_experience', [])
            
            if not work_experience:
                return {'match_score': 0.0, 'relevant_experience': [], 'total_years': 0}
            
            #总工作年限
            total_years = len(work_experience)  # 每个工作经历约1年
            
            #相关经验
            relevant_experience = []
            job_keywords = self._extract_job_keywords(job_description)
            
            for exp in work_experience:
                exp_text = f"{exp.get('position', '')} {exp.get('description', '')}"
                relevance_score = self._calculate_text_relevance(exp_text, job_keywords)
                
                if relevance_score > 0.3: 
                    relevant_experience.append({
                        'experience': exp,
                        'relevance_score': relevance_score
                    })
            
            # 计算经验匹配分数
            if relevant_experience:
                avg_relevance = sum(exp['relevance_score'] for exp in relevant_experience) / len(relevant_experience)
                experience_factor = min(total_years / 3.0, 1.0)  # 假设3年为满分
                match_score = avg_relevance * experience_factor
            else:
                match_score = 0.0
            
            return {
                'match_score': match_score,
                'relevant_experience': relevant_experience,
                'total_years': total_years,
                'relevant_positions': len(relevant_experience)
            }
            
        except Exception as e:
            print(f"经验匹配计算失败: {e}")
            return {'match_score': 0.0, 'relevant_experience': [], 'total_years': 0}
    
    def _calculate_education_match(self, resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """计算教育背景匹配度"""
        try:
            education = resume_data.get('education', [])
            if not education:
                return {'match_score': 0.0, 'degree_match': False, 'major_relevance': 0.0}

            # 只用中文关键词
            education_keywords = [
                '本科', '硕士', '博士', '学士', '学位', '计算机', '软件', '工程', '信息', '技术', '自动化', '电子', '通信', '人工智能',
                '电子信息', '通信工程', '自动化', '计算机科学', '软件工程'
            ]

            # 学历等级定义
            degree_level_map = {'博士': 3, 'phd': 3, '硕士': 2, 'master': 2, '本科': 1, '学士': 1, 'bachelor': 1}
            highest_level = 0
            highest_degree = ''
            degree_match = False
            major_relevance = 0.0

            # 岗位描述中学历要求
            job_desc = job_description.lower()
            required_degree = None
            if '博士' in job_desc or 'phd' in job_desc:
                required_degree = 3
            elif '硕士' in job_desc or 'master' in job_desc:
                required_degree = 2
            elif '本科' in job_desc or '学士' in job_desc or 'bachelor' in job_desc:
                required_degree = 1

            for edu in education:
                degree = edu.get('degree', '').lower()
                major = edu.get('major', '').lower()
                # 最高学历
                for k, v in degree_level_map.items():
                    if k in degree and v > highest_level:
                        highest_level = v
                        highest_degree = degree
                # 专业相关性
                major_text = f"{major} {degree}"
                relevance = self._calculate_text_relevance(major_text, education_keywords)
                major_relevance = max(major_relevance, relevance)

            # 学历是否满足岗位要求
            if required_degree is None or highest_level >= required_degree:
                degree_match = True

            # 评分
            match_score = (0.6 * (1.0 if degree_match else 0.0)) + (0.4 * major_relevance)

            return {
                'match_score': match_score,
                'degree_match': degree_match,
                'highest_degree': highest_degree,
                'major_relevance': major_relevance
            }

        except Exception as e:
            print(f"教育背景匹配计算失败: {e}")
            return {'match_score': 0.0, 'degree_match': False, 'major_relevance': 0.0}
    
    def _calculate_topic_similarity(self, resume_data: Dict[str, Any], job_description: str) -> float:
        """使用主题模型计算相似度"""
        try:
            # 构建文档
            resume_text = self._build_resume_text(resume_data)
            documents = [resume_text, job_description]
            
            # TF-IDF向量化
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                min_df=1
            )
            
            tfidf_matrix = vectorizer.fit_transform(documents)
            
            # LDA主题建模
            lda = LatentDirichletAllocation(n_components=5, random_state=42)
            topic_distributions = lda.fit_transform(tfidf_matrix)
            
            # 计算主题分布的相似度
            similarity = cosine_similarity(
                topic_distributions[0:1], 
                topic_distributions[1:2]
            )[0][0]
            
            return float(similarity)
            
        except Exception as e:
            print(f"主题相似度计算失败: {e}")
            return 0.0
    
    async def _ai_comprehensive_assessment(self, resume_data: Dict[str, Any], job_description: str, job_title: str) -> Dict[str, Any]:
        """使用AI进行综合评估"""
        try:
            resume_text = self._build_resume_text(resume_data)
            
            prompt = f"""
            作为一名专业的HR和技术专家，请评估以下简历与目标岗位的匹配度：

            目标岗位：{job_title}

            岗位描述：
            {job_description}

            候选人简历：
            {resume_text}

            请从以下几个维度进行评估（0-1分）：
            1. 技术技能匹配度
            2. 工作经验相关性
            3. 项目经验适配度
            4. 学习能力和发展潜力
            5. 整体适合度

            请以JSON格式返回评估结果：
            {{
                "technical_skills": 0.8,
                "work_experience": 0.7,
                "project_experience": 0.6,
                "learning_potential": 0.8,
                "overall_score": 0.75,
                "strengths": ["优势1", "优势2"],
                "weaknesses": ["不足1", "不足2"],
                "summary": "综合评估总结"
            }}
            """
            
            response = self.llm.complete(prompt)
            result_text = response.text
            
            # 尝试解析JSON
            try:
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass
            
            # 如果解析失败，返回默认结构
            return {
                "technical_skills": 0.5,
                "work_experience": 0.5,
                "project_experience": 0.5,
                "learning_potential": 0.5,
                "overall_score": 0.5,
                "strengths": ["需要进一步分析"],
                "weaknesses": ["需要进一步分析"],
                "summary": "AI评估暂时不可用"
            }
            
        except Exception as e:
            print(f"AI评估失败: {e}")
            return {
                "technical_skills": 0.5,
                "work_experience": 0.5,
                "project_experience": 0.5,
                "learning_potential": 0.5,
                "overall_score": 0.5,
                "strengths": [],
                "weaknesses": [],
                "summary": f"评估失败: {str(e)}"
            }
    
    def _calculate_final_score(self, scores: Dict[str, float]) -> float:
        """计算最终匹配分数"""
        weights = {
            'tfidf_score': 0.15,
            'skill_match': 0.30,
            'experience_match': 0.25,
            'education_match': 0.10,
            'topic_match': 0.10,
            'ai_score': 0.10
        }
        
        final_score = 0.0
        for metric, score in scores.items():
            if metric in weights:
                if isinstance(score, dict):
                    score = score.get('match_rate', 0.0) if 'match_rate' in score else score.get('match_score', 0.0)
                final_score += weights[metric] * score
        
        return min(max(final_score, 0.0), 1.0)  # 确保分数在0-1之间
    
    def _build_resume_text(self, resume_data: Dict[str, Any]) -> str:
        """构建简历文本"""
        text_parts = []
        
        # 添加原始文本
        if 'raw_text' in resume_data:
            text_parts.append(resume_data['raw_text'])
        
        # 添加技能
        skills = resume_data.get('skills', [])
        if skills:
            text_parts.append(' '.join(skills))
        
        # 添加工作经验
        work_exp = resume_data.get('work_experience', [])
        for exp in work_exp:
            if isinstance(exp, dict):
                text_parts.append(f"{exp.get('position', '')} {exp.get('description', '')}")
        
        # 添加项目经验
        projects = resume_data.get('projects', [])
        for project in projects:
            if isinstance(project, dict):
                text_parts.append(f"{project.get('name', '')} {project.get('description', '')}")
        
        return ' '.join(text_parts)
    
    def _extract_job_skills(self, job_description: str) -> List[str]:
        """从岗位描述中提取技能要求"""
        # 常见技术技能关键词
        tech_skills = [
            'python', 'java', 'javascript', 'react', 'vue', 'angular', 'node.js',
            'django', 'flask', 'spring', 'mysql', 'postgresql', 'mongodb',
            'docker', 'kubernetes', 'aws', 'azure', 'git', 'linux',
            'machine learning', 'deep learning', 'ai', 'data analysis',
            'html', 'css', 'sql', 'redis', 'elasticsearch', 'microservices',
            'agile', 'scrum', 'devops', 'ci/cd', 'api', 'graphql',
            'testing', 'unit testing', 'integration testing', 'selenium', 'junit', 'testng',
            '人工智能', '大数据', '数据分析', '深度学习', '机器学习', '前端', '后端', '全栈', '小程序',
            '算法', '架构', '测试', '自动化测试', '项目管理', '产品经理', '运维', '云计算', '区块链',
            '移动开发', '安卓', 'iOS', '嵌入式', '网络安全', '数据挖掘', '爬虫', '数据库', '分布式',
            '高并发', '高可用', '微服务', '接口', '中台', 'ERP', 'CRM', 'OA', 'CMS', 'B2B', 'B2C',
            'SaaS', 'PaaS', 'IaaS', '物联网', '边缘计算', '智能硬件', '虚拟现实', '增强现实', '5G',
            '区块链', '智能合约', '数字货币', 'NFT', '云原生', '边缘计算', '容器化', '服务网格',
            '持续集成', '持续部署', '自动化运维', '基础设施即代码', '监控', '日志分析', '性能优化',
            '安全', '加密', '身份认证', '访问控制', '漏洞扫描', '渗透测试', '安全审计',
            '数据可视化', 'BI', '报表', '数据仓库', 'ETL', '数据治理', '数据质量',
            '数据建模', '数据挖掘', '数据科学', '统计分析', '自然语言处理',
        ]
        
        job_desc_lower = job_description.lower()
        found_skills = []
        
        for skill in tech_skills:
            if skill in job_desc_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """提取岗位关键词"""
        # 简单的关键词提取
        words = re.findall(r'\b\w+\b', job_description.lower())
        # 过滤常见停用词
        stopwords = {'的', '了', '和', '是', '在', '与', '及', '为', '对', '等', '也', '就', '都', '而', '及其', '并', '或', '被', '由', '于'}
        keywords = [word for word in words if len(word) > 1 and word not in stopwords]

        # 返回最常见的关键词
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(20)]
    
    def _calculate_text_relevance(self, text: str, keywords: List[str]) -> float:
        """计算文本与关键词的相关性"""
        text_lower = text.lower()
        matched_keywords = sum(1 for keyword in keywords if keyword in text_lower)
        return matched_keywords / len(keywords) if keywords else 0.0
    
    def _generate_detailed_analysis(self, resume_data, job_description, job_title, 
                                  tfidf_score, skill_match, experience_match, 
                                  education_match, topic_match, ai_assessment) -> str:
        """生成详细分析报告"""
        analysis = f"""
        ## 简历匹配分析报告

        **岗位**: {job_title}

        ### 1. 文本相似度分析
        - TF-IDF相似度: {tfidf_score:.2%}
        - 主题相似度: {topic_match:.2%}

        ### 2. 技能匹配分析
        - 技能匹配率: {skill_match.get('match_rate', 0):.2%}
        - 匹配技能: {', '.join(skill_match.get('matched_skills', [])[:5])}
        - 缺失技能: {', '.join(skill_match.get('missing_skills', [])[:3])}

        ### 3. 工作经验分析
        - 经验匹配度: {experience_match.get('match_score', 0):.2%}
        - 相关工作经历: {experience_match.get('relevant_positions', 0)}个

        ### 4. 教育背景分析
        - 教育匹配度: {education_match.get('match_score', 0):.2%}
        - 学历匹配: {'是' if education_match.get('degree_match', False) else '否'}

        ### 5. AI综合评估
        - 整体评分: {ai_assessment.get('overall_score', 0):.2%}
        - 主要优势: {', '.join(ai_assessment.get('strengths', [])[:3])}
        - 需要改进: {', '.join(ai_assessment.get('weaknesses', [])[:3])}
        """
        
        return analysis
    
    def _generate_recommendations(self, skill_match, experience_match, ai_assessment) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于技能匹配的建议
        missing_skills = skill_match.get('missing_skills', [])
        if missing_skills:
            recommendations.append(f"建议学习以下技能: {', '.join(missing_skills[:3])}")
        
        # 基于经验匹配的建议
        if experience_match.get('match_score', 0) < 0.6:
            recommendations.append("建议积累更多相关项目经验")
        
        # 基于AI评估的建议
        weaknesses = ai_assessment.get('weaknesses', [])
        if weaknesses:
            recommendations.append(f"需要提升: {', '.join(weaknesses[:2])}")
        
        if not recommendations:
            recommendations.append("整体匹配度较好，建议继续保持和提升现有技能")
        
        return recommendations
