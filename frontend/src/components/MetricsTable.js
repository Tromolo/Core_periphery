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
  Grid
} from '@mui/material';

const MetricsTable = ({ metrics }) => {
  if (!metrics) return null;

  const formatParameterName = (name) => {
    // Convert parameter names to more readable format
    const formattedNames = {
      'alpha': 'Alpha (α)',
      'beta': 'Beta (β)',
      'num_runs': 'Number of Runs',
      'num_iterations': 'Number of Iterations', 
      'threshold': 'Convergence Threshold'
    };
    
    return formattedNames[name] || name;
  };

  const formatParameterValue = (value) => {
    // Format values appropriately
    if (typeof value === 'number') {
      return Number.isInteger(value) ? value : value.toFixed(3);
    }
    return value;
  };

  const getParameterDescription = (key) => {
    // Provide descriptions for each parameter
    const descriptions = {
      'alpha': 'Controls the relative importance of core-to-core connections. Higher values prioritize dense connections within the core.',
      'beta': 'Controls the relative importance of core-to-periphery connections. Higher values emphasize connections between core and periphery nodes.',
      'num_runs': 'Number of independent algorithm runs with different initializations. Higher values improve result consistency.',
      'num_iterations': 'Maximum number of iterations for the optimization process. More iterations may improve accuracy at the cost of computation time.',
      'threshold': 'Convergence threshold determining when the algorithm stops. Lower values yield more precise results but require more iterations.'
    };
    
    return descriptions[key] || 'No description available';
  };

  const getAlgorithmName = (metrics) => {
    if (metrics.algorithm_params?.alpha !== undefined) {
      return "Rombach Algorithm";
    } else if (metrics.algorithm_params?.num_iterations !== undefined) {
      return "Holme Algorithm";
    } else if (metrics.algorithm_params?.num_runs !== undefined) {
      // Only BE has num_runs but no alpha or num_iterations
      return "Borgatti & Everett (BE) Algorithm";
    }
    return "Unknown Algorithm";
  };

  const getAlgorithmDescription = (metrics) => {
    if (metrics.algorithm_params?.alpha !== undefined) {
      return "A continuous core-periphery detection method that optimizes a quality function based on the density of connections. It allows for a more nuanced assignment of nodes to the core or periphery.";
    } else if (metrics.algorithm_params?.num_iterations !== undefined) {
      return "An iterative method that optimizes a core-coefficient quality function through node swapping. This algorithm focuses on finding a structure that maximizes connections within the core and between core and periphery.";
    } else if (metrics.algorithm_params?.num_runs !== undefined) {
      // Only BE has num_runs but no alpha or num_iterations
      return "A discrete core-periphery detection method based on correlation with an ideal core-periphery structure. This algorithm identifies a binary core/periphery structure.";
    }
    return "No description available for this algorithm.";
  };

  const getAlgorithmReference = (metrics) => {
    if (metrics.algorithm_params?.alpha !== undefined) {
      return "Reference: Rombach et al. (2017). \"Core-Periphery Structure in Networks.\"";
    } else if (metrics.algorithm_params?.num_iterations !== undefined) {
      return "Reference: Holme (2005). \"Core-periphery organization of complex networks.\"";
    } else if (metrics.algorithm_params?.num_runs !== undefined) {
      // Only BE has num_runs but no alpha or num_iterations
      return "Reference: Borgatti & Everett (2000). \"Models of Core/Periphery Structures.\"";
    }
    return "";
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
              {getAlgorithmName(metrics)}
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
                {metrics.algorithm_params && Object.entries(metrics.algorithm_params).map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell>{formatParameterName(key)}</TableCell>
                    <TableCell>{formatParameterValue(value)}</TableCell>
                    <TableCell>{getParameterDescription(key)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mb: 2, mt: 4 }}>
            Top Nodes by Coreness and Peripheriness
          </Typography>
          
          <Grid container spacing={3}>
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
                                '&:nth-of-type(odd)': { bgcolor: 'rgba(211, 47, 47, 0.03)' },
                                '&:hover': { bgcolor: 'rgba(211, 47, 47, 0.06)' }
                              }}
                            >
                              <TableCell sx={{ fontWeight: index === 0 ? 'bold' : 'normal' }}>
                                {node.id}
                              </TableCell>
                              <TableCell>
                                <Box 
                                  sx={{ 
                                    display: 'inline-block',
                                    bgcolor: '#d32f2f',
                                    color: 'white',
                                    px: 1,
                                    py: 0.2,
                                    borderRadius: 1,
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
                                '&:nth-of-type(odd)': { bgcolor: 'rgba(25, 118, 210, 0.03)' },
                                '&:hover': { bgcolor: 'rgba(25, 118, 210, 0.06)' }
                              }}
                            >
                              <TableCell sx={{ fontWeight: index === 0 ? 'bold' : 'normal' }}>
                                {node.id}
                              </TableCell>
                              <TableCell>
                                <Box 
                                  sx={{ 
                                    display: 'inline-block',
                                    bgcolor: '#1976d2',
                                    color: 'white',
                                    px: 1,
                                    py: 0.2,
                                    borderRadius: 1,
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
        </Card>
      </Grow>
    </Box>
  );
};

export default MetricsTable; 