import React from 'react';
import { 
  Box, 
  Card, 
  Typography, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper,
  Grow,
  Grid,
  Divider,
  Chip,
  Tooltip,
  LinearProgress
} from '@mui/material';
import { 
  BarChart, 
  Assessment, 
  Settings, 
  Info as InfoIcon, 
  Check as CheckIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Speed as SpeedIcon,
  Timeline
} from '@mui/icons-material';

const MetricsTable = ({ metrics }) => {
  if (!metrics) return null;

  const formatParameterName = (name) => {
    // Convert parameter names to more readable format
    const formattedNames = {
      'alpha': 'Alpha (α)',
      'beta': 'Beta (β)',
      'num_runs': 'Number of Runs',
      'threshold': 'Core Classification Threshold',
      'final_score': 'Quality Score (Q)',
      'execution_time': 'Execution Time (s)',
      'runs_planned': 'Planned Runs',
      'runs_completed': 'Completed Runs',
      'early_stops': 'Early Stops',
      'parallel': 'Parallel Execution',
      'algorithm': 'Algorithm Type',
      'respect_num_runs': 'Respect Num Runs'
    };
    
    return formattedNames[name] || name;
  };

  const formatParameterValue = (value) => {
    // Format values appropriately
    if (typeof value === 'number') {
      return Number.isInteger(value) ? value : value.toFixed(3);
    }
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    return value;
  };

  const getParameterDescription = (key) => {
    // Provide descriptions for each parameter
    // Determine if we're using the Rombach or Cucuringu algorithm
    const isRombach = metrics.algorithm_params?.alpha !== undefined;
    const isCucuringu = metrics.algorithm_params?.beta !== undefined && !metrics.algorithm_params?.alpha;
    
    const descriptions = {
      'alpha': 'Controls the sharpness of the core-periphery boundary in the Rombach algorithm. Higher values create a more defined boundary.',
      'beta': isRombach 
        ? 'Controls the fraction of peripheral nodes in the network partitioning.' 
        : isCucuringu 
        ? 'Controls the minimum boundary size for core detection, affecting how the algorithm partitions the network using spectral properties.' 
        : 'Controls network partitioning parameters.',
      'num_runs': 'Number of independent algorithm runs with different initializations. Higher values improve result consistency.',
      'threshold': 'Threshold for classifying nodes as core or periphery. Nodes with coreness above this value are classified as core.',
      'final_score': 'Quality score measuring how well the detected structure matches an ideal core-periphery pattern. Higher values indicate better match.',
      'runs_planned': 'The total number of algorithm runs that were planned.',
      'runs_completed': 'The actual number of algorithm runs that were completed.',
      'early_stops': 'The number of times the algorithm stopped early due to convergence.',
      'respect_num_runs': 'Whether the algorithm strictly respected the requested number of runs.'
    };
    
    return descriptions[key] || 'No description available';
  };

  const getAlgorithmName = (metrics) => {
    // Improved detection of algorithm type
    if (metrics.algorithm_stats?.algorithm === 'rombach') {
      return "Rombach Algorithm";
    } else if (metrics.algorithm_stats?.algorithm === 'be') {
      return "Borgatti & Everett (BE) Algorithm";
    } else if (metrics.algorithm_stats?.algorithm === 'cucuringu') {
      return "Cucuringu Algorithm (LowRankCore)";
    } else if (metrics.algorithm_params?.alpha !== undefined) {
      return "Rombach Algorithm";
    } else if (metrics.algorithm_params?.beta !== undefined && !metrics.algorithm_params?.alpha) {
      return "Cucuringu Algorithm (LowRankCore)";
    } else if (metrics.algorithm_params?.num_runs !== undefined && !metrics.algorithm_params?.alpha) {
      // Only BE has num_runs but no alpha
      return "Borgatti & Everett (BE) Algorithm";
    }
    
    // Additional fallback detection - if we have network_metrics, check structure quality
    if (metrics.network_metrics?.core_stats) {
      // Based on the presence of core stats, we can assume some algorithm was run
      // Default to Rombach as it's the most commonly used
      return "Core-Periphery Algorithm";
    }
    
    return "Core-Periphery Analysis";
  };

  const getAlgorithmDescription = (metrics) => {
    // First check algorithm_stats if available
    if (metrics.algorithm_stats?.algorithm === 'rombach') {
      return "A continuous core-periphery detection method that optimizes a quality function based on the density of connections. It allows for a more nuanced assignment of nodes to the core or periphery.";
    } else if (metrics.algorithm_stats?.algorithm === 'be') {
      return "A discrete core-periphery detection method based on correlation with an ideal core-periphery structure. This algorithm identifies a binary core/periphery structure.";
    } else if (metrics.algorithm_stats?.algorithm === 'cucuringu') {
      return "A spectral method for core-periphery detection using low-rank matrix approximation and eigendecomposition. This algorithm finds core-periphery structure by analyzing the network's spectral properties.";
    }
    
    // Fallback to checking params if algorithm_stats doesn't have the info
    if (metrics.algorithm_params?.alpha !== undefined) {
      return "A continuous core-periphery detection method that optimizes a quality function based on the density of connections. It allows for a more nuanced assignment of nodes to the core or periphery.";
    } else if (metrics.algorithm_params?.beta !== undefined && !metrics.algorithm_params?.alpha) {
      return "A spectral method for core-periphery detection using low-rank matrix approximation and eigendecomposition. This algorithm finds core-periphery structure by analyzing the network's spectral properties.";
    } else if (metrics.algorithm_params?.num_runs !== undefined && !metrics.algorithm_params?.alpha) {
      // Only BE has num_runs but no alpha
      return "A discrete core-periphery detection method based on correlation with an ideal core-periphery structure. This algorithm identifies a binary core/periphery structure.";
    }
    
    // Final fallback - generic description
    return "This algorithm detects core-periphery structure by dividing the network into densely connected core nodes and more sparsely connected peripheral nodes.";
  };

  const getAlgorithmReference = (metrics) => {
    // First check algorithm_stats if available
    if (metrics.algorithm_stats?.algorithm === 'rombach') {
      return "Reference: Rombach et al. (2017). \"Core-Periphery Structure in Networks.\"";
    } else if (metrics.algorithm_stats?.algorithm === 'be') {
      return "Reference: Borgatti & Everett (2000). \"Models of Core/Periphery Structures.\"";
    } else if (metrics.algorithm_stats?.algorithm === 'cucuringu') {
      return "Reference: Cucuringu et al. (2016). \"Detection of core-periphery structure in networks using spectral methods and geodesic paths.\"";
    }
    
    // Fallback to checking params
    if (metrics.algorithm_params?.alpha !== undefined) {
      return "Reference: Rombach et al. (2017). \"Core-Periphery Structure in Networks.\"";
    } else if (metrics.algorithm_params?.beta !== undefined && !metrics.algorithm_params?.alpha) {
      return "Reference: Cucuringu et al. (2016). \"Detection of core-periphery structure in networks using spectral methods and geodesic paths.\"";
    } else if (metrics.algorithm_params?.num_runs !== undefined && !metrics.algorithm_params?.alpha) {
      // Only BE has num_runs but no alpha
      return "Reference: Borgatti & Everett (2000). \"Models of Core/Periphery Structures.\"";
    }
    
    // Generic reference list if we can't determine the specific algorithm
    return "References: Borgatti & Everett (2000), Rombach et al. (2017), Cucuringu et al. (2016)";
  };

  const getAlgorithmParams = () => {
    const algorithm_stats = metrics.algorithm_stats || {};
    const algorithm_params = metrics.algorithm_params || {};
    
    // Combine algorithm stats with parameters
    const combinedParams = {
      ...algorithm_params,
      ...(algorithm_stats.final_score !== undefined ? { final_score: algorithm_stats.final_score } : {}),
      ...(algorithm_stats.execution_time !== undefined ? { execution_time: algorithm_stats.execution_time } : {}),
      ...(algorithm_stats.runs_planned !== undefined ? { runs_planned: algorithm_stats.runs_planned } : {}),
      ...(algorithm_stats.runs_completed !== undefined ? { runs_completed: algorithm_stats.runs_completed } : {}),
      ...(algorithm_stats.early_stops !== undefined ? { early_stops: algorithm_stats.early_stops } : {})
    };
    
    // If we don't have params, try to extract what we can from network_metrics
    if (Object.keys(combinedParams).length === 0 && metrics.network_metrics?.core_stats) {
      const coreStats = metrics.network_metrics.core_stats;
      // Add a fallback quality score if available
      if (coreStats.ideal_pattern_match !== undefined) {
        combinedParams.final_score = coreStats.ideal_pattern_match / 100;
      }
    }
    
    return combinedParams;
  };

  const getDisplayParameters = (params) => {
    // Prioritize showing these parameters in this order
    const priorityParams = [
      'final_score', 
      'alpha', 
      'beta', 
      'num_runs',
      'threshold',
      'execution_time',
      'runs_planned',
      'runs_completed',
      'early_stops'
    ];
    
    // Filter out parameters with undefined values
    const filteredParams = Object.entries(params)
      .filter(([_, value]) => value !== undefined)
      .reduce((obj, [key, value]) => {
        obj[key] = value;
        return obj;
      }, {});
    
    // Sort parameters by priority
    return Object.entries(filteredParams)
      .sort((a, b) => {
        const indexA = priorityParams.indexOf(a[0]);
        const indexB = priorityParams.indexOf(b[0]);
        
        if (indexA === -1 && indexB === -1) return 0;
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        
        return indexA - indexB;
      })
      .reduce((obj, [key, value]) => {
        obj[key] = value;
        return obj;
      }, {});
  };

  const getQualityInterpretation = (value) => {
    if (value >= 0.8) return 'Excellent';
    if (value >= 0.6) return 'Good';
    if (value >= 0.4) return 'Moderate';
    if (value >= 0.2) return 'Poor';
    return 'Very Poor';
  };

  const getQualityColor = (value) => {
    if (value >= 0.8) return '#4caf50';
    if (value >= 0.6) return '#8bc34a';
    if (value >= 0.4) return '#ffc107';
    if (value >= 0.2) return '#ff9800';
    return '#f44336';
  };

  const formatCoreness = (value) => {
    if (typeof value === 'number') {
      // Show a maximum of 3 decimal places
      return value.toFixed(Math.min(3, value.toString().split('.')[1]?.length || 0));
    }
    return value;
  };

  if (!metrics || !metrics.top_nodes) {
    return <Typography variant="body1">Loading metrics...</Typography>;
  }

  const params = getAlgorithmParams();
  const displayParams = getDisplayParameters(params);
  const algorithmName = getAlgorithmName(metrics);
  const qualityScore = metrics.algorithm_stats?.final_score;

  // Determine if centrality metrics are available for the node tables
  const hasCloseness = metrics.top_nodes.top_core_nodes.length > 0 && 
    metrics.top_nodes.top_core_nodes[0].hasOwnProperty('closeness') && 
    metrics.top_nodes.top_core_nodes[0].closeness > 0;
  const hasBetweenness = metrics.top_nodes.top_core_nodes.length > 0 && 
    metrics.top_nodes.top_core_nodes[0].hasOwnProperty('betweenness') && 
    metrics.top_nodes.top_core_nodes[0].betweenness > 0;

  // Get centrality metrics from the network_metrics object
  const hasCentralityMetrics = metrics.network_metrics?.centrality_metrics;
  const hasClosenessMetrics = hasCentralityMetrics && 
    metrics.network_metrics.centrality_metrics.avg_closeness !== undefined && 
    metrics.network_metrics.centrality_metrics.avg_closeness > 0;
  const hasBetweennessMetrics = hasCentralityMetrics && 
    metrics.network_metrics.centrality_metrics.avg_betweenness !== undefined && 
    metrics.network_metrics.centrality_metrics.avg_betweenness > 0;

  // Check if we have actual non-zero metrics to show
  const hasMeaningfulCloseness = hasClosenessMetrics;
  const hasMeaningfulBetweenness = hasBetweennessMetrics;
  const hasAnyCentralityMetrics = hasMeaningfulCloseness || hasMeaningfulBetweenness;
  
  // Add a function to create a color-coded quality score display
  const renderQualityScore = (score) => {
    const interpretation = getQualityInterpretation(score);
    const color = getQualityColor(score);
    
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
        <Typography variant="subtitle1" sx={{ mr: 2 }}>
          Quality Score (Q): 
        </Typography>
        <Box 
          sx={{ 
            bgcolor: `${color}20`, 
            color: color, 
            px: 2, 
            py: 1, 
            borderRadius: 2,
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          {score.toFixed(3)} 
          <Typography variant="body2" sx={{ ml: 1, fontStyle: 'italic' }}>
            ({interpretation})
          </Typography>
        </Box>
      </Box>
    );
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography 
          variant="h4" 
          sx={{ 
            background: 'linear-gradient(45deg, #1a237e, #0d47a1)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            color: 'transparent',
            fontWeight: 'bold'
          }}
        >
          Analysis Results
        </Typography>
      </Box>

      <Grow in={true} timeout={500}>
        <Card
          sx={{
            p: 3,
            background: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7))',
            backdropFilter: 'blur(10px)',
            transition: 'transform 0.2s ease-in-out',
            '&:hover': {
              transform: 'scale(1.01)',
            },
          }}
        >
          <Typography variant="h6" sx={{ mb: 2 }}>
            Algorithm Information
          </Typography>
          <Paper sx={{ p: 2, mb: 3, bgcolor: 'rgba(25, 118, 210, 0.08)', borderRadius: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
              {algorithmName}
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              {getAlgorithmDescription(metrics)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {getAlgorithmReference(metrics)}
            </Typography>
            
            {/* Add Quality Score display if available */}
            {qualityScore !== undefined && renderQualityScore(qualityScore)}
          </Paper>

          <Typography variant="h6" sx={{ mb: 2 }}>
            Understanding Core-Periphery Structure
          </Typography>
          <Paper sx={{ p: 2, mb: 3, bgcolor: 'rgba(76, 175, 80, 0.08)', borderRadius: 2 }}>
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2 }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  A core-periphery structure divides the network into two parts:
                </Typography>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  <li>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#d32f2f' }}>
                      Core nodes
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      Densely connected central nodes that form the backbone of the network. They typically have high degree and high coreness values.
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                      Periphery nodes
                    </Typography>
                    <Typography variant="body2">
                      Sparsely connected nodes that primarily connect to core nodes rather than to each other. They typically have lower degree and coreness values.
                    </Typography>
                  </li>
                </ul>
              </Box>
              <Box sx={{ 
                width: { xs: '100%', sm: '150px' }, 
                height: { xs: '150px', sm: '150px' },
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                position: 'relative'
              }}>
                {/* Simple visual representation of core-periphery */}
                <Box sx={{ 
                  width: 60, 
                  height: 60, 
                  bgcolor: 'rgba(211, 47, 47, 0.7)', 
                  borderRadius: '50%',
                  position: 'absolute',
                  zIndex: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontWeight: 'bold',
                  fontSize: '12px'
                }}>
                  CORE
                </Box>
                <Box sx={{ 
                  width: 130, 
                  height: 130, 
                  border: '2px dashed rgba(25, 118, 210, 0.7)', 
                  borderRadius: '50%',
                  position: 'absolute',
                  zIndex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Box sx={{ 
                    position: 'absolute', 
                    top: 15, 
                    right: 15, 
                    width: 20, 
                    height: 20, 
                    bgcolor: 'rgba(25, 118, 210, 0.7)', 
                    borderRadius: '50%' 
                  }} />
                  <Box sx={{ 
                    position: 'absolute', 
                    bottom: 20, 
                    left: 15, 
                    width: 20, 
                    height: 20, 
                    bgcolor: 'rgba(25, 118, 210, 0.7)', 
                    borderRadius: '50%' 
                  }} />
                  <Box sx={{ 
                    position: 'absolute', 
                    bottom: 30, 
                    right: 25, 
                    width: 20, 
                    height: 20, 
                    bgcolor: 'rgba(25, 118, 210, 0.7)', 
                    borderRadius: '50%' 
                  }} />
                  <Box sx={{ 
                    position: 'absolute', 
                    top: 30, 
                    left: 20, 
                    width: 20, 
                    height: 20, 
                    bgcolor: 'rgba(25, 118, 210, 0.7)', 
                    borderRadius: '50%' 
                  }} />
                </Box>
              </Box>
            </Box>
          </Paper>

          <Typography variant="h6" sx={{ mb: 2 }}>
            Algorithm Parameters
          </Typography>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            These parameters control how the core-periphery detection algorithm identifies and categorizes nodes. 
            Different settings can significantly affect the resulting structure.
          </Typography>
          <TableContainer component={Paper} sx={{ mb: 4, boxShadow: 'none' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Parameter</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Value</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Description</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {/* Algorithm Configuration Parameters */}
                {(displayParams.alpha !== undefined || 
                  displayParams.beta !== undefined || 
                  displayParams.num_runs !== undefined || 
                  displayParams.threshold !== undefined) && (
                  <TableRow>
                    <TableCell colSpan={3} sx={{ bgcolor: 'rgba(25, 118, 210, 0.05)', fontWeight: 'bold' }}>
                      Algorithm Configuration
                    </TableCell>
                  </TableRow>
                )}
                {displayParams.alpha !== undefined && (
                  <TableRow>
                    <TableCell>{formatParameterName('alpha')}</TableCell>
                    <TableCell>{formatParameterValue(displayParams.alpha)}</TableCell>
                    <TableCell>{getParameterDescription('alpha')}</TableCell>
                  </TableRow>
                )}
                {displayParams.beta !== undefined && (
                  <TableRow>
                    <TableCell>{formatParameterName('beta')}</TableCell>
                    <TableCell>{formatParameterValue(displayParams.beta)}</TableCell>
                    <TableCell>{getParameterDescription('beta')}</TableCell>
                  </TableRow>
                )}
                {displayParams.num_runs !== undefined && (
                  <TableRow>
                    <TableCell>{formatParameterName('num_runs')}</TableCell>
                    <TableCell>{formatParameterValue(displayParams.num_runs)}</TableCell>
                    <TableCell>{getParameterDescription('num_runs')}</TableCell>
                  </TableRow>
                )}
                {displayParams.threshold !== undefined && (
                  <TableRow>
                    <TableCell>{formatParameterName('threshold')}</TableCell>
                    <TableCell>{formatParameterValue(displayParams.threshold)}</TableCell>
                    <TableCell>{getParameterDescription('threshold')}</TableCell>
                  </TableRow>
                )}
                
                {/* Performance Metrics */}
                {(displayParams.execution_time !== undefined || 
                  displayParams.runs_planned !== undefined || 
                  displayParams.runs_completed !== undefined || 
                  displayParams.early_stops !== undefined) && (
                  <TableRow>
                    <TableCell colSpan={3} sx={{ bgcolor: 'rgba(76, 175, 80, 0.05)', fontWeight: 'bold' }}>
                      Performance Metrics
                    </TableCell>
                  </TableRow>
                )}
                {displayParams.execution_time !== undefined && (
                  <TableRow>
                    <TableCell>{formatParameterName('execution_time')}</TableCell>
                    <TableCell>{formatParameterValue(displayParams.execution_time)}</TableCell>
                    <TableCell>{getParameterDescription('execution_time')}</TableCell>
                  </TableRow>
                )}
                {displayParams.runs_planned !== undefined && (
                  <TableRow>
                    <TableCell>{formatParameterName('runs_planned')}</TableCell>
                    <TableCell>{formatParameterValue(displayParams.runs_planned)}</TableCell>
                    <TableCell>{getParameterDescription('runs_planned')}</TableCell>
                  </TableRow>
                )}
                {displayParams.runs_completed !== undefined && (
                  <TableRow>
                    <TableCell>{formatParameterName('runs_completed')}</TableCell>
                    <TableCell>{formatParameterValue(displayParams.runs_completed)}</TableCell>
                    <TableCell>{getParameterDescription('runs_completed')}</TableCell>
                  </TableRow>
                )}
                {displayParams.early_stops !== undefined && (
                  <TableRow>
                    <TableCell>{formatParameterName('early_stops')}</TableCell>
                    <TableCell>{formatParameterValue(displayParams.early_stops)}</TableCell>
                    <TableCell>{getParameterDescription('early_stops')}</TableCell>
                  </TableRow>
                )}
                
                {/* Other Parameters */}
                {Object.entries(displayParams)
                  .filter(([key]) => !['alpha', 'beta', 'num_runs', 'threshold', 
                                      'execution_time', 'runs_planned', 'runs_completed', 
                                      'early_stops', 'final_score'].includes(key))
                  .length > 0 && (
                  <TableRow>
                    <TableCell colSpan={3} sx={{ bgcolor: 'rgba(211, 47, 47, 0.05)', fontWeight: 'bold' }}>
                      Additional Settings
                    </TableCell>
                  </TableRow>
                )}
                {Object.entries(displayParams)
                  .filter(([key]) => !['alpha', 'beta', 'num_runs', 'threshold', 
                                      'execution_time', 'runs_planned', 'runs_completed', 
                                      'early_stops', 'final_score'].includes(key))
                  .map(([key, value]) => (
                    <TableRow key={key}>
                      <TableCell>{formatParameterName(key)}</TableCell>
                      <TableCell>{formatParameterValue(value)}</TableCell>
                      <TableCell>{getParameterDescription(key)}</TableCell>
                    </TableRow>
                  ))
                }
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mb: 2, mt: 4 }}>
            Top Nodes by Coreness and Peripheriness
          </Typography>
          
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {/* Core Nodes Panel */}
            <Grid item xs={12} md={6}>
              <Paper 
                sx={{ 
                  p: 2, 
                  borderRadius: 2,
                  border: '1px solid rgba(211, 47, 47, 0.2)',
                  boxShadow: '0 4px 12px rgba(211, 47, 47, 0.08)',
                  height: '100%',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                <Box 
                  sx={{ 
                    position: 'absolute', 
                    top: 0, 
                    right: 0, 
                    width: '30%', 
                    height: '100%',
                    background: 'linear-gradient(90deg, rgba(211, 47, 47, 0) 0%, rgba(211, 47, 47, 0.05) 100%)',
                    zIndex: 0
                  }}
                />
                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box 
                      sx={{ 
                        width: 16, 
                        height: 16, 
                        borderRadius: '50%', 
                        bgcolor: '#d32f2f',
                        mr: 1
                      }} 
                    />
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#d32f2f' }}>
                      Top Core Nodes
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
                    Core nodes have the highest coreness values and are central to the network structure.
                  </Typography>
                  
                  <TableContainer sx={{ boxShadow: 'none' }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 'bold', width: '30%' }}>Node ID</TableCell>
                          <TableCell sx={{ fontWeight: 'bold', width: '15%' }}>Type</TableCell>
                          <TableCell sx={{ fontWeight: 'bold', width: '30%' }}>Coreness</TableCell>
                          <TableCell sx={{ fontWeight: 'bold', width: '25%' }}>Degree</TableCell>
                          {hasCloseness && (
                            <TableCell sx={{ fontWeight: 'bold' }}>Closeness</TableCell>
                          )}
                          {hasBetweenness && (
                            <TableCell sx={{ fontWeight: 'bold' }}>Betweenness</TableCell>
                          )}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {metrics.top_nodes && metrics.top_nodes.top_core_nodes && metrics.top_nodes.top_core_nodes.map((node, index) => {
                          const corenessValue = node.coreness !== undefined ? node.coreness : 0;
                          const maxCoreness = metrics.top_nodes.top_core_nodes[0]?.coreness || 1;
                          const relativeCoreness = corenessValue / maxCoreness;
                          
                          return (
                            <TableRow 
                              key={node.id}
                              sx={{ 
                                '&:nth-of-type(odd)': { bgcolor: 'rgba(211, 47, 47, 0.04)' },
                                '&:hover': { bgcolor: 'rgba(211, 47, 47, 0.1)' },
                                fontWeight: index === 0 ? 'bold' : 'normal'
                              }}
                            >
                              <TableCell>{node.id}</TableCell>
                              <TableCell>
                                <Box 
                                  sx={{ 
                                    display: 'inline-block',
                                    bgcolor: 'rgba(211, 47, 47, 0.1)', 
                                    color: '#d32f2f',
                                    p: '3px 8px',
                                    borderRadius: '10px',
                                    fontSize: '0.75rem',
                                    fontWeight: 'bold'
                                  }}
                                >
                                  {node.type}
                                </Box>
                              </TableCell>
                              <TableCell>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                  <Box sx={{ width: '100%', mr: 1 }}>
                                    <Box
                                      sx={{
                                        width: `${relativeCoreness * 100}%`,
                                        height: 6,
                                        bgcolor: 'rgba(211, 47, 47, 0.7)',
                                        borderRadius: 1,
                                      }}
                                    />
                                  </Box>
                                  <Box sx={{ minWidth: 35 }}>
                                    {node.coreness !== undefined ? node.coreness.toFixed(3) : 'N/A'}
                                  </Box>
                                </Box>
                              </TableCell>
                              <TableCell>{node.degree}</TableCell>
                              {hasCloseness && node.closeness !== undefined && node.closeness > 0 && (
                                <TableCell>{node.closeness.toFixed(4)}</TableCell>
                              )}
                              {hasBetweenness && node.betweenness !== undefined && node.betweenness > 0 && (
                                <TableCell>{node.betweenness.toFixed(4)}</TableCell>
                              )}
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              </Paper>
            </Grid>
            
            {/* Periphery Nodes Panel */}
            <Grid item xs={12} md={6}>
              <Paper 
                sx={{ 
                  p: 2, 
                  borderRadius: 2,
                  border: '1px solid rgba(25, 118, 210, 0.2)',
                  boxShadow: '0 4px 12px rgba(25, 118, 210, 0.08)',
                  height: '100%',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                <Box 
                  sx={{ 
                    position: 'absolute', 
                    top: 0, 
                    right: 0, 
                    width: '30%', 
                    height: '100%',
                    background: 'linear-gradient(90deg, rgba(25, 118, 210, 0) 0%, rgba(25, 118, 210, 0.05) 100%)',
                    zIndex: 0
                  }}
                />
                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box 
                      sx={{ 
                        width: 16, 
                        height: 16, 
                        borderRadius: '50%', 
                        bgcolor: '#1976d2',
                        mr: 1
                      }} 
                    />
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                      Top Periphery Nodes
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
                    Periphery nodes have the lowest coreness values and are situated at the edge of the network.
                  </Typography>
                  
                  <TableContainer sx={{ boxShadow: 'none' }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 'bold', width: '30%' }}>Node ID</TableCell>
                          <TableCell sx={{ fontWeight: 'bold', width: '15%' }}>Type</TableCell>
                          <TableCell sx={{ fontWeight: 'bold', width: '30%' }}>Coreness</TableCell>
                          <TableCell sx={{ fontWeight: 'bold', width: '25%' }}>Degree</TableCell>
                          {hasCloseness && (
                            <TableCell sx={{ fontWeight: 'bold' }}>Closeness</TableCell>
                          )}
                          {hasBetweenness && (
                            <TableCell sx={{ fontWeight: 'bold' }}>Betweenness</TableCell>
                          )}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {metrics.top_nodes && metrics.top_nodes.top_periphery_nodes && metrics.top_nodes.top_periphery_nodes.map((node, index) => {
                          const corenessValue = node.coreness !== undefined ? node.coreness : 0;
                          const minCoreness = metrics.top_nodes.top_periphery_nodes[0]?.coreness || 0;
                          const maxCoreness = metrics.top_nodes.top_periphery_nodes[metrics.top_nodes.top_periphery_nodes.length - 1]?.coreness || 1;
                          const range = maxCoreness - minCoreness;
                          const relativeCoreness = range > 0 ? (corenessValue - minCoreness) / range : 0;
                          
                          return (
                            <TableRow 
                              key={node.id}
                              sx={{ 
                                '&:nth-of-type(odd)': { bgcolor: 'rgba(25, 118, 210, 0.04)' },
                                '&:hover': { bgcolor: 'rgba(25, 118, 210, 0.1)' },
                                fontWeight: index === 0 ? 'bold' : 'normal'
                              }}
                            >
                              <TableCell>{node.id}</TableCell>
                              <TableCell>
                                <Box 
                                  sx={{ 
                                    display: 'inline-block',
                                    bgcolor: 'rgba(25, 118, 210, 0.1)', 
                                    color: '#1976d2',
                                    p: '3px 8px',
                                    borderRadius: '10px',
                                    fontSize: '0.75rem',
                                    fontWeight: 'bold'
                                  }}
                                >
                                  {node.type}
                                </Box>
                              </TableCell>
                              <TableCell>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                  <Box sx={{ width: '100%', mr: 1 }}>
                                    <Box
                                      sx={{
                                        width: `${relativeCoreness * 100}%`,
                                        height: 6,
                                        bgcolor: 'rgba(25, 118, 210, 0.7)',
                                        borderRadius: 1,
                                      }}
                                    />
                                  </Box>
                                  <Box sx={{ minWidth: 35 }}>
                                    {node.coreness !== undefined ? node.coreness.toFixed(3) : 'N/A'}
                                  </Box>
                                </Box>
                              </TableCell>
                              <TableCell>{node.degree}</TableCell>
                              {hasCloseness && node.closeness !== undefined && node.closeness > 0 && (
                                <TableCell>{node.closeness.toFixed(4)}</TableCell>
                              )}
                              {hasBetweenness && node.betweenness !== undefined && node.betweenness > 0 && (
                                <TableCell>{node.betweenness.toFixed(4)}</TableCell>
                              )}
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              </Paper>
            </Grid>
          </Grid>

          {/* Add Centrality Metrics Section if metrics include centrality data */}
          {hasAnyCentralityMetrics && (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
                <Timeline sx={{ mr: 1, color: 'primary.main' }} />
                Centrality Metrics
              </Typography>
              
              <Grid container spacing={3}>
                {hasClosenessMetrics && (
                  <Grid item xs={12} md={6}>
                    <Paper 
                      elevation={1} 
                      sx={{ 
                        p: 3, 
                        borderRadius: 2,
                        border: '1px solid rgba(76, 175, 80, 0.2)',
                        boxShadow: '0 4px 12px rgba(76, 175, 80, 0.08)',
                        height: '100%'
                      }}
                    >
                      <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: '#4caf50' }}>
                        Closeness Centrality
                      </Typography>
                      
                      <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
                        Measures how close a node is to all other nodes in the network. Higher values indicate nodes that can quickly reach all others.
                      </Typography>
                      
                      <Box sx={{ mb: 3 }}>
                        <Grid container spacing={2}>
                          {metrics.network_metrics.centrality_metrics.avg_closeness > 0 && (
                            <Grid item xs={6}>
                              <Typography variant="body2" sx={{ color: 'text.secondary' }}>Average Closeness:</Typography>
                              <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                                {metrics.network_metrics.centrality_metrics.avg_closeness.toFixed(4)}
                              </Typography>
                            </Grid>
                          )}
                          {metrics.network_metrics.centrality_metrics.max_closeness > 0 && (
                            <Grid item xs={6}>
                              <Typography variant="body2" sx={{ color: 'text.secondary' }}>Max Closeness:</Typography>
                              <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                                {metrics.network_metrics.centrality_metrics.max_closeness.toFixed(4)}
                              </Typography>
                            </Grid>
                          )}
                        </Grid>
                      </Box>
                      
                      {/* Only show comparison if either value is non-zero */}
                      {(metrics.network_metrics.centrality_metrics.avg_core_closeness > 0 || 
                        metrics.network_metrics.centrality_metrics.avg_periphery_closeness > 0) && (
                        <>
                          <Typography variant="body2" sx={{ fontWeight: 'medium', mb: 1 }}>Core vs. Periphery Comparison:</Typography>
                          <Grid container spacing={2}>
                            {metrics.network_metrics.centrality_metrics.avg_core_closeness > 0 && (
                              <Grid item xs={6}>
                                <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                                  <Typography variant="body2" sx={{ color: '#d32f2f', fontWeight: 'medium' }}>Core Nodes:</Typography>
                                  <Typography variant="body1">
                                    {metrics.network_metrics.centrality_metrics.avg_core_closeness.toFixed(4)}
                                  </Typography>
                                </Box>
                              </Grid>
                            )}
                            {metrics.network_metrics.centrality_metrics.avg_periphery_closeness > 0 && (
                              <Grid item xs={6}>
                                <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                                  <Typography variant="body2" sx={{ color: '#0288d1', fontWeight: 'medium' }}>Periphery Nodes:</Typography>
                                  <Typography variant="body1">
                                    {metrics.network_metrics.centrality_metrics.avg_periphery_closeness.toFixed(4)}
                                  </Typography>
                                </Box>
                              </Grid>
                            )}
                          </Grid>
                        </>
                      )}
                    </Paper>
                  </Grid>
                )}
                
                {hasBetweennessMetrics && (
                  <Grid item xs={12} md={6}>
                    <Paper 
                      elevation={1} 
                      sx={{ 
                        p: 3, 
                        borderRadius: 2,
                        border: '1px solid rgba(103, 58, 183, 0.2)',
                        boxShadow: '0 4px 12px rgba(103, 58, 183, 0.08)',
                        height: '100%'
                      }}
                    >
                      <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: '#673ab7' }}>
                        Betweenness Centrality
                      </Typography>
                      
                      <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
                        Measures how often a node lies on the shortest path between other nodes. Identifies nodes that control information flow.
                      </Typography>
                      
                      <Box sx={{ mb: 3 }}>
                        <Grid container spacing={2}>
                          {metrics.network_metrics.centrality_metrics.avg_betweenness > 0 && (
                            <Grid item xs={6}>
                              <Typography variant="body2" sx={{ color: 'text.secondary' }}>Average Betweenness:</Typography>
                              <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                                {metrics.network_metrics.centrality_metrics.avg_betweenness.toFixed(4)}
                              </Typography>
                            </Grid>
                          )}
                          {metrics.network_metrics.centrality_metrics.max_betweenness > 0 && (
                            <Grid item xs={6}>
                              <Typography variant="body2" sx={{ color: 'text.secondary' }}>Max Betweenness:</Typography>
                              <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                                {metrics.network_metrics.centrality_metrics.max_betweenness.toFixed(4)}
                              </Typography>
                            </Grid>
                          )}
                        </Grid>
                      </Box>
                      
                      {/* Only show comparison if either value is non-zero */}
                      {(metrics.network_metrics.centrality_metrics.avg_core_betweenness > 0 || 
                        metrics.network_metrics.centrality_metrics.avg_periphery_betweenness > 0) && (
                        <>
                          <Typography variant="body2" sx={{ fontWeight: 'medium', mb: 1 }}>Core vs. Periphery Comparison:</Typography>
                          <Grid container spacing={2}>
                            {metrics.network_metrics.centrality_metrics.avg_core_betweenness > 0 && (
                              <Grid item xs={6}>
                                <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                                  <Typography variant="body2" sx={{ color: '#d32f2f', fontWeight: 'medium' }}>Core Nodes:</Typography>
                                  <Typography variant="body1">
                                    {metrics.network_metrics.centrality_metrics.avg_core_betweenness.toFixed(4)}
                                  </Typography>
                                </Box>
                              </Grid>
                            )}
                            {metrics.network_metrics.centrality_metrics.avg_periphery_betweenness > 0 && (
                              <Grid item xs={6}>
                                <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                                  <Typography variant="body2" sx={{ color: '#0288d1', fontWeight: 'medium' }}>Periphery Nodes:</Typography>
                                  <Typography variant="body1">
                                    {metrics.network_metrics.centrality_metrics.avg_periphery_betweenness.toFixed(4)}
                                  </Typography>
                                </Box>
                              </Grid>
                            )}
                          </Grid>
                        </>
                      )}
                    </Paper>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </Card>
      </Grow>
    </Box>
  );
};

export default MetricsTable; 