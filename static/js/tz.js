/**
 * tz.js — Utilitários de fuso horário para o DJ VRC Booking
 *
 * Prioridade do fuso para EXIBIÇÃO:
 *   1. window.DJVRC_USER_TZ  (fuso configurado na conta — injetado pelo servidor)
 *   2. Intl.DateTimeFormat().resolvedOptions().timeZone (fuso do navegador — fallback)
 *
 * Prioridade do fuso para SALVAR (formulários):
 *   Sempre o fuso da conta (DJVRC_USER_TZ), nunca o do navegador.
 */
(function () {
  'use strict';

  // Fuso para exibição: conta > navegador
  const BROWSER_TZ = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const DISPLAY_TZ = (window.DJVRC_USER_TZ && window.DJVRC_USER_TZ !== 'null')
    ? window.DJVRC_USER_TZ
    : BROWSER_TZ;

  /**
   * Aplica conversão em todos os elementos com data-utc="<iso>" no DOM.
   * data-fmt: "date" | "time" | "full" (padrão)
   */
  function applyAll() {
    document.querySelectorAll('[data-utc]').forEach(el => {
      const iso = el.dataset.utc;
      if (!iso || iso === 'null' || iso === 'None') { el.textContent = '—'; return; }
      const fmt = el.dataset.fmt || 'full';
      let opts;
      switch (fmt) {
        case 'date': opts = { dateStyle: 'short', timeZone: DISPLAY_TZ }; break;
        case 'time': opts = { timeStyle: 'short', timeZone: DISPLAY_TZ }; break;
        default:     opts = { dateStyle: 'short', timeStyle: 'short', timeZone: DISPLAY_TZ };
      }
      try {
        el.textContent = new Date(iso).toLocaleString('pt-BR', opts);
        el.title = 'Horário em ' + DISPLAY_TZ;
      } catch (e) { el.textContent = iso; }
    });
  }

  /**
   * Retorna o offset em ms de uma timezone para uma data.
   * (positivo = à frente do UTC)
   */
  function getOffsetMs(date, tz) {
    try {
      const utcStr = date.toLocaleString('en-US', { timeZone: 'UTC' });
      const tzStr  = date.toLocaleString('en-US', { timeZone: tz });
      return new Date(tzStr) - new Date(utcStr);
    } catch (e) { return 0; }
  }

  /**
   * Converte horário recorrente (HH:MM) do fuso do DJ para o fuso do visitante.
   * Usado para exibir a disponibilidade semanal corretamente.
   * @param {string} timeStr  - "HH:MM" no fuso do DJ
   * @param {string} djTz     - IANA tz do DJ
   * @param {number} weekday  - 0=Seg…6=Dom (conforme banco)
   */
  function convertRecurringTime(timeStr, djTz) {
    if (!timeStr || !djTz || djTz === DISPLAY_TZ) return timeStr;
    try {
      const [h, m] = timeStr.split(':').map(Number);
      // Usa hoje como data de referência para calcular offset
      const ref = new Date();
      ref.setHours(h, m, 0, 0);
      const djOffsetMs   = getOffsetMs(ref, djTz);
      const visOffsetMs  = getOffsetMs(ref, DISPLAY_TZ);
      const utcMs  = ref.getTime() - djOffsetMs;
      const visMs  = utcMs + visOffsetMs;
      const result = new Date(visMs);
      const pad = n => String(n).padStart(2, '0');
      return `${pad(result.getHours())}:${pad(result.getMinutes())}`;
    } catch (e) { return timeStr; }
  }

  /**
   * Aplica conversão nos elementos de disponibilidade (data-avail-*).
   */
  function applyAvailability() {
    document.querySelectorAll('[data-avail-start]').forEach(el => {
      const start  = el.dataset.availStart;
      const end    = el.dataset.availEnd;
      const djTz   = el.dataset.availTz;
      if (!start || !djTz || djTz === DISPLAY_TZ) return;
      const newStart = convertRecurringTime(start, djTz);
      const newEnd   = end ? convertRecurringTime(end, djTz) : null;
      const span = el.querySelector('.avail-time') || el;
      span.textContent = newEnd ? `${newStart} – ${newEnd}` : newStart;
      el.title = `Original (${djTz}): ${start}${newEnd ? ' – ' + end : ''}`;
    });
  }

  /**
   * Preenche campos hidden de fuso nos formulários.
   * Sempre usa o fuso da conta (DJVRC_USER_TZ), não o do navegador.
   */
  function fillTimezoneFields() {
    document.querySelectorAll('[data-tz-field]').forEach(el => {
      el.value = DISPLAY_TZ;
    });
  }

  // Expor API pública
  window.DJVRC_TZ = { applyAll, applyAvailability, convertRecurringTime, DISPLAY_TZ, BROWSER_TZ };

  function init() {
    applyAll();
    applyAvailability();
    fillTimezoneFields();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
