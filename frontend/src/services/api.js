// frontend/src/service/api.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const getAuthToken = () => {
  return localStorage.getItem('access_token');
};

const apiRequest = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        ...options.headers,
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'API request failed');
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
};

export const materialAPI = {
  getAll: async (subjectId = null) => {
    const url = subjectId 
      ? `/db/material?subject_id=${subjectId}`
      : `/db/material`;
    const data = await apiRequest(url);
    return data.materials || [];
  },

  add: async (materialData) => {
    const formData = new FormData();
    Object.keys(materialData).forEach(key => {
      formData.append(key, materialData[key]);
    });

    const data = await apiRequest('/db/material-add', {
      method: 'POST',
      body: formData,
      headers: {}
    });
    return data;
  },

  delete: async (materialId) => {
    const data = await apiRequest(`/db/material-delete?material_id=${materialId}`, {
      method: 'DELETE'
    });
    return data;
  },

  update: async (materialId, updateData) => {
    const data = await apiRequest(`/db/material-update?material_id=${materialId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updateData)
    });
    return data;
  }
};

export const subjectAPI = {
  getAll: async (userId = null, role = null) => {
    let url = '/db/subject';
    
    if (userId && role === 'teacher') {
      url += `?teacher_id=${userId}`;
    } else if (userId && role === 'student') {
      url += `?student_id=${userId}`;
    }
    
    const data = await apiRequest(url);
    return data.subjects || [];
  },

  add: async (subjectData) => {
    const data = await apiRequest('/db/subject-add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(subjectData)
    });
    return data;
  },

  getById: async (subjectId) => {
    const data = await apiRequest(`/db/subject?id=${subjectId}`);
    return data.subjects?.[0] || null;
  }
};

export const questionAPI = {
  getByMaterial: async (materialId) => {
    const data = await apiRequest(`/db/question?material_id=${materialId}`);
    return data.questions || [];
  },

  add: async (questionData) => {
    const data = await apiRequest('/db/question-add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(questionData)
    });
    return data;
  }
};

export const studentAnswerAPI = {
  getAll: async (studentId, materialId = null) => {
    let url = `/db/student-answers?student_id=${studentId}`;
    if (materialId) {
      url += `&material_id=${materialId}`;
    }
    
    const data = await apiRequest(url);
    return data.submissions || [];
  },

  submit: async (answersData) => {
    const data = await apiRequest('/db/student-answers-submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(answersData)
    });
    return data;
  }
};

export const userAPI = {
  getAll: async (role = null) => {
    let url = '/db/user';
    if (role) {
      url += `?role=${role}`;
    }
    
    const data = await apiRequest(url);
    return data.users || [];
  },

  add: async (userData) => {
    const data = await apiRequest('/db/user-add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });
    return data;
  }
};

export const topicAPI = {
  getBySubject: async (subjectId) => {
    const data = await apiRequest(`/db/topic?subject_id=${subjectId}`);
    return data.topics || [];
  }
};
