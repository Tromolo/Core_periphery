import React, { useState } from 'react';
import { 
  Card, 
  Box, 
  Typography, 
  Grow,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Snackbar,
  Alert
} from '@mui/material';
import { 
  CloudUpload
} from '@mui/icons-material';


const GraphUploader = ({ onUpload }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [algorithm, setAlgorithm] = useState('rombach'); 
  const [file, setFile] = useState(null); 
  const [success, setSuccess] = useState(false); 

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null); 
    }
  };

  const handleFileUpload = async () => {
    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('algorithm', algorithm);
    // sending algorithm to backend correctly backend receives algorithm as rombach
    console.log("Algorithm:", algorithm);

    try {
      const response = await fetch('http://localhost:8080/upload_graph', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      onUpload(data);
      setSuccess(true);
      setFile(null);
    } catch (err) {
      setError(err.message || 'Failed to upload file. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Grow in={true} timeout={500}>
      <Card
        sx={{
          p: 4,
          textAlign: 'center',
          background: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7))',
          backdropFilter: 'blur(10px)',
          boxShadow: 3,
          borderRadius: 2,
        }}
      >
        <Stack spacing={3} alignItems="center">
          <Box>
            <input
              type="file"
              accept=".csv,.txt,.gml,.graphml,.gexf,.edgelist"
              onChange={handleFileChange}
              style={{ display: 'none' }}
              id="file-upload"
            />
            <label htmlFor="file-upload">
              <Button
                component="span"
                variant="contained"
                size="large"
                startIcon={<CloudUpload />}
                sx={{
                  px: 4,
                  py: 2,
                  bgcolor: 'primary.main',
                  '&:hover': {
                    bgcolor: 'primary.dark',
                  },
                  transition: 'background-color 0.3s ease',
                }}
              >
                {file ? file.name : 'Select Network File'}
              </Button>
            </label>
          </Box>

          <Typography variant="body1" sx={{ color: 'text.secondary' }}>
            Accepted file types: CSV, TXT, GML, GraphML, GEXF
          </Typography>

          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel id="algorithm-select-label">Algorithm</InputLabel>
            <Select
              labelId="algorithm-select-label"
              value={algorithm}
              label="Algorithm"
              onChange={(e) => setAlgorithm(e.target.value)}
            >
              <MenuItem value="rombach">Rombach</MenuItem>
              <MenuItem value="be">BE</MenuItem>
              <MenuItem value="holme">Holme</MenuItem>
            </Select>
          </FormControl>

          <Button
            variant="contained"
            onClick={handleFileUpload}
            disabled={loading || !file}
            sx={{
              bgcolor: 'primary.main',
              '&:hover': {
                bgcolor: 'primary.dark',
              },
              transition: 'background-color 0.3s ease',
            }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Submit'}
          </Button>

          {error && (
            <Typography color="error">
              {error}
            </Typography>
          )}
        </Stack>

        <Snackbar open={success} autoHideDuration={6000} onClose={() => setSuccess(false)}>
          <Alert onClose={() => setSuccess(false)} severity="success" sx={{ width: '100%' }}>
            File uploaded successfully!
          </Alert>
        </Snackbar>
      </Card>
    </Grow>
  );
};

export default GraphUploader;