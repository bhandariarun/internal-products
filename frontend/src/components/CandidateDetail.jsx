import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { SSE } from 'sse.js';
import { ArrowLeft, UserCircle, Brain, Star, FileText } from 'lucide-react';

export default function CandidateDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [candidate, setCandidate] = useState(null);
  const [scores, setScores] = useState([]);
  const [summary, setSummary] = useState('');
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [scoreForm, setScoreForm] = useState({ category: 'Technical', score: 5, note: '' });

  useEffect(() => {
    const fetchCandidate = async () => {
      try {
        const res = await api.get(`/candidates/${id}`);
        setCandidate(res.data);
        setScores(res.data.scores);
      } catch (err) {
        console.error(err);
      }
    };
    fetchCandidate();

    // Setup SSE for real-time scores
    const token = localStorage.getItem('token');
    const source = new SSE(`http://localhost:8000/candidates/${id}/stream`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    source.addEventListener('new_score', (e) => {
      // Re-fetch candidate to get the latest scores properly hydrated
      // Or simply append if data was full object. Here we just re-fetch for simplicity.
      fetchCandidate();
    });

    source.stream();

    return () => {
      source.close();
    };
  }, [id]);

  const handleScoreSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/candidates/${id}/scores`, scoreForm);
      setScoreForm({ category: 'Technical', score: 5, note: '' });
      // SSE will trigger re-fetch, but we can optimistically add if we wanted
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerateSummary = async () => {
    setIsGeneratingSummary(true);
    try {
      const res = await api.post(`/candidates/${id}/summary`);
      setSummary(res.data.summary);
    } catch (err) {
      console.error(err);
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  if (!candidate) return <div className="min-h-screen flex items-center justify-center bg-slate-50">Loading...</div>;

  return (
    <div className="min-h-screen bg-slate-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        
        <Link to="/" className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-primary-600 mb-6 transition-colors">
          <ArrowLeft size={16} className="mr-2" />
          Back to Candidates
        </Link>

        {/* Profile Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mb-8">
          <div className="p-6 sm:p-8 flex items-start space-x-6">
            <UserCircle size={80} className="text-slate-300 flex-shrink-0" />
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-slate-900 mb-1">{candidate.name}</h1>
              <p className="text-slate-500 font-medium mb-4">{candidate.role_applied} • {candidate.email}</p>
              
              <div className="flex flex-wrap gap-2">
                {candidate.skills.map(s => (
                  <span key={s} className="px-3 py-1 bg-slate-100 text-slate-600 text-sm rounded-full font-medium">
                    {s}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex flex-col items-end">
              <span className={`px-4 py-2 inline-flex text-sm font-bold uppercase tracking-wider rounded-lg 
                  ${candidate.status === 'new' ? 'bg-blue-100 text-blue-800' : ''}
                  ${candidate.status === 'reviewed' ? 'bg-yellow-100 text-yellow-800' : ''}
                  ${candidate.status === 'hired' ? 'bg-green-100 text-green-800' : ''}
                  ${candidate.status === 'rejected' ? 'bg-red-100 text-red-800' : ''}
                `}>
                {candidate.status}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          <div className="md:col-span-2 space-y-8">
            {/* AI Summary Section */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5">
                <Brain size={120} />
              </div>
              <h3 className="text-lg font-bold text-slate-800 flex items-center mb-4 relative z-10">
                <Brain size={20} className="text-primary-500 mr-2" />
                AI Assistant Summary
              </h3>
              
              {summary ? (
                <div className="bg-primary-50 p-4 rounded-xl border border-primary-100 text-primary-900 leading-relaxed relative z-10">
                  {summary}
                </div>
              ) : (
                <div className="relative z-10">
                  <p className="text-slate-500 text-sm mb-4">Generate an AI summary of this candidate's profile and initial assessments.</p>
                  <button 
                    onClick={handleGenerateSummary}
                    disabled={isGeneratingSummary}
                    className="flex items-center px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-50"
                  >
                    {isGeneratingSummary ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing Profile...
                      </>
                    ) : 'Generate Summary'}
                  </button>
                </div>
              )}
            </div>

            {/* Scores List */}
            <div>
              <h3 className="text-lg font-bold text-slate-800 flex items-center mb-4">
                <Star size={20} className="text-yellow-500 mr-2" />
                Reviewer Scores
              </h3>
              <div className="space-y-4">
                {scores.map(s => (
                  <div key={s.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-start">
                    <div className="h-12 w-12 bg-yellow-100 rounded-lg flex items-center justify-center text-yellow-700 font-bold text-xl mr-4 flex-shrink-0">
                      {s.score}
                    </div>
                    <div>
                      <div className="font-bold text-slate-800">{s.category}</div>
                      <div className="text-sm text-slate-500 mb-2">By Reviewer: {s.reviewer_id.substring(0,8)}...</div>
                      {s.note && <div className="text-slate-700 italic bg-slate-50 p-2 rounded text-sm border border-slate-100">"{s.note}"</div>}
                    </div>
                  </div>
                ))}
                {scores.length === 0 && (
                  <div className="text-center p-8 bg-white rounded-xl border border-slate-200 border-dashed text-slate-500">
                    No scores submitted yet.
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-8">
            {/* Scoring Form */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
              <h3 className="text-lg font-bold text-slate-800 mb-4">Submit Score</h3>
              <form onSubmit={handleScoreSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
                  <select 
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    value={scoreForm.category}
                    onChange={e => setScoreForm({...scoreForm, category: e.target.value})}
                  >
                    <option>Technical</option>
                    <option>Communication</option>
                    <option>Culture Fit</option>
                    <option>System Design</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Score (1-5)</label>
                  <div className="flex gap-2">
                    {[1,2,3,4,5].map(num => (
                      <button
                        key={num}
                        type="button"
                        onClick={() => setScoreForm({...scoreForm, score: num})}
                        className={`flex-1 py-2 rounded-lg font-bold transition-all ${scoreForm.score === num ? 'bg-primary-600 text-white shadow-md' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                      >
                        {num}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Notes</label>
                  <textarea 
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    rows="3"
                    value={scoreForm.note}
                    onChange={e => setScoreForm({...scoreForm, note: e.target.value})}
                    placeholder="Optional feedback..."
                  ></textarea>
                </div>
                <button type="submit" className="w-full bg-primary-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-primary-700 transition-colors shadow-md">
                  Submit Score
                </button>
              </form>
            </div>

            {/* Admin Notes */}
            {user?.role === 'admin' && (
              <div className="bg-amber-50 p-6 rounded-2xl border border-amber-200">
                <h3 className="text-lg font-bold text-amber-900 flex items-center mb-2">
                  <FileText size={20} className="mr-2" />
                  Internal Notes (Admin Only)
                </h3>
                <p className="text-sm text-amber-800 bg-amber-100 p-3 rounded-lg">
                  {candidate.internal_notes || 'No internal notes recorded.'}
                </p>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
