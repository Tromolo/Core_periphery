import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Button,
  CircularProgress,
  Snackbar,
  Alert,
  Card,
  Grow
} from '@mui/material';
import { 
  CloudUpload
} from '@mui/icons-material';

const GraphUploader = ({ onUpload, selectedAnalyses }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) return;
    
    console.log('Selected file:', selectedFile);
    setFile(selectedFile);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    // Append selected analyses data
    if (selectedAnalyses) {
      formData.append('selectedAnalyses', JSON.stringify(selectedAnalyses));
      console.log('Appending selected analyses:', selectedAnalyses);
    }

    try {
      console.log('Sending upload request to /upload_graph...');
      
      onUpload({
        graph_data: { nodes: [], edges: [] },
        community_data: { 
          num_communities: 0,
          graph_data: { nodes: [], edges: [] }
        },
        network_metrics: {},
        filename: file.name, 
        filesize: file.size,
        filetype: file.type,
        loading: true
      });
      
      const response = await fetch('http://localhost:8080/upload_graph', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }
      
      const data = await response.json();
      console.log('Upload response:', data);
      
      data.filename = file.name;
      data.filesize = file.size;
      data.filetype = file.type;
      data.loading = false;
      
      onUpload(data);
      setSuccess(true);
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Failed to upload file. Please try again.');
      
      onUpload({
        error: err.message || 'Failed to upload file. Please try again.',
        loading: false
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Grow in={true} timeout={500}>
      <Card
        sx={{
          p: 4,
          background: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7))',
          backdropFilter: 'blur(10px)',
          boxShadow: 3,
          borderRadius: 2,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Typography variant="h5" sx={{ mb: 4, fontWeight: 'bold', color: 'primary.main', textAlign: 'center' }}>
          Upload Network Graph
        </Typography>
        
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
          <input
            accept=".csv,.txt,.gml,.graphml,.gexf,.edgelist,.net,.pajek"
            style={{ display: 'none' }}
            id="basic-graph-file-upload"
            type="file"
            onChange={handleFileChange}
          />
          <label htmlFor="basic-graph-file-upload">
            <Button
              variant="contained"
              component="span"
              startIcon={<CloudUpload />}
              sx={{
                bgcolor: 'primary.main',
                color: 'white',
                '&:hover': {
                  bgcolor: 'primary.dark',
                },
                py: 1.5,
                px: 3,
                borderRadius: 2,
                fontWeight: 'bold',
                boxShadow: '0 4px 10px rgba(0, 0, 0, 0.15)',
              }}
            >
              SELECT FILE
            </Button>
          </label>
          
          {file && (
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                Selected: {file.name}
              </Typography>
            </Box>
          )}

          {file && (
            <Button
              variant="contained"
              onClick={handleUpload}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <CloudUpload />}
              sx={{
                mt: 3,
                bgcolor: 'primary.main',
                '&:hover': {
                  bgcolor: 'primary.dark',
                },
                py: 1.5,
                px: 3,
                borderRadius: 2,
                fontWeight: 'bold',
                boxShadow: '0 4px 10px rgba(0, 0, 0, 0.15)',
              }}
            >
              {loading ? 'UPLOADING...' : 'UPLOAD GRAPH'}
            </Button>
          )}

          {error && (
            <Typography color="error" sx={{ mt: 2, textAlign: 'center' }}>
              {error}
            </Typography>
          )}

          <Snackbar open={success} autoHideDuration={6000} onClose={() => setSuccess(false)}>
            <Alert onClose={() => setSuccess(false)} severity="success" sx={{ width: '100%' }}>
              Graph uploaded successfully!
            </Alert>
          </Snackbar>
        </Box>
        
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Upload your network graph file to analyze basic network metrics, community structure, and connected components.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Supported formats: CSV, TXT, GML, GEXF, Edgelist,
          </Typography>
        </Box>
      </Card>
    </Grow>
  );
};

export default GraphUploader;