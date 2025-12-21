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


### JSX Props Documentation

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
  onLogout:       function
```

## Overview

```
Props:
  activeSection:  string
  totalStudents:  number
  mockMaterials:  Array
  mockGeneratedContent: Array
  mockGeneratedVideos: Array
```

## AddSubject

```
Props:
  activeSection:      string
  setActiveSection:   function(section: string)
```

## AddUser

```
Props:
  activeSection:      string
  setActiveSection:   function(section: string)
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
```

## StudentAnalytics

```
Props:
  activeSection:  string
```

## MaterialViewer

```
Props:
  activeSection:  string
  userInfo:       Object
    id:           number
    username:     string
  userRole:       string ("student" | "teacher" | "admin")
  mockMaterials:  Array
```

## SubjectList

```
Props:
  subjects:       Array
    id:           number
    subject:      string
    topics:       Array<string>
  materials:      Object (keyed by subject id)
    [subjectId]:  Array
      id:         number
      topic:      string
      filename:   string
      upload_date: string
  userInfo:       Object
    id:           number
    username:     string
  userRole:       string
```

## MaterialList

```
Props:
  subject:        Object
    id:           number
    subject:      string
    topics:       Array<string>
  materials:      Array
    id:           number
    topic:        string
    filename:     string
    upload_date:  string
  userInfo:       Object
    id:           number
    username:     string
  userRole:       string ("student" | "teacher" | "admin")
```

## UploadMaterial

```
Props:
  subject:        Object
    id:           number
    subject:      string
    topics:       Array<string>
  onClose:        function
```

## GenerateMaterial

```
Props:
  subject:        Object
    id:           number
    subject:      string
    topics:       Array<string>
  username:       string
  onClose:        function
```

## ViewMaterial

```
Props:
  material:       Object
    id:           number
    topic:        string
    filename:     string
    upload_date:  string
  onClose:        function (optional)
```

## EditMaterial

```
Props:
  material:       Object
    id:           number
    topic:        string
    filename:     string
    upload_date:  string
  onClose:        function (optional)

activeSection:  string (destructured separately)
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

## MaterialGenerator

```
Props:
  activeSection:  string
```

## AIChatroom

```
No props required

State:
  isDarkMode:     boolean
  messages:       Array
    role:         string ("user" | "ai")
    text:         string
    model:        string
  input:          string
  loading:        boolean
  streamingMessage: string
  isStreaming:    boolean
  readerMode:     boolean
```