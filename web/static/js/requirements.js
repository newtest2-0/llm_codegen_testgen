/**
 * 需求管理模块
 *
 * 功能：
 * 1. 管理5个需求文档章节（详细需求、架构设计、详细设计、两个追溯）
 * 2. LLMs评阅（复用系统已有的LLM配置）
 * 3. 专家评阅（用户手动填写）
 * 4. 文档上传/下载
 * 5. 日志记录（预留接口）
 */

const RequirementsManager = {
    // 当前文档ID
    currentDocId: null,

    // 章节类型配置
    sections: [
        {
            id: 'detailed_requirement',
            title: '详细需求描述',
            icon: 'fa-file-alt',
            color: 'blue',
            placeholder: '请详细描述项目需求，包括功能点、业务流程、用户场景等...'
        },
        {
            id: 'architecture_design',
            title: '架构设计',
            icon: 'fa-sitemap',
            color: 'green',
            placeholder: '请描述系统架构设计，包括技术栈、模块划分、数据流等...'
        },
        {
            id: 'detailed_design',
            title: '详细设计（含接口+参数+返回值）',
            icon: 'fa-code',
            color: 'purple',
            placeholder: '请详细设计API接口，包括接口路径、请求参数、返回值等...'
        },
        {
            id: 'requirement_architecture_trace',
            title: '需求 → 架构 追溯',
            icon: 'fa-project-diagram',
            color: 'orange',
            placeholder: '请建立需求到架构的追溯关系，确保架构设计覆盖所有需求...'
        },
        {
            id: 'requirement_design_trace',
            title: '需求 → 详细设计 追溯',
            icon: 'fa-link',
            color: 'red',
            placeholder: '请建立需求到详细设计的追溯关系，确保详细设计覆盖所有需求...'
        }
    ],

    /**
     * 初始化需求管理模块
     */
    init: async function() {
        console.log('🚀 初始化需求管理模块...');

        // 创建新文档或加载现有文档（必须等待完成）
        await this.createOrLoadDocument();

        // 渲染所有章节
        this.renderAllSections();

        console.log('✅ 需求管理模块初始化完成，文档ID:', this.currentDocId);
    },

    /**
     * 创建或加载文档
     */
    createOrLoadDocument: async function() {
        // 检查本地存储是否有文档ID
        const savedDocId = localStorage.getItem('requirements_doc_id');

        if (savedDocId) {
            // 验证文档是否存在
            try {
                const response = await fetch(`${API_BASE}/api/v1/requirements/documents/${savedDocId}`);

                if (response.ok) {
                    this.currentDocId = savedDocId;
                    console.log('📄 加载已有文档:', savedDocId);
                    return;
                } else {
                    console.log('⚠️  文档不存在，将创建新文档');
                    localStorage.removeItem('requirements_doc_id');
                }
            } catch (error) {
                console.log('⚠️  验证文档失败，将创建新文档:', error);
                localStorage.removeItem('requirements_doc_id');
            }
        }

        // 创建新文档
        try {
            const response = await fetch(`${API_BASE}/api/v1/requirements/documents`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_name: 'Professional Code Development Platform 项目',
                    sections: {}
                })
            });

            if (!response.ok) {
                throw new Error('创建文档失败');
            }

            const doc = await response.json();
            this.currentDocId = doc.doc_id;
            localStorage.setItem('requirements_doc_id', doc.doc_id);

            console.log('✅ 新文档创建成功:', this.currentDocId);
        } catch (error) {
            console.error('❌ 创建文档失败:', error);
        }
    },

    /**
     * 渲染所有章节
     */
    renderAllSections: function() {
        const container = document.getElementById('requirementsSectionsContainer');

        if (!container) {
            console.error('❌ 找不到需求章节容器');
            return;
        }

        // 清空容器
        container.innerHTML = '';

        // 渲染每个章节
        this.sections.forEach(section => {
            const sectionHtml = this.createSectionCard(section);
            container.insertAdjacentHTML('beforeend', sectionHtml);
        });

        // 绑定事件
        this.bindSectionEvents();
    },

    /**
     * 创建章节卡片HTML
     */
    createSectionCard: function(section) {
        return `
            <div class="surface-card rounded-xl p-6 mb-6" id="section-${section.id}">
                <!-- 章节标题 -->
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-${section.color}-100 rounded-lg flex items-center justify-center">
                            <i class="fas ${section.icon} text-${section.color}-600"></i>
                        </div>
                        <h3 class="text-lg font-semibold text-gray-900">${section.title}</h3>
                    </div>
                    <span class="text-sm text-gray-500" id="status-${section.id}">未编辑</span>
                </div>

                <!-- 内容编辑区 -->
                <div class="mb-4">
                    <textarea
                        id="content-${section.id}"
                        class="w-full h-48 p-4 border border-gray-300 rounded-lg resize-y focus:ring-2 focus:ring-${section.color}-500 focus:border-${section.color}-500"
                        placeholder="${section.placeholder}"
                    ></textarea>
                </div>

                <!-- LLM评阅区域 -->
                <div id="llm-review-${section.id}" class="mb-4 hidden">
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div class="flex items-center gap-2 mb-2">
                            <i class="fas fa-robot text-blue-600"></i>
                            <span class="font-medium text-blue-900">LLM评阅</span>
                        </div>
                        <div id="llm-review-content-${section.id}" class="text-sm text-gray-700 whitespace-pre-wrap"></div>
                    </div>
                </div>

                <!-- 专家评阅区域 -->
                <div id="expert-review-${section.id}" class="mb-4 hidden">
                    <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div class="flex items-center gap-2 mb-2">
                            <i class="fas fa-user-check text-green-600"></i>
                            <span class="font-medium text-green-900">专家评阅</span>
                        </div>
                        <textarea
                            id="expert-review-content-${section.id}"
                            class="w-full h-32 p-3 border border-green-300 rounded-lg resize-y focus:ring-2 focus:ring-green-500"
                            placeholder="请输入专家评阅意见..."
                        ></textarea>
                    </div>
                </div>

                <!-- 操作按钮 -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <button
                        class="btn-llm-review px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                        data-section="${section.id}"
                    >
                        <i class="fas fa-robot"></i>
                        <span>LLMs评阅</span>
                    </button>

                    <button
                        class="btn-expert-review px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                        data-section="${section.id}"
                    >
                        <i class="fas fa-user-edit"></i>
                        <span>专家评阅</span>
                    </button>

                    <button
                        class="btn-download px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                        data-section="${section.id}"
                    >
                        <i class="fas fa-download"></i>
                        <span>下载文档</span>
                    </button>

                    <button
                        class="btn-upload px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                        data-section="${section.id}"
                    >
                        <i class="fas fa-upload"></i>
                        <span>上传文档</span>
                    </button>
                </div>

                <!-- 隐藏的文件上传input -->
                <input type="file" id="file-upload-${section.id}" class="hidden" accept=".txt,.md,.doc,.docx">
            </div>
        `;
    },

    /**
     * 绑定章节事件
     */
    bindSectionEvents: function() {
        // LLM评阅按钮
        document.querySelectorAll('.btn-llm-review').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sectionId = btn.getAttribute('data-section');
                this.generateLLMReview(sectionId);
            });
        });

        // 专家评阅按钮
        document.querySelectorAll('.btn-expert-review').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sectionId = btn.getAttribute('data-section');
                this.toggleExpertReview(sectionId);
            });
        });

        // 下载文档按钮
        document.querySelectorAll('.btn-download').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sectionId = btn.getAttribute('data-section');
                this.downloadDocument(sectionId);
            });
        });

        // 上传文档按钮
        document.querySelectorAll('.btn-upload').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sectionId = btn.getAttribute('data-section');
                this.triggerUpload(sectionId);
            });
        });

        // 文件上传input变化事件
        this.sections.forEach(section => {
            const fileInput = document.getElementById(`file-upload-${section.id}`);
            if (fileInput) {
                fileInput.addEventListener('change', (e) => {
                    this.handleFileUpload(section.id, e.target.files[0]);
                });
            }
        });

        // 内容变化时自动保存
        this.sections.forEach(section => {
            const textarea = document.getElementById(`content-${section.id}`);
            if (textarea) {
                textarea.addEventListener('blur', () => {
                    this.saveContent(section.id);
                });
            }
        });
    },

    /**
     * 生成LLM评阅（复用系统已有的LLM配置）
     */
    generateLLMReview: async function(sectionId) {
        const content = document.getElementById(`content-${sectionId}`).value.trim();

        if (!content) {
            showNotification('请先填写内容再进行评阅', 'error');
            return;
        }

        const btn = document.querySelector(`.btn-llm-review[data-section="${sectionId}"]`);
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 评阅中...';
        btn.disabled = true;

        try {
            console.log('🤖 开始LLM评阅:', sectionId);

            // 调用后端API（复用系统已有的provider配置）
            const response = await fetch(`${API_BASE}/api/v1/requirements/documents/${this.currentDocId}/llm-review`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    section_type: sectionId,
                    content: content
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '评阅失败');
            }

            const result = await response.json();

            // 显示评阅结果并渲染Mermaid图表
            const reviewContainer = document.getElementById(`llm-review-${sectionId}`);
            const reviewContent = document.getElementById(`llm-review-content-${sectionId}`);

            reviewContainer.classList.remove('hidden');

            // 使用innerHTML来渲染Markdown和Mermaid
            reviewContent.innerHTML = this.convertMarkdownToHTML(result.llm_review);

            // 渲染Mermaid图表
            await this.renderMermaidCharts(reviewContent);

            showNotification(`LLM评阅完成（使用 ${result.provider}）`, 'success');

            console.log('✅ LLM评阅完成:', result.provider);

        } catch (error) {
            console.error('❌ LLM评阅失败:', error);
            showNotification(`评阅失败: ${error.message}`, 'error');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    },

    /**
     * 切换专家评阅显示
     */
    toggleExpertReview: function(sectionId) {
        const reviewContainer = document.getElementById(`expert-review-${sectionId}`);

        if (reviewContainer.classList.contains('hidden')) {
            reviewContainer.classList.remove('hidden');
        } else {
            // 保存专家评阅
            this.saveExpertReview(sectionId);
        }
    },

    /**
     * 保存专家评阅
     */
    saveExpertReview: async function(sectionId) {
        const expertReview = document.getElementById(`expert-review-content-${sectionId}`).value.trim();

        if (!expertReview) {
            showNotification('请输入专家评阅内容', 'error');
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/api/v1/requirements/documents/${this.currentDocId}/expert-review`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    section_type: sectionId,
                    expert_review: expertReview
                })
            });

            if (!response.ok) {
                throw new Error('保存失败');
            }

            showNotification('专家评阅已保存', 'success');

            // 隐藏编辑区
            document.getElementById(`expert-review-${sectionId}`).classList.add('hidden');

        } catch (error) {
            console.error('❌ 保存专家评阅失败:', error);
            showNotification('保存失败', 'error');
        }
    },

    /**
     * 保存内容
     */
    saveContent: async function(sectionId) {
        const content = document.getElementById(`content-${sectionId}`).value.trim();

        if (!content) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/api/v1/requirements/documents/${this.currentDocId}/sections`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    section_type: sectionId,
                    content: content
                })
            });

            if (!response.ok) {
                throw new Error('保存失败');
            }

            // 更新状态
            document.getElementById(`status-${sectionId}`).textContent = '已保存';

            console.log('✅ 内容已保存:', sectionId);

        } catch (error) {
            console.error('❌ 保存内容失败:', error);
            document.getElementById(`status-${sectionId}`).textContent = '保存失败';
        }
    },

    /**
     * 下载文档
     */
    downloadDocument: async function(sectionId) {
        try {
            // 先保存当前内容
            await this.saveContent(sectionId);

            // 下载文档
            const url = `${API_BASE}/api/v1/requirements/documents/${this.currentDocId}/download/${sectionId}`;

            // 创建临时a标签触发下载
            const a = document.createElement('a');
            a.href = url;
            a.download = `${sectionId}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            showNotification('文档下载成功', 'success');

        } catch (error) {
            console.error('❌ 下载文档失败:', error);
            showNotification('下载失败', 'error');
        }
    },

    /**
     * 触发文件上传
     */
    triggerUpload: function(sectionId) {
        const fileInput = document.getElementById(`file-upload-${sectionId}`);
        fileInput.click();
    },

    /**
     * 处理文件上传
     */
    handleFileUpload: async function(sectionId, file) {
        if (!file) {
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE}/api/v1/requirements/documents/${this.currentDocId}/upload/${sectionId}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('上传失败');
            }

            const result = await response.json();

            // 读取上传的文件内容（从服务器返回）
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById(`content-${sectionId}`).value = e.target.result;
                document.getElementById(`status-${sectionId}`).textContent = '已上传';
            };
            reader.readAsText(file);

            showNotification('文档上传成功', 'success');

        } catch (error) {
            console.error('❌ 上传文档失败:', error);
            showNotification('上传失败', 'error');
        }
    },

    /**
     * 将Markdown转换为HTML（简单实现）
     */
    convertMarkdownToHTML: function(markdown) {
        let html = markdown;

        // 转换标题
        html = html.replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>');
        html = html.replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold mt-6 mb-3">$1</h2>');
        html = html.replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold mt-8 mb-4">$1</h1>');

        // 转换代码块（保留Mermaid）
        html = html.replace(/```mermaid\n([\s\S]*?)```/g, function(_match, code) {
            const id = 'mermaid-' + Math.random().toString(36).substring(2, 11);
            return `<div class="mermaid-chart my-4 p-4 bg-white border border-gray-200 rounded-lg" id="${id}">${code.trim()}</div>`;
        });

        // 转换其他代码块
        html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="bg-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code>$2</code></pre>');

        // 转换行内代码
        html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-2 py-1 rounded text-sm">$1</code>');

        // 转换粗体
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // 转换列表
        html = html.replace(/^\d+\. (.*$)/gm, '<li class="ml-6 my-1">$1</li>');
        html = html.replace(/^- (.*$)/gm, '<li class="ml-6 my-1">$1</li>');

        // 转换段落（换行）
        html = html.replace(/\n\n/g, '<br><br>');

        return html;
    },

    /**
     * 渲染Mermaid图表
     */
    renderMermaidCharts: async function(container) {
        try {
            if (typeof window.mermaid === 'undefined') {
                console.warn('Mermaid未加载');
                return;
            }

            // 查找所有Mermaid图表容器
            const charts = container.querySelectorAll('.mermaid-chart');

            for (const chart of charts) {
                const code = chart.textContent;
                const id = chart.id;

                try {
                    // 使用Mermaid渲染图表
                    const { svg } = await window.mermaid.render(id + '-svg', code);
                    chart.innerHTML = svg;
                    console.log('✅ Mermaid图表渲染成功:', id);
                } catch (error) {
                    console.error('❌ Mermaid渲染失败:', error);
                    chart.innerHTML = `<div class="text-red-600 text-sm">图表渲染失败: ${error.message}</div>`;
                }
            }
        } catch (error) {
            console.error('❌ renderMermaidCharts错误:', error);
        }
    }
};

// 全局函数：显示通知
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    const bgColor = type === 'error' ? 'bg-red-500' : 'bg-green-500';
    const icon = type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle';

    notification.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transform transition-transform duration-300`;
    notification.innerHTML = `
        <div class="flex items-center gap-2">
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.transform = 'translateX(500px)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}
