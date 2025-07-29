import React, { useState } from 'react';
import axios from 'axios';

function NoteClassifier() {
  const [note, setNote] = useState('');
  const [label, setLabel] = useState('');

  const classifyNote = async () => {
    try {
      const response = await axios.post('http://172.25.50.9:5086/llama/classify', {
        note: note
      });
      setLabel(response.data.label);
    } catch (error) {
      console.error("Classification failed", error);
      setLabel("Error: Could not classify note");
    }
  };

  return (
    <div>
      <h2>Clinical Note Classifier</h2>
      <textarea
        rows="10"
        cols="80"
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
      <br />
      <button onClick={classifyNote}>Classify</button>
      {label && <p><strong>Predicted Label:</strong> {label}</p>}
    </div>
  );
}

export default NoteClassifier;
