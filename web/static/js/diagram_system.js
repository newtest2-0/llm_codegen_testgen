/**
 * UML图表系统 - 支持Mermaid图表的生成、编辑和渲染
 */

const DiagramSystem = {
  // 图表类型配置
  diagramTypes: {
    detailedRequirement: {
      type: 'usecase',
      name: '用例图',
      icon: 'fa-project-diagram'
    },
    architectureDesign: {
      type: 'component',
      name: '组件图',
      icon: 'fa-cubes'
    },
    detailedDesign: {
      type: 'class',
      name: '类图',
      icon: 'fa-sitemap'
    },
    requirementToArchitecture: {
      type: 'flowchart',
      name: '流程图',
      icon: 'fa-stream'
    },
    requirementToDesign: {
      type: 'sequence',
      name: '序列图',
      icon: 'fa-exchange-alt'
    }
  },

  /**
   * 初始化图表系统
   */
  init() {
    console.log('🎨 初始化UML图表系统...');
    
    // 初始化Mermaid
    if (typeof mermaid !== 'undefined') {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose',
        flowchart: {
          useMaxWidth: true,
          htmlLabels: true,
          curve: 'basis'
        }
      });
      console.log('✅ Mermaid初始化完成');
    } else {
      console.error('❌ Mermaid库未加载');
    }
  },

  /**
   * 切换标签页（文本/图表）
   */
  switchTab(moduleId, tabType) {
    console.log(`🔄 切换标签页: ${moduleId} → ${tabType}`);
    
    // 更新按钮状态
    const buttons = document.querySelectorAll(`[data-module="${moduleId}"]`);
    buttons.forEach(btn => {
      if (btn.dataset.tab === tabType) {
        btn.classList.add('active', 'bg-blue-100', 'text-blue-700');
        btn.classList.remove('bg-gray-100', 'text-gray-600');
      } else {
        btn.classList.remove('active', 'bg-blue-100', 'text-blue-700');
        btn.classList.add('bg-gray-100', 'text-gray-600');
      }
    });
    
    // 切换面板
    const textPanel = document.getElementById(`${moduleId}-text-panel`);
    const diagramPanel = document.getElementById(`${moduleId}-diagram-panel`);
    
    if (tabType === 'text') {
      textPanel?.classList.remove('hidden');
      textPanel?.classList.add('active');
      diagramPanel?.classList.add('hidden');
      diagramPanel?.classList.remove('active');
    } else {
      textPanel?.classList.add('hidden');
      textPanel?.classList.remove('active');
      diagramPanel?.classList.remove('hidden');
      diagramPanel?.classList.add('active');
    }
  },

  /**
   * 渲染Mermaid图表
   */
  async renderDiagram(moduleId) {
    console.log(`🎨 渲染图表: ${moduleId}`);
    
    const codeElement = document.getElementById(`${moduleId}-diagram-code`);
    const previewElement = document.getElementById(`${moduleId}-diagram-preview`);
    
    if (!codeElement || !previewElement) {
      console.error('找不到图表元素');
      return;
    }
    
    const code = codeElement.value.trim();
    
    if (!code) {
      previewElement.innerHTML = `
        <div class="text-gray-400 text-center mt-40">
          <i class="fas fa-exclamation-circle text-4xl mb-2"></i>
          <p class="text-sm">请先输入Mermaid代码</p>
        </div>
      `;
      return;
    }
    
    try {
      // 清空预览区
      previewElement.innerHTML = '';
      
      // 创建临时元素
      const tempId = `mermaid-${moduleId}-${Date.now()}`;
      const tempDiv = document.createElement('div');
      tempDiv.id = tempId;
      tempDiv.className = 'mermaid';
      tempDiv.textContent = code;
      previewElement.appendChild(tempDiv);
      
      // 渲染图表
      await mermaid.run({
        nodes: [tempDiv]
      });
      
      console.log('✅ 图表渲染成功');
      ReviewSystem.showNotification('图表渲染成功', 'success');
      
    } catch (error) {
      console.error('图表渲染失败:', error);
      previewElement.innerHTML = `
        <div class="text-red-500 text-center mt-40">
          <i class="fas fa-times-circle text-4xl mb-2"></i>
          <p class="text-sm font-semibold">图表渲染失败</p>
          <p class="text-xs mt-2">${error.message}</p>
          <div class="mt-4 text-left bg-red-50 p-3 rounded text-xs">
            <pre class="whitespace-pre-wrap">${error.stack || error}</pre>
          </div>
        </div>
      `;
      ReviewSystem.showNotification('图表渲染失败: ' + error.message, 'error');
    }
  },

  /**
   * 使用LLM生成图表
   */
  async generateDiagram(moduleId, diagramType) {
    console.log(`🤖 生成图表: ${moduleId}, 类型: ${diagramType}`);
    
    const textArea = document.getElementById(moduleId);
    const content = textArea?.value.trim();
    
    if (!content) {
      ReviewSystem.showNotification('请先填写文本内容', 'warning');
      return;
    }
    
    // 切换到图表视图
    this.switchTab(moduleId, 'diagram');
    
    // 显示加载提示
    ReviewSystem.showNotification('正在生成图表，请稍候...', 'info');
    
    try {
      const response = await fetch('/api/v1/review/generate-diagram', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          content: content,
          diagram_type: diagramType,
          module_id: moduleId
        })
      });
      
      if (!response.ok) {
        throw new Error('图表生成请求失败');
      }
      
      const result = await response.json();
      
      if (result.success && result.diagram_code) {
        // 填充图表代码
        const codeElement = document.getElementById(`${moduleId}-diagram-code`);
        if (codeElement) {
          codeElement.value = result.diagram_code;
        }
        
        // 自动渲染
        await this.renderDiagram(moduleId);
        
        ReviewSystem.showNotification('图表生成成功！', 'success');
      } else {
        throw new Error(result.error || '图表生成失败');
      }
      
    } catch (error) {
      console.error('生成图表失败:', error);
      ReviewSystem.showNotification('生成图表失败: ' + error.message, 'error');
      
      // 提供默认模板
      const templates = this.getDefaultTemplates(diagramType);
      const codeElement = document.getElementById(`${moduleId}-diagram-code`);
      if (codeElement && templates) {
        codeElement.value = templates;
        ReviewSystem.showNotification('已加载默认模板，请手动编辑', 'info');
      }
    }
  },

  /**
   * 获取默认图表模板
   */
  getDefaultTemplates(diagramType) {
    const templates = {
      usecase: `graph TD
    A[用户] -->|使用| B(系统功能)
    A -->|查询| C(数据查询)
    A -->|管理| D(配置管理)
    
    B --> E{验证权限}
    E -->|通过| F[执行操作]
    E -->|拒绝| G[返回错误]
    
    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#fff4e1
    style D fill:#fff4e1`,
      
      component: `graph TB
    subgraph "前端层"
        UI[用户界面]
        Controller[控制器]
    end
    
    subgraph "业务层"
        Service[业务服务]
        Logic[业务逻辑]
    end
    
    subgraph "数据层"
        DAO[数据访问对象]
        DB[(数据库)]
    end
    
    UI --> Controller
    Controller --> Service
    Service --> Logic
    Logic --> DAO
    DAO --> DB
    
    style UI fill:#e1f5ff
    style Service fill:#fff4e1
    style DB fill:#ffe1e1`,
      
      class: `classDiagram
    class User {
        +String username
        +String email
        +String password
        +login()
        +logout()
        +updateProfile()
    }
    
    class Database {
        +Connection conn
        +query(sql)
        +execute(sql)
        +close()
    }
    
    class Service {
        +processRequest()
        +validateData()
        +handleError()
    }
    
    User --> Service
    Service --> Database`,
      
      sequence: `sequenceDiagram
    participant User as 用户
    participant UI as 界面
    participant Service as 服务层
    participant DB as 数据库
    
    User->>UI: 发起请求
    UI->>Service: 转发请求
    Service->>DB: 查询数据
    DB-->>Service: 返回数据
    Service-->>UI: 处理结果
    UI-->>User: 显示结果`,
      
      flowchart: `graph LR
    A[需求分析] --> B[架构设计]
    B --> C[详细设计]
    C --> D[代码实现]
    D --> E[测试验证]
    E --> F{测试通过?}
    F -->|是| G[发布上线]
    F -->|否| C
    
    style A fill:#e1f5ff
    style G fill:#e1ffe1
    style F fill:#fff4e1`
    };
    
    return templates[diagramType] || templates.flowchart;
  },

  /**
   * 导出图表为图片
   */
  async exportDiagramAsImage(moduleId) {
    const previewElement = document.getElementById(`${moduleId}-diagram-preview`);
    const svgElement = previewElement?.querySelector('svg');
    
    if (!svgElement) {
      ReviewSystem.showNotification('没有可导出的图表', 'warning');
      return;
    }
    
    try {
      // 获取SVG内容
      const svgData = new XMLSerializer().serializeToString(svgElement);
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        // 转换为PNG并下载
        canvas.toBlob(blob => {
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `${moduleId}-diagram-${Date.now()}.png`;
          link.click();
          URL.revokeObjectURL(url);
          
          ReviewSystem.showNotification('图表已导出', 'success');
        });
      };
      
      img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
      
    } catch (error) {
      console.error('导出图表失败:', error);
      ReviewSystem.showNotification('导出失败: ' + error.message, 'error');
    }
  },

  /**
   * 保存图表代码到localStorage
   */
  saveDiagramCode(moduleId) {
    const codeElement = document.getElementById(`${moduleId}-diagram-code`);
    if (codeElement) {
      const code = codeElement.value;
      localStorage.setItem(`diagram_${moduleId}`, code);
      ReviewSystem.showNotification('图表代码已保存', 'success');
    }
  },

  /**
   * 加载图表代码从localStorage
   */
  loadDiagramCode(moduleId) {
    const saved = localStorage.getItem(`diagram_${moduleId}`);
    if (saved) {
      const codeElement = document.getElementById(`${moduleId}-diagram-code`);
      if (codeElement) {
        codeElement.value = saved;
        this.renderDiagram(moduleId);
        ReviewSystem.showNotification('已加载保存的图表', 'success');
      }
    }
  },

  /**
   * 基于图表生成代码（核心功能）
   */
  async generateCodeFromDiagram(moduleId) {
    console.log(`🎯 基于图表生成代码: ${moduleId}`);
    
    const diagramCodeElement = document.getElementById(`${moduleId}-diagram-code`);
    const diagramCode = diagramCodeElement?.value.trim();
    
    if (!diagramCode) {
      ReviewSystem.showNotification('请先生成或编辑图表', 'warning');
      return;
    }
    
    // 获取文本描述（作为补充信息）
    const textElement = document.getElementById(moduleId);
    const textContent = textElement?.value.trim() || '';
    
    // 显示加载提示
    ReviewSystem.showNotification('正在基于图表生成代码，请稍候...', 'info');
    
    try {
      const response = await fetch('/api/v1/review/code-from-diagram', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          diagram_code: diagramCode,
          text_content: textContent,
          module_id: moduleId,
          diagram_type: this.diagramTypes[moduleId]?.type
        })
      });
      
      if (!response.ok) {
        throw new Error('代码生成请求失败');
      }
      
      const result = await response.json();
      
      if (result.success && result.generated_code) {
        // 显示生成的代码
        this.showGeneratedCode(moduleId, result);
        ReviewSystem.showNotification('代码生成成功！', 'success');
      } else {
        throw new Error(result.error || '代码生成失败');
      }
      
    } catch (error) {
      console.error('基于图表生成代码失败:', error);
      ReviewSystem.showNotification('代码生成失败: ' + error.message, 'error');
    }
  },

  /**
   * 显示生成的代码
   */
  showGeneratedCode(moduleId, result) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
    modal.innerHTML = `
      <div class="bg-white rounded-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <div class="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
          <h3 class="text-xl font-semibold text-gray-900">
            <i class="fas fa-code text-blue-600 mr-2"></i>
            基于图表生成的代码
          </h3>
          <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[70vh]">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h4 class="font-semibold text-blue-900 mb-2">
              <i class="fas fa-lightbulb mr-2"></i>生成说明
            </h4>
            <p class="text-sm text-blue-800">${result.explanation || '代码已基于UML图表结构生成，请验证其正确性。'}</p>
          </div>
          
          <div class="code-block rounded-lg overflow-hidden">
            <div class="flex items-center justify-between px-4 py-2 bg-slate-800">
              <div class="flex items-center gap-2">
                <i class="fas fa-file-code text-blue-400"></i>
                <span class="text-gray-300 text-sm font-mono">generated_code.py</span>
              </div>
              <button onclick="navigator.clipboard.writeText(this.dataset.code).then(() => ReviewSystem.showNotification('代码已复制', 'success'))" 
                      data-code="${result.generated_code.replace(/"/g, '&quot;')}"
                      class="text-gray-400 hover:text-white transition-colors">
                <i class="fas fa-copy"></i>
              </button>
            </div>
            <pre class="p-4 overflow-auto max-h-96 font-mono text-sm">${this.escapeHtml(result.generated_code)}</pre>
          </div>
          
          ${result.suggestions && result.suggestions.length > 0 ? `
            <div class="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-4">
              <h4 class="font-semibold text-amber-900 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>注意事项
              </h4>
              <ul class="list-disc list-inside space-y-1 text-sm text-amber-800">
                ${result.suggestions.map(s => `<li>${this.escapeHtml(s)}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
        </div>
        <div class="p-6 border-t border-gray-200 bg-gray-50 flex gap-3">
          <button 
            onclick="navigator.clipboard.writeText(this.dataset.code).then(() => { ReviewSystem.showNotification('代码已复制到剪贴板', 'success'); this.closest('.fixed').remove(); })"
            data-code="${result.generated_code.replace(/"/g, '&quot;')}"
            class="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg transition-colors"
          >
            <i class="fas fa-copy mr-2"></i>复制代码
          </button>
          <button 
            onclick="this.closest('.fixed').remove()"
            class="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
  },

  /**
   * HTML转义
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },

  /**
   * 验证图表一致性
   */
  async validateConsistency() {
    console.log('🔍 验证图表一致性...');
    
    const modules = ['detailedRequirement', 'architectureDesign', 'detailedDesign'];
    const diagrams = {};
    
    // 收集所有图表
    for (const moduleId of modules) {
      const codeElement = document.getElementById(`${moduleId}-diagram-code`);
      if (codeElement && codeElement.value.trim()) {
        diagrams[moduleId] = codeElement.value;
      }
    }
    
    if (Object.keys(diagrams).length < 2) {
      ReviewSystem.showNotification('至少需要2个图表才能验证一致性', 'warning');
      return;
    }
    
    ReviewSystem.showNotification('正在验证图表一致性...', 'info');
    
    try {
      const response = await fetch('/api/v1/review/validate-consistency', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ diagrams })
      });
      
      if (!response.ok) {
        throw new Error('一致性验证请求失败');
      }
      
      const result = await response.json();
      
      // 显示验证结果
      this.showValidationResult(result);
      
    } catch (error) {
      console.error('一致性验证失败:', error);
      ReviewSystem.showNotification('验证失败: ' + error.message, 'error');
    }
  },

  /**
   * 显示验证结果
   */
  showValidationResult(result) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
    
    const statusColor = result.is_consistent ? 'green' : 'red';
    const statusIcon = result.is_consistent ? 'fa-check-circle' : 'fa-exclamation-triangle';
    
    modal.innerHTML = `
      <div class="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
        <div class="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 class="text-xl font-semibold text-gray-900">
            <i class="fas fa-check-double text-${statusColor}-600 mr-2"></i>
            图表一致性验证结果
          </h3>
          <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[70vh]">
          <div class="bg-${statusColor}-50 border border-${statusColor}-200 rounded-lg p-4 mb-4">
            <div class="flex items-center gap-3">
              <i class="fas ${statusIcon} text-${statusColor}-600 text-2xl"></i>
              <div>
                <h4 class="font-semibold text-${statusColor}-900">
                  ${result.is_consistent ? '图表一致性良好' : '发现一致性问题'}
                </h4>
                <p class="text-sm text-${statusColor}-800 mt-1">
                  ${result.message || '请查看详细报告'}
                </p>
              </div>
            </div>
          </div>
          
          ${result.issues && result.issues.length > 0 ? `
            <div class="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
              <h4 class="font-semibold text-amber-900 mb-2">
                <i class="fas fa-exclamation-circle mr-2"></i>发现的问题
              </h4>
              <ul class="list-disc list-inside space-y-1 text-sm text-amber-800">
                ${result.issues.map(issue => `<li>${this.escapeHtml(issue)}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
          
          ${result.suggestions && result.suggestions.length > 0 ? `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 class="font-semibold text-blue-900 mb-2">
                <i class="fas fa-lightbulb mr-2"></i>改进建议
              </h4>
              <ul class="list-disc list-inside space-y-1 text-sm text-blue-800">
                ${result.suggestions.map(s => `<li>${this.escapeHtml(s)}</li>`).join('')}
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
   * 一键生成完整流程（需求→图表→代码）
   */
  async generateFullWorkflow() {
    if (!confirm('即将执行完整的图表驱动代码生成流程：\n\n1. 从需求生成用例图\n2. 从架构生成组件图\n3. 从设计生成类图\n4. 验证图表一致性\n5. 基于图表生成代码\n\n是否继续？')) {
      return;
    }
    
    ReviewSystem.showNotification('开始完整工作流，请耐心等待...', 'info');
    
    const workflow = [
      { module: 'detailedRequirement', type: 'usecase', name: '用例图' },
      { module: 'architectureDesign', type: 'component', name: '组件图' },
      { module: 'detailedDesign', type: 'class', name: '类图' }
    ];
    
    let successCount = 0;
    
    try {
      // 步骤1-3: 生成所有图表
      for (const step of workflow) {
        const textElement = document.getElementById(step.module);
        if (textElement && textElement.value.trim()) {
          try {
            await this.generateDiagram(step.module, step.type);
            successCount++;
            ReviewSystem.showNotification(`✓ ${step.name}生成完成`, 'success');
            await new Promise(resolve => setTimeout(resolve, 2000));
          } catch (error) {
            console.error(`${step.name}生成失败:`, error);
          }
        }
      }
      
      // 步骤4: 验证一致性
      if (successCount >= 2) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await this.validateConsistency();
      }
      
      // 步骤5: 基于类图生成代码
      const classDigramCode = document.getElementById('detailedDesign-diagram-code')?.value;
      if (classDigramCode && classDigramCode.trim()) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await this.generateCodeFromDiagram('detailedDesign');
      }
      
      ReviewSystem.showNotification(`完整工作流执行完成！生成了${successCount}个图表`, 'success');
      
    } catch (error) {
      console.error('完整工作流执行失败:', error);
      ReviewSystem.showNotification('工作流执行失败: ' + error.message, 'error');
    }
  }
};

// 页面加载完成后初始化
window.addEventListener('load', function() {
  DiagramSystem.init();
  console.log('✅ DiagramSystem初始化完成');
});

// 使DiagramSystem全局可用
window.DiagramSystem = DiagramSystem;

