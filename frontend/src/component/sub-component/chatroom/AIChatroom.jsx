import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './AIChatroom.css';

const AIChatroom = () => {
  const [messages, setMessages] = useState([
    { 
      role: 'ai', 
      text: '你好！你有咩問題？', 
      model: 'deepseek' 
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
        text: `只限英文輸入，或無晒Credit`, 
        model: 'error' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-chatroom">
      <div className="chat-header" style={{ background: '#00d4aa' }}>
        <h3>Chatroom</h3>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}-message`}>
            <div className={`message-bubble ${msg.role === 'ai' ? 'ai' : 'user'}`}>
              {msg.role === 'ai' && (
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
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
              )}
              {msg.role === 'user' && <div>{msg.text}</div>}
            </div>
          </div>
        ))}
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
          placeholder="你有咩問題"
          rows="3"
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          {loading ? '思考中...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default AIChatroom;