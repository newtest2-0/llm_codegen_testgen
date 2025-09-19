const API_BASE = "http://localhost:8000";

// 测试JavaScript是否正常加载
console.log('🚀 main.js 开始加载...');
window.addEventListener('load', function() {
  console.log('📱 页面完全加载完成');
});

async function getHealth(){
  console.log('开始健康检查...', API_BASE);
  const sysElement = document.getElementById("sys");
  
  if (!sysElement) {
    console.error('找不到sys元素');
    return;
  }
  
  try {
    const r = await fetch(API_BASE + "/health");
    console.log('健康检查响应状态:', r.status);
    
    if (!r.ok) {
      throw new Error(`HTTP ${r.status}`);
    }
    
    const j = await r.json();
    console.log('健康检查成功:', j);
    
      sysElement.innerHTML = `
    <div class="flex items-center gap-2 text-green-600 text-sm">
      <div class="w-2 h-2 bg-green-500 rounded-full"></div>
      <span>服务在线</span>
    </div>
    <div class="text-gray-500 text-xs mt-1">模型: ${j.providers.join(", ")}</div>
  `;
  } catch(e){
    console.error('健康检查失败:', e);
    sysElement.innerHTML = `
      <div class="flex items-center gap-2 text-red-600 text-sm">
        <div class="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
        <span>连接失败</span>
      </div>
      <div class="text-gray-500 text-xs mt-1">错误: ${e.message || e}</div>
    `;
  }
}

function escapeHtml(s){ return s.replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[m])); }

function displayTests(testsCode) {
  console.log('显示测试用例:', testsCode);
  
  const testsSection = document.getElementById("testsSection");
  const testsCodeElement = document.getElementById("testsCode");
  const testInfo = document.getElementById("testInfo");
  const testStatus = document.getElementById("testStatus");
  
  if (!testsSection || !testsCodeElement) {
    console.error('找不到测试展示元素');
    return;
  }
  
  // 显示测试代码
  testsCodeElement.textContent = testsCode;
  
  // 分析测试代码信息
  const testLines = testsCode.split('\n');
  const testFunctions = testLines.filter(line => line.trim().startsWith('def test_')).length;
  const hasEdgeCases = testsCode.includes('edge') || testsCode.includes('boundary') || testsCode.includes('边界');
  const hasExceptions = testsCode.includes('pytest.raises') || testsCode.includes('Exception') || testsCode.includes('异常');
  
  // 更新测试信息
  testInfo.innerHTML = `
    <div class="flex justify-between">
      <span>生成方式:</span>
      <span class="font-medium text-blue-600">智能分析代码结构</span>
    </div>
    <div class="flex justify-between">
      <span>测试框架:</span>
      <span class="font-medium">pytest</span>
    </div>
    <div class="flex justify-between">
      <span>测试函数:</span>
      <span class="font-medium text-green-600">${testFunctions} 个</span>
    </div>
    <div class="flex justify-between">
      <span>边界测试:</span>
      <span class="font-medium ${hasEdgeCases ? 'text-green-600' : 'text-gray-400'}">${hasEdgeCases ? '✓ 包含' : '✗ 无'}</span>
    </div>
    <div class="flex justify-between">
      <span>异常测试:</span>
      <span class="font-medium ${hasExceptions ? 'text-green-600' : 'text-gray-400'}">${hasExceptions ? '✓ 包含' : '✗ 无'}</span>
    </div>
  `;
  
  // 更新测试状态
  testStatus.innerHTML = `
    <div class="text-green-600">
      <i class="fas fa-check-circle text-2xl mb-2"></i>
      <p class="font-medium">测试用例生成完成</p>
      <p class="text-sm text-gray-500 mt-1">包含 ${testFunctions} 个测试函数</p>
    </div>
  `;
  
  // 显示测试区域
  testsSection.classList.remove('hidden');
  
  // 滚动到测试区域
  setTimeout(() => {
    testsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 500);
}

// 复制测试代码功能
function initCopyTestsButton() {
  const copyBtn = document.getElementById('copyTestsBtn');
  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      const testsCode = document.getElementById('testsCode').textContent;
      try {
        await navigator.clipboard.writeText(testsCode);
        
        // 显示复制成功提示
        const originalIcon = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check text-green-400"></i>';
        copyBtn.title = '已复制！';
        
        setTimeout(() => {
          copyBtn.innerHTML = originalIcon;
          copyBtn.title = '复制代码';
        }, 2000);
        
      } catch (err) {
        console.error('复制失败:', err);
        alert('复制失败，请手动选择代码复制');
      }
    });
  }
}

function card(result){
  const m = result.metrics;
  const scoreColor = m.aggregate_score >= 0.8 ? 'text-green-600' : 
                     m.aggregate_score >= 0.6 ? 'text-yellow-600' : 
                     'text-red-600';
  
  const scoreBg = m.aggregate_score >= 0.8 ? 'bg-green-50 border-green-200' : 
                  m.aggregate_score >= 0.6 ? 'bg-yellow-50 border-yellow-200' : 
                  'bg-red-50 border-red-200';
  
  const modelIcons = {
    'openai': '🤖',
    'deepseek': '🔍', 
    'claude': '🎭',
    'gemini': '💎',
    'qwen': '🌟',
    'baichuan': '🏔️',
    'chatglm': '💬',
    'llama': '🦙'
  };
  
  return `
  <div class="surface-card rounded-xl p-6 hover:shadow-lg transition-all duration-200">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
          <span class="text-lg">${modelIcons[result.provider] || '🤖'}</span>
        </div>
        <div>
          <h3 class="font-semibold text-gray-900">${result.provider}</h3>
          <p class="text-gray-500 text-sm">${result.model}</p>
        </div>
      </div>
      <div class="text-right">
        <div class="px-3 py-1 ${scoreBg} border rounded-lg">
          <div class="font-semibold ${scoreColor}">${m.aggregate_score.toFixed(3)}</div>
        </div>
        <div class="text-gray-400 text-xs mt-1">综合评分</div>
      </div>
    </div>
    
    <div class="grid grid-cols-2 gap-4 mb-6">
      <div class="bg-gray-50 rounded-lg p-4">
        <h4 class="font-medium text-gray-900 mb-3 text-sm">性能指标</h4>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-gray-600">BLEU</span>
            <span class="font-medium text-gray-900">${m.bleu.toFixed(3)}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">AST</span>
            <span class="font-medium ${m.ast_parse_ok ? 'text-green-600' : 'text-red-600'}">${m.ast_parse_ok ? "✓" : "✗"}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">复杂度</span>
            <span class="font-medium text-gray-900">${m.cyclomatic.toFixed(1)}</span>
          </div>
        </div>
      </div>
      
      <div class="bg-gray-50 rounded-lg p-4">
        <h4 class="font-medium text-gray-900 mb-3 text-sm">测试结果</h4>
        <div class="space-y-2 text-sm">
          ${m.tests.supported ? `
            <div class="flex justify-between">
              <span class="text-gray-600">通过</span>
              <span class="font-medium text-green-600">${m.tests.passed}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">失败</span>
              <span class="font-medium text-red-600">${m.tests.failed}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">退出码</span>
              <span class="font-medium text-gray-900">${m.tests.exit_code}</span>
            </div>
          ` : `
            <div class="text-center text-gray-500">
              <div class="text-xs">测试不支持</div>
            </div>
          `}
        </div>
      </div>
    </div>
    
    <details class="group">
      <summary class="cursor-pointer flex items-center gap-3 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
        <i class="fas fa-code text-gray-600"></i>
        <span class="font-medium text-gray-900">查看代码</span>
        <i class="fas fa-chevron-down group-open:rotate-180 transition-transform ml-auto text-gray-400"></i>
      </summary>
      <div class="mt-4">
        <div class="code-block rounded-lg overflow-hidden">
          <div class="px-4 py-2 bg-slate-800">
            <span class="text-gray-300 text-sm font-mono">${result.provider}.py</span>
          </div>
          <pre class="p-4 overflow-auto max-h-80 font-mono text-sm">${escapeHtml(result._code || "")}</pre>
        </div>
      </div>
    </details>
    
    ${result.code_path ? `
      <div class="mt-4 p-3 bg-blue-50 rounded-xl border border-blue-200">
        <div class="flex items-center gap-2 text-blue-600 text-xs">
          <i class="fas fa-folder-open"></i>
          <span>代码路径</span>
        </div>
        <div class="text-blue-800 text-xs mt-1 break-all font-mono">${result.code_path}</div>
      </div>
    ` : ''}
  </div>`;
}

document.getElementById("runBtn").addEventListener("click", async () => {
  console.log('点击了生成按钮');
  
  // 清空之前的结果
  const resultsDiv = document.getElementById("results");
  const winnerDiv = document.getElementById("winner");
  const testsDiv = document.getElementById("testsSection");
  
  resultsDiv.innerHTML = '';
  winnerDiv.classList.add('hidden');
  testsDiv.classList.add('hidden');
  
  const requirement = document.getElementById("requirement").value.trim();
  const language = document.getElementById("language").value;
  const extra = document.getElementById("extra").value.trim();
  
  console.log('需求描述:', requirement);
  console.log('编程语言:', language);
  console.log('额外要求:', extra);
  
  // 获取选中的模型提供者
  const selectedProviders = Array.from(document.querySelectorAll('.provider-checkbox:checked')).map(cb => cb.value);
  console.log('选中的模型:', selectedProviders);
  
  if(!requirement){ 
    alert("请填写需求描述"); 
    console.log('需求描述为空，停止执行');
    return; 
  }

  const genBody = {
    requirement, language,
    providers: selectedProviders.length > 0 ? selectedProviders : null,
    extra_directives: extra || null
  };

  console.log('准备发送生成请求:', genBody);

  try {
    const genResponse = await fetch(API_BASE + "/api/v1/generation/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(genBody)
    });
    
    console.log('生成请求响应状态:', genResponse.status);
    
    if (!genResponse.ok) {
      throw new Error(`生成请求失败: ${genResponse.status} ${genResponse.statusText}`);
    }
    
    const gen = await genResponse.json();
    console.log('生成请求成功:', gen);

    // 显示测试用例
    if (gen.tests_code) {
      displayTests(gen.tests_code);
    }

    const artifacts = gen.artifacts.map(a => ({...a, _code: a.code}));
    console.log('处理生成的代码:', artifacts);

    const evalBody = { session_id: gen.session_id, artifacts, tests_code: gen.tests_code, language };
    console.log('准备发送评测请求:', evalBody);
    
    const evalResponse = await fetch(API_BASE + "/api/v1/evaluation/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(evalBody)
    });
    
    console.log('评测请求响应状态:', evalResponse.status);
    
    if (!evalResponse.ok) {
      throw new Error(`评测请求失败: ${evalResponse.status} ${evalResponse.statusText}`);
    }
    
    const ev = await evalResponse.json();
    console.log('评测请求成功:', ev);

    ev.results.forEach((r,i)=>{ r._code = artifacts[i]._code; });

    const best = ev.best;
    const winner = document.getElementById("winner");
    winner.classList.remove("hidden");
    document.getElementById("winnerMeta").textContent = JSON.stringify(best, null, 2);
    document.getElementById("winnerCode").textContent = artifacts.find(a => a.provider===best.provider)._code;

    const html = ev.results
      .sort((a,b)=>b.metrics.aggregate_score - a.metrics.aggregate_score)
      .map(card).join("\\n");
    document.getElementById("results").innerHTML = html;
    
    console.log('✅ 完整流程执行成功！');
    
  } catch (error) {
    console.error('❌ 代码生成流程失败:', error);
    alert('代码生成失败: ' + error.message);
  }
});

// 添加全选/取消全选功能和交互增强
function addSelectAllButton() {
  const gridContainer = document.querySelector('.grid.grid-cols-2.md\\:grid-cols-4');
  if (gridContainer) {
    const selectAllContainer = document.createElement('div');
    selectAllContainer.className = 'flex items-center justify-between mb-4';
    selectAllContainer.innerHTML = `
      <div class="flex items-center gap-3">
        <button id="selectAllBtn" class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-all duration-300 text-sm font-medium">
          <i class="fas fa-check-double mr-2"></i>全选
        </button>
        <button id="deselectAllBtn" class="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-all duration-300 text-sm font-medium">
          <i class="fas fa-times mr-2"></i>取消全选
        </button>
      </div>
      <div class="flex items-center gap-2 bg-gray-100 px-3 py-2 rounded-lg border border-gray-200">
        <i class="fas fa-info-circle text-blue-500"></i>
        <span class="text-gray-700 text-sm" id="selectedCount">已选择：2个模型</span>
      </div>
    `;
    gridContainer.parentNode.insertBefore(selectAllContainer, gridContainer);
    
    // 绑定事件
    document.getElementById('selectAllBtn').addEventListener('click', () => {
      document.querySelectorAll('.provider-checkbox').forEach(cb => cb.checked = true);
      updateSelectedCount();
    });
    
    document.getElementById('deselectAllBtn').addEventListener('click', () => {
      document.querySelectorAll('.provider-checkbox').forEach(cb => cb.checked = false);
      updateSelectedCount();
    });
    
    // 监听复选框变化和卡片交互
    document.querySelectorAll('.provider-checkbox').forEach(cb => {
      cb.addEventListener('change', function() {
        updateSelectedCount();
        updateCardState(this);
      });
      // 初始化卡片状态
      updateCardState(cb);
    });
    
    // 更新选择数量显示
    function updateSelectedCount() {
      const count = document.querySelectorAll('.provider-checkbox:checked').length;
      document.getElementById('selectedCount').textContent = `已选择：${count}个模型`;
    }
    
    // 更新卡片状态
    function updateCardState(checkbox) {
      const card = checkbox.closest('.provider-card');
      if (card) {
        if (checkbox.checked) {
          card.classList.add('selected');
        } else {
          card.classList.remove('selected');
        }
      }
    }
    
    // 初始化计数
    updateSelectedCount();
  }
}

// 添加页面加载动画
function initPageAnimations() {
  // 监听页面滚动，添加渐入效果
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-fade-in-up');
      }
    });
  }, observerOptions);
  
  // 观察所有需要动画的元素
  document.querySelectorAll('.qwen-card').forEach(card => {
    observer.observe(card);
  });
}

// 等待DOM加载完成后添加功能
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM加载完成，开始初始化...');
  addSelectAllButton();
  initPageAnimations();
  initCopyTestsButton();
  
  // 延迟执行健康检查，确保所有元素都已渲染
  setTimeout(() => {
    console.log('开始执行健康检查...');
    getHealth();
  }, 500);
});

// 页面完全加载后也执行一次
window.addEventListener('load', function() {
  console.log('页面完全加载，再次执行健康检查...');
  setTimeout(getHealth, 1000);
});

// ===========================================
// 新增功能：历史记录、导出代码、设置
// ===========================================

// 存储相关功能
const Storage = {
  // 保存生成历史
  saveHistory: function(data) {
    try {
      let history = this.getHistory();
      const historyItem = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        requirement: data.requirement,
        language: data.language,
        providers: data.providers,
        results: data.results,
        testsCode: data.testsCode,
        winner: data.winner
      };
      
      history.unshift(historyItem); // 添加到开头
      
      // 限制历史记录数量（最多保存50条）
      if (history.length > 50) {
        history = history.slice(0, 50);
      }
      
      localStorage.setItem('codeforge_history', JSON.stringify(history));
      console.log('历史记录已保存');
    } catch (error) {
      console.error('保存历史记录失败:', error);
    }
  },

  // 获取历史记录
  getHistory: function() {
    try {
      const history = localStorage.getItem('codeforge_history');
      return history ? JSON.parse(history) : [];
    } catch (error) {
      console.error('获取历史记录失败:', error);
      return [];
    }
  },

  // 删除历史记录
  deleteHistory: function(id) {
    try {
      let history = this.getHistory();
      history = history.filter(item => item.id !== id);
      localStorage.setItem('codeforge_history', JSON.stringify(history));
      console.log('历史记录已删除');
    } catch (error) {
      console.error('删除历史记录失败:', error);
    }
  },

  // 清空所有历史记录
  clearHistory: function() {
    try {
      localStorage.removeItem('codeforge_history');
      console.log('所有历史记录已清空');
    } catch (error) {
      console.error('清空历史记录失败:', error);
    }
  },

  // 保存设置
  saveSettings: function(settings) {
    try {
      localStorage.setItem('codeforge_settings', JSON.stringify(settings));
      console.log('设置已保存');
    } catch (error) {
      console.error('保存设置失败:', error);
    }
  },

  // 获取设置
  getSettings: function() {
    try {
      const settings = localStorage.getItem('codeforge_settings');
      return settings ? JSON.parse(settings) : {
        apiKeys: {},
        defaultLanguage: 'python',
        autoSaveHistory: true,
        showNotifications: true
      };
    } catch (error) {
      console.error('获取设置失败:', error);
      return {};
    }
  }
};

// 历史记录功能
const HistoryManager = {
  // 显示历史记录模态框
  show: function() {
    const modal = document.getElementById('historyModal');
    const historyList = document.getElementById('historyList');
    
    // 获取历史记录
    const history = Storage.getHistory();
    
    // 清空列表
    historyList.innerHTML = '';
    
    if (history.length === 0) {
      historyList.innerHTML = `
        <div class="text-center py-12">
          <i class="fas fa-history text-gray-300 text-4xl mb-4"></i>
          <p class="text-gray-500">暂无历史记录</p>
        </div>
      `;
    } else {
      // 渲染历史记录
      history.forEach(item => {
        const historyItem = this.createHistoryItem(item);
        historyList.appendChild(historyItem);
      });
    }
    
    modal.classList.remove('hidden');
  },

  // 创建历史记录项
  createHistoryItem: function(item) {
    const div = document.createElement('div');
    div.className = 'bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors';
    
    const date = new Date(item.timestamp).toLocaleString('zh-CN');
    const resultsCount = item.results ? item.results.length : 0;
    
    div.innerHTML = `
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-2">
            <span class="text-sm font-medium text-gray-900">${item.language}</span>
            <span class="text-xs text-gray-500">${date}</span>
          </div>
          <p class="text-gray-700 mb-2 line-clamp-2">${item.requirement}</p>
          <div class="flex items-center gap-4 text-xs text-gray-500">
            <span><i class="fas fa-robot mr-1"></i>${item.providers?.length || 0} 个模型</span>
            <span><i class="fas fa-code mr-1"></i>${resultsCount} 个结果</span>
          </div>
        </div>
        <div class="flex items-center gap-2 ml-4">
          <button onclick="HistoryManager.loadHistory(${item.id})" class="text-blue-600 hover:text-blue-800 text-sm">
            <i class="fas fa-redo mr-1"></i>重新生成
          </button>
          <button onclick="HistoryManager.deleteItem(${item.id})" class="text-red-600 hover:text-red-800 text-sm">
            <i class="fas fa-trash mr-1"></i>删除
          </button>
        </div>
      </div>
    `;
    
    return div;
  },

  // 加载历史记录到当前表单
  loadHistory: function(id) {
    const history = Storage.getHistory();
    const item = history.find(h => h.id === id);
    
    if (item) {
      // 填充表单
      document.getElementById('requirement').value = item.requirement;
      document.getElementById('language').value = item.language;
      
      // 选择对应的模型
      if (item.providers) {
        const checkboxes = document.querySelectorAll('.provider-checkbox');
        checkboxes.forEach(checkbox => {
          checkbox.checked = item.providers.includes(checkbox.value);
        });
        // updateSelectedCount(); // 注释掉不存在的函数调用
      }
      
      // 关闭模态框
      this.hide();
      
      // 显示通知
      this.showNotification('历史记录已加载到表单');
    }
  },

  // 删除历史记录项
  deleteItem: function(id) {
    if (confirm('确定要删除这条历史记录吗？')) {
      Storage.deleteHistory(id);
      this.show(); // 重新加载列表
      this.showNotification('历史记录已删除');
    }
  },

  // 隐藏模态框
  hide: function() {
    document.getElementById('historyModal').classList.add('hidden');
  },

  // 显示通知
  showNotification: function(message) {
    // 简单的通知实现
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg z-50 transition-opacity';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 2000);
  }
};

// 导出功能
const ExportManager = {
  currentData: null,

  // 显示导出模态框
  show: function() {
    // 检查是否有可导出的数据
    const results = document.getElementById('results');
    if (!results || results.children.length === 0) {
      alert('暂无可导出的代码，请先生成代码。');
      return;
    }

    // 收集当前页面的数据
    this.collectCurrentData();
    
    document.getElementById('exportModal').classList.remove('hidden');
  },

  // 收集当前数据
  collectCurrentData: function() {
    const requirement = document.getElementById('requirement').value;
    const language = document.getElementById('language').value;
    
    // 收集生成的代码
    const codeElements = document.querySelectorAll('[id$="Code"]');
    const codes = Array.from(codeElements).map(el => el.textContent).filter(code => code.trim());
    
    // 收集测试代码
    const testsCode = document.getElementById('testsCode')?.textContent || '';
    
    // 收集最优方案
    const winnerCode = document.getElementById('winnerCode')?.textContent || '';
    
    this.currentData = {
      requirement,
      language,
      codes,
      testsCode,
      winnerCode,
      timestamp: new Date().toISOString()
    };
  },

  // 执行导出
  export: function() {
    if (!this.currentData) {
      alert('没有可导出的数据');
      return;
    }

    const format = document.getElementById('exportFormat').value;
    const includeCode = document.getElementById('includeCode').checked;
    const includeTests = document.getElementById('includeTests').checked;
    const includeResults = document.getElementById('includeResults').checked;

    try {
      if (format === 'zip') {
        this.exportAsZip(includeCode, includeTests, includeResults);
      } else if (format === 'py') {
        this.exportAsPython(includeCode, includeTests);
      } else if (format === 'txt') {
        this.exportAsText(includeCode, includeTests, includeResults);
      }
      
      this.hide();
      this.showNotification('代码导出成功！');
    } catch (error) {
      console.error('导出失败:', error);
      alert('导出失败，请重试');
    }
  },

  // 导出为文本文件
  exportAsText: function(includeCode, includeTests, includeResults) {
    let content = `代码生成报告\n`;
    content += `生成时间: ${new Date(this.currentData.timestamp).toLocaleString('zh-CN')}\n`;
    content += `需求描述: ${this.currentData.requirement}\n`;
    content += `编程语言: ${this.currentData.language}\n\n`;
    
    if (includeCode && this.currentData.winnerCode) {
      content += `=== 推荐代码方案 ===\n`;
      content += this.currentData.winnerCode;
      content += `\n\n`;
    }
    
    if (includeCode && this.currentData.codes.length > 0) {
      content += `=== 所有生成的代码 ===\n`;
      this.currentData.codes.forEach((code, index) => {
        content += `--- 方案 ${index + 1} ---\n`;
        content += code;
        content += `\n\n`;
      });
    }
    
    if (includeTests && this.currentData.testsCode) {
      content += `=== 测试代码 ===\n`;
      content += this.currentData.testsCode;
      content += `\n\n`;
    }

    this.downloadFile(content, 'codeforge_export.txt', 'text/plain');
  },

  // 导出为Python文件
  exportAsPython: function(includeCode, includeTests) {
    let content = `# -*- coding: utf-8 -*-\n`;
    content += `"""\n代码生成结果\n`;
    content += `需求: ${this.currentData.requirement}\n`;
    content += `生成时间: ${new Date(this.currentData.timestamp).toLocaleString('zh-CN')}\n`;
    content += `"""\n\n`;
    
    if (includeCode && this.currentData.winnerCode) {
      content += this.currentData.winnerCode;
      content += `\n\n`;
    }
    
    if (includeTests && this.currentData.testsCode) {
      content += `# 测试代码\n`;
      content += this.currentData.testsCode;
    }

    this.downloadFile(content, 'codeforge_solution.py', 'text/python');
  },

  // 简化的ZIP导出（实际上导出为文本，因为浏览器环境限制）
  exportAsZip: function(includeCode, includeTests, includeResults) {
    // 在浏览器环境中，我们创建一个包含多个文件内容的文本文件
    let content = `CodeForge 导出包\n`;
    content += `================\n\n`;
    
    content += `文件清单:\n`;
    if (includeCode) content += `- solution.${this.getFileExtension()}\n`;
    if (includeTests) content += `- tests.py\n`;
    if (includeResults) content += `- report.txt\n`;
    content += `\n`;
    
    if (includeCode && this.currentData.winnerCode) {
      content += `=== solution.${this.getFileExtension()} ===\n`;
      content += this.currentData.winnerCode;
      content += `\n\n`;
    }
    
    if (includeTests && this.currentData.testsCode) {
      content += `=== tests.py ===\n`;
      content += this.currentData.testsCode;
      content += `\n\n`;
    }
    
    if (includeResults) {
      content += `=== report.txt ===\n`;
      content += `需求描述: ${this.currentData.requirement}\n`;
      content += `编程语言: ${this.currentData.language}\n`;
      content += `生成时间: ${new Date(this.currentData.timestamp).toLocaleString('zh-CN')}\n`;
      content += `生成结果数量: ${this.currentData.codes.length}\n`;
    }

    this.downloadFile(content, 'codeforge_package.txt', 'text/plain');
  },

  // 获取文件扩展名
  getFileExtension: function() {
    const extensions = {
      python: 'py',
      javascript: 'js',
      java: 'java',
      cpp: 'cpp',
      go: 'go'
    };
    return extensions[this.currentData.language] || 'txt';
  },

  // 下载文件
  downloadFile: function(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    URL.revokeObjectURL(url);
  },

  // 隐藏模态框
  hide: function() {
    document.getElementById('exportModal').classList.add('hidden');
  },

  // 显示通知
  showNotification: function(message) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-blue-500 text-white px-4 py-2 rounded-lg z-50 transition-opacity';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 2000);
  }
};

// 设置管理
const SettingsManager = {
  // 显示设置模态框
  show: function() {
    document.getElementById('settingsModal').classList.remove('hidden');
    
    // 加载当前设置
    const settings = Storage.getSettings();
    
    // 更新API状态显示
    this.updateApiStatuses(settings);
    
    // 填充API密钥到输入框
    this.loadApiKeys(settings);
    
    // 填充系统偏好
    document.getElementById('defaultLanguage').value = settings.defaultLanguage || 'python';
    document.getElementById('autoSaveHistory').checked = settings.autoSaveHistory !== false;
    document.getElementById('showNotifications').checked = settings.showNotifications !== false;
    
    // 绑定API配置面板事件
    this.bindApiEvents();
  },
  
  updateApiStatuses: function(settings) {
    const providers = ['openai', 'deepseek', 'claude', 'gemini', 'qwen', 'baichuan', 'chatglm'];
    
    providers.forEach(provider => {
      const statusElement = document.querySelector(`[data-provider="${provider}"] .api-status`);
      const keyExists = settings[`${provider}Key`] && settings[`${provider}Key`].trim();
      
      if (statusElement) {
        if (provider === 'llama') {
          // LLaMA是本地模型，状态不变
          return;
        }
        
        if (keyExists) {
          statusElement.className = 'api-status text-xs px-2 py-1 rounded-full bg-green-100 text-green-600';
          statusElement.textContent = '已配置';
        } else {
          statusElement.className = 'api-status text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600';
          statusElement.textContent = '未配置';
        }
      }
    });
  },
  
  loadApiKeys: function(settings) {
    const providers = ['openai', 'deepseek', 'claude', 'gemini', 'qwen', 'baichuan', 'chatglm'];
    
    providers.forEach(provider => {
      const input = document.querySelector(`[data-provider="${provider}"] .api-key-input`);
      if (input) {
        input.value = settings[`${provider}Key`] || '';
      }
    });
  },
  
  bindApiEvents: function() {
    // API提供商项目点击事件
    document.querySelectorAll('.api-provider-item').forEach(item => {
      const header = item.querySelector('.cursor-pointer');
      const panel = item.querySelector('.api-config-panel');
      const chevron = item.querySelector('.fa-chevron-right');
      
      if (header && panel && chevron) {
        header.addEventListener('click', () => {
          const isHidden = panel.classList.contains('hidden');
          
          // 关闭其他面板
          document.querySelectorAll('.api-config-panel').forEach(p => p.classList.add('hidden'));
          document.querySelectorAll('.fa-chevron-right').forEach(c => c.classList.remove('rotate-90'));
          
          if (isHidden) {
            panel.classList.remove('hidden');
            chevron.classList.add('rotate-90');
          }
        });
      }
    });
    
    // 密码可见性切换
    document.querySelectorAll('.toggle-visibility').forEach(button => {
      button.addEventListener('click', () => {
        const input = button.parentElement.querySelector('.api-key-input');
        const icon = button.querySelector('i');
        
        if (input.type === 'password') {
          input.type = 'text';
          icon.className = 'fas fa-eye-slash text-gray-500';
        } else {
          input.type = 'password';
          icon.className = 'fas fa-eye text-gray-500';
        }
      });
    });
    
    // 保存API密钥
    document.querySelectorAll('.save-api-key').forEach(button => {
      button.addEventListener('click', () => {
        const item = button.closest('.api-provider-item');
        const provider = item.dataset.provider;
        const input = item.querySelector('.api-key-input');
        const value = input.value.trim();
        
        // 获取当前设置
        const settings = Storage.getSettings();
        settings[`${provider}Key`] = value;
        
        // 保存设置
        Storage.saveSettings(settings);
        
        // 更新状态显示
        this.updateApiStatuses(settings);
        
        // 显示通知
        this.showNotification(`${provider.toUpperCase()} API Key 已保存`);
      });
    });
    
    // 清除API密钥
    document.querySelectorAll('.clear-api-key').forEach(button => {
      button.addEventListener('click', () => {
        const item = button.closest('.api-provider-item');
        const provider = item.dataset.provider;
        const input = item.querySelector('.api-key-input');
        
        if (confirm(`确定要清除 ${provider.toUpperCase()} 的API密钥吗？`)) {
          input.value = '';
          
          // 获取当前设置
          const settings = Storage.getSettings();
          delete settings[`${provider}Key`];
          
          // 保存设置
          Storage.saveSettings(settings);
          
          // 更新状态显示
          this.updateApiStatuses(settings);
          
          // 显示通知
          this.showNotification(`${provider.toUpperCase()} API Key 已清除`);
        }
      });
    });
  },

  // 保存设置
  save: function() {
    const settings = Storage.getSettings();
    
    // 保存系统偏好
    settings.defaultLanguage = document.getElementById('defaultLanguage').value;
    settings.autoSaveHistory = document.getElementById('autoSaveHistory').checked;
    settings.showNotifications = document.getElementById('showNotifications').checked;
    
    Storage.saveSettings(settings);
    this.hide();
    this.showNotification('系统设置已保存');
    
    // 应用默认语言设置
    document.getElementById('language').value = settings.defaultLanguage;
  },

  // 重置设置
  reset: function() {
    if (confirm('确定要重置所有设置吗？这将清除所有API密钥和偏好设置。')) {
      Storage.saveSettings({});
      this.hide();
      this.showNotification('设置已重置');
    }
  },

  // 隐藏模态框
  hide: function() {
    document.getElementById('settingsModal').classList.add('hidden');
    // 关闭所有展开的面板
    document.querySelectorAll('.api-config-panel').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.fa-chevron-right').forEach(c => c.classList.remove('rotate-90'));
  },

  // 显示通知
  showNotification: function(message) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 transform transition-transform duration-300 translate-x-full';
    notification.innerHTML = `
      <div class="flex items-center gap-2">
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    // 显示通知
    setTimeout(() => {
      notification.classList.remove('translate-x-full');
    }, 100);
    
    // 自动隐藏
    setTimeout(() => {
      notification.classList.add('translate-x-full');
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 2000);
  }
};

// 生成代码的主要函数
async function generateCode() {
  console.log('点击了生成按钮');
  
  // 获取表单数据
  const requirement = document.getElementById('requirement').value.trim();
  const language = document.getElementById('language').value;
  const extra = document.getElementById('extra').value.trim();
  
  if (!requirement) {
    alert('请输入需求描述');
    return;
  }
  
  // 获取选中的模型
  const selectedProviders = Array.from(document.querySelectorAll('.provider-checkbox:checked')).map(cb => cb.value);
  console.log('选中的模型:', selectedProviders);
  
  if (selectedProviders.length === 0) {
    alert('请至少选择一个AI模型');
    return;
  }
  
  // 构建请求体
  const genBody = {
    requirement: requirement,
    language: language,
    extra_directives: extra,
    providers: selectedProviders
  };
  
  console.log('准备发送生成请求:', genBody);
  
  try {
    const genResponse = await fetch(API_BASE + "/api/v1/generation/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(genBody)
    });
    
    console.log('生成请求响应状态:', genResponse.status);
    
    if (!genResponse.ok) {
      throw new Error(`生成请求失败: ${genResponse.status} ${genResponse.statusText}`);
    }
    
    const gen = await genResponse.json();
    console.log('生成响应:', gen);
    
    // 显示测试代码
    if (gen.tests_code) {
      displayTests(gen.tests_code);
    }
    
    // 处理生成的代码
    const artifacts = gen.artifacts || [];
    console.log('处理生成的代码:', artifacts);

    const evalBody = { session_id: gen.session_id, artifacts, tests_code: gen.tests_code, language };
    console.log('准备发送评测请求:', evalBody);
    
    const evalResponse = await fetch(API_BASE + "/api/v1/evaluation/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(evalBody)
    });
    
    console.log('评测请求响应状态:', evalResponse.status);
    
    if (!evalResponse.ok) {
      throw new Error(`评测请求失败: ${evalResponse.status} ${evalResponse.statusText}`);
    }
    
    const evalResult = await evalResponse.json();
    console.log('评测响应:', evalResult);
    
    // 显示结果
    displayResults(evalResult.results, evalResult.winner);
    
    // 如果设置了自动保存历史记录
    const settings = Storage.getSettings();
    if (settings.autoSaveHistory !== false) {
      // 等待结果渲染完成后保存
      setTimeout(() => {
        const codeElements = document.querySelectorAll('[id$="Code"]');
        const results = Array.from(codeElements).map(el => el.textContent).filter(code => code.trim());
        const testsCode = document.getElementById('testsCode')?.textContent || '';
        const winnerCode = document.getElementById('winnerCode')?.textContent || '';
        
        Storage.saveHistory({
          requirement,
          language,
          providers: selectedProviders,
          results,
          testsCode,
          winner: winnerCode
        });
      }, 1000);
    }
    
  } catch (error) {
    console.error('❌ 代码生成流程失败:', error);
    alert(`代码生成失败: ${error.message}`);
  }
}

// 显示结果的函数
function displayResults(results, winner) {
  console.log('显示结果:', results, winner);
  
  const resultsContainer = document.getElementById('results');
  if (!resultsContainer) return;
  
  // 清空之前的结果
  resultsContainer.innerHTML = '';
  
  // 显示每个结果
  results.forEach((result, index) => {
    const resultCard = createResultCard(result, index);
    resultsContainer.appendChild(resultCard);
  });
  
  // 显示最优方案
  if (winner) {
    displayWinner(winner);
  }
}

// 创建结果卡片
function createResultCard(result, index) {
  const div = document.createElement('div');
  div.className = 'surface-card rounded-xl p-6';
  
  const score = Math.round(result.total_score * 100);
  const provider = result.provider || `方案${index + 1}`;
  
  div.innerHTML = `
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-gray-900">${provider}</h3>
      <div class="flex items-center gap-2">
        <span class="text-2xl font-bold text-blue-600">${score}</span>
        <span class="text-sm text-gray-500">分</span>
      </div>
    </div>
    
    <div class="space-y-3 mb-4">
      <div class="flex justify-between">
        <span class="text-sm text-gray-600">BLEU分数:</span>
        <span class="font-medium">${Math.round((result.bleu_score || 0) * 100)}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-sm text-gray-600">测试通过率:</span>
        <span class="font-medium">${Math.round((result.tests_pass_rate || 0) * 100)}%</span>
      </div>
      <div class="flex justify-between">
        <span class="text-sm text-gray-600">AST质量:</span>
        <span class="font-medium">${Math.round((result.ast_quality || 0) * 100)}</span>
      </div>
    </div>
    
    <details class="group">
      <summary class="cursor-pointer flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
        <i class="fas fa-code text-gray-600"></i>
        <span class="font-medium text-gray-900">查看代码</span>
        <i class="fas fa-chevron-down group-open:rotate-180 transition-transform ml-auto text-gray-400"></i>
      </summary>
      <div class="mt-3">
        <div class="code-block rounded-lg overflow-hidden">
          <div class="flex items-center justify-between px-4 py-2 bg-slate-800">
            <span class="text-gray-300 text-sm font-mono">solution.py</span>
            <button onclick="copyToClipboard(this)" class="text-gray-400 hover:text-white transition-colors">
              <i class="fas fa-copy"></i>
            </button>
          </div>
          <pre id="code${index}Code" class="p-4 overflow-auto max-h-96 font-mono text-sm">${result.code || ''}</pre>
        </div>
      </div>
    </details>
  `;
  
  return div;
}

// 显示最优方案
function displayWinner(winner) {
  const winnerSection = document.getElementById('winner');
  const winnerMeta = document.getElementById('winnerMeta');
  const winnerCode = document.getElementById('winnerCode');
  
  if (!winnerSection || !winnerMeta || !winnerCode) return;
  
  const score = Math.round(winner.total_score * 100);
  
  winnerMeta.textContent = `提供者: ${winner.provider || '未知'}
总分: ${score}/100
BLEU分数: ${Math.round((winner.bleu_score || 0) * 100)}
测试通过率: ${Math.round((winner.tests_pass_rate || 0) * 100)}%
AST质量: ${Math.round((winner.ast_quality || 0) * 100)}`;
  
  winnerCode.textContent = winner.code || '';
  
  winnerSection.classList.remove('hidden');
}

// 复制到剪贴板
function copyToClipboard(button) {
  const codeElement = button.closest('.code-block').querySelector('pre');
  const text = codeElement.textContent;
  
  navigator.clipboard.writeText(text).then(() => {
    const originalIcon = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check"></i>';
    setTimeout(() => {
      button.innerHTML = originalIcon;
    }, 1000);
  }).catch(err => {
    console.error('复制失败:', err);
  });
}

// 初始化新功能的事件监听器
document.addEventListener('DOMContentLoaded', function() {
  console.log('🚀 DOM加载完成，开始绑定事件监听器...');
  
  // 生成按钮事件
  const runBtn = document.getElementById('runBtn');
  if (runBtn) {
    runBtn.addEventListener('click', generateCode);
    console.log('✅ 生成按钮事件已绑定');
  }
  
  // 历史记录按钮
  const historyBtn = document.getElementById('historyBtn');
  if (historyBtn) {
    historyBtn.addEventListener('click', () => {
      console.log('🕐 历史记录按钮被点击');
      console.log('检查HistoryManager:', typeof HistoryManager);
      console.log('检查HistoryManager.show:', typeof HistoryManager.show);
      try {
        HistoryManager.show();
      } catch (error) {
        console.error('❌ 历史记录功能错误:', error);
        alert('历史记录功能出错：' + error.message);
      }
    });
    console.log('✅ 历史记录按钮事件已绑定');
  } else {
    console.error('❌ 找不到历史记录按钮');
  }
  
  const closeHistoryModal = document.getElementById('closeHistoryModal');
  if (closeHistoryModal) {
    closeHistoryModal.addEventListener('click', () => HistoryManager.hide());
  }
  
  // 导出按钮
  const exportBtn = document.getElementById('exportBtn');
  if (exportBtn) {
    exportBtn.addEventListener('click', () => {
      console.log('📥 导出按钮被点击');
      try {
        ExportManager.show();
      } catch (error) {
        console.error('❌ 导出功能错误:', error);
      }
    });
    console.log('✅ 导出按钮事件已绑定');
  } else {
    console.error('❌ 找不到导出按钮');
  }
  
  const closeExportModal = document.getElementById('closeExportModal');
  if (closeExportModal) {
    closeExportModal.addEventListener('click', () => ExportManager.hide());
  }
  
  const confirmExport = document.getElementById('confirmExport');
  if (confirmExport) {
    confirmExport.addEventListener('click', () => ExportManager.export());
  }
  
  const cancelExport = document.getElementById('cancelExport');
  if (cancelExport) {
    cancelExport.addEventListener('click', () => ExportManager.hide());
  }
  
  // 设置按钮
  const settingsBtn = document.getElementById('settingsBtn');
  if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
      console.log('⚙️ 设置按钮被点击');
      try {
        SettingsManager.show();
      } catch (error) {
        console.error('❌ 设置功能错误:', error);
      }
    });
    console.log('✅ 设置按钮事件已绑定');
  } else {
    console.error('❌ 找不到设置按钮');
  }
  
  const closeSettingsModal = document.getElementById('closeSettingsModal');
  if (closeSettingsModal) {
    closeSettingsModal.addEventListener('click', () => SettingsManager.hide());
  }
  
  const saveSettings = document.getElementById('saveSettings');
  if (saveSettings) {
    saveSettings.addEventListener('click', () => SettingsManager.save());
  }
  
  const resetSettings = document.getElementById('resetSettings');
  if (resetSettings) {
    resetSettings.addEventListener('click', () => SettingsManager.reset());
  }
  
  const cancelSettings = document.getElementById('cancelSettings');
  if (cancelSettings) {
    cancelSettings.addEventListener('click', () => SettingsManager.hide());
  }
  
  // 点击模态框背景关闭
  document.getElementById('historyModal')?.addEventListener('click', function(e) {
    if (e.target === this) HistoryManager.hide();
  });
  document.getElementById('exportModal')?.addEventListener('click', function(e) {
    if (e.target === this) ExportManager.hide();
  });
  document.getElementById('settingsModal')?.addEventListener('click', function(e) {
    if (e.target === this) SettingsManager.hide();
  });
  
  // 应用保存的设置
  const settings = Storage.getSettings();
  if (settings.defaultLanguage) {
    document.getElementById('language').value = settings.defaultLanguage;
  }
});
