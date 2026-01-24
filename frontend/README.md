# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)


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