/**
 * tz.js — Utilitários de fuso horário para o DJ VRC Booking
 * Converte timestamps UTC → fuso local do visitante usando a API Intl nativa do browser.
 */

(function () {
  'use strict';

  // Fuso do visitante detectado pelo browser
  const VISITOR_TZ = Intl.DateTimeFormat().resolvedOptions().timeZone;

  /**
   * Formata uma string ISO UTC (ex: "2026-07-04T23:00:00Z") no fuso local do visitante.
   * @param {string} isoUtc - string ISO 8601 com "Z" ou "+00:00"
   * @param {object} opts   - opções Intl.DateTimeFormat (opcional)
   * @returns {string}
   */
  function formatUtc(isoUtc, opts) {
    if (!isoUtc) return '—';
    try {
      const dt = new Date(isoUtc);
      const defaultOpts = {
        dateStyle: 'short',
        timeStyle: 'short',
        timeZone: VISITOR_TZ,
      };
      return dt.toLocaleString('pt-BR', opts || defaultOpts);
    } catch (e) {
      return isoUtc;
    }
  }

  /**
   * Aplica conversão em todos os elementos com data-utc="<iso>" no DOM.
   * Atributos opcionais:
   *   data-fmt="date"  → só data
   *   data-fmt="time"  → só hora
   *   data-fmt="full"  → data + hora (padrão)
   *   data-fmt="weekday" → dia da semana + hora
   */
  function applyAll() {
    document.querySelectorAll('[data-utc]').forEach(el => {
      const iso = el.dataset.utc;
      if (!iso || iso === 'null' || iso === 'None') {
        el.textContent = '—';
        return;
      }
      const fmt = el.dataset.fmt || 'full';
      let opts;
      switch (fmt) {
        case 'date':
          opts = { dateStyle: 'short', timeZone: VISITOR_TZ };
          break;
        case 'time':
          opts = { timeStyle: 'short', timeZone: VISITOR_TZ };
          break;
        case 'weekday':
          opts = { weekday: 'long', hour: '2-digit', minute: '2-digit', timeZone: VISITOR_TZ };
          break;
        default: // 'full'
          opts = { dateStyle: 'short', timeStyle: 'short', timeZone: VISITOR_TZ };
      }
      try {
        el.textContent = new Date(iso).toLocaleString('pt-BR', opts);
        // Adicionar tooltip com o fuso
        el.title = `Horário exibido em ${VISITOR_TZ}`;
      } catch (e) {
        el.textContent = iso;
      }
    });
  }

  // Expor para uso global
  window.DJVRC_TZ = { formatUtc, applyAll, VISITOR_TZ };

  // Aplica automaticamente quando DOM carrega
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyAll);
  } else {
    applyAll();
  }
})();
