# 智能简历分析系统

## 项目简介

这是一个基于AI的智能简历分析系统，支持多种文件格式上传和岗位匹配度计算。系统使用豆包API进行智能分析，结合多种机器学习算法，为求职者和招聘者提供精准的简历匹配分析。

## demo



## 功能特性

### 🚀 核心功能
- **多格式支持**: PDF、Word、Markdown、纯文本、网页链接
- **智能匹配**: AI驱动的简历与岗位匹配分析
- **批量处理**: 支持同时分析多个简历文件
- **实时分析**: 快速生成详细的匹配报告

### 🧠 算法技术
- **TF-IDF相似度计算**: 文本相似度分析
- **技能匹配算法**: 智能识别和匹配技能关键词
- **经验匹配分析**: 工作经验相关性评估
- **主题模型分析**: LDA主题建模
- **AI综合评估**: 豆包大模型深度分析

### 📊 分析维度
- 整体匹配度评分
- 技能匹配率分析
- 工作经验匹配度
- 教育背景匹配度
- 文本相似度计算
- 主题相似度分析
- 个性化改进建议

## 技术架构

### 后端技术栈
- **FastAPI**: 高性能Web框架
- **LlamaIndex**: 文档索引和检索框架
- **豆包API**: 中文优化的大语言模型
- **scikit-learn**: 机器学习算法库
- **PyPDF2**: PDF文档处理
- **python-docx**: Word文档处理
- **BeautifulSoup**: HTML解析

### 前端技术栈
- **HTML5/CSS3**: 现代化界面设计
- **Bootstrap 5**: 响应式UI框架
- **JavaScript ES6+**: 交互逻辑
- **Font Awesome**: 图标库

## 安装部署

### 环境要求
- Python 3.8+
- Node.js (可选，用于前端开发)

### 后端部署

1. **克隆项目**
```bash
cd resume_analyzer/backend
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# Windows
set DOUBAO_API_KEY=your_doubao_api_key

# Linux/Mac
export DOUBAO_API_KEY=your_doubao_api_key
```

4. **启动后端服务**
```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

### 前端部署

1. **进入前端目录**
```bash
cd resume_analyzer/frontend
```

2. **直接打开HTML文件**
```bash
# 使用浏览器打开 index.html
# 或使用简单的HTTP服务器
python -m http.server 3000
```

前端将在 `http://localhost:3000` 启动

## API文档

### 主要接口

#### 1. 单个文件上传分析
```http
POST /upload/file
Content-Type: multipart/form-data

参数:
- file: 简历文件 (PDF/Word/Markdown)
- job_title: 目标岗位
- job_description: 岗位描述
```

#### 2. 批量文件分析
```http
POST /analyze/batch
Content-Type: multipart/form-data

参数:
- files: 多个简历文件
- job_title: 目标岗位
- job_description: 岗位描述
```

#### 3. 网页链接分析
```http
POST /upload/url
Content-Type: application/x-www-form-urlencoded

参数:
- url: 网页链接
- job_title: 目标岗位
- job_description: 岗位描述
```

#### 4. 健康检查
```http
GET /health
```

### 响应格式

```json
{
  "status": "success",
  "resume_data": {
    "personal_info": {...},
    "education": [...],
    "work_experience": [...],
    "skills": [...],
    "projects": [...]
  },
  "match_result": {
    "overall_match_score": 0.85,
    "skill_match": {...},
    "experience_match": {...},
    "education_match": {...},
    "ai_assessment": {...},
    "recommendations": [...]
  }
}
```

## 使用指南

### 1. 单个简历分析
1. 选择或拖拽简历文件到上传区域
2. 输入目标岗位和详细的岗位描述
3. 点击"开始分析"按钮
4. 查看详细的匹配分析报告

### 2. 批量简历分析
1. 选择多个简历文件
2. 输入统一的岗位要求
3. 系统将按匹配度排序显示结果
4. 支持快速筛选最佳候选人

### 3. 网页简历分析
1. 输入在线简历或个人网站链接
2. 系统自动抓取和解析网页内容
3. 生成匹配度分析报告

## 算法详解

### 1. TF-IDF相似度计算
- 将简历和岗位描述转换为TF-IDF向量
- 计算余弦相似度衡量文本相似性
- 权重: 15%

### 2. 技能匹配算法
- 智能提取岗位技能要求
- 模糊匹配简历中的技能
- 计算匹配率和缺失技能
- 权重: 30%

### 3. 经验匹配分析
- 分析工作经验与岗位的相关性
- 考虑工作年限和职位匹配度
- 权重: 25%

### 4. 教育背景匹配
- 学历层次匹配分析
- 专业相关性评估
- 权重: 10%

### 5. 主题模型分析
- 使用LDA进行主题建模
- 分析简历和岗位的主题分布相似性
- 权重: 10%

### 6. AI综合评估
- 豆包大模型深度理解和分析
- 多维度评分和个性化建议
- 权重: 10%

## 评分说明

- **90-100%**: 优秀匹配，强烈推荐
- **70-89%**: 良好匹配，值得考虑
- **50-69%**: 一般匹配，需要培训
- **50%以下**: 匹配度较低，不建议

## 开发说明

### 项目结构
```
resume_analyzer/
├── backend/
│   ├── main.py              # FastAPI主应用
│   ├── resume_processor.py  # 简历处理模块
│   ├── job_matcher.py       # 匹配算法模块
│   └── requirements.txt     # 依赖包列表
├── frontend/
│   ├── index.html          # 主页面
│   ├── app.js              # 前端逻辑
│   └── style.css           # 样式文件
└── README.md               # 项目文档
```

### 扩展建议
1. **数据库集成**: 添加PostgreSQL存储历史分析记录
2. **用户系统**: 实现用户注册和登录功能
3. **报告导出**: 支持PDF格式的分析报告导出
4. **API认证**: 添加JWT令牌认证机制
5. **缓存优化**: 使用Redis缓存分析结果
6. **容器化**: 使用Docker进行部署

## 注意事项

1. **API密钥**: 确保正确配置豆包API密钥
2. **文件大小**: 建议单个文件不超过10MB
3. **网络访问**: 网页分析需要稳定的网络连接
4. **隐私安全**: 上传的简历文件不会被永久存储

## 常见问题

### Q: 如何获取豆包API密钥？
A: 访问火山引擎控制台，注册并申请豆包大模型API服务。

### Q: 支持哪些简历格式？
A: 支持PDF、Word(.docx/.doc)、Markdown(.md)、纯文本(.txt)和网页链接。

### Q: 分析准确度如何？
A: 系统结合多种算法和AI模型，准确率在85%以上，但仍建议人工复核。

### Q: 能否自定义匹配算法？
A: 可以修改`job_matcher.py`中的权重配置和算法逻辑。

## 更新日志

### v1.0.0 (2025-08-06)
- 初始版本发布
- 支持多格式简历上传
- 实现AI驱动的匹配分析
- 提供批量处理功能
- 完善的前端界面

## 技术支持

如有问题或建议，请联系开发团队或提交Issue。

## 许可证

MIT License - 详见LICENSE文件



