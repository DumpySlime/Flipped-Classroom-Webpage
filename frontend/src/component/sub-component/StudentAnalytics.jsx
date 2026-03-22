import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const API_BASE_URL = 'http://localhost:5000';

const fetchDataWithRetry = async (url, options = {}, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await axios(url, options);
      return response;
    } catch (error) {
      if (i < retries - 1) {
        const delay = Math.pow(2, i) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
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
        <p key={`p-${index}`} className="mb-2 text-sm leading-relaxed">
          {boldedContent}
        </p>
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
    const options = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    };
    return date.toLocaleString('en-US', options);
  } catch (error) {
    return dateString;
  }
};

const StudentAnalytics = (props) => {
  const { t } = useTranslation();

  const [studentData, setStudentData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reportState, setReportState] = useState({
    targetId: null,
    report: null,
    error: null,
    isLoading: false,
  });

  const fetchStudents = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetchDataWithRetry(`${API_BASE_URL}/api/analytics/students`, {
        method: 'GET',
        withCredentials: true,
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
        }
      });

      if (response.data && response.data.length > 0) {
        setStudentData(response.data);
      } else {
        setStudentData([]);
      }
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
    if (reportState.isLoading) return;

    setReportState({
      targetId: studentId,
      report: null,
      error: null,
      isLoading: true
    });

    try {
      const response = await fetchDataWithRetry(`${API_BASE_URL}/api/analytics/report`, {
        method: 'POST',
        data: { student_id: studentId },
        withCredentials: true,
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      setReportState(prev => ({
        ...prev,
        report: response.data.report,
        isLoading: false,
        error: null
      }));
    } catch (err) {
      console.error('Error generating AI report:', err.response ? err.response.data : err.message);
      const errorMessage = err.response?.data?.error || t('errorFor', { name: studentName });
      setReportState(prev => ({
        ...prev,
        report: null,
        isLoading: false,
        error: errorMessage
      }));
    }
  };

  if (props.activeSection && props.activeSection !== 'student-analytics') return null;

  return (
    <div className="p-6 bg-gray-50 min-h-screen font-sans">
      <div className="max-w-7xl mx-auto bg-white rounded-xl shadow-2xl p-10 lg:p-12">
        <div className="border-b border-gray-200 pb-4 mb-6">
          <h3 className="text-3xl font-extrabold text-gray-900">
            {t('studentPerformanceAnalytics')}
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {t('viewStudentProgress')}
          </p>
        </div>

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
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('studentName')}
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('progress')}
                  </th>
                  <th scope="col" className="hidden sm:table-cell px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('avgScore')}
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('lastActivity')}
                  </th>
                  <th scope="col" className="px-6 py-3">
                    <span className="sr-only">{t('actions')}</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {studentData.map((student) => (
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
                          ></div>
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
                        <button
                          onClick={() => handleGenerateReport(student.id, student.name)}
                          disabled={reportState.isLoading && reportState.targetId === student.id}
                          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-150"
                        >
                          {reportState.isLoading && reportState.targetId === student.id
                            ? t('generating')
                            : t('generateReport')}
                        </button>
                      </td>
                    </tr>

                    {reportState.targetId === student.id && (reportState.report || reportState.error) && (
                      <tr className="bg-indigo-50 border-t border-indigo-200">
                        <td colSpan="6" className="px-6 py-4">
                          <p className="font-bold text-base text-indigo-800 mb-2">
                            {reportState.report
                              ? t('aiReportFor', { name: student.name })
                              : t('errorFor', { name: student.name })}
                          </p>
                          <div className={`p-4 rounded-lg border shadow-inner bg-white text-gray-800 text-sm ${reportState.error ? 'border-red-400 bg-red-50 text-red-700' : 'border-indigo-300'}`}>
                            {reportState.report ? renderMarkdown(reportState.report) : reportState.error}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
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
