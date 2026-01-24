import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Mic, Square, Loader2, LayoutDashboard, Home } from 'lucide-react';

const API_URL = "https://unreconciled-snowily-ema.ngrok-free.dev"; 

function App() {
  const [view, setView] = useState('home'); 
  
  // Recording States
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null); // Now used for playback
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Data States
  const [transcription, setTranscription] = useState("");
  const [extractedData, setExtractedData] = useState(null);
  
  // Dashboard Data
  const [dashboardData, setDashboardData] = useState([]);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  // --- RECORDING LOGIC ---
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        
        // Save blob to state so we can play it back in the UI
        setAudioBlob(blob); 
        
        // Immediately send to backend
        processAudio(blob); 
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      
      // Reset previous results
      setAudioBlob(null);
      setTranscription("");
      setExtractedData(null);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Microphone access denied.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  // --- API LOGIC ---
  const processAudio = async (blob) => {
    setIsProcessing(true);
    const formData = new FormData();
    formData.append('file', blob, 'recording.webm');

    try {
      const response = await axios.post(`${API_URL}/process-audio`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setTranscription(response.data.transcription);
      setExtractedData(response.data.extracted_data);
    } catch (error) {
      console.error("API Error:", error);
      alert("Failed to process audio. Is Backend running?");
    } finally {
      setIsProcessing(false);
    }
  };

  const fetchDashboard = async () => {
    try {
      // 1. Added ngrok header to bypass the warning screen
      const res = await axios.get(`${API_URL}/dashboard-data`, {
        headers: {
          "ngrok-skip-browser-warning": "69420"
        }
      });
      
      // 2. Safety check: Ensure the response is actually an array
      if (Array.isArray(res.data)) {
        setDashboardData(res.data);
      } else {
        console.warn("API returned non-array data:", res.data);
        setDashboardData([]); // Fallback to empty array
      }
      
      setView('dashboard');
    } catch (error) {
      console.error("Dashboard fetch error:", error);
      alert("Could not load dashboard data");
    }
  };

  // --- UI COMPONENTS ---

  const RecordView = () => (
    <div className="flex flex-col items-center justify-center p-6 space-y-6 max-w-md mx-auto">
      <h1 className="text-2xl font-bold text-gray-800">Voice CRM</h1>
      
      {/* Mic Button */}
      <button
        onClick={isRecording ? stopRecording : startRecording}
        className={`w-24 h-24 rounded-full flex items-center justify-center transition-all shadow-lg ${
          isRecording ? 'bg-red-500 animate-pulse' : 'bg-blue-600 hover:bg-blue-700'
        }`}
      >
        {isRecording ? <Square size={32} color="white" /> : <Mic size={32} color="white" />}
      </button>
      <p className="text-gray-500">
        {isRecording ? "Listening... Tap to Stop" : "Tap Microphone to Start"}
      </p>

      {/* FIXED: Audio Player using audioBlob */}
      {audioBlob && !isRecording && (
        <div className="w-full bg-white p-3 rounded-lg border shadow-sm">
            <p className="text-xs text-gray-400 mb-2">Recording Preview:</p>
            <audio controls src={URL.createObjectURL(audioBlob)} className="w-full h-8" />
        </div>
      )}

      {/* Loading State */}
      {isProcessing && (
        <div className="flex items-center space-x-2 text-blue-600">
          <Loader2 className="animate-spin" />
          <span>Processing voice input...</span>
        </div>
      )}

      {/* Results Area */}
      {transcription && (
        <div className="w-full space-y-4 animate-fade-in">
          <div className="bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-sm font-semibold text-gray-500 mb-1">TRANSCRIPTION</h3>
            <p className="text-gray-800">{transcription}</p>
          </div>

          {extractedData && (
            <div className="w-full">
              <h3 className="text-sm font-semibold text-gray-500 mb-1">EXTRACTED JSON</h3>
              <pre className="json-view">
                {JSON.stringify(extractedData, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const DashboardView = () => (
    <div className="p-4 max-w-4xl mx-auto">
      <h2 className="text-xl font-bold mb-4">Evaluation Dashboard</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 border">ID</th>
              <th className="p-2 border">Timestamp</th>
              <th className="p-2 border">Transcription Snippet</th>
              <th className="p-2 border">Customer Name</th>
              <th className="p-2 border">Status</th>
            </tr>
          </thead>
          <tbody>
            {dashboardData.map((row) => (
              <tr key={row.id} className="text-sm hover:bg-gray-50">
                <td className="p-2 border">{row.id}</td>
                <td className="p-2 border">{new Date(row.timestamp).toLocaleTimeString()}</td>
                <td className="p-2 border truncate max-w-[150px]">{row.text}</td>
                <td className="p-2 border font-medium">
                  {row.data?.customer?.full_name || "N/A"}
                </td>
                <td className="p-2 border text-green-600">Processed</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 text-xs text-gray-500">
        * This data is fetched from the temporary in-memory Python backend.
      </p>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {view === 'home' ? <RecordView /> : <DashboardView />}
      
      <div className="fixed bottom-0 w-full bg-white border-t flex justify-around p-3">
        <button 
          onClick={() => setView('home')}
          className={`flex flex-col items-center ${view === 'home' ? 'text-blue-600' : 'text-gray-400'}`}
        >
          <Home size={24} />
          <span className="text-xs">Record</span>
        </button>
        <button 
          onClick={fetchDashboard}
          className={`flex flex-col items-center ${view === 'dashboard' ? 'text-blue-600' : 'text-gray-400'}`}
        >
          <LayoutDashboard size={24} />
          <span className="text-xs">Dashboard</span>
        </button>
      </div>
    </div>
  );
}

export default App;