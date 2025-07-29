// import React, { useState, useEffect } from 'react';
// import axios from 'axios';

// function NoteClassifier() {
//   const [note, setNote] = useState('');
//   const [label, setLabel] = useState('');
//   const [rawOutput, setRawOutput] = useState('');
//   const [timestamp, setTimestamp] = useState('');
//   const [loading, setLoading] = useState(false);
//   const [errorMsg, setErrorMsg] = useState('');
//   const [history, setHistory] = useState([]);
//   const [historyLoading, setHistoryLoading] = useState(false);
//   const [historyError, setHistoryError] = useState('');

//   // Fetch classification history from backend
//   const fetchHistory = async () => {
//     setHistoryLoading(true);
//     setHistoryError('');
//     try {
//       const response = await axios.get('http://172.25.50.9:5088/llama/records');
//       setHistory(response.data);
//     } catch (err) {
//       setHistoryError('Failed to load history');
//       console.error(err);
//     } finally {
//       setHistoryLoading(false);
//     }
//   };

//   useEffect(() => {
//     fetchHistory();
//   }, []);

//   const classifyNote = async () => {
//     if (!note.trim()) return;

//     setLoading(true);
//     setLabel('');
//     setRawOutput('');
//     setTimestamp('');
//     setErrorMsg('');

//     try {
//       const response = await axios.post('http://172.25.50.9:5088/llama/classify', { note });
//       const data = response.data;
//       setLabel(data.label);
//       setRawOutput(data.raw_output);
//       setTimestamp(new Date(data.timestamp).toLocaleString());
//       // Update history immediately with new record
//       setHistory(prev => [data, ...prev]);
//     } catch (error) {
//       console.error("❌ Classification failed:", error);
//       setErrorMsg("Error: Could not classify note");
//     } finally {
//       setLoading(false);
//     }
//   };

//   const downloadCSV = () => {
//     window.open('http://172.25.50.9:5088/llama/export', '_blank');
//   };

//   return (
//     <div style={{ padding: '1rem', fontFamily: 'Arial, sans-serif' }}>
//       <h2>🩺 Clinical Note Classifier</h2>

//       <textarea
//         rows="10"
//         cols="80"
//         placeholder="Paste clinical note here..."
//         value={note}
//         onChange={(e) => {
//           setNote(e.target.value);
//           setLabel('');
//           setRawOutput('');
//           setTimestamp('');
//           setErrorMsg('');
//         }}
//       />
//       <br /><br />

//       <button onClick={classifyNote} disabled={loading}>
//         {loading ? 'Classifying...' : '🔍 Classify'}
//       </button>

//       <button onClick={downloadCSV} style={{ marginLeft: '1rem' }}>
//         ⬇️ Export All Results
//       </button>

//       <hr />

//       {errorMsg && <p style={{ color: 'red' }}>{errorMsg}</p>}

//       {label && (
//         <div style={{ marginTop: '1rem' }}>
//           <p><strong>🧠 Predicted Label:</strong> {label}</p>
//           <p><strong>🕒 Timestamp:</strong> {timestamp}</p>
//           <p><strong>📄 LLM Output:</strong></p>
//           <pre style={{
//             background: '#f4f4f4',
//             padding: '10px',
//             borderRadius: '5px',
//             whiteSpace: 'pre-wrap'
//           }}>{rawOutput}</pre>
//         </div>
//       )}

//       <hr />
//       <h3>🗂 Classification History</h3>

//       {historyLoading && <p>Loading history...</p>}
//       {historyError && <p style={{ color: 'red' }}>{historyError}</p>}

//       {!historyLoading && history.length === 0 && <p>No records yet.</p>}

//       {!historyLoading && history.length > 0 && (
//         <table
//           style={{
//             borderCollapse: 'collapse',
//             width: '100%',
//             maxHeight: '300px',
//             overflowY: 'scroll',
//             display: 'block'
//           }}
//         >
//           <thead>
//             <tr style={{ backgroundColor: '#eee' }}>
//               <th style={{ border: '1px solid #ccc', padding: '8px' }}>Note (truncated)</th>
//               <th style={{ border: '1px solid #ccc', padding: '8px' }}>Label</th>
//               <th style={{ border: '1px solid #ccc', padding: '8px' }}>Timestamp</th>
//             </tr>
//           </thead>
//           <tbody>
//             {history.map((record) => (
//               <tr key={record.id}>
//                 <td style={{ border: '1px solid #ccc', padding: '8px', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
//                   {record.note}
//                 </td>
//                 <td style={{ border: '1px solid #ccc', padding: '8px' }}>{record.label}</td>
//                 <td style={{ border: '1px solid #ccc', padding: '8px' }}>
//                   {new Date(record.timestamp).toLocaleString()}
//                 </td>
//               </tr>
//             ))}
//           </tbody>
//         </table>
//       )}
//     </div>
//   );
// }

// export default NoteClassifier;

import React, { useState, useEffect } from 'react';
import axios from 'axios';

function NoteClassifier() {
  const [note, setNote] = useState('');
  const [label, setLabel] = useState('');
  const [rawOutput, setRawOutput] = useState('');
  const [timestamp, setTimestamp] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');

  // Change this URL to match your Flask backend port (5088 from your code)
  const backendUrl = 'http://172.25.50.9:5089';

  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return 'N/A';
    }
  };

  const fetchHistory = async () => {
    setHistoryLoading(true);
    setHistoryError('');
    try {
      const response = await axios.get(`${backendUrl}/llama/records`);
      setHistory(response.data);
    } catch (err) {
      setHistoryError('Failed to load history');
      console.error(err);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
    // Optional auto-refresh every 30s:
    // const interval = setInterval(fetchHistory, 30000);
    // return () => clearInterval(interval);
  }, []);

  const classifyNote = async () => {
    if (!note.trim()) return;

    setLoading(true);
    setLabel('');
    setRawOutput('');
    setTimestamp('');
    setErrorMsg('');

    try {
      const response = await axios.post(`${backendUrl}/llama/classify`, { note });
      const data = response.data;
      setLabel(data.label || 'No label returned');
      setRawOutput(data.raw_output || '');
      setTimestamp(formatDate(data.timestamp));
      setHistory(prev => [data, ...prev]);
    } catch (error) {
      console.error("❌ Classification failed:", error);
      setErrorMsg("Error: Could not classify note");
    } finally {
      setLoading(false);
    }
  };

  const downloadCSV = () => {
    window.open(`${backendUrl}/llama/export`, '_blank');
  };

  return (
    <div style={{ padding: '1rem', fontFamily: 'Arial, sans-serif' }}>
      <h2>🩺 Clinical Note Classifier</h2>

      <textarea
        rows="10"
        cols="80"
        placeholder="Paste clinical note here..."
        value={note}
        onChange={(e) => {
          setNote(e.target.value);
          setLabel('');
          setRawOutput('');
          setTimestamp('');
          setErrorMsg('');
        }}
      />
      <br /><br />

      <button onClick={classifyNote} disabled={loading || !note.trim()}>
        {loading ? 'Classifying...' : '🔍 Classify'}
      </button>

      <button onClick={downloadCSV} style={{ marginLeft: '1rem' }}>
        ⬇️ Export All Results
      </button>

      <hr />

      {errorMsg && <p style={{ color: 'red' }}>{errorMsg}</p>}

      {label && (
        <div style={{ marginTop: '1rem' }}>
          <p><strong>🧠 Predicted Label:</strong> {label}</p>
          <p><strong>🕒 Timestamp:</strong> {timestamp}</p>
          <p><strong>📄 LLM Output:</strong></p>
          <pre style={{
            background: '#f4f4f4',
            padding: '10px',
            borderRadius: '5px',
            whiteSpace: 'pre-wrap'
          }}>{rawOutput}</pre>
        </div>
      )}

      <hr />
      <h3>🗂 Classification History</h3>

      {historyLoading && <p>Loading history...</p>}
      {historyError && <p style={{ color: 'red' }}>{historyError}</p>}

      {!historyLoading && history.length === 0 && <p>No records yet.</p>}

      {!historyLoading && history.length > 0 && (
        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
          <table style={{ borderCollapse: 'collapse', width: '100%' }}>
            <thead>
              <tr style={{ backgroundColor: '#eee' }}>
                <th style={{ border: '1px solid #ccc', padding: '8px' }}>Note (truncated)</th>
                <th style={{ border: '1px solid #ccc', padding: '8px' }}>Label</th>
                <th style={{ border: '1px solid #ccc', padding: '8px' }}>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {history.map((record) => (
                <tr key={record.id}>
                  <td style={{
                    border: '1px solid #ccc',
                    padding: '8px',
                    maxWidth: '300px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {record.note}
                  </td>
                  <td style={{ border: '1px solid #ccc', padding: '8px' }}>{record.label}</td>
                  <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                    {formatDate(record.timestamp)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default NoteClassifier;



