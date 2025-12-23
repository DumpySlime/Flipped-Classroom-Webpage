import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import ViewMaterial from './ViewMaterial';
import ViewQuestion from './ViewQuestion';

function GenerateMaterial({subject, username, onClose}) {
  const [topics, setTopics] = useState([])
  const [values, setValues] = useState({
    topic: '',
    description: '',
    subject: subject?.subject || '',
    subject_id: subject?.id || '',
    username: username || '',
  })
  const [error, setError] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedMaterial, setGeneratedMaterial] = useState(null);
  const [hasCreatedQuestions, setHasCreatedQuestions] = useState(false);
  const [generatedQuestionId, setGeneratedQuestionId] = useState(null);

  const handleChanges = (e) => {
    setValues({...values, [e.target.name]: e.target.value })
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!values.topic) {
      setError("Please select a topic.");
      return;
    }
    setIsGenerating(true);
    console.log('Form submitted with values:', values);
    
    // Store current values before they get reset
    const submittedValues = { ...values };
    
    axios.post('/api/llm/material/create', values, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    .then(function (response) {
      console.log(`Material generation request sent successfully:`, response.data);
      const sid = response.data?.data?.sid;
      if (sid) {
        console.log(`Material task created with sid: ${sid}`);
        // Pass the submitted values to polling
        pollMaterialProgress(sid, submittedValues);
      }
      // DON'T reset values here - wait until after questions are generated
    })
    .catch(function (error) {
      console.log(`Error sending material generation parameters: ${error}`);
      setError("Failed to generate material. Please try again.");
      setIsGenerating(false);
    })
  }

  useEffect(() => {
    // set subject name to current subject once detected
    setTopics(subject.topics || ["undefined"]);
    setValues(prev => ({...prev, subject: subject.subject}))
  }, [subject])

  // Function to poll the material generation progress
  const pollMaterialProgress = (sid, submittedValues) => {
    const maxAttempts = 60;
    let attempts = 0;
    const checkProgress = () => {
      if (attempts >= maxAttempts) {
        console.log("Material generation timed out. Please try again later.");
        setIsGenerating(false);
        return;
      }

      axios.get(`/api/llm/material/progress?sid=${sid}`)
      .then( (response) => {
        const data = response.data?.data || {};
        const status = data.materialStatus
        console.log(`Material progress: ${status} (attempt ${attempts + 1}/${maxAttempts})`);
        if (status === 'done') {
          console.log("Material generation completed!");
          console.log("Generated material data:", data);
          setError(null);
          setGeneratedMaterial(data);
          // Pass the submitted values to question generation
          generateQuestions(data.sid, submittedValues);
        } else if (status === 'failed') {
          setError('Material generation failed. Please try again.');
          console.log("Material generation failed.");
          setIsGenerating(false);
        } else {
          attempts += 1;
          setTimeout(checkProgress, 5000); // Poll every 5 seconds
        }
      })
      .catch( (error) => {
        console.log(`Error checking progress: ${error}`);
        setError('Error checking generation progress.');
        setIsGenerating(false);
      })
    }
    checkProgress();
  }

  // function for question generation
  const generateQuestions = (materialSid, submittedValues) => {
    const questionData = {
      subject: submittedValues.subject,
      subject_id: submittedValues.subject_id,
      topic: submittedValues.topic,
      material_id: materialSid
    }
    
    console.log('Generating questions with data:', questionData);
    
    axios.post('/api/ai/generate-question', questionData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    .then( (response) => {
      const data = response.data;
      console.log(`Question generation request sent successfully:`, data);
      setGeneratedQuestionId(data._id);
      setHasCreatedQuestions(true);
      
      // NOW reset the form values after everything is done
      setValues({
        topic: '',
        description: '',
        subject: subject?.subject || '',
        subject_id: subject?.id || '',
        username: username || '',
      });
    })
    .catch( (error) => {
      console.log(`Error sending question generation request: ${error}`);
      console.log('Error details:', error.response?.data);
      setError("Failed to send question generation request.");
    })
    .finally(() => setIsGenerating(false) )
  }

  if (!subject) {
    return (
      <div className="container">
        <p>Loading subject information...</p>
      </div>
    );
  }

  return (
    <div className="container">
      {!generatedMaterial ? (
        <form onSubmit={handleSubmit} className="form-container">
          <h2>Generate Material</h2>
          
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="subject">Subject:</label>
            <input 
              type="text" 
              id="subject"
              name="subject" 
              value={values.subject} 
              disabled 
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="topic">Topic:</label>
            <select 
              id="topic"
              name="topic" 
              value={values.topic} 
              onChange={handleChanges}
              className="form-input"
            >
              <option value="">Select a topic</option>
              {topics.map((topic, index) => (
                <option key={index} value={topic}>
                  {topic}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="description">Description:</label>
            <textarea 
              id="description"
              name="description" 
              value={values.description} 
              onChange={handleChanges}
              placeholder="Enter additional details for material generation"
              className="form-textarea"
              rows="4"
            />
          </div>

          <button 
            type="submit" 
            disabled={isGenerating}
            className="submit-button"
          >
            {isGenerating ? 'Generating...' : 'Generate Material'}
          </button>
        </form>
      ) : isGenerating ? (
        <div className="loading-container">
          <p>Generating your material, please wait...</p>
        </div>
      ) : (
        <div className="result-container">
          {generatedMaterial && <ViewMaterial materialData={generatedMaterial} />}
          {hasCreatedQuestions && generatedMaterial?.sid && (
            <ViewQuestion materialId={generatedMaterial.sid} questionId={generatedQuestionId} />
          )}
        </div>
      )}
    </div>
  );
}

export default GenerateMaterial;
