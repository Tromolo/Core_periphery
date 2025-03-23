import React, { useEffect, useRef, useState, useLayoutEffect, useMemo, useCallback } from "react";
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
  Tooltip,
  Slider,
  FormControlLabel,
  Switch
} from "@mui/material";
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, Legend, CartesianGrid, Cell } from "recharts";
import Sigma from "sigma";
import Graph from "graphology";
import forceAtlas2 from 'graphology-layout-forceatlas2';
import FA2Layout from 'graphology-layout-forceatlas2/worker';
import DownloadIcon from '@mui/icons-material/Download';
import InfoIcon from '@mui/icons-material/Info';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import CheckIcon from '@mui/icons-material/Check';
import CenterFocusStrongIcon from '@mui/icons-material/CenterFocusStrong';

// Add a style tag to ensure canvas elements fill their container
const sigmaCanvasStyle = `
  .sigma-container canvas {
    width: 100% !important;
    height: 100% !important;
    position: absolute;
    top: 0;
    left: 0;
  }
  
  .sigma-controls {
    position: absolute;
    bottom: 10px;
    right: 10px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    z-index: 10;
  }
  
  .sigma-tooltip {
    position: absolute;
    background-color: rgba(255, 255, 255, 0.95);
    padding: 10px;
    border-radius: 4px;
    box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.15);
    font-size: 12px;
    max-width: 200px;
    pointer-events: none;
  }
`;

const CommunityAnalysis = ({ communityData }) => {
  const sigmaRef = useRef(null);
  const rendererRef = useRef(null);
  const containerRef = useRef(null);
  const layoutWorkerRef = useRef(null);
  const graphRef = useRef(null);
  const [sigmaLoaded, setSigmaLoaded] = useState(false);
  const [sigmaError, setSigmaError] = useState(null);
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const [nodeSize, setNodeSize] = useState(1.0);
  const [showLabels, setShowLabels] = useState(false);
  const [isLayoutRunning, setIsLayoutRunning] = useState(false);
  const highlightedNodes = useRef(new Map());
  const initDone = useRef(false);
  const layoutTransitionRef = useRef(false);
  const faWorkerRef = useRef(null);
  const [isForceAtlas2Running, setIsForceAtlas2Running] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const autoStartRef = useRef(false);

  if (!communityData) return null;
  
  // Check if we have real data or just placeholder data
  if (communityData.num_communities === 0 || 
      !communityData.graph_data || 
      !communityData.graph_data.nodes || 
      communityData.graph_data.nodes.length === 0) {
    return (
      <Paper sx={{ p: 4, borderRadius: 2, boxShadow: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column', p: 4 }}>
          <CircularProgress size={40} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Loading community data...
          </Typography>
        </Box>
      </Paper>
    );
  }

  const { 
    num_communities, 
    mean_size, 
    max_size, 
    min_size, 
    modularity, 
    size_distribution,
    graph_data
  } = communityData;

  // Enhanced colors for the communities with better saturation (AtlasGroup2 style)
  const COLORS = [
    '#3366CC', '#DC3912', '#FF9900', '#109618', '#990099', '#0099C6',
    '#DD4477', '#66AA00', '#B82E2E', '#316395', '#994499', '#22AA99',
    '#AAAA11', '#6633CC', '#E67300', '#8B0707', '#329262', '#5574A6'
  ];

  // Add this useMemo to memoize the COLORS array
  const memoizedColors = useMemo(() => COLORS, []);

  // Prepare data for histogram
  const histogramData = size_distribution.map((item, index) => ({
    name: `Community ${item.community}`,
    size: item.size,
    color: memoizedColors[index % memoizedColors.length]
  }));

  // Sort histogram data by size (descending)
  histogramData.sort((a, b) => b.size - a.size);

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
            // Just refresh the renderer without changing the camera state
            rendererRef.current.refresh();
          } catch (e) {
            console.error("Error refreshing Sigma during resize:", e);
          }
        }
      });
      
      resizeObserver.observe(containerRef.current);
      updateSize(); // Initial size calculation
      
      return () => {
        resizeObserver.disconnect();
      };
    }
  }, []);

  // Clean up resources on unmount
  useEffect(() => {
    return () => {
      // Clean up Sigma renderer
      if (rendererRef.current) {
        console.log("Cleaning up Sigma renderer on unmount");
        try {
          rendererRef.current.kill();
        } catch (e) {
          console.error("Error during Sigma cleanup:", e);
        }
        rendererRef.current = null;
      }
      
      // Clean up ForceAtlas2 worker
      if (layoutWorkerRef.current) {
        console.log("Cleaning up ForceAtlas2 worker on unmount");
        try {
          layoutWorkerRef.current.stop();
          layoutWorkerRef.current.kill();
        } catch (e) {
          console.error("Error during ForceAtlas2 cleanup:", e);
        }
        layoutWorkerRef.current = null;
      }
    };
  }, []);

  // Create FA2Layout worker with a render callback
  const createLayoutWorker = () => {
    try {
      if (!graphRef.current || !rendererRef.current) {
        console.error("Cannot create layout worker: graph or renderer missing");
        return null;
      }

      console.log("Creating ForceAtlas2 layout worker");
      
      const settings = {
        linLogMode: false,
        outboundAttractionDistribution: false,
        adjustSizes: false,
        edgeWeightInfluence: 1,
        scalingRatio: 1,
        strongGravityMode: false,
        gravity: 1,
        slowDown: 2,
        barnesHutOptimize: true,
        barnesHutTheta: 0.5,
      };
      
      // Create a new FA2Layout worker with our graph and settings
      const worker = new FA2Layout(graphRef.current, {
        settings: settings,
        getEdgeWeight: 'weight'
      });
      
      // Setup the refresh callback
      const renderFrame = () => {
        if (rendererRef.current) {
          try {
            rendererRef.current.refresh();
            // Continue animation loop if worker is still running
            if (worker.isRunning()) {
              requestAnimationFrame(renderFrame);
            }
          } catch (e) {
            console.error("Error refreshing during layout:", e);
          }
        }
      };
      
      // Add a refresh callback
      worker.onTick = () => {
        requestAnimationFrame(renderFrame);
      };
      
      return worker;
    } catch (e) {
      console.error("Error creating layout worker:", e);
      return null;
    }
  };

  // Update the useEffect to automatically start ForceAtlas2 after initialization
  useEffect(() => {
    let sigma = null;
    
    if (containerRef.current && graph_data) {
      console.log("Initializing graph in useEffect");
      
      // Prevent reinitialization during layout transition
      if (layoutTransitionRef.current) {
        console.log("Skipping reinitialization during layout transition");
        return;
      }

      // Check if we're currently running ForceAtlas2 - don't reinitialize if so
      if (isForceAtlas2Running && faWorkerRef.current) {
        console.log("Skipping reinitialization while ForceAtlas2 is running");
        return;
      }

      // Cleanup previous instances
    if (rendererRef.current) {
        console.log("Cleaning up previous renderer");
      try {
        rendererRef.current.kill();
          rendererRef.current = null;
        } catch (e) {
          console.error("Error killing renderer:", e);
        }
      }
      
      if (sigmaRef.current) {
        // Clean up any canvas elements left by previous renderer
        while (sigmaRef.current.firstChild) {
          sigmaRef.current.removeChild(sigmaRef.current.firstChild);
        }
      }
      
      // Only clean up ForceAtlas2 if it's not running
      if (faWorkerRef.current && !isForceAtlas2Running) {
        console.log("Cleaning up previous ForceAtlas2 worker");
        try {
          // Cancel animation frame if it exists
          if (faWorkerRef.current.animationFrameId) {
            cancelAnimationFrame(faWorkerRef.current.animationFrameId);
          }
          faWorkerRef.current.stop();
          faWorkerRef.current = null;
      } catch (e) {
          console.error("Error stopping ForceAtlas2 worker:", e);
        }
      }
      
      // Only reset running state if we're not actually running
      if (!isForceAtlas2Running) {
        setIsForceAtlas2Running(false);
      }
      
      try {
        console.log("Creating new graph instance");
        // Create a new graph or clear the existing one
        if (!graphRef.current) {
          graphRef.current = new Graph();
        } else {
          graphRef.current.clear();
        }
        
        // Add nodes to the graph
        if (graph_data.nodes && graph_data.nodes.length > 0) {
          console.log(`Adding ${graph_data.nodes.length} nodes to graph`);
          
          graph_data.nodes.forEach(node => {
            try {
            const communityId = graph_data.communities && graph_data.communities[node.id] 
              ? graph_data.communities[node.id] 
              : 0;
              
              // Add node with attributes compatible with Sigma 3.0.1
              graphRef.current.addNode(node.id, {
                x: node.x !== undefined ? node.x : Math.random(),
                y: node.y !== undefined ? node.y : Math.random(),
                size: Math.max(3, Math.log((node.degree || 1) + 1) * 2),
                label: `Node ${node.id}`,
                color: COLORS[communityId % COLORS.length],
                communityId: parseInt(communityId, 10) || 0
              });
            } catch (e) {
              console.error(`Error adding node ${node.id}:`, e);
            }
          });
          
          // Add edges to the graph
          if (graph_data.edges && graph_data.edges.length > 0) {
            console.log(`Adding ${graph_data.edges.length} edges to graph`);
            
            graph_data.edges.forEach(edge => {
              try {
                if (graphRef.current.hasNode(edge.source) && graphRef.current.hasNode(edge.target)) {
                  graphRef.current.addEdge(edge.source, edge.target, {
                    weight: edge.weight || 1,
                    color: "#ccc", // Add explicit edge color
                    size: 1 // Add explicit size
                  });
                }
              } catch (e) {
                console.error(`Error adding edge ${edge.source}-${edge.target}:`, e);
              }
            });
          }
          
          // Apply initial layout with a static ForceAtlas2
          console.log("Applying initial ForceAtlas2 layout (static)");
          const initialLayout = forceAtlas2.assign(graphRef.current, {
            iterations: 20,  // Just a few iterations for initial layout
            settings: {
              gravity: 1,
              scalingRatio: 2,
              strongGravityMode: true,
              slowDown: 10
            }
          });
          
          console.log("Creating Sigma renderer");
          // Create the renderer
          const renderer = new Sigma(graphRef.current, sigmaRef.current, {
            renderEdgeLabels: false,
            allowInvalidContainer: true,
            defaultEdgeColor: "#ccc",
            defaultNodeColor: "#6c7293",
            labelSize: 14,
            labelWeight: "normal",
            labelRenderedSizeThreshold: showLabels ? 1 : 12,
            renderLabels: showLabels,
            minCameraRatio: 0.1,
            maxCameraRatio: 10,
            // Settings for smoother interactions
            enableEdgeHoverEvents: true,
            enableNodeHoverEvents: true,
            hideEdgesOnMove: true,
            // Explicitly set defaultEdgeType and defaultNodeType for compatibility
            defaultEdgeType: "line",
            // Reduce WebGL program complexity
            nodeProgramClasses: {
              // Let Sigma handle node program selection automatically
            },
            nodeReducer: (node, data) => {
              // Apply node size multiplier from slider
              return {
                ...data,
                size: data.size * nodeSize
              };
            }
          });
          
          // Add display log to help debug
          console.log("Sigma renderer settings:", {
            renderEdgeLabels: false,
            showLabels,
            nodeSize,
          });
          
          // Store the renderer
          rendererRef.current = renderer;
          setSigmaLoaded(true);
          setSigmaError(null);
          
          console.log("Graph initialized successfully with", graphRef.current.order, "nodes and", graphRef.current.size, "edges");
          
          // Automatically start ForceAtlas2 layout if not already done
          if (!autoStartRef.current) {
            console.log("Auto-starting ForceAtlas2 layout");
            // Use setTimeout to ensure component is fully mounted before starting layout
            setTimeout(() => {
              if (!isForceAtlas2Running && graphRef.current && rendererRef.current) {
                autoStartRef.current = true;
                toggleForceAtlas2();
                
                // Stop layout after 3 seconds
                setTimeout(() => {
                  if (isForceAtlas2Running && faWorkerRef.current) {
                    toggleForceAtlas2();
                  }
                }, 3000);
              }
            }, 500);
          }
        } else {
          console.error("No nodes found in graph data");
          setSigmaError("No valid nodes found in graph data");
        }
      } catch (error) {
        console.error("Error initializing graph:", error);
        setSigmaError(error.message);
      }
    }
    
    // Cleanup function
    return () => {
      console.log("Running cleanup in useEffect");
      
      // Skip cleanup if we're transitioning layouts or ForceAtlas2 is running
      if (layoutTransitionRef.current || isForceAtlas2Running) {
        console.log("Skipping cleanup during layout transition or while ForceAtlas2 is running");
        return;
      }
      
      if (rendererRef.current) {
        try {
          console.log("Killing renderer");
          rendererRef.current.kill();
          rendererRef.current = null;
        } catch (e) {
          console.error("Error killing renderer:", e);
        }
      }
      
      if (faWorkerRef.current) {
        try {
          console.log("Stopping ForceAtlas2 worker");
          // Cancel animation frame if it exists
          if (faWorkerRef.current.animationFrameId) {
            cancelAnimationFrame(faWorkerRef.current.animationFrameId);
          }
          faWorkerRef.current.stop();
          faWorkerRef.current = null;
          setIsForceAtlas2Running(false);
        } catch (e) {
          console.error("Error stopping ForceAtlas2 worker:", e);
        }
      }
      
      // Reset auto-start flag when component unmounts
      autoStartRef.current = false;
    };
  }, [graph_data, containerRef, nodeSize, showLabels, isForceAtlas2Running, memoizedColors]);

  // Improve WebGL context management
  useLayoutEffect(() => {
    // Ensure only one WebGL context is created by limiting canvas initialization
    if (graphRef.current && rendererRef.current && sigmaRef.current) {
      // If we already have a valid graph and renderer, ensure they stay connected
      console.log("Preserving existing Sigma graph connection");
      
      // Apply any canvas size changes without recreating the WebGL context
      const updateCanvasSize = () => {
        if (!sigmaRef.current) return;
        
        const rect = sigmaRef.current.getBoundingClientRect();
        const canvases = sigmaRef.current.querySelectorAll('canvas');
        
        canvases.forEach(canvas => {
          // Only update CSS dimensions, not the actual canvas dimensions
          // This avoids recreating the WebGL context
          canvas.style.width = `${rect.width}px`;
          canvas.style.height = `${rect.height}px`;
        });
        
        // Refresh the renderer without changing WebGL context
        try {
          rendererRef.current?.refresh();
        } catch (e) {
          console.error("Error refreshing renderer:", e);
        }
      };
      
      // Initial size update
      updateCanvasSize();
      
      // Set up resize observer for the container
      const observer = new ResizeObserver(() => {
        updateCanvasSize();
      });
      
      if (containerRef.current) {
        observer.observe(containerRef.current);
      }
      
      return () => {
        observer.disconnect();
      };
    }
  }, [graphRef.current, rendererRef.current, sigmaRef.current]);

  // Apply node size changes
  useEffect(() => {
    if (rendererRef.current && graphRef.current) {
      try {
        rendererRef.current.refresh();
      } catch (e) {
        console.error("Error applying node size:", e);
      }
    }
  }, [nodeSize]);

  // Apply label visibility changes
  useEffect(() => {
    if (rendererRef.current) {
      try {
        rendererRef.current.setSetting('labelRenderedSizeThreshold', showLabels ? 1 : 12);
        rendererRef.current.refresh();
      } catch (e) {
        console.error("Error toggling labels:", e);
      }
    }
  }, [showLabels]);

  // Update node size
  const handleNodeSizeChange = (e, newValue) => {
    setNodeSize(newValue);
  };

  // Toggle node labels
  const handleToggleLabels = () => {
    setShowLabels(!showLabels);
    
    if (rendererRef.current) {
      const renderer = rendererRef.current;
      // Update label threshold - if showLabels is true, show all labels, otherwise hide most
      renderer.setSetting('labelRenderedSizeThreshold', !showLabels ? 1 : 12);
      renderer.refresh();
    }
  };

  // Function to determine color based on modularity value
  const getModularityColor = (value) => {
    if (value >= 0.7) return 'success';
    if (value >= 0.4) return 'info';
    if (value >= 0.2) return 'warning';
    return 'error';
  };

  // Function to get tooltip text based on modularity value
  const getModularityTooltip = (value) => {
    if (value >= 0.7) return 'Very strong community structure';
    if (value >= 0.4) return 'Strong community structure';
    if (value >= 0.2) return 'Moderate community structure';
    return 'Weak community structure';
  };

  // Function to get descriptive text based on modularity value
  const getModularityInterpretation = (value) => {
    if (value >= 0.7) {
      return `This network has a very strong community structure (modularity: ${value.toFixed(3)}). The communities are clearly defined and well separated from each other.`;
    } else if (value >= 0.4) {
      return `This network has a strong community structure (modularity: ${value.toFixed(3)}). The communities are well defined with relatively few connections between different communities.`;
    } else if (value >= 0.2) {
      return `This network has a moderate community structure (modularity: ${value.toFixed(3)}). The communities can be identified but have significant connections between them.`;
    } else {
      return `This network has a weak community structure (modularity: ${value.toFixed(3)}). The communities are not well defined and have many connections between them.`;
    }
  };

  // Fix ForceAtlas2 implementation to ensure it runs properly
  const toggleForceAtlas2 = () => {
    // Log the current state before toggling
    console.log("Toggle ForceAtlas2 - Current state:", isForceAtlas2Running ? "running" : "stopped");
    
    // Check if renderer and graph are available
    if (!rendererRef.current || !graphRef.current) {
      console.error("Cannot toggle ForceAtlas2: renderer or graph is not available", {
        renderer: !!rendererRef.current,
        graph: !!graphRef.current
      });
      return;
    }
    
    // Set transition flag to prevent reinitialization
    layoutTransitionRef.current = true;
    
    if (isForceAtlas2Running) {
      // Stop the layout if it's running
      console.log("Stopping ForceAtlas2");
      try {
        // Ensure we have a valid worker before trying to stop
        if (faWorkerRef.current) {
          // Cancel animation frame first if it exists
          if (faWorkerRef.current.animationFrameId) {
            console.log("Canceling animation frame:", faWorkerRef.current.animationFrameId);
            cancelAnimationFrame(faWorkerRef.current.animationFrameId);
            faWorkerRef.current.animationFrameId = null;
          }
          
          faWorkerRef.current.stop();
          console.log("ForceAtlas2 worker stopped successfully");
          
          // Don't set to null to allow restarting with the same worker
          setIsForceAtlas2Running(false);
        } else {
          console.warn("No ForceAtlas2 worker found to stop");
        }
      } catch (e) {
        console.error("Error stopping ForceAtlas2:", e);
        // Still set running to false in case of error
        setIsForceAtlas2Running(false);
      }
    } else {
      // Start the layout if it's not running
      console.log("Starting ForceAtlas2");
      try {
        // Double check renderer and graph again
        if (!rendererRef.current || !graphRef.current) {
          console.error("Cannot start ForceAtlas2: renderer or graph missing");
          return;
        }
        
        // Create a new worker if it doesn't exist
        if (!faWorkerRef.current) {
          console.log("Creating new ForceAtlas2 worker");
          
          const settings = {
            linLogMode: false,
            outboundAttractionDistribution: false,
            adjustSizes: false,
            edgeWeightInfluence: 1,
            scalingRatio: 1,
            strongGravityMode: false,
            gravity: 1,
            slowDown: 2,
            barnesHutOptimize: true,
            barnesHutTheta: 0.5,
          };
          
          // Create worker directly instead of using a factory function
          try {
            faWorkerRef.current = new FA2Layout(graphRef.current, {
              settings: settings,
              getEdgeWeight: 'weight'
            });
            
            // Set up animation loop for layout
            let animationFrameId = null;
            
            const refreshFrame = () => {
              if (!rendererRef.current || !faWorkerRef.current) return;
              
              try {
                // Only refresh if the renderer exists
                rendererRef.current.refresh();
                
                // Continue the animation if layout is still running
                if (faWorkerRef.current && faWorkerRef.current.isRunning()) {
                  animationFrameId = requestAnimationFrame(refreshFrame);
                  faWorkerRef.current.animationFrameId = animationFrameId;
                }
              } catch (e) {
                console.error("Error in animation loop:", e);
                cancelAnimationFrame(animationFrameId);
              }
            };
            
            // Set to running state BEFORE starting the layout to prevent cleanup
            setIsForceAtlas2Running(true);
            
            // Start the worker after state update
            setTimeout(() => {
              if (faWorkerRef.current) {
                console.log("Starting ForceAtlas2 layout with delay");
                faWorkerRef.current.start();
                // Start animation loop
                animationFrameId = requestAnimationFrame(refreshFrame);
                
                // Store animation frame ID for cleanup
                faWorkerRef.current.animationFrameId = animationFrameId;
              }
            }, 100);
          } catch (err) {
            console.error("Error creating ForceAtlas2 worker:", err);
            faWorkerRef.current = null;
            setIsForceAtlas2Running(false);
          }
        } else {
          console.log("Using existing ForceAtlas2 worker");
          
          // Set to running state BEFORE starting the layout to prevent cleanup
          setIsForceAtlas2Running(true);
          
          // If worker exists, just start it (with small delay to ensure state is updated)
          setTimeout(() => {
            if (faWorkerRef.current) {
              faWorkerRef.current.start();
              
              // Set up animation loop for existing worker
              const refreshFrame = () => {
                if (!rendererRef.current || !faWorkerRef.current) return;
                
                try {
                  // Only refresh if the renderer exists
                  rendererRef.current.refresh();
                  
                  // Continue the animation if layout is still running
                  if (faWorkerRef.current && faWorkerRef.current.isRunning()) {
                    const newAnimationId = requestAnimationFrame(refreshFrame);
                    faWorkerRef.current.animationFrameId = newAnimationId;
                  }
                } catch (e) {
                  console.error("Error in animation loop:", e);
                  if (faWorkerRef.current && faWorkerRef.current.animationFrameId) {
                    cancelAnimationFrame(faWorkerRef.current.animationFrameId);
                  }
                }
              };
              
              // Start animation loop
              faWorkerRef.current.animationFrameId = requestAnimationFrame(refreshFrame);
            }
          }, 100);
        }
      } catch (e) {
        console.error("Error starting ForceAtlas2:", e);
        setIsForceAtlas2Running(false);
      }
    }
    
    // Reset transition flag after delay to allow state updates
    setTimeout(() => {
      layoutTransitionRef.current = false;
      console.log("Layout transition flag reset");
    }, 1000); // Increased timeout to ensure all operations complete
  };

  // Add download current visualization function
  const handleDownloadCurrentVisualization = useCallback(() => {
    if (!rendererRef.current || !containerRef.current || !sigmaRef.current) {
      console.error("Cannot download visualization: Renderer, container, or sigma ref not available");
      return;
    }

    try {
      // Try to use the direct Sigma method if available (ideal solution)
      let downloadSuccessful = false;
      
      // Try to access the Sigma renderer 
      // Different versions of Sigma have different APIs
      if (typeof rendererRef.current.refresh === 'function') {
        // Make sure the visualization is up to date
        rendererRef.current.refresh();
        
        // Try to access snapshot method
        const canvasRenderer = rendererRef.current.getCanvasRenderer?.() || 
                               rendererRef.current.getRenderer?.();
                               
        if (canvasRenderer && typeof canvasRenderer.snapshot === 'function') {
          console.log("Using Sigma's built-in snapshot method");
          // Sigma v2 provides a snapshot method to get the rendered graph
          const snapshot = canvasRenderer.snapshot({
            download: true,
            filename: 'community_visualization.png',
            background: 'white'
          });
          
          downloadSuccessful = true;
          console.log("Visualization downloaded using Sigma's built-in method");
        }
      }
      
      // If the direct method failed, use our canvas-based approach
      if (!downloadSuccessful) {
        console.log("Falling back to manual canvas capture method");
        
        // Get references to both container and Sigma container
        const container = containerRef.current;
        const sigmaContainer = sigmaRef.current;
        
        if (!container || !sigmaContainer) {
          console.error("Cannot download: Containers not found");
          return;
        }
        
        // Get all canvases in the Sigma container
        const canvases = sigmaContainer.querySelectorAll('canvas');
        
        if (!canvases || canvases.length === 0) {
          console.error("Cannot download: No canvas elements found");
          return;
        }
        
        // Get the container dimensions
        const containerRect = container.getBoundingClientRect();
        const width = containerRect.width;
        const height = containerRect.height;
        
        console.log(`Container dimensions: ${width}x${height}, Found ${canvases.length} canvases`);
        
        // Create a new canvas for the final image
        const outputCanvas = document.createElement('canvas');
        outputCanvas.width = width;
        outputCanvas.height = height;
        const outputCtx = outputCanvas.getContext('2d');
        
        // Fill with a white background
        outputCtx.fillStyle = 'white';
        outputCtx.fillRect(0, 0, width, height);
        
        // Draw each canvas in order
        console.log(`Drawing ${canvases.length} canvases to output`);
        Array.from(canvases).forEach((canvas, index) => {
          try {
            // Check if the canvas is empty or has content
            if (canvas.width > 0 && canvas.height > 0) {
              // Draw maintaining the aspect ratio
              outputCtx.drawImage(canvas, 0, 0, width, height);
              console.log(`Canvas ${index} drawn successfully`);
            } else {
              console.log(`Canvas ${index} skipped (empty/invalid dimensions)`);
            }
          } catch (e) {
            console.error(`Error drawing canvas ${index}:`, e);
          }
        });
        
        // Create a download link
        const link = document.createElement('a');
        link.download = 'community_visualization.png';
        link.href = outputCanvas.toDataURL('image/png');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log("Visualization downloaded successfully via manual method");
      }
      
      // Show success feedback
      setDownloadSuccess(true);
      setTimeout(() => {
        setDownloadSuccess(false);
      }, 2000);
    } catch (error) {
      console.error("Error downloading visualization:", error);
      alert("Failed to download the visualization: " + error.message);
    }
  }, [containerRef, sigmaRef, rendererRef]);

  // Add handleCenterView function
  const handleCenterView = useCallback(() => {
    if (rendererRef.current) {
      try {
        console.log("Centering the view");
        // Reset the camera to show the entire graph
        rendererRef.current.getCamera().animatedReset();
        rendererRef.current.refresh();
      } catch (e) {
        console.error("Error centering view:", e);
      }
    }
  }, [rendererRef]);

  return (
    <Paper sx={{ p: 4, borderRadius: 2, boxShadow: 3 }}>
      <style>{sigmaCanvasStyle}</style>
      
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" gutterBottom>
          Community Analysis
        </Typography>
        
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Tooltip title={getModularityTooltip(modularity)}>
                    <Chip 
              label={`Modularity: ${modularity.toFixed(3)}`} 
                      color={getModularityColor(modularity)} 
              sx={{ ml: 2 }}
              icon={<InfoIcon />}
                    />
                    </Tooltip>
                  </Box>
                </Box>
      
      <Divider sx={{ mb: 3 }} />
      
      <Grid container spacing={4} direction="column">
        {/* Bar chart - Full Width */}
        <Grid item xs={12}>
          <Card sx={{ minHeight: 400 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                  Community Size Distribution
                </Typography>
              </Box>
              
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={histogramData} margin={{ top: 10, right: 30, left: 30, bottom: 30 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="name"
                      interval={0} 
                      angle={-45} 
                      textAnchor="end" 
                      height={70} 
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis label={{ value: 'Size (nodes)', angle: -90, position: 'insideLeft' }} />
                    <RechartsTooltip formatter={(value, name) => [value, 'Nodes']} />
                    <Bar dataKey="size" nameKey="name">
                    {histogramData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>                                                                                                       
              </ResponsiveContainer>
              </Box>
              
              <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 3, justifyContent: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Number of communities: <strong>{num_communities}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Average community size: <strong>{mean_size}</strong> nodes
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Largest community: <strong>{max_size}</strong> nodes
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Smallest community: <strong>{min_size}</strong> nodes
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Interactive Graph - Full Width */}
        {graph_data && (
        <Grid item xs={12}>
            <Card sx={{ minHeight: 650 }}>
              <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
                  Interactive Community Visualization
                </Typography>
                
                {/* Control panel moved below the title */}
                <Box sx={{ 
                  display: 'flex', 
                  flexWrap: 'wrap', 
                  gap: 2, 
                  mb: 2,
                  bgcolor: 'rgba(0, 0, 0, 0.02)',
                  p: 2,
                  borderRadius: 2,
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained" 
                      size="small"
                      startIcon={downloadSuccess ? <CheckIcon /> : <DownloadIcon />}
                      onClick={handleDownloadCurrentVisualization}
                      disabled={!rendererRef.current || downloadSuccess}
                      color={downloadSuccess ? "success" : "primary"}
                      sx={{
                        boxShadow: 2,
                        '&:hover': {
                          boxShadow: 4
                        },
                        minWidth: '150px',
                        transition: 'all 0.3s ease'
                      }}
                    >
                      {downloadSuccess ? "Downloaded!" : "Save Current View"}
                    </Button>
                    
                    <Button
                      variant="outlined"
                      size="small"
                      color={isForceAtlas2Running ? "error" : "primary"}
                      onClick={toggleForceAtlas2}
                      startIcon={isForceAtlas2Running ? <PauseIcon /> : <PlayArrowIcon />}
                      sx={{ minWidth: '120px' }}
                    >
                      {isForceAtlas2Running ? "Stop Layout" : "Run Layout"}
                    </Button>
                    
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={handleCenterView}
                      startIcon={<CenterFocusStrongIcon />}
                      sx={{ minWidth: '120px' }}
                    >
                      Center View
                    </Button>
                  </Box>
                  
                  <Box sx={{ display: 'flex', gap: 3, alignItems: 'center', flexGrow: 1, justifyContent: 'flex-end' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: 250 }}>
                      <Typography variant="body2" sx={{ mr: 1, minWidth: '70px' }}>
                        Node Size:
                      </Typography>
                      <Slider
                        value={nodeSize}
                        min={0.5}
                        max={3}
                        step={0.1}
                        onChange={handleNodeSizeChange}
                        aria-labelledby="node-size-slider"
                        valueLabelDisplay="auto"
                        sx={{ ml: 1 }}
                      />
                    </Box>
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={showLabels}
                          onChange={handleToggleLabels}
                          color="primary"
                        />
                      }
                      label="Show Labels"
                    />
                  </Box>
                </Box>
                
                <Box sx={{ position: 'relative', flexGrow: 1, minHeight: 550 }}>
                  <div 
                    ref={containerRef}
                    style={{ 
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      border: '1px solid #eee',
                      borderRadius: 8,
                      overflow: 'hidden'
                    }}
                  >
                    <div
                      ref={sigmaRef}
                      style={{ 
                        width: '100%', 
                        height: '100%', 
                        position: 'relative',
                      }}
                    />
                  </div>
                  
                  {!sigmaLoaded && (
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0, 
                      bottom: 0, 
                      display: 'flex',
                      alignItems: 'center', 
                      justifyContent: 'center',
                      backgroundColor: 'rgba(255,255,255,0.7)',
                      zIndex: 10
                    }}>
                      <CircularProgress />
                    </div>
                  )}
                  
                  {sigmaError && (
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0, 
                      bottom: 0, 
                      display: 'flex',
                      alignItems: 'center', 
                      justifyContent: 'center',
                      backgroundColor: 'rgba(255,255,255,0.7)',
                      zIndex: 10
                    }}>
                      <Typography color="error">
                        Error loading graph: {sigmaError}
                      </Typography>
                    </div>
                  )}
                </Box>
                
                <Typography variant="body2" sx={{ mt: 2, textAlign: 'center', color: 'text.secondary' }}>
                  Interactive graph visualization with communities colored by clusters. 
                  Hover over nodes to see details and highlight connections.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          )}
        
        {/* Add modularity interpretation */}
        <Grid item xs={12}>
          <Box sx={{ 
            p: 2, 
            bgcolor: `${getModularityColor(modularity)}.light`, 
            borderRadius: 2,
            opacity: 0.9
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