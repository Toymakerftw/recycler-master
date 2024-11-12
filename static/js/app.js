import React, { useState, useEffect } from 'react';
import { AppProvider, useApp } from './AppContext';
import { api } from './api';
import { 
  Users, Folder, File, ChevronRight, ChevronDown, 
  Trash2, Eye, AlertCircle, Download, RefreshCw,
  HardDrive, Clock, Database
} from 'lucide-react';

// Utility function to format bytes to human readable format
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

// Utility function to format date
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString();
};

// Stats Card Component
const StatsCard = ({ title, value, icon: Icon, subtext }) => (
  <div className="bg-white rounded-lg shadow p-6 flex flex-col">
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-sm font-medium text-gray-600">{title}</h3>
      <Icon className="h-5 w-5 text-gray-400" />
    </div>
    <div className="text-2xl font-bold mb-1">{value}</div>
    {subtext && <p className="text-sm text-gray-500">{subtext}</p>}
  </div>
);

// File Explorer Component
const FileExplorer = ({ clientIp }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedFolders, setExpandedFolders] = useState({});

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        setLoading(true);
        const response = await api.getClientFiles(clientIp);
        if (response.success) {
          setFiles(response.files);
        } else {
          setError(response.message);
        }
      } catch (err) {
        setError('Failed to fetch files');
      } finally {
        setLoading(false);
      }
    };

    if (clientIp) {
      fetchFiles();
    }
  }, [clientIp]);

  const toggleFolder = (path) => {
    setExpandedFolders(prev => ({
      ...prev,
      [path]: !prev[path]
    }));
  };

  const handleDownload = async (filePath) => {
    await api.downloadFile(clientIp, filePath);
  };

  const renderFileTree = (items, path = '') => {
    return items?.map((item) => {
      const currentPath = `${path}/${item.name}`;
      const isExpanded = expandedFolders[currentPath];

      if (item.type === 'folder') {
        return (
          <div key={currentPath} className="ml-4">
            <div 
              className="flex items-center gap-2 py-1 hover:bg-gray-100 rounded cursor-pointer"
              onClick={() => toggleFolder(currentPath)}
            >
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              <Folder size={16} className="text-blue-500" />
              <span className="flex-1">{item.name}</span>
              <span className="text-sm text-gray-500">{formatBytes(item.size)}</span>
              <span className="text-sm text-gray-500">{formatDate(item.modified)}</span>
            </div>
            {isExpanded && item.children && (
              <div className="ml-4">
                {renderFileTree(item.children, currentPath)}
              </div>
            )}
          </div>
        );
      }

      return (
        <div key={currentPath} className="flex items-center gap-2 py-1 ml-8 hover:bg-gray-100 rounded group">
          <File size={16} className="text-gray-500" />
          <span className="flex-1">{item.name}</span>
          <span className="text-sm text-gray-500">{formatBytes(item.size)}</span>
          <span className="text-sm text-gray-500">{formatDate(item.modified)}</span>
          <button
            onClick={() => handleDownload(currentPath)}
            className="invisible group-hover:visible p-1 hover:bg-blue-100 rounded"
          >
            <Download size={16} className="text-blue-500" />
          </button>
        </div>
      );
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8 text-red-500">
        <AlertCircle className="h-6 w-6 mr-2" />
        {error}
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-4">
      {files.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No files found
        </div>
      ) : (
        renderFileTree(files)
      )}
    </div>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const { 
    clients, 
    loading, 
    error, 
    addClient, 
    removeClient, 
    refreshClients 
  } = useApp();
  const [newClientIp, setNewClientIp] = useState('');
  const [selectedClient, setSelectedClient] = useState(null);

  const handleAddClient = async (e) => {
    e.preventDefault();
    if (!newClientIp) return;

    const result = await addClient(newClientIp);
    if (result.success) {
      setNewClientIp('');
    } else {
      alert(result.message);
    }
  };

  const handleRemoveClient = async (clientIp) => {
    if (window.confirm(`Are you sure you want to remove client ${clientIp}?`)) {
      const result = await removeClient(clientIp);
      if (!result.success) {
        alert(result.message);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen text-red-500">
        <AlertCircle className="h-8 w-8 mr-2" />
        {error}
      </div>
    );
  }

  const totalStorage = clients.reduce((acc, client) => acc + client.total_size, 0);
  const totalFiles = clients.reduce((acc, client) => acc + client.total_files, 0);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">NFS Client Manager</h1>
        <p className="text-gray-500">Manage your NFS clients and explore their files</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <StatsCard 
          title="Total Clients"
          value={clients.length}
          icon={Users}
          subtext="Active NFS connections"
        />
        <StatsCard 
          title="Total Storage"
          value={formatBytes(totalStorage)}
          icon={HardDrive}
          subtext="Combined storage usage"
        />
        <StatsCard 
          title="Total Files"
          value={totalFiles}
          icon={Database}
          subtext="Across all clients"
        />
        <StatsCard 
          title="Last Update"
          value={formatDate(new Date())}
          icon={Clock}
          subtext="System status"
        />
      </div>

      {/* Add Client Form */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-medium mb-4">Add New Client</h2>
        <form onSubmit={handleAddClient} className="flex gap-4">
          <input
            type="text"
            value={newClientIp}
            onChange={(e) => setNewClientIp(e.target.value)}
            placeholder="Enter client IP address"
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Add Client
          </button>
        </form>
      </div>

      {/* Clients List and File Explorer */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Clients List */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">Connected Clients</h2>
          <div className="space-y-2">
            {clients.map(client => (
              <div 
                key={client.ip}
                className={`p-3 rounded-lg border cursor-pointer transition-colors
                  ${selectedClient === client.ip ? 'bg-blue-50 border-blue-200' : 'hover:bg-gray-50 border-gray-200'}`}
                onClick={() => setSelectedClient(client.ip)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{client.ip}</div>
                    <div className="text-sm text-gray-500">
                      {formatBytes(client.total_size)} • {client.total_files} files
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedClient(client.ip);
                      }}
                      className="p-2 hover:bg-blue-100 rounded"
                    >
                      <Eye className="h-4 w-4 text-blue-500" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveClient(client.ip);
                      }}
                      className="p-2 hover:bg-red-100 rounded"
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* File Explorer */}
        <div className="bg-white rounded-lg shadow p-6 md:col-span-2">
          <h2 className="text-lg font-medium mb-4">File Explorer</h2>
          {selectedClient ? (
            <FileExplorer clientIp={selectedClient} />
          ) : (
            <div className="text-center py-8 text-gray-500">
              Select a client to view files
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Root App Component
const App = () => (
  <AppProvider>
    <Dashboard />
  </AppProvider>
);

// Render the app
ReactDOM.render(<App />, document.getElementById('root'));
