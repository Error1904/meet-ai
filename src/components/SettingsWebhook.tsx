import React, { useState, useEffect } from 'react';
import { Webhook, Plus, Trash2, CheckCircle2, AlertCircle, Play, RefreshCw, Terminal } from 'lucide-react';

interface WebhookConfig {
  id: string;
  name: string;
  url: string;
  is_active: boolean;
  headers?: any;
}

interface WebhookLog {
  id: number;
  webhook_id: string;
  session_id: string;
  status_code: number;
  request_payload: any;
  response_body: string;
  timestamp: number;
}

const API_BASE = 'http://localhost:8765/api';

export const SettingsWebhook: React.FC = () => {
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([]);
  const [logs, setLogs] = useState<WebhookLog[]>([]);
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const fetchWebhooks = async () => {
    try {
      const res = await fetch(`${API_BASE}/webhooks`);
      if (res.ok) {
        const data = await res.json();
        setWebhooks(data);
      }
    } catch (err) {
      console.error('[Fetch Webhooks Error]', err);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/webhooks/logs`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error('[Fetch Logs Error]', err);
    }
  };

  useEffect(() => {
    fetchWebhooks();
    fetchLogs();
  }, []);

  const handleAddWebhook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !url.trim()) return;

    const newWh: WebhookConfig = {
      id: `wh-${Date.now()}`,
      name,
      url,
      is_active: true,
    };

    try {
      const res = await fetch(`${API_BASE}/webhooks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newWh),
      });
      if (res.ok) {
        setName('');
        setUrl('');
        fetchWebhooks();
      }
    } catch (err) {
      console.error('[Add Webhook Error]', err);
    }
  };

  const handleDeleteWebhook = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/webhooks/${id}`, { method: 'DELETE' });
      if (res.ok) {
        fetchWebhooks();
      }
    } catch (err) {
      console.error('[Delete Webhook Error]', err);
    }
  };

  const handleTestWebhook = async (webhookId: string = 'mock-webhook-1') => {
    setIsTestRunning(true);
    setTestResult(null);

    try {
      const res = await fetch(`${API_BASE}/webhooks/retrigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          webhook_id: webhookId,
          session_id: 'test-verification-session',
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setTestResult(`Test Webhook Triggered! Status Code: ${data.status_code}. Response: ${data.response}`);
        fetchLogs();
      } else {
        setTestResult('Failed to trigger test webhook endpoint.');
      }
    } catch (err) {
      setTestResult('Error connecting to webhook engine.');
    }
    setIsTestRunning(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] gap-6 overflow-y-auto pr-1">
      {/* Header */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-lg text-white flex items-center gap-2">
            <Webhook className="w-5 h-5 text-indigo-400" />
            <span>Automated Action Item Webhook Dispatcher</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Automatically post extracted Action Items upon meeting conclusion to Notion, Trello, Zapier, n8n, or local REST endpoints.
          </p>
        </div>
      </div>

      {/* Grid: Webhook Configurator and Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form and Registered Webhooks */}
        <div className="space-y-4">
          {/* Add Form */}
          <div className="glass-card rounded-2xl p-5 border border-slate-800">
            <h3 className="text-sm font-semibold text-white mb-3">Add Webhook Endpoint</h3>
            <form onSubmit={handleAddWebhook} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Webhook Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Notion Action Items / Trello Board"
                  className="w-full bg-slate-900 border border-slate-700 text-white text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Target Endpoint URL</label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="http://localhost:8080/webhook"
                  className="w-full bg-slate-900 border border-slate-700 text-white text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-indigo-500"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs py-2 rounded-lg flex items-center justify-center gap-1.5 transition-all shadow-md"
              >
                <Plus className="w-4 h-4" />
                <span>Save Webhook</span>
              </button>
            </form>
          </div>

          {/* Registered Webhooks List */}
          <div className="glass-card rounded-2xl p-5 border border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">Configured Endpoints</h3>
              <button
                onClick={() => handleTestWebhook('mock-webhook-1')}
                disabled={isTestRunning}
                className="bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-500/40 text-xs px-3 py-1 rounded-lg flex items-center gap-1.5 transition-colors disabled:opacity-50"
              >
                <Play className="w-3 h-3 text-emerald-400 fill-current" />
                <span>Test Local Mock Endpoint (8080)</span>
              </button>
            </div>

            {testResult && (
              <div className="mb-3 bg-indigo-950/90 border border-indigo-500/40 text-indigo-200 text-xs p-3 rounded-xl animate-in fade-in">
                {testResult}
              </div>
            )}

            <div className="space-y-2.5">
              {webhooks.map((wh) => (
                <div
                  key={wh.id}
                  className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 flex items-center justify-between gap-3"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-white">{wh.name}</span>
                      <span className="bg-emerald-950 text-emerald-300 border border-emerald-500/30 text-[10px] px-1.5 py-0.2 rounded">
                        Active
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-mono truncate mt-0.5">{wh.url}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleTestWebhook(wh.id)}
                      className="text-indigo-400 hover:text-indigo-300 text-xs bg-indigo-950/60 p-1.5 rounded border border-indigo-500/30"
                      title="Test Webhook"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                    </button>
                    <button
                      onClick={() => handleDeleteWebhook(wh.id)}
                      className="text-slate-500 hover:text-rose-400 text-xs p-1.5 rounded"
                      title="Delete"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Webhook Execution Logs (1 Col) */}
        <div className="glass-card rounded-2xl p-5 border border-slate-800 flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Terminal className="w-4 h-4 text-indigo-400" />
              <span>Execution Logs & Delivery Payloads</span>
            </h3>
            <button
              onClick={fetchLogs}
              className="text-slate-400 hover:text-slate-200 p-1 rounded"
              title="Refresh Logs"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 text-xs pr-1">
            {logs.length === 0 ? (
              <div className="text-center py-10 text-slate-500 text-xs">
                No webhook execution logs recorded yet.
              </div>
            ) : (
              logs.map((log) => {
                const isSuccess = log.status_code >= 200 && log.status_code < 300;
                return (
                  <div
                    key={log.id}
                    className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[11px] text-slate-400">
                        {new Date(log.timestamp * 1000).toLocaleTimeString()}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                          isSuccess
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
                            : 'bg-rose-950 text-rose-300 border border-rose-500/40'
                        }`}
                      >
                        HTTP {log.status_code}
                      </span>
                    </div>

                    <div>
                      <p className="text-[10px] text-slate-500 font-mono">Payload Sample:</p>
                      <pre className="bg-slate-950 p-2 rounded text-[10px] text-slate-300 font-mono overflow-x-auto mt-1 border border-slate-800/80">
                        {JSON.stringify(log.request_payload, null, 2)}
                      </pre>
                    </div>

                    <div>
                      <p className="text-[10px] text-slate-500 font-mono">Response Output:</p>
                      <p className="text-[11px] text-slate-300 truncate mt-0.5">{log.response_body}</p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
