import React, { forwardRef, useImperativeHandle, useRef, useEffect, useState, useCallback } from 'react';
import { Box, CircularProgress, Alert, AlertTitle } from '@mui/material';
import Graph from 'graphology';
import Sigma from 'sigma';
import { Coordinates, EdgeDisplayData, NodeDisplayData } from 'sigma/types';
import forceAtlas2 from 'graphology-layout-forceatlas2';
import FA2Layout from 'graphology-layout-forceatlas2/worker';

// Component to show during loading
const LoadingOverlay = ({ message }) => (
  <Box
    sx={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'rgba(255, 255, 255, 0.8)',
      zIndex: 2,
    }}
  >
    <CircularProgress size={40} thickness={5} sx={{ mb: 2 }} />
    <Box sx={{ mt: 2, maxWidth: '80%', textAlign: 'center' }}>
      {message}
    </Box>
  </Box>
);

// Check if container has valid dimensions
const hasValidDimensions = (element) => {
  if (!element) return false;
  
  const rect = element.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
};

// ForwardRef to expose methods to parent
const SigmaRenderer = forwardRef(({
  graphData,
  nodeSize,
  showLabels,
  onNodeSelect,
  isForceAtlas2Running,
  setIsForceAtlas2Running,
  graphDetail,
  isLarge,
  loading,
  error,
  setRendererReady
}, ref) => {
  // Refs
  const containerRef = useRef(null);
  const sigmaRef = useRef(null);
  const graphRef = useRef(null);
  const fa2WorkerRef = useRef(null);
  const resizeObserverRef = useRef(null);
  
  // State
  const [containerWidth, setContainerWidth] = useState(0);
  const [containerHeight, setContainerHeight] = useState(0);
  const [showWarning, setShowWarning] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('Loading graph data...');
  const [userHasInteracted, setUserHasInteracted] = useState(false);
  const [isVeryLarge, setIsVeryLarge] = useState(false);
  const [errorState, setErrorState] = useState(null);
  
  // Cleanup function to stop workers and free resources
  const cleanup = useCallback(() => {
    console.log('Running comprehensive cleanup to prevent duplication...');
    
    // Cancel any pending frames and timeouts
    if (fa2WorkerRef.current) {
      // Cancel animation frame
      if (fa2WorkerRef.current.animationFrameId) {
        try {
          cancelAnimationFrame(fa2WorkerRef.current.animationFrameId);
          console.log('Canceled animation frame');
        } catch (e) {
          console.error('Error canceling animation frame:', e);
        }
      }
      
      // Clear any resume timeouts
      if (fa2WorkerRef.current.resumeTimeout) {
        clearTimeout(fa2WorkerRef.current.resumeTimeout);
      }
      
      // Stop and kill ForceAtlas2 worker
      try {
        // Make sure it's stopped first
        if (fa2WorkerRef.current.isRunning) {
          fa2WorkerRef.current.stop();
        }
        fa2WorkerRef.current.kill();
        console.log('Stopped and killed ForceAtlas2 worker');
      } catch (e) {
        console.error('Error stopping ForceAtlas2 worker:', e);
      } finally {
        fa2WorkerRef.current = null;
      }
    }
    
    // Kill Sigma instance
    if (sigmaRef.current) {
      try {
        // Check if container still exists in the DOM before killing
        if (containerRef.current && document.body.contains(containerRef.current)) {
          // Remove all event listeners first to prevent memory leaks
          sigmaRef.current.getMouseCaptor()?.removeAllListeners?.();
          sigmaRef.current.getCamera()?.removeAllListeners?.();
          sigmaRef.current.removeAllListeners?.();
          
          // Kill the Sigma instance
          sigmaRef.current.kill();
          console.log('Killed Sigma instance');
        } else {
          console.log('Container not in DOM, skipping Sigma kill');
        }
      } catch (e) {
        console.error('Error killing Sigma instance:', e);
      } finally {
        sigmaRef.current = null;
      }
    }
    
    // Disconnect resize observer
    if (resizeObserverRef.current) {
      try {
        resizeObserverRef.current.disconnect();
        console.log('Disconnected resize observer');
      } catch (e) {
        console.error('Error disconnecting resize observer:', e);
      } finally {
        resizeObserverRef.current = null;
      }
    }
    
    // Clear graph reference
    if (graphRef.current) {
      try {
        graphRef.current.clear();
        console.log('Cleared graph');
      } catch (e) {
        console.error('Error clearing graph:', e);
      } finally {
        graphRef.current = null;
      }
    }
    
    // Reset state
    setIsForceAtlas2Running(false);
    
    // Reset renderer ready state
    if (setRendererReady) {
      setRendererReady(false);
    }
  }, [setIsForceAtlas2Running, setRendererReady]);

  // Functions for ForceAtlas2 management
  const startFA2 = useCallback(() => {
    if (!fa2WorkerRef.current) return;
    
    console.log('Starting ForceAtlas2 layout');
    fa2WorkerRef.current.start();
    setIsForceAtlas2Running(true);
    
    // Store initial state for use in pause/resume
    fa2WorkerRef.current.isRunning = true;
    fa2WorkerRef.current.isPaused = false;
    
    // Add pause and resume methods to worker
    fa2WorkerRef.current.pause = function() {
      if (this.isRunning && !this.isPaused) {
        this.isPaused = true;
        this.stop();
        console.log('ForceAtlas2 paused');
      }
    };
    
    fa2WorkerRef.current.resume = function() {
      if (this.isRunning && this.isPaused) {
        this.isPaused = false;
        this.start();
        console.log('ForceAtlas2 resumed');
      }
    };
    
    // Set up rendering loop
    let frame;
    const requestRender = () => {
      if (sigmaRef.current) {
        sigmaRef.current.refresh();
      }
      frame = requestAnimationFrame(requestRender);
    };
    
    frame = requestAnimationFrame(requestRender);
    fa2WorkerRef.current.animationFrameId = frame;
  }, [setIsForceAtlas2Running]);
  
  const stopFA2 = useCallback(() => {
    if (!fa2WorkerRef.current) return;
    
    console.log('Stopping ForceAtlas2 layout');
    
    // Cancel animation frame
    if (fa2WorkerRef.current.animationFrameId) {
      cancelAnimationFrame(fa2WorkerRef.current.animationFrameId);
    }
    
    // Clear any pending resume timeouts
    if (fa2WorkerRef.current.resumeTimeout) {
      clearTimeout(fa2WorkerRef.current.resumeTimeout);
    }
    
    fa2WorkerRef.current.stop();
    setIsForceAtlas2Running(false);
    
    // Update state tracking
    fa2WorkerRef.current.isRunning = false;
    fa2WorkerRef.current.isPaused = false;
  }, [setIsForceAtlas2Running]);
  
  const initFA2 = useCallback(() => {
    console.log(`Initializing ForceAtlas2 worker...`);
    
    if (!graphRef.current || !sigmaRef.current) {
      console.warn("Cannot initialize ForceAtlas2 - graph or sigma not available");
      return;
    }
    
    if (fa2WorkerRef.current) {
      console.log("FA2 worker already exists, stopping it first");
      fa2WorkerRef.current.kill();
      fa2WorkerRef.current = null;
    }
    
    try {
      const graph = graphRef.current;
      
      // Get node count for adaptive settings
      const nodeCount = graph.order;
      
      // Settings based on graph size
      const settings = {
        gravity: isVeryLarge ? 1.5 : (isLarge ? 0.8 : 0.1),
        scalingRatio: isVeryLarge ? 12 : (isLarge ? 10 : 4),
        slowDown: isVeryLarge ? 30 : (isLarge ? 15 : 5),
        barnesHutOptimize: true,
        barnesHutTheta: isVeryLarge ? 0.8 : (isLarge ? 0.7 : 0.5),
        adjustSizes: false,
        linLogMode: Boolean(isVeryLarge || isLarge), // Explicitly cast to boolean
        outboundAttractionDistribution: Boolean(isVeryLarge || isLarge), // Explicitly cast to boolean
        strongGravityMode: false,
        edgeWeightInfluence: 1,
      };
      
      console.log('Starting ForceAtlas2 worker with settings:', settings);
      
      // Create the FA2 worker with higher refresh rates to improve UI responsiveness
      fa2WorkerRef.current = new FA2Layout(graph, {
        settings,
        refreshRate: isVeryLarge ? 2000 : (isLarge ? 1000 : 500), // Slower refresh rates for better performance
      });
      
      // Start layout algorithm
      startFA2();
    } catch (error) {
      console.error('Error initializing ForceAtlas2:', error);
      setErrorState(`Failed to initialize ForceAtlas2: ${error.message}`);
    }
  }, [isVeryLarge, isLarge, setErrorState, startFA2]);
  
  // Expose methods to parent component
  useImperativeHandle(ref, () => ({
    getSigma: () => sigmaRef.current,
    getCamera: () => sigmaRef.current?.getCamera(),
    getGraph: () => graphRef.current,
    getContainer: () => containerRef.current,
    refresh: () => sigmaRef.current?.refresh(),
    startForceAtlas2: () => {
      if (sigmaRef.current && graphRef.current) {
        initFA2();
      }
    },
    toggleForceAtlas2: () => {
      if (!fa2WorkerRef.current) {
        initFA2();
      } else {
        if (fa2WorkerRef.current.isRunning) {
          stopFA2();
        } else {
          startFA2();
        }
      }
    },
    centerView: () => {
      if (sigmaRef.current) {
        sigmaRef.current.getCamera().animatedReset();
      }
    }
  }), [initFA2, startFA2, stopFA2]);
  
  // Initialize the graph from provided data
  const initGraph = useCallback(() => {
    if (!graphData || !graphData.nodes || !graphData.edges) {
      setLoadingMessage('No graph data available');
      return;
    }
    
    // Make sure container is available
    if (!containerRef.current || !document.body.contains(containerRef.current)) {
      console.error('Container ref is not available or not in DOM');
      setLoadingMessage('Error: Visualization container not available');
      return;
    }
    
    try {
      // Clean up previous instances
      cleanup();
      
      // Create a new graph
      const graph = new Graph();
      graphRef.current = graph;
      
      // Calculate graph size for adaptive settings
      const nodeCount = graphData.nodes.length;
      const edgeCount = graphData.edges.length;
      console.log(`Initializing graph with ${nodeCount} nodes and ${edgeCount} edges`);
      
      // Update the large/very large state based on graph size
      const newIsLarge = nodeCount > 1000 || edgeCount > 3000;
      const newIsVeryLarge = nodeCount > 5000 || edgeCount > 15000;
      
      // This value might be passed from the parent, but we can still calculate it here
      if (newIsVeryLarge !== isVeryLarge) {
        setIsVeryLarge(newIsVeryLarge);
      }
      
      // Set warning and loading message for large graphs
      if (newIsLarge) {
        setShowWarning(true);
        
        if (newIsVeryLarge) {
          setLoadingMessage(`Loading a very large graph with ${nodeCount.toLocaleString()} nodes and ${edgeCount.toLocaleString()} edges. This may take a while...`);
        } else {
          setLoadingMessage(`Loading a large graph with ${nodeCount.toLocaleString()} nodes and ${edgeCount.toLocaleString()} edges...`);
        }
      }
      
      // Adjust performance settings if large graph
      let adaptiveSettings = {};
      if (newIsVeryLarge) {
        console.log("Very large graph detected, applying performance optimizations");
        adaptiveSettings = {
          renderEdgeLabels: false, // Never render edge labels initially for better performance
          hideEdgesOnMove: true, // Always hide edges on move for better performance
          hideLabelsOnMove: true,
          labelRenderedSizeThreshold: 8, // Increased thresholds
          labelDensity: 0.05, // Lower density for better performance
          labelGridCellSize: 300, // Larger grid cell size
          enableEdgeHoverEvents: false, // Disable edge hover events for large graphs
          enableNodeHoverEvents: false, // Only disable node hover for very large graphs
        };
      } else if (newIsLarge) {
        console.log("Large graph detected, applying performance optimizations");
        adaptiveSettings = {
          renderEdgeLabels: false, // Never render edge labels initially for better performance
          hideEdgesOnMove: true, // Always hide edges on move for better performance
          hideLabelsOnMove: true,
          labelRenderedSizeThreshold: 5, // Increased thresholds
          labelDensity: 0.2, // Lower density for better performance
          labelGridCellSize: 200, // Larger grid cell size
          enableEdgeHoverEvents: false, // Disable edge hover events for large graphs
          enableNodeHoverEvents: false, // Only disable node hover for very large graphs
        };
      } else {
        console.log("Normal graph detected, using default settings");
        adaptiveSettings = {
          renderEdgeLabels: true,
          hideEdgesOnMove: false,
          hideLabelsOnMove: false,
          labelRenderedSizeThreshold: 2,
          labelDensity: 0.5,
          labelGridCellSize: 100,
          enableEdgeHoverEvents: true,
          enableNodeHoverEvents: true,
        };
      }
      
      // Signal that we're starting to add nodes
      setLoadingMessage(`Adding ${Math.min(10000, nodeCount)} nodes to the graph...`);
      
      // Add all nodes (respecting graphDetail percentage for decimation)
      const detailFactor = graphDetail / 100;
      const maxNodes = Math.min(10000, Math.ceil(nodeCount * detailFactor)); // Cap at 10k nodes
      const nodesToRender = nodeCount <= maxNodes ? graphData.nodes : graphData.nodes.slice(0, maxNodes);
      
      // Track node IDs that are actually added to the graph
      const addedNodeIds = new Set();
      
      nodesToRender.forEach(node => {
        // Type-based color assignment
        const isCore = node.type === 'C' || node.type === 'core' || node.typeAttribute === 'C';
        const color = isCore ? '#d32f2f' : '#1976d2';
        
        // Add node to graph
        graph.addNode(node.id, {
          ...node,
          x: node.x || Math.random(),
          y: node.y || Math.random(),
          size: nodeSize,
          color: color,
          label: node.label || node.id,
          // For Sigma rendering, use 'circle' type
          type: 'circle',
          // Store our custom attributes
          isCore: isCore,
        });
        
        addedNodeIds.add(node.id);
      });
      
      // Signal that we're starting to add edges
      setLoadingMessage(`Adding edges to the graph...`);
      
      // Add edges (only for nodes that exist in the graph)
      graphData.edges.forEach(edge => {
        if (addedNodeIds.has(edge.source) && addedNodeIds.has(edge.target)) {
          // Determine edge color based on node types
          const sourceIsCore = graph.getNodeAttribute(edge.source, 'isCore');
          const targetIsCore = graph.getNodeAttribute(edge.target, 'isCore');
          
          let color;
          if (sourceIsCore && targetIsCore) {
            color = '#d32f2f'; // Core-Core: Red
          } else if (!sourceIsCore && !targetIsCore) {
            color = '#1976d2'; // Periphery-Periphery: Blue
          } else {
            color = '#9c27b0'; // Core-Periphery: Purple
          }
          
          // Add edge to graph
          graph.addEdge(edge.source, edge.target, {
            ...edge,
            size: 1,
            color: color,
          });
        }
      });
      
      console.log(`Graph initialized with ${graph.order} nodes and ${graph.size} edges`);
      setLoadingMessage(`Creating visualization renderer...`);
      
      // Verify container is still in DOM before creating Sigma
      if (!containerRef.current || !document.body.contains(containerRef.current)) {
        console.error('Container was removed from DOM during initialization');
        return;
      }
      
      // Create a new Sigma instance
      sigmaRef.current = new Sigma(graph, containerRef.current, {
        ...adaptiveSettings,
        minCameraRatio: 0.05, // Allow more zoom in
        maxCameraRatio: 20,   // Allow more zoom out
        renderLabels: showLabels,
        defaultNodeColor: '#999',
        defaultEdgeColor: '#ddd',
        edgeLabelSize: 10,
        allowInvalidContainer: true, // Allow initialization even if container dimensions aren't ready yet
        // Enable smoother camera animations for zoom/pan
        cameraSmoothingAnimation: {
          enabled: true,
          duration: 150,
          easing: 'cubic-bezier(0.25, 0.1, 0.25, 1)'
        },
        // Configure mouse interaction settings
        mouseWheelSensitivity: 1.2,
        nodeReducer: (node, data) => {
          const res = { ...data };
          
          // Highlight connected nodes when a node is hovered
          if (data.highlighted) {
            res.color = '#ff5722'; // Highlight color
            res.zIndex = 1;
          } else if (data.lowlighted) {
            res.color = '#e0e0e0'; // Gray out disconnected nodes
            res.zIndex = 0;
          }
          
          // Apply size based on the nodeSize setting
          res.size = data.size = nodeSize;
          
          // Hide nodes if needed
          if (data.hidden) {
            res.size = 0;
            res.label = '';
            res.hidden = true;
          }
          
          return res;
        },
        edgeReducer: (edge, data) => {
          const res = { ...data };
          
          // Highlight or lowlight edges when a node is hovered
          if (data.highlighted) {
            res.color = '#ff5722'; // Highlight color
            res.zIndex = 1;
            res.size = 2;
          } else if (data.lowlighted) {
            res.color = '#f0f0f0'; // Gray out disconnected edges
            res.size = 0.5;
            res.zIndex = 0;
          }
          
          return res;
        }
      });
      
      setLoadingMessage(`Applying initial layout...`);
      
      // Immediately set renderer as ready when Sigma is created
      if (setRendererReady) {
        // Short delay to allow the UI to update before reporting ready
        setTimeout(() => {
          console.log('Setting renderer ready state to true');
          setRendererReady(true);
        }, 100);
      }
      
      // Add event listeners
      sigmaRef.current.on('clickNode', ({ node }) => {
        if (onNodeSelect && typeof onNodeSelect === 'function') {
          const nodeData = graph.getNodeAttributes(node);
          onNodeSelect(nodeData);
        }
      });
      
      sigmaRef.current.on('clickStage', () => {
        if (onNodeSelect && typeof onNodeSelect === 'function') {
          onNodeSelect(null); // Deselect when clicking on empty space
        }
      });
      
      // Keep track of camera changes to know if user is panning/zooming
      let lastCameraState = sigmaRef.current.getCamera().getState();
      let userInteracting = false;
      
      // Track when user starts interacting with the graph
      sigmaRef.current.getMouseCaptor().on('mousedown', () => {
        userInteracting = true;
        setUserHasInteracted(true); // Remember that user has interacted
      });
      
      sigmaRef.current.getMouseCaptor().on('mouseup', () => {
        setTimeout(() => {
          userInteracting = false;
        }, 300); // Small delay to ensure we capture any momentum-based movements
      });
      
      // Handle touch events for mobile
      sigmaRef.current.getTouchCaptor().on('touchstart', () => {
        userInteracting = true;
      });
      
      sigmaRef.current.getTouchCaptor().on('touchend', () => {
        setTimeout(() => {
          userInteracting = false;
        }, 300);
      });
      
      sigmaRef.current.getCamera().on('updated', () => {
        const currentState = sigmaRef.current.getCamera().getState();
        
        // Only act on significant camera movements
        const hasMoved = 
          Math.abs(currentState.x - lastCameraState.x) > 0.01 || 
          Math.abs(currentState.y - lastCameraState.y) > 0.01 ||
          Math.abs(currentState.ratio - lastCameraState.ratio) > 0.01;
        
        if (hasMoved) {
          // Only pause ForceAtlas2 when the user is actively interacting
          if (userInteracting && fa2WorkerRef.current && isForceAtlas2Running) {
            // Pause layout while user is navigating
            fa2WorkerRef.current.pause();
            
            // Resume after a delay with no camera movement
            clearTimeout(fa2WorkerRef.current.resumeTimeout);
            fa2WorkerRef.current.resumeTimeout = setTimeout(() => {
              if (!userInteracting && fa2WorkerRef.current && isForceAtlas2Running) {
                fa2WorkerRef.current.resume();
              }
            }, 1000); // Longer delay to ensure navigation is complete
          }
        }
        
        lastCameraState = currentState;
      });
      
      // Node hover effects
      sigmaRef.current.on('enterNode', ({ node }) => {
        // Highlight the node and its connections
        const connectedNodes = new Set();
        graph.forEachNeighbor(node, (neighbor) => {
          connectedNodes.add(neighbor);
          graph.setNodeAttribute(neighbor, 'highlighted', true);
          
          // Highlight the edges
          graph.forEachEdge(node, neighbor, (edge) => {
            graph.setEdgeAttribute(edge, 'highlighted', true);
          });
        });
        
        // Lowlight disconnected nodes and edges
        graph.forEachNode((n) => {
          if (n !== node && !connectedNodes.has(n)) {
            graph.setNodeAttribute(n, 'lowlighted', true);
          }
        });
        
        graph.forEachEdge((e) => {
          const source = graph.source(e);
          const target = graph.target(e);
          if (source !== node && target !== node) {
            graph.setEdgeAttribute(e, 'lowlighted', true);
          }
        });
        
        // Also highlight the hovered node
        graph.setNodeAttribute(node, 'highlighted', true);
        
        // Refresh the rendering
        sigmaRef.current.refresh();
      });
      
      sigmaRef.current.on('leaveNode', () => {
        // Reset all nodes and edges
        graph.forEachNode((n) => {
          graph.setNodeAttribute(n, 'highlighted', false);
          graph.setNodeAttribute(n, 'lowlighted', false);
        });
        
        graph.forEachEdge((e) => {
          graph.setEdgeAttribute(e, 'highlighted', false);
          graph.setEdgeAttribute(e, 'lowlighted', false);
        });
        
        // Refresh the rendering
        sigmaRef.current.refresh();
      });
      
      // Apply initial ForceAtlas2 layout with static iterations 
      if (nodeCount > 0) {
        let staticIterations = 0;
        let staticSettings = {};
        
        // Determine iterations and settings based on graph size
        if (newIsVeryLarge) {
          staticIterations = 20; // Reduced from 50 for faster initial rendering
          staticSettings = {
            gravity: 1.8, // Increased gravity to prevent node dispersion
            scalingRatio: 8,
            slowDown: 40, // Increased slowDown for stability
            edgeWeightInfluence: 1,
            barnesHutOptimize: true,
            barnesHutTheta: 0.9, // More optimization
            linLogMode: true, // Explicitly boolean
            outboundAttractionDistribution: true, // Explicitly boolean
            adjustSizes: false,
          };
        } else if (newIsLarge) {
          staticIterations = 30; // Reduced from 75 for faster initial rendering
          staticSettings = {
            gravity: 1.0,
            scalingRatio: 8,
            slowDown: 20,
            edgeWeightInfluence: 1,
            barnesHutOptimize: true,
            barnesHutTheta: 0.8,
            linLogMode: true, // Explicitly boolean
            outboundAttractionDistribution: true, // Add this setting with explicit boolean
          };
        } else {
          staticIterations = 50; // Reduced from 150 for faster initial rendering
          staticSettings = {
            gravity: 0.2,
            scalingRatio: 4,
            slowDown: 10,
            edgeWeightInfluence: 1,
            linLogMode: false, // Add with explicit boolean
            outboundAttractionDistribution: false, // Add with explicit boolean
          };
        }
        
        console.log(`Applying initial ForceAtlas2 layout with ${staticIterations} iterations`);
        forceAtlas2.assign(graph, { iterations: staticIterations, settings: staticSettings });
        
        // Force a rendering refresh
        sigmaRef.current.refresh();
        
        // Center the camera only on initial load, not after user interaction
        if (!userHasInteracted) {
          sigmaRef.current.getCamera().animatedReset();
        }
      }
      
      console.log('Sigma instance created');
      
    } catch (error) {
      console.error('Error initializing graph:', error);
      setErrorState(`Failed to initialize graph visualization: ${error.message}`);
      
      // Clean up any partial initialization
      cleanup();
    }
  }, [
    graphData, 
    cleanup,
    setLoadingMessage, 
    containerRef, 
    setRendererReady, 
    nodeSize, 
    showLabels, 
    isLarge,
    isVeryLarge,
    setIsForceAtlas2Running,
    onNodeSelect,
    userHasInteracted,
    setErrorState,
    setShowWarning,
    graphDetail
  ]);
  
  // Handle container resize
  useEffect(() => {
    if (!containerRef.current) return;
    
    // Set up resize observer to update container dimensions
    resizeObserverRef.current = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      setContainerWidth(width);
      setContainerHeight(height);
      
      // Refresh Sigma if available
      if (sigmaRef.current) {
        sigmaRef.current.refresh();
      }
    });
    
    resizeObserverRef.current.observe(containerRef.current);
    
    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
      }
    };
  }, []);
  
  // Effect for updating graph with new settings
  useEffect(() => {
    if (sigmaRef.current) {
      // Update node size
      if (graphRef.current) {
        graphRef.current.forEachNode((node) => {
          graphRef.current.setNodeAttribute(node, 'size', nodeSize);
        });
      }
      
      // Update label visibility
      sigmaRef.current.setSettings({ renderLabels: showLabels });
      
      // Refresh the rendering
      sigmaRef.current.refresh();
    }
  }, [nodeSize, showLabels]);
  
  // Initialize or update graph when data changes
  useEffect(() => {
    if (graphData) {
      // Delay graph initialization slightly to ensure container is ready
      const timer = setTimeout(() => {
        // Double check that container has dimensions before initializing
        if (containerRef.current) {
          const rect = containerRef.current.getBoundingClientRect();
          console.log(`Container dimensions: ${rect.width}x${rect.height}`);
          
          if (rect.width > 0 && rect.height > 0) {
            initGraph();
          } else {
            console.warn("Container has zero dimensions, delaying graph initialization");
            // Try again in a moment with a more significant delay
            setTimeout(initGraph, 500);
          }
        }
      }, 100);
      
      return () => {
        clearTimeout(timer);
        cleanup();
      };
    }
    
    return () => {
      cleanup();
    };
  }, [graphData, initGraph, cleanup]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);
  
  // Set internal loading state when component mounts or loading prop changes
  useEffect(() => {
    if (graphData && !sigmaRef.current) {
      // If we have graph data but no sigma instance yet, show loading overlay
      setLoadingMessage('Initializing graph renderer...');
    }
  }, [graphData]);
  
  // Add useEffect hook to ensure container is visible and has valid dimensions
  useEffect(() => {
    if (!containerRef.current) return;
    
    // Track previous dimensions to detect actual changes
    let prevWidth = 0;
    let prevHeight = 0;
    
    // Check if container has valid dimensions
    const checkContainerDimensions = () => {
      if (hasValidDimensions(containerRef.current)) {
        const rect = containerRef.current.getBoundingClientRect();
        const currentWidth = rect.width;
        const currentHeight = rect.height;
        
        // Only reset camera if the dimensions have actually changed significantly
        if (sigmaRef.current && 
            (Math.abs(currentWidth - prevWidth) > 5 || Math.abs(currentHeight - prevHeight) > 5)) {
          console.log('Container dimensions changed significantly, refreshing Sigma');
          sigmaRef.current.refresh();
          
          // Update the previous dimensions
          prevWidth = currentWidth;
          prevHeight = currentHeight;
        }
      }
    };
    
    // Check dimensions initially
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      prevWidth = rect.width;
      prevHeight = rect.height;
    }
    
    // Set up a mutation observer to detect changes to the container or its parents
    // but only refresh - don't reset the camera position
    const observer = new MutationObserver(() => {
      checkContainerDimensions();
    });
    
    // Observe only the container and its attributes, not the entire document
    observer.observe(containerRef.current, { 
      attributes: true,
      attributeFilter: ['style', 'class']
    });
    
    // Use a less frequent periodic check to catch resize events
    const interval = setInterval(checkContainerDimensions, 2000);
    
    return () => {
      observer.disconnect();
      clearInterval(interval);
    };
  }, []);
  
  return (
    <Box 
      ref={containerRef}
      sx={{ 
        height: '500px', 
        width: '100%',
        minHeight: '500px',
        minWidth: '300px',
        position: 'relative',
        borderRadius: 1,
        overflow: 'hidden',
        border: '1px solid rgba(0, 0, 0, 0.12)',
        backgroundColor: '#fafafa',
        // Force immediate rendering with explicit dimensions
        display: 'block',
        boxSizing: 'border-box'
      }}
      className="sigma-container"
    >
      {loading && <LoadingOverlay message={loadingMessage} />}
      
      {error && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 3,
          }}
        >
          <Alert severity="error" sx={{ width: '100%', maxWidth: 500 }}>
            <AlertTitle>Error loading graph</AlertTitle>
            {error}
          </Alert>
        </Box>
      )}
      
      {showWarning && !loading && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 8,
            right: 8,
            zIndex: 5,
            maxWidth: '400px', // Make it smaller
          }}
        >
          <Alert 
            severity="info" 
            variant="outlined"
            sx={{ boxShadow: 1, fontSize: '0.85rem', opacity: 0.85 }}
            onClose={() => setShowWarning(false)} // Make it dismissible
          >
            <AlertTitle>Large Graph Information</AlertTitle>
            {graphRef.current && (
              <>
                <p>Graph loaded: {graphRef.current.order.toLocaleString()} nodes and {graphRef.current.size.toLocaleString()} edges.</p>
                <ul style={{ margin: 0, paddingLeft: 16 }}>
                  <li>Click 'Start Layout' to apply ForceAtlas2</li>
                  <li>Use mouse wheel to zoom, drag to pan</li>
                </ul>
              </>
            )}
          </Alert>
        </Box>
      )}
    </Box>
  );
});

export default SigmaRenderer; 