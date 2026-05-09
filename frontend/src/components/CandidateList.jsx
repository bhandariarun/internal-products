import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { Search, Filter, ChevronLeft, ChevronRight, LogOut, Users } from 'lucide-react';

export default function CandidateList() {
  const [candidates, setCandidates] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ status: '', role_applied: '', keyword: '' });
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const fetchCandidates = async () => {
    try {
      const params = new URLSearchParams({ page, page_size: 10 });
      if (filters.status) params.append('status', filters.status);
      if (filters.role_applied) params.append('role_applied', filters.role_applied);
      if (filters.keyword) params.append('keyword', filters.keyword);

      const res = await api.get(`/candidates?${params.toString()}`);
      setCandidates(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [page, filters]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-primary-600">
            <Users size={24} />
            <span className="font-bold text-xl tracking-tight text-slate-800">TechKraft</span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-slate-500 bg-slate-100 px-3 py-1 rounded-full uppercase tracking-wider">
              {user?.role}
            </span>
            <button
              onClick={handleLogout}
              className="text-slate-500 hover:text-red-600 transition-colors p-2"
              title="Logout"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 mb-6 flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Search</label>
            <div className="relative">
              <input
                type="text"
                placeholder="Name or email..."
                className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"
                value={filters.keyword}
                onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              />
              <Search className="absolute left-3 top-2.5 text-slate-400" size={18} />
            </div>
          </div>
          <div className="w-48">
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Status</label>
            <select
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            >
              <option value="">All Statuses</option>
              <option value="new">New</option>
              <option value="reviewed">Reviewed</option>
              <option value="hired">Hired</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <div className="w-48">
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Role</label>
            <input
              type="text"
              placeholder="e.g. Backend Engineer"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"
              value={filters.role_applied}
              onChange={(e) => setFilters({ ...filters, role_applied: e.target.value })}
            />
          </div>
        </div>

        {/* List */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Candidate</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {candidates.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 flex-shrink-0 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold">
                        {c.name.charAt(0)}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-slate-900">{c.name}</div>
                        <div className="text-sm text-slate-500">{c.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                    {c.role_applied}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                      ${c.status === 'new' ? 'bg-blue-100 text-blue-800' : ''}
                      ${c.status === 'reviewed' ? 'bg-yellow-100 text-yellow-800' : ''}
                      ${c.status === 'hired' ? 'bg-green-100 text-green-800' : ''}
                      ${c.status === 'rejected' ? 'bg-red-100 text-red-800' : ''}
                    `}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link to={`/candidate/${c.id}`} className="text-primary-600 hover:text-primary-900 font-semibold bg-primary-50 px-3 py-1 rounded-md hover:bg-primary-100 transition-colors">
                      Review
                    </Link>
                  </td>
                </tr>
              ))}
              {candidates.length === 0 && (
                <tr>
                  <td colSpan="4" className="px-6 py-12 text-center text-slate-500">
                    No candidates found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-slate-500">
            Showing <span className="font-medium">{(page - 1) * 10 + 1}</span> to <span className="font-medium">{Math.min(page * 10, total)}</span> of <span className="font-medium">{total}</span> results
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
            >
              <ChevronLeft size={20} className="text-slate-600" />
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page * 10 >= total}
              className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
            >
              <ChevronRight size={20} className="text-slate-600" />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
