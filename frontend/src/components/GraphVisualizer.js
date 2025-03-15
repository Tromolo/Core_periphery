import React, { useState, useEffect, useRef } from 'react';
import { Box, Card, Typography, Button, Paper, Grid, CircularProgress, Chip } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { 
  Hub, 
  Timeline, 
  AccountTree, 
  DeviceHub
} from '@mui/icons-material';
import { Stack } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import Sigma from "sigma";
import Graph from "graphology";

const GraphVisualizer = ({ graphData, metrics, csvFile, imageFile, gdfFile }) => {
  const theme = useTheme();
  const containerRef = useRef(null);
  const sigmaInstanceRef = useRef(null);
  const graphRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const mountedRef = useRef(true);

  // Handle downloads
  const handleDownloadCSV = () => csvFile && window.open(`http://localhost:8080/static/${csvFile}`, '_blank');
  const handleDownloadImage = () => imageFile && window.open(`http://localhost:8080/static/${imageFile}`, '_blank');
  const handleDownloadGDF = () => gdfFile && window.open(`http://localhost:8080/static/${gdfFile}`, '_blank');

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
            onClick={handleDownloadCSV}
            disabled={!csvFile}
          >
            CSV
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
      <Grid container spacing={2} sx={{ mt: 1 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard 
            title="Total Nodes" 
            value={metrics?.node_count || 0}
            icon={<Hub />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard 
            title="Total Edges" 
            value={metrics?.edge_count || 0}
            icon={<Timeline />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard 
            title="Core Nodes" 
            value={getCoreCount(metrics, graphData)}
            icon={<AccountTree />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard 
            title="Periphery Nodes" 
            value={getPeripheryCount(metrics, graphData)}
            icon={<DeviceHub />}
          />
        </Grid>
      </Grid>
    </Card>
  );
};

const MetricCard = ({ title, value, icon }) => {
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
          {typeof value === 'number' ? value : '-'}
        </Typography>
      </Box>
    </Paper>
  );
};

// Helper functions to get core and periphery counts with fallbacks
const getCoreCount = (metrics, graphData) => {
  // Log the values we're working with
  console.log("Getting core count:", { 
    metricsValue: metrics?.core_stats?.core_size,
    graphDataLength: graphData?.nodes?.length,
    coreNodesInGraphData: graphData?.nodes ? graphData.nodes.filter(node => node.type === 'C').length : 'N/A'
  });
  
  // Always calculate from graphData since metrics.core_stats values are incorrect
  if (graphData?.nodes) {
    return graphData.nodes.filter(node => node.type === 'C').length;
  }
  
  // Fallback to metrics if graphData is not available
  if (metrics?.core_stats?.core_size !== undefined) {
    return metrics.core_stats.core_size;
  }
  
  return 0;
};

const getPeripheryCount = (metrics, graphData) => {
  // Log the values we're working with
  console.log("Getting periphery count:", { 
    metricsValue: metrics?.core_stats?.periphery_size,
    graphDataLength: graphData?.nodes?.length,
    peripheryNodesInGraphData: graphData?.nodes ? graphData.nodes.filter(node => node.type === 'P').length : 'N/A'
  });
  
  // Always calculate from graphData since metrics.core_stats values are incorrect
  if (graphData?.nodes) {
    return graphData.nodes.filter(node => node.type === 'P').length;
  }
  
  // Fallback to metrics if graphData is not available
  if (metrics?.core_stats?.periphery_size !== undefined) {
    return metrics.core_stats.periphery_size;
  }
  
  return 0;
};

export default GraphVisualizer;