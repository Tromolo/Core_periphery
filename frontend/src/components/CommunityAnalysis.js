import React, { useEffect, useRef, useState, useLayoutEffect } from "react";
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Divider,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Button,
  IconButton,
  Tooltip
} from "@mui/material";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import Sigma from "sigma";
import Graph from "graphology";
import DownloadIcon from '@mui/icons-material/Download';
import InfoIcon from '@mui/icons-material/Info';

// Add a style tag to ensure canvas elements fill their container
const sigmaCanvasStyle = `
  .sigma-container canvas {
    width: 100% !important;
    height: 100% !important;
    position: absolute;
    top: 0;
    left: 0;
  }
`;

const CommunityAnalysis = ({ communityData }) => {
  const sigmaRef = useRef(null);
  const rendererRef = useRef(null);
  const containerRef = useRef(null);
  const [sigmaLoaded, setSigmaLoaded] = useState(false);
  const [sigmaError, setSigmaError] = useState(null);
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });

  if (!communityData) return null;

  const { 
    num_communities, 
    mean_size, 
    max_size, 
    min_size, 
    modularity, 
    size_distribution,
    visualization_file,
    graph_data
  } = communityData;

  // Colors for the pie chart and graph visualization
  const COLORS = ['#1a237e', '#303f9f', '#3f51b5', '#5c6bc0', '#7986cb', '#9fa8da', 
                 '#7e57c2', '#5e35b1', '#3949ab', '#1e88e5', '#039be5', '#00acc1'];

  // Prepare data for pie chart
  const pieData = size_distribution.map(item => ({
    name: `Community ${item.community}`,
    value: item.size
  }));

  // Monitor container size changes
  useLayoutEffect(() => {
    if (containerRef.current) {
      const updateSize = () => {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setContainerSize({ width, height });
      };

      const resizeObserver = new ResizeObserver(() => {
        updateSize();
        if (rendererRef.current) {
          try {
            rendererRef.current.refresh();
            // Force the renderer to resize
            rendererRef.current.getCamera().setState({
              x: 0.5,
              y: 0.5,
              ratio: 1.2,
              angle: 0
            });
            rendererRef.current.refresh();
          } catch (e) {
            console.error("Error refreshing Sigma:", e);
          }
        }
      });
      
      resizeObserver.observe(containerRef.current);
      updateSize(); // Initial size calculation
      
      return () => {
        resizeObserver.disconnect();
      };
    }
  }, [sigmaLoaded]);

  useEffect(() => {
    return () => {
      if (rendererRef.current) {
        console.log("Cleaning up Sigma renderer on unmount");
        try {
          rendererRef.current.kill();
        } catch (e) {
          console.error("Error during Sigma cleanup:", e);
        }
        rendererRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (rendererRef.current) {
      console.log("Cleaning up previous Sigma renderer");
      try {
        rendererRef.current.kill();
      } catch (e) {
        console.error("Error during Sigma cleanup:", e);
      }
      rendererRef.current = null;
      setSigmaLoaded(false);
    }

    if (graph_data && sigmaRef.current && containerRef.current) {
      try {
        console.log("Initializing Sigma graph...");
        
        // Get the exact container dimensions
        const containerRect = containerRef.current.getBoundingClientRect();
        const width = containerRect.width;
        const height = containerRect.height;
        
        console.log(`Container dimensions: ${width}x${height}`);
        
        const graph = new Graph();
        
        if (graph_data.nodes && Array.isArray(graph_data.nodes)) {
          graph_data.nodes.forEach(node => {
            if (!node || !node.id) return;
            
            const communityId = graph_data.communities && graph_data.communities[node.id] 
              ? graph_data.communities[node.id] 
              : 0;
              
            graph.addNode(node.id, {
              x: typeof node.x === 'number' ? node.x : Math.random(),
              y: typeof node.y === 'number' ? node.y : Math.random(),
              size: typeof node.size === 'number' ? node.size : 5,
              label: node.label || `Node ${node.id}`,
              color: COLORS[communityId % COLORS.length]
            });
          });
        }
        
        if (graph_data.edges && Array.isArray(graph_data.edges)) {
          graph_data.edges.forEach(edge => {
            if (!edge || !edge.source || !edge.target) return;
            
            if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
              try {
                if (!graph.hasEdge(edge.source, edge.target)) {
                  graph.addEdge(edge.source, edge.target, {
                    size: edge.weight || 1,
                    color: "#ccc"
                  });
                }
              } catch (edgeError) {
                console.warn("Error adding edge:", edgeError);
              }
            }
          });
        }
        
        if (graph.order > 0) {
          // Ensure the sigma container takes the full width and height
          if (sigmaRef.current) {
            sigmaRef.current.style.width = "100%";
            sigmaRef.current.style.height = "100%";
          }
          
          const renderer = new Sigma(graph, sigmaRef.current, {
            renderEdgeLabels: false,
            allowInvalidContainer: true,
            defaultEdgeColor: "#ccc",
            defaultNodeColor: "#999",
            labelSize: 14,
            labelWeight: "bold",
            camera: {
              ratio: 1.0,
            }
          });
          
          // Manually set the canvas sizes to match the container
          const updateCanvasSizes = () => {
            const container = sigmaRef.current;
            if (!container) return;
            
            const rect = container.getBoundingClientRect();
            const canvases = container.querySelectorAll('canvas');
            
            console.log(`Updating canvas sizes to ${rect.width}x${rect.height}`);
            
            canvases.forEach(canvas => {
              // Set the display size (css pixels)
              canvas.style.width = `${rect.width}px`;
              canvas.style.height = `${rect.height}px`;
              
              // Set the resolution (actual pixels)
              const pixelRatio = window.devicePixelRatio || 1;
              const width = Math.floor(rect.width * pixelRatio);
              const height = Math.floor(rect.height * pixelRatio);
              
              if (canvas.width !== width || canvas.height !== height) {
                canvas.width = width;
                canvas.height = height;
                
                // If this is a WebGL canvas, we need to update the viewport
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (gl) {
                  gl.viewport(0, 0, width, height);
                }
              }
            });
            
            // Force the renderer to redraw with the new dimensions
            renderer.refresh();
            
            // Center the camera
            renderer.getCamera().setState({
              x: 0.5,
              y: 0.5,
              ratio: 1.2,
              angle: 0
            });
            renderer.refresh();
          };
          
          // Initial canvas size update
          updateCanvasSizes();
          
          // Add resize event listener to update canvas sizes
          window.addEventListener('resize', updateCanvasSizes);
          
          // Force a resize after initialization
          setTimeout(() => {
            if (renderer) {
              try {
                updateCanvasSizes();
                renderer.getCamera().setState({
                  x: 0.5,
                  y: 0.5,
                  ratio: 1.2,
                  angle: 0
                });
                renderer.refresh();
                renderer.getCamera().animate({
                  x: 0.5,
                  y: 0.5,
                  ratio: 1.2,
                  angle: 0
                }, { duration: 300 });
              } catch (e) {
                console.error("Error refreshing Sigma:", e);
              }
            }
          }, 100);
          
          rendererRef.current = renderer;
          setSigmaLoaded(true);
          setSigmaError(null);
          console.log("Sigma graph initialized successfully with", graph.order, "nodes and", graph.size, "edges");
          
          // Clean up the resize listener when component unmounts
          return () => {
            window.removeEventListener('resize', updateCanvasSizes);
          };
        } else {
          setSigmaError("No valid nodes found in graph data");
        }
      } catch (error) {
        console.error("Error initializing Sigma graph:", error);
        setSigmaError(error.message);
      }
    }
  }, [graph_data, COLORS]);

  // Add a download function for the static image
  const handleDownloadVisualization = () => {
    if (visualization_file) {
      window.open(`http://localhost:8080/download/${visualization_file}`, '_blank');
    }
  };

  // Determine color based on modularity value
  const getModularityColor = (value) => {
    if (value >= 0.7) return "success";
    if (value >= 0.4) return "primary";
    if (value >= 0.2) return "warning";
    return "error";
  };

  // Get tooltip text for modularity value
  const getModularityTooltip = (value) => {
    return `Modularity ranges from -0.5 to 1. Higher values indicate stronger community structure. This network's score is ${value.toFixed(3)}.`;
  };

  // Get detailed interpretation text based on modularity value
  // This is the authoritative source for modularity in the application
  // Modularity calculation is done in the backend's prepare_community_analysis_data function
  const getModularityInterpretation = (value) => {
    if (value >= 0.7) {
      return "This network has very strong community structure. The communities are clearly defined with many more connections within communities than between them.";
    } else if (value >= 0.4) {
      return "This network has good community structure. Communities are well-defined, with significantly more connections within communities than between them.";
    } else if (value >= 0.2) {
      return "This network has moderate community structure. Communities can be identified, but there are still substantial connections between different communities.";
    } else {
      return "This network has weak community structure. The identified communities have nearly as many connections between them as within them.";
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 4,
        borderRadius: 4,
        background: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        textAlign: "center",
      }}
    >
      {/* Add the style tag to the component */}
      <style>{sigmaCanvasStyle}</style>
      
      <Typography variant="h4" sx={{ mb: 3, fontWeight: "bold", color: "primary.main" }}>
        Community Structure Analysis
      </Typography>

      <Grid container spacing={4}>
        {/* Community Statistics Card */}
        <Grid item xs={12} md={6}>
          <Card elevation={0} sx={{ height: '100%', borderRadius: 4, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Community Statistics</Typography>
              <Divider sx={{ mb: 3 }} />
              
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                  <Typography variant="body1">Number of Communities:</Typography>
                  <Chip color="primary" label={num_communities} />
                </Box>
                
                <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                  <Typography variant="body1">Average Community Size:</Typography>
                  <Chip color="primary" label={mean_size} />
                </Box>
                
                <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                  <Typography variant="body1">Largest Community:</Typography>
                  <Chip color="primary" label={max_size} />
                </Box>
                
                <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                  <Typography variant="body1">Smallest Community:</Typography>
                  <Chip color="primary" label={min_size} />
                </Box>
                
                <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                  <Typography variant="body1">Modularity Score:</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Chip 
                      color={getModularityColor(modularity)} 
                      label={modularity.toFixed(3)} 
                      sx={{ fontWeight: 'bold' }}
                    />
                    <Tooltip title={getModularityTooltip(modularity)}>
                      <IconButton size="small">
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Pie Chart Card */}
        <Grid item xs={12} md={6}>
          <Card elevation={0} sx={{ height: '100%', borderRadius: 4, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Community Size Distribution</Typography>
              <Divider sx={{ mb: 3 }} />
              
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`Size: ${value}`, 'Community']} />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Interactive Graph - Full Width */}
        <Grid item xs={12}>
          {graph_data && (
            <Card elevation={0} sx={{ borderRadius: 4, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)' }}>
              <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Interactive Community Graph</Typography>
                  {visualization_file && (
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={handleDownloadVisualization}
                    >
                      Download Static Image
                    </Button>
                  )}
                </Box>
                <Divider sx={{ mb: 3 }} />
                
                <div 
                  ref={containerRef}
                  style={{ 
                    width: '100%',
                    height: 500,
                    position: 'relative',
                    borderRadius: '8px',
                    border: '1px solid #eee',
                    overflow: 'hidden',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center'
                  }}
                >
                  <div 
                    ref={sigmaRef} 
                    className="sigma-container"
                    style={{ 
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      display: 'block'
                    }}
                  />
                  
                  {!sigmaLoaded && !sigmaError && (
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      zIndex: 10
                    }}>
                      <CircularProgress size={60} thickness={4} />
                    </div>
                  )}
                  
                  {sigmaError && (
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      zIndex: 10
                    }}>
                      <Typography color="error">
                        Error loading graph: {sigmaError}
                      </Typography>
                    </div>
                  )}
                </div>
                
                <Typography variant="body2" sx={{ mt: 2, textAlign: 'center', color: 'text.secondary' }}>
                  Interactive graph visualization with communities colored using the same palette as the charts.
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
        
        {/* Add modularity interpretation */}
        <Grid item xs={12}>
          <Box sx={{ 
            p: 2, 
            bgcolor: `${getModularityColor(modularity)}.light`, 
            borderRadius: 2,
            opacity: 0.9,
            mb: 2 
          }}>
            <Typography variant="body2">
              {getModularityInterpretation(modularity)}
            </Typography>
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default CommunityAnalysis;