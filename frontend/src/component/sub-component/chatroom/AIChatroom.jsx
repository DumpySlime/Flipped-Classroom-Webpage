import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import 'katex/dist/katex.min.css';
import './AIChatroom.css';

const AIChatroom = () => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved === 'true';
  });

  const [messages, setMessages] = useState([
    { role: 'ai', text: '**你好！** 我係你嘅學習助手！', model: 'deepseek' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [readerMode, setReaderMode] = useState(false);
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);

  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    localStorage.setItem('darkMode', newMode);
  };

  useEffect(() => {
    document.body.classList.toggle('dark-mode', isDarkMode);
  }, [isDarkMode]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  const handleClear = () => {
    if (isStreaming) handleStop();
    setMessages([
      { role: 'ai', text: '**你好！** 我係你嘅學習助手！', model: 'deepseek' }
    ]);
    setInput('');
    setStreamingMessage('');
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setLoading(false);
    if (streamingMessage.trim()) {
      setMessages(prev => [...prev, { role: 'ai', text: streamingMessage, model: 'deepseek' }]);
    }
    setStreamingMessage('');
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMessage = input.trim();
    setInput('');
    const newMessages = [...messages, { role: 'user', text: userMessage }];
    setMessages(newMessages);
    setLoading(true);
    setIsStreaming(true);
    setStreamingMessage('');

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch('http://localhost:5000/api/ai/ai-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMessages.map(m => ({
            role: m.role === 'ai' ? 'assistant' : 'user',
            content: m.text
          }))
        }),
        signal: controller.signal,
        credentials: 'include'
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = '';
      let fullReply = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += value;

        let boundary = buffer.indexOf('\n\n');
        while (boundary > -1) {
          const chunk = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);

          const dataLine = chunk.split('\n').find(l => l.startsWith('data: '));
          if (dataLine) {
            const payload = dataLine.slice(6).trim();
            if (payload && payload !== '[DONE]') {
              try {
                const json = JSON.parse(payload);
                const content = json.content;
                if (typeof content === 'string' && content) {
                  fullReply += content;
                  setStreamingMessage(fullReply);
                }
                if (json.error) throw new Error(json.error);
              } catch (e) {
                console.warn('SSE parse error:', payload);
              }
            }
          }
          boundary = buffer.indexOf('\n\n');
        }
      }

      if (fullReply.trim()) {
        setMessages(prev => [...prev, { role: 'ai', text: fullReply, model: 'deepseek' }]);
      }

    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Stream aborted by user');
      } else {
        setMessages(prev => [...prev, { 
          role: 'ai', 
          text: `**連線錯誤**\n\n\`\`\`\n${error.message}\n\`\`\`\n\n請檢查 Backend 有冇啟動`, 
          model: 'error' 
        }]);
      }
    } finally {
      setStreamingMessage('');
      setIsStreaming(false);
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <>
      <div className={`ai-chatroom ${isDarkMode ? 'dark' : 'light'}`}>
        <div className="chat-header">
          <div className="header-left">
            <button className="clear-btn" onClick={handleClear}>
              清除
            </button>
          </div>

          <h3 style={{ color: '#FFD700', margin: 0 }}>小鼠工具</h3>

          <div className="header-right">
            <button className="dark-mode-btn" onClick={toggleDarkMode}>
              {isDarkMode ? 'Light Mode' : 'Dark Mode'}
            </button>
            <button className="reader-mode-btn" onClick={() => setReaderMode(true)}>
              閱讀模式
            </button>
          </div>
        </div>

        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}-message`}>
              <div className={`message-bubble ${msg.role === 'ai' ? 'ai' : 'user'}`}>
                {msg.role === 'ai' ? (
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                      code({node, inline, className, children, ...props}) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                          <SyntaxHighlighter
                            style={tomorrow}
                            language={match[1]}
                            PreTag="div"
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      }
                    }}
                  >
                    {msg.text}
                  </ReactMarkdown>
                ) : (
                  <div>{msg.text}</div>
                )}
              </div>
            </div>
          ))}

          {isStreaming && (
          <div className="message ai-message">
            <div className="message-bubble ai streaming-bubble"
            style={{ position: 'relative' }}>
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  code({node, inline, className, children, ...props}) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter style={tomorrow} language={match[1]} {...props}>
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>{children}</code>
                    );
                  }
                }}
              >
                {streamingMessage || '　'}
              </ReactMarkdown>
              <div className="typing">
                <span></span><span></span><span></span>
              </div>
              <button className="stop-btn" onClick={handleStop}>
                停止
              </button>
            </div>
          </div>
        )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="輸入訊息..."
            rows="3"
            disabled={loading}
          />
          <button onClick={handleSend} disabled={loading || !input.trim()}>
            {loading ? '思考中...' : '發送'}
          </button>
        </div>
      </div>

      {readerMode && (
        <div 
          className={`reader-overlay ${isDarkMode ? 'dark-mode' : 'light-mode'}`}
          style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 9999 }}
          onClick={() => setReaderMode(false)}
        >
          <div className="reader-content" onClick={(e) => e.stopPropagation()}>
            <button className="close-reader" onClick={() => setReaderMode(false)}>×</button>
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]} 
              rehypePlugins={[rehypeKatex]}
              components={{
                code({node, inline, className, children, ...props}) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter 
                      style={tomorrow} 
                      language={match[1]} 
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>{children}</code>
                  );
                }
              }}
            >
              {messages
                .filter(m => m.role === 'ai')
                .map(m => m.text)
                .join('\n\n---\n\n')}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </>
  );
};

export default AIChatroom;