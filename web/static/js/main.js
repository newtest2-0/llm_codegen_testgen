const API_BASE = "http://localhost:8001";

// 全局变量存储角色信息
let availableRoles = {};
let currentRole = 'developer';

// 实时监控相关变量
let metricsInterval = null;
let isMonitoringActive = false;

// 测试JavaScript是否正常加载
console.log('🚀 main.js 开始加载...');
window.addEventListener('load', function() {
  console.log('📱 页面完全加载完成');
  // 页面加载完成后初始化角色
  initializeRoles();
  // 启动实时系统监控
  startSystemMonitoring();
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

function displayTests(testsCode, testProvider) {
  console.log('🧪 displayTests 被调用，代码长度:', testsCode?.length, '提供者:', testProvider);
  
  const testsSection = document.getElementById("tests-section");
  const testsCodeElement = document.getElementById("testsCode");
  const testInfo = document.getElementById("testInfo");
  const testStatus = document.getElementById("testStatus");
  
  if (!testsSection || !testsCodeElement) {
    console.error('❌ 找不到测试展示元素:', {
      testsSection: !!testsSection,
      testsCodeElement: !!testsCodeElement,
      testInfo: !!testInfo,
      testStatus: !!testStatus
    });
    return;
  }
  
  if (!testsCode || testsCode.trim().length === 0) {
    console.warn('⚠️ 测试代码为空');
    testsCodeElement.textContent = '# 测试代码为空\n# 请手动添加测试用例';
  }
  
  // 显示测试代码
  testsCodeElement.textContent = testsCode;
  
  // 分析测试代码信息
  const testLines = testsCode.split('\n');
  const testFunctions = testLines.filter(line => line.trim().startsWith('def test_')).length;
  const hasEdgeCases = testsCode.includes('edge') || testsCode.includes('boundary') || testsCode.includes('边界');
  const hasExceptions = testsCode.includes('pytest.raises') || testsCode.includes('Exception') || testsCode.includes('异常');
  const hasAsserts = testsCode.includes('assert ') || testsCode.includes('assertEqual');
  const hasSetup = testsCode.includes('setUp') || testsCode.includes('fixture') || testsCode.includes('@');
  
  // 分析测试覆盖类型
  const testTypes = [];
  if (testsCode.includes('正常') || testsCode.includes('normal') || testsCode.includes('valid')) testTypes.push('正常用例');
  if (hasEdgeCases) testTypes.push('边界用例');
  if (hasExceptions) testTypes.push('异常用例');
  if (testsCode.includes('性能') || testsCode.includes('performance')) testTypes.push('性能测试');
  
  // 更新测试信息
  const providerDisplayName = testProvider ? testProvider.toUpperCase() : '未知';
  const providerColor = testProvider ? 'text-blue-600' : 'text-gray-500';
  
  testInfo.innerHTML = `
    <div class="flex justify-between">
      <span class="text-gray-600">生成方式:</span>
      <span class="font-medium text-blue-600">智能分析代码结构</span>
    </div>
    <div class="flex justify-between">
      <span class="text-gray-600">AI提供者:</span>
      <span class="font-medium ${providerColor}">${providerDisplayName}</span>
    </div>
    <div class="flex justify-between">
      <span class="text-gray-600">测试框架:</span>
      <span class="font-medium">pytest</span>
    </div>
    <div class="flex justify-between">
      <span class="text-gray-600">测试函数:</span>
      <span class="font-medium text-green-600">${testFunctions} 个</span>
    </div>
    <div class="flex justify-between">
      <span class="text-gray-600">断言检查:</span>
      <span class="font-medium ${hasAsserts ? 'text-green-600' : 'text-gray-400'}">${hasAsserts ? '✓ 包含' : '✗ 无'}</span>
    </div>
    <div class="flex justify-between">
      <span class="text-gray-600">测试类型:</span>
      <span class="font-medium text-blue-600">${testTypes.length > 0 ? testTypes.join(', ') : '基础测试'}</span>
    </div>
    <div class="flex justify-between">
      <span class="text-gray-600">测试覆盖:</span>
      <span class="font-medium ${testTypes.length >= 3 ? 'text-green-600' : testTypes.length >= 2 ? 'text-yellow-600' : 'text-gray-600'}">${testTypes.length >= 3 ? '全面' : testTypes.length >= 2 ? '良好' : '基础'}</span>
    </div>
  `;
  
  // 更新测试状态
  const qualityScore = testTypes.length >= 3 ? '优秀' : testTypes.length >= 2 ? '良好' : '基础';
  const qualityColor = testTypes.length >= 3 ? 'text-green-600' : testTypes.length >= 2 ? 'text-yellow-600' : 'text-blue-600';
  
  testStatus.innerHTML = `
    <div class="${qualityColor}">
      <i class="fas fa-check-circle text-2xl mb-2"></i>
      <p class="font-medium">测试用例生成完成</p>
      <p class="text-sm text-gray-500 mt-1">${testFunctions} 个测试函数</p>
      <div class="mt-2 text-xs">
        <span class="inline-block px-2 py-1 bg-gray-100 rounded text-gray-700">质量评级: ${qualityScore}</span>
      </div>
    </div>
  `;
  
  // 显示测试区域
  testsSection.classList.remove('hidden');
  console.log('✅ 测试区域已显示');
  
  // 更新右侧导航
  if (typeof RightNavigation !== 'undefined') {
    RightNavigation.updateNavigationItems();
  }
  
  // 滚动到测试区域
  setTimeout(() => {
    testsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    console.log('📍 已滚动到测试区域');
  }, 500);
  
  console.log('✅ displayTests 完成');
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
            <span class="text-gray-600">BLEU-4</span>
            <span class="font-medium text-gray-900">${m.bleu4.toFixed(3)}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">ROUGE-1</span>
            <span class="font-medium text-gray-900">${m.rouge?.rouge1?.toFixed(3) || '0.000'}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">ROUGE-2</span>
            <span class="font-medium text-gray-900">${m.rouge?.rouge2?.toFixed(3) || '0.000'}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">ROUGE-L</span>
            <span class="font-medium text-gray-900">${m.rouge?.rougeL?.toFixed(3) || '0.000'}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Pass@1</span>
            <span class="font-medium text-gray-900">${m.pass_at_k?.['pass@1']?.toFixed(3) || '0.000'}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Pass@10</span>
            <span class="font-medium text-gray-900">${m.pass_at_k?.['pass@10']?.toFixed(3) || '0.000'}</span>
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
  const resultsDiv = document.getElementById("results-section");
  const winnerDiv = document.getElementById("winner-section");
  const testsDiv = document.getElementById("tests-section");
  
  if (resultsDiv) resultsDiv.innerHTML = '';
  if (winnerDiv) winnerDiv.classList.add('hidden');
  if (testsDiv) testsDiv.classList.add('hidden');
  
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
      displayTests(gen.tests_code, gen.test_provider);
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
    const winner = document.getElementById("winner-section");
    winner.classList.remove("hidden");
    document.getElementById("winnerMeta").textContent = JSON.stringify(best, null, 2);
    document.getElementById("winnerCode").textContent = artifacts.find(a => a.provider===best.provider)._code;

    const html = ev.results
      .sort((a,b)=>b.metrics.aggregate_score - a.metrics.aggregate_score)
      .map(card).join("\\n");
    document.getElementById("results-section").innerHTML = html;
    
    // 更新快速导航
    if (typeof QuickNavigation !== 'undefined') {
      QuickNavigation.updateNavigationItems();
    }
    
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

// 旧的初始化代码已移动到下面的统一初始化函数中

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
    const results = document.getElementById('results-section');
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
      button.addEventListener('click', async () => {
        const item = button.closest('.api-provider-item');
        const provider = item.dataset.provider;
        const input = item.querySelector('.api-key-input');
        const value = input.value.trim();
        
        try {
          // 调用后端API保存密钥
          const response = await fetch(API_BASE + '/api/v1/settings/api-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              provider: provider,
              api_key: value
            })
          });
          
          if (!response.ok) {
            throw new Error(`保存失败: ${response.status}`);
          }
          
          const result = await response.json();
          
          // 同时保存到本地存储（兼容性）
          const settings = Storage.getSettings();
          settings[`${provider}Key`] = value;
          Storage.saveSettings(settings);
          
          // 更新状态显示
          this.updateApiStatuses(settings);
          
          // 显示通知
          this.showNotification(result.message || `${provider.toUpperCase()} API Key 已保存`);
          
        } catch (error) {
          console.error('保存API密钥失败:', error);
          this.showNotification(`保存失败: ${error.message}`, 'error');
        }
      });
    });
    
    // 清除API密钥
    document.querySelectorAll('.clear-api-key').forEach(button => {
      button.addEventListener('click', async () => {
        const item = button.closest('.api-provider-item');
        const provider = item.dataset.provider;
        const input = item.querySelector('.api-key-input');
        
        if (confirm(`确定要清除 ${provider.toUpperCase()} 的API密钥吗？`)) {
          try {
            // 调用后端API清除密钥
            const response = await fetch(API_BASE + `/api/v1/settings/api-key/${provider}`, {
              method: 'DELETE'
            });
            
            if (!response.ok) {
              throw new Error(`清除失败: ${response.status}`);
            }
            
            const result = await response.json();
            
            // 清空输入框
            input.value = '';
            
            // 同时清除本地存储（兼容性）
            const settings = Storage.getSettings();
            delete settings[`${provider}Key`];
            Storage.saveSettings(settings);
            
            // 更新状态显示
            this.updateApiStatuses(settings);
            
            // 显示通知
            this.showNotification(result.message || `${provider.toUpperCase()} API Key 已清除`);
            
          } catch (error) {
            console.error('清除API密钥失败:', error);
            this.showNotification(`清除失败: ${error.message}`, 'error');
          }
        }
      });
    });
  },

  // 保存设置
  save: async function() {
    const settings = Storage.getSettings();
    
    // 保存系统偏好
    settings.defaultLanguage = document.getElementById('defaultLanguage').value;
    settings.autoSaveHistory = document.getElementById('autoSaveHistory').checked;
    settings.showNotifications = document.getElementById('showNotifications').checked;
    
    // 保存角色设置到后端
    const defaultRoleSelect = document.getElementById('defaultRoleTab');
    if (defaultRoleSelect && defaultRoleSelect.value !== currentRole) {
      try {
        await setDefaultRole(defaultRoleSelect.value);
        currentRole = defaultRoleSelect.value;
      } catch (error) {
        console.error('保存默认角色失败:', error);
        this.showNotification('保存默认角色失败');
        return;
      }
    }
    
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
  showNotification: function(message, type = 'success') {
    const notification = document.createElement('div');
    const bgColor = type === 'error' ? 'bg-red-500' : 'bg-green-500';
    const icon = type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle';
    
    notification.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transform transition-transform duration-300 translate-x-full`;
    notification.innerHTML = `
      <div class="flex items-center gap-2">
        <i class="fas ${icon}"></i>
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
  
  // 获取当前选择的角色提示词
  const rolePrompt = getCurrentRolePrompt();
  
  // 构建请求体
  const genBody = {
    requirement: requirement,
    language: language,
    extra_directives: extra,
    providers: selectedProviders,
    role: currentRole,
    role_prompt: rolePrompt
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
      displayTests(gen.tests_code, gen.test_provider);
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
  console.log('🎯 displayResults 被调用:', { results: results?.length, winner: winner?.provider });
  
  const resultsContainer = document.getElementById('results-section');
  if (!resultsContainer) {
    console.error('❌ 找不到 results-section 容器');
    return;
  }
  
  // 清空之前的结果
  resultsContainer.innerHTML = '';
  
  if (!results || results.length === 0) {
    console.warn('⚠️ 没有结果数据可显示');
    resultsContainer.innerHTML = '<div class="text-center py-8 text-gray-500">暂无结果数据</div>';
    return;
  }
  
  // 显示每个结果
  console.log('📊 开始渲染', results.length, '个结果卡片');
  results.forEach((result, index) => {
    try {
      const resultCard = createResultCard(result, index);
      resultsContainer.appendChild(resultCard);
      console.log('✅ 结果卡片', index + 1, '渲染完成:', result.provider);
    } catch (error) {
      console.error('❌ 渲染结果卡片失败:', error, result);
    }
  });
  
  // 显示最优方案
  if (winner) {
    console.log('🏆 显示最优方案:', winner.provider);
    displayWinner(winner);
  } else {
    console.warn('⚠️ 没有最优方案数据');
  }
  
  console.log('✅ displayResults 完成');
}

// 创建结果卡片
function createResultCard(result, index) {
  const div = document.createElement('div');
  div.className = 'surface-card rounded-xl p-6';
  
  const score = Math.round((result.metrics?.aggregate_score || 0) * 100);
  const provider = result.provider || `方案${index + 1}`;
  
  // 获取增强指标
  const enhancedMetrics = result.metrics?.enhanced_metrics || {};
  
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
        <span class="text-sm text-gray-600">BLEU-4分数:</span>
        <span class="font-medium">${Math.round((result.metrics?.bleu4 || 0) * 100)}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-sm text-gray-600">测试通过率:</span>
        <span class="font-medium">${result.metrics?.tests?.passed || 0}/${(result.metrics?.tests?.passed || 0) + (result.metrics?.tests?.failed || 0)}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-sm text-gray-600">AST解析:</span>
        <span class="font-medium">${result.metrics?.ast_parse_ok ? '✅' : '❌'}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-sm text-gray-600">可维护性指数:</span>
        <span class="font-medium">${Math.round((enhancedMetrics.maintainability_index || 0) * 100)}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-sm text-gray-600">代码风格得分:</span>
        <span class="font-medium">${Math.round((enhancedMetrics.style_score || 0) * 100)}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-sm text-gray-600">安全性得分:</span>
        <span class="font-medium">${Math.round((enhancedMetrics.security_score || 0) * 100)}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-sm text-gray-600">文档覆盖率:</span>
        <span class="font-medium">${Math.round((enhancedMetrics.docstring_coverage || 0) * 100)}%</span>
      </div>
      <div class="flex justify-between">
        <span class="text-sm text-gray-600">圈复杂度:</span>
        <span class="font-medium">${result.metrics?.cyclomatic || 0}</span>
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
          <pre id="code${index}Code" class="p-4 overflow-auto max-h-96 font-mono text-sm">${result._code || ''}</pre>
        </div>
      </div>
    </details>
    
    <!-- 增强指标详情 -->
    <details class="group mt-3">
      <summary class="cursor-pointer flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
        <i class="fas fa-chart-bar text-gray-600"></i>
        <span class="font-medium text-gray-900">详细指标</span>
        <i class="fas fa-chevron-down group-open:rotate-180 transition-transform ml-auto text-gray-400"></i>
      </summary>
      <div class="mt-3 bg-gray-50 rounded-lg p-4">
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span class="text-gray-600">ROUGE-1:</span>
            <span class="font-medium ml-2">${Math.round(((result.metrics?.rouge?.rouge1 || 0) * 100))}</span>
          </div>
          <div>
            <span class="text-gray-600">ROUGE-2:</span>
            <span class="font-medium ml-2">${Math.round(((result.metrics?.rouge?.rouge2 || 0) * 100))}</span>
          </div>
          <div>
            <span class="text-gray-600">ROUGE-L:</span>
            <span class="font-medium ml-2">${Math.round(((result.metrics?.rouge?.rougeL || 0) * 100))}</span>
          </div>
          <div>
            <span class="text-gray-600">Pass@1:</span>
            <span class="font-medium ml-2">${Math.round(((result.metrics?.pass_at_k?.pass_at_1 || 0) * 100))}%</span>
          </div>
          <div>
            <span class="text-gray-600">Pass@10:</span>
            <span class="font-medium ml-2">${Math.round(((result.metrics?.pass_at_k?.pass_at_10 || 0) * 100))}%</span>
          </div>
          <div>
            <span class="text-gray-600">AST节点数:</span>
            <span class="font-medium ml-2">${result.metrics?.ast_nodes || 0}</span>
          </div>
        </div>
        
        <!-- 安全问题和代码异味 -->
        ${(enhancedMetrics.security_issues && enhancedMetrics.security_issues.length > 0) ? `
        <div class="mt-3">
          <div class="text-sm font-medium text-gray-900 mb-2">安全问题 (${enhancedMetrics.security_issues.length})</div>
          <ul class="text-xs space-y-1">
            ${enhancedMetrics.security_issues.slice(0, 3).map(issue => `
              <li class="flex items-start">
                <span class="text-red-500 mr-1">•</span>
                <span>${issue.message} (第${issue.line}行)</span>
              </li>
            `).join('')}
            ${enhancedMetrics.security_issues.length > 3 ? `<li class="text-gray-500">... 还有${enhancedMetrics.security_issues.length - 3}个问题</li>` : ''}
          </ul>
        </div>
        ` : ''}
        
        ${(enhancedMetrics.style_violations && enhancedMetrics.style_violations.length > 0) ? `
        <div class="mt-3">
          <div class="text-sm font-medium text-gray-900 mb-2">代码风格问题 (${enhancedMetrics.style_violations.length})</div>
          <ul class="text-xs space-y-1">
            ${enhancedMetrics.style_violations.slice(0, 3).map(violation => `
              <li class="flex items-start">
                <span class="text-yellow-500 mr-1">•</span>
                <span>${violation.message} (第${violation.line}行)</span>
              </li>
            `).join('')}
            ${enhancedMetrics.style_violations.length > 3 ? `<li class="text-gray-500">... 还有${enhancedMetrics.style_violations.length - 3}个问题</li>` : ''}
          </ul>
        </div>
        ` : ''}
        
        ${(enhancedMetrics.code_smells && enhancedMetrics.code_smells.length > 0) ? `
        <div class="mt-3">
          <div class="text-sm font-medium text-gray-900 mb-2">代码异味 (${enhancedMetrics.code_smells.length})</div>
          <ul class="text-xs space-y-1">
            ${enhancedMetrics.code_smells.slice(0, 3).map(smell => `
              <li class="flex items-start">
                <span class="text-orange-500 mr-1">•</span>
                <span>${smell}</span>
              </li>
            `).join('')}
            ${enhancedMetrics.code_smells.length > 3 ? `<li class="text-gray-500">... 还有${enhancedMetrics.code_smells.length - 3}个问题</li>` : ''}
          </ul>
        </div>
        ` : ''}
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
  
  const score = Math.round((winner.metrics?.aggregate_score || 0) * 100);
  
  winnerMeta.textContent = `提供者: ${winner.provider || '未知'}
总分: ${score}/100
BLEU-4分数: ${Math.round((winner.metrics?.bleu4 || 0) * 100)}
测试通过: ${winner.metrics?.tests?.passed || 0}/${(winner.metrics?.tests?.passed || 0) + (winner.metrics?.tests?.failed || 0)}
AST解析: ${winner.metrics?.ast_parse_ok ? '✅' : '❌'}`;
  
  winnerCode.textContent = winner._code || '';
  
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

// 专业生成功能
async function professionalGenerate() {
  console.log('🎯 点击了专业生成按钮');
  
  const requirement = document.getElementById("requirement").value.trim();
  const language = document.getElementById("language").value;
  const extra = document.getElementById("extra").value.trim();
  
  if (!requirement) {
    alert("请输入需求描述");
    return;
  }
  
  // 显示加载状态
  const professionalBtn = document.getElementById('professionalRunBtn');
  const originalText = professionalBtn.innerHTML;
  professionalBtn.innerHTML = '<i class="fas fa-spinner fa-spin w-4 h-4"></i><span>需求优化中...</span>';
  professionalBtn.disabled = true;
  
  try {
    // 第一步：优化需求
    console.log('📝 开始需求优化...');
    
    // 获取选中的模型提供者，使用第一个作为需求优化器
    const selectedProviders = Array.from(document.querySelectorAll('.provider-checkbox:checked')).map(cb => cb.value);
    const preferredRefiner = selectedProviders.length > 0 ? selectedProviders[0] : null;
    
    const refineResponse = await fetch(API_BASE + "/api/v1/generation/refine-requirement", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        requirement: requirement,
        language: language,
        extra_directives: extra,
        preferred_refiner: preferredRefiner  // 使用选中的第一个模型进行需求优化
      })
    });
    
    if (!refineResponse.ok) {
      throw new Error(`需求优化失败: ${refineResponse.status} ${refineResponse.statusText}`);
    }
    
    const refineResult = await refineResponse.json();
    console.log('✅ 需求优化完成:', refineResult);
    
    // 显示优化后的需求
    showRefinedRequirement(refineResult);
    
    // 重置按钮状态
    professionalBtn.innerHTML = originalText;
    professionalBtn.disabled = false;
    
    showNotification('需求优化完成！您可以编辑需求，然后点击"继续生成代码"', 'success');
    
    return; // 不再自动继续生成代码，等待用户点击"继续生成"
    
    const genBody = {
      requirement: refineResult.refined_requirement, // 使用优化后的需求
      language: language,
      providers: selectedProviders,
      extra_directives: extra || null
    };
    
    // 清空之前的结果
    const resultsDiv = document.getElementById("results-section");
    const winnerDiv = document.getElementById("winner-section");
    const testsDiv = document.getElementById("tests-section");
    
    if (resultsDiv) resultsDiv.innerHTML = '';
    if (winnerDiv) winnerDiv.classList.add('hidden');
    if (testsDiv) testsDiv.classList.add('hidden');
    
    // 调用现有的代码生成流程
    const genResponse = await fetch(API_BASE + "/api/v1/generation/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(genBody)
    });
    
    if (!genResponse.ok) {
      throw new Error(`专业代码生成失败: ${genResponse.status} ${genResponse.statusText}`);
    }
    
    const gen = await genResponse.json();
    console.log('🎉 专业代码生成完成:', gen);

    // 显示测试用例
    if (gen.tests_code) {
      displayTests(gen.tests_code, gen.test_provider);
    }

    const artifacts = gen.artifacts.map(a => ({...a, _code: a.code}));
    const evalBody = { session_id: gen.session_id, artifacts, tests_code: gen.tests_code, language };
    
    const evalResponse = await fetch(API_BASE + "/api/v1/evaluation/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(evalBody)
    });
    
    if (!evalResponse.ok) {
      throw new Error(`代码评测失败: ${evalResponse.status} ${evalResponse.statusText}`);
    }
    
    const ev = await evalResponse.json();
    console.log('📊 代码评测完成:', ev);

    ev.results.forEach((r,i)=>{ r._code = artifacts[i]._code; });

    const best = ev.best;
    const winner = document.getElementById("winner-section");
    winner.classList.remove("hidden");
    document.getElementById("winnerMeta").textContent = JSON.stringify(best, null, 2);
    document.getElementById("winnerCode").textContent = artifacts.find(a => a.provider===best.provider)._code;

    const html = ev.results
      .sort((a,b)=>b.metrics.aggregate_score - a.metrics.aggregate_score)
      .map(card).join("\\n");
    document.getElementById("results-section").innerHTML = html;
    
    // 更新快速导航
    if (typeof QuickNavigation !== 'undefined') {
      QuickNavigation.updateNavigationItems();
    }
    
    console.log('✅ 专业生成流程完成！');
    
  } catch (error) {
    console.error('❌ 需求优化失败:', error);
    showNotification(`需求优化失败: ${error.message}`, 'error');
  } finally {
    // 恢复按钮状态
    professionalBtn.innerHTML = originalText;
    professionalBtn.disabled = false;
  }
}

// 过滤需求描述中的代码部分
function filterCodeFromRequirement(text) {
  // 移除代码块（```包围的内容）
  let filtered = text.replace(/```[\s\S]*?```/g, '');
  
  // 移除行内代码（`包围的内容）
  filtered = filtered.replace(/`[^`\n]+`/g, '');
  
  // 移除可能的函数调用格式
  filtered = filtered.replace(/\w+\([^)]*\)/g, '');
  
  // 移除类名格式（大写开头的驼峰命名）
  filtered = filtered.replace(/\b[A-Z][a-zA-Z]*(?:[A-Z][a-zA-Z]*)*\b/g, '');
  
  // 移除技术术语和格式化标记
  filtered = filtered.replace(/\*\*([^*]+)\*\*/g, '$1'); // 移除加粗标记，保留内容
  filtered = filtered.replace(/\*([^*]+)\*/g, '$1'); // 移除斜体标记，保留内容
  filtered = filtered.replace(/#{1,6}\s+/g, ''); // 移除markdown标题标记
  filtered = filtered.replace(/^\s*[-*+]\s+/gm, ''); // 移除列表标记
  filtered = filtered.replace(/^\s*\d+\.\s+/gm, ''); // 移除数字列表标记
  
  // 移除常见的技术术语模式
  filtered = filtered.replace(/\b(?:def|class|import|from|return|if|else|for|while|try|except|function|var|let|const|interface|type)\b/g, '');
  
  // 移除特殊符号和格式化字符
  filtered = filtered.replace(/[{}[\]()=;:,.<>]/g, ' ');
  
  // 清理多余的空白和换行
  filtered = filtered.replace(/\n{3,}/g, '\n\n'); // 最多保留两个连续换行
  filtered = filtered.replace(/[ \t]{2,}/g, ' '); // 多个空格替换为单个空格
  filtered = filtered.replace(/^\s+|\s+$/gm, ''); // 移除行首行尾空白
  filtered = filtered.trim();
  
  return filtered;
}

// 显示优化后的需求
function showRefinedRequirement(refineResult) {
  // 过滤掉代码部分，只保留纯文字需求描述
  const filteredRequirement = filterCodeFromRequirement(refineResult.refined_requirement);
  
  // 在需求输入框上方添加一个展示优化需求的区域
  const requirementContainer = document.getElementById('requirement').parentElement;
  
  // 移除之前的优化需求显示
  const existingRefined = document.getElementById('refinedRequirementDisplay');
  if (existingRefined) {
    existingRefined.remove();
  }
  
  // 创建优化需求显示区域
  const refinedDiv = document.createElement('div');
  refinedDiv.id = 'refinedRequirementDisplay';
  refinedDiv.className = 'mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg';
  refinedDiv.innerHTML = `
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-2">
        <i class="fas fa-magic text-blue-600"></i>
        <span class="text-sm font-medium text-blue-900">AI优化后的专业需求</span>
        <span class="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full">
          由 ${refineResult.refinement_provider} 生成
        </span>
      </div>
      <div class="flex items-center gap-2">
        <button onclick="editRefinedRequirement()" id="editRefinedBtn" class="text-blue-600 hover:text-blue-800 text-sm">
          <i class="fas fa-edit mr-1"></i>编辑
        </button>
        <button onclick="copyRefinedRequirement()" class="text-blue-600 hover:text-blue-800 text-sm">
          <i class="fas fa-copy mr-1"></i>复制
        </button>
        <button onclick="toggleRefinedRequirement()" class="text-blue-600 hover:text-blue-800 text-sm">
          <i class="fas fa-eye-slash mr-1"></i>收起
        </button>
      </div>
    </div>
    
     <!-- 显示模式 -->
     <div id="refinedDisplay" class="bg-white p-3 rounded border">
       <div class="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">${filteredRequirement}</div>
     </div>
     
     <!-- 编辑模式 -->
     <div id="refinedEditor" class="bg-white p-3 rounded border" style="display: none;">
       <textarea id="refinedTextarea" class="w-full h-64 p-3 border border-gray-300 rounded text-sm resize-y focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="编辑您的需求...">${filteredRequirement}</textarea>
      <div class="flex items-center gap-2 mt-3">
        <button onclick="saveRefinedRequirement()" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm flex items-center gap-2">
          <i class="fas fa-check"></i>
          保存
        </button>
        <button onclick="cancelEditRequirement()" class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm flex items-center gap-2">
          <i class="fas fa-times"></i>
          取消
        </button>
      </div>
    </div>
    
    <!-- 操作按钮区域 -->
    <div class="mt-3 flex items-center gap-3 pt-3 border-t border-blue-200">
      <button onclick="continueGenerate()" id="continueGenerateBtn" class="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded flex items-center gap-2 font-medium">
        <i class="fas fa-play"></i>
        继续生成代码
      </button>
      <div class="text-xs text-gray-600">
        <strong>原始需求：</strong>${refineResult.original_requirement}
      </div>
    </div>
  `;
  
  requirementContainer.appendChild(refinedDiv);
  
  // 滚动到优化需求区域
  setTimeout(() => {
    refinedDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);
  
  // 存储优化后的需求以供后续使用（使用过滤后的文本）
  window.refinedRequirementData = {
    ...refineResult,
    refined_requirement: filteredRequirement
  };
}

// 复制优化后的需求
function copyRefinedRequirement() {
  if (window.refinedRequirementData) {
    navigator.clipboard.writeText(window.refinedRequirementData.refined_requirement).then(() => {
      showNotification('优化需求已复制到剪贴板');
    }).catch(err => {
      console.error('复制失败:', err);
    });
  }
}

// 使用优化后的需求替换原始需求
function useRefinedRequirement() {
  if (window.refinedRequirementData) {
    document.getElementById('requirement').value = window.refinedRequirementData.refined_requirement;
    showNotification('已将优化需求填入输入框');
  }
}

// 编辑优化后的需求
function editRefinedRequirement() {
  const display = document.getElementById('refinedDisplay');
  const editor = document.getElementById('refinedEditor');
  const editBtn = document.getElementById('editRefinedBtn');
  
  if (display && editor) {
    display.style.display = 'none';
    editor.style.display = 'block';
    editBtn.innerHTML = '<i class="fas fa-times mr-1"></i>取消编辑';
    editBtn.onclick = cancelEditRequirement;
    
    // 自动聚焦到文本框
    const textarea = document.getElementById('refinedTextarea');
    if (textarea) {
      textarea.focus();
    }
  }
}

// 保存编辑后的需求
function saveRefinedRequirement() {
  const textarea = document.getElementById('refinedTextarea');
  const display = document.getElementById('refinedDisplay');
  const editor = document.getElementById('refinedEditor');
  const editBtn = document.getElementById('editRefinedBtn');
  
  if (textarea && display && editor) {
    const editedRequirement = textarea.value.trim();
    if (!editedRequirement) {
      alert('需求内容不能为空');
      return;
    }
    
    // 更新显示内容
    const preElement = display.querySelector('pre');
    if (preElement) {
      preElement.textContent = editedRequirement;
    }
    
    // 更新存储的需求数据
    if (window.refinedRequirementData) {
      window.refinedRequirementData.refined_requirement = editedRequirement;
    }
    
    // 切换回显示模式
    display.style.display = 'block';
    editor.style.display = 'none';
    editBtn.innerHTML = '<i class="fas fa-edit mr-1"></i>编辑';
    editBtn.onclick = editRefinedRequirement;
    
    showNotification('需求已保存');
  }
}

// 取消编辑需求
function cancelEditRequirement() {
  const display = document.getElementById('refinedDisplay');
  const editor = document.getElementById('refinedEditor');
  const editBtn = document.getElementById('editRefinedBtn');
  const textarea = document.getElementById('refinedTextarea');
  
  if (display && editor && textarea) {
    // 恢复原始内容
    if (window.refinedRequirementData) {
      textarea.value = window.refinedRequirementData.refined_requirement;
    }
    
    // 切换回显示模式
    display.style.display = 'block';
    editor.style.display = 'none';
    editBtn.innerHTML = '<i class="fas fa-edit mr-1"></i>编辑';
    editBtn.onclick = editRefinedRequirement;
  }
}

// 评估生成的代码
async function evaluateResults(generateResult) {
  try {
    const language = document.getElementById("language").value;
    const artifacts = generateResult.artifacts || [];
    
    if (artifacts.length === 0) {
      console.warn('没有找到代码工件进行评估');
      return null;
    }
    
    // 构建评估请求
    const evalBody = { 
      session_id: generateResult.session_id, 
      artifacts: artifacts.map(a => ({...a, _code: a.code})), 
      tests_code: generateResult.tests_code, 
      language 
    };
    
    console.log('准备发送评测请求:', evalBody);
    
    const evalResponse = await fetch(API_BASE + "/api/v1/evaluation/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(evalBody)
    });
    
    if (!evalResponse.ok) {
      throw new Error(`评测失败: ${evalResponse.status} ${evalResponse.statusText}`);
    }
    
    const evalResult = await evalResponse.json();
    console.log('评测完成:', evalResult);
    
    // 为结果添加代码内容
    if (evalResult.results) {
      evalResult.results.forEach((r, i) => { 
        if (artifacts[i]) {
          r._code = artifacts[i].code; 
        }
      });
    }
    
    return evalResult;
    
  } catch (error) {
    console.error('评估失败:', error);
    return null;
  }
}

// 继续生成代码（使用当前的优化需求）
async function continueGenerate() {
  console.log('🎯 点击了继续生成按钮');
  
  if (!window.refinedRequirementData) {
    alert('没有可用的优化需求');
    return;
  }
  
  const language = document.getElementById("language").value;
  const extra = document.getElementById("extra").value.trim();
  
  // 获取当前的需求内容（可能已被编辑）
  const currentRequirement = window.refinedRequirementData.refined_requirement;
  
  // 显示加载状态
  const continueBtn = document.getElementById('continueGenerateBtn');
  const originalText = continueBtn.innerHTML;
  continueBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>代码生成中...';
  continueBtn.disabled = true;
  
  try {
    console.log('🔧 开始基于优化需求生成代码...');
    
    // 清空之前的结果
    const resultsDiv = document.getElementById("results-section");
    const winnerDiv = document.getElementById("winner-section");
    const testsDiv = document.getElementById("tests-section");
    
    if (resultsDiv) resultsDiv.innerHTML = '';
    if (winnerDiv) winnerDiv.classList.add('hidden');
    if (testsDiv) testsDiv.classList.add('hidden');
    
    // 获取选中的模型提供者
    const selectedProviders = Array.from(document.querySelectorAll('.provider-checkbox:checked')).map(cb => cb.value);
    
    if (selectedProviders.length === 0) {
      throw new Error('请至少选择一个AI模型');
    }
    
    // 使用优化后的需求生成代码
    const generateResponse = await fetch(API_BASE + "/api/v1/generation/generate", {
      method: "POST", 
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        requirement: currentRequirement,  // 使用优化后的需求
        language: language,
        extra_directives: extra,
        providers: selectedProviders
      })
    });
    
    if (!generateResponse.ok) {
      throw new Error(`代码生成失败: ${generateResponse.status} ${generateResponse.statusText}`);
    }
    
    const generateResult = await generateResponse.json();
    console.log('✅ 代码生成完成:', generateResult);
    
    // 显示测试用例
    if (generateResult.tests_code) {
      console.log('📝 显示测试用例:', generateResult.tests_code.substring(0, 100) + '...');
      displayTests(generateResult.tests_code, generateResult.test_provider);
    } else {
      console.warn('⚠️ 没有测试用例数据');
    }
    
    // 自动评估代码
    console.log('🔍 开始评估代码...');
    const evalResult = await evaluateResults(generateResult);
    console.log('📊 评估结果:', evalResult);
    
    // 显示生成结果
    if (evalResult && evalResult.results) {
      console.log('🎯 显示生成结果，共', evalResult.results.length, '个方案');
      displayResults(evalResult.results, evalResult.winner);
      
      // 显示最优方案
      if (evalResult.winner) {
        const winnerSection = document.getElementById('winner-section');
        if (winnerSection) {
          winnerSection.classList.remove('hidden');
          console.log('🏆 显示最优方案:', evalResult.winner.provider);
        }
      }
    } else {
      console.error('❌ 评估结果为空或无效');
    }
    
    showNotification('代码生成完成！', 'success');
    
  } catch (error) {
    console.error('❌ 继续生成失败:', error);
    showNotification(`生成失败: ${error.message}`, 'error');
  } finally {
    continueBtn.innerHTML = originalText;
    continueBtn.disabled = false;
  }
}

// 切换优化需求的显示/隐藏
function toggleRefinedRequirement() {
  const display = document.getElementById('refinedRequirementDisplay');
  if (display) {
    const content = display.querySelector('.bg-white');
    const button = display.querySelector('[onclick="toggleRefinedRequirement()"]');
    const icon = button.querySelector('i');
    
    if (content.style.display === 'none') {
      content.style.display = 'block';
      icon.className = 'fas fa-eye-slash mr-1';
      button.innerHTML = '<i class="fas fa-eye-slash mr-1"></i>收起';
    } else {
      content.style.display = 'none';
      icon.className = 'fas fa-eye mr-1';
      button.innerHTML = '<i class="fas fa-eye mr-1"></i>展开';
    }
  }
}

// 简单的通知功能
function showNotification(message) {
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

// 标签页管理器
const TabManager = {
  currentTab: 'home',
  
  // 初始化标签页功能
  init: function() {
    console.log('🏷️ 初始化标签页管理器...');
    
    // 绑定标签按钮事件
    document.querySelectorAll('.tab-button').forEach(button => {
      button.addEventListener('click', (e) => {
        e.preventDefault();
        const tabId = button.getAttribute('data-tab');
        this.switchTab(tabId);
      });
    });
    
    // 初始化历史记录标签页内容
    this.initHistoryTab();
    
    // 初始化设置标签页内容
    this.initSettingsTab();
    
    console.log('✅ 标签页管理器初始化完成');
  },
  
  // 切换标签页
  switchTab: function(tabId) {
    console.log(`🔄 切换到标签页: ${tabId}`);
    
    // 更新当前标签
    this.currentTab = tabId;
    
    // 更新标签按钮状态
    document.querySelectorAll('.tab-button').forEach(btn => {
      btn.classList.remove('active');
      if (btn.getAttribute('data-tab') === tabId) {
        btn.classList.add('active');
      }
    });
    
    // 切换标签内容
    document.querySelectorAll('.tab-content').forEach(content => {
      content.classList.add('hidden');
      content.classList.remove('active');
    });
    
    const targetTab = document.getElementById(tabId + 'Tab');
    if (targetTab) {
      targetTab.classList.remove('hidden');
      targetTab.classList.add('active');
      
      // 根据不同标签页执行特定初始化
      this.onTabSwitch(tabId);
      
      // 控制右侧导航的显示（仅在代码生成页面显示）
      if (typeof RightNavigation !== 'undefined') {
        RightNavigation.toggleVisibility(tabId === 'home');
      }
    }
  },
  
  // 标签页切换后的回调
  onTabSwitch: function(tabId) {
    switch(tabId) {
      case 'history':
        this.refreshHistoryContent();
        break;
      case 'export':
        this.refreshExportContent();
        break;
      case 'settings':
        this.refreshSettingsContent();
        break;
    }
  },
  
  // 初始化历史记录标签页
  initHistoryTab: function() {
    // 清空全部历史记录按钮
    const clearAllBtn = document.getElementById('clearAllHistory');
    if (clearAllBtn) {
      clearAllBtn.addEventListener('click', () => {
        if (confirm('确定要清空所有历史记录吗？此操作不可撤销。')) {
          Storage.clearHistory();
          this.refreshHistoryContent();
          showNotification('所有历史记录已清空');
        }
      });
    }
    
    // 搜索功能
    const searchInput = document.getElementById('historySearch');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.filterHistory(e.target.value);
      });
    }
  },
  
  // 初始化设置标签页
  initSettingsTab: function() {
    // 保存设置按钮
    const saveBtn = document.getElementById('saveSettingsTab');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => {
        this.saveTabSettings();
      });
    }
    
    // 重置设置按钮
    const resetBtn = document.getElementById('resetSettingsTab');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        if (confirm('确定要重置所有设置吗？')) {
          this.resetTabSettings();
        }
      });
    }
    
    // 导出按钮
    const exportBtn = document.getElementById('exportNowBtn');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        this.executeExport();
      });
    }
  },
  
  // 刷新历史记录内容
  refreshHistoryContent: function() {
    const historyList = document.getElementById('historyListContent');
    const historyCount = document.getElementById('historyCount');
    
    if (!historyList || !historyCount) return;
    
    const history = Storage.getHistory();
    historyCount.textContent = `共 ${history.length} 条记录`;
    
    if (history.length === 0) {
      historyList.innerHTML = `
        <div class="text-center py-12 text-gray-500">
          <i class="fas fa-history text-4xl mb-4 opacity-50"></i>
          <p>暂无历史记录</p>
          <p class="text-sm mt-2">生成代码后将自动保存到历史记录</p>
        </div>
      `;
    } else {
      historyList.innerHTML = history.map(item => this.createHistoryItem(item)).join('');
    }
  },
  
  // 创建历史记录项
  createHistoryItem: function(item) {
    const date = new Date(item.timestamp).toLocaleString('zh-CN');
    const resultsCount = item.results ? item.results.length : 0;
    
    return `
      <div class="surface-card rounded-lg p-4 hover:shadow-md transition-all duration-200">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full font-medium">${item.language}</span>
              <span class="text-xs text-gray-500">${date}</span>
            </div>
            <p class="text-gray-700 mb-3 line-clamp-2">${item.requirement}</p>
            <div class="flex items-center gap-4 text-xs text-gray-500">
              <span><i class="fas fa-robot mr-1"></i>${item.providers?.length || 0} 个模型</span>
              <span><i class="fas fa-code mr-1"></i>${resultsCount} 个结果</span>
              ${item.testsCode ? '<span><i class="fas fa-flask mr-1"></i>包含测试</span>' : ''}
            </div>
          </div>
          <div class="flex items-center gap-2 ml-4">
            <button onclick="TabManager.loadHistoryItem(${item.id})" class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
              <i class="fas fa-redo mr-1"></i>重新生成
            </button>
            <button onclick="TabManager.deleteHistoryItem(${item.id})" class="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors">
              <i class="fas fa-trash mr-1"></i>删除
            </button>
          </div>
        </div>
      </div>
    `;
  },
  
  // 加载历史记录项
  loadHistoryItem: function(id) {
    const history = Storage.getHistory();
    const item = history.find(h => h.id === id);
    
    if (item) {
      // 切换到代码生成标签页
      this.switchTab('home');
      
      // 填充表单
      setTimeout(() => {
        document.getElementById('requirement').value = item.requirement;
        document.getElementById('language').value = item.language;
        
        // 选择对应的模型
        if (item.providers) {
          const checkboxes = document.querySelectorAll('.provider-checkbox');
          checkboxes.forEach(checkbox => {
            checkbox.checked = item.providers.includes(checkbox.value);
          });
        }
        
        showNotification('历史记录已加载到代码生成页面');
      }, 300);
    }
  },
  
  // 删除历史记录项
  deleteHistoryItem: function(id) {
    if (confirm('确定要删除这条历史记录吗？')) {
      Storage.deleteHistory(id);
      this.refreshHistoryContent();
      showNotification('历史记录已删除');
    }
  },
  
  // 过滤历史记录
  filterHistory: function(searchTerm) {
    const history = Storage.getHistory();
    const filtered = history.filter(item => 
      item.requirement.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.language.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    const historyList = document.getElementById('historyListContent');
    if (historyList) {
      if (filtered.length === 0) {
        historyList.innerHTML = `
          <div class="text-center py-12 text-gray-500">
            <i class="fas fa-search text-4xl mb-4 opacity-50"></i>
            <p>未找到匹配的历史记录</p>
          </div>
        `;
      } else {
        historyList.innerHTML = filtered.map(item => this.createHistoryItem(item)).join('');
      }
    }
  },
  
  // 刷新导出内容
  refreshExportContent: function() {
    // 检查是否有可导出的内容
    const hasResults = document.getElementById('results-section')?.children.length > 0;
    const exportBtn = document.getElementById('exportNowBtn');
    
    if (exportBtn) {
      if (hasResults) {
        exportBtn.disabled = false;
        exportBtn.innerHTML = '<i class="fas fa-download mr-2"></i>立即导出';
      } else {
        exportBtn.disabled = true;
        exportBtn.innerHTML = '<i class="fas fa-exclamation-triangle mr-2"></i>暂无可导出内容';
      }
    }
  },
  
  // 刷新设置内容
  refreshSettingsContent: function() {
    const settings = Storage.getSettings();
    
    // 加载API配置列表
    this.loadApiConfigList();
    
    // 填充系统偏好设置
    const defaultLangSelect = document.getElementById('defaultLanguageTab');
    const autoSaveCheck = document.getElementById('autoSaveHistoryTab');
    const notificationsCheck = document.getElementById('showNotificationsTab');
    
    if (defaultLangSelect) defaultLangSelect.value = settings.defaultLanguage || 'python';
    if (autoSaveCheck) autoSaveCheck.checked = settings.autoSaveHistory !== false;
    if (notificationsCheck) notificationsCheck.checked = settings.showNotifications !== false;
  },
  
  // 加载API配置列表
  loadApiConfigList: function() {
    const apiList = document.getElementById('apiConfigList');
    if (!apiList) return;
    
    const providers = [
      { id: 'openai', name: 'OpenAI', icon: '🤖', desc: 'GPT-4 系列模型' },
      { id: 'deepseek', name: 'DeepSeek', icon: '🔍', desc: 'DeepSeek Chat 模型' },
      { id: 'claude', name: 'Claude', icon: '🎭', desc: 'Anthropic Claude 3.5' },
      { id: 'gemini', name: 'Gemini', icon: '💎', desc: 'Google Gemini 1.5' },
      { id: 'qwen', name: '通义千问', icon: '🌟', desc: '阿里云 Qwen Plus' },
      { id: 'baichuan', name: '百川智能', icon: '🏔️', desc: 'Baichuan4 模型' },
      { id: 'chatglm', name: 'ChatGLM', icon: '💬', desc: '智谱 GLM-4 Plus' },
      { id: 'llama', name: 'LLaMA', icon: '🦙', desc: 'Meta LLaMA 3.1' }
    ];
    
    const settings = Storage.getSettings();
    
    apiList.innerHTML = providers.map(provider => {
      const hasKey = settings[`${provider.id}Key`] && settings[`${provider.id}Key`].trim();
      const isLocal = provider.id === 'llama';
      
      return `
        <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <span class="text-lg">${provider.icon}</span>
            </div>
            <div>
              <div class="font-medium text-gray-900">${provider.name}</div>
              <div class="text-sm text-gray-500">${provider.desc}</div>
            </div>
          </div>
          <div class="flex items-center gap-3">
            ${isLocal ? 
              '<span class="text-xs px-2 py-1 rounded-full bg-green-100 text-green-600">本地模型</span>' :
              `<span class="text-xs px-2 py-1 rounded-full ${hasKey ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'}">${hasKey ? '已配置' : '未配置'}</span>`
            }
            ${!isLocal ? 
              `<button onclick="TabManager.configureApi('${provider.id}')" class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
                ${hasKey ? '更新' : '配置'}
              </button>` : ''
            }
          </div>
        </div>
      `;
    }).join('');
  },
  
  // 配置API
  configureApi: function(providerId) {
    const key = prompt(`请输入 ${providerId.toUpperCase()} 的API密钥:`);
    if (key && key.trim()) {
      const settings = Storage.getSettings();
      settings[`${providerId}Key`] = key.trim();
      Storage.saveSettings(settings);
      this.refreshSettingsContent();
      showNotification(`${providerId.toUpperCase()} API密钥已保存`);
    }
  },
  
  // 保存标签页设置
  saveTabSettings: function() {
    const settings = Storage.getSettings();
    
    const defaultLang = document.getElementById('defaultLanguageTab')?.value;
    const autoSave = document.getElementById('autoSaveHistoryTab')?.checked;
    const notifications = document.getElementById('showNotificationsTab')?.checked;
    
    if (defaultLang) settings.defaultLanguage = defaultLang;
    if (autoSave !== undefined) settings.autoSaveHistory = autoSave;
    if (notifications !== undefined) settings.showNotifications = notifications;
    
    Storage.saveSettings(settings);
    
    // 同步到代码生成页面
    if (defaultLang) {
      const mainLangSelect = document.getElementById('language');
      if (mainLangSelect) mainLangSelect.value = defaultLang;
    }
    
    showNotification('设置已保存');
  },
  
  // 重置标签页设置
  resetTabSettings: function() {
    Storage.saveSettings({});
    this.refreshSettingsContent();
    showNotification('设置已重置');
  },
  
  // 执行导出
  executeExport: function() {
    try {
      ExportManager.collectCurrentData();
      ExportManager.export();
      showNotification('导出完成！');
    } catch (error) {
      console.error('导出失败:', error);
      showNotification('导出失败，请重试', 'error');
    }
  }
};

// 右侧导航管理器
const RightNavigation = {
  sections: ['requirements-section', 'models-section', 'tests-section', 'winner-section', 'results-section'],
  isExpanded: false,
  
  // 初始化右侧导航
  init: function() {
    console.log('🧭 初始化右侧导航...');
    
    // 绑定展开/收起按钮事件
    const navToggle = document.getElementById('navToggle');
    const navClose = document.getElementById('navClose');
    const rightNav = document.getElementById('rightNavigation');
    
    if (navToggle) {
      console.log('✅ 找到导航切换按钮，绑定点击事件');
      navToggle.addEventListener('click', (e) => {
        console.log('🖱️ 导航切换按钮被点击');
        e.preventDefault();
        e.stopPropagation();
        this.toggleNavigation();
      });
    } else {
      console.error('❌ 未找到导航切换按钮 #navToggle');
    }
    
    if (navClose) {
      navClose.addEventListener('click', () => {
        this.closeNavigation();
      });
    }
    
    // 点击导航外部区域关闭
    document.addEventListener('click', (e) => {
      if (this.isExpanded && rightNav && !rightNav.contains(e.target)) {
        this.closeNavigation();
      }
    });
    
    // 绑定导航链接点击事件
    document.querySelectorAll('#rightNavigation .nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = link.getAttribute('href').substring(1);
        this.scrollToSection(targetId);
        // 跳转后关闭导航
        setTimeout(() => {
          this.closeNavigation();
        }, 500);
      });
    });
    
    // 监听滚动事件，更新当前活跃区域
    window.addEventListener('scroll', () => {
      this.updateActiveSection();
    });
    
    // 监听窗口大小变化
    window.addEventListener('resize', () => {
      this.handleResize();
    });
    
    // 监听缩放变化（处理Ctrl+/Ctrl-缩放）
    window.addEventListener('wheel', (e) => {
      if (e.ctrlKey) {
        // 延迟执行以等待缩放完成
        setTimeout(() => {
          this.handleResize();
        }, 100);
      }
    }, { passive: true });
    
    // 监听ESC键关闭导航
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isExpanded) {
        this.closeNavigation();
      }
    });
    
    console.log('✅ 右侧导航初始化完成');
    
    // 确保在代码生成页面显示导航，但初始状态为收起
    this.toggleVisibility(true);
    this.closeNavigation();
    
    // 调试信息
    const debugRightNav = document.getElementById('rightNavigation');
    if (debugRightNav) {
      console.log('🔍 右侧导航元素已找到');
      console.log('📍 导航位置:', debugRightNav.getBoundingClientRect());
      console.log('👁️ 导航可见性:', window.getComputedStyle(debugRightNav).display);
    } else {
      console.error('❌ 未找到右侧导航元素');
    }
  },
  
  // 滚动到操作按钮区域
  scrollToActionButtons: function() {
    const actionSection = document.getElementById('action-buttons-section');
    if (actionSection) {
      const offsetTop = actionSection.offsetTop - 150; // 预留更多空间
      
      window.scrollTo({
        top: offsetTop,
        behavior: 'smooth'
      });
      
      // 高亮整个操作区域
      setTimeout(() => {
        this.highlightSection(actionSection);
      }, 500);
    }
  },
  
  // 高亮按钮
  highlightButton: function(button) {
    // 移除之前的高亮
    document.querySelectorAll('.button-highlight').forEach(el => {
      el.classList.remove('button-highlight');
    });
    
    // 添加按钮高亮效果
    button.classList.add('button-highlight');
    
    // 添加脉冲动画
    button.style.animation = 'buttonPulse 2s ease-in-out';
    
    // 3秒后移除高亮
    setTimeout(() => {
      button.classList.remove('button-highlight');
      button.style.animation = '';
    }, 3000);
  },
  
  // 切换导航展开/收起状态
  toggleNavigation: function() {
    const rightNav = document.getElementById('rightNavigation');
    if (rightNav) {
      if (this.isExpanded) {
        this.closeNavigation();
      } else {
        this.openNavigation();
      }
    }
  },
  
  // 打开导航
  openNavigation: function() {
    const rightNav = document.getElementById('rightNavigation');
    const trigger = document.getElementById('navTrigger');
    
    if (rightNav && trigger) {
      rightNav.classList.add('expanded');
      trigger.classList.add('expanded');
      rightNav.style.transform = 'translateY(-50%) translateX(0)';
      rightNav.style.visibility = 'visible';
      rightNav.style.opacity = '1';
      this.isExpanded = true;
      
      // 更新导航项状态
      this.updateNavigationItems();
      this.updateActiveSection();
      console.log('📖 导航已展开');
    }
  },
  
  // 关闭导航
  closeNavigation: function() {
    const rightNav = document.getElementById('rightNavigation');
    const trigger = document.getElementById('navTrigger');
    
    if (rightNav && trigger) {
      rightNav.classList.remove('expanded');
      trigger.classList.remove('expanded');
      rightNav.style.transform = 'translateY(-50%) translateX(100%)';
      rightNav.style.visibility = 'hidden';
      rightNav.style.opacity = '0';
      this.isExpanded = false;
      console.log('📕 导航已关闭');
    }
  },
  
  // 滚动到指定区域
  scrollToSection: function(sectionId) {
    const targetElement = document.getElementById(sectionId);
    if (targetElement) {
      const offsetTop = targetElement.offsetTop - 120; // 预留顶部导航栏空间
      
      window.scrollTo({
        top: offsetTop,
        behavior: 'smooth'
      });
      
      // 添加临时高亮效果
      this.highlightSection(targetElement);
    }
  },
  
  // 高亮目标区域
  highlightSection: function(element) {
    // 移除之前的高亮
    document.querySelectorAll('.section-highlight').forEach(el => {
      el.classList.remove('section-highlight');
    });
    
    // 添加高亮类
    element.classList.add('section-highlight');
    
    // 3秒后移除高亮
    setTimeout(() => {
      element.classList.remove('section-highlight');
    }, 3000);
  },
  
  // 更新当前活跃区域
  updateActiveSection: function() {
    const scrollPosition = window.scrollY + 200; // 偏移量
    let currentSection = '';
    
    // 检查每个区域是否在视口中
    this.sections.forEach(sectionId => {
      const element = document.getElementById(sectionId);
      if (element) {
        const sectionTop = element.offsetTop;
        const sectionBottom = sectionTop + element.offsetHeight;
        
        if (scrollPosition >= sectionTop && scrollPosition < sectionBottom) {
          currentSection = sectionId;
        }
      }
    });
    
    // 更新导航链接的活跃状态
    document.querySelectorAll('#quickNavigation .nav-link').forEach(link => {
      const targetId = link.getAttribute('href').substring(1);
      if (targetId === currentSection) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
    
    // 更新进度条
    this.updateProgress();
  },
  
  // 更新页面进度
  updateProgress: function() {
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight - windowHeight;
    const scrollTop = window.scrollY;
    const progress = Math.min(100, Math.max(0, (scrollTop / documentHeight) * 100));
    
    const progressBar = document.getElementById('pageProgress');
    const progressPercentage = document.getElementById('progressPercentage');
    
    if (progressBar) {
      progressBar.style.width = progress + '%';
    }
    
    if (progressPercentage) {
      progressPercentage.textContent = Math.round(progress) + '%';
    }
  },
  
  // 处理窗口大小变化
  handleResize: function() {
    // 在小屏幕上自动关闭导航
    if (window.innerWidth < 768 && this.isExpanded) {
      this.closeNavigation();
    }
    
    // 确保导航始终在正确位置（处理缩放情况）
    const navigation = document.getElementById('rightNavigation');
    if (navigation && navigation.style.display !== 'none') {
      // 重新应用定位，确保在任何缩放级别都易于识别
      navigation.style.setProperty('position', 'fixed', 'important');
      navigation.style.setProperty('right', '60px', 'important');
      navigation.style.setProperty('top', '50%', 'important');
      navigation.style.setProperty('transform', 'translateY(-50%)', 'important');
    }
  },
  
  // 显示/隐藏右侧导航（仅在代码生成标签页显示）
  toggleVisibility: function(show) {
    const trigger = document.getElementById('navTrigger');
    const navigation = document.getElementById('rightNavigation');
    
    if (trigger && navigation) {
      if (show) {
        trigger.style.display = 'block';
        // 导航面板保持隐藏，等待用户点击触发按钮
      } else {
        trigger.style.display = 'none';
        // 切换标签页时关闭导航
        this.closeNavigation();
      }
    }
  },
  
  // 更新导航项的可见性（根据内容是否存在）
  updateNavigationItems: function() {
    const navLinks = {
      'tests-section': document.getElementById('tests-section'),
      'winner-section': document.getElementById('winner-section'),
      'results-section': document.getElementById('results-section')
    };
    
    Object.entries(navLinks).forEach(([sectionId, element]) => {
      const link = document.querySelector(`#rightNavigation a[href="#${sectionId}"]`);
      if (link) {
        const hasContent = element && !element.classList.contains('hidden') && element.children.length > 0;
        
        if (hasContent) {
          link.style.display = 'flex';
          link.style.opacity = '1';
          link.style.pointerEvents = 'auto';
        } else {
          link.style.opacity = '0.5';
          link.style.pointerEvents = 'none';
        }
      }
    });
  },
  
  // 跳转到操作按钮区域
  scrollToActionButtons: function() {
    const actionSection = document.getElementById('action-buttons-section');
    if (actionSection) {
      const offsetTop = actionSection.offsetTop - 120;
      
      window.scrollTo({
        top: offsetTop,
        behavior: 'smooth'
      });
      
      // 高亮操作按钮区域
      this.highlightSection(actionSection);
      
      // 延迟关闭导航，让用户看到跳转效果
      setTimeout(() => {
        this.closeNavigation();
      }, 800);
    }
  },
  
  // 跳转到专业生成按钮并高亮
  scrollToProfessionalGenerate: function() {
    const actionSection = document.getElementById('action-buttons-section');
    const professionalBtn = document.getElementById('professionalRunBtn');
    
    if (actionSection && professionalBtn) {
      const offsetTop = actionSection.offsetTop - 120;
      
      window.scrollTo({
        top: offsetTop,
        behavior: 'smooth'
      });
      
      // 高亮整个操作区域
      this.highlightSection(actionSection);
      
      // 特别高亮专业生成按钮
      setTimeout(() => {
        professionalBtn.classList.add('button-highlight');
        setTimeout(() => {
          professionalBtn.classList.remove('button-highlight');
        }, 2000);
      }, 500);
      
      // 延迟关闭导航
      setTimeout(() => {
        this.closeNavigation();
      }, 800);
      
      console.log('🎯 跳转到专业生成按钮');
    }
  },
  
  // 滚动到页面顶部
  scrollToTop: function() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  },

  // 初始化搜索功能
  initSearch: function() {
    const searchInput = document.getElementById('navSearch');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.filterNavigation(e.target.value);
      });
    }
  },

  // 过滤导航项
  filterNavigation: function(query) {
    const navSteps = document.querySelectorAll('.nav-step');
    const actionBtns = document.querySelectorAll('.action-btn');
    const toolBtns = document.querySelectorAll('.tool-btn');
    
    const searchTerm = query.toLowerCase();
    
    // 过滤工作流程步骤
    navSteps.forEach(step => {
      const text = step.textContent.toLowerCase();
      if (text.includes(searchTerm)) {
        step.style.display = 'flex';
      } else {
        step.style.display = 'none';
      }
    });
    
    // 过滤快速操作按钮
    actionBtns.forEach(btn => {
      const text = btn.textContent.toLowerCase();
      if (text.includes(searchTerm)) {
        btn.style.display = 'flex';
      } else {
        btn.style.display = 'none';
      }
    });
    
    // 过滤工具按钮
    toolBtns.forEach(btn => {
      const text = btn.textContent.toLowerCase();
      if (text.includes(searchTerm)) {
        btn.style.display = 'flex';
      } else {
        btn.style.display = 'none';
      }
    });
  },

  // 更新时间戳
  updateTimestamp: function() {
    const timestamp = document.getElementById('navTimestamp');
    if (timestamp) {
      const now = new Date();
      const timeString = now.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      timestamp.textContent = timeString + ' 更新';
    }
  },

  // 标记步骤为已完成
  markStepCompleted: function(stepNumber) {
    const step = document.querySelector(`[data-step="${stepNumber}"]`);
    if (step) {
      step.classList.add('completed');
      step.classList.remove('active');
    }
  },

  // 标记步骤为激活状态
  markStepActive: function(stepNumber) {
    // 清除所有激活状态
    document.querySelectorAll('.nav-step').forEach(step => {
      step.classList.remove('active');
    });
    
    // 设置当前步骤为激活
    const step = document.querySelector(`[data-step="${stepNumber}"]`);
    if (step) {
      step.classList.add('active');
    }
  }
};

// 统一的初始化函数
document.addEventListener('DOMContentLoaded', function() {
  console.log('🚀 DOM加载完成，开始统一初始化...');
  
  // 旧的初始化功能
  addSelectAllButton();
  initPageAnimations();
  initCopyTestsButton();
  
  // 初始化标签页管理器
  TabManager.init();
  
  // 初始化右侧导航
  RightNavigation.init();
  
  // 初始化搜索功能
  RightNavigation.initSearch();
  
  // 更新时间戳
  RightNavigation.updateTimestamp();
  
  // 延迟执行健康检查，确保所有元素都已渲染
  setTimeout(() => {
    console.log('开始执行健康检查...');
    getHealth();
  }, 500);
  
  // 生成按钮事件
  const runBtn = document.getElementById('runBtn');
  if (runBtn) {
    runBtn.addEventListener('click', generateCode);
    console.log('✅ 生成按钮事件已绑定');
  }
  
  // 专业生成按钮事件
  const professionalRunBtn = document.getElementById('professionalRunBtn');
  if (professionalRunBtn) {
    professionalRunBtn.addEventListener('click', professionalGenerate);
    console.log('✅ 专业生成按钮事件已绑定');
  }
  
  // 保留模态框相关功能，以便向后兼容
  const closeHistoryModal = document.getElementById('closeHistoryModal');
  if (closeHistoryModal) {
    closeHistoryModal.addEventListener('click', () => HistoryManager.hide());
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

// 角色管理相关函数
async function initializeRoles() {
  console.log('🎭 初始化角色系统...');
  try {
    await loadRoles();
    setupRoleEventListeners();
  } catch (error) {
    console.error('❌ 角色系统初始化失败:', error);
  }
}

async function loadRoles() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/settings/roles`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    availableRoles = data.roles;
    currentRole = data.default_role;
    
    console.log('✅ 角色数据加载成功:', data);
    
    // 更新角色选择器
    updateRoleSelectors();
    
    // 更新角色提示词预览
    updateRolePromptPreview(currentRole);
    
  } catch (error) {
    console.error('❌ 加载角色失败:', error);
    // 使用默认角色配置
    availableRoles = {
      developer: {
        id: 'developer',
        name: '开发人员',
        description: '专注于功能实现和代码质量',
        icon: 'fas fa-code',
        color: 'blue',
        prompt_template: '作为一名经验丰富的开发人员，请根据需求编写高质量、可维护的代码。'
      }
    };
    currentRole = 'developer';
    updateRoleSelectors();
  }
}

function updateRoleSelectors() {
  const roleSelect = document.getElementById('roleSelect');
  const defaultRoleTab = document.getElementById('defaultRoleTab');
  
  if (roleSelect) {
    roleSelect.innerHTML = '';
    Object.entries(availableRoles).forEach(([roleId, role]) => {
      const option = document.createElement('option');
      option.value = roleId;
      option.textContent = role.name;
      option.selected = roleId === currentRole;
      roleSelect.appendChild(option);
    });
  }
  
  if (defaultRoleTab) {
    defaultRoleTab.innerHTML = '';
    Object.entries(availableRoles).forEach(([roleId, role]) => {
      const option = document.createElement('option');
      option.value = roleId;
      option.textContent = role.name;
      option.selected = roleId === currentRole;
      defaultRoleTab.appendChild(option);
    });
  }
}

function setupRoleEventListeners() {
  const roleSelect = document.getElementById('roleSelect');
  const defaultRoleTab = document.getElementById('defaultRoleTab');
  
  if (roleSelect) {
    roleSelect.addEventListener('change', function() {
      const selectedRole = this.value;
      currentRole = selectedRole;
      updateRoleDescription(selectedRole);
      updateRolePromptPreview(selectedRole);
    });
  }
  
  if (defaultRoleTab) {
    defaultRoleTab.addEventListener('change', function() {
      const selectedRole = this.value;
      updateRolePreview(selectedRole);
    });
    
    // 初始化时显示当前角色预览
    updateRolePreview(currentRole);
  }
}

function updateRoleDescription(roleId) {
  const roleDescElement = document.getElementById('roleDescription');
  if (roleDescElement && availableRoles[roleId]) {
    const role = availableRoles[roleId];
    roleDescElement.innerHTML = `
      <div class="flex items-center gap-2">
        <i class="${role.icon} text-${role.color}-600"></i>
        <span>${role.description}</span>
      </div>
    `;
  }
}

function updateRolePromptPreview(roleId) {
  const previewElement = document.getElementById('rolePromptPreview');
  if (previewElement && availableRoles[roleId]) {
    const role = availableRoles[roleId];
    
    // 获取角色的测试策略信息
    const testingStrategy = getRoleTestingStrategy(roleId);
    
    previewElement.innerHTML = `
      <div class="space-y-2">
        <div class="font-medium text-gray-800">${testingStrategy.name}</div>
        <div class="text-gray-600">${testingStrategy.description}</div>
        <div class="text-xs">
          <strong>测试重点：</strong>
          <div class="mt-1 pl-2 border-l-2 border-blue-200">
            ${testingStrategy.focus_areas.split('\n').filter(line => line.trim()).map(line => 
              `<div>• ${line.trim().replace(/^- /, '')}</div>`
            ).join('')}
          </div>
        </div>
      </div>
    `;
  }
}

function getRoleTestingStrategy(roleId) {
  const strategies = {
    "developer": {
      "name": "开发人员测试策略",
      "description": "注重功能完整性和代码质量验证",
      "focus_areas": `- 确保所有功能按预期工作
- 验证输入输出的正确性
- 测试常见的使用场景
- 基础性能验证`
    },
    "software_engineer": {
      "name": "软件工程师测试策略", 
      "description": "强调系统架构和工程质量的测试",
      "focus_areas": `- 模块间的交互测试
- 系统架构的健壮性
- 可扩展性验证
- 错误传播和处理
- 资源管理测试`
    },
    "system_analyst": {
      "name": "系统分析师测试策略",
      "description": "深度业务逻辑和需求符合性测试",
      "focus_areas": `- 业务逻辑的正确性
- 需求的完整实现
- 用户体验验证
- 数据处理准确性
- 业务流程完整性`
    },
    "senior_evaluator": {
      "name": "高级评测专家测试策略",
      "description": "全面的质量评估和性能测试",
      "focus_areas": `- 性能瓶颈识别
- 安全漏洞检测
- 内存和资源使用优化
- 并发和多线程安全
- 代码复杂度分析
- 可维护性评估`
    },
    "software_analyst": {
      "name": "软件分析人员测试策略",
      "description": "深入的代码分析和质量保证测试",
      "focus_areas": `- 代码质量度量
- 潜在问题识别
- 代码可读性验证
- 最佳实践符合性
- 重构建议验证
- 代码异味检测`
    }
  };
  
  return strategies[roleId] || strategies["developer"];
}

function updateRolePreview(roleId) {
  const previewContent = document.getElementById('rolePreviewContent');
  if (previewContent && availableRoles[roleId]) {
    const role = availableRoles[roleId];
    previewContent.innerHTML = `
      <div class="space-y-2">
        <div class="flex items-center gap-2">
          <i class="${role.icon} text-${role.color}-600"></i>
          <span class="font-medium">${role.name}</span>
        </div>
        <div class="text-gray-600">${role.description}</div>
        <div class="bg-white rounded p-2 text-xs">
          <strong>提示词模板:</strong><br>
          ${role.prompt_template}
        </div>
      </div>
    `;
  }
}

async function setDefaultRole(roleId) {
  try {
    const response = await fetch(`${API_BASE}/api/v1/settings/default-role`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ role_id: roleId })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const result = await response.json();
    console.log('✅ 默认角色设置成功:', result);
    
    // 显示成功消息
    showNotification(result.message, 'success');
    
    return result;
  } catch (error) {
    console.error('❌ 设置默认角色失败:', error);
    showNotification('设置默认角色失败', 'error');
    throw error;
  }
}

function getCurrentRolePrompt() {
  if (availableRoles[currentRole]) {
    return availableRoles[currentRole].prompt_template;
  }
  return '请根据需求编写高质量的代码。';
}

// 实时系统监控功能
async function startSystemMonitoring() {
  if (isMonitoringActive) return;
  
  isMonitoringActive = true;
  console.log('🔄 启动实时系统监控...');
  
  // 立即执行一次
  await updateSystemMetrics();
  
  // 每3秒更新一次指标
  metricsInterval = setInterval(async () => {
    await updateSystemMetrics();
  }, 3000);
}

function stopSystemMonitoring() {
  if (metricsInterval) {
    clearInterval(metricsInterval);
    metricsInterval = null;
  }
  isMonitoringActive = false;
  console.log('⏹️ 停止实时系统监控');
}

async function updateSystemMetrics() {
  try {
    const startTime = performance.now();
    
    // 调用系统指标API
    const response = await fetch(`${API_BASE}/api/v1/system/metrics`);
    
    const endTime = performance.now();
    const clientLatency = Math.round(endTime - startTime);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const metrics = await response.json();
    
    // 更新UI显示
    updateMetricsDisplay(metrics, clientLatency);
    
  } catch (error) {
    console.error('❌ 获取系统指标失败:', error);
    updateMetricsDisplay(null, -1);
  }
}

function updateMetricsDisplay(metrics, clientLatency) {
  // 更新延迟显示
  const latencyElement = document.getElementById('apiLatency');
  if (latencyElement) {
    if (metrics && metrics.api_latency >= 0) {
      const totalLatency = Math.round(metrics.api_latency + clientLatency);
      latencyElement.textContent = `${totalLatency} ms`;
      latencyElement.className = getLatencyColorClass(totalLatency);
    } else {
      latencyElement.textContent = '-- ms';
      latencyElement.className = 'text-2xl font-bold text-red-600';
    }
  }
  
  // 更新队列大小
  const queueElement = document.getElementById('queueSize');
  if (queueElement) {
    if (metrics) {
      queueElement.textContent = metrics.queue_size || 0;
      queueElement.className = getQueueColorClass(metrics.queue_size || 0);
    } else {
      queueElement.textContent = '--';
      queueElement.className = 'text-2xl font-bold text-gray-500';
    }
  }
  
  // 更新系统状态
  updateSystemStatus(metrics);
}

function getLatencyColorClass(latency) {
  if (latency < 0) return 'text-2xl font-bold text-red-600';
  if (latency < 100) return 'text-2xl font-bold text-blue-800';
  if (latency < 500) return 'text-2xl font-bold text-yellow-600';
  return 'text-2xl font-bold text-red-600';
}

function getQueueColorClass(queueSize) {
  if (queueSize === 0) return 'text-2xl font-bold text-green-800';
  if (queueSize < 3) return 'text-2xl font-bold text-yellow-600';
  return 'text-2xl font-bold text-red-600';
}

function updateSystemStatus(metrics) {
  const sysElement = document.getElementById("sys");
  if (!sysElement) return;
  
  if (metrics && metrics.system && metrics.system.status === 'online') {
    const providerCount = metrics.providers ? metrics.providers.available : 0;
    const providerNames = metrics.providers ? metrics.providers.names : [];
    
    sysElement.innerHTML = `
      <div class="flex items-center gap-2 text-green-600 text-sm">
        <div class="w-2 h-2 bg-green-500 rounded-full"></div>
        <span>服务在线</span>
      </div>
      <div class="text-gray-500 text-xs mt-1">
        模型: ${providerNames.slice(0, 3).join(", ")}${providerNames.length > 3 ? '...' : ''}
      </div>
      <div class="text-gray-400 text-xs mt-1">
        ${providerCount} 个提供者可用
      </div>
    `;
  } else {
    sysElement.innerHTML = `
      <div class="flex items-center gap-2 text-red-600 text-sm">
        <div class="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
        <span>连接失败</span>
      </div>
      <div class="text-gray-500 text-xs mt-1">无法获取系统状态</div>
    `;
  }
}

// 页面可见性变化时控制监控
document.addEventListener('visibilitychange', function() {
  if (document.hidden) {
    // 页面隐藏时停止监控以节省资源
    stopSystemMonitoring();
  } else {
    // 页面重新可见时恢复监控
    startSystemMonitoring();
  }
});

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
  stopSystemMonitoring();
});
