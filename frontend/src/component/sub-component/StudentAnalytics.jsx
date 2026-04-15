import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const fetchDataWithRetry = async (url, options = {}, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const { data, method = 'GET', headers = {}, withCredentials, ...rest } = options;
      const response = await fetch(url, {
        method,
        headers,
        credentials: withCredentials ? 'include' : 'same-origin',
        body: data ? JSON.stringify(data) : undefined,
        ...rest
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const json = await response.json();
      return { data: json };  // 保持跟 axios 一樣的 response.data 格式
    } catch (error) {
      if (i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
      } else {
        throw error;
      }
    }
  }
};

const renderMarkdown = (markdown) => {
  if (!markdown) return null;
  const lines = markdown.split('\n');
  let elements = [];
  let listItems = [];
  let inList = false;

  const renderList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="list-disc pl-6 mb-3 list-inside text-sm">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  lines.forEach((line, index) => {
    const trimmedLine = line.trim();
    if (trimmedLine.startsWith('-') || trimmedLine.startsWith('*') || /^\d+\./.test(trimmedLine)) {
      if (!inList) inList = true;
      const content = trimmedLine.replace(/^[-*]\s|^\d+\.\s/, '').trim();
      const boldedContent = content.split('**').map((text, i) =>
        i % 2 === 1 ? <strong key={`bold-${index}-${i}`}>{text}</strong> : text
      );
      listItems.push(<li key={`li-${index}`}>{boldedContent}</li>);
      return;
    }
    if (inList) renderList();
    if (trimmedLine.startsWith('##')) {
      elements.push(
        <h2 key={`h2-${index}`} className="text-xl font-bold mt-4 mb-2 text-indigo-800">
          {trimmedLine.substring(2).trim()}
        </h2>
      );
    } else if (trimmedLine.startsWith('#')) {
      elements.push(
        <h3 key={`h3-${index}`} className="text-lg font-semibold mt-3 mb-1 text-indigo-700">
          {trimmedLine.substring(1).trim()}
        </h3>
      );
    } else if (trimmedLine.length > 0) {
      const boldedContent = trimmedLine.split('**').map((text, i) =>
        i % 2 === 1 ? <strong key={`p-bold-${index}-${i}`}>{text}</strong> : text
      );
      elements.push(
        <p key={`p-${index}`} className="mb-2 text-sm leading-relaxed">{boldedContent}</p>
      );
    }
  });
  renderList();
  return elements;
};

const formatLastActivity = (dateString, neverLabel) => {
  if (!dateString) return neverLabel;
  try {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit', hour12: true
    });
  } catch {
    return dateString;
  }
};

const StudentAnalytics = (props) => {
  const { t } = useTranslation();

  const [studentData, setStudentData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generateState, setGenerateState] = useState({});
  const [expandedRows, setExpandedRows] = useState({});
  const [storedReports, setStoredReports] = useState({});
  const [reportLang, setReportLang] = useState('en');
  const [generatingAll, setGeneratingAll] = useState(false);
  const [generateAllResult, setGenerateAllResult] = useState(null);

  const authHeaders = {
    'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`,
      'X-Tunnel-Skip-Anti-Phishing-Page': 'true'
  };

  const fetchStudents = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetchDataWithRetry(`${API_BASE_URL}/api/analytics/students`, {
        method: 'GET',
        withCredentials: true,
        headers: authHeaders
      });
      setStudentData(response.data && response.data.length > 0 ? response.data : []);
    } catch (err) {
      console.error('Error fetching student list:', err);
      setError(t('errorLabel'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (props.activeSection === 'student-analytics' || !props.activeSection) {
      fetchStudents();
    }
  }, [props.activeSection]);

  const handleGenerateReport = async (studentId, studentName) => {
    setGenerateState(prev => ({ ...prev, [studentId]: { isLoading: true, error: null } }));
    try {
      const response = await fetchDataWithRetry(`${API_BASE_URL}/api/analytics/report`, {
        method: 'POST',
        data: { student_id: studentId },
        withCredentials: true,
        headers: { ...authHeaders, 'Content-Type': 'application/json' }
      });
      setStoredReports(prev => ({
        ...prev,
        [studentId]: {
          report_en: response.data.report_en,
          report_zh: response.data.report_zh,
          generated_at: new Date().toISOString()
        }
      }));
      setExpandedRows(prev => ({ ...prev, [studentId]: true }));
      setGenerateState(prev => ({ ...prev, [studentId]: { isLoading: false, error: null } }));
    } catch (err) {
      const errorMessage = err.response?.data?.error || t('errorFor', { name: studentName });
      setGenerateState(prev => ({ ...prev, [studentId]: { isLoading: false, error: errorMessage } }));
    }
  };

  const handleViewReport = async (studentId, studentName) => {
    if (storedReports[studentId]) {
      setExpandedRows(prev => ({ ...prev, [studentId]: !prev[studentId] }));
      return;
    }
    setGenerateState(prev => ({ ...prev, [studentId]: { isLoading: true, error: null } }));
    try {
      const response = await fetchDataWithRetry(`${API_BASE_URL}/api/analytics/report/${studentId}`, {
        method: 'GET',
        withCredentials: true,
        headers: authHeaders
      });
      setStoredReports(prev => ({
        ...prev,
        [studentId]: {
          report_en: response.data.report_en,
          report_zh: response.data.report_zh,
          generated_at: response.data.generated_at
        }
      }));
      setExpandedRows(prev => ({ ...prev, [studentId]: true }));
      setGenerateState(prev => ({ ...prev, [studentId]: { isLoading: false, error: null } }));
    } catch (err) {
      if (err.response?.status === 404) {
        setGenerateState(prev => ({
          ...prev,
          [studentId]: { isLoading: false, error: 'No report generated yet. Click "Generate Report" first.' }
        }));
        setExpandedRows(prev => ({ ...prev, [studentId]: true }));
      } else {
        setGenerateState(prev => ({
          ...prev,
          [studentId]: { isLoading: false, error: t('errorFor', { name: studentName }) }
        }));
      }
    }
  };

  const handleGenerateAll = async () => {
    setGeneratingAll(true);
    setGenerateAllResult(null);
    try {
      const response = await fetchDataWithRetry(`${API_BASE_URL}/api/analytics/report/all`, {
        method: 'POST',
        withCredentials: true,
        headers: { ...authHeaders, 'Content-Type': 'application/json' }
      });
      setGenerateAllResult(response.data);
      setStoredReports({});
    } catch (err) {
      setGenerateAllResult({ error: err.response?.data?.error || 'Failed to generate all reports' });
    } finally {
      setGeneratingAll(false);
    }
  };

  if (props.activeSection && props.activeSection !== 'student-analytics') return null;

  return (
    <div className="p-6 bg-gray-50 min-h-screen font-sans">
      <div className="max-w-7xl mx-auto bg-white rounded-xl shadow-2xl p-10 lg:p-12">

        <div className="border-b border-gray-200 pb-4 mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 className="text-3xl font-extrabold text-gray-900">
              {t('studentPerformanceAnalytics')}
            </h3>
            <p className="mt-1 text-sm text-gray-500">{t('viewStudentProgress')}</p>
          </div>

          <button
            onClick={handleGenerateAll}
            disabled={generatingAll}
            className="inline-flex items-center px-5 py-2.5 bg-green-600 text-white text-sm font-medium rounded-lg shadow hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition duration-150"
          >
            {generatingAll ? t('generating') : t('generateAllReports')}
          </button>
        </div>

        {generateAllResult && (
          <div className={`mb-4 px-4 py-3 rounded-md text-sm border ${generateAllResult.error ? 'bg-red-50 border-red-300 text-red-700' : 'bg-green-50 border-green-300 text-green-800'}`}>
            {generateAllResult.error
              ? t('generateAllError', { message: generateAllResult.error })
              : (
                <>
                  {t('generateAllSuccess', { count: generateAllResult.success?.length || 0 })}
                  {generateAllResult.failed?.length > 0 && ` ${t('generateAllFailed', { count: generateAllResult.failed.length })}`}
                </>
              )
            }
          </div>
        )}

        {isLoading && (
          <div className="text-center py-10 text-gray-600">
            <p>{t('loadingStudentData')}</p>
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md mb-4 text-sm" role="alert">
            <strong className="font-bold mr-2">{t('errorLabel')}</strong>
            <span className="block sm:inline ml-2">{error}</span>
          </div>
        )}

        {!isLoading && !error && (
          <div className="overflow-x-auto rounded-lg shadow-md">
            <table className="min-w-full divide-y divide-gray-200 table-fixed">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('studentName')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('progress')}
                  </th>
                  <th className="hidden sm:table-cell px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('avgScore')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('lastActivity')}
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {studentData.map((student) => {
                  const state = generateState[student.id] || { isLoading: false, error: null };
                  const isExpanded = expandedRows[student.id];
                  const report = storedReports[student.id];

                  return (
                    <React.Fragment key={student.id}>
                      <tr className="hover:bg-indigo-50 transition duration-150">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {student.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="w-24 bg-gray-200 rounded-full h-2.5 inline-block align-middle">
                            <div
                              className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                              style={{ width: `${student.progress}%` }}
                            />
                          </div>
                          <span className="ml-2 text-xs font-semibold text-gray-600">{student.progress}%</span>
                        </td>
                        <td className="hidden sm:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {student.avgQuizScore}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatLastActivity(student.lastActivity, t('never'))}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleGenerateReport(student.id, student.name)}
                              disabled={state.isLoading}
                              className="inline-flex items-center px-3 py-2 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed transition duration-150"
                            >
                              {state.isLoading ? t('generating') : (report ? t('regenerateReport') : t('generateReport'))}
                            </button>

                            <button
                              onClick={() => handleViewReport(student.id, student.name)}
                              disabled={state.isLoading}
                              className="inline-flex items-center px-3 py-2 border border-indigo-400 text-xs font-medium rounded-md text-indigo-600 bg-white hover:bg-indigo-50 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed transition duration-150"
                            >
                              {isExpanded ? t('hideReport') || 'Hide Report' : t('viewReport') || 'View Report'}
                            </button>
                          </div>
                        </td>
                      </tr>

                      {/* Dropdown Report Row */}
                      {isExpanded && (
                        <tr className="bg-indigo-50 border-t border-indigo-200">
                          <td colSpan="5" className="px-6 py-4">
                            {state.error && !report ? (
                              <p className="text-red-600 text-sm">{state.error}</p>
                            ) : report ? (
                              <>
                                <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                                  <p className="font-bold text-base text-indigo-800">
                                    {t('aiReportFor', { name: student.name })}
                                  </p>
                                  <div className="flex items-center gap-2">
                                    <button
                                      onClick={() => setReportLang('en')}
                                      className={`px-3 py-1 text-xs rounded-full border font-medium transition duration-150 ${
                                        reportLang === 'en'
                                          ? 'bg-indigo-600 text-white border-indigo-600'
                                          : 'text-indigo-600 border-indigo-400 hover:bg-indigo-100'
                                      }`}
                                    >
                                      English
                                    </button>
                                    <button
                                      onClick={() => setReportLang('zh')}
                                      className={`px-3 py-1 text-xs rounded-full border font-medium transition duration-150 ${
                                        reportLang === 'zh'
                                          ? 'bg-indigo-600 text-white border-indigo-600'
                                          : 'text-indigo-600 border-indigo-400 hover:bg-indigo-100'
                                      }`}
                                    >
                                      中文
                                    </button>
                                    {report.generated_at && (
                                      <span className="text-xs text-gray-400 ml-2">
                                        Generated: {formatLastActivity(report.generated_at, '')}
                                      </span>
                                    )}
                                  </div>
                                </div>

                                <div className="p-4 rounded-lg border border-indigo-300 bg-white text-gray-800 text-sm shadow-inner">
                                  {renderMarkdown(
                                    reportLang === 'en' ? report.report_en : report.report_zh
                                  )}
                                </div>
                              </>
                            ) : (
                              <p className="text-gray-500 text-sm">
                                No report generated yet. Click Generate Report to create one.
                              </p>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {studentData.length === 0 && !isLoading && (
          <p className="p-4 text-center text-gray-500">{t('noStudentData')}</p>
        )}
      </div>
    </div>
  );
};

export default StudentAnalytics;