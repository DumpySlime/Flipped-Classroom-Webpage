// src/components/sub-component/chatroom/AIChatroom.jsx
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import 'katex/dist/katex.min.css';
import './AIChatroom.css';

const AIChatroom = () => {
  const [messages, setMessages] = useState([
    { 
      role: 'ai', 
      text: '**你好！** 我係你嘅 DeepSeek AI 學習助手！\n\n支援 **Markdown、程式碼、數學公式**！\n\n試下問我：\n```js\nconsole.log("Hello FYP!")\n```\n或者：\n$$ E = mc^2 $$', 
      model: 'deepseek' 
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedMessages, setExpandedMessages] = useState({});
  const [readerMode, setReaderMode] = useState(false);
  const messagesEndRef = useRef(null);

  // 自動滾動
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 長訊息自動定位
  useEffect(() => {
    const lastAiMsg = messages[messages.length - 1];
    if (lastAiMsg?.role === 'ai' && lastAiMsg.text.length > 500) {
      setTimeout(() => {
        const bubble = document.querySelector('.message-bubble:last-child');
        bubble?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 600);
    }
  }, [messages]);

  const toggleExpand = (index) => {
    setExpandedMessages(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
    setLoading(true);

    try {
      const response = await axios.post(
        'http://localhost:5000/api/ai-chat',
        { message: userMessage, model: 'deepseek' },
        {
          timeout: 90000,
          withCredentials: true,
          headers: { 'Content-Type': 'application/json' }
        }
      );

      const aiReply = response.data.reply || "DeepSeek 無回應...";
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: aiReply, 
        model: 'deepseek' 
      }]);

    } catch (error) {
      const errMsg = error.response?.data?.error || error.message;
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: `**DeepSeek 錯誤**\n\n\`\`\`\n${errMsg}\n\`\`\`\n\n建議：\n- 檢查 .env 有冇 \`DEEPSEEK_API_KEY\`\n- 充值 $1 USD 喺 https://platform.deepseek.com`, 
        model: 'error' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="ai-chatroom">
        <div className="chat-header" style={{ background: 'linear-gradient(135deg, #00d4aa, #00a08a)' }}>
          <h3>Chatroom</h3>
          <button 
            className="reader-mode-btn"
            onClick={() => setReaderMode(true)}
          >
            Read Mode
          </button>
        </div>

        <div className="chat-messages">
          {messages.map((msg, i) => {
            const isLong = msg.text.length > 350;
            const isExpanded = expandedMessages[i];

            return (
              <div key={i} className={`message ${msg.role}-message`}>
                <div className={`message-bubble ${msg.role === 'ai' ? 'ai' : 'user'} ${isExpanded ? 'expanded' : ''}`}>
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

                  {isLong && (
                    <button 
                      className="expand-btn"
                      onClick={() => toggleExpand(i)}
                    >
                      {isExpanded ? 'Collapse' : 'Expand Full Text'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="message ai-message">
              <div className="message-bubble ai typing">
                <span></span><span></span><span></span>
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
            placeholder="Ask me anything..."
            rows="3"
          />
          <button onClick={handleSend} disabled={loading || !input.trim()}>
            {loading ? 'Thinking...' : 'Send'}
          </button>
        </div>
      </div>

      {readerMode && (
        <div className="reader-overlay" onClick={() => setReaderMode(false)}>
          <div className="reader-content" onClick={(e) => e.stopPropagation()}>
            <button className="close-reader" onClick={() => setReaderMode(false)}>×</button>
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