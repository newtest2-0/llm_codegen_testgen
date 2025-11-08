/**
 * 审阅系统 - 处理五个专业模块的日志记录和评阅功能
 */

const ReviewSystem = {
  // 存储键前缀
  STORAGE_PREFIX: 'review_log_',
  
  // 字段配置
  fields: {
    detailedRequirement: {
      name: '详细需求描述',
      type: 'requirement'
    },
    architectureDesign: {
      name: '架构设计',
      type: 'architecture'
    },
    detailedDesign: {
      name: '详细设计',
      type: 'design'
    },
    requirementToArchitecture: {
      name: '需求到架构的追溯',
      type: 'trace_arch'
    },
    requirementToDesign: {
      name: '需求到详细设计的追溯',
      type: 'trace_design'
    }
  },

  /**
   * 初始化审阅系统
   */
  init() {
    console.log('🚀 初始化审阅系统...');
    
    // 为每个字段添加字符计数功能
    Object.keys(this.fields).forEach(fieldId => {
      const textarea = document.getElementById(fieldId);
      const charCountSpan = document.getElementById(`${fieldId}CharCount`);
      
      if (textarea && charCountSpan) {
        textarea.addEventListener('input', () => {
          charCountSpan.textContent = textarea.value.length;
        });
      }
      
      // 加载日志计数
      this.updateLogCount(fieldId);
    });
    
    console.log('✅ 审阅系统初始化完成');
  },

  /**
   * LLM评阅 - 将内容发送给LLM进行评阅
   */
  async llmReview(fieldId) {
    const textarea = document.getElementById(fieldId);
    const content = textarea.value.trim();
    
    if (!content) {
      this.showNotification('请先输入内容', 'warning');
      return;
    }
    
    const fieldConfig = this.fields[fieldId];
    
    // 显示加载提示
    this.showNotification(`正在提交给LLM评阅: ${fieldConfig.name}...`, 'info');
    
    try {
      // 调用后端API进行LLM评阅
      const response = await fetch('/api/v1/review/llm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          field_type: fieldConfig.type,
          content: content,
          field_name: fieldConfig.name
        })
      });
      
      if (!response.ok) {
        throw new Error('LLM评阅请求失败');
      }
      
      const result = await response.json();
      
      // 显示评阅结果
      this.showReviewResult(fieldId, result, 'llm');
      
      // 保存评阅记录
      this.saveReviewLog(fieldId, content, result, 'llm');
      
      this.showNotification('LLM评阅完成', 'success');
      
    } catch (error) {
      console.error('LLM评阅失败:', error);
      this.showNotification('LLM评阅失败: ' + error.message, 'error');
    }
  },

  /**
   * 专家评阅 - 允许用户直接编辑和修改
   */
  expertReview(fieldId) {
    const textarea = document.getElementById(fieldId);
    const fieldConfig = this.fields[fieldId];
    
    // 创建专家评阅模态框
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
    modal.innerHTML = `
      <div class="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div class="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 class="text-xl font-semibold text-gray-900">
            <i class="fas fa-user-tie text-blue-600 mr-2"></i>
            专家评阅: ${fieldConfig.name}
          </h3>
          <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[70vh]">
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              内容编辑
              <span class="text-xs text-gray-500 ml-2">(您可以直接修改和完善内容)</span>
            </label>
            <textarea 
              id="expertEditContent" 
              class="w-full h-96 form-input rounded-lg p-4 resize-y text-sm font-mono"
              placeholder="在此编辑和完善内容..."
            >${textarea.value}</textarea>
          </div>
          
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">评审意见</label>
            <textarea 
              id="expertComments" 
              class="w-full h-32 form-input rounded-lg p-4 resize-y text-sm"
              placeholder="记录您的评审意见、建议和改进点..."
            ></textarea>
          </div>
          
          <div class="flex gap-3">
            <button 
              onclick="ReviewSystem.saveExpertReview('${fieldId}')"
              class="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg transition-colors"
            >
              <i class="fas fa-save mr-2"></i>保存评审结果
            </button>
            <button 
              onclick="this.closest('.fixed').remove()"
              class="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
  },

  /**
   * 保存专家评审结果
   */
  saveExpertReview(fieldId) {
    const editedContent = document.getElementById('expertEditContent').value;
    const comments = document.getElementById('expertComments').value;
    
    if (!editedContent.trim()) {
      this.showNotification('内容不能为空', 'warning');
      return;
    }
    
    // 更新原文本框内容
    document.getElementById(fieldId).value = editedContent;
    
    // 保存评审记录
    const reviewData = {
      content: editedContent,
      comments: comments,
      type: 'expert',
      timestamp: new Date().toISOString()
    };
    
    this.saveReviewLog(fieldId, editedContent, reviewData, 'expert');
    
    // 关闭模态框
    document.querySelector('.fixed.inset-0').remove();
    
    this.showNotification('专家评审已保存', 'success');
  },

  /**
   * 下载文档
   */
  downloadDoc(fieldId) {
    const textarea = document.getElementById(fieldId);
    const content = textarea.value.trim();
    
    if (!content) {
      this.showNotification('没有可下载的内容', 'warning');
      return;
    }
    
    const fieldConfig = this.fields[fieldId];
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `${fieldConfig.name}_${timestamp}.txt`;
    
    // 创建下载
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
    
    this.showNotification('文档已下载', 'success');
  },

  /**
   * 上传文档
   */
  uploadDoc(fieldId) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt,.md,.json';
    
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      try {
        const text = await file.text();
        document.getElementById(fieldId).value = text;
        
        // 更新字符计数
        const charCountSpan = document.getElementById(`${fieldId}CharCount`);
        if (charCountSpan) {
          charCountSpan.textContent = text.length;
        }
        
        this.showNotification('文档已上传', 'success');
      } catch (error) {
        console.error('文件读取失败:', error);
        this.showNotification('文件读取失败', 'error');
      }
    };
    
    input.click();
  },

  /**
   * 保存日志记录
   */
  saveLog(fieldId) {
    const textarea = document.getElementById(fieldId);
    const content = textarea.value.trim();
    
    if (!content) {
      this.showNotification('请先输入内容', 'warning');
      return;
    }
    
    const fieldConfig = this.fields[fieldId];
    
    const logEntry = {
      id: `log_${Date.now()}`,
      content: content,
      fieldName: fieldConfig.name,
      fieldType: fieldConfig.type,
      timestamp: new Date().toISOString(),
      author: 'user'
    };
    
    // 获取现有日志
    const logs = this.getLogsForField(fieldId);
    logs.unshift(logEntry);
    
    // 保存到localStorage
    localStorage.setItem(
      `${this.STORAGE_PREFIX}${fieldId}`,
      JSON.stringify(logs)
    );
    
    // 更新计数
    this.updateLogCount(fieldId);
    
    this.showNotification(`已保存到日志: ${fieldConfig.name}`, 'success');
  },

  /**
   * 查看日志
   */
  viewLogs(fieldId) {
    const logs = this.getLogsForField(fieldId);
    const fieldConfig = this.fields[fieldId];
    
    if (logs.length === 0) {
      this.showNotification('暂无日志记录', 'info');
      return;
    }
    
    // 创建日志查看模态框
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
    
    const logsHtml = logs.map((log, index) => `
      <div class="bg-white rounded-lg p-4 mb-3 border border-gray-200">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="text-sm font-semibold text-gray-900">#${logs.length - index}</span>
            <span class="text-xs text-gray-500">${new Date(log.timestamp).toLocaleString('zh-CN')}</span>
          </div>
          <div class="flex gap-2">
            <button 
              onclick="ReviewSystem.loadLog('${fieldId}', '${log.id}')"
              class="text-xs text-blue-600 hover:text-blue-700"
            >
              <i class="fas fa-undo mr-1"></i>恢复
            </button>
            <button 
              onclick="ReviewSystem.deleteLog('${fieldId}', '${log.id}')"
              class="text-xs text-red-600 hover:text-red-700"
            >
              <i class="fas fa-trash mr-1"></i>删除
            </button>
          </div>
        </div>
        <pre class="text-xs text-gray-700 bg-gray-50 p-3 rounded overflow-auto max-h-40">${log.content}</pre>
        ${log.comments ? `<div class="mt-2 text-xs text-gray-600 italic">评论: ${log.comments}</div>` : ''}
      </div>
    `).join('');
    
    modal.innerHTML = `
      <div class="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div class="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 class="text-xl font-semibold text-gray-900">
            <i class="fas fa-history text-gray-600 mr-2"></i>
            日志记录: ${fieldConfig.name}
          </h3>
          <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[70vh]">
          ${logsHtml}
        </div>
        <div class="p-6 border-t border-gray-200 bg-gray-50">
          <button 
            onclick="ReviewSystem.clearAllLogs('${fieldId}')"
            class="text-sm text-red-600 hover:text-red-700"
          >
            <i class="fas fa-trash-alt mr-1"></i>清空所有日志
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
  },

  /**
   * 加载某条日志
   */
  loadLog(fieldId, logId) {
    const logs = this.getLogsForField(fieldId);
    const log = logs.find(l => l.id === logId);
    
    if (log) {
      document.getElementById(fieldId).value = log.content;
      
      // 更新字符计数
      const charCountSpan = document.getElementById(`${fieldId}CharCount`);
      if (charCountSpan) {
        charCountSpan.textContent = log.content.length;
      }
      
      // 关闭模态框
      document.querySelector('.fixed.inset-0')?.remove();
      
      this.showNotification('已恢复日志内容', 'success');
    }
  },

  /**
   * 删除某条日志
   */
  deleteLog(fieldId, logId) {
    if (!confirm('确定要删除这条日志吗?')) return;
    
    let logs = this.getLogsForField(fieldId);
    logs = logs.filter(l => l.id !== logId);
    
    localStorage.setItem(
      `${this.STORAGE_PREFIX}${fieldId}`,
      JSON.stringify(logs)
    );
    
    // 更新计数
    this.updateLogCount(fieldId);
    
    // 刷新日志视图
    document.querySelector('.fixed.inset-0')?.remove();
    this.viewLogs(fieldId);
    
    this.showNotification('日志已删除', 'success');
  },

  /**
   * 清空所有日志
   */
  clearAllLogs(fieldId) {
    if (!confirm('确定要清空所有日志吗?此操作不可恢复!')) return;
    
    localStorage.removeItem(`${this.STORAGE_PREFIX}${fieldId}`);
    this.updateLogCount(fieldId);
    
    // 关闭模态框
    document.querySelector('.fixed.inset-0')?.remove();
    
    this.showNotification('已清空所有日志', 'success');
  },

  /**
   * 获取字段的所有日志
   */
  getLogsForField(fieldId) {
    const stored = localStorage.getItem(`${this.STORAGE_PREFIX}${fieldId}`);
    return stored ? JSON.parse(stored) : [];
  },

  /**
   * 保存评审日志
   */
  saveReviewLog(fieldId, content, reviewData, reviewType) {
    const logEntry = {
      id: `log_${Date.now()}`,
      content: content,
      reviewData: reviewData,
      reviewType: reviewType,
      timestamp: new Date().toISOString()
    };
    
    const logs = this.getLogsForField(fieldId);
    logs.unshift(logEntry);
    
    localStorage.setItem(
      `${this.STORAGE_PREFIX}${fieldId}`,
      JSON.stringify(logs)
    );
    
    this.updateLogCount(fieldId);
  },

  /**
   * 更新日志计数
   */
  updateLogCount(fieldId) {
    const logs = this.getLogsForField(fieldId);
    const countSpan = document.getElementById(`${fieldId}LogCount`);
    if (countSpan) {
      countSpan.textContent = logs.length;
    }
  },

  /**
   * 显示评审结果
   */
  showReviewResult(fieldId, result, reviewType) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
    
    const typeLabel = reviewType === 'llm' ? 'LLM评阅' : '专家评阅';
    const iconClass = reviewType === 'llm' ? 'fa-robot' : 'fa-user-tie';
    
    modal.innerHTML = `
      <div class="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div class="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 class="text-xl font-semibold text-gray-900">
            <i class="fas ${iconClass} text-purple-600 mr-2"></i>
            ${typeLabel}结果
          </h3>
          <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[70vh]">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h4 class="font-semibold text-blue-900 mb-2">
              <i class="fas fa-check-circle mr-2"></i>评阅完成
            </h4>
            <div class="text-sm text-blue-800 whitespace-pre-wrap">${result.review || result.suggestion || '评阅完成,请查看详细内容。'}</div>
          </div>
          
          ${result.score ? `
            <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <h4 class="font-semibold text-green-900 mb-2">质量评分</h4>
              <div class="text-2xl font-bold text-green-600">${result.score}/100</div>
            </div>
          ` : ''}
          
          ${result.suggestions && result.suggestions.length > 0 ? `
            <div class="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <h4 class="font-semibold text-amber-900 mb-2">改进建议</h4>
              <ul class="list-disc list-inside space-y-1 text-sm text-amber-800">
                ${result.suggestions.map(s => `<li>${s}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
        </div>
        <div class="p-6 border-t border-gray-200 flex gap-3">
          <button 
            onclick="this.closest('.fixed').remove()"
            class="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg transition-colors"
          >
            确定
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
  },

  /**
   * 显示通知
   */
  showNotification(message, type = 'info') {
    const colors = {
      success: 'bg-green-500',
      error: 'bg-red-500',
      warning: 'bg-yellow-500',
      info: 'bg-blue-500'
    };
    
    const icons = {
      success: 'fa-check-circle',
      error: 'fa-exclamation-circle',
      warning: 'fa-exclamation-triangle',
      info: 'fa-info-circle'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-3 animate-slide-in`;
    notification.innerHTML = `
      <i class="fas ${icons[type]}"></i>
      <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.opacity = '0';
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }
};

// 页面加载完成后初始化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => ReviewSystem.init());
} else {
  ReviewSystem.init();
}

// 等待main.js加载完成后，扩展RightNavigation对象
window.addEventListener('load', function() {
  // 检查RightNavigation是否已存在（由main.js创建）
  if (typeof window.RightNavigation !== 'undefined') {
    console.log('🔧 扩展RightNavigation功能...');
    
    // 保存原有的scrollToSection方法（如果存在）
    const originalScrollToSection = window.RightNavigation.scrollToSection;
    
    // 添加新的方法到现有的RightNavigation对象
    Object.assign(window.RightNavigation, {
      /**
       * 滚动到指定区域（增强版）
       */
      scrollToSectionEnhanced(sectionId) {
        const element = document.getElementById(sectionId);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          // 添加高亮效果
          element.classList.add('section-highlight');
          setTimeout(() => {
            element.classList.remove('section-highlight');
          }, 3000);
        }
      },
      
      /**
       * 批量评阅所有模块
       */
      async batchReview() {
        const modules = [
          'detailedRequirement',
          'architectureDesign',
          'detailedDesign',
          'requirementToArchitecture',
          'requirementToDesign'
        ];

        // 检查是否有内容
        const hasContent = modules.some(moduleId => {
          const textarea = document.getElementById(moduleId);
          return textarea && textarea.value.trim();
        });

        if (!hasContent) {
          ReviewSystem.showNotification('请先填写至少一个模块的内容', 'warning');
          return;
        }

        if (!confirm('确定要对所有填写的模块进行LLM批量评阅吗？\n\n这可能需要一些时间。')) {
          return;
        }

        ReviewSystem.showNotification('开始批量评阅，请稍候...', 'info');

        let successCount = 0;
        let failCount = 0;

        for (const moduleId of modules) {
          const textarea = document.getElementById(moduleId);
          if (textarea && textarea.value.trim()) {
            try {
              await ReviewSystem.llmReview(moduleId);
              successCount++;
              // 等待一秒再继续，避免API限流
              await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
              console.error(`模块 ${moduleId} 评阅失败:`, error);
              failCount++;
            }
          }
        }

        ReviewSystem.showNotification(
          `批量评阅完成！成功: ${successCount}, 失败: ${failCount}`,
          failCount === 0 ? 'success' : 'warning'
        );
      }
    });
    
    console.log('✅ RightNavigation功能扩展完成');
  } else {
    console.warn('⚠️ RightNavigation对象未找到，可能main.js未正确加载');
  }
});

