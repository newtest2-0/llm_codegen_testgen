/**
 * 知识库管理系统
 * 用于管理和检索项目经验
 */

const KnowledgeSystem = {
    // 配置
    config: {
        apiBase: '/api/v1/knowledge',
        storageKey: 'knowledge_entries'
    },

    /**
     * 初始化知识库系统
     */
    init() {
        console.log('[Knowledge] 知识库系统初始化...');
        this.loadStatistics();
    },

    /**
     * 加载知识库统计信息
     */
    async loadStatistics() {
        try {
            const response = await fetch(`${this.config.apiBase}/statistics`);
            const data = await response.json();
            
            if (data.success) {
                this.updateStatisticsDisplay(data.statistics);
            }
        } catch (error) {
            console.error('[Knowledge] 加载统计信息失败:', error);
        }
    },

    /**
     * 更新统计信息显示
     */
    updateStatisticsDisplay(stats) {
        const statsElement = document.getElementById('knowledge-statistics');
        if (!statsElement) return;

        statsElement.innerHTML = `
            <div class="grid grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
                <div class="text-center">
                    <div class="text-2xl font-bold text-blue-600">${stats.total}</div>
                    <div class="text-sm text-gray-600">总条目数</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-green-600">${stats.avg_quality.toFixed(2)}</div>
                    <div class="text-sm text-gray-600">平均质量</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-purple-600">${Object.keys(stats.languages).length}</div>
                    <div class="text-sm text-gray-600">语言种类</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-orange-600">${Object.keys(stats.tags).length}</div>
                    <div class="text-sm text-gray-600">标签种类</div>
                </div>
            </div>
        `;
    },

    /**
     * 添加知识条目
     */
    async addEntry(requirement, code, language, qualityScore, tags = [], testResults = null) {
        try {
            const response = await fetch(`${this.config.apiBase}/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    requirement,
                    code,
                    language,
                    tags,
                    quality_score: qualityScore,
                    test_results: testResults
                })
            });

            const data = await response.json();
            
            if (data.success) {
                console.log('[Knowledge] 添加成功:', data.entry_id);
                this.showNotification('知识条目已添加', 'success');
                this.loadStatistics();
                return data.entry_id;
            } else {
                throw new Error(data.message || '添加失败');
            }
        } catch (error) {
            console.error('[Knowledge] 添加失败:', error);
            this.showNotification('添加失败: ' + error.message, 'error');
            return null;
        }
    },

    /**
     * 搜索知识库
     */
    async search(query, language = null, topK = 5) {
        try {
            const response = await fetch(`${this.config.apiBase}/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    top_k: topK,
                    language,
                    min_quality: 0.5
                })
            });

            const data = await response.json();
            
            if (data.success) {
                console.log(`[Knowledge] 找到 ${data.count} 条相关记录`);
                return data.results;
            } else {
                throw new Error(data.message || '搜索失败');
            }
        } catch (error) {
            console.error('[Knowledge] 搜索失败:', error);
            return [];
        }
    },

    /**
     * 获取增强的prompt
     */
    async getEnhancedPrompt(requirement, language) {
        try {
            const response = await fetch(`${this.config.apiBase}/enhanced-prompt`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    requirement,
                    language,
                    top_k: 3
                })
            });

            const data = await response.json();
            
            if (data.success) {
                console.log(`[Knowledge] 生成增强prompt，参考 ${data.reference_count} 个案例`);
                return {
                    prompt: data.enhanced_prompt,
                    references: data.references
                };
            } else {
                return null;
            }
        } catch (error) {
            console.error('[Knowledge] 获取增强prompt失败:', error);
            return null;
        }
    },

    /**
     * 列出知识条目
     */
    async listEntries(language = null, limit = 50, offset = 0) {
        try {
            const params = new URLSearchParams({
                limit: limit.toString(),
                offset: offset.toString()
            });
            if (language) {
                params.append('language', language);
            }

            const response = await fetch(`${this.config.apiBase}/list?${params}`);
            const data = await response.json();
            
            if (data.success) {
                return data.entries;
            } else {
                throw new Error(data.message || '获取列表失败');
            }
        } catch (error) {
            console.error('[Knowledge] 获取列表失败:', error);
            return [];
        }
    },

    /**
     * 删除知识条目
     */
    async deleteEntry(entryId) {
        try {
            const response = await fetch(`${this.config.apiBase}/entry/${entryId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                console.log('[Knowledge] 删除成功:', entryId);
                this.showNotification('知识条目已删除', 'success');
                this.loadStatistics();
                return true;
            } else {
                throw new Error(data.message || '删除失败');
            }
        } catch (error) {
            console.error('[Knowledge] 删除失败:', error);
            this.showNotification('删除失败: ' + error.message, 'error');
            return false;
        }
    },

    /**
     * 显示知识库浏览器
     */
    showBrowser() {
        const modal = this.createBrowserModal();
        document.body.appendChild(modal);
        this.loadEntriesInBrowser();
    },

    /**
     * 创建浏览器模态框
     */
    createBrowserModal() {
        const modal = document.createElement('div');
        modal.id = 'knowledge-browser-modal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg w-5/6 h-5/6 flex flex-col">
                <!-- 头部 -->
                <div class="flex items-center justify-between p-4 border-b">
                    <h2 class="text-xl font-bold">
                        <i class="fas fa-database mr-2"></i>知识库浏览器
                    </h2>
                    <button onclick="KnowledgeSystem.closeBrowser()" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>

                <!-- 搜索栏 -->
                <div class="p-4 border-b">
                    <div class="flex gap-2">
                        <input 
                            type="text" 
                            id="knowledge-search-input"
                            placeholder="搜索需求..."
                            class="flex-1 px-4 py-2 border rounded-lg"
                        />
                        <select id="knowledge-language-filter" class="px-4 py-2 border rounded-lg">
                            <option value="">所有语言</option>
                            <option value="python">Python</option>
                            <option value="javascript">JavaScript</option>
                            <option value="java">Java</option>
                            <option value="cpp">C++</option>
                        </select>
                        <button onclick="KnowledgeSystem.searchInBrowser()" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                            <i class="fas fa-search mr-2"></i>搜索
                        </button>
                    </div>
                </div>

                <!-- 统计信息 -->
                <div id="knowledge-statistics" class="p-4"></div>

                <!-- 条目列表 -->
                <div id="knowledge-entries-list" class="flex-1 overflow-auto p-4">
                    <div class="text-center text-gray-500">加载中...</div>
                </div>

                <!-- 底部 -->
                <div class="p-4 border-t flex justify-between">
                    <button onclick="KnowledgeSystem.loadStatistics()" class="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300">
                        <i class="fas fa-sync mr-2"></i>刷新
                    </button>
                    <button onclick="KnowledgeSystem.closeBrowser()" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        关闭
                    </button>
                </div>
            </div>
        `;
        return modal;
    },

    /**
     * 在浏览器中加载条目
     */
    async loadEntriesInBrowser() {
        const container = document.getElementById('knowledge-entries-list');
        if (!container) return;

        container.innerHTML = '<div class="text-center text-gray-500">加载中...</div>';

        const entries = await this.listEntries();
        
        if (entries.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-500">暂无知识条目</div>';
            return;
        }

        container.innerHTML = entries.map(entry => `
            <div class="border rounded-lg p-4 mb-4 hover:shadow-lg transition">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">${entry.language}</span>
                            <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">质量: ${(entry.quality_score * 100).toFixed(0)}%</span>
                            ${entry.tags.map(tag => `<span class="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">${tag}</span>`).join('')}
                        </div>
                        <div class="text-sm text-gray-600 mb-2">${entry.requirement.substring(0, 200)}...</div>
                    </div>
                    <button onclick="KnowledgeSystem.deleteEntry('${entry.id}')" class="text-red-500 hover:text-red-700 ml-4">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <details class="text-sm">
                    <summary class="cursor-pointer text-blue-600 hover:text-blue-800">查看代码</summary>
                    <pre class="bg-gray-100 p-3 rounded mt-2 overflow-auto"><code>${this.escapeHtml(entry.code)}</code></pre>
                </details>
            </div>
        `).join('');
    },

    /**
     * 在浏览器中搜索
     */
    async searchInBrowser() {
        const query = document.getElementById('knowledge-search-input').value;
        const language = document.getElementById('knowledge-language-filter').value;
        
        if (!query.trim()) {
            this.loadEntriesInBrowser();
            return;
        }

        const container = document.getElementById('knowledge-entries-list');
        container.innerHTML = '<div class="text-center text-gray-500">搜索中...</div>';

        const results = await this.search(query, language || null, 20);
        
        if (results.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-500">未找到相关结果</div>';
            return;
        }

        container.innerHTML = results.map(result => {
            const entry = result.entry;
            return `
                <div class="border rounded-lg p-4 mb-4 hover:shadow-lg transition">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">${entry.language}</span>
                                <span class="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">相似度: ${(result.score * 100).toFixed(0)}%</span>
                                <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">质量: ${(entry.quality_score * 100).toFixed(0)}%</span>
                                ${entry.tags.map(tag => `<span class="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">${tag}</span>`).join('')}
                            </div>
                            <div class="text-sm text-gray-600 mb-2">${entry.requirement.substring(0, 200)}...</div>
                        </div>
                        <button onclick="KnowledgeSystem.useEntry('${entry.id}')" class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 ml-4">
                            使用此案例
                        </button>
                    </div>
                    <details class="text-sm">
                        <summary class="cursor-pointer text-blue-600 hover:text-blue-800">查看代码</summary>
                        <pre class="bg-gray-100 p-3 rounded mt-2 overflow-auto"><code>${this.escapeHtml(entry.code)}</code></pre>
                    </details>
                </div>
            `;
        }).join('');
    },

    /**
     * 使用知识条目
     */
    async useEntry(entryId) {
        // 获取条目详情
        const response = await fetch(`${this.config.apiBase}/entry/${entryId}`);
        const data = await response.json();
        
        if (data.success) {
            const entry = data.entry;
            // 填充到需求输入框
            const requirementTextarea = document.getElementById('requirement') || 
                                       document.getElementById('detailedRequirement');
            if (requirementTextarea) {
                requirementTextarea.value = entry.requirement;
            }
            
            this.showNotification('已加载知识案例', 'success');
            this.closeBrowser();
        }
    },

    /**
     * 关闭浏览器
     */
    closeBrowser() {
        const modal = document.getElementById('knowledge-browser-modal');
        if (modal) {
            modal.remove();
        }
    },

    /**
     * 转义HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * 显示通知
     */
    showNotification(message, type = 'info') {
        // 复用ReviewSystem的通知
        if (typeof ReviewSystem !== 'undefined' && ReviewSystem.showNotification) {
            ReviewSystem.showNotification(message, type);
        } else {
            console.log(`[Knowledge] ${type}: ${message}`);
        }
    }
};

// 页面加载完成后初始化
window.addEventListener('load', () => {
    if (typeof KnowledgeSystem !== 'undefined') {
        KnowledgeSystem.init();
    }
});

console.log('[OK] 知识库系统已加载');

