"""
frontend/js/analytics.js — Privacy-first analytics tracker (Phase 10)
Sends events to own backend /api/analytics/event (NOT Google Analytics or Mixpanel).
All data stays on our servers. GDPR/DPDP Act compliant.
"""

const Analytics = (() => {
  const SESSION_KEY = 'arogya_session';
  let _sessionId = null;

  function _getSessionId() {
    if (!_sessionId) {
      _sessionId = localStorage.getItem(SESSION_KEY) ||
        (Math.random().toString(36).slice(2) + Date.now().toString(36));
      localStorage.setItem(SESSION_KEY, _sessionId);
    }
    return _sessionId;
  }

  /**
   * Core track function — fire-and-forget, never throws.
   * @param {string} event - Event name
   * @param {Object} props - Additional properties
   */
  async function track(event, props = {}) {
    try {
      const payload = {
        event: String(event).slice(0, 100),
        properties: {
          ...props,
          path: window.location.pathname,
          referrer: document.referrer || 'direct',
          user_agent: navigator.userAgent.slice(0, 100),
          timestamp_ms: Date.now(),
        },
        session_id: _getSessionId(),
      };

      // Attach token if logged in
      const headers = { 'Content-Type': 'application/json' };
      const token = localStorage.getItem('arogya_token');
      if (token) headers['Authorization'] = `Bearer ${token}`;

      await fetch('/api/analytics/event', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        keepalive: true,  // Fires even if page unloads
      });
    } catch {
      // Analytics must NEVER break the user experience
    }
  }

  return {
    track,

    // ── Named event helpers ───────────────────────────────────────────────────

    /** Track page view. Called automatically on script load. */
    pageView(page) {
      return track('page_view', { page: page || window.location.pathname });
    },

    /** Track when user sends a chat message. */
    chatSent(queryNumber, language) {
      return track('chat_sent', { query_number: queryNumber, language });
    },

    /** Track when an upgrade CTA is clicked. */
    upgradeClicked(source) {
      return track('upgrade_clicked', { source });
    },

    /** Track successful Premium purchase. */
    premiumPurchased(plan, amountInr) {
      return track('subscription_purchased', { plan, amount_inr: amountInr });
    },

    /** Track when a premium module is opened. */
    moduleOpened(module) {
      return track('module_opened', { module });
    },

    /** Track emergency detection (no PII logged). */
    emergencyDetected() {
      return track('emergency_detected');
    },

    /** Track data export (DPDP compliance). */
    dataExported() {
      return track('data_exported');
    },

    /** Track referral share. */
    referralShared(channel) {
      return track('referral_shared', { channel });
    },

    /** Track onboarding step completion. */
    onboardingStep(step, completed) {
      return track('onboarding_step', { step, completed });
    },

    /** Track health score sharing. */
    scoreShared(score) {
      return track('score_shared', { score });
    },

    /** Track notification interaction. */
    notificationClicked(notificationId, type) {
      return track('notification_clicked', { notification_id: notificationId, type });
    },
  };
})();

// ── Auto page-view tracking ────────────────────────────────────────────────────
// Fire page_view immediately when this script loads
(function () {
  const PAGE_MAP = {
    '/': 'landing',
    '/dashboard': 'dashboard',
    '/chat': 'chat',
    '/pricing': 'pricing',
    '/profile': 'profile',
    '/family': 'family',
    '/reports': 'reports',
    '/onboarding': 'onboarding',
    '/nutrition': 'nutrition_module',
    '/fitness': 'fitness_module',
    '/mindfulness': 'mindfulness_module',
    '/genetics': 'genetics_module',
    '/food-scanner': 'food_scanner',
    '/drug-checker': 'drug_checker',
    '/emergency': 'emergency',
    '/admin': 'admin',
    '/login': 'login',
    '/signup': 'signup',
  };
  const page = PAGE_MAP[window.location.pathname] || window.location.pathname;
  Analytics.pageView(page);
})();

// ── Expose globally ────────────────────────────────────────────────────────────
window.Analytics = Analytics;
