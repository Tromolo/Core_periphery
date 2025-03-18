import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Box, Card, Typography, Button, Paper, Grid, CircularProgress, Chip, Divider } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { 
  AccountTree, 
  DeviceHub,
  PieChart as PieChartIcon,
  CompareArrows,
  Insights,
  BlurOn
} from '@mui/icons-material';
import { Stack } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import Sigma from "sigma";
import Graph from "graphology";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const GraphVisualizer = ({ graphData, metrics, nodeCsvFile, edgeCsvFile, imageFile, gdfFile }) => {
  const theme = useTheme();
  const containerRef = useRef(null);
  const sigmaInstanceRef = useRef(null);
  const graphRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const mountedRef = useRef(true);

  // Handle downloads
  const handleDownloadNodeCSV = () => nodeCsvFile && window.open(`http://localhost:8080/download/${nodeCsvFile}`, '_blank');
  const handleDownloadEdgeCSV = () => edgeCsvFile && window.open(`http://localhost:8080/download/${edgeCsvFile}`, '_blank');
  const handleDownloadImage = () => imageFile && window.open(`http://localhost:8080/download/${imageFile}`, '_blank');
  const handleDownloadGDF = () => gdfFile && window.open(`http://localhost:8080/download/${gdfFile}`, '_blank');

  // Set mounted flag to false when component unmounts
  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Initialize and clean up Sigma
  useEffect(() => {
    // Skip if no data or container
    if (!graphData?.nodes || !containerRef.current) return;

    // Log metrics for debugging
    console.log("Metrics data:", metrics);
    if (metrics?.core_stats) {
      console.log("Core stats:", metrics.core_stats);
    } else {
      console.log("Core stats not found in metrics");
    }

    // Clear previous error
    setError(null);
    setLoading(true);

    // Clean up previous instance if it exists
    if (sigmaInstanceRef.current) {
      try {
        sigmaInstanceRef.current.kill();
      } catch (e) {
        console.error("Error cleaning up previous Sigma instance:", e);
      }
      sigmaInstanceRef.current = null;
    }

    // Create graph
    try {
      const graph = new Graph();
      graphRef.current = graph;

      // Add nodes with minimal attributes
      graphData.nodes.forEach(node => {
        const isCore = node.type === 'C';
        const degree = node.degree || 1;
        // Calculate node size based primarily on degree with a minimum size
        // Square root scaling helps prevent extremely large nodes
        const nodeSize = 3 + Math.sqrt(degree) * 2;
        
        graph.addNode(node.id, {
          x: Math.random() * 10 - 5,
          y: Math.random() * 10 - 5,
          size: nodeSize,
          color: isCore ? '#d32f2f' : '#1976d2',
          label: `Node ${node.id}`,
          nodeType: isCore ? 'core' : 'periphery',
          coreness: node.coreness || 0,
          degree: degree,
          betweenness: node.betweenness || 0,
          closeness: node.closeness || 0
        });
      });

      // Add edges with minimal attributes
      graphData.edges.forEach(edge => {
        if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
          const sourceType = graph.getNodeAttribute(edge.source, 'nodeType');
          const targetType = graph.getNodeAttribute(edge.target, 'nodeType');
          
          // Determine edge color based on connected node types
          let edgeColor;
          if (sourceType === 'core' && targetType === 'core') {
            edgeColor = '#d32f2f'; // Red for Core-Core
          } else if (sourceType === 'periphery' && targetType === 'periphery') {
            edgeColor = '#1976d2'; // Blue for Periphery-Periphery
        } else {
            edgeColor = '#9e9e9e'; // Gray for Core-Periphery
          }
          
          graph.addEdge(edge.source, edge.target, {
            size: 1,
            color: edgeColor
          });
        }
      });

      // Initialize Sigma with minimal settings
      const renderer = new Sigma(graph, containerRef.current, {
        renderEdgeLabels: false,
        defaultEdgeColor: '#ccc',
        defaultNodeColor: theme.palette.primary.main,
        labelRenderedSizeThreshold: 6
      });

      // Add minimal event listeners
      renderer.on('clickNode', ({ node }) => {
        if (mountedRef.current) {
          setSelectedNode(node);
        }
      });

      renderer.on('clickStage', () => {
        if (mountedRef.current) {
          setSelectedNode(null);
        }
      });

      // Store the renderer
      sigmaInstanceRef.current = renderer;
      
      // Update state
      if (mountedRef.current) {
        setLoading(false);
      }
          } catch (e) {
      console.error("Error initializing graph:", e);
      if (mountedRef.current) {
        setError(`Error initializing graph: ${e.message}`);
        setLoading(false);
      }
    }

    // Clean up function
    return () => {
      if (sigmaInstanceRef.current) {
        try {
          sigmaInstanceRef.current.kill();
        } catch (e) {
          console.error("Error cleaning up Sigma instance:", e);
        }
        sigmaInstanceRef.current = null;
      }
    };
  }, [graphData, theme]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (sigmaInstanceRef.current && mountedRef.current) {
        try {
          sigmaInstanceRef.current.refresh();
      } catch (e) {
          console.error("Error refreshing Sigma instance:", e);
        }
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <Card sx={{ p: 3, boxShadow: 3, borderRadius: 2, height: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, color: theme.palette.primary.main }}>
          Core-Periphery Visualization
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button 
            variant="outlined" 
            size="small"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadNodeCSV}
            disabled={!nodeCsvFile}
          >
            Nodes Data
          </Button>
          <Button 
            variant="outlined" 
            size="small"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadEdgeCSV}
            disabled={!edgeCsvFile}
          >
            Edges Data
          </Button>
          <Button 
            variant="outlined" 
            size="small"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadGDF}
            disabled={!gdfFile}
          >
            GDF
          </Button>
          <Button 
            variant="outlined" 
            size="small"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadImage}
            disabled={!imageFile}
          >
            Image
          </Button>
        </Box>
      </Box>

      {/* Main content */}
      <Grid container spacing={2}>
        {/* Graph visualization */}
        <Grid item xs={12} md={9}>
          <Box 
            ref={containerRef}
              sx={{ 
                height: 500, 
                position: 'relative',
              bgcolor: 'rgba(0,0,0,0.02)',
                borderRadius: 2,
                overflow: 'hidden',
              border: '1px solid rgba(0,0,0,0.1)',
              '& canvas': {
                width: '100% !important',
                height: '100% !important',
                position: 'absolute',
                top: 0,
                left: 0
              }
            }}
          >
            {loading && (
                <Box sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center',
                height: '100%',
                flexDirection: 'column',
                  position: 'absolute', 
                  top: 0, 
                  left: 0, 
                  right: 0, 
                  bottom: 0, 
                zIndex: 10,
                bgcolor: 'rgba(255,255,255,0.7)'
                }}>
                <CircularProgress size={40} />
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Loading graph visualization...
                </Typography>
                </Box>
              )}
              
            {error && (
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
                  flexDirection: 'column',
                p: 3
                }}>
                <Typography variant="body1" color="error" sx={{ mb: 2 }}>
                  {error}
                  </Typography>
                  <Typography variant="body2">
                  Please try uploading a different graph file or refreshing the page.
                  </Typography>
                </Box>
              )}
          </Box>
        </Grid>
        
        {/* Sidebar */}
        <Grid item xs={12} md={3}>
          <Stack spacing={2}>
            {/* Legend */}
            <Paper sx={{ p: 2, borderRadius: 2 }}>
              <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                Legend
              </Typography>
              
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ 
                    width: 16, 
                    height: 16, 
                    borderRadius: '50%', 
                    bgcolor: '#d32f2f'
                  }} />
                  <Typography variant="body2">Core Node</Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ 
                    width: 16, 
                    height: 16, 
                    borderRadius: '50%', 
                    bgcolor: '#1976d2'
                  }} />
                  <Typography variant="body2">Periphery Node</Typography>
                </Box>

                <Box sx={{ mt: 2, mb: 1 }}>
                  <Typography variant="subtitle2">Edge Types</Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ 
                    width: 16, 
                    height: 3, 
                    bgcolor: '#d32f2f'
                  }} />
                  <Typography variant="body2">Core-Core Connection</Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ 
                    width: 16, 
                    height: 3, 
                    bgcolor: '#1976d2'
                  }} />
                  <Typography variant="body2">Periphery-Periphery Connection</Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ 
                    width: 16, 
                    height: 3, 
                    bgcolor: '#9e9e9e'
                  }} />
                  <Typography variant="body2">Core-Periphery Connection</Typography>
                </Box>
              </Stack>
            </Paper>
            
            {/* Node details */}
            {selectedNode && graphRef.current && graphRef.current.hasNode(selectedNode) && (
              <Paper sx={{ p: 2, borderRadius: 2 }}>
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                  Node Details
                </Typography>
                
                <Stack spacing={1}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">ID:</Typography>
                    <Typography variant="body2" fontWeight="medium">{selectedNode}</Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Type:</Typography>
                    <Chip 
                      size="small" 
                      label={graphRef.current.getNodeAttribute(selectedNode, 'nodeType') === 'core' ? 'Core' : 'Periphery'}
                      color={graphRef.current.getNodeAttribute(selectedNode, 'nodeType') === 'core' ? 'error' : 'primary'}
              />
            </Box>
            
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Coreness:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {graphRef.current.getNodeAttribute(selectedNode, 'coreness').toFixed(3)}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Degree:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {graphRef.current.getNodeAttribute(selectedNode, 'degree')}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Betweenness:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {graphRef.current.getNodeAttribute(selectedNode, 'betweenness').toFixed(3)}
                    </Typography>
            </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Closeness:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {graphRef.current.getNodeAttribute(selectedNode, 'closeness').toFixed(3)}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Connections:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {graphRef.current.degree(selectedNode)}
                    </Typography>
                  </Box>
      </Stack>
              </Paper>
            )}
          </Stack>
        </Grid>
      </Grid>
      
      {/* Network statistics */}
      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <Typography variant="h6" sx={{ mb: 1 }}>Core-Periphery Structure</Typography>
          <Divider sx={{ mb: 2 }} />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard 
            title="Core Nodes" 
            value={getCoreCount(metrics, graphData)}
            icon={<AccountTree />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard 
            title="Periphery Nodes" 
            value={getPeripheryCount(metrics, graphData)}
            icon={<DeviceHub />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard 
            title="Core Percentage" 
            value={getCorePercentage(metrics, graphData)}
            icon={<PieChartIcon />}
          />
        </Grid>
        
        {/* New metrics row */}
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard 
            title="Core Density" 
            value={getCoreDensity(metrics, graphData)}
            icon={<BlurOn />}
            tooltip="How densely connected the core nodes are to each other"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard 
            title="Core-Periphery Connectivity" 
            value={getCorePeriConnectivity(metrics, graphData)}
            icon={<CompareArrows />}
            tooltip="Average number of connections from periphery nodes to core nodes"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard 
            title="Periphery Isolation" 
            value={getPeripheryIsolation(metrics, graphData)}
            icon={<Insights />}
            tooltip="Percentage of connections between periphery nodes"
          />
        </Grid>
      </Grid>
      
      {/* Add core-periphery structural analysis section */}
      {graphData?.nodes && graphData?.edges && (
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ mb: 1 }}>Core-Periphery Structural Analysis</Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>
          <Grid item xs={12}>
            <Paper elevation={2} sx={{ p: 2, borderRadius: 2 }}>
              <Grid container spacing={2}>
                {/* Text Analysis */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>Quality Assessment</Typography>
                  <Typography variant="body2" paragraph>
                    {getShortCorePeripheryAnalysis(metrics, graphData)}
                  </Typography>
                  
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>Structure Strength Indicators:</Typography>
                    <Grid container spacing={2} sx={{ mt: 1 }}>
                      <Grid item xs={12} sm={4}>
                        <Box sx={{ 
                          p: 1.5, 
                          bgcolor: 'rgba(25, 118, 210, 0.08)', 
                          borderRadius: 1,
                          border: '1px solid rgba(25, 118, 210, 0.2)'
                        }}>
                          <Typography variant="body2" fontWeight="medium" color="primary">Core Cohesion</Typography>
                          <Typography variant="h6">{getCoreDensity(metrics, graphData)}</Typography>
                          <Typography variant="caption">
                            {interpretCoreDensity(metrics, getCoreDensity(metrics, graphData))}
                          </Typography>
    </Box>
                      </Grid>
                      <Grid item xs={12} sm={4}>
                        <Box sx={{ 
                          p: 1.5, 
                          bgcolor: 'rgba(25, 118, 210, 0.08)', 
                          borderRadius: 1,
                          border: '1px solid rgba(25, 118, 210, 0.2)'
                        }}>
                          <Typography variant="body2" fontWeight="medium" color="primary">Core-Periphery Ratio</Typography>
                          <Typography variant="h6">{getCorePeripheryRatio(metrics, graphData)}</Typography>
                          <Typography variant="caption">
                            {interpretCorePeripheryRatio(metrics, getCorePeripheryRatio(metrics, graphData))}
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12} sm={4}>
                        <Box sx={{ 
                          p: 1.5, 
                          bgcolor: 'rgba(25, 118, 210, 0.08)', 
                          borderRadius: 1,
                          border: '1px solid rgba(25, 118, 210, 0.2)'
                        }}>
                          <Typography variant="body2" fontWeight="medium" color="primary">Ideal Pattern Match</Typography>
                          <Typography variant="h6">{calculateIdealPatternMatch(metrics, graphData)}</Typography>
                          <Typography variant="caption">
                            {interpretIdealPatternMatch(metrics, calculateIdealPatternMatch(metrics, graphData))}
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </Box>
                </Grid>
                
                {/* Connection Patterns Visualization */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>Connection Patterns</Typography>
                  <Box sx={{ height: 280, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <ConnectionPieChart metrics={metrics} graphData={graphData} />
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      )}
      
      {/* Edge Distribution Section */}
      {graphData?.edges && graphData.edges.length > 0 && (
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ mb: 1 }}>Connection Patterns</Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>
          <Grid item xs={12}>
            <Paper elevation={2} sx={{ p: 2, borderRadius: 2 }}>
              <EdgeDistributionStats graphData={graphData} />
            </Paper>
          </Grid>
        </Grid>
      )}
    </Card>
  );
};

const MetricCard = ({ title, value, icon, tooltip }) => {
  const theme = useTheme();
  
  return (
    <Paper
      elevation={2}
        sx={{
        p: 2,
        borderRadius: 2,
          display: 'flex',
          alignItems: 'center',
        gap: 2,
        height: '100%',
      }}
      title={tooltip}
      >
        <Box 
          sx={{ 
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 40,
          height: 40,
          borderRadius: '50%',
          bgcolor: 'rgba(25, 118, 210, 0.1)',
            color: theme.palette.primary.main,
          }}
        >
          {icon}
        </Box>
      <Box>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
          {value !== undefined ? value : '-'}
        </Typography>
      </Box>
    </Paper>
  );
};

// Helper functions to get core and periphery counts with fallbacks
const getCoreCount = (metrics, graphData) => {
  // First check if metrics has core_stats.core_size
  if (metrics?.core_stats?.core_size !== undefined) {
    return metrics.core_stats.core_size;
  }
  
  // Fallback to calculating from graphData if metrics not available
  if (graphData?.nodes) {
    return graphData.nodes.filter(node => node.type === 'C').length;
  }
  
  return 0;
};

const getPeripheryCount = (metrics, graphData) => {
  // First check if metrics has core_stats.periphery_size
  if (metrics?.core_stats?.periphery_size !== undefined) {
    return metrics.core_stats.periphery_size;
  }
  
  // Fallback to calculating from graphData if metrics not available
  if (graphData?.nodes) {
    return graphData.nodes.filter(node => node.type === 'P').length;
  }
  
  return 0;
};

// Get Core Percentage from metrics when available
const getCorePercentage = (metrics, graphData) => {
  // First check if metrics has core_stats.core_percentage
  if (metrics?.core_stats?.core_percentage !== undefined) {
    return `${metrics.core_stats.core_percentage.toFixed(1)}%`;
  }
  
  // Fallback to calculating from graphData if metrics not available
  if (graphData?.nodes) {
    const totalNodes = graphData.nodes.length;
    const coreNodes = graphData.nodes.filter(node => node.type === 'C').length;
    
    if (totalNodes > 0) {
      const percentage = (coreNodes / totalNodes) * 100;
      return `${percentage.toFixed(1)}%`;
    }
  }
  
  return '0.0%';
};

// Get Core Density from metrics when available
const getCoreDensity = (metrics, graphData) => {
  // First check if metrics has core_periphery_metrics.core_density
  if (metrics?.core_periphery_metrics?.core_density !== undefined) {
    return metrics.core_periphery_metrics.core_density.toFixed(2);
  }
  
  // Fallback to calculating from graphData if metrics not available
  if (graphData?.nodes && graphData?.edges) {
    const coreNodes = graphData.nodes.filter(node => node.type === 'C');
    if (coreNodes.length <= 1) return '0.00';
    
    const coreNodeIds = new Set(coreNodes.map(node => node.id));
    let coreEdges = 0;
    let possibleCoreEdges = (coreNodes.length * (coreNodes.length - 1)) / 2;
    
    graphData.edges.forEach(edge => {
      if (coreNodeIds.has(edge.source) && coreNodeIds.has(edge.target)) {
        coreEdges++;
      }
    });
    
    return (coreEdges / possibleCoreEdges).toFixed(2);
  }
  
  return '0.00';
};

const getCorePeriConnectivity = (metrics, graphData) => {
  // First check if metrics has core_periphery_metrics.periphery_core_connectivity
  if (metrics?.core_periphery_metrics?.periphery_core_connectivity !== undefined) {
    return metrics.core_periphery_metrics.periphery_core_connectivity.toFixed(2);
  }
  
  // Calculate from graphData if available (fallback)
  if (graphData?.nodes && graphData?.edges) {
    const peripheryNodes = graphData.nodes.filter(node => node.type === 'P');
    if (peripheryNodes.length === 0) return '0.00';
    
    const peripheryNodeIds = new Set(peripheryNodes.map(node => node.id));
    const coreNodeIds = new Set(graphData.nodes.filter(node => node.type === 'C').map(node => node.id));
    let corePeriEdges = 0;
    
    graphData.edges.forEach(edge => {
      if ((coreNodeIds.has(edge.source) && peripheryNodeIds.has(edge.target)) ||
          (coreNodeIds.has(edge.target) && peripheryNodeIds.has(edge.source))) {
        corePeriEdges++;
      }
    });
    
    return (corePeriEdges / peripheryNodes.length).toFixed(2);
  }
  
  return '0.00';
};

const getPeripheryIsolation = (metrics, graphData) => {
  // Check if metrics has core_periphery_metrics with periphery_isolation
  if (metrics?.core_periphery_metrics?.periphery_isolation !== undefined) {
    return metrics.core_periphery_metrics.periphery_isolation.toFixed(2) + '%';
  }
  
  // Calculate from graphData if available (fallback)
  if (graphData?.nodes && graphData?.edges) {
    const peripheryNodes = graphData.nodes.filter(node => node.type === 'P');
    if (peripheryNodes.length <= 1) return '0.00%';
    
    const peripheryNodeIds = new Set(peripheryNodes.map(node => node.id));
    let peripheryPeripheryEdges = 0;
    let totalEdges = graphData.edges.length;
    
    graphData.edges.forEach(edge => {
      if (peripheryNodeIds.has(edge.source) && peripheryNodeIds.has(edge.target)) {
        peripheryPeripheryEdges++;
      }
    });
    
    if (totalEdges === 0) return '0.00%';
    const peripheryIsolation = (peripheryPeripheryEdges / totalEdges) * 100;
    return peripheryIsolation.toFixed(2) + '%';
  }
  
  return '0.00%';
};

const getShortCorePeripheryAnalysis = (metrics, graphData) => {
  // If we have backend-calculated analysis, use it
  if (metrics?.core_periphery_analysis?.structure_quality) {
    const quality = metrics.core_periphery_analysis.structure_quality;
    const corePercentage = metrics.core_stats.core_percentage.toFixed(1);
    const coreDensity = metrics.core_periphery_metrics.core_density.toFixed(2);
    
    // Generate explanation based on structure quality
    let explanation = "";
    if (quality === "strong") {
      explanation = "This network exhibits a strong core-periphery structure with a densely connected core and periphery nodes primarily connected to the core.";
    } else if (quality === "moderate") {
      explanation = "This network shows a moderate core-periphery structure with a reasonably connected core and periphery nodes that have some connections to the core.";
    } else if (quality === "weak") {
      explanation = "This network has a weak core-periphery structure as periphery-to-periphery connections dominate, contradicting the ideal pattern.";
    } else {
      explanation = "This network shows a mixed structure with some core-periphery characteristics but significant deviations from the ideal pattern.";
    }
    
    return `${explanation} The core represents ${corePercentage}% of nodes with a density of ${coreDensity}.`;
  }
  
  // Fallback to calculating from graphData
  if (!graphData?.nodes || !graphData?.edges) {
    return "Core-periphery analysis data is not available.";
  }
  
  // Calculate metrics for analysis
  const coreNodes = graphData.nodes.filter(node => node.type === 'C');
  const peripheryNodes = graphData.nodes.filter(node => node.type === 'P');
  const totalNodes = graphData.nodes.length;
  
  if (coreNodes.length === 0 || peripheryNodes.length === 0) {
    return "The network doesn't have a proper core-periphery structure as either core or periphery nodes are missing.";
  }
  
  const corePercentage = (coreNodes.length / totalNodes) * 100;
  const coreDensity = parseFloat(getCoreDensity(null, graphData));
  
  const coreNodeIds = new Set(coreNodes.map(node => node.id));
  const peripheryNodeIds = new Set(peripheryNodes.map(node => node.id));
  
  let coreCore = 0, corePeriphery = 0, peripheryPeriphery = 0;
  
  graphData.edges.forEach(edge => {
    const sourceIsCore = coreNodeIds.has(edge.source);
    const targetIsCore = coreNodeIds.has(edge.target);
    
    if (sourceIsCore && targetIsCore) {
      coreCore++;
    } else if ((!sourceIsCore && targetIsCore) || (sourceIsCore && !targetIsCore)) {
      corePeriphery++;
    } else {
      peripheryPeriphery++;
    }
  });
  
  const totalEdges = graphData.edges.length;
  const peripheryPeripheryPct = (peripheryPeriphery / totalEdges) * 100;
  
  // Interpret the results
  let structureQuality = "uncertain";
  let explanation = "";
  
  if (coreDensity > 0.7 && peripheryPeripheryPct < 10) {
    structureQuality = "strong";
    explanation = "This network exhibits a strong core-periphery structure with a densely connected core and periphery nodes primarily connected to the core.";
  } else if (coreDensity > 0.4 && peripheryPeripheryPct < 20) {
    structureQuality = "moderate";
    explanation = "This network shows a moderate core-periphery structure with a reasonably connected core and periphery nodes that have some connections to the core.";
  } else if (peripheryPeripheryPct > 30) {
    structureQuality = "weak";
    explanation = "This network has a weak core-periphery structure as periphery-to-periphery connections dominate, contradicting the ideal pattern.";
  } else {
    structureQuality = "mixed";
    explanation = "This network shows a mixed structure with some core-periphery characteristics but significant deviations from the ideal pattern.";
  }
  
  return `${explanation} The core represents ${corePercentage.toFixed(1)}% of nodes with a density of ${coreDensity}.`;
};

const getCorePeripheryAnalysis = (graphData) => {
  // Calculate metrics for analysis
  const coreNodes = graphData.nodes.filter(node => node.type === 'C');
  const peripheryNodes = graphData.nodes.filter(node => node.type === 'P');
  const totalNodes = graphData.nodes.length;
  
  if (coreNodes.length === 0 || peripheryNodes.length === 0) {
    return "The network doesn't have a proper core-periphery structure as either core or periphery nodes are missing.";
  }
  
  const corePercentage = (coreNodes.length / totalNodes) * 100;
  const coreDensity = parseFloat(getCoreDensity(null, graphData));
  
  const coreNodeIds = new Set(coreNodes.map(node => node.id));
  const peripheryNodeIds = new Set(peripheryNodes.map(node => node.id));
  
  let coreCore = 0, corePeriphery = 0, peripheryPeriphery = 0;
  
  graphData.edges.forEach(edge => {
    const sourceIsCore = coreNodeIds.has(edge.source);
    const targetIsCore = coreNodeIds.has(edge.target);
    
    if (sourceIsCore && targetIsCore) {
      coreCore++;
    } else if ((!sourceIsCore && targetIsCore) || (sourceIsCore && !targetIsCore)) {
      corePeriphery++;
    } else {
      peripheryPeriphery++;
    }
  });
  
  const totalEdges = graphData.edges.length;
  const coreCorePct = (coreCore / totalEdges) * 100;
  const corePeripheryPct = (corePeriphery / totalEdges) * 100;
  const peripheryPeripheryPct = (peripheryPeriphery / totalEdges) * 100;
  
  // Interpret the results
  let structureQuality = "uncertain";
  let explanation = "";
  
  if (coreDensity > 0.7 && peripheryPeripheryPct < 10) {
    structureQuality = "strong";
    explanation = "This network exhibits a strong core-periphery structure with a densely connected core and periphery nodes primarily connected to the core.";
  } else if (coreDensity > 0.4 && peripheryPeripheryPct < 20) {
    structureQuality = "moderate";
    explanation = "This network shows a moderate core-periphery structure with a reasonably connected core and periphery nodes that have some connections to the core.";
  } else if (peripheryPeripheryPct > coreCorePct || peripheryPeripheryPct > corePeripheryPct) {
    structureQuality = "weak";
    explanation = "This network has a weak core-periphery structure as periphery-to-periphery connections dominate, contradicting the ideal pattern.";
  } else {
    structureQuality = "mixed";
    explanation = "This network shows a mixed structure with some core-periphery characteristics but significant deviations from the ideal pattern.";
  }
  
  return `${explanation} The core represents ${corePercentage.toFixed(1)}% of nodes with a density of ${coreDensity}. There are ${coreCore} core-core connections (${coreCorePct.toFixed(1)}%), ${corePeriphery} core-periphery connections (${corePeripheryPct.toFixed(1)}%), and ${peripheryPeriphery} periphery-periphery connections (${peripheryPeripheryPct.toFixed(1)}%).`;
};

const getCorePeripheryRatio = (metrics, graphData) => {
  // If we have backend-calculated ratio, use it
  if (metrics?.core_periphery_metrics?.core_periphery_ratio !== undefined) {
    return metrics.core_periphery_metrics.core_periphery_ratio.toFixed(2);
  }
  
  // Calculate the ratio of core-periphery edges to total edges
  if (!graphData?.nodes || !graphData?.edges) {
    return '0.00';
  }
  
  const coreNodeIds = new Set(graphData.nodes.filter(node => node.type === 'C').map(node => node.id));
  const peripheryNodeIds = new Set(graphData.nodes.filter(node => node.type === 'P').map(node => node.id));
  
  let corePeripheryEdges = 0;
  const totalEdges = graphData.edges.length;
  
  if (totalEdges === 0) return '0.00';
  
  graphData.edges.forEach(edge => {
    if ((coreNodeIds.has(edge.source) && peripheryNodeIds.has(edge.target)) ||
        (coreNodeIds.has(edge.target) && peripheryNodeIds.has(edge.source))) {
      corePeripheryEdges++;
    }
  });
  
  const ratio = (corePeripheryEdges / totalEdges).toFixed(2);
  return ratio;
};

const interpretCoreDensity = (metrics, density) => {
  // If we have backend-calculated interpretation, use it
  if (metrics?.core_periphery_analysis?.interpretations?.core_density) {
    return metrics.core_periphery_analysis.interpretations.core_density;
  }
  
  // Fallback to interpreting based on the density value
  const value = parseFloat(density);
  
  if (value >= 0.8) {
    return "Very high density - strongly connected core";
  } else if (value >= 0.6) {
    return "High density - well-connected core";
  } else if (value >= 0.4) {
    return "Moderate density - reasonably connected core";
  } else if (value >= 0.2) {
    return "Low density - sparsely connected core";
  } else {
    return "Very low density - poorly connected core";
  }
};

const interpretCorePeripheryRatio = (metrics, ratio) => {
  // If we have backend-calculated interpretation, use it
  if (metrics?.core_periphery_analysis?.interpretations?.cp_ratio) {
    return metrics.core_periphery_analysis.interpretations.cp_ratio;
  }
  
  // Fallback to interpreting based on the ratio value
  const value = parseFloat(ratio);
  
  if (value >= 0.6) {
    return "High integration between core and periphery";
  } else if (value >= 0.4) {
    return "Moderate integration between core and periphery";
  } else if (value >= 0.2) {
    return "Low integration between core and periphery";
  } else {
    return "Very low integration between core and periphery";
  }
};

const calculateIdealPatternMatch = (metrics, graphData) => {
  // If we have backend-calculated analysis, use it
  if (metrics?.core_periphery_analysis?.ideal_pattern_match !== undefined) {
    return metrics.core_periphery_analysis.ideal_pattern_match.toFixed(1) + '%';
  }
  
  // Fallback to calculating from graphData
  if (!graphData?.nodes || !graphData?.edges) {
    return '0.0%';
  }
  
  // Calculate ideal pattern match score
  const coreNodes = graphData.nodes.filter(node => node.type === 'C');
  const peripheryNodes = graphData.nodes.filter(node => node.type === 'P');
  
  if (coreNodes.length === 0 || peripheryNodes.length === 0) {
    return '0.0%';
  }
  
  const coreNodeIds = new Set(coreNodes.map(node => node.id));
  const peripheryNodeIds = new Set(peripheryNodes.map(node => node.id));
  
  let totalPatternScore = 0;
  let maxPatternScore = 0;
  
  // For each pair of nodes, check if their connection status matches the ideal pattern
  for (let i = 0; i < graphData.nodes.length; i++) {
    const node1 = graphData.nodes[i];
    for (let j = i + 1; j < graphData.nodes.length; j++) {
      const node2 = graphData.nodes[j];
      
      // Skip if nodes are the same
      if (node1.id === node2.id) continue;
      
      const node1IsCore = coreNodeIds.has(node1.id);
      const node2IsCore = coreNodeIds.has(node2.id);
      
      // Check if an edge exists between these nodes
      const hasEdge = graphData.edges.some(
        edge => (edge.source === node1.id && edge.target === node2.id) || 
                (edge.source === node2.id && edge.target === node1.id)
      );
      
      maxPatternScore++;
      
      // In ideal pattern:
      // - Core-Core: should have edge
      // - Core-Periphery: should have edge
      // - Periphery-Periphery: should NOT have edge
      if (node1IsCore && node2IsCore) {
        // Core-Core: should have edge
        if (hasEdge) totalPatternScore++;
      } else if ((!node1IsCore && node2IsCore) || (node1IsCore && !node2IsCore)) {
        // Core-Periphery: should have edge
        if (hasEdge) totalPatternScore++;
      } else {
        // Periphery-Periphery: should NOT have edge
        if (!hasEdge) totalPatternScore++;
      }
    }
  }
  
  const matchPercentage = (totalPatternScore / maxPatternScore * 100);
  return matchPercentage.toFixed(1) + '%';
};

const interpretIdealPatternMatch = (metrics, matchValue) => {
  // If we have backend-calculated analysis, use it
  if (metrics?.core_periphery_analysis?.pattern_match_interpretation) {
    return metrics.core_periphery_analysis.pattern_match_interpretation;
  }
  
  // Fallback to interpreting based on the match value
  const value = parseFloat(matchValue);
  
  if (value >= 90) {
    return "Excellent match to ideal core-periphery structure";
  } else if (value >= 75) {
    return "Good match to ideal core-periphery structure";
  } else if (value >= 50) {
    return "Moderate match to ideal core-periphery structure";
  } else if (value >= 25) {
    return "Weak match to ideal core-periphery structure";
  } else {
    return "Poor match to ideal core-periphery structure";
  }
};

// Component to display edge distribution statistics
const EdgeDistributionStats = ({ graphData }) => {
  const edgeStats = useMemo(() => {
    if (!graphData?.nodes || !graphData?.edges) return null;
    
    const coreNodeIds = new Set(graphData.nodes.filter(node => node.type === 'C').map(node => node.id));
    const peripheryNodeIds = new Set(graphData.nodes.filter(node => node.type === 'P').map(node => node.id));
    
    let coreCore = 0;
    let corePeriphery = 0;
    let peripheryPeriphery = 0;
    
    graphData.edges.forEach(edge => {
      const sourceIsCore = coreNodeIds.has(edge.source);
      const targetIsCore = coreNodeIds.has(edge.target);
      
      if (sourceIsCore && targetIsCore) {
        coreCore++;
      } else if ((!sourceIsCore && targetIsCore) || (sourceIsCore && !targetIsCore)) {
        corePeriphery++;
      } else {
        peripheryPeriphery++;
      }
    });
    
    const total = graphData.edges.length;
    return {
      coreCore,
      corePeriphery,
      peripheryPeriphery,
      total,
      coreCorePct: ((coreCore / total) * 100).toFixed(1),
      corePeripheryPct: ((corePeriphery / total) * 100).toFixed(1),
      peripheryPeripheryPct: ((peripheryPeriphery / total) * 100).toFixed(1)
    };
  }, [graphData]);
  
  if (!edgeStats) return null;
  
  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <Typography variant="subtitle1" gutterBottom>Edge Distribution</Typography>
      </Grid>
      <Grid item xs={12} sm={4}>
        <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'rgba(211, 47, 47, 0.1)', borderRadius: 2 }}>
          <Typography variant="body2" color="error">Core-Core</Typography>
          <Typography variant="h6">{edgeStats.coreCore}</Typography>
          <Typography variant="caption">({edgeStats.coreCorePct}%)</Typography>
        </Box>
      </Grid>
      <Grid item xs={12} sm={4}>
        <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'rgba(158, 158, 158, 0.1)', borderRadius: 2 }}>
          <Typography variant="body2" color="text.secondary">Core-Periphery</Typography>
          <Typography variant="h6">{edgeStats.corePeriphery}</Typography>
          <Typography variant="caption">({edgeStats.corePeripheryPct}%)</Typography>
        </Box>
      </Grid>
      <Grid item xs={12} sm={4}>
        <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'rgba(25, 118, 210, 0.1)', borderRadius: 2 }}>
          <Typography variant="body2" color="primary">Periphery-Periphery</Typography>
          <Typography variant="h6">{edgeStats.peripheryPeriphery}</Typography>
          <Typography variant="caption">({edgeStats.peripheryPeripheryPct}%)</Typography>
        </Box>
      </Grid>
    </Grid>
  );
};

// Component to display a pie chart of connection patterns
const ConnectionPieChart = ({ metrics, graphData }) => {
  const theme = useTheme();
  const edgeStats = useMemo(() => {
    // If we have backend-calculated connection patterns, use them
    if (metrics?.core_periphery_analysis?.connection_patterns) {
      const patterns = metrics.core_periphery_analysis.connection_patterns;
      return [
        { 
          name: 'Core-Core', 
          value: patterns.core_core.count, 
          percentage: patterns.core_core.percentage.toFixed(1) + '%',
          color: '#d32f2f'
        },
        { 
          name: 'Core-Periphery', 
          value: patterns.core_periphery.count, 
          percentage: patterns.core_periphery.percentage.toFixed(1) + '%',
          color: '#9e9e9e'
        },
        { 
          name: 'Periphery-Periphery', 
          value: patterns.periphery_periphery.count, 
          percentage: patterns.periphery_periphery.percentage.toFixed(1) + '%',
          color: '#1976d2'
        }
      ];
    }
    
    // Fallback to calculating from graphData
    if (!graphData?.nodes || !graphData?.edges) return null;
    
    const coreNodeIds = new Set(graphData.nodes.filter(node => node.type === 'C').map(node => node.id));
    const peripheryNodeIds = new Set(graphData.nodes.filter(node => node.type === 'P').map(node => node.id));
    
    let coreCore = 0;
    let corePeriphery = 0;
    let peripheryPeriphery = 0;
    
    graphData.edges.forEach(edge => {
      const sourceIsCore = coreNodeIds.has(edge.source);
      const targetIsCore = coreNodeIds.has(edge.target);
      
      if (sourceIsCore && targetIsCore) {
        coreCore++;
      } else if ((!sourceIsCore && targetIsCore) || (sourceIsCore && !targetIsCore)) {
        corePeriphery++;
      } else {
        peripheryPeriphery++;
      }
    });
    
    const total = graphData.edges.length;
    
    return [
      { 
        name: 'Core-Core', 
        value: coreCore, 
        percentage: ((coreCore / total) * 100).toFixed(1) + '%',
        color: '#d32f2f'
      },
      { 
        name: 'Core-Periphery', 
        value: corePeriphery, 
        percentage: ((corePeriphery / total) * 100).toFixed(1) + '%',
        color: '#9e9e9e'
      },
      { 
        name: 'Periphery-Periphery', 
        value: peripheryPeriphery, 
        percentage: ((peripheryPeriphery / total) * 100).toFixed(1) + '%',
        color: '#1976d2'
      }
    ];
  }, [metrics, graphData]);
  
  if (!edgeStats) return <Typography>No data available</Typography>;
  
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={edgeStats}
          cx="50%"
          cy="50%"
          labelLine={true}
          label={({name, percentage}) => `${name}: ${percentage}`}
          outerRadius={80}
          dataKey="value"
        >
          {edgeStats.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip 
          formatter={(value, name, props) => [
            `${value} (${props.payload.percentage})`,
            name
          ]}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default GraphVisualizer;