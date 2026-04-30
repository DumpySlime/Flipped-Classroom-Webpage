# Flipped-Classroom-Webpage

## Quick start (frontend)
1. cd frontend
2. npm install
3. npm start
4. Backend must be running at API_BASE_URL for full functionality.

## Demo credentials
- Teacher: username = `teacher`, password = `teacher`  
- Student: username = `student`, password = `student`  
- Admin: username = `aa`, password = `aa`

---

## File → Purpose / Functions (component map)

- frontend/src/index.jsx  
  - App bootstrap and React StrictMode; includes i18n and reportWebVitals.

- frontend/src/reportWebVitals.jsx  
  - Performance helper to report web vitals (web-vitals import wrapper).

- frontend/src/i18n.js  
  - Internationalization setup (i18next) and translation resources for en / zh-HK.

- frontend/src/utils/langText.js  
  - getLangText(val, lang) — helper to extract localized text from objects.

- frontend/src/setupTests.jsx  
  - Jest DOM setup for tests.

- frontend/src/styles.css  
  - Global styles and form / login / slide templates used across components.

- frontend/src/dashboard.css  
  - Dashboard-specific styling (sidebar, cards, materials, viewer, etc).

- frontend/src/services/api.js  
  - API layer:
    - apiRequest(endpoint, options) — fetch wrapper with Authorization header using sessionStorage token.
    - materialAPI: getAll, add, delete, update
    - subjectAPI: getAll, add, getById
    - questionAPI: getByMaterial, add
    - studentAnswerAPI: getAll, submit
    - userAPI: getAll, add
    - topicAPI: getBySubject
    - authAPI.login(credentials) — login endpoint (no Authorization header)

- frontend/src/App.jsx  
  - Root app component: manages login state and toggles between Login and Dashboard.
  - handleLogin(role, user), handleLogout()

- frontend/src/component/Login.jsx  
  - Login form component handling authentication via authAPI.login and storing session data; calls onLogin callback.

- frontend/src/component/Dashboard.jsx  
  - Main dashboard container: loads subjects/materials/students/assignments and renders sections.
  - loadDashboardData(), calculateProgress(), getLastActivity(), handleSubjectChange(), handlers for add/delete material, submit answers, add question, logout.
  - Manages role-specific nav and language switch.

- frontend/src/component/sub-component/Overview.jsx  
  - Dashboard overview: stats cards, recent materials, subject cards, entry to MaterialList.

- frontend/src/component/sub-component/AddUser.jsx  
  - AddUser form to create users (calls apiRequest to /db/user-add).

- frontend/src/component/sub-component/AddSubject.jsx  
  - UI to create a new subject, manage topics and assign teachers (uses axios to /db/subject-add).

- frontend/src/component/sub-component/Assignment.jsx  
  - Assignment management UI (create assignments and view current assignments). Local/mock logic for selection.

- frontend/src/component/sub-component/StudentAnalytics.jsx  
  - Student analytics UI: fetches student data, generate / view AI reports, generate-all functionality and report caching.
  - Helper: renderMarkdown(), formatLastActivity().

- frontend/src/component/sub-component/SubjectMembers.jsx  
  - SubjectMembers: show members grouped by subject for admin/teacher views (fetches /db/subjectmembers and /db/subject).

- frontend/src/component/sub-component/chatroom/AIChatroom.jsx  
  - AI chatroom UI with streaming SSE-like consumption, message list, dark mode, reader mode, abort/stop streaming.
  - Uses apiRequest for some endpoints and direct fetch for streaming chat.

- frontend/src/component/sub-component/chatroom/AIChatroom.css  
  - Styles for AIChatroom (dark/light theme, streaming bubble, reader overlay).

- frontend/src/component/sub-component/material-viewer/MaterialViewer.jsx  
  - High-level material viewer that chooses between single MaterialList or SubjectList based on subjects count.

- frontend/src/component/sub-component/material-viewer/SubjectList.jsx  
  - Shows subject grid and opens MaterialList when a subject is selected.

- frontend/src/component/sub-component/material-viewer/MaterialList.jsx  
  - Lists materials for a subject; supports view / edit / delete / generate / upload flows.
  - deleteMaterial(matId), handleViewMaterial(), handleEditMaterial(), handleBackToSubjects().

- frontend/src/component/sub-component/material-viewer/ViewMaterial.jsx  
  - ViewMaterial: renders slides and questions for a material (slide navigation, thumbnails, progress, quiz submission).
  - loadMaterial(), refreshQuestions(), loadStudentSubmission(), handleEditMaterial(), handleBackToMaterials(), slide navigation and submission handling.

- frontend/src/component/sub-component/material-viewer/EditMaterial.jsx  
  - EditMaterial: edit slides and questions (editable slide content, add/remove points/questions/options, save handler).

- frontend/src/component/sub-component/material-viewer/GenerateMaterial.jsx  
  - GenerateMaterial: form to call LLM material generation endpoints and subsequent question/video generation.
  - handleSubmit(), generateQuestions(), generateVideo(), handleBackToMaterials().

- frontend/src/component/sub-component/material-viewer/SlideExplanation.jsx  
  - Slide template: renders explanation-type slide with subtitle, bullet points and optional video.

- frontend/src/component/sub-component/material-viewer/SlideExample.jsx  
  - Slide template: renders example-type slide with question and solution steps.

- frontend/src/component/sub-component/material-viewer/ViewQuestion.jsx  
  - ViewQuestion: standalone question viewer/submitter for a material (fetches /db/question, formats answers, posts via studentAnswerAPI.submit).

- frontend/src/component/sub-component/material-viewer/EditMaterial.jsx (already above)  
  - (Listed again to note preview & save functions.)

---

## Notes & known assumptions
- API base URL default is http://localhost:5000 — change services/api.js or set REACT_APP_API_URL for alternate host.
- authAPI.login returns a JSON object with access_token and user. Login component expects user fields: id/_id, role, firstName, lastName, username.
- Some components use direct axios calls to legacy endpoints; consider consolidating through services/api.js for consistency.
- This README documents the frontend files currently present under frontend/src. Backend implementations and DB contract are out of scope here.

---

## JSX Props Documentation

## App

```
No props required (root component)

State:
  isLoggedIn:     boolean
  userRole:       string ("student" | "teacher" | "admin")
  userInfo:       Object
    username:     string
    role:         string
    firstName:    string
    lastName:     string
    id:           number
```

## Login

```
Props:
  onLogin:        function(role: string, user: Object)
```

## Dashboard

```
Props:
  userRole:       string ("student" | "teacher" | "admin")
  userInfo:       Object
    id:           number
    username:     string
    role:         string
    firstName:    string
    lastName:     string
  userId:         number (optional)
  onLogout:       function

State:
  activeSection:  string
  materials:      Array
  subjects:       Array
  students:       Array
  studentProgress: Array
  assignments:    Array
  loading:        boolean
  error:          string | null
  selectedSubject: number | null
```

## Overview

```
Props:
  activeSection:    string
  materials:        Array
    id:             number
    topic:          string
    subject:        string
    created_at:     string
  subjects:         Array
    id:             number
    subject:        string
    topics:         Array<string>
  students:         Array
    id:             number
    username:       string
  studentProgress:  Array
    id:             number
    name:           string
    progress:       number
    lastActivity:   string
  totalStudents:    number
  userRole:         string ("student" | "teacher" | "admin")
```

## Assignment

```
Props:
  activeSection:          string
  mockAssignments:        Array
    id:                   number
    title:                string
    description:          string
    dueDate:              string
    assignedStudents:     Array<string>
    status:               string
  mockStudentProgress:    Array
    id:                   number
    name:                 string
    progress:             number
    lastActivity:         string
  materials:              Array
  onSubmitAnswers:        function
  fetchQuestions:         function
  userRole:               string
  userId:                 number

State:
  activeAssignmentSection: string ("manage" | "current")
  newAssignment:          Object
    title:                string
    description:          string
    dueDate:              string
    selectedStudents:     Array<string>
  showStudentDropdown:    boolean
```

## StudentAnalytics

```
Props:
  studentId:              number
  studentProgress:        Array
  students:               Array
  fetchStudentAnswers:    function
  userRole:               string
```

## MaterialViewer

```
Props:
  subjects:           Array
    id:               number
    subject:          string
    topics:           Array<string>
  materials:          Array
    id:               number
    topic:            string
    subject:          string
    created_at:       string
  selectedSubject:    number
  onSubjectChange:    function(subjectId: number)
  userRole:           string ("student" | "teacher" | "admin")
  userInfo:           Object
    id:               number
    username:         string
    firstname:        string
    lastname:         string
  activeSection:      string

State:
  selectedSubject:    Object | null
  userMaterials:      Object (keyed by subject id)
  userSubjects:       Array
```

## SubjectList

```
Props:
  subjects:           Array
    id:               number
    subject:          string
    topics:           Array<string>
  materials:          Object (keyed by subject id)
    [subjectId]:      Array
      id:             number
      topic:          string
      created_at:     string
  userRole:           string
  userInfo:           Object
    id:               number
    username:         string
  activeSection:      string
  onSubjectSelect:    function(subject: Object)

State:
  selectedSubject:    Object | null
```

## MaterialList

```
Props:
  subject:            Object
    id:               number
    subject:          string
    topics:           Array<string>
  materials:          Array
    id:               number
    topic:            string
    created_at:       string
  userRole:           string ("student" | "teacher" | "admin")
  userInfo:           Object
    id:               number
    username:         string

State:
  materials:          Array
  showUpload:         boolean
  showEdit:           boolean
  showView:           boolean
  showGenerate:       boolean
  selectedMaterial:   Object | null
```

## UploadMaterial

```
Props:
  subject:            Object
    id:               number
    subject:          string
    topics:           Array<string>
  onClose:            function

State:
  file:               File | null
  topics:             Array<string>
  values:             Object
    topic:            string
    subject_id:       number
```

## GenerateMaterial

```
Props:
  subject:            Object
    id:               number
    _id:              string (optional)
    subject:          string
    topics:           Array<string>
  username:           string
  onClose:            function

State:
  topics:             Array
  loadingTopics:      boolean
  topicsError:        string | null
  values:             Object
    topic:            string
    description:      string
    subject:          string
    subject_id:       number
  error:              string | null
  isGenerating:       boolean
  generatedMaterial:  Object | null
  hasCreatedQuestions: boolean
  generatedQuestionId: string | null
```

## ViewMaterial

```
Props:
  material:           Object (optional)
    id:               number
    topic:            string
    subject_id:       number
    uploaded_by:      string
  materialData:       Object (optional, AI-generated)
    sid:              string
    slides:           Array
      subtitle:       string
      content:        Array<string>
      slidetype:      string ("explanation" | "example")
      page:           number
  props:              Object (optional)
    userInfo:         Object
      id:             number

State:
  slides:             Array
  questions:          Array
  currentSlideIndex:  number
  err:                string | null
  loadingQuestions:   boolean
  userAnswers:        Object (keyed by questionKey)
  submitted:          boolean
  score:              number
  resetKey:           number
  materialId:         string | null
```

## EditMaterial

```
Props:
  material:           Object
    id:               number
    topic:            string
    filename:         string
    upload_date:      string
  onClose:            function (optional)
  activeSection:      string (destructured separately)
```

## FileUpload

```
Props:
  name:                   string
  max_file_size_in_kb:    string | number
  allowed_extensions:     Array<string> (e.g., ['ppt', 'pptx'])
  dataChanger:            function(file: File)
  required:               boolean (optional, default: false)
```

## SlideExplanation

```
Props:
  slide:              Object
    subtitle:         string
    content:          string | Array<string>
    slidetype:        string
    page:             number
```

## SlideExample

```
Props:
  slide:              Object
    subtitle:         string
    content:          Array<string> (first item is question, rest are solution steps)
    slidetype:        string
    page:             number
```

## ViewQuestion

```
Props:
  materialId:         number | string

State:
  error:              string | null
  questions:          Array
  topic:              string
  answers:            Object (keyed by question index)
```

## AIChatroom

```
No props required

State:
  isDarkMode:         boolean
  messages:           Array
    role:             string ("user" | "ai")
    text:             string
    model:            string
  input:              string
  loading:            boolean
  streamingMessage:   string
  isStreaming:        boolean
  readerMode:         boolean
```

## AddSubject

```
Props:
  subjects:           Array (optional)
  onSubjectsUpdate:   function
```

## AddUser

```
Props:
  onUsersUpdate:      function
```

## SubjectMembers

```
Props:
  userInfo:           Object
    id:               number
    username:         string
    firstname:        string
    lastname:         string
  userRole:           string ("student" | "teacher" | "admin")
  subjects:           Array
    id:               number
    subject:          string
```