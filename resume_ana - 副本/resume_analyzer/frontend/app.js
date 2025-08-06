// API基础URL
const API_BASE_URL = 'http://localhost:8001';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async function() {
    // 文件拖拽上传功能
    function setupDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');
        const areas = [uploadArea, document.getElementById('batchUploadArea')];
        
        areas.forEach(area => {
            if (!area) return;
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                area.addEventListener(eventName, preventDefaults, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                area.addEventListener(eventName, highlight, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                area.addEventListener(eventName, unhighlight, false);
            });

            area.addEventListener('drop', handleDrop, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        function highlight(e) {
            e.currentTarget.classList.add('dragover');
        }

        function unhighlight(e) {
            e.currentTarget.classList.remove('dragover');
        }

        function handleDrop(e) {
            const files = e.dataTransfer.files;
            const target = e.currentTarget;
            
            console.log('文件拖拽事件:', {
                targetId: target.id,
                filesCount: files.length,
                files: Array.from(files).map(f => f.name)
            });
            
            if (target.id === 'uploadArea') {
                let resumeFile = document.getElementById('resumeFile');
                
                // 如果文件输入框不存在，先创建它
                if (!resumeFile) {
                    console.log('创建新的文件输入框');
                    resumeFile = document.createElement('input');
                    resumeFile.type = 'file';
                    resumeFile.id = 'resumeFile';
                    resumeFile.name = 'file';
                    resumeFile.accept = '.pdf,.docx,.doc,.md,.txt';
                    resumeFile.style.display = 'none';
                    target.appendChild(resumeFile);
                }
                
                const dt = new DataTransfer();
                dt.items.add(files[0]);
                resumeFile.files = dt.files;
                displaySelectedFile(files[0]);
            } else if (target.id === 'batchUploadArea') {
                let batchResumeFiles = document.getElementById('batchResumeFiles');
                
                // 如果批量文件输入框不存在，先创建它
                if (!batchResumeFiles) {
                    console.log('创建新的批量文件输入框');
                    batchResumeFiles = document.createElement('input');
                    batchResumeFiles.type = 'file';
                    batchResumeFiles.id = 'batchResumeFiles';
                    batchResumeFiles.name = 'files';
                    batchResumeFiles.multiple = true;
                    batchResumeFiles.accept = '.pdf,.docx,.doc,.md,.txt';
                    batchResumeFiles.style.display = 'none';
                    target.appendChild(batchResumeFiles);
                    
                    // 添加事件监听器
                    batchResumeFiles.addEventListener('change', function(e) {
                        console.log('批量文件选择发生变化:', e.target.files);
                        displaySelectedFiles(e.target.files);
                    });
                }
                
                const dt = new DataTransfer();
                for (let i = 0; i < files.length; i++) {
                    dt.items.add(files[i]);
                }
                batchResumeFiles.files = dt.files;
                console.log('批量拖拽设置完成，文件数量:', batchResumeFiles.files.length);
                displaySelectedFiles(files);
            }
        }
    }

    function setupFileInputs() {
        console.log('开始设置文件输入框事件监听器');
        
        // 使用延迟重试机制
        function trySetupFileInputs(attempts = 0) {
            const resumeFile = document.getElementById('resumeFile');
            console.log(`尝试第${attempts + 1}次，resumeFile元素:`, resumeFile);
            
            if (!resumeFile) {
                if (attempts < 5) {
                    console.log(`第${attempts + 1}次未找到文件输入框，将在500ms后重试`);
                    setTimeout(() => trySetupFileInputs(attempts + 1), 500);
                    return;
                } else {
                    console.error('文件输入框未找到，DOM元素列表:');
                    console.log('所有input元素:', document.querySelectorAll('input'));
                    console.log('所有带id的元素:', document.querySelectorAll('[id]'));
                    console.log('完整HTML内容长度:', document.documentElement.innerHTML.length);
                    return;
                }
            }
            
            console.log('单个文件输入框找到，设置事件监听器');
            resumeFile.addEventListener('change', function(e) {
                console.log('文件选择发生变化:', e.target.files);
                if (e.target.files.length > 0) {
                    displaySelectedFile(e.target.files[0]);
                }
            });

            // 设置批量文件输入框
            const batchResumeFiles = document.getElementById('batchResumeFiles');
            console.log('批量文件输入框:', batchResumeFiles);
            
            if (batchResumeFiles) {
                console.log('批量文件输入框找到，设置事件监听器');
                batchResumeFiles.addEventListener('change', function(e) {
                    console.log('批量文件选择发生变化:', e.target.files, '文件数量:', e.target.files.length);
                    displaySelectedFiles(e.target.files);
                });
            } else {
                console.warn('批量文件输入框未找到，将在重试时再次检查');
                // 延迟重试批量文件输入框
                setTimeout(() => {
                    const batchInput = document.getElementById('batchResumeFiles');
                    if (batchInput) {
                        console.log('延迟重试找到批量文件输入框');
                        batchInput.addEventListener('change', function(e) {
                            console.log('批量文件选择发生变化:', e.target.files, '文件数量:', e.target.files.length);
                            displaySelectedFiles(e.target.files);
                        });
                    }
                }, 1000);
            }
        }
        
        trySetupFileInputs();
    }

    function displaySelectedFile(file) {
        const uploadArea = document.getElementById('uploadArea');
        
        // 保存原有的文件输入框
        const existingFileInput = document.getElementById('resumeFile');
        
        uploadArea.innerHTML = `
            <div class="upload-icon text-success">
                <i class="fas fa-check-circle"></i>
            </div>
            <h6 class="text-success">文件已选择</h6>
            <p class="text-muted">${file.name}</p>
            <small class="text-muted">${formatFileSize(file.size)}</small>
            <button type="button" class="btn btn-outline-primary btn-sm mt-2" onclick="document.getElementById('resumeFile').click()">
                <i class="fas fa-edit me-1"></i>重新选择
            </button>
        `;
        
        // 重新添加文件输入框（如果不存在的话）
        if (!document.getElementById('resumeFile')) {
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.id = 'resumeFile';
            fileInput.name = 'file';
            fileInput.accept = '.pdf,.docx,.doc,.md,.txt';
            fileInput.style.display = 'none';
            
            // 重新添加change事件监听器
            fileInput.addEventListener('change', function(e) {
                console.log('文件选择发生变化:', e.target.files);
                if (e.target.files.length > 0) {
                    displaySelectedFile(e.target.files[0]);
                }
            });
            
            uploadArea.appendChild(fileInput);
        }
        
        // 如果有现有文件输入框且有文件，保持文件选择状态
        if (existingFileInput && existingFileInput.files.length > 0) {
            const newFileInput = document.getElementById('resumeFile');
            if (newFileInput) {
                // 创建新的文件列表
                const dt = new DataTransfer();
                for (let i = 0; i < existingFileInput.files.length; i++) {
                    dt.items.add(existingFileInput.files[i]);
                }
                newFileInput.files = dt.files;
            }
        }
    }

    function displaySelectedFiles(files) {
        const fileList = document.getElementById('fileList');
        const batchUploadArea = document.getElementById('batchUploadArea');
        
        console.log('displaySelectedFiles调用，文件数量:', files.length);
        
        if (!fileList) {
            console.error('fileList元素未找到');
            return;
        }
        
        if (files.length === 0) {
            fileList.innerHTML = '<span class="text-muted">暂无文件</span>';
            // 恢复原始上传区域
            if (batchUploadArea) {
                batchUploadArea.innerHTML = `
                    <div class="upload-icon">
                        <i class="fas fa-files"></i>
                    </div>
                    <h5>批量上传简历文件</h5>
                    <p class="text-muted">可同时选择多个文件</p>
                    <input type="file" id="batchResumeFiles" name="files" multiple accept=".pdf,.docx,.doc,.md,.txt" style="display: none;">
                    <button type="button" class="btn btn-primary" onclick="document.getElementById('batchResumeFiles').click()">
                        <i class="fas fa-folder-open me-2"></i>选择多个文件
                    </button>
                `;
                
                // 重新设置事件监听器
                const newBatchInput = document.getElementById('batchResumeFiles');
                if (newBatchInput) {
                    newBatchInput.addEventListener('change', function(e) {
                        console.log('重新绑定的批量文件选择事件:', e.target.files.length);
                        displaySelectedFiles(e.target.files);
                    });
                }
            }
            return;
        }

        let html = '';
        for (let i = 0; i < files.length; i++) {
            html += `
                <div class="batch-upload-item">
                    <i class="fas fa-file me-2"></i>
                    <strong>${files[i].name}</strong>
                    <small class="text-muted ms-2">(${formatFileSize(files[i].size)})</small>
                </div>
            `;
        }
        fileList.innerHTML = html;
        
        // 更新批量上传区域显示，但保持原始input元素
        if (batchUploadArea) {
            // 检查是否已经有input元素
            let existingInput = document.getElementById('batchResumeFiles');
            let preservedFiles = null;
            
            if (existingInput && existingInput.files.length > 0) {
                preservedFiles = existingInput.files;
                console.log('保存现有文件:', preservedFiles.length);
            }
            
            batchUploadArea.innerHTML = `
                <div class="upload-icon text-success">
                    <i class="fas fa-check-circle"></i>
                </div>
                <h6 class="text-success">已选择 ${files.length} 个文件</h6>
                <p class="text-muted">点击下方按钮重新选择</p>
                <input type="file" id="batchResumeFiles" name="files" multiple accept=".pdf,.docx,.doc,.md,.txt" style="display: none;">
                <button type="button" class="btn btn-outline-primary btn-sm" onclick="document.getElementById('batchResumeFiles').click()">
                    <i class="fas fa-edit me-1"></i>重新选择文件
                </button>
            `;
            
            // 重新获取新创建的input元素并设置文件
            const newBatchInput = document.getElementById('batchResumeFiles');
            if (newBatchInput) {
                console.log('重新创建批量文件输入框，multiple属性:', newBatchInput.multiple);
                
                // 恢复文件列表
                const dt = new DataTransfer();
                const filesToRestore = preservedFiles || files;
                for (let i = 0; i < filesToRestore.length; i++) {
                    dt.items.add(filesToRestore[i]);
                }
                newBatchInput.files = dt.files;
                
                console.log('文件恢复完成，当前文件数量:', newBatchInput.files.length);
                
                // 重新添加事件监听器
                newBatchInput.addEventListener('change', function(e) {
                    console.log('批量文件选择发生变化:', e.target.files.length);
                    displaySelectedFiles(e.target.files);
                });
            }
        }
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function setupForms() {
        console.log('开始设置表单事件监听器');
        
        const singleAnalysisForm = document.getElementById('singleAnalysisForm');
        const batchAnalysisForm = document.getElementById('batchAnalysisForm');
        const urlAnalysisForm = document.getElementById('urlAnalysisForm');
        
        console.log('表单元素检查:', {
            singleAnalysisForm: !!singleAnalysisForm,
            batchAnalysisForm: !!batchAnalysisForm,
            urlAnalysisForm: !!urlAnalysisForm
        });
        
        if (singleAnalysisForm) {
            singleAnalysisForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                await handleSingleAnalysis();
            });
        } else {
            console.error('单个分析表单未找到');
        }

        if (batchAnalysisForm) {
            batchAnalysisForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                await handleBatchAnalysis();
            });
        } else {
            console.error('批量分析表单未找到');
        }

        if (urlAnalysisForm) {
            urlAnalysisForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                await handleUrlAnalysis();
            });
        } else {
            console.error('URL分析表单未找到');
        }
    }

    async function handleSingleAnalysis() {
        console.log('开始单个简历分析');
        
        const singleAnalysisForm = document.getElementById('singleAnalysisForm');
        if (!singleAnalysisForm) {
            showError('无法找到分析表单，请刷新页面重试');
            return;
        }
        
        // 增强的文件输入框检查，包含重试机制
        function checkFileInput(attempts = 0) {
            const fileInput = document.getElementById('resumeFile');
            console.log(`检查文件输入框，尝试第${attempts + 1}次:`, fileInput);
            
            if (!fileInput) {
                if (attempts < 3) {
                    console.log(`第${attempts + 1}次未找到，将在300ms后重试`);
                    return new Promise(resolve => {
                        setTimeout(() => resolve(checkFileInput(attempts + 1)), 300);
                    });
                } else {
                    showError('无法找到文件输入框，请刷新页面重试');
                    console.error('多次尝试后仍未找到文件输入框');
                    console.log('当前页面所有input元素:', document.querySelectorAll('input'));
                    return null;
                }
            }
            
            return fileInput;
        }
        
        const fileInput = await checkFileInput();
        if (!fileInput) {
            return;
        }
        
        if (!fileInput.files || fileInput.files.length === 0) {
            showError('请选择简历文件');
            return;
        }
        
        console.log('选择的文件:', fileInput.files[0]);
        
        const formData = new FormData(singleAnalysisForm);
        console.log('表单数据:', formData.get('file'), formData.get('job_title'), formData.get('job_description'));

        showLoading();
        
        try {
            const response = await fetch(`${API_BASE_URL}/upload/file`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (response.ok) {
                displaySingleResult(result);
            } else {
                showError(result.detail || '分析失败');
            }
        } catch (error) {
            showError('网络错误，请检查后端服务是否启动');
        } finally {
            hideLoading();
        }
    }

    async function handleBatchAnalysis() {
        console.log('开始批量简历分析');
        
        const batchAnalysisForm = document.getElementById('batchAnalysisForm');
        if (!batchAnalysisForm) {
            showError('无法找到批量分析表单，请刷新页面重试');
            return;
        }
        
        // 检查文件输入框
        function checkBatchFileInput(attempts = 0) {
            const batchFileInput = document.getElementById('batchResumeFiles');
            console.log(`检查批量文件输入框，尝试第${attempts + 1}次:`, batchFileInput);
            
            if (!batchFileInput) {
                if (attempts < 3) {
                    console.log(`第${attempts + 1}次未找到批量文件输入框，将在300ms后重试`);
                    return new Promise(resolve => {
                        setTimeout(() => resolve(checkBatchFileInput(attempts + 1)), 300);
                    });
                } else {
                    showError('无法找到批量文件输入框，请刷新页面重试');
                    console.error('多次尝试后仍未找到批量文件输入框');
                    return null;
                }
            }
            
            return batchFileInput;
        }
        
        const batchFileInput = await checkBatchFileInput();
        if (!batchFileInput) {
            return;
        }
        
        const files = batchFileInput.files;
        console.log('批量分析文件检查:', {
            fileInput: batchFileInput,
            multiple: batchFileInput.multiple,
            filesLength: files.length,
            files: Array.from(files).map(f => ({ name: f.name, size: f.size, type: f.type }))
        });
        
        if (!files || files.length === 0) {
            showError('请选择至少一个简历文件');
            return;
        }

        // 手动构建FormData，不依赖表单的自动构建
        const formData = new FormData();
        
        // 添加表单字段
        const jobTitle = document.getElementById('batchJobTitle').value;
        const jobDescription = document.getElementById('batchJobDescription').value;
        
        if (!jobTitle || !jobDescription) {
            showError('请填写完整的岗位信息');
            return;
        }
        
        formData.append('job_title', jobTitle);
        formData.append('job_description', jobDescription);
        
        // 逐个添加文件，使用相同的字段名
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
            console.log(`添加文件 ${i + 1}: ${files[i].name} (${files[i].size} bytes)`);
        }
        
        // 验证FormData内容
        console.log('批量分析FormData内容:', {
            job_title: formData.get('job_title'),
            job_description: formData.get('job_description'),
            files_count: formData.getAll('files').length,
            files_details: formData.getAll('files').map(f => ({ name: f.name, size: f.size }))
        });

        showLoading();
        
        try {
            console.log('发送批量分析请求到:', `${API_BASE_URL}/analyze/batch`);
            
            const response = await fetch(`${API_BASE_URL}/analyze/batch`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            console.log('批量分析响应:', result);
            
            if (response.ok) {
                displayBatchResults(result);
            } else {
                console.error('批量分析失败:', result);
                showError(result.detail || '批量分析失败');
            }
        } catch (error) {
            console.error('批量分析网络错误:', error);
            showError('网络错误，请检查后端服务是否启动');
        } finally {
            hideLoading();
        }
    }

    async function handleUrlAnalysis() {
        const urlAnalysisForm = document.getElementById('urlAnalysisForm');
        const formData = new FormData(urlAnalysisForm);
        
        showLoading();
        
        try {
            const response = await fetch(`${API_BASE_URL}/upload/url`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (response.ok) {
                displayUrlResult(result);
            } else {
                showError(result.detail || '网页分析失败');
            }
        } catch (error) {
            showError('网络错误，请检查后端服务是否启动');
        } finally {
            hideLoading();
        }
    }

    function displaySingleResult(result) {
        const singleResults = document.getElementById('singleResults');
        const matchScore = result.match_result.overall_match_score;
        const scoreClass = getScoreClass(matchScore);
        
        singleResults.innerHTML = `
            <div class="text-center mb-4">
                <div class="score-circle ${scoreClass}">
                    ${Math.round(matchScore * 100)}%
                </div>
                <h5 class="mt-3">整体匹配度</h5>
            </div>
            
            <div class="analysis-section">
                <h6><i class="fas fa-cogs me-2"></i>技能匹配分析</h6>
                <div class="row">
                    <div class="col-6">
                        <small class="text-muted">匹配率</small>
                        <div class="fw-bold">${Math.round(result.match_result.skill_match.match_rate * 100)}%</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">匹配技能</small>
                        <div class="fw-bold">${result.match_result.skill_match.matched_skills.length}</div>
                    </div>
                </div>
                <div class="mt-2">
                    <small class="text-muted d-block">匹配的技能：</small>
                    ${result.match_result.skill_match.matched_skills.slice(0, 5).map(skill => 
                        `<span class="skill-tag">${skill}</span>`
                    ).join('')}
                </div>
                ${result.match_result.skill_match.missing_skills.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted d-block">建议学习：</small>
                        ${result.match_result.skill_match.missing_skills.slice(0, 3).map(skill => 
                            `<span class="skill-tag missing-skill-tag">${skill}</span>`
                        ).join('')}
                    </div>
                ` : ''}
            </div>
            
            <div class="analysis-section">
                <h6><i class="fas fa-briefcase me-2"></i>工作经验匹配</h6>
                <div class="progress mb-2">
                    <div class="progress-bar" style="width: ${result.match_result.experience_match.match_score * 100}%"></div>
                </div>
                <small class="text-muted">匹配度: ${Math.round(result.match_result.experience_match.match_score * 100)}%</small>
            </div>
            
            <div class="analysis-section">
                <h6><i class="fas fa-graduation-cap me-2"></i>教育背景匹配</h6>
                <div class="progress mb-2">
                    <div class="progress-bar" style="width: ${result.match_result.education_match.match_score * 100}%"></div>
                </div>
                <small class="text-muted">匹配度: ${Math.round(result.match_result.education_match.match_score * 100)}%</small>
            </div>
            
            <div class="analysis-section">
                <h6><i class="fas fa-robot me-2"></i>AI综合评估</h6>
                <div class="row">
                    <div class="col-6">
                        <small class="text-muted">技术技能</small>
                        <div class="fw-bold">${Math.round(result.match_result.ai_assessment.technical_skills * 100)}%</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">学习潜力</small>
                        <div class="fw-bold">${Math.round(result.match_result.ai_assessment.learning_potential * 100)}%</div>
                    </div>
                </div>
                ${result.match_result.ai_assessment.summary ? `
                    <div class="mt-2">
                        <small class="text-muted d-block">AI评估总结：</small>
                        <p class="small">${result.match_result.ai_assessment.summary}</p>
                    </div>
                ` : ''}
            </div>
            
            ${result.match_result.recommendations.length > 0 ? `
                <div class="analysis-section">
                    <h6><i class="fas fa-lightbulb me-2"></i>改进建议</h6>
                    <ul class="list-unstyled">
                        ${result.match_result.recommendations.map(rec => 
                            `<li class="small"><i class="fas fa-arrow-right me-2 text-primary"></i>${rec}</li>`
                        ).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
    }

    function displayBatchResults(result) {
        const batchResults = document.getElementById('batchResults');
        let html = `
            <div class="result-card">
                <div class="card-header bg-info text-white">
                    <h5 class="mb-0">批量分析结果</h5>
                    <small>共处理 ${result.total_files} 个文件</small>
                </div>
                <div class="card-body">
        `;
        
        const sortedResults = result.results
            .filter(r => r.status === 'success')
            .sort((a, b) => b.match_result.overall_match_score - a.match_result.overall_match_score);
        
        sortedResults.forEach((item, index) => {
            const score = item.match_result.overall_match_score;
            const scoreClass = getScoreClass(score);
            
            html += `
                <div class="row align-items-center mb-3 p-3 border rounded">
                    <div class="col-md-3">
                        <h6 class="mb-1">${item.filename}</h6>
                        <small class="text-muted">排名 #${index + 1}</small>
                    </div>
                    <div class="col-md-2 text-center">
                        <div class="score-circle ${scoreClass}" style="width: 60px; height: 60px; font-size: 1rem;">
                            ${Math.round(score * 100)}%
                        </div>
                    </div>
                    <div class="col-md-7">
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">技能匹配</small>
                                <div class="progress progress-sm">
                                    <div class="progress-bar" style="width: ${item.match_result.skill_match.match_rate * 100}%"></div>
                                </div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">经验匹配</small>
                                <div class="progress progress-sm">
                                    <div class="progress-bar" style="width: ${item.match_result.experience_match.match_score * 100}%"></div>
                                </div>
                            </div>
                        </div>
                        <div class="mt-2">
                            ${item.match_result.skill_match.matched_skills.slice(0, 3).map(skill => 
                                `<span class="skill-tag" style="font-size: 0.7rem;">${skill}</span>`
                            ).join('')}
                        </div>
                    </div>
                </div>
            `;
        });
        
        const failedResults = result.results.filter(r => r.status === 'error');
        if (failedResults.length > 0) {
            html += `
                <div class="mt-4">
                    <h6 class="text-danger">处理失败的文件：</h6>
                    ${failedResults.map(item => 
                        `<div class="alert alert-danger py-2">
                            <strong>${item.filename}</strong>: ${item.error}
                        </div>`
                    ).join('')}
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
        
        batchResults.innerHTML = html;
    }

    function displayUrlResult(result) {
        const urlResults = document.getElementById('urlResults');
        urlResults.innerHTML = `
            <div class="result-card">
                <div class="card-header bg-warning text-dark">
                    <h5 class="mb-0">网页简历分析结果</h5>
                    <small>${result.url_info.url}</small>
                </div>
                <div class="card-body">
                    ${generateDetailedResult(result)}
                </div>
            </div>
        `;
    }

    function generateDetailedResult(result) {
        const matchScore = result.match_result.overall_match_score;
        const scoreClass = getScoreClass(matchScore);
        
        return `
            <div class="row">
                <div class="col-md-4 text-center">
                    <div class="score-circle ${scoreClass}">
                        ${Math.round(matchScore * 100)}%
                    </div>
                    <h6 class="mt-3">综合匹配度</h6>
                </div>
                <div class="col-md-8">
                    <div class="row mb-3">
                        <div class="col-6">
                            <h6>技能匹配</h6>
                            <div class="progress">
                                <div class="progress-bar" style="width: ${result.match_result.skill_match.match_rate * 100}%"></div>
                            </div>
                            <small>${Math.round(result.match_result.skill_match.match_rate * 100)}%</small>
                        </div>
                        <div class="col-6">
                            <h6>经验匹配</h6>
                            <div class="progress">
                                <div class="progress-bar" style="width: ${result.match_result.experience_match.match_score * 100}%"></div>
                            </div>
                            <small>${Math.round(result.match_result.experience_match.match_score * 100)}%</small>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-6">
                            <h6>文本相似度</h6>
                            <div class="progress">
                                <div class="progress-bar" style="width: ${result.match_result.tfidf_similarity * 100}%"></div>
                            </div>
                            <small>${Math.round(result.match_result.tfidf_similarity * 100)}%</small>
                        </div>
                        <div class="col-6">
                            <h6>主题相似度</h6>
                            <div class="progress">
                                <div class="progress-bar" style="width: ${result.match_result.topic_similarity * 100}%"></div>
                            </div>
                            <small>${Math.round(result.match_result.topic_similarity * 100)}%</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <hr>
            
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="fas fa-check-circle text-success me-2"></i>匹配技能</h6>
                    <div class="mb-3">
                        ${result.match_result.skill_match.matched_skills.slice(0, 8).map(skill => 
                            `<span class="skill-tag">${skill}</span>`
                        ).join('')}
                    </div>
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-plus-circle text-warning me-2"></i>建议技能</h6>
                    <div class="mb-3">
                        ${result.match_result.skill_match.missing_skills.slice(0, 5).map(skill => 
                            `<span class="skill-tag missing-skill-tag">${skill}</span>`
                        ).join('')}
                    </div>
                </div>
            </div>
            
            ${result.match_result.recommendations.length > 0 ? `
                <div class="mt-3">
                    <h6><i class="fas fa-lightbulb text-info me-2"></i>改进建议</h6>
                    <ul class="list-unstyled">
                        ${result.match_result.recommendations.map(rec => 
                            `<li class="mb-1"><i class="fas fa-arrow-right me-2 text-primary"></i>${rec}</li>`
                        ).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
    }

    function getScoreClass(score) {
        if (score >= 0.8) return 'score-excellent';
        if (score >= 0.6) return 'score-good';
        if (score >= 0.4) return 'score-average';
        return 'score-poor';
    }

    function showLoading() {
        const loadingSpinner = document.getElementById('loadingSpinner');
        loadingSpinner.style.display = 'block';
    }

    function hideLoading() {
        const loadingSpinner = document.getElementById('loadingSpinner');
        loadingSpinner.style.display = 'none';
    }

    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
        `;
        
        document.querySelector('.main-container').appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    function showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            ${message}
        `;
        
        document.querySelector('.main-container').appendChild(successDiv);
        
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }

    // 初始化
    console.log('页面加载完成，开始初始化');
    console.log('当前页面所有元素数量:', document.querySelectorAll('*').length);
    
    setupDragAndDrop();
    setupFileInputs();
    setupForms();

    // 检查API连接
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            showSuccess('系统已就绪，可以开始分析');
        }
    } catch (error) {
        showError('无法连接到后端服务，请确保服务已启动');
    }
});
