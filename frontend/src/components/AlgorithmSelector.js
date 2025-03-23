import React, { useState } from 'react';
import { 
  Card, 
  Box, 
  Typography, 
  Grow,
  Button,
  CircularProgress,
  Snackbar,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Paper,
  Grid,
  Chip
} from '@mui/material';
import { 
  PlayArrow,
  Science,
  Analytics,
  BarChart,
  CloudUpload
} from '@mui/icons-material';

const AlgorithmSelector = ({ graphData, onAnalysis, onUpload }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('rombach'); // Default to Rombach
  const [success, setSuccess] = useState(false);

  const algorithmInfo = {
    rombach: {
      name: "Rombach Algorithm",
      description: "A continuous core-periphery detection method that optimizes a quality function based on the density of connections.",
      reference: "Rombach et al. (2017)",
      icon: <Science />,
      params: {
        alpha: 0.3,
        beta: 0.6,
        num_runs: 10
      }
    },
    be: {
      name: "BE Algorithm",
      description: "Borgatti & Everett's discrete core-periphery detection method based on correlation with an ideal core-periphery structure.",
      reference: "Borgatti & Everett (2000)",
      icon: <Analytics />,
      params: {
        num_runs: 10
      }
    },
    holme: {
      name: "Holme Algorithm",
      description: "An iterative method that optimizes a core-coefficient quality function through node swapping.",
      reference: "Holme (2005)",
      icon: <BarChart />,
      params: {
        num_iterations: 100,
        threshold: 0.05
      }
    }
  };

  const handleAlgorithmChange = (algorithm) => {
    setSelectedAlgorithm(algorithm);
    setError(null);
  };
  
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) return;
    
    console.log('Selected file:', selectedFile);
    setFile(selectedFile);
    setError(null);
  };

  const handleAnalysis = async () => {
    if (!selectedAlgorithm) {
      setError('Please select an algorithm to analyze the graph.');
      return;
    }

    if (!file) {
      setError('Please select a graph file first.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Create a FormData object to send the file and algorithm parameters
      const formData = new FormData();
      formData.append('file', file);
      formData.append('algorithm', selectedAlgorithm);
      
      // Add algorithm-specific parameters
      const params = algorithmInfo[selectedAlgorithm].params;
      for (const [key, value] of Object.entries(params)) {
        formData.append(key, value);
      }

      // Send the request to the backend
      const response = await fetch('http://localhost:8080/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.error || 'Analysis failed');
      }

      // Immediately trigger navigation with placeholder data
      if (onUpload) {
        onUpload({
          filename: file.name,
          filesize: file.size,
          filetype: file.type
        });
      }
      
      // Provide minimal placeholder data to trigger immediate navigation
      onAnalysis({
        graph_data: { nodes: [], edges: [] },
        network_metrics: {},
        node_csv_file: null,
        edge_csv_file: null,
        gdf_file: null,
        image_file: null
      });
      
      // Continue processing the actual data in the background
      const data = await response.json();
      console.log('Analysis response:', data);
      
      // Pass the complete analysis results to the parent component
      onAnalysis(data);
      setSuccess(true);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to analyze graph. Please try again.');
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
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main', textAlign: 'center' }}>
          Core-Periphery Analysis
        </Typography>
        
        <Divider sx={{ mb: 3 }} />
        
        <Box sx={{ mb: 4, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <input
            accept=".csv,.txt,.gml,.graphml,.gexf,.edgelist,.net,.pajek"
            style={{ display: 'none' }}
            id="graph-file-upload"
            type="file"
            onChange={handleFileChange}
          />
          <label htmlFor="graph-file-upload">
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

          {error && (
            <Typography color="error" sx={{ mt: 2, textAlign: 'center' }}>
              {error}
            </Typography>
          )}
        </Box>
        
        <Typography variant="body1" sx={{ mb: 4, textAlign: 'center' }}>
          Select an algorithm to detect core-periphery structure in your network.
          Each algorithm uses different approaches to identify core and peripheral nodes.
        </Typography>

        <Typography variant="h6" sx={{ mb: 2, color: 'primary.dark' }}>
          Available Algorithms:
        </Typography>
        
        <Grid container spacing={2} sx={{ mb: 4 }}>
          {Object.entries(algorithmInfo).map(([key, info]) => (
            <Grid item xs={12} md={4} key={key}>
              <Paper 
                elevation={selectedAlgorithm === key ? 3 : 1}
                sx={{ 
                  p: 2, 
                  borderRadius: 2,
                  cursor: 'pointer',
                  border: selectedAlgorithm === key ? '2px solid #1a237e' : '1px solid #e0e0e0',
                  bgcolor: selectedAlgorithm === key ? 'rgba(26, 35, 126, 0.05)' : 'white',
                  transition: 'all 0.2s ease',
                  height: '100%',
                  '&:hover': {
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
                    transform: 'translateY(-2px)'
                  }
                }}
                onClick={() => handleAlgorithmChange(key)}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box sx={{ color: 'primary.main', mr: 1 }}>
                    {info.icon}
                  </Box>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {info.name}
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {info.description}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Reference: {info.reference}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ mt: 'auto', display: 'flex', justifyContent: 'center' }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            disabled={loading || !file}
            onClick={handleAnalysis}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
            sx={{
              py: 1.5,
              px: 4,
              borderRadius: 2,
              fontWeight: 'bold',
              background: 'linear-gradient(45deg, #1a237e 30%, #0d47a1 90%)',
              boxShadow: '0 4px 10px rgba(0, 0, 0, 0.25)',
              '&:hover': {
                background: 'linear-gradient(45deg, #0d47a1 30%, #1a237e 90%)',
                transform: 'translateY(-2px)',
                boxShadow: '0 6px 15px rgba(0, 0, 0, 0.3)',
              },
              transition: 'all 0.3s ease',
            }}
          >
            {loading ? 'ANALYZING...' : 'RUN CORE-PERIPHERY ANALYSIS'}
          </Button>
        </Box>

        <Snackbar 
          open={success} 
          autoHideDuration={6000} 
          onClose={() => setSuccess(false)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert onClose={() => setSuccess(false)} severity="success" sx={{ width: '100%' }}>
            Analysis completed successfully!
          </Alert>
        </Snackbar>
      </Card>
    </Grow>
  );
};

export default AlgorithmSelector; 