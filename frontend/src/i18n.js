import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
  en: {
    translation: {

      //Analytics
      studentPerformanceAnalytics: 'Student Performance Analytics',
      viewStudentProgress: 'View student progress and generate AI-driven performance reports.',
      loadingStudentData: 'Loading student data...',
      errorLabel: 'Error',
      studentName: 'Student Name',
      progress: 'Progress',
      avgScore: 'Avg. Score',
      lastActivity: 'Last Activity',
      actions: 'Actions',
      generating: 'Generating...',
      generateReport: 'Generate Report',
      aiReportFor: 'AI Report for {{name}}:',
      errorFor: 'Error for {{name}}:',
      noStudentData: 'No student data available.',
      never: 'Never',
      generating: 'Generating...',
      generateReport: 'Generate Report',
      regenerateReport: 'Regenerate',
      viewReport: 'View Report',
      hideReport: 'Hide Report',
      generateAllReports: 'Generate All Reports',
      aiReportFor: 'AI Report for {{name}}',
      errorFor: 'Failed to generate report for {{name}}',
      noStudentData: 'No student data available.',
      generateAllSuccess: 'Generated {{count}} reports successfully.',
      generateAllFailed: '{{count}} failed.',
      generateAllError: 'Error: {{message}}',

      //Dashboard
      dashboardTitle: 'Dashboard',
      logout: '🚪 Logout',
      loadingDashboard: 'Loading dashboard data...',
      errorLoadingDashboard: 'Error Loading Dashboard',
      retry: 'Retry',

      //item
      navOverview: '📊 Overview',
      navSubjectMembers: '🧑‍🤝‍🧑 Subject Members',
      navMaterials: '📚 Materials',
      navAssignments: '📝 Assignments',
      navAnalytics: '📈 Analytics',
      navSubjects: '📖 Subjects',
      navUsers: '👥 Users',
      navChatroom: '💬 AI Chatroom',

    }
  },
  'zh-HK': {
    translation: {
      //Analytics
      studentPerformanceAnalytics: '學生表現分析',
      viewStudentProgress: '查看學生進度並生成 AI 驅動的表現報告。',
      loadingStudentData: '正在載入學生資料...',
      errorLabel: '錯誤',
      studentName: '學生姓名',
      progress: '進度',
      avgScore: '平均分數',
      lastActivity: '最後活動',
      actions: '操作',
      generating: '正在生成...',
      generateReport: '生成報告',
      aiReportFor: '{{name}} 的 AI 報告：',
      errorFor: '{{name}} 的錯誤：',
      noStudentData: '沒有可用的學生資料。',
      never: '從未',
      generating: '生成中...',
      generateReport: '生成報告',
      regenerateReport: '重新生成',
      viewReport: '查看報告',
      hideReport: '隱藏報告',
      generateAllReports: '生成所有報告',
      aiReportFor: '{{name}}的AI 報告',
      errorFor: '無法為{{name}}生成報告',
      noStudentData: '沒有可用的學生資料。',
      generateAllSuccess: '成功生成 {{count}} 份報告。',
      generateAllFailed: '{{count}} 份失敗。',
      generateAllError: '錯誤：{{message}}',

      //Dashboard
      dashboardTitle: '控制台',
      logout: '🚪 登出',
      loadingDashboard: '正在載入控制台資料...',
      errorLoadingDashboard: '載入控制台時發生錯誤',
      retry: '重試',

      //item
      navOverview: '📊 概覽',
      navSubjectMembers: '🧑‍🤝‍🧑 科目成員',
      navMaterials: '📚 學習材料',
      navAssignments: '📝 作業',
      navAnalytics: '📈 分析',
      navSubjects: '📖 科目',
      navUsers: '👥 用戶',
      navChatroom: '💬 AI 聊天室',
    }
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    supportedLngs: ['en', 'zh-HK'],
    load: 'currentOnly',
    nonExplicitSupportedLngs: false,
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },
    interpolation: { escapeValue: false }
  });

export default i18n;
