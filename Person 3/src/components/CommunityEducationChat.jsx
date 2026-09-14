import React, { useState, useRef, useEffect } from 'react';

/**
 * CommunityEducationChat — standalone FAQ chat widget.
 *
 * Calls the CommunityEducationBot's respond() endpoint via a simple
 * REST POST (or WebSocket, depending on backend wiring).
 *
 * This component is COMPLETELY SEPARATE from AgentConsole and carries
 * no risk-scoring, SVI, case-file, or audit-logging UI.
 */

const FALLBACK_RESPONSE = {
  matched_intent: 'fallback',
  response:
    "I'm sorry, I couldn't find a specific answer for that. For immediate help, please call 14566 (NHAA Helpline) — it's free, confidential, and available 24/7.",
  language: 'en',
};

export default function CommunityEducationChat({ apiEndpoint = '/api/education-bot' }) {
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      text: 'Welcome! I can help answer common questions about filing complaints, legal aid, helpline services, and more. Type your question below.\n\nयदि आप हिंदी में पूछना चाहें तो भी पूछ सकते हैं।',
      intent: 'welcome',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isCrisis, setIsCrisis] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMsg = { role: 'user', text: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: trimmed }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (data.matched_intent === 'crisis_redirect') {
        setIsCrisis(true);
      }

      setMessages((prev) => [
        ...prev,
        { role: 'bot', text: data.response, intent: data.matched_intent },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'bot', text: FALLBACK_RESPONSE.response, intent: 'error' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={styles.container}>
      {/* ── Header ─────────────────────────────────────────────── */}
      <div style={styles.header}>
        <div style={styles.headerIcon}>📚</div>
        <div>
          <div style={styles.headerTitle}>Community Education Assistant</div>
          <div style={styles.headerSub}>
            FAQ &amp; Information — not a crisis service
          </div>
        </div>
      </div>

      {/* ── Messages ───────────────────────────────────────────── */}
      <div style={styles.messageArea}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              ...styles.bubble,
              ...(msg.role === 'user' ? styles.userBubble : styles.botBubble),
              ...(msg.intent === 'crisis_redirect' ? styles.crisisBubble : {}),
            }}
          >
            {msg.intent === 'crisis_redirect' && (
              <div style={styles.crisisTag}>⚠️ Important — please read</div>
            )}
            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
          </div>
        ))}

        {loading && (
          <div style={{ ...styles.bubble, ...styles.botBubble, opacity: 0.6 }}>
            <span style={styles.typing}>Typing…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Crisis banner (sticky once triggered) ──────────────── */}
      {isCrisis && (
        <div style={styles.crisisBanner}>
          If you are in distress, please call{' '}
          <strong style={{ color: '#fff' }}>14566</strong> now — 24/7, free,
          confidential.
        </div>
      )}

      {/* ── Input ──────────────────────────────────────────────── */}
      <div style={styles.inputRow}>
        <textarea
          style={styles.textarea}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question… (Hindi, English, or Hinglish)"
          rows={1}
        />
        <button
          style={{
            ...styles.sendBtn,
            opacity: input.trim() ? 1 : 0.4,
          }}
          onClick={sendMessage}
          disabled={!input.trim() || loading}
        >
          Send
        </button>
      </div>

      <div style={styles.disclaimer}>
        This is an informational chatbot only. It does not replace professional
        counseling or crisis support. If you need immediate help, call{' '}
        <strong>14566</strong>.
      </div>
    </div>
  );
}

/* ── Inline styles ────────────────────────────────────────────────── */
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    width: '100%',
    maxWidth: 520,
    margin: '0 auto',
    height: '100%',
    maxHeight: 720,
    borderRadius: 16,
    overflow: 'hidden',
    background: '#0f1117',
    border: '1px solid rgba(255,255,255,0.08)',
    fontFamily: "'Inter', 'Segoe UI', sans-serif",
    color: '#e2e8f0',
    fontSize: 14,
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '14px 18px',
    background: 'linear-gradient(135deg, #1a1d2e 0%, #141722 100%)',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
  },
  headerIcon: { fontSize: 24 },
  headerTitle: { fontWeight: 700, fontSize: 15, letterSpacing: 0.3 },
  headerSub: { fontSize: 11, color: '#94a3b8', marginTop: 2 },
  messageArea: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px 14px',
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  bubble: {
    maxWidth: '85%',
    padding: '10px 14px',
    borderRadius: 14,
    lineHeight: 1.55,
    fontSize: 13,
  },
  userBubble: {
    alignSelf: 'flex-end',
    background: '#2563eb',
    color: '#fff',
    borderBottomRightRadius: 4,
  },
  botBubble: {
    alignSelf: 'flex-start',
    background: '#1e2130',
    border: '1px solid rgba(255,255,255,0.06)',
    borderBottomLeftRadius: 4,
  },
  crisisBubble: {
    background: '#3b1318',
    border: '1px solid #ef4444',
  },
  crisisTag: {
    fontSize: 11,
    fontWeight: 700,
    color: '#f87171',
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  crisisBanner: {
    padding: '8px 14px',
    background: '#7f1d1d',
    color: '#fca5a5',
    fontSize: 12,
    textAlign: 'center',
    fontWeight: 500,
  },
  inputRow: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: 8,
    padding: '10px 14px',
    borderTop: '1px solid rgba(255,255,255,0.06)',
    background: '#12141f',
  },
  textarea: {
    flex: 1,
    resize: 'none',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 10,
    padding: '9px 12px',
    fontSize: 13,
    background: '#1a1d2e',
    color: '#e2e8f0',
    outline: 'none',
    fontFamily: 'inherit',
  },
  sendBtn: {
    padding: '9px 16px',
    borderRadius: 10,
    border: 'none',
    background: '#2563eb',
    color: '#fff',
    fontWeight: 600,
    fontSize: 13,
    cursor: 'pointer',
  },
  typing: {
    display: 'inline-block',
    animation: 'pulse 1.2s infinite',
    color: '#94a3b8',
    fontSize: 12,
  },
  disclaimer: {
    padding: '8px 14px',
    fontSize: 10,
    color: '#64748b',
    textAlign: 'center',
    background: '#0c0e17',
    borderTop: '1px solid rgba(255,255,255,0.04)',
  },
};
