import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Placeholder Mock Data
const mockData = [
    { id: 'S001', name: "Alice Smith", progress: 85, avgQuizScore: 92, aiInteractions: 15, lastActivity: "2 hours ago", email: "alice@school.edu" },
    { id: 'S002', name: "Bob Johnson", progress: 45, avgQuizScore: 68, aiInteractions: 4, lastActivity: "2 days ago", email: "bob@school.edu" },
    { id: 'S003', name: "Charlie Brown", progress: 95, avgQuizScore: 98, aiInteractions: 25, lastActivity: "30 minutes ago", email: "charlie@school.edu" },
];

// Base URL for your Flask Backend (Assuming this is defined for API calls)
const API_BASE_URL = 'http://localhost:5000'; 

// Function for exponential backoff retry logic (Good practice for API calls)
const fetchDataWithRetry = async (url, options = {}, retries = 3) => {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await axios(url, options);
            return response;
        } catch (error) {
            if (i < retries - 1) {
                const delay = Math.pow(2, i) * 1000;
                // Simple delay before retrying
                await new Promise(resolve => setTimeout(resolve, delay));
            } else {
                throw error;
            }
        }
    }
};

/**
 * Utility function to convert basic markdown (like **bold**, lists, and headings)
 * into formatted JSX elements for better readability.
 * This is crucial as the raw LLM output is markdown text.
 */
const renderMarkdown = (markdown) => {
    if (!markdown) return null;

    const lines = markdown.split('\n');
    let elements = [];
    let listItems = [];
    let inList = false;

    const renderList = () => {
        if (listItems.length > 0) {
            // Apply Tailwind classes for list formatting
            elements.push(<ul key={`list-${elements.length}`} className="list-disc pl-6 mb-3 list-inside text-sm">
                {listItems}
            </ul>);
            listItems = [];
        }
        inList = false;
    };

    lines.forEach((line, index) => {
        const trimmedLine = line.trim();

        // Check for List Items (starts with *, -, or number + .)
        if (trimmedLine.startsWith('* ') || trimmedLine.startsWith('- ') || /^\d+\. /.test(trimmedLine)) {
            if (!inList) inList = true;
            
            const content = trimmedLine.replace(/^(\* |\- |\d+\. )/, '').trim();
            const boldedContent = content.split('**').map((text, i) => 
                i % 2 === 1 ? <strong key={`bold-${index}-${i}`}>{text}</strong> : text
            );
            
            listItems.push(<li key={`li-${index}`} className="mb-0.5">{boldedContent}</li>);
            return;
        } 
        
        if (inList) {
            renderList();
        }

        // Check for Headings
        if (trimmedLine.startsWith('## ')) {
            // Tailwind classes for H2
            elements.push(<h2 key={`h2-${index}`} className="text-xl font-bold mt-4 mb-2 text-indigo-800">{trimmedLine.substring(3).trim()}</h2>);
        } else if (trimmedLine.startsWith('#')) {
            // Tailwind classes for H3
            elements.push(<h3 key={`h3-${index}`} className="text-lg font-semibold mt-3 mb-1 text-indigo-700">{trimmedLine.substring(1).trim()}</h3>);
        }
        // Check for Paragraphs
        else if (trimmedLine.length > 0) {
            const boldedContent = trimmedLine.split('**').map((text, i) => 
                i % 2 === 1 ? <strong key={`p-bold-${index}-${i}`}>{text}</strong> : text
            );
            // Tailwind classes for P
            elements.push(<p key={`p-${index}`} className="mb-2 text-sm leading-relaxed">{boldedContent}</p>);
        }
    });

    // Render any remaining list
    renderList();
    
    return elements;
};

// Helper to format ISO dates (from DB) into relative time
const formatLastActivity = (dateString) => {
    // If it's already a simple string like "2 hours ago", just return it
    if (!dateString || !dateString.includes('T') && !dateString.includes('-')) {
        return dateString; 
    }

    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (isNaN(diffInSeconds)) return dateString; // Fallback

    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} mins ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    return `${Math.floor(diffInSeconds / 86400)} days ago`;
};

const StudentAnalytics = (props) => {
    const [studentData, setStudentData] = useState(mockData); // Initialize with mockData
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [reportState, setReportState] = useState({
        targetId: null,
        report: null,
        error: null,
        isLoading: false,
    });

    // 1. Fetch Student List Data
    const fetchStudents = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetchDataWithRetry(`${API_BASE_URL}/api/analytics/students`, {
                method: 'GET',
                withCredentials: true,
            });
            
            if (response.data && response.data.length > 0) {
                setStudentData(response.data);
            } else {
                setStudentData(mockData); 
            }
        } catch (err) {
            console.error('Error fetching student list:', err);
            setError("Failed to load student data. Displaying mock data.");
            setStudentData(mockData); // Fallback to mock data on error
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (props.activeSection === 'student-analytics' || !props.activeSection) {
            fetchStudents();
        }
    }, [props.activeSection]);


    // 2. Generate AI Report Handler
    const handleGenerateReport = async (studentId, studentName) => {
        if (reportState.isLoading) return;

        setReportState({ targetId: studentId, report: null, error: null, isLoading: true });

        try {
            const response = await fetchDataWithRetry(`${API_BASE_URL}/api/analytics/report`, {
                method: 'POST',
                data: { student_id: studentId },
                withCredentials: true,
            });

            setReportState(prev => ({
                ...prev,
                report: response.data.report,
                isLoading: false,
                error: null
            }));

        } catch (err) {
            console.error('Error generating AI report:', err.response ? err.response.data : err.message);
            const errorMessage = err.response?.data?.error || `An unknown network error occurred while generating report for ${studentName}.`;
            
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
        // Replaced custom class 'analytics-page' with Tailwind classes
        <div className="p-6 bg-gray-50 min-h-screen font-sans">
            
            {/* Replaced custom class 'analytics-card' with Tailwind classes */}
            <div className="max-w-7xl mx-auto bg-white rounded-xl shadow-2xl p-10 lg:p-12">
                
                {/* Replaced custom class 'card-header' with Tailwind classes */}
                <div className="border-b border-gray-200 pb-4 mb-6">
                    {/* Replaced custom class 'card-title' with Tailwind classes */}
                    <h3 className="text-3xl font-extrabold text-gray-900">Student Performance Analytics</h3>
                    {/* Replaced custom class 'card-subtitle' with Tailwind classes */}
                    <p className="mt-1 text-sm text-gray-500">View student progress and generate AI-driven performance reports.</p>
                </div>

                {isLoading && (
                    <div className="text-center py-10 text-gray-600">
                        <p>Loading student data...</p>
                    </div>
                )}

                {error && (
                    // CORRECTED: Removed extraneous braces around the alert div
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md mb-4 text-sm" role="alert">
                        <strong className="font-bold mr-2">Error:</strong>
                        <span className="block sm:inline ml-2">{error}</span>
                    </div>
                )}

                {/* Replaced custom class 'data-table-container' with Tailwind classes */}
                <div className="overflow-x-auto rounded-lg shadow-md">
                    
                    {/* Replaced custom class 'student-table' with Tailwind classes */}
                    <table className="min-w-full divide-y divide-gray-200 table-fixed">
                        
                        {/* Replaced custom class 'table-header' with Tailwind classes */}
                        <thead className="bg-gray-100">
                            <tr>
                                {/* Replaced custom class 'student-table th' with Tailwind classes */}
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Student Name</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Progress</th>
                                <th scope="col" className="hidden sm:table-cell px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Avg. Score</th>
                                <th scope="col" className="hidden md:table-cell px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">AI Interactions</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Last Activity</th>
                                <th scope="col" className="px-6 py-3"><span className="sr-only">Actions</span></th>
                            </tr>
                        </thead>
                        
                        {/* Replaced custom class 'student-table tbody' with Tailwind classes */}
                        <tbody className="bg-white divide-y divide-gray-200">
                            {studentData.map(student => (
                            <React.Fragment key={student.id}>
                                {/* Replaced custom class 'table-row' with Tailwind classes */}
                                <tr className="hover:bg-indigo-50 transition duration-150">
                                    {/* Replaced custom class 'student-name' and 'student-table td' with Tailwind classes */}
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{student.name}</td>
                                    
                                    {/* Replaced custom class 'progress-cell' and 'student-table td' with Tailwind classes */}
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {/* Replaced custom class 'progress-bar' with Tailwind classes */}
                                        <div className="w-24 bg-gray-200 rounded-full h-2.5 inline-block align-middle">
                                            {/* Replaced custom class 'progress-fill' with Tailwind classes */}
                                            <div 
                                                className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300" 
                                                style={{ width: `${student.progress}%` }}
                                            ></div>
                                        </div>
                                        {/* Replaced custom class 'progress-percentage' with Tailwind classes */}
                                        <span className="ml-2 text-xs font-semibold text-gray-600">{student.progress}%</span>
                                    </td>
                                    
                                    <td className="hidden sm:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-500">{student.avgQuizScore}%</td>
                                    <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-500">{student.aiInteractions}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatLastActivity(student.lastActivity)}</td>                     
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button
                                            onClick={() => handleGenerateReport(student.id, student.name)}
                                            disabled={reportState.isLoading && reportState.targetId === student.id}
                                            // Replaced custom class 'generate-report-btn' with Tailwind classes
                                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-150"
                                        >
                                            {reportState.isLoading && reportState.targetId === student.id ? 'Generating...' : 'Generate Report'}
                                        </button>
                                    </td>
                                </tr>
                                
                                {/* Display Student Report Row */}
                                {reportState.targetId === student.id && (reportState.report || reportState.error) && (
                                    // Replaced custom class 'report-row' with Tailwind classes
                                    <tr className="bg-indigo-50 border-t border-indigo-200">
                                        {/* colSpan="6" ensures it covers the entire width of the table */}
                                        <td colSpan="6" className="px-6 py-4">
                                            {/* Replaced custom class 'report-title' with Tailwind classes */}
                                            <p className="font-bold text-base text-indigo-800 mb-2">
                                                {reportState.report ? `AI Report for ${student.name}:` : `Error for ${student.name}:`}
                                            </p>
                                            
                                            {/* Replaced custom class 'report-content' with Tailwind classes */}
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
                {studentData.length === 0 && !isLoading && <p className="p-4 text-center text-gray-500">No student data available.</p>}
            </div>
        </div>
    );
};

export default StudentAnalytics;