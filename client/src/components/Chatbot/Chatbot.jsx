import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper, TextField, IconButton, Typography, CircularProgress, Tooltip } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ChatIcon from '@mui/icons-material/Chat';
import CloseIcon from '@mui/icons-material/Close';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import LightModeIcon from '@mui/icons-material/LightMode';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import styles from '../../styles/Chatbot.module.scss';

const Chatbot = ({ chatId, messages: propMessages = [] }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const messagesEndRef = useRef(null);
  const [darkMode, setDarkMode] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);
  // Removed chat history persistence and sidebar

  // Simple quick reply suggestions
  const quickReplies = [
    'Breastfeeding tips',
    'PPD symptoms',
    'Baby sleep schedule',
    'Nutrition after delivery'
  ];

  // --- Rich rendering helpers for bot messages ---
  const highlightKeywords = (text) => {
    const terms = [
      'Important', 'Note', 'Tip', 'Warning', 'PPD', 'depression', 'breastfeeding', 'lactation', 'sleep', 'nutrition', 'doctor', 'emergency'
    ];
    const termRegex = new RegExp(`(${terms.join('|')})`, 'gi');
    const urlSplitRegex = /(https?:\/\/[^\s)]+|\bwww\.[^\s)]+)/gi; // for splitting
    const urlTestRegex = /^(https?:\/\/[^\s)]+|\bwww\.[^\s)]+)$/i; // for testing a segment

    // Simple markdown bold **text**
    const renderBold = (str) => {
      const boldSplit = str.split(/(\*\*[^*]+\*\*)/g);
      return boldSplit.map((chunk, idx) => {
        if (/^\*\*[^*]+\*\*$/.test(chunk)) {
          return <strong key={`b-${idx}`}>{chunk.slice(2, -2)}</strong>;
        }
        return chunk;
      });
    };

    const segments = text.split(urlSplitRegex);
    return segments.map((seg, i) => {
      if (!seg) return null;
      if (urlTestRegex.test(seg)) {
        const href = seg.startsWith('http') ? seg : `https://${seg}`;
        return (
          <a key={`url-${i}`} href={href} target="_blank" rel="noopener noreferrer" className={styles.link}>
            {seg}
          </a>
        );
      }
      const parts = seg.split(termRegex);
      return parts.map((part, idx) =>
        termRegex.test(part) ? (
          <span key={`hl-${i}-${idx}`} className={styles.highlight}>{part}</span>
        ) : (
          <React.Fragment key={`txt-${i}-${idx}`}>{renderBold(part)}</React.Fragment>
        )
      );
    });
  };

  const emojiForLine = (line) => {
    const l = line.toLowerCase();
    if (l.includes('breast') || l.includes('latch')) return '🤱';
    if (l.includes('sleep')) return '😴';
    if (l.includes('nutrition') || l.includes('diet')) return '🥗';
    if (l.includes('ppd') || l.includes('depression')) return '💙';
    if (l.includes('exercise') || l.includes('walk')) return '🏃‍♀️';
    if (l.includes('warning') || l.includes('emergency')) return '⚠️';
    if (l.includes('tip') || l.includes('recommend')) return '💡';
    return '•';
  };

  const renderRichBotContent = (content) => {
    const lines = content.split(/\r?\n/);
    const elements = [];
    let i = 0;
    while (i < lines.length) {
      const raw = lines[i];
      if (!raw || raw.trim() === '') { i++; continue; }
      const l = raw.trim();
      // Divider line
      if (/^[-]{3,}$/.test(l)) {
        elements.push(<div key={`div-${i}`} className={styles.divider} />);
        i++;
        continue;
      }
      // Section heading: a short line ending with ':'
      if (!/^\s*(\* |- |\d+\.)/.test(l) && /:\s*$/.test(l) && l.length <= 60) {
        const title = l.replace(/:\s*$/, '');
        elements.push(
          <div key={`h-${i}`} className={styles.sectionHeading}>
            {highlightKeywords(title)}
          </div>
        );
        i++;
        continue;
      }
      // List items
      if (/^\s*(\* |- |\d+\.)/.test(l)) {
        const items = [];
        while (i < lines.length) {
          const cand = (lines[i] || '').trim();
          if (/^\s*(\* |- |\d+\.)/.test(cand)) {
            const stripped = cand.replace(/^\s*(\* |- |\d+\.)\s*/, '');
            items.push(stripped);
            i++;
          } else { break; }
        }
        const keyBase = i; // capture loop index for stable keys inside map
        elements.push(
          <ul key={`ul-${keyBase}`} className={styles.ulList}>
            {items.map((it, idx) => (
              <li key={`li-${keyBase}-${idx}`}>
                <span className={styles.emoji}>{emojiForLine(it)}</span>
                <span className={styles.liText}>{highlightKeywords(it)}</span>
              </li>
            ))}
          </ul>
        );
        continue;
      }
      // Paragraphs
      elements.push(
        <Typography variant="body1" key={`p-${i}`} paragraph>
          {highlightKeywords(l)}
        </Typography>
      );
      i++;
    }

    return elements;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Also scroll when loading state changes (typing indicator appears/disappears)
  useEffect(() => {
    scrollToBottom();
  }, [isLoading]);

  useEffect(() => {
    if (propMessages && propMessages.length > 0) {
      // Map backend messages to the expected format
      setMessages(
        propMessages.map(msg => ({
          type: msg.sender === 'user' ? 'user' : (msg.sender === 'bot' ? 'bot' : 'info'),
          content: msg.text,
          timestamp: msg.timestamp
        }))
      );
    } else if (propMessages && propMessages.length === 0 && chatId) {
      setMessages([]); // Clear if switching to a chat with no messages
    }
  }, [propMessages, chatId]);

  // Removed auto-loading of persisted chat history

  // Restore simple initialize behavior (best-effort, no guard)
  useEffect(() => {
    if (isOpen && messages.length === 0 && !isInitializing) {
      const initializeChatbot = async () => {
        setIsInitializing(true);
        try {
          const initResponse = await fetch('/api/chatbot/initialize', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
          });
          if (!initResponse.ok) {
            try {
              const initData = await initResponse.json();
              setMessages(prev => [...prev, { type: 'error', content: initData.error || 'Failed to initialize chatbot.' }]);
            } catch (_) {}
          }
        } catch (error) {
          setMessages(prev => [...prev, { type: 'error', content: 'Failed to connect to chatbot service.' }]);
        } finally {
          setIsInitializing(false);
        }
      };
      initializeChatbot();
    }
  }, [isOpen, messages.length, isInitializing]);

  // Removed chat list fetching

  const handleSend = async (overrideMessage) => {
    const base = typeof overrideMessage === 'string' ? overrideMessage : input;
    if (!base || !base.trim()) return;
    if (isLoading) return;

    const userMessage = base.trim();
    if (!overrideMessage) setInput('');
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('/api/chatbot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ message: userMessage })
      });
      let data;
      try {
        data = await response.json();
      } catch (_) {
        try {
          const text = await response.text();
          data = { error: text };
        } catch (__) {
          data = { error: 'Unexpected response from server.' };
        }
      }
      
      if (response.ok) {
        setMessages(prev => [...prev, { 
          type: 'bot', 
          content: data.answer,
          metadata: data.metadata,
          similarQuestions: data.similar_questions
        }]);
      } else {
        if (response.status === 401) {
          setMessages(prev => [...prev, { 
            type: 'error', 
            content: 'Please sign in to use the assistant.' 
          }]);
        } else {
          setMessages(prev => [...prev, { 
            type: 'error', 
            content: data.error || 'Sorry, I encountered an error. Please try again.' 
          }]);
        }
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickReply = (text) => {
    if (isLoading) return;
    handleSend(text);
  };

  return (
    <div className={styles.chatbotContainer}>
      {!isOpen && (
        <IconButton
          className={styles.chatButton}
          onClick={() => setIsOpen(true)}
          color="primary"
          aria-label="Open chat"
        >
          <ChatIcon />
        </IconButton>
      )}

      {isOpen && (
        <Paper className={`${styles.chatWindow} ${darkMode ? styles.dark : ''}`} elevation={3}>
          <Box className={styles.chatHeader}>
            <Typography variant="h6">Postpartum Care Assistant</Typography>
            <Box>
              <Tooltip title={darkMode ? 'Light mode' : 'Dark mode'}>
                <IconButton onClick={() => setDarkMode(v => !v)} size="small">
                  {darkMode ? <LightModeIcon /> : <DarkModeIcon />}
                </IconButton>
              </Tooltip>
              <IconButton onClick={() => setIsOpen(false)} size="small">
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
          <Box className={styles.messagesContainer}>
            {isInitializing && (
              <Box className={styles.loadingContainer}>
                <CircularProgress size={20} />
                <Typography variant="caption">Initializing Chatbot...</Typography>
              </Box>
            )}
            {messages.map((message, index) => (
              <Box
                key={index}
                className={`${styles.message} ${styles[message.type]}`}
              >
                {/* Avatar only for bot */}
                {message.type === 'bot' && (
                  <span className={`${styles.avatar} ${styles.avatarBot}`}>B</span>
                )}
                <Box className={styles.messageBody}>
                  {message.type === 'bot' ? (
                    renderRichBotContent(message.content)
                  ) : (
                    <Typography variant="body1">{message.content}</Typography>
                  )}
                  {message.type === 'bot' && (
                    <Box className={styles.messageActions}>
                      <Tooltip title={copiedIndex === index ? 'Copied!' : 'Copy'}>
                        <IconButton
                          size="small"
                          className={styles.copyButton}
                          onClick={async () => {
                            try {
                              await navigator.clipboard.writeText(message.content || '');
                              setCopiedIndex(index);
                              setTimeout(() => setCopiedIndex(null), 1200);
                            } catch (e) {}
                          }}
                        >
                          {copiedIndex === index ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
                        </IconButton>
                      </Tooltip>
                    </Box>
                  )}
                  {message.type === 'bot' && message.metadata && (
                    <Box className={styles.messageMetadata}>
                      <Typography variant="caption" color="textSecondary">
                        Source: {message.metadata.source.toUpperCase()}
                        {message.metadata.confidence && ` • Confidence: ${Math.round(message.metadata.confidence * 100)}%`}
                      </Typography>
                    </Box>
                  )}
                  {message.type === 'bot' && message.similarQuestions && message.similarQuestions.length > 0 && (
                    <Box className={styles.similarQuestions}>
                      <Typography variant="subtitle2">Related Questions:</Typography>
                      {message.similarQuestions.map((qa, idx) => (
                        <Typography key={idx} variant="body2">
                          Q: {qa.question}
                        </Typography>
                      ))}
                    </Box>
                  )}
                </Box>
              </Box>
            ))}
            {isLoading && (
              <Box className={`${styles.message} ${styles.bot}`}>
                <span className={`${styles.avatar} ${styles.avatarBot}`}>B</span>
                <span className={styles.typingIndicator}>
                  Bot is typing
                  <span className={styles.dots}>
                    <span className={styles.dot}></span>
                    <span className={styles.dot}></span>
                    <span className={styles.dot}></span>
                  </span>
                </span>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </Box>

          <Box className={styles.inputContainer}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Type your question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              multiline
              maxRows={4}
            />
            <IconButton
              color="primary"
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              className={styles.sendButton}
            >
              <SendIcon />
            </IconButton>
          </Box>

          {/* Quick Replies (available even during initialization) */}
          <Box className={styles.quickReplies}>
              {quickReplies.map((qr) => (
                <button
                  key={qr}
                  type="button"
                  className={styles.quickReplyButton}
                  onClick={() => handleQuickReply(qr)}
                >
                  {qr}
                </button>
              ))}
          </Box>
        </Paper>
      )}
    </div>
  );
};

export default Chatbot;
