import React, { useState } from 'react';
import axios from 'axios';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';

export default function ManimGenerator() {
  const [concept, setConcept] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const examples = [
    'Demonstrate the Pythagorean theorem with animated triangle and squares',
    'Visualize a quadratic function and its properties with animation',
    'Show how sine and cosine are related on the unit circle with animated angle',
    'Create a 3D surface plot showing z = x^2 + y^2',
    'Calculate and visualize the volume of a sphere with radius r',
    'Show how to find the surface area of a cube with animations',
    'Visualize derivatives as the slope of a tangent line',
    'Show how integration works with animated area under a curve',
    'Demonstrate matrix operations with animated transformations',
    'Visualize eigenvalues and eigenvectors of a 2x2 matrix',
    'Show how complex numbers multiply using rotation and scaling',
    'Animate solutions to a simple differential equation'
  ];

  const exampleTitles = [
    'Pythagorean Theorem',
    'Quadratic Function',
    'Trigonometry',
    '3D Surface Plot',
    'Sphere Volume',
    'Cube Surface Area',
    'Derivatives',
    'Integration',
    'Matrix Operations',
    'Eigenvalues',
    'Complex Numbers',
    'Differential Equations'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!concept.trim()) {
      setError('Please enter a mathematical concept to visualize.');
      return;
    }

    setLoading(true);
    setResults(null);
    setError(null);

    try {
      const response = await axios.post('/generate', {
        concept: concept
      }, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 60000
      });

      // Axios automatically parses JSON response
      setResults(response.data);
      
      // Highlight code after results are set
      setTimeout(() => Prism.highlightAll(), 0);

    } catch (err) {
      // Axios error handling
      if (err.response) {
        // Server responded with error status
        setError(err.response.data.error || 'Failed to generate animation');
      } else if (err.request) {
        // Request made but no response received
        setError('No response from server. Please check if the backend is running.');
      } else {
        // Error setting up the request
        setError(err.message || 'Something went wrong. Please try again.');
      }
      console.error('Error details:', err);
    } finally {
      setLoading(false);
    }
  };

  const setExample = (text) => {
    setConcept(text);
  };

  const copyCode = () => {
    if (results?.code) {
      navigator.clipboard.writeText(results.code).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Hero Section */}
      <div className="text-center mb-16">
        <h1 className="text-4xl md:text-5xl font-bold mb-6">
          <span className="gradient-text">Create Beautiful Mathematical Animations</span>
        </h1>
        <p className="text-xl text-gray-300 max-w-3xl mx-auto">
          Transform your mathematical concepts into stunning animations using AI and Manim.
          Just describe what you want to visualize, and we'll generate the code and animation for you.
        </p>
      </div>

      {/* Main Input Form */}
      <div className="max-w-4xl mx-auto">
        <div className="glass-card rounded-xl p-6 mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Text Input */}
            <div>
              <label htmlFor="concept" className="block text-sm font-medium text-gray-300 mb-2">
                Describe Your Animation
              </label>
              <textarea
                id="concept"
                name="concept"
                rows="4"
                value={concept}
                onChange={(e) => setConcept(e.target.value)}
                className="w-full px-4 py-3 bg-indigo-900 bg-opacity-50 border border-indigo-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="Example: Visualize the relationship between sine and cosine on the unit circle..."
              />
            </div>

            {/* Example Concepts */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Try These Examples</label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {examples.map((example, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setExample(example)}
                    className="px-3 py-2 text-sm bg-indigo-900 bg-opacity-50 hover:bg-opacity-75 rounded-lg text-white transition-all"
                  >
                    {exampleTitles[idx]}
                  </button>
                ))}
              </div>
            </div>

            {/* Generate Button */}
            <div className="flex justify-center">
              <button
                type="submit"
                disabled={loading}
                className="gradient-button px-8 py-3 rounded-lg text-white font-medium text-lg shadow-lg flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>{loading ? 'Generating...' : 'Generate Animation'}</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </button>
            </div>
          </form>
        </div>

        {/* Results Section */}
        {results && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Generated Code */}
              <div className="glass-card rounded-xl p-6 h-[400px] flex flex-col">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">Generated Manim Code</h3>
                  <button
                    onClick={copyCode}
                    className="text-indigo-400 hover:text-indigo-300 flex items-center space-x-2"
                  >
                    {copied ? (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Copied!</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        <span>Copy Code</span>
                      </>
                    )}
                  </button>
                </div>
                <div className="flex-1 overflow-auto">
                  <pre className="h-full">
                    <code className="language-python">{results.code}</code>
                  </pre>
                </div>
              </div>

              {/* Animation Preview */}
              <div className="glass-card rounded-xl p-6 h-[400px] flex flex-col">
                <h3 className="text-lg font-semibold mb-4">Animation Preview</h3>
                <div className="flex-1 bg-black rounded-lg overflow-hidden">
                  <video className="w-full h-full object-contain" controls>
                    <source src={results.video_url} type="video/mp4" />
                    Your browser does not support the video tag.
                  </video>
                </div>
              </div>
            </div>

            {/* Download Section */}
            <div className="flex justify-center space-x-4">
              <a
                href={results.video_url}
                download
                className="gradient-button px-6 py-2 rounded-lg text-white font-medium flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Download MP4</span>
              </a>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="loading-spinner mb-4"></div>
            <p className="text-lg text-gray-300">Generating your animation...</p>
            <p className="text-sm text-gray-400 mt-2">This may take a few moments</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="glass-card rounded-xl p-6 border border-red-500">
            <div className="flex items-center space-x-3 text-red-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-lg font-medium">Error</h3>
            </div>
            <p className="mt-2 text-gray-300">{error}</p>
          </div>
        )}
      </div>

      {/* Example Showcase */}
      <div className="mt-24">
        <h2 className="text-3xl font-bold text-center mb-12">
          <span className="gradient-text">Example Animations</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {[
            { title: 'Trigonometry', img: 'differential_equations.gif', desc: 'Visualization of sine and cosine functions on the unit circle with animated angle.' },
            { title: '3D Surface Plot', img: '3d_calculus.gif', desc: '3D visualization of the surface area of a cube with animations.' },
            { title: 'Complex Numbers', img: 'ComplexNumbersAnimation_ManimCE_v0.17.3.gif', desc: 'Geometric interpretation of complex number operations with rotation and scaling.' },
            { title: 'Linear Algebra', img: 'TrigonometryAnimation_ManimCE_v0.17.3.gif', desc: 'Differential equations to life by visualizing solution curves and phase spaces.' }
          ].map((item, idx) => (
            <div key={idx} className="glass-card rounded-xl p-6">
              <h3 className="text-lg font-semibold mb-4">{item.title}</h3>
              <div className="aspect-w-16 aspect-h-9 rounded-lg overflow-hidden mb-4 bg-indigo-900 bg-opacity-50">
                <div className="flex items-center justify-center">
                  <img src={`/static/gifs/${item.img}`} alt={item.title} className="w-full h-full object-contain" />
                </div>
              </div>
              <p className="text-gray-300">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
