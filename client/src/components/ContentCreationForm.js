import React, { useState } from "react";
import "./ContentCreationForm.css";

const ContentCreationForm = () => {
  const [formData, setFormData] = useState({
    genre: "",
    theme: "",
    visualStyle: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [generatedScript, setGeneratedScript] = useState(null);

  const genres = [
    "Action",
    "Drama",
    "Comedy",
    "Sci-Fi",
    "Fantasy",
    "Romance",
    "Mystery",
    "Horror",
  ];

  const visualStyles = [
    "Realistic",
    "Animated",
    "Cinematic",
    "Artistic",
    "Minimalist",
    "Vintage",
  ];

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5001/generate-script", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error("Failed to generate script");
      }

      const data = await response.json();
      setGeneratedScript(data);
      setSuccess(true);
      console.log("Generated script:", data);
    } catch (error) {
      console.error("Error submitting form:", error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h1>Create Your Story</h1>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="genre">Genre</label>
          <select
            id="genre"
            name="genre"
            value={formData.genre}
            onChange={handleChange}
            required
          >
            <option value="">Select a genre</option>
            {genres.map((genre) => (
              <option key={genre} value={genre}>
                {genre}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="theme">Theme</label>
          <input
            type="text"
            id="theme"
            name="theme"
            value={formData.theme}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="visualStyle">Visual Style</label>
          <select
            id="visualStyle"
            name="visualStyle"
            value={formData.visualStyle}
            onChange={handleChange}
            required
          >
            <option value="">Select a visual style</option>
            {visualStyles.map((style) => (
              <option key={style} value={style}>
                {style}
              </option>
            ))}
          </select>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "Generating..." : "Generate Story"}
        </button>
      </form>

      {generatedScript && (
        <div className="script-container">
          <h2>Generated Script: {generatedScript.title}</h2>
          {generatedScript.scenes.map((scene) => (
            <div key={scene.scene_number} className="scene">
              <h3>Scene {scene.scene_number}</h3>
              <p>
                <strong>Description:</strong> {scene.description}
              </p>
              <p>
                <strong>Dialogue:</strong> {scene.dialogue}
              </p>
            </div>
          ))}
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      {success && (
        <div className="success-message">Script generated successfully!</div>
      )}
    </div>
  );
};

export default ContentCreationForm;
