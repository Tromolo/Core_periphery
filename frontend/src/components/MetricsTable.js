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
    const formattedNames = {
      'alpha': 'Alpha (α)',
      'beta': 'Beta (β)',
      'num_runs': 'Number of Runs',
      'threshold': 'Core Classification Threshold',
      'execution_time': 'Execution Time (s)',
      'runs_completed': 'Completed Runs',
      'early_stops': 'Early Stops',
      'parallel': 'Parallel Execution',
      'algorithm': 'Algorithm Type',
      'respect_num_runs': 'Respect Num Runs'
    };
    
    return formattedNames[name] || name;
  };

  const formatParameterValue = (value) => {
    if (typeof value === 'number') {
      return Number.isInteger(value) ? value : value.toFixed(3);
    }
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    return value;
  };

  const getParameterDescription = (key) => {
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
      'runs_planned': 'The total number of algorithm runs that were planned.',
      'runs_completed': 'The actual number of algorithm runs that were completed.',
      'early_stops': 'The number of times the algorithm stopped early due to convergence.',
      'respect_num_runs': 'Whether the algorithm strictly respected the requested number of runs.'
    };
    
    return descriptions[key] || 'No description available';
  };

  const getAlgorithmName = (metrics) => {
    if (metrics.algorithm_stats?.algorithm === 'rombach') {
      return "Rombach Algorithm";
    } else if (metrics.algorithm_stats?.algorithm === 'be') {
      return "Borgatti & Everett (BE) Algorithm";
    } else if (metrics.algorithm_stats?.algorithm === 'cucuringu') {
      return "Cucuringu Algorithm (LowRankCore)";
    } 
    
    else if (metrics.network_metrics?.rombach_params) {
      return "Rombach Algorithm";
    } else if (metrics.network_metrics?.be_params) {
      return "Borgatti & Everett (BE) Algorithm";
    } else if (metrics.network_metrics?.cucuringu_params) {
      return "Cucuringu Algorithm (LowRankCore)";
    } 
    
    else if (metrics.algorithm_params?.alpha !== undefined) {
      return "Rombach Algorithm";
    } else if (metrics.algorithm_params?.beta !== undefined && !metrics.algorithm_params?.alpha) {
      return "Cucuringu Algorithm (LowRankCore)";
    } else if (metrics.algorithm_params?.num_runs !== undefined && !metrics.algorithm_params?.alpha) {
      return "Borgatti & Everett (BE) Algorithm";
    }
    
    if (metrics.network_metrics?.core_stats) {
      return "Core-Periphery Algorithm";
    }
    
    return "Core-Periphery Analysis";
  };

  const getAlgorithmDescription = (metrics) => {
    if (metrics.algorithm_stats?.algorithm === 'rombach') {
      return "A continuous core-periphery detection method that optimizes a quality function based on the density of connections. It allows for a more nuanced assignment of nodes to the core or periphery.";
    } else if (metrics.algorithm_stats?.algorithm === 'be') {
      return "A discrete core-periphery detection method based on correlation with an ideal core-periphery structure. This algorithm identifies a binary core/periphery structure.";
    } else if (metrics.algorithm_stats?.algorithm === 'cucuringu') {
      return "A spectral method for core-periphery detection using low-rank matrix approximation and eigendecomposition. This algorithm finds core-periphery structure by analyzing the network's spectral properties.";
    }
    
    else if (metrics.network_metrics?.rombach_params) {
      return "A continuous core-periphery detection method that optimizes a quality function based on the density of connections. It allows for a more nuanced assignment of nodes to the core or periphery.";
    } else if (metrics.network_metrics?.be_params) {
      return "A discrete core-periphery detection method based on correlation with an ideal core-periphery structure. This algorithm identifies a binary core/periphery structure.";
    } else if (metrics.network_metrics?.cucuringu_params) {
      return "A spectral method for core-periphery detection using low-rank matrix approximation and eigendecomposition. This algorithm finds core-periphery structure by analyzing the network's spectral properties.";
    }
    
    else if (metrics.algorithm_params?.alpha !== undefined) {
      return "A continuous core-periphery detection method that optimizes a quality function based on the density of connections. It allows for a more nuanced assignment of nodes to the core or periphery.";
    } else if (metrics.algorithm_params?.beta !== undefined && !metrics.algorithm_params?.alpha) {
      return "A spectral method for core-periphery detection using low-rank matrix approximation and eigendecomposition. This algorithm finds core-periphery structure by analyzing the network's spectral properties.";
    } else if (metrics.algorithm_params?.num_runs !== undefined && !metrics.algorithm_params?.alpha) {
      return "A discrete core-periphery detection method based on correlation with an ideal core-periphery structure. This algorithm identifies a binary core/periphery structure.";
    }
    
    return "This algorithm detects core-periphery structure by dividing the network into densely connected core nodes and more sparsely connected peripheral nodes.";
  };

  const getAlgorithmReference = (metrics) => {
    if (metrics.algorithm_stats?.algorithm === 'rombach') {
      return "Reference: Rombach et al. (2017). \"Core-Periphery Structure in Networks.\"";
    } else if (metrics.algorithm_stats?.algorithm === 'be') {
      return "Reference: Borgatti & Everett (2000). \"Models of Core/Periphery Structures.\"";
    } else if (metrics.algorithm_stats?.algorithm === 'cucuringu') {
      return "Reference: Cucuringu et al. (2016). \"Detection of core-periphery structure in networks using spectral methods and geodesic paths.\"";
    }
    
    else if (metrics.network_metrics?.rombach_params) {
      return "Reference: Rombach et al. (2017). \"Core-Periphery Structure in Networks.\"";
    } else if (metrics.network_metrics?.be_params) {
      return "Reference: Borgatti & Everett (2000). \"Models of Core/Periphery Structures.\"";
    } else if (metrics.network_metrics?.cucuringu_params) {
      return "Reference: Cucuringu et al. (2016). \"Detection of core-periphery structure in networks using spectral methods and geodesic paths.\"";
    }
    
    else if (metrics.algorithm_params?.alpha !== undefined) {
      return "Reference: Rombach et al. (2017). \"Core-Periphery Structure in Networks.\"";
    } else if (metrics.algorithm_params?.beta !== undefined && !metrics.algorithm_params?.alpha) {
      return "Reference: Cucuringu et al. (2016). \"Detection of core-periphery structure in networks using spectral methods and geodesic paths.\"";
    } else if (metrics.algorithm_params?.num_runs !== undefined && !metrics.algorithm_params?.alpha) {
      return "Reference: Borgatti & Everett (2000). \"Models of Core/Periphery Structures.\"";
    }
    
    return "References: Borgatti & Everett (2000), Rombach et al. (2017), Cucuringu et al. (2016)";
  };

  const getAlgorithmParams = () => {
    const algorithm_stats = metrics.algorithm_stats || {};
    
    let algorithmParams = {};
    
    if (metrics.network_metrics?.rombach_params) {
      algorithmParams = {
        ...metrics.network_metrics.rombach_params,
        alpha: metrics.network_metrics.rombach_params.alpha,
        beta: metrics.network_metrics.rombach_params.beta,
        num_runs: metrics.network_metrics.rombach_params.num_runs,
        final_score: metrics.network_metrics.rombach_params.Q
      };
      delete algorithmParams.Q;
    } else if (metrics.network_metrics?.cucuringu_params) {
      algorithmParams = {
        ...metrics.network_metrics.cucuringu_params,
        beta: metrics.network_metrics.cucuringu_params.beta,
        final_score: metrics.network_metrics.cucuringu_params.Q
      };
      delete algorithmParams.Q;
    } else if (metrics.network_metrics?.be_params) {
      algorithmParams = {
        ...metrics.network_metrics.be_params,
        num_runs: metrics.network_metrics.be_params.num_runs,
        final_score: metrics.network_metrics.be_params.Q
      };
      delete algorithmParams.Q;
    }
    
    const algorithm_params = metrics.algorithm_params || {};
    
    const combinedParams = {
      ...algorithm_params,
      ...algorithmParams,
      ...(algorithm_stats.final_score !== undefined ? { final_score: algorithm_stats.final_score } : {}),
      ...(algorithm_stats.execution_time !== undefined ? { execution_time: algorithm_stats.execution_time } : {}),
      ...(algorithm_stats.runs_completed !== undefined ? { runs_completed: algorithm_stats.runs_completed } : {}),
      ...(algorithm_stats.early_stops !== undefined ? { early_stops: algorithm_stats.early_stops } : {})
    };
    
    delete combinedParams.Q;
    
    if (Object.keys(combinedParams).length === 0 && metrics.network_metrics?.core_stats) {
      const coreStats = metrics.network_metrics.core_stats;
      if (coreStats.ideal_pattern_match !== undefined) {
        combinedParams.final_score = coreStats.ideal_pattern_match / 100;
      }
    }
    
    return combinedParams;
  };

  const getDisplayParameters = (params) => {
    const priorityParams = [
      'final_score', 
      'alpha', 
      'beta', 
      'num_runs',
      'runs_planned',
      'runs_completed',
      'early_stops'
    ];
    
    const filteredParams = Object.entries(params)
      .filter(([_, value]) => value !== undefined)
      .reduce((obj, [key, value]) => {
        obj[key] = value;
        return obj;
      }, {});
    
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
  
  const hasCloseness = metrics.top_nodes.top_core_nodes.length > 0 && 
    metrics.top_nodes.top_core_nodes[0].hasOwnProperty('closeness') && 
    metrics.top_nodes.top_core_nodes[0].closeness > 0;
  const hasBetweenness = metrics.top_nodes.top_core_nodes.length > 0 && 
    metrics.top_nodes.top_core_nodes[0].hasOwnProperty('betweenness') && 
    metrics.top_nodes.top_core_nodes[0].betweenness > 0;

  const hasCentralityMetrics = metrics.network_metrics?.centrality_metrics;
  const hasClosenessMetrics = hasCentralityMetrics && 
    metrics.network_metrics.centrality_metrics.avg_closeness !== undefined && 
    metrics.network_metrics.centrality_metrics.avg_closeness > 0;
  const hasBetweennessMetrics = hasCentralityMetrics && 
    metrics.network_metrics.centrality_metrics.avg_betweenness !== undefined && 
    metrics.network_metrics.centrality_metrics.avg_betweenness > 0;

  const hasMeaningfulCloseness = hasClosenessMetrics;
  const hasMeaningfulBetweenness = hasBetweennessMetrics;
  const hasAnyCentralityMetrics = hasMeaningfulCloseness || hasMeaningfulBetweenness;
  
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
          
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {Object.entries(displayParams).map(([key, value]) => {
              if (key === 'execution_time') return null;
              
              if (key === 'Q') return null;
              
              if (key === 'final_score') return null;
              
              let icon;
              let color;
              let bgColor;
              let borderColor;
              
              if (key === 'alpha') {
                icon = <Settings sx={{ fontSize: 24 }} />;
                color = '#e91e63';
                bgColor = 'rgba(233, 30, 99, 0.08)';
                borderColor = 'rgba(233, 30, 99, 0.2)';
              } else if (key === 'beta') {
                icon = <Timeline sx={{ fontSize: 24 }} />;
                color = '#9c27b0';
                bgColor = 'rgba(156, 39, 176, 0.08)';
                borderColor = 'rgba(156, 39, 176, 0.2)';
              } else if (key === 'num_runs' || key === 'runs_planned') {
                icon = <Assessment sx={{ fontSize: 24 }} />;
                color = '#2196f3';
                bgColor = 'rgba(33, 150, 243, 0.08)';
                borderColor = 'rgba(33, 150, 243, 0.2)';
              } else if (key === 'runs_completed') {
                icon = <CheckIcon sx={{ fontSize: 24 }} />;
                color = '#4caf50';
                bgColor = 'rgba(76, 175, 80, 0.08)';
                borderColor = 'rgba(76, 175, 80, 0.2)';
              } else if (key === 'early_stops') {
                icon = <SpeedIcon sx={{ fontSize: 24 }} />;
                color = '#ff9800';
                bgColor = 'rgba(255, 152, 0, 0.08)';
                borderColor = 'rgba(255, 152, 0, 0.2)';
              } 
                else if (key === 'threshold') {
                icon = <BarChart sx={{ fontSize: 24 }} />;
                color = '#673ab7';
                bgColor = 'rgba(103, 58, 183, 0.08)';
                borderColor = 'rgba(103, 58, 183, 0.2)';
              } else {
                icon = <InfoIcon sx={{ fontSize: 24 }} />;
                color = '#607d8b';
                bgColor = 'rgba(96, 125, 139, 0.08)';
                borderColor = 'rgba(96, 125, 139, 0.2)';
              }
              
              return (
                <Grid item xs={12} sm={6} md={4} key={key}>
                  <Paper 
                    elevation={0} 
                    sx={{ 
                      p: 2, 
                      height: '100%',
                      border: `1px solid ${borderColor}`,
                      borderRadius: 2,
                      bgcolor: bgColor,
                      transition: 'transform 0.2s',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: `0 6px 12px ${borderColor}`
                      }
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Box sx={{ color: color, mr: 1.5 }}>
                        {icon}
                      </Box>
                      <Tooltip title={getParameterDescription(key)}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'medium', color: color }}>
                          {formatParameterName(key)}
                        </Typography>
                      </Tooltip>
                    </Box>
                    
                    {key === 'final_score' ? (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="h5" sx={{ fontWeight: 'bold', color }}>
                          {formatParameterValue(value)}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                          <Box sx={{ width: '100%', mr: 1 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={Math.min(value * 100, 100)} 
                              sx={{ 
                                height: 8, 
                                borderRadius: 4,
                                bgcolor: `${color}30`,
                                '& .MuiLinearProgress-bar': {
                                  bgcolor: color,
                                  borderRadius: 4,
                                }
                              }}
                            />
                          </Box>
                        </Box>
                      </Box>
                    ) : (
                      <Box>
                        <Typography variant="h5" sx={{ fontWeight: 'bold', color }}>
                          {formatParameterValue(value)}
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                          {key === 'alpha' && 'Boundary Sharpness'}
                          {key === 'beta' && 'Network Partitioning'}
                          {key === 'num_runs' && 'Initialization Count'}
                          {key === 'runs_planned' && 'Planned Runs'}
                          {key === 'runs_completed' && 'Completed Runs'}
                          {key === 'early_stops' && 'Early Convergence'}
                          {key === 'threshold' && 'Core Threshold Value'}
                        </Typography>
                      </Box>
                    )}
                  </Paper>
                </Grid>
              );
            })}
          </Grid>

          <Typography variant="h6" sx={{ mb: 2, mt: 4 }}>
            Top Nodes by Coreness and Peripheriness
          </Typography>
          
          <Grid container spacing={3} sx={{ mb: 4 }}>
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