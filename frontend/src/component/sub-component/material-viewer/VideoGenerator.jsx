import { useState } from "react";
import axios from "axios";
import "../../../styles.css";
import "../../../dashboard.css";

const API_BASE_URL = "http://localhost:5000"; // adjust if needed

function VideoGenerator({ materialId, onVideoGenerated }) {
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState("");
  const [slides, setSlides] = useState([]);
  const [storyboard, setStoryboard] = useState("");
  const [manimCode, setManimCode] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    if (!materialId) {
      setError("materialId is missing.");
      return;
    }

    const token = localStorage.getItem("access_token"); // check this key
    if (!token) {
      setError("You are not logged in or token is missing.");
      return;
    }
    const authHeaders = { Authorization: `Bearer ${token}` };

    setIsLoading(true);
    setError(null);
    setSlides([]);
    setStoryboard("");
    setManimCode("");
    setVideoUrl("");
    setStep("Step 1/4: Extracting slides from material...");

    try {
      const prepareRes = await axios.post(
        `${API_BASE_URL}/api/generate-video/prepare`,
        { material_id: materialId },
        { headers: authHeaders }
      );
      const { slides: preparedSlides, topic } = prepareRes.data;

      if (!preparedSlides || preparedSlides.length === 0) {
        throw new Error("No slides found in this material.");
      }
      setSlides(preparedSlides);

      // 2) Storyboard generation
      setStep("Step 2/4: Generating Manim storyboard...");
      const storyboardRes = await axios.post(
        `${API_BASE_URL}/api/generate-video/storyboard`,
        { slides: preparedSlides, topic },
        { headers: authHeaders }
      );
      const sb = storyboardRes.data.storyboard;
      setStoryboard(sb);

      // 3) Manim code generation
      setStep("Step 3/4: Generating Manim Python code...");
      const codeRes = await axios.post(
        `${API_BASE_URL}/api/generate-video/code`,
        { storyboard: sb, topic },
        { headers: authHeaders }
      );
      const code = codeRes.data.manim_code;
      setManimCode(code);

      // 4) Render video
      setStep("Step 4/4: Rendering video with Manim (this may take a few minutes)...");
      const renderRes = await axios.post(
        `${API_BASE_URL}/api/generate-video/render`,
        {
          manim_code: code,
          material_id: materialId,
          quality: "medium",
        },
        {
          headers: authHeaders,
          timeout: 6 * 60 * 1000, // 6 minutes
        }
      );

      const url = renderRes.data.video_url;
      setVideoUrl(url);
      setStep("Completed!");

      if (onVideoGenerated) {
        onVideoGenerated(url);
      }
    } catch (err) {
      console.error("Video generation error:", err);
      const msg =
        err.response?.data?.error ||
        err.message ||
        "Failed to generate Manim video.";
      setError(msg);
      setStep("");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginTop: "1rem" }}>
      <div className="card-header">🎬 Generate Manim Video</div>
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

        {slides.length > 0 && (
          <details style={{ marginTop: "0.5rem" }}>
            <summary>Preview slides used</summary>
            <pre style={{ whiteSpace: "pre-wrap" }}>
              {slides
                .map(
                  (s) =>
                    `Slide ${s.slide_number}: ${s.title}\n${s.content}\n\n`
                )
                .join("")}
            </pre>
          </details>
        )}

        {storyboard && (
          <details style={{ marginTop: "0.5rem" }}>
            <summary>Generated storyboard</summary>
            <pre style={{ whiteSpace: "pre-wrap" }}>{storyboard}</pre>
          </details>
        )}

        {manimCode && (
          <details style={{ marginTop: "0.5rem" }}>
            <summary>Generated Manim code</summary>
            <pre style={{ whiteSpace: "pre-wrap" }}>{manimCode}</pre>
          </details>
        )}

        {videoUrl && (
          <div style={{ marginTop: "0.5rem" }}>
            <p>Generated video:</p>
            <video controls width="100%">
              <source src={videoUrl} type="video/mp4" />
            </video>
          </div>
        )}
      </div>
    </div>
  );
}

export default VideoGenerator;
