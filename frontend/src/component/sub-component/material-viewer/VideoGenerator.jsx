import { useState } from "react";
import axios from "axios";
import "../../../styles.css";
import "../../../dashboard.css";

const API_BASE_URL = "http://localhost:5000";

function VideoGenerator({ materialId, onVideoGenerated }) {
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState("");
  const [videos, setVideos] = useState([]);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    if (!materialId) {
      setError("materialId is missing.");
      return;
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("You are not logged in or token is missing.");
      return;
    }
    const authHeaders = { Authorization: `Bearer ${token}` };

    setIsLoading(true);
    setError(null);
    setVideos([]);
    setStep("Generating videos for slides 2–5 (this may take several minutes)...");

    try {
      const res = await axios.post(
        `${API_BASE_URL}/api/generate-video/generate`,
        { material_id: materialId, quality: "medium" },
        { headers: authHeaders, timeout: 10 * 6000 * 1000 } 
      );

      const generatedVideos = res.data.videos;
      if (!generatedVideos || generatedVideos.length === 0) {
        throw new Error("Backend did not return any videos.");
      }

      setVideos(generatedVideos);
      setStep("Generation complete!");

      if (onVideoGenerated) {
        onVideoGenerated(generatedVideos);
      }

    } catch (err) {
      console.error("Video generation error:", err);
      if (err.response) {
        console.error("Status:", err.response.status);
        console.error("Data:", err.response.data);
      }
      const msg =
        err.response?.data?.error ||
        err.response?.data?.details ||
        err.message ||
        "Failed to generate video.";
      setError(msg);
      setStep("");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginTop: "1rem" }}>
      <div className="card-header"> Generate Manim Video</div>
      <div className="card-body">
        <button
          className="btn btn-primary"
          onClick={handleGenerate}
          disabled={isLoading}
        >
          {isLoading ? "Generating..." : "Generate Video from Slides"}
        </button>

        {step && <p style={{ marginTop: "0.5rem" }}>{step}</p>}

        {error && (
          <div className="alert alert-danger" style={{ marginTop: "0.5rem" }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

export default VideoGenerator;