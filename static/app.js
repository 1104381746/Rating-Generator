const HISTORY_STORAGE_KEY = 'shopReviewHistory';
const MAX_HISTORY_COUNT = 10;
let currentResult = '';

function saveToHistory(shopName) {
  if (!shopName || !shopName.trim()) return;
  let history = getHistory();
  history = history.filter(item => item.toLowerCase() !== shopName.toLowerCase());
  history.unshift(shopName);
  if (history.length > MAX_HISTORY_COUNT) {
    history = history.slice(0, MAX_HISTORY_COUNT);
  }
  try {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
  } catch (e) {
    console.warn('无法保存历史记录:', e);
  }
}

function getHistory() {
  try {
    const stored = localStorage.getItem(HISTORY_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (e) {
    console.warn('无法读取历史记录:', e);
    return [];
  }
}

function renderHistory() {
  const history = getHistory();
  const container = document.getElementById('historyContainer');
  if (history.length === 0) {
    container.innerHTML = '';
    return;
  }
  container.innerHTML = '';
  const title = document.createElement('div');
  title.className = 'history-title';
  title.textContent = '历史记录：';
  container.appendChild(title);

  const list = document.createElement('div');
  list.className = 'history-list';
  history.forEach(item => {
    const tag = document.createElement('span');
    tag.className = 'history-tag';
    tag.textContent = item;
    tag.addEventListener('click', () => selectHistory(item));
    list.appendChild(tag);
  });
  container.appendChild(list);
}

function selectHistory(shopName) {
  document.getElementById('shopName').value = shopName;
  document.getElementById('shopName').focus();
}

function clearHistory() {
  if (confirm('确定要清除所有历史记录吗？')) {
    localStorage.removeItem(HISTORY_STORAGE_KEY);
    renderHistory();
  }
}

async function generateReview() {
  const shopName = document.getElementById('shopName').value;
  const wordCount = document.getElementById('wordCount').value;
  const resultBox = document.getElementById('resultBox');
  const copyBtn = document.getElementById('copyBtn');
  const genBtn = document.getElementById('genBtn');
  const progressBar = document.getElementById('progressBar');

  genBtn.disabled = true;
  copyBtn.disabled = true;
  progressBar.style.display = 'block';
  resultBox.textContent = '正在生成评价...';
  resultBox.classList.remove('empty');

  try {
    const response = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        keyword: shopName,
        min_w: parseInt(wordCount.split('-')[0]),
        max_w: parseInt(wordCount.split('-')[1]),
      }),
    });
    const data = await response.json();
    if (data.success) {
      currentResult = data.review;
      resultBox.textContent = data.review;
      copyBtn.disabled = false;
      saveToHistory(shopName);
      renderHistory();
      loadGenHistory();
    } else {
      resultBox.textContent = '错误：' + (data.error || '生成失败');
      resultBox.classList.add('empty');
    }
  } catch (e) {
    resultBox.textContent = '网络错误，请检查服务是否运行';
    resultBox.classList.add('empty');
  } finally {
    genBtn.disabled = false;
    progressBar.style.display = 'none';
  }
}

function copyResult() {
  const copyBtn = document.getElementById('copyBtn');
  if (!currentResult) {
    const resultBox = document.getElementById('resultBox');
    if (resultBox && resultBox.textContent && !resultBox.classList.contains('empty')) {
      currentResult = resultBox.textContent;
    }
  }
  copyText(currentResult, copyBtn);
}

function showCopyFeedback(message, targetElement) {
  const btn = targetElement || document.getElementById('copyBtn');
  const originalText = btn.innerText;
  btn.innerText = message;
  const originalBackground = btn.style.background;
  btn.style.background = '#48bb78';
  setTimeout(() => {
    btn.innerText = originalText;
    btn.style.background = originalBackground;
  }, 2000);
}

function fallbackCopy(text, targetElement) {
  let success = false;
  const textArea = document.createElement('textarea');
  try {
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.width = '2em';
    textArea.style.height = '2em';
    textArea.style.padding = '0';
    textArea.style.border = 'none';
    textArea.style.outline = 'none';
    textArea.style.boxShadow = 'none';
    textArea.style.background = 'transparent';
    document.body.appendChild(textArea);

    if (navigator.userAgent.match(/ipad|ipod|iphone/i)) {
      const range = document.createRange();
      range.selectNodeContents(textArea);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      textArea.setSelectionRange(0, 999999);
    } else {
      textArea.focus();
      textArea.select();
    }

    success = document.execCommand('copy');
  } catch (err) {
    console.error('Fallback 执行出错:', err);
  } finally {
    if (textArea && textArea.parentNode) {
      document.body.removeChild(textArea);
    }
  }
  if (success) {
    showCopyFeedback('✅ 已复制！', targetElement);
  } else {
    alert('❌ 复制失败，请长按结果框手动复制');
  }
}

function escapeHtml(text) {
  return String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

async function loadGenHistory() {
  const list = document.getElementById('genHistoryList');
  if (!list) return;
  list.innerHTML = '';

  const loading = document.createElement('div');
  loading.textContent = '正在加载...';
  list.appendChild(loading);

  try {
    const resp = await fetch('/history?limit=30');
    const data = await resp.json();
    if (!data.success) {
      list.innerHTML = '';
      const err = document.createElement('div');
      err.className = 'history-title';
      err.textContent = '加载失败：' + (data.error || '');
      list.appendChild(err);
      return;
    }
    const items = data.records || [];
    if (items.length === 0) {
      list.innerHTML = '';
      const empty = document.createElement('div');
      empty.className = 'history-title';
      empty.textContent = '暂无历史记录';
      list.appendChild(empty);
      return;
    }

    list.innerHTML = '';
    for (const item of items) {
      const itemDiv = document.createElement('div');
      itemDiv.className = 'gen-history-item';

      const metaSection = document.createElement('div');
      metaSection.className = 'gen-history-section';
      metaSection.innerHTML =
        '<div class="gen-history-section-title">输入信息</div>' +
        '<div class="gen-history-meta" style="margin-bottom:0;">' +
        '<div class="gen-history-meta-left">' +
        `<span class="pill">${escapeHtml(item.keyword || '（未命名）')}</span>` +
        `<span class="pill">${escapeHtml((item.min_w || '') + '-' + (item.max_w || ''))} 字</span>` +
        `<span class="meta-text">${escapeHtml(item.ts_local || item.ts_utc || '')}</span>` +
        '</div></div>';

      const shopSection = document.createElement('div');
      shopSection.className = 'gen-history-section';
      let shopHtml = '<div class="gen-history-section-title">店铺信息</div>' +
        '<div class="gen-history-meta" style="margin-bottom:0;">' +
        '<div class="gen-history-meta-left">';
      if (item.shop_name) {
        shopHtml += `<span class="pill">${escapeHtml(item.shop_name)}</span>`;
      } else {
        shopHtml += '<span class="meta-text">（未获取到店铺名称）</span>';
      }
      if (item.category) {
        shopHtml += `<span class="pill">${escapeHtml(item.category)}</span>`;
      }
      shopHtml += '</div></div>';
      if (item.address) {
        shopHtml += `<div class="meta-text wrap" style="margin-top:6px;">${escapeHtml(item.address)}</div>`;
      }
      shopSection.innerHTML = shopHtml;

      const reviewBox = document.createElement('div');
      reviewBox.className = 'result-box';
      reviewBox.style.minHeight = 'auto';
      reviewBox.style.maxHeight = '200px';
      reviewBox.textContent = item.review || '';

      const copyBtn = document.createElement('button');
      copyBtn.className = 'small-copy block';
      copyBtn.textContent = '复制';
      copyBtn.addEventListener('click', () => copyText(item.review || '', copyBtn));

      itemDiv.appendChild(metaSection);
      itemDiv.appendChild(shopSection);
      itemDiv.appendChild(reviewBox);
      itemDiv.appendChild(copyBtn);
      list.appendChild(itemDiv);
    }
  } catch (e) {
    list.innerHTML = '';
    const err = document.createElement('div');
    err.className = 'history-title';
    err.textContent = '加载失败：网络错误';
    list.appendChild(err);
  }
}

async function clearGenHistory() {
  if (!confirm('确定要清空服务器上的历史生成记录吗？')) return;
  try {
    const resp = await fetch('/history/clear', { method: 'POST' });
    const data = await resp.json();
    if (data.success) {
      loadGenHistory();
    } else {
      alert('清空失败：' + (data.error || '未知错误'));
    }
  } catch (e) {
    alert('清空失败：网络错误');
  }
}

function copyText(text, targetElement) {
  if (!text) return;
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => {
      showCopyFeedback('✅ 已复制！', targetElement);
    }).catch(() => {
      fallbackCopy(text, targetElement);
    });
  } else {
    fallbackCopy(text, targetElement);
  }
}

window.onload = function () {
  renderHistory();
  loadGenHistory();
};
