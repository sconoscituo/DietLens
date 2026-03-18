// DietLens 공통 JavaScript

/**
 * HTML 특수문자 이스케이프 (XSS 방지)
 * @param {string} str - 이스케이프할 문자열
 * @returns {string}
 */
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * 토스트 알림 표시
 * @param {string} message - 표시할 메시지
 * @param {'success'|'error'} type - 알림 타입
 */
function showToast(message, type = 'success') {
  // 기존 토스트 제거
  document.querySelectorAll('.toast').forEach(t => t.remove());

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  // 3초 후 자동 제거
  setTimeout(() => toast.remove(), 3100);
}

/**
 * 숫자를 소수점 1자리로 포맷
 * @param {number} value
 * @returns {string}
 */
function formatNum(value) {
  return parseFloat(value || 0).toFixed(1);
}

/**
 * 칼로리 색상 클래스 반환 (목표 대비)
 * @param {number} pct - 퍼센트
 * @returns {string}
 */
function calorieColorClass(pct) {
  if (pct >= 110) return 'text-red-500';
  if (pct >= 90) return 'text-yellow-500';
  return 'text-emerald-500';
}

/**
 * 날짜 문자열을 한국어 형식으로 변환
 * @param {string} dateStr - YYYY-MM-DD
 * @returns {string}
 */
function formatDateKr(dateStr) {
  const d = new Date(dateStr);
  const days = ['일', '월', '화', '수', '목', '금', '토'];
  return `${d.getMonth() + 1}월 ${d.getDate()}일 (${days[d.getDay()]})`;
}

/**
 * 오늘 날짜를 YYYY-MM-DD 형식으로 반환
 * @returns {string}
 */
function getTodayStr() {
  return new Date().toISOString().slice(0, 10);
}

/**
 * API 요청 공통 처리
 * @param {string} url
 * @param {object} options
 * @returns {Promise<any>}
 */
async function apiRequest(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: '서버 오류' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    if (res.status === 204) return null;
    return await res.json();
  } catch (e) {
    showToast(e.message || '오류가 발생했습니다', 'error');
    throw e;
  }
}

// 전역 Enter 키 검색 지원
document.addEventListener('DOMContentLoaded', () => {
  // 날짜 입력 필드 최대값을 오늘로 설정
  document.querySelectorAll('input[type="date"]').forEach(input => {
    if (!input.max) input.max = getTodayStr();
  });
});
