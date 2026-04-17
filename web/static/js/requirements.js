/**
 * 需求管理模块
 *
 * 功能：
 * 1. 管理5个需求文档章节（详细需求、架构设计、详细设计、两个追溯）
 * 2. LLMs评阅（复用系统已有的LLM配置）
 * 3. 专家评阅（用户手动填写）
 * 4. 文档上传/下载（含本地图片上传 + 网络图片直接渲染）
 * 5. 日志记录（预留接口）
 */

/**
 * 动态加载并初始化 Mermaid 库
 * @returns {Promise<typeof window.mermaid>}
 */
function loadMermaid() {
    return new Promise((resolve, reject) => {
        if (window.mermaid) {
            resolve(window.mermaid);
            return;
        }
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
        script.onload = () => {
            window.mermaid.initialize({
                startOnLoad: false,
                theme: 'default',
                securityLevel: 'loose',
                sequence: { showSequenceNumbers: false }
            });
            window.dispatchEvent(new Event('mermaid-ready'));
            resolve(window.mermaid);
        };
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

const RequirementsManager = {
    currentDocId: null,

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

    init: async function() {
        console.log('🚀 初始化需求管理模块...');
        await this.createOrLoadDocument();
        this.renderAllSections();
        console.log('✅ 需求管理模块初始化完成，文档ID:', this.currentDocId);
    },

    createOrLoadDocument: async function() {
        const savedDocId = localStorage.getItem('requirements_doc_id');
        if (savedDocId) {
            try {
                const response = await fetch(`${API_BASE}/api/v1/requirements/documents/${savedDocId}`);
                if (response.ok) {
                    this.currentDocId = savedDocId;
                    return;
                }
                localStorage.removeItem('requirements_doc_id');
            } catch (error) {
                localStorage.removeItem('requirements_doc_id');
            }
        }
        try {
            const response = await fetch(`${API_BASE}/api/v1/requirements/documents`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_name: 'Professional Code Development Platform 项目', sections: {} })
            });
            if (!response.ok) throw new Error('创建文档失败');
            const doc = await response.json();
            this.currentDocId = doc.doc_id;
            localStorage.setItem('requirements_doc_id', doc.doc_id);
        } catch (error) {
            console.error('❌ 创建文档失败:', error);
        }
    },

    renderAllSections: function() {
        const container = document.getElementById('requirementsSectionsContainer');
        if (!container) { console.error('❌ 找不到需求章节容器'); return; }
        container.innerHTML = '';
        this.sections.forEach(section => {
            container.insertAdjacentHTML('beforeend', this.createSectionCard(section));
        });
        this.bindSectionEvents();
    },

    createSectionCard: function(section) {
        return `
            <div class="surface-card rounded-xl p-6 mb-6" id="section-${section.id}">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-${section.color}-100 rounded-lg flex items-center justify-center">
                            <i class="fas ${section.icon} text-${section.color}-600"></i>
                        </div>
                        <h3 class="text-lg font-semibold text-gray-900">${section.title}</h3>
                    </div>
                    <span class="text-sm text-gray-500" id="status-${section.id}">未编辑</span>
                </div>

                <!-- 编辑/预览切换标签 -->
                <div class="flex gap-2 mb-3">
                    <button class="btn-tab-edit px-3 py-1 text-sm rounded-lg bg-${section.color}-600 text-white font-medium"
                        data-section="${section.id}" onclick="RequirementsManager.switchTab('${section.id}','edit')">编辑</button>
                    <button class="btn-tab-preview px-3 py-1 text-sm rounded-lg bg-gray-100 text-gray-600 font-medium"
                        data-section="${section.id}" onclick="RequirementsManager.switchTab('${section.id}','preview')">预览</button>
                </div>

                <!-- 编辑区 -->
                <div id="edit-panel-${section.id}" class="mb-4">
                    <textarea
                        id="content-${section.id}"
                        class="w-full h-48 p-4 border border-gray-300 rounded-lg resize-y focus:ring-2 focus:ring-${section.color}-500 focus:border-${section.color}-500"
                        placeholder="${section.placeholder}"
                    ></textarea>
                </div>

                <!-- Markdown预览区（含图片渲染） -->
                <div id="preview-panel-${section.id}" class="hidden mb-4">
                    <div id="preview-content-${section.id}"
                        class="prose max-w-none p-4 border border-gray-200 rounded-lg bg-white min-h-[12rem] markdown-preview">
                        <p class="text-gray-400 text-sm">（暂无内容，请先在编辑区填写或上传 Markdown 文件）</p>
                    </div>
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
                    <button class="btn-llm-review px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                        data-section="${section.id}">
                        <i class="fas fa-robot"></i><span>LLMs评阅</span>
                    </button>
                    <button class="btn-expert-review px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                        data-section="${section.id}">
                        <i class="fas fa-user-edit"></i><span>专家评阅</span>
                    </button>
                    <button class="btn-download px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                        data-section="${section.id}">
                        <i class="fas fa-download"></i><span>下载文档</span>
                    </button>
                    <button class="btn-upload px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                        data-section="${section.id}">
                        <i class="fas fa-upload"></i><span>上传文档</span>
                    </button>
                </div>

                <!-- 拖拽上传区域 -->
                <div id="drop-zone-${section.id}" class="hidden mt-3 border-2 border-dashed border-orange-300 rounded-lg p-6 text-center bg-orange-50 transition-colors"
                    ondragover="RequirementsManager.onDragOver(event,'${section.id}')"
                    ondragleave="RequirementsManager.onDragLeave(event,'${section.id}')"
                    ondrop="RequirementsManager.onDrop(event,'${section.id}')">
                    <i class="fas fa-cloud-upload-alt text-orange-400 text-3xl mb-2"></i>
                    <p class="text-sm text-orange-700 font-medium">拖拽 .md 文件到此处（可同时拖入本地图片）</p>
                    <p class="text-xs text-orange-500 mt-1">或点击下方按钮选择文件（.md 最大 10MB，图片最大 10MB/张）</p>
                    <div class="flex justify-center gap-3 mt-3">
                        <button type="button"
                            class="px-4 py-1.5 bg-orange-500 hover:bg-orange-600 text-white text-sm rounded-lg transition-colors"
                            onclick="document.getElementById('file-upload-${section.id}').click()">
                            选择 .md 文件
                        </button>
                        <button type="button"
                            class="px-4 py-1.5 bg-yellow-500 hover:bg-yellow-600 text-white text-sm rounded-lg transition-colors"
                            onclick="document.getElementById('img-upload-${section.id}').click()">
                            上传本地图片
                        </button>
                    </div>
                    <!-- 已上传图片列表 -->
                    <div id="img-list-${section.id}" class="mt-3 text-left hidden">
                        <p class="text-xs text-orange-700 font-medium mb-1">已上传图片（点击复制Markdown引用）：</p>
                        <ul id="img-list-items-${section.id}" class="text-xs text-orange-600 space-y-1"></ul>
                    </div>
                    <!-- 进度条 -->
                    <div id="upload-progress-${section.id}" class="hidden mt-3">
                        <div class="w-full bg-orange-200 rounded-full h-2">
                            <div id="upload-progress-bar-${section.id}" class="bg-orange-500 h-2 rounded-full transition-all duration-300" style="width:0%"></div>
                        </div>
                        <p id="upload-progress-text-${section.id}" class="text-xs text-orange-600 mt-1">上传中...</p>
                    </div>
                </div>

                <!-- 隐藏的文件上传input -->
                <input type="file" id="file-upload-${section.id}" class="hidden" accept=".md,.markdown">
                <!-- 隐藏的图片上传input（支持多选） -->
                <input type="file" id="img-upload-${section.id}" class="hidden" accept="image/*" multiple>
            </div>
        `;
    },

    /** 切换编辑/预览标签 */
    switchTab: function(sectionId, tab) {
        const editPanel = document.getElementById(`edit-panel-${sectionId}`);
        const previewPanel = document.getElementById(`preview-panel-${sectionId}`);
        const editBtn = document.querySelector(`.btn-tab-edit[data-section="${sectionId}"]`);
        const previewBtn = document.querySelector(`.btn-tab-preview[data-section="${sectionId}"]`);
        const section = this.sections.find(s => s.id === sectionId);
        const color = section ? section.color : 'blue';

        if (tab === 'edit') {
            editPanel.classList.remove('hidden');
            previewPanel.classList.add('hidden');
            editBtn.className = `btn-tab-edit px-3 py-1 text-sm rounded-lg bg-${color}-600 text-white font-medium`;
            previewBtn.className = `btn-tab-preview px-3 py-1 text-sm rounded-lg bg-gray-100 text-gray-600 font-medium`;
        } else {
            editPanel.classList.add('hidden');
            previewPanel.classList.remove('hidden');
            editBtn.className = `btn-tab-edit px-3 py-1 text-sm rounded-lg bg-gray-100 text-gray-600 font-medium`;
            previewBtn.className = `btn-tab-preview px-3 py-1 text-sm rounded-lg bg-${color}-600 text-white font-medium`;
            // 渲染当前编辑区内容
            const content = document.getElementById(`content-${sectionId}`).value;
            this.renderMarkdownPreview(sectionId, content);
        }
    },

    /**
     * 核心：用 marked.js 渲染 Markdown 到预览区
     * 网络图片直接渲染；本地路径图片显示占位提示
     */
    renderMarkdownPreview: async function(sectionId, markdown) {
        const previewEl = document.getElementById(`preview-content-${sectionId}`);
        if (!previewEl) return;

        if (!markdown || !markdown.trim()) {
            previewEl.innerHTML = '<p class="text-gray-400 text-sm">（暂无内容）</p>';
            return;
        }

        // 配置 marked：允许 HTML，开启 GFM
        if (typeof marked !== 'undefined') {
            const renderer = new marked.Renderer();
            renderer.image = function(href, title, text) {
                const titleAttr = title ? ` title="${title}"` : '';
                const altAttr = text || '';
                const isRemote = /^https?:\/\//i.test(href);
                const isUploaded = href && href.startsWith('/uploads/');
                if (isRemote || isUploaded) {
                    return `<img src="${href}" alt="${altAttr}"${titleAttr}
                        style="max-width:100%;height:auto;border-radius:6px;margin:8px 0;"
                        data-img-error="1"
                    >`;
                }
                return `<div style="padding:8px;background:#fef3c7;border:1px solid #f59e0b;border-radius:6px;color:#92400e;font-size:12px;">
                    📎 本地图片 <code>${altAttr || href}</code> — 请使用"上传本地图片"按钮上传后替换路径
                </div>`;
            };
            // mermaid 代码块：输出 .mermaid-chart div，避免 marked 对 >> 做 HTML 转义
            // marked v5+ 传 token 对象 {text, lang}；旧版传 (code, language)
            renderer.code = function(codeOrToken, language) {
                let code, lang;
                if (codeOrToken && typeof codeOrToken === 'object') {
                    code = codeOrToken.text;
                    lang = codeOrToken.lang;
                } else {
                    code = codeOrToken;
                    lang = language;
                }
                if (lang === 'mermaid') {
                    const id = 'mermaid-' + Math.random().toString(36).substring(2, 11);
                    const wrapped = '```mermaid\n' + code + '\n```';
                    const fixed = RequirementsManager.fixMermaidSyntax(wrapped);
                    const cleanCode = fixed.replace(/^```mermaid\r?\n/, '').replace(/\r?\n```$/, '');
                    const escaped = cleanCode.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    return `<div class="mermaid-chart my-4 p-4 bg-white border border-gray-200 rounded-lg" id="${id}" data-code="${encodeURIComponent(cleanCode)}">${escaped}</div>`;
                }
                return false;
            };

            let html = marked.parse(markdown, { renderer, gfm: true, breaks: true });
            // XSS 防护：使用 DOMPurify 消毒，保留 Mermaid 图表所需属性
            if (typeof DOMPurify !== 'undefined') {
                html = DOMPurify.sanitize(html, {
                    ADD_TAGS: ['div'],
                    ADD_ATTR: ['id', 'data-code', 'data-img-error', 'style']
                });
            }
            previewEl.innerHTML = html;
            // 图片加载失败处理（替代被 DOMPurify 移除的 onerror 内联属性）
            previewEl.querySelectorAll('img[data-img-error]').forEach(img => {
                img.addEventListener('error', function() {
                    const div = document.createElement('div');
                    div.style.cssText = 'padding:8px;background:#fef3c7;border:1px solid #f59e0b;border-radius:6px;color:#92400e;font-size:12px;';
                    div.textContent = '⚠️ 图片加载失败：' + (this.getAttribute('alt') || this.getAttribute('src') || '');
                    this.replaceWith(div);
                });
            });

            // 渲染 Mermaid 图表（如果有）
            await this.renderMermaidCharts(previewEl);
        } else {
            // fallback：使用原有简单转换
            previewEl.innerHTML = this.convertMarkdownToHTML(markdown);
            await this.renderMermaidCharts(previewEl);
        }
    },

    bindSectionEvents: function() {
        document.querySelectorAll('.btn-llm-review').forEach(btn => {
            btn.addEventListener('click', () => this.generateLLMReview(btn.getAttribute('data-section')));
        });
        document.querySelectorAll('.btn-expert-review').forEach(btn => {
            btn.addEventListener('click', () => this.toggleExpertReview(btn.getAttribute('data-section')));
        });
        document.querySelectorAll('.btn-download').forEach(btn => {
            btn.addEventListener('click', () => this.downloadDocument(btn.getAttribute('data-section')));
        });
        document.querySelectorAll('.btn-upload').forEach(btn => {
            btn.addEventListener('click', () => this.triggerUpload(btn.getAttribute('data-section')));
        });
        this.sections.forEach(section => {
            const fileInput = document.getElementById(`file-upload-${section.id}`);
            if (fileInput) {
                fileInput.addEventListener('change', (e) => {
                    this.handleFileUpload(section.id, e.target.files[0]);
                    e.target.value = '';
                });
            }
            const imgInput = document.getElementById(`img-upload-${section.id}`);
            if (imgInput) {
                imgInput.addEventListener('change', (e) => {
                    this.handleImageUpload(section.id, Array.from(e.target.files));
                    e.target.value = '';
                });
            }
            const textarea = document.getElementById(`content-${section.id}`);
            if (textarea) {
                textarea.addEventListener('blur', () => this.saveContent(section.id));
            }
        });
    },

    generateLLMReview: async function(sectionId) {
        const content = document.getElementById(`content-${sectionId}`).value.trim();
        if (!content) { showNotification('请先填写内容再进行评阅', 'error'); return; }
        if (!this.currentDocId) {
            showNotification('文档未初始化，请刷新页面重试', 'error');
            return;
        }
        const btn = document.querySelector(`.btn-llm-review[data-section="${sectionId}"]`);
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 评阅中，请稍候...';
        btn.disabled = true;

        // 显示加载占位
        const reviewContainer = document.getElementById(`llm-review-${sectionId}`);
        const reviewContent = document.getElementById(`llm-review-content-${sectionId}`);
        reviewContainer.classList.remove('hidden');
        reviewContent.innerHTML = '<p class="text-blue-500 text-sm"><i class="fas fa-spinner fa-spin mr-1"></i>AI 正在评阅，请稍候...</p>';

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000); // 2分钟超时
            let response;
            try {
                response = await fetch(`${API_BASE}/api/v1/requirements/documents/${this.currentDocId}/llm-review`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ section_type: sectionId, content }),
                    signal: controller.signal
                });
            } finally {
                clearTimeout(timeoutId);
            }
            if (!response.ok) {
                let detail = '评阅请求失败';
                try { const err = await response.json(); detail = err.detail || detail; } catch (_) {}
                throw new Error(detail);
            }
            const result = await response.json();
            const fixedReview = this.fixMermaidSyntax(result.llm_review || '');
            reviewContent.innerHTML = this.convertMarkdownToHTML(fixedReview);
            await this.renderMermaidCharts(reviewContent);
            showNotification(`LLM评阅完成（使用 ${result.provider}）`, 'success');
        } catch (error) {
            console.error('❌ LLM评阅失败:', error);
            let msg = error.message || '未知错误';
            if (error.name === 'AbortError') msg = '请求超时，请重试';
            else if (msg.includes('Load failed') || msg.includes('Failed to fetch') || msg.includes('NetworkError')) msg = '网络异常，请检查后端服务是否正常运行';
            reviewContent.innerHTML = `<p class="text-red-500 text-sm"><i class="fas fa-exclamation-circle mr-1"></i>评阅失败：${msg}。请重试。</p>`;
            showNotification(`评阅失败: ${msg}`, 'error');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    },

    /**
     * 修复 LLM 生成的 Mermaid 代码块中的语法错误
     * 规则：
     *  1. graph LR/TD/TB — 每条节点定义、箭头、%% 注释独占一行
     *  2. useCaseDiagram — 修正 graph TD/LR 误用，保留 actor/usecase/rectangle/-->/../: 语法
     *  3. sequenceDiagram / classDiagram — 保持原样，仅做空行清理
     */
    fixMermaidSyntax: function(markdown) {
        return markdown.replace(/```mermaid\r?\n([\s\S]*?)\r?\n?```/g, function(_match, code) {
            const rawLines = code.split('\n');
            const decl = (rawLines.find(l => l.trim()) || '').trim();
            if (/^sequenceDiagram/i.test(decl)) {
                return RequirementsManager._fixSequenceDiagram(rawLines);
            }
            if (/^graph\s/i.test(decl)) {
                const trimmed = code.trim();
                const split = RequirementsManager._splitGraphStatements(trimmed);
                const quoted = RequirementsManager._quoteLabelsWithSpaces(split);
                const clean = RequirementsManager._quoteChineseLabels(quoted);
                return '```mermaid\n' + clean + '\n```';
            }
            return _match;
        });
    },

    toggleExpertReview: function(sectionId) {
        const reviewContainer = document.getElementById(`expert-review-${sectionId}`);
        if (reviewContainer.classList.contains('hidden')) {
            reviewContainer.classList.remove('hidden');
        } else {
            this.saveExpertReview(sectionId);
        }
    },

    saveExpertReview: async function(sectionId) {
        const expertReview = document.getElementById(`expert-review-content-${sectionId}`).value.trim();
        if (!expertReview) { showNotification('请输入专家评阅内容', 'error'); return; }
        try {
            const response = await fetch(`${API_BASE}/api/v1/requirements/documents/${this.currentDocId}/expert-review`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ section_type: sectionId, expert_review: expertReview })
            });
            if (!response.ok) throw new Error('保存失败');
            showNotification('专家评阅已保存', 'success');
            document.getElementById(`expert-review-${sectionId}`).classList.add('hidden');
        } catch (error) {
            console.error('❌ 保存专家评阅失败:', error);
            showNotification('保存失败', 'error');
        }
    },

    saveContent: async function(sectionId) {
        const content = document.getElementById(`content-${sectionId}`).value.trim();
        if (!content) return;
        try {
            const response = await fetch(`${API_BASE}/api/v1/requirements/documents/${this.currentDocId}/sections`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ section_type: sectionId, content })
            });
            if (!response.ok) throw new Error('保存失败');
            document.getElementById(`status-${sectionId}`).textContent = '已保存';
        } catch (error) {
            console.error('❌ 保存内容失败:', error);
            document.getElementById(`status-${sectionId}`).textContent = '保存失败';
        }
    },

    downloadDocument: async function(sectionId) {
        const content = document.getElementById(`content-${sectionId}`).value.trim();
        if (!content) { showNotification('当前章节内容为空，无法下载', 'error'); return; }
        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const defaultName = `文档_${now.getFullYear()}${pad(now.getMonth()+1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}.md`;
        const customName = window.prompt('请输入下载文件名（留空使用默认名称）：', defaultName);
        if (customName === null) return;
        const filename = (customName.trim() || defaultName).replace(/\.md$/i, '') + '.md';
        try {
            await this.saveContent(sectionId);
            const url = `${API_BASE}/api/v1/requirements/documents/${this.currentDocId}/download/${sectionId}?filename=${encodeURIComponent(filename)}`;
            const a = document.createElement('a');
            a.href = url; a.download = filename;
            document.body.appendChild(a); a.click(); document.body.removeChild(a);
            showNotification('文档下载成功', 'success');
        } catch (error) {
            console.error('❌ 下载文档失败:', error);
            showNotification('下载失败，请检查网络连接', 'error');
        }
    },

    triggerUpload: function(sectionId) {
        document.getElementById(`drop-zone-${sectionId}`).classList.toggle('hidden');
    },

    onDragOver: function(event, sectionId) {
        event.preventDefault(); event.stopPropagation();
        document.getElementById(`drop-zone-${sectionId}`).classList.add('border-orange-500', 'bg-orange-100');
    },

    onDragLeave: function(event, sectionId) {
        event.preventDefault(); event.stopPropagation();
        document.getElementById(`drop-zone-${sectionId}`).classList.remove('border-orange-500', 'bg-orange-100');
    },

    onDrop: function(event, sectionId) {
        event.preventDefault(); event.stopPropagation();
        document.getElementById(`drop-zone-${sectionId}`).classList.remove('border-orange-500', 'bg-orange-100');
        const files = Array.from(event.dataTransfer.files);
        const mdFile = files.find(f => /\.(md|markdown)$/i.test(f.name));
        const imgFiles = files.filter(f => /\.(png|jpe?g|gif|webp|svg|bmp)$/i.test(f.name));
        if (imgFiles.length > 0) this.handleImageUpload(sectionId, imgFiles);
        if (mdFile) this.handleFileUpload(sectionId, mdFile);
        else if (imgFiles.length === 0) showNotification('请拖入 .md 或 .markdown 文件', 'error');
    },

    /**
     * 处理 .md 文件上传
     * 上传后填入编辑区，自动切换预览并用 marked.js 渲染（含图片）
     */
    handleFileUpload: async function(sectionId, file) {
        if (!file) return;
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!['.md', '.markdown'].includes(ext)) {
            showNotification('文件格式错误：仅支持 .md 或 .markdown 文件', 'error');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            showNotification(`文件过大：${(file.size/1024/1024).toFixed(1)}MB，最大允许 10MB`, 'error');
            return;
        }
        const progressWrap = document.getElementById(`upload-progress-${sectionId}`);
        const progressBar  = document.getElementById(`upload-progress-bar-${sectionId}`);
        const progressText = document.getElementById(`upload-progress-text-${sectionId}`);
        progressWrap.classList.remove('hidden');
        progressBar.style.width = '20%';
        progressText.textContent = '正在上传...';
        const formData = new FormData();
        formData.append('file', file);
        try {
            progressBar.style.width = '50%';
            const response = await fetch(
                `${API_BASE}/api/v1/requirements/documents/${this.currentDocId}/upload/${sectionId}`,
                { method: 'POST', body: formData }
            );
            progressBar.style.width = '80%';
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || `服务器错误 (${response.status})`);
            }
            await response.json();
            const reader = new FileReader();
            reader.onload = async (e) => {
                const mdContent = e.target.result;
                document.getElementById(`content-${sectionId}`).value = mdContent;
                document.getElementById(`status-${sectionId}`).textContent = '已上传';
                document.getElementById(`drop-zone-${sectionId}`).classList.add('hidden');
                // 自动切换到预览区渲染（含图片）
                this.switchTab(sectionId, 'preview');
            };
            reader.onerror = () => showNotification('文件读取失败，请重试', 'error');
            reader.readAsText(file, 'UTF-8');
            progressBar.style.width = '100%';
            progressText.textContent = '上传成功';
            setTimeout(() => progressWrap.classList.add('hidden'), 1500);
            showNotification('文档上传成功', 'success');
        } catch (error) {
            progressBar.style.width = '100%';
            progressBar.classList.replace('bg-orange-500', 'bg-red-500');
            progressText.textContent = `上传失败：${error.message}`;
            setTimeout(() => {
                progressWrap.classList.add('hidden');
                progressBar.classList.replace('bg-red-500', 'bg-orange-500');
            }, 3000);
            console.error('❌ 上传文档失败:', error);
            showNotification(`上传失败：${error.message}`, 'error');
        }
    },

    /**
     * 上传本地图片到后端 /api/v1/requirements/images/upload
     * 返回 /uploads/xxx 路径，显示在图片列表中，点击复制 Markdown 引用
     */
    handleImageUpload: async function(sectionId, files) {
        if (!files || files.length === 0) return;
        const listWrap = document.getElementById(`img-list-${sectionId}`);
        const listEl   = document.getElementById(`img-list-items-${sectionId}`);
        listWrap.classList.remove('hidden');
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            try {
                const response = await fetch(`${API_BASE}/api/v1/requirements/images/upload`, {
                    method: 'POST', body: formData
                });
                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    showNotification(`图片上传失败：${err.detail || file.name}`, 'error');
                    continue;
                }
                const result = await response.json();
                const mdRef = `![${file.name}](${result.url})`;
                const li = document.createElement('li');
                li.className = 'cursor-pointer hover:text-orange-800 truncate';
                li.title = '点击复制 Markdown 引用';
                li.textContent = `✅ ${file.name} → ${result.url}`;
                li.addEventListener('click', () => {
                    navigator.clipboard.writeText(mdRef).then(() => {
                        showNotification(`已复制：${mdRef}`, 'success');
                    });
                });
                listEl.appendChild(li);
                showNotification(`图片上传成功：${file.name}`, 'success');
            } catch (error) {
                console.error('❌ 图片上传失败:', error);
                showNotification(`图片上传失败：${file.name}`, 'error');
            }
        }
    },

    /** 原有简单 Markdown → HTML 转换（LLM评阅区域使用） */
    convertMarkdownToHTML: function(markdown) {
        // 先提取 mermaid 代码块，用占位符替换，避免后续正则破坏代码块内容
        const mermaidBlocks = [];
        // 正则兼容：代码块末尾 ``` 前可能没有换行
        let html = markdown.replace(/```mermaid\r?\n([\s\S]*?)\r?\n?```/g, function(_match, code) {
            const id = 'mermaid-' + Math.random().toString(36).substring(2, 11);
            const trimmed = code.trim();
            const firstLineTrimmed = (trimmed.split('\n').find(l => l.trim()) || '').trim();
            let cleanCode;
            if (/^sequenceDiagram/i.test(firstLineTrimmed)) {
                // sequenceDiagram 已由 fixMermaidSyntax 处理完毕，原样使用
                cleanCode = trimmed;
            } else if (/^graph\s/i.test(firstLineTrimmed)) {
                // graph：拆行（同行多语句）→ 含空格标签加引号 → 中文标签加引号
                const split = RequirementsManager._splitGraphStatements(trimmed);
                const quoted = RequirementsManager._quoteLabelsWithSpaces(split);
                cleanCode = RequirementsManager._quoteChineseLabels(quoted);
            } else {
                cleanCode = trimmed;
            }
            const escaped = cleanCode
                .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
            const placeholder = `\x00MERMAID_${mermaidBlocks.length}\x00`;
            mermaidBlocks.push(`<div class="mermaid-chart my-4 p-4 bg-white border border-gray-200 rounded-lg" id="${id}" data-code="${encodeURIComponent(cleanCode)}">${escaped}</div>`);
            return placeholder;
        });

        // 再处理其他 Markdown 语法（此时代码块已被占位符保护）
        html = html.replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>');
        html = html.replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold mt-6 mb-3">$1</h2>');
        html = html.replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold mt-8 mb-4">$1</h1>');
        html = html.replace(/```(\w+)?\r?\n([\s\S]*?)```/g, '<pre class="bg-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code>$2</code></pre>');
        html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-2 py-1 rounded text-sm">$1</code>');
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/^\d+\. (.*$)/gm, '<li class="ml-6 my-1">$1</li>');
        html = html.replace(/^- (.*$)/gm, '<li class="ml-6 my-1">$1</li>');
        html = html.replace(/\n\n/g, '<br><br>');

        // 最后还原 mermaid 占位符
        html = html.replace(/\x00MERMAID_(\d+)\x00/g, (_, i) => mermaidBlocks[+i]);
        return html;
    },

    /**
     * 对 graph 类 Mermaid 代码做语句拆行。
     * sequenceDiagram / classDiagram 不处理，直接原样返回。
     */
    _splitGraphStatements: function(code) {
        const firstLine = code.split('\n').find(l => l.trim()) || '';
        // 非 graph 类图表直接返回，不做任何处理
        if (!/^graph\s/i.test(firstLine.trim())) return code;

        const lines = code.split('\n');
        const result = [];
        for (const rawLine of lines) {
            const line = rawLine.replace(/\r$/, '').trim();
            if (!line) continue;

            // graph 声明行：提取声明部分，剩余内容作为普通行继续处理
            if (/^graph\s+(LR|TD|TB|BT|RL)\b/i.test(line)) {
                const m = line.match(/^(graph\s+(?:LR|TD|TB|BT|RL))(.*)/i);
                result.push(m[1]);
                const rest = m[2].trim();
                if (rest) {
                    // 把剩余内容当普通行递归拆分
                    const sub = RequirementsManager._splitGraphStatements('graph TB\n' + rest).split('\n').slice(1);
                    for (const s of sub) if (s.trim()) result.push(s.trim());
                }
                continue;
            }

            // 逐字符扫描，跟踪方括号/圆括号深度，在深度 0 处的语句边界拆分
            const stmts = [];
            let depth = 0;
            let cur = '';
            for (let i = 0; i < line.length; i++) {
                const ch = line[i];
                if (ch === '[' || ch === '(') depth++;
                else if (ch === ']' || ch === ')') depth--;
                // depth=0 时遇到空格：向前跳过所有空格，看下一个非空字符是否是标识符起始
                if (depth === 0 && ch === ' ') {
                    let j = i + 1;
                    while (j < line.length && line[j] === ' ') j++;
                    if (j < line.length && /[A-Za-z_]/.test(line[j])) {
                        const trimmed = cur.trim();
                        // 如果 cur 以箭头结尾（连接线还未完整），不拆分
                        const endsWithArrow = /[-=][-=]?>$/.test(trimmed) || /---$/.test(trimmed);
                        if (!endsWithArrow) {
                            if (trimmed) stmts.push(trimmed);
                            cur = '';
                            i = j - 1;
                            continue;
                        }
                    }
                }
                cur += ch;
            }
            if (cur.trim()) stmts.push(cur.trim());
            for (const s of stmts) result.push(s);
        }
        return result.join('\n');
    },

    /**
     * 给 Mermaid graph 代码中不带引号的中文节点标签自动加引号。
     * 例如：Node[用户客户端]  →  Node["用户客户端"]
     *       Node(借阅服务)    →  Node("借阅服务")
     *       Node[(Redis)]     保持不变（已是英文）
     * 带引号的标签不处理。
     */
    _quoteChineseLabels: function(code) {
        // 匹配 [内容] 或 (内容) 或 [(内容)] 形式，内容不含引号且含中文
        return code
            // Node[中文] → Node["中文"]
            .replace(/(\w)\[([^\]"]*[\u4e00-\u9fff][^\]"]*)\]/g, '$1["$2"]')
            // Node(中文) → Node("中文")
            .replace(/(\w)\(([^)"]*[\u4e00-\u9fff][^)"]*)\)/g, '$1("$2")')
            // Node[(中文)] → Node[("中文")]
            .replace(/(\w)\[\(([^)"]*[\u4e00-\u9fff][^)"]*)\)\]/g, '$1[("$2")]');
    },

    /**
     * 给节点标签中含空格但未加引号的内容补引号（英文/中文均处理）。
     * 例如：DB[(MySQL DB)] → DB[("MySQL DB")]
     *       SVC[Auth Service] → SVC["Auth Service"]
     * 已有引号的不处理。
     */
    _quoteLabelsWithSpaces: function(code) {
        // 用 [^\S\n] 代替 \s，只匹配空格/制表符，不跨行
        return code
            // Node[(内容含空格)] → Node[("内容")]  ← 必须先处理，避免被下面的规则误匹配
            .replace(/(\w)\[\(([^)"]*[^\S\n][^)"]*)\)\]/g, '$1[("$2")]')
            // Node[内容含空格] → Node["内容"]  ← 排除已含 ( 的情况（圆柱体语法）
            .replace(/(\w)\[([^\]"(]*[^\S\n][^\]"(]*)\]/g, '$1["$2"]')
            // Node(内容含空格) → Node("内容")
            .replace(/(\w)\(([^)"]*[^\S\n][^)"]*)\)/g, '$1("$2")');
    },

    /**
     * 专门处理 sequenceDiagram 的语法修复，与 graph 类完全隔离。
     * - participant/actor 顶格，清理别名中的特殊字符
     * - loop/alt/else/opt/par/critical/break/end/Note 顶格
     * - 消息行（所有箭头类型）缩进 4 空格，清理消息文本中的特殊字符
     */
    _fixSequenceDiagram: function(rawLines) {
        // LLM が一行で書いた場合（例: "sequenceDiagram participant A C->>A: msg"）を展開する
        // セミコロンまたは既知キーワードの前で改行を挿入
        const expanded = [];
        for (const line of rawLines) {
            const t = line.replace(/\r$/, '').trim();
            if (!t) continue;
            if (/^sequenceDiagram/i.test(t) && t.length > 'sequenceDiagram'.length) {
                // 宣言と残りを分離
                expanded.push('sequenceDiagram');
                const rest = t.slice('sequenceDiagram'.length).trim();
                // キーワード境界で分割
                const parts = rest.split(/(?=\b(?:participant|actor|loop|alt|else|opt|par|critical|break|end|Note|activate|deactivate)\b)/i);
                for (const p of parts) if (p.trim()) expanded.push(p.trim());
            } else {
                expanded.push(t);
            }
        }

        const out = ['sequenceDiagram'];
        for (const line of expanded) {
            const t = line.replace(/\r$/, '').trim();
            if (!t || /^%%/.test(t) || /^sequenceDiagram$/i.test(t)) continue;

            // participant/actor：顶格，清理特殊字符
            if (/^(participant|actor)\s/i.test(t)) {
                out.push(t.replace(/[{}]/g, '').replace(/"/g, "'").replace(/[()]/g, ''));
                continue;
            }
            // 控制关键字：顶格
            if (/^(loop|alt|else|opt|par|critical|break|end|Note)\b/i.test(t)) {
                out.push(t);
                continue;
            }
            // 消息行：所有合法箭头类型，缩进 4 空格，清理消息文本
            if (/--?>?>?[>x)]/.test(t)) {
                const colonIdx = t.indexOf(':');
                if (colonIdx !== -1) {
                    const prefix = t.slice(0, colonIdx + 1);
                    const msg = t.slice(colonIdx + 1)
                        .replace(/[{}]/g, '')
                        .replace(/"/g, "'")
                        .replace(/[()]/g, '')
                        .replace(/\s+/g, ' ').trim();
                    out.push('    ' + prefix + ' ' + msg);
                    continue;
                }
            }
            // 其他行（activate/deactivate 等）：缩进 4 空格
            out.push('    ' + t);
        }
        return '```mermaid\n' + out.join('\n') + '\n```';
    },

    renderMermaidCharts: async function(container) {
        try {
            await loadMermaid();
            if (typeof window.mermaid === 'undefined') return;

            const charts = container.querySelectorAll('.mermaid-chart');
            for (const chart of charts) {
                const rawAttr = chart.getAttribute('data-code');
                const code = rawAttr ? decodeURIComponent(rawAttr) : null;
                if (!code || !code.trim()) {
                    chart.innerHTML = '<div class="text-red-600 text-sm">图表代码为空</div>';
                    continue;
                }
                // 每次使用唯一 ID，避免重复渲染时 Mermaid 内部 ID 冲突
                const renderId = 'mermaid-r-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);
                try {
                    const { svg } = await window.mermaid.render(renderId, code);
                    chart.innerHTML = svg;
                } catch (error) {
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
    notification.innerHTML = `<div class="flex items-center gap-2"><i class="fas ${icon}"></i><span>${message}</span></div>`;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.style.transform = 'translateX(500px)';
        setTimeout(() => document.body.removeChild(notification), 300);
    }, 3000);
}
