const state = {
  documentId: '',
  browserPath: '/Users/moon',
  lastText: '',
  lastStructure: null,
  history: [],
  editorReady: false,
  editorRequestId: 0,
  pendingEditorRequests: new Map(),
};

const els = {
  readinessText: document.getElementById('readinessText'),
  saveText: document.getElementById('saveText'),
  sessionText: document.getElementById('sessionText'),
  documentMeta: document.getElementById('documentMeta'),
  outputPane: document.getElementById('outputPane'),
  structurePane: document.getElementById('structurePane'),
  structureSummary: document.getElementById('structureSummary'),
  historyPane: document.getElementById('historyPane'),
  metaFormat: document.getElementById('metaFormat'),
  metaChars: document.getElementById('metaChars'),
  metaTables: document.getElementById('metaTables'),
  pathInput: document.getElementById('pathInput'),
  browsePath: document.getElementById('browsePath'),
  browserPane: document.getElementById('browserPane'),
  readonlyToggle: document.getElementById('readonlyToggle'),
  paragraphIndex: document.getElementById('paragraphIndex'),
  replaceText: document.getElementById('replaceText'),
  insertText: document.getElementById('insertText'),
  savePath: document.getElementById('savePath'),
  refreshStatus: document.getElementById('refreshStatus'),
  reloadDocument: document.getElementById('reloadDocument'),
  browseBtn: document.getElementById('browseBtn'),
  goParentBtn: document.getElementById('goParentBtn'),
  usePathBtn: document.getElementById('usePathBtn'),
  openBtn: document.getElementById('openBtn'),
  textBtn: document.getElementById('textBtn'),
  structureBtn: document.getElementById('structureBtn'),
  replaceBtn: document.getElementById('replaceBtn'),
  insertBtn: document.getElementById('insertBtn'),
  saveBtn: document.getElementById('saveBtn'),
  validateBtn: document.getElementById('validateBtn'),
  clearBtn: document.getElementById('clearBtn'),
  editorFrame: document.getElementById('editorFrame'),
};

function renderOutput(label, payload) {
  els.outputPane.textContent = `${label}\n\n${JSON.stringify(payload, null, 2)}`;
}

function addHistory(title, detail) {
  state.history.unshift({ title, detail, time: new Date().toLocaleTimeString('ko-KR') });
  state.history = state.history.slice(0, 20);
  renderHistory();
}

function renderHistory() {
  if (!state.history.length) {
    els.historyPane.textContent = '아직 작업 이력이 없다.';
    return;
  }
  els.historyPane.innerHTML = '';
  for (const item of state.history) {
    const row = document.createElement('div');
    row.className = 'history-entry';
    row.innerHTML = `<strong>${item.title}</strong><small>${item.time}</small><span>${item.detail}</span>`;
    els.historyPane.appendChild(row);
  }
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return await res.json();
}

function updateSessionText() {
  els.sessionText.textContent = state.documentId ? `열린 문서: ${state.documentId}` : '열린 문서 없음';
}

function updateMeta({ format = '-', chars = '-', tables = '-', path = '' } = {}) {
  els.metaFormat.textContent = `형식: ${format}`;
  els.metaChars.textContent = `글자 수: ${chars}`;
  els.metaTables.textContent = `테이블: ${tables}`;
  els.documentMeta.textContent = path ? `현재 대상: ${path}` : '문서를 열면 형식, 글자 수, 테이블 수를 보여준다.';
}

function renderStructure(structure) {
  state.lastStructure = structure;
  if (!structure) {
    els.structureSummary.textContent = '아직 구조를 불러오지 않았다.';
    els.structurePane.textContent = '문단 인덱스와 테이블 정보를 여기에 표시한다.';
    return;
  }
  els.structureSummary.textContent = `문단 ${structure.paragraph_count}개 · 섹션 ${structure.section_count}개 · 테이블 ${structure.table_count}개`;
  els.structurePane.innerHTML = '';

  const sections = Array.isArray(structure.sections) ? structure.sections : [];
  const paragraphs = Array.isArray(structure.paragraphs) ? structure.paragraphs : [];
  const tables = Array.isArray(structure.tables) ? structure.tables : [];

  for (const section of sections) {
    const row = document.createElement('div');
    row.className = 'structure-entry';
    row.innerHTML = `<strong>섹션 ${section.section_index}: ${section.title}</strong><small>문단 시작 인덱스 ${section.paragraph_index}</small>`;
    els.structurePane.appendChild(row);
  }
  for (const paragraph of paragraphs.slice(0, 20)) {
    const row = document.createElement('div');
    row.className = 'structure-entry';
    row.innerHTML = `<strong>문단 ${paragraph.paragraph_index}</strong><small>${paragraph.text_preview || '(빈 문단)'}</small>`;
    row.addEventListener('click', () => {
      els.paragraphIndex.value = paragraph.paragraph_index;
      addHistory('문단 선택', `문단 ${paragraph.paragraph_index}을 편집 대상으로 선택`);
    });
    els.structurePane.appendChild(row);
  }
  if (tables.length) {
    for (const table of tables.slice(0, 12)) {
      const row = document.createElement('div');
      row.className = 'structure-entry';
      row.innerHTML = `<strong>테이블 · ${table.rowCount || '?'}행 × ${table.colCount || '?'}열</strong><small>page ${table.pageIndex ?? '-'} / para ${table.paragraph ?? '-'}</small>`;
      els.structurePane.appendChild(row);
    }
  }
}

function renderBrowser(entries, currentPath, parentPath) {
  state.browserPath = currentPath;
  els.browsePath.value = currentPath;
  els.browserPane.innerHTML = '';

  const parent = document.createElement('div');
  parent.className = 'browser-entry';
  parent.innerHTML = `<strong>⬆ 상위 폴더</strong><small>${parentPath}</small>`;
  parent.addEventListener('click', () => browse(parentPath));
  els.browserPane.appendChild(parent);

  for (const entry of entries) {
    const row = document.createElement('div');
    row.className = 'browser-entry';
    const icon = entry.type === 'dir' ? '📁' : '📄';
    row.innerHTML = `<strong>${icon} ${entry.name}</strong><small>${entry.path}</small>`;
    row.addEventListener('click', () => {
      if (entry.type === 'dir') {
        browse(entry.path);
        return;
      }
      els.pathInput.value = entry.path;
      if (!els.savePath.value || els.savePath.value.includes('gui_saved') || els.savePath.value.includes('.gui-edited')) {
        const ext = entry.path.endsWith('.hwp') ? '.hwp' : entry.path.endsWith('.hwpx') ? '.hwpx' : '.txt';
        els.savePath.value = entry.path.replace(ext, `.gui-edited${ext}`);
      }
      addHistory('파일 선택', entry.path);
      renderOutput('FILE_SELECTED', entry);
    });
    els.browserPane.appendChild(row);
  }
}

async function browse(path = state.browserPath) {
  const payload = await postJson('/api/browse', { path });
  if (!payload.ok) {
    renderOutput('BROWSE_FAILED', payload);
    return;
  }
  renderBrowser(payload.data.entries, payload.data.current_path, payload.data.parent_path);
}

async function refreshStatus() {
  const res = await fetch('/api/status');
  const payload = await res.json();
  const integration = payload.integration?.data || {};
  const save = payload.save?.data || {};
  els.readinessText.textContent = integration.ready
    ? `읽기 준비 완료 · workspace ${payload.allowed_workspace}`
    : '읽기 엔진 준비 안 됨';
  els.saveText.textContent = save.ready
    ? '저장 엔진 준비 완료'
    : '저장 엔진은 부분 지원 상태';
  renderOutput('STATUS', payload);
}

function base64ToArrayBuffer(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

function sendEditorRequest(method, params = {}) {
  if (!els.editorFrame?.contentWindow) {
    return Promise.reject(new Error('Editor frame is not available'));
  }
  state.editorRequestId += 1;
  const id = `req-${state.editorRequestId}`;
  return new Promise((resolve, reject) => {
    state.pendingEditorRequests.set(id, { resolve, reject });
    els.editorFrame.contentWindow.postMessage(
      {
        type: 'rhwp-request',
        id,
        method,
        params,
      },
      '*',
    );
  });
}

window.addEventListener('message', (event) => {
  const msg = event.data;
  if (!msg || msg.type !== 'rhwp-response' || !msg.id) return;
  const pending = state.pendingEditorRequests.get(msg.id);
  if (!pending) return;
  state.pendingEditorRequests.delete(msg.id);
  if (msg.error) {
    pending.reject(new Error(msg.error));
    return;
  }
  pending.resolve(msg.result);
});

els.editorFrame.addEventListener('load', async () => {
  try {
    await sendEditorRequest('ready');
    state.editorReady = true;
    addHistory('에디터 준비', 'rhwp-studio 에디터가 준비되었다.');
  } catch (error) {
    state.editorReady = false;
    addHistory('에디터 준비 실패', String(error));
  }
});

async function loadIntoEditor(path) {
  const payload = await postJson('/api/file-bytes', { path });
  if (!payload.ok) {
    renderOutput('EDITOR_LOAD_FAILED', payload);
    return false;
  }
  const buffer = base64ToArrayBuffer(payload.data.base64);
  const result = await sendEditorRequest('loadFile', {
    data: buffer,
    fileName: payload.data.file_name,
  });
  addHistory('에디터 로드', `${payload.data.file_name} / ${result.pageCount || '?'}페이지`);
  return true;
}

async function openDocument() {
  const payload = await postJson('/api/open', {
    path: els.pathInput.value,
    readonly: els.readonlyToggle.checked,
  });
  state.documentId = payload.data?.document_id || '';
  updateSessionText();
  updateMeta({ path: payload.data?.path || els.pathInput.value });
  addHistory('문서 열기', payload.data?.path || els.pathInput.value);
  renderOutput('OPEN_DOCUMENT', payload);
  if (payload.ok && state.editorReady) {
    try {
      await loadIntoEditor(payload.data.path || els.pathInput.value);
    } catch (error) {
      addHistory('에디터 로드 실패', String(error));
    }
  }
}

async function extractText() {
  const payload = await postJson('/api/text', {
    document_id: state.documentId,
    path: state.documentId ? '' : els.pathInput.value,
  });
  if (payload.ok) {
    state.lastText = payload.data.text || '';
    updateMeta({
      format: payload.data.source_format || '-',
      chars: payload.data.char_count || '-',
      tables: state.lastStructure?.table_count ?? '-',
      path: payload.data.path || els.pathInput.value,
    });
    addHistory('텍스트 추출', `${payload.data.source_format} / ${payload.data.char_count} chars`);
  }
  renderOutput('EXTRACT_TEXT', payload);
}

async function extractStructure() {
  const payload = await postJson('/api/structure', {
    document_id: state.documentId,
    path: state.documentId ? '' : els.pathInput.value,
  });
  if (payload.ok) {
    renderStructure(payload.data);
    updateMeta({
      format: payload.data.source_format || '-',
      chars: state.lastText ? state.lastText.length : '-',
      tables: payload.data.table_count || 0,
      path: payload.data.path || els.pathInput.value,
    });
    addHistory('구조 추출', `문단 ${payload.data.paragraph_count} / 테이블 ${payload.data.table_count}`);
  }
  renderOutput('EXTRACT_STRUCTURE', payload);
}

async function reloadDocumentState() {
  if (!state.documentId && !els.pathInput.value) return;
  await extractText();
  await extractStructure();
}

async function replaceParagraph() {
  const payload = await postJson('/api/replace', {
    document_id: state.documentId,
    paragraph_index: Number(els.paragraphIndex.value),
    new_text: els.replaceText.value,
  });
  if (payload.ok) {
    addHistory('문단 치환', `문단 ${els.paragraphIndex.value} 수정`);
    await reloadDocumentState();
  }
  renderOutput('REPLACE_PARAGRAPH', payload);
}

async function insertParagraph() {
  const payload = await postJson('/api/insert', {
    document_id: state.documentId,
    after_paragraph_index: Number(els.paragraphIndex.value),
    text: els.insertText.value,
  });
  if (payload.ok) {
    addHistory('문단 삽입', `문단 ${els.paragraphIndex.value} 뒤에 새 문단 추가`);
    await reloadDocumentState();
  }
  renderOutput('INSERT_PARAGRAPH', payload);
}

async function saveDocument() {
  const payload = await postJson('/api/save', {
    document_id: state.documentId,
    output_path: els.savePath.value,
  });
  if (payload.ok) {
    addHistory('저장', payload.data.output_path || els.savePath.value);
  }
  renderOutput('SAVE_AS', payload);
}

async function validateDocument() {
  const payload = await postJson('/api/validate', {
    path: els.savePath.value,
  });
  if (payload.ok) {
    addHistory('검증', `${els.savePath.value} 검증 완료`);
  }
  renderOutput('VALIDATE_DOCUMENT', payload);
}

els.refreshStatus.addEventListener('click', refreshStatus);
els.reloadDocument.addEventListener('click', reloadDocumentState);
els.browseBtn.addEventListener('click', () => browse(els.browsePath.value));
els.goParentBtn.addEventListener('click', () => browse(state.browserPath.split('/').slice(0, -1).join('/') || '/'));
els.usePathBtn.addEventListener('click', () => {
  els.pathInput.value = els.browsePath.value;
  addHistory('경로 선택', els.pathInput.value);
  renderOutput('PATH_SELECTED', { path: els.pathInput.value });
});
els.openBtn.addEventListener('click', openDocument);
els.textBtn.addEventListener('click', extractText);
els.structureBtn.addEventListener('click', extractStructure);
els.replaceBtn.addEventListener('click', replaceParagraph);
els.insertBtn.addEventListener('click', insertParagraph);
els.saveBtn.addEventListener('click', saveDocument);
els.validateBtn.addEventListener('click', validateDocument);
els.clearBtn.addEventListener('click', () => {
  els.outputPane.textContent = '아직 실행 결과가 없습니다.';
});

updateSessionText();
updateMeta();
renderHistory();
renderStructure(null);
refreshStatus();
browse('/Users/moon');
