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
  Chip,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Tooltip,
  TextField,
  Slider,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import { 
  PlayArrow,
  Science,
  Analytics,
  BarChart,
  CloudUpload,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon,
  Timeline,
  Assessment
} from '@mui/icons-material';

const AlgorithmSelector = ({ graphData, onAnalysis, onUpload }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('rombach');
  const [success, setSuccess] = useState(false);
  const [calculateCloseness, setCalculateCloseness] = useState(false);
  const [calculateBetweenness, setCalculateBetweenness] = useState(false);
  
  const algorithmInfo = {
    rombach: {
      name: "Rombach Algorithm",
      description: "A continuous core-periphery detection method that optimizes a quality function based on the density of connections.",
      reference: "Rombach et al. (2017)",
      icon: <Science />,
      params: {
        alpha: 0.5,
        beta: 0.8,
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
    cucuringu: {
      name: "Cucuringu Algorithm",
      description: "A spectral method for core-periphery detection using low-rank matrix approximation and eigendecomposition.",
      reference: "Cucuringu et al. (2016)",
      icon: <BarChart />,
      params: {
        beta: 0.1
      }
    }
  };
  
  const [alpha, setAlpha] = useState(algorithmInfo.rombach.params.alpha);
  const [beta, setBeta] = useState(algorithmInfo.rombach.params.beta);
  const [numRuns, setNumRuns] = useState(algorithmInfo.rombach.params.num_runs);

  const handleAlgorithmChange = (algorithm) => {
    setSelectedAlgorithm(algorithm);
    setError(null);
    
    const defaultParams = algorithmInfo[algorithm].params;
    if (defaultParams.alpha !== undefined) setAlpha(defaultParams.alpha);
    if (defaultParams.beta !== undefined) setBeta(defaultParams.beta);
    if (defaultParams.num_runs !== undefined) setNumRuns(defaultParams.num_runs);
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

    let validationError = null;
    
    if (selectedAlgorithm === 'rombach') {
      if (alpha < 0 || alpha > 1) {
        validationError = 'Alpha must be between 0 and 1';
      } else if (beta < 0 || beta > 1) {
        validationError = 'Beta must be between 0 and 1';
      } else if (numRuns < 1) {
        validationError = 'Number of runs must be at least 1';
      }
    } else if (selectedAlgorithm === 'be') {
      if (numRuns < 1) {
        validationError = 'Number of runs must be at least 1';
      }
    } else if (selectedAlgorithm === 'cucuringu') {
      if (beta < 0.01 || beta > 0.5) {
        validationError = 'Beta must be between 0.01 and 0.5 for Cucuringu algorithm';
      }
    }
    
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('algorithm', selectedAlgorithm);
      
      if (selectedAlgorithm === 'rombach') {
        formData.append('alpha', Number(alpha));
        formData.append('beta', Number(beta));
        formData.append('num_runs', Number(numRuns));
      } else if (selectedAlgorithm === 'be') {
        formData.append('num_runs', Number(numRuns));
      } else if (selectedAlgorithm === 'cucuringu') {
        formData.append('beta', Number(beta));
      }
      
      formData.append('calculate_closeness', calculateCloseness);
      formData.append('calculate_betweenness', calculateBetweenness);

      console.log('Sending parameters:', {
        algorithm: selectedAlgorithm,
        ...(selectedAlgorithm === 'rombach' ? { alpha, beta, num_runs: numRuns } : {}),
        ...(selectedAlgorithm === 'be' ? { num_runs: numRuns } : {}),
        ...(selectedAlgorithm === 'cucuringu' ? { beta } : {})
      });

      const response = await fetch('http://localhost:8080/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.error || 'Analysis failed');
      }

      if (onUpload) {
        onUpload({
          filename: file.name,
          filesize: file.size,
          filetype: file.type
        });
      }
      
      onAnalysis({
        graph_data: { nodes: [], edges: [] },
        network_metrics: {},
        node_csv_file: null,
        edge_csv_file: null,
        gdf_file: null,
        image_file: null
      });
      
      const data = await response.json();
      console.log('Analysis response:', data);
      
      onAnalysis(data);
      setSuccess(true);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to analyze graph. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getParameterDescription = (key) => {
    const descriptions = {
      'alpha': 'Controls the sharpness of the core-periphery boundary. Higher values create a more defined boundary.',
      'beta': selectedAlgorithm === 'rombach' 
        ? 'Controls the fraction of peripheral nodes in the network partitioning.' 
        : 'Controls the minimum boundary size for core detection, affecting how the algorithm partitions the network.',
      'num_runs': 'Number of independent algorithm runs with different initializations. Higher values improve result consistency.'
    };
    
    return descriptions[key] || 'No description available';
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

        <Accordion 
          expanded={true}
          sx={{ 
            mb: 4, 
            bgcolor: 'rgba(25, 118, 210, 0.04)', 
            borderRadius: '8px !important',
            '&:before': { display: 'none' } 
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{ borderRadius: '8px' }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <SettingsIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ color: 'primary.dark' }}>
                Algorithm Parameters
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" sx={{ mb: 3, color: 'text.secondary' }}>
              Customize parameters to fine-tune the core-periphery detection. Different settings may yield different results.
            </Typography>
            
            <Grid container spacing={3}>
              {selectedAlgorithm === 'rombach' && (
                <>
                  <Grid item xs={12} md={4}>
                    <Box sx={{ 
                      p: 3, 
                      bgcolor: 'rgba(233, 30, 99, 0.05)', 
                      borderRadius: 2,
                      border: '1px solid rgba(233, 30, 99, 0.1)'
                    }}>
                      <Typography variant="h6" sx={{ 
                        color: '#e91e63', 
                        mb: 2,
                        display: 'flex',
                        alignItems: 'center'
                      }}>
                        <SettingsIcon sx={{ fontSize: 20, mr: 1 }} />
                        Alpha (α)
                      </Typography>
                      
                      <Typography variant="body2" sx={{ mb: 3 }}>
                        Controls the sharpness of the core-periphery boundary. Higher values create a more defined boundary.
                      </Typography>
                      
                      <Box sx={{ mb: 3 }}>
                        <Slider
                          value={alpha}
                          onChange={(e, newValue) => setAlpha(newValue)}
                          min={0}
                          max={1}
                          step={0.1}
                          marks={[
                            { value: 0, label: '0' },
                            { value: 0.5, label: '0.5' },
                            { value: 1, label: '1' }
                          ]}
                          sx={{
                            color: '#e91e63',
                            '& .MuiSlider-thumb': {
                              width: 24,
                              height: 24,
                              backgroundColor: '#fff',
                              border: '2px solid #e91e63',
                              '&:focus, &:hover, &.Mui-active': {
                                boxShadow: '0 0 0 8px rgba(233, 30, 99, 0.16)',
                              },
                            },
                            '& .MuiSlider-valueLabel': {
                              backgroundColor: '#e91e63',
                            },
                          }}
                        />
                      </Box>
                      
                      <TextField 
                        label="Alpha Value"
                        type="number"
                        value={alpha}
                        onChange={(e) => setAlpha(parseFloat(e.target.value))}
                        inputProps={{ min: 0, max: 1, step: 0.1 }}
                        variant="outlined"
                        size="small"
                        fullWidth
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            '&.Mui-focused fieldset': {
                              borderColor: '#e91e63',
                            },
                          },
                          '& .MuiInputLabel-root.Mui-focused': {
                            color: '#e91e63',
                          }
                        }}
                      />
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Box sx={{ 
                      p: 3, 
                      bgcolor: 'rgba(156, 39, 176, 0.05)', 
                      borderRadius: 2, 
                      border: '1px solid rgba(156, 39, 176, 0.1)'
                    }}>
                      <Typography variant="h6" sx={{ 
                        color: '#9c27b0', 
                        mb: 2,
                        display: 'flex',
                        alignItems: 'center'
                      }}>
                        <Timeline sx={{ fontSize: 20, mr: 1 }} />
                        Beta (β)
                      </Typography>
                      
                      <Typography variant="body2" sx={{ mb: 3 }}>
                        Controls the fraction of peripheral nodes in the network partitioning.
                      </Typography>
                      
                      <Box sx={{ mb: 3 }}>
                        <Slider
                          value={beta}
                          onChange={(e, newValue) => setBeta(newValue)}
                          min={0}
                          max={1}
                          step={0.1}
                          marks={[
                            { value: 0, label: '0' },
                            { value: 0.5, label: '0.5' },
                            { value: 1, label: '1' }
                          ]}
                          sx={{
                            color: '#9c27b0',
                            '& .MuiSlider-thumb': {
                              width: 24,
                              height: 24,
                              backgroundColor: '#fff',
                              border: '2px solid #9c27b0',
                              '&:focus, &:hover, &.Mui-active': {
                                boxShadow: '0 0 0 8px rgba(156, 39, 176, 0.16)',
                              },
                            },
                            '& .MuiSlider-valueLabel': {
                              backgroundColor: '#9c27b0',
                            },
                          }}
                        />
                      </Box>
                      
                      <TextField 
                        label="Beta Value"
                        type="number"
                        value={beta}
                        onChange={(e) => setBeta(parseFloat(e.target.value))}
                        inputProps={{ min: 0, max: 1, step: 0.1 }}
                        variant="outlined"
                        size="small"
                        fullWidth
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            '&.Mui-focused fieldset': {
                              borderColor: '#9c27b0',
                            },
                          },
                          '& .MuiInputLabel-root.Mui-focused': {
                            color: '#9c27b0',
                          }
                        }}
                      />
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Box sx={{ 
                      p: 3, 
                      bgcolor: 'rgba(33, 150, 243, 0.05)', 
                      borderRadius: 2,
                      border: '1px solid rgba(33, 150, 243, 0.1)'
                    }}>
                      <Typography variant="h6" sx={{ 
                        color: '#2196f3', 
                        mb: 2,
                        display: 'flex',
                        alignItems: 'center'
                      }}>
                        <Assessment sx={{ fontSize: 20, mr: 1 }} />
                        Number of Runs
                      </Typography>
                      
                      <Typography variant="body2" sx={{ mb: 3 }}>
                        Number of independent algorithm runs with different initializations. Higher values improve result consistency.
                      </Typography>
                      
                      <Box sx={{ mb: 3 }}>
                        <Slider
                          value={numRuns}
                          onChange={(e, newValue) => setNumRuns(newValue)}
                          min={1}
                          max={20}
                          step={1}
                          marks={[
                            { value: 1, label: '1' },
                            { value: 10, label: '10' },
                            { value: 20, label: '20' }
                          ]}
                          sx={{
                            color: '#2196f3',
                            '& .MuiSlider-thumb': {
                              width: 24,
                              height: 24,
                              backgroundColor: '#fff',
                              border: '2px solid #2196f3',
                              '&:focus, &:hover, &.Mui-active': {
                                boxShadow: '0 0 0 8px rgba(33, 150, 243, 0.16)',
                              },
                            },
                            '& .MuiSlider-valueLabel': {
                              backgroundColor: '#2196f3',
                            },
                          }}
                        />
                      </Box>
                      
                      <TextField 
                        label="Number of Runs"
                        type="number"
                        value={numRuns}
                        onChange={(e) => setNumRuns(parseInt(e.target.value))}
                        inputProps={{ min: 1, max: 50, step: 1 }}
                        variant="outlined"
                        size="small"
                        fullWidth
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            '&.Mui-focused fieldset': {
                              borderColor: '#2196f3',
                            },
                          },
                          '& .MuiInputLabel-root.Mui-focused': {
                            color: '#2196f3',
                          }
                        }}
                      />
                    </Box>
                  </Grid>
                </>
              )}
              
              {selectedAlgorithm === 'be' && (
                <Grid item xs={12} md={6} sx={{ mx: 'auto' }}>
                  <Box sx={{ 
                    p: 3, 
                    bgcolor: 'rgba(33, 150, 243, 0.05)', 
                    borderRadius: 2,
                    border: '1px solid rgba(33, 150, 243, 0.1)'
                  }}>
                    <Typography variant="h6" sx={{ 
                      color: '#2196f3', 
                      mb: 2,
                      display: 'flex',
                      alignItems: 'center'
                    }}>
                      <Assessment sx={{ fontSize: 20, mr: 1 }} />
                      Number of Runs
                    </Typography>
                    
                    <Typography variant="body2" sx={{ mb: 3 }}>
                      Number of independent algorithm runs with different initializations. Higher values improve result consistency.
                    </Typography>
                    
                    <Box sx={{ mb: 3 }}>
                      <Slider
                        value={numRuns}
                        onChange={(e, newValue) => setNumRuns(newValue)}
                        min={1}
                        max={20}
                        step={1}
                        marks={[
                          { value: 1, label: '1' },
                          { value: 10, label: '10' },
                          { value: 20, label: '20' }
                        ]}
                        sx={{
                          color: '#2196f3',
                          '& .MuiSlider-thumb': {
                            width: 24,
                            height: 24,
                            backgroundColor: '#fff',
                            border: '2px solid #2196f3',
                            '&:focus, &:hover, &.Mui-active': {
                              boxShadow: '0 0 0 8px rgba(33, 150, 243, 0.16)',
                            },
                          },
                          '& .MuiSlider-valueLabel': {
                            backgroundColor: '#2196f3',
                          },
                        }}
                      />
                    </Box>
                    
                    <TextField 
                      label="Number of Runs"
                      type="number"
                      value={numRuns}
                      onChange={(e) => setNumRuns(parseInt(e.target.value))}
                      inputProps={{ min: 1, max: 50, step: 1 }}
                      variant="outlined"
                      size="small"
                      fullWidth
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '&.Mui-focused fieldset': {
                            borderColor: '#2196f3',
                          },
                        },
                        '& .MuiInputLabel-root.Mui-focused': {
                          color: '#2196f3',
                        }
                      }}
                    />
                  </Box>
                </Grid>
              )}
              
              {selectedAlgorithm === 'cucuringu' && (
                <Grid item xs={12} md={6} sx={{ mx: 'auto' }}>
                  <Box sx={{ 
                    p: 3, 
                    bgcolor: 'rgba(156, 39, 176, 0.05)', 
                    borderRadius: 2,
                    border: '1px solid rgba(156, 39, 176, 0.1)'
                  }}>
                    <Typography variant="h6" sx={{ 
                      color: '#9c27b0', 
                      mb: 2,
                      display: 'flex',
                      alignItems: 'center'
                    }}>
                      <Timeline sx={{ fontSize: 20, mr: 1 }} />
                      Beta (β)
                    </Typography>
                    
                    <Typography variant="body2" sx={{ mb: 3 }}>
                      Controls the minimum boundary size for core detection, affecting how the algorithm partitions the network.
                    </Typography>
                    
                    <Box sx={{ mb: 3 }}>
                      <Slider
                        value={beta}
                        onChange={(e, newValue) => setBeta(newValue)}
                        min={0.01}
                        max={0.5}
                        step={0.01}
                        marks={[
                          { value: 0.01, label: '0.01' },
                          { value: 0.1, label: '0.1' },
                          { value: 0.5, label: '0.5' }
                        ]}
                        sx={{
                          color: '#9c27b0',
                          '& .MuiSlider-thumb': {
                            width: 24,
                            height: 24,
                            backgroundColor: '#fff',
                            border: '2px solid #9c27b0',
                            '&:focus, &:hover, &.Mui-active': {
                              boxShadow: '0 0 0 8px rgba(156, 39, 176, 0.16)',
                            },
                          },
                          '& .MuiSlider-valueLabel': {
                            backgroundColor: '#9c27b0',
                          },
                        }}
                      />
                    </Box>
                    
                    <TextField 
                      label="Beta Value"
                      type="number"
                      value={beta}
                      onChange={(e) => setBeta(parseFloat(e.target.value))}
                      inputProps={{ min: 0.01, max: 0.5, step: 0.01 }}
                      variant="outlined"
                      size="small"
                      fullWidth
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '&.Mui-focused fieldset': {
                            borderColor: '#9c27b0',
                          },
                        },
                        '& .MuiInputLabel-root.Mui-focused': {
                          color: '#9c27b0',
                        }
                      }}
                    />
                  </Box>
                </Grid>
              )}
            </Grid>
          </AccordionDetails>
        </Accordion>

        <Box sx={{ mb: 4, px: 2 }}>
          <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary', display: 'flex', alignItems: 'center' }}>
            <InfoIcon fontSize="small" sx={{ mr: 1, color: 'primary.main' }} />
            Your customized parameter values will be used when running the analysis. Adjust them to find the optimal core-periphery structure for your network.
          </Typography>
        </Box>

        <Typography variant="h6" sx={{ mb: 2, color: 'primary.dark' }}>
          Optional Metrics:
        </Typography>
        
        <Paper sx={{ p: 2, mb: 4, borderRadius: 2 }}>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            You can include additional centrality metrics in the analysis. Note that these calculations may increase processing time for large networks.
          </Typography>
          
          <FormGroup sx={{ display: 'flex', flexDirection: 'row' }}>
            <FormControlLabel
              control={
                <Checkbox 
                  checked={calculateCloseness}
                  onChange={(e) => setCalculateCloseness(e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="body2" sx={{ mr: 0.5 }}>Closeness Centrality</Typography>
                  <Tooltip title="Measures how close a node is to all other nodes in the network. Useful for identifying nodes that can quickly reach all others.">
                    <InfoIcon fontSize="small" color="action" />
                  </Tooltip>
                </Box>
              }
              sx={{ mr: 4 }}
            />
            
            <FormControlLabel
              control={
                <Checkbox 
                  checked={calculateBetweenness}
                  onChange={(e) => setCalculateBetweenness(e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="body2" sx={{ mr: 0.5 }}>Betweenness Centrality</Typography>
                  <Tooltip title="Measures how often a node lies on the shortest path between other nodes. Identifies nodes that control information flow in the network.">
                    <InfoIcon fontSize="small" color="action" />
                  </Tooltip>
                </Box>
              }
            />
          </FormGroup>
        </Paper>

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