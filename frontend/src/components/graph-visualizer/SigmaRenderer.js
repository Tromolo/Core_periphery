import React, { forwardRef, useImperativeHandle, useRef, useEffect, useState, useCallback } from 'react';
import { Box, CircularProgress, Alert, AlertTitle } from '@mui/material';
import Graph from 'graphology';
import Sigma from 'sigma';
import { Coordinates, EdgeDisplayData, NodeDisplayData } from 'sigma/types';
import forceAtlas2 from 'graphology-layout-forceatlas2';
import FA2Layout from 'graphology-layout-forceatlas2/worker';

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

const hasValidDimensions = (element) => {
  if (!element) return false;
  
  const rect = element.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
};

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
  const containerRef = useRef(null);
  const sigmaRef = useRef(null);
  const graphRef = useRef(null);
  const fa2WorkerRef = useRef(null);
  const resizeObserverRef = useRef(null);
  
  const [containerWidth, setContainerWidth] = useState(0);
  const [containerHeight, setContainerHeight] = useState(0);
  const [showWarning, setShowWarning] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('Loading graph data...');
  const [userHasInteracted, setUserHasInteracted] = useState(false);
  const [isVeryLarge, setIsVeryLarge] = useState(false);
  const [errorState, setErrorState] = useState(null);
  
  const cleanup = useCallback(() => {
    console.log('Running comprehensive cleanup to prevent duplication...');
    
    if (fa2WorkerRef.current) {
      if (fa2WorkerRef.current.animationFrameId) {
        try {
          cancelAnimationFrame(fa2WorkerRef.current.animationFrameId);
          console.log('Canceled animation frame');
        } catch (e) {
          console.error('Error canceling animation frame:', e);
        }
      }
      
      if (fa2WorkerRef.current.resumeTimeout) {
        clearTimeout(fa2WorkerRef.current.resumeTimeout);
      }
      
      try {
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
    
    if (sigmaRef.current) {
      try {
        if (containerRef.current && document.body.contains(containerRef.current)) {
          sigmaRef.current.getMouseCaptor()?.removeAllListeners?.();
          sigmaRef.current.getCamera()?.removeAllListeners?.();
          sigmaRef.current.removeAllListeners?.();
          
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
    
    setIsForceAtlas2Running(false);
    
    if (setRendererReady) {
      setRendererReady(false);
    }
  }, [setIsForceAtlas2Running, setRendererReady]);

  const startFA2 = useCallback(() => {
    if (!fa2WorkerRef.current) return;
    
    console.log('Starting ForceAtlas2 layout');
    fa2WorkerRef.current.start();
    setIsForceAtlas2Running(true);
    
    fa2WorkerRef.current.isRunning = true;
    fa2WorkerRef.current.isPaused = false;
    
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
    
    if (fa2WorkerRef.current.animationFrameId) {
      cancelAnimationFrame(fa2WorkerRef.current.animationFrameId);
    }
    
    if (fa2WorkerRef.current.resumeTimeout) {
      clearTimeout(fa2WorkerRef.current.resumeTimeout);
    }
    
    fa2WorkerRef.current.stop();
    setIsForceAtlas2Running(false);
    
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
      
      const nodeCount = graph.order;
      
      const settings = {
        gravity: isVeryLarge ? 1.5 : (isLarge ? 0.8 : 0.1),
        scalingRatio: isVeryLarge ? 12 : (isLarge ? 10 : 4),
        slowDown: isVeryLarge ? 30 : (isLarge ? 15 : 5),
        barnesHutOptimize: true,
        barnesHutTheta: isVeryLarge ? 0.8 : (isLarge ? 0.7 : 0.5),
        adjustSizes: false,
        linLogMode: Boolean(isVeryLarge || isLarge),
        outboundAttractionDistribution: Boolean(isVeryLarge || isLarge),
        strongGravityMode: false,
        edgeWeightInfluence: 1,
      };
      
      console.log('Starting ForceAtlas2 worker with settings:', settings);
      
      fa2WorkerRef.current = new FA2Layout(graph, {
        settings,
        refreshRate: isVeryLarge ? 2000 : (isLarge ? 1000 : 500),
      });
      
      startFA2();
    } catch (error) {
      console.error('Error initializing ForceAtlas2:', error);
      setErrorState(`Failed to initialize ForceAtlas2: ${error.message}`);
    }
  }, [isVeryLarge, isLarge, setErrorState, startFA2]);
  
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
  
  const initGraph = useCallback(() => {
    if (!graphData || !graphData.nodes || !graphData.edges) {
      setLoadingMessage('No graph data available');
      return;
    }
    
    if (!containerRef.current || !document.body.contains(containerRef.current)) {
      console.error('Container ref is not available or not in DOM');
      setLoadingMessage('Error: Visualization container not available');
      return;
    }
    
    try {
      cleanup();
      
      const graph = new Graph();
      graphRef.current = graph;
      
      const nodeCount = graphData.nodes.length;
      const edgeCount = graphData.edges.length;
      console.log(`Initializing graph with ${nodeCount} nodes and ${edgeCount} edges`);
      
      const newIsLarge = nodeCount > 1000 || edgeCount > 3000;
      const newIsVeryLarge = nodeCount > 5000 || edgeCount > 15000;
      
      if (newIsVeryLarge !== isVeryLarge) {
        setIsVeryLarge(newIsVeryLarge);
      }
      
      if (newIsLarge) {
        setShowWarning(true);
        
        if (newIsVeryLarge) {
          setLoadingMessage(`Loading a very large graph with ${nodeCount.toLocaleString()} nodes and ${edgeCount.toLocaleString()} edges. This may take a while...`);
        } else {
          setLoadingMessage(`Loading a large graph with ${nodeCount.toLocaleString()} nodes and ${edgeCount.toLocaleString()} edges...`);
        }
      }
      
      let adaptiveSettings = {};
      if (newIsVeryLarge) {
        console.log("Very large graph detected, applying performance optimizations");
        adaptiveSettings = {
          renderEdgeLabels: false,
          hideEdgesOnMove: true,
          hideLabelsOnMove: true,
          labelRenderedSizeThreshold: 8,
          labelDensity: 0.05,
          labelGridCellSize: 300,
          enableEdgeHoverEvents: false,
          enableNodeHoverEvents: false,
        };
      } else if (newIsLarge) {
        console.log("Large graph detected, applying performance optimizations");
        adaptiveSettings = {
          renderEdgeLabels: false,
          hideEdgesOnMove: true,
          hideLabelsOnMove: true,
          labelRenderedSizeThreshold: 5,
          labelDensity: 0.2,
          labelGridCellSize: 200,
          enableEdgeHoverEvents: false,
          enableNodeHoverEvents: false,
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
      
      setLoadingMessage(`Adding ${Math.min(10000, nodeCount)} nodes to the graph...`);
      
      const detailFactor = graphDetail / 100;
      const maxNodes = Math.min(10000, Math.ceil(nodeCount * detailFactor));
      const nodesToRender = nodeCount <= maxNodes ? graphData.nodes : graphData.nodes.slice(0, maxNodes);
      
      const addedNodeIds = new Set();
      
      nodesToRender.forEach(node => {
        const isCore = node.type === 'C' || node.type === 'core' || node.typeAttribute === 'C';
        const color = isCore ? '#d32f2f' : '#1976d2';
        
        graph.addNode(node.id, {
          ...node,
          x: node.x || Math.random(),
          y: node.y || Math.random(),
          size: nodeSize,
          color: color,
          label: node.label || node.id,
          type: 'circle',
          isCore: isCore,
        });
        
        addedNodeIds.add(node.id);
      });
      
      setLoadingMessage(`Adding edges to the graph...`);
      
      graphData.edges.forEach(edge => {
        if (addedNodeIds.has(edge.source) && addedNodeIds.has(edge.target)) {
          const sourceIsCore = graph.getNodeAttribute(edge.source, 'isCore');
          const targetIsCore = graph.getNodeAttribute(edge.target, 'isCore');
          
          let color;
          if (sourceIsCore && targetIsCore) {
            color = '#d32f2f';
          } else if (!sourceIsCore && !targetIsCore) {
            color = '#1976d2';
          } else {
            color = '#9c27b0';
          }
          
          graph.addEdge(edge.source, edge.target, {
            ...edge,
            size: 1,
            color: color,
          });
        }
      });
      
      console.log(`Graph initialized with ${graph.order} nodes and ${graph.size} edges`);
      setLoadingMessage(`Creating visualization renderer...`);
      
      if (!containerRef.current || !document.body.contains(containerRef.current)) {
        console.error('Container was removed from DOM during initialization');
        return;
      }
      
      sigmaRef.current = new Sigma(graph, containerRef.current, {
        ...adaptiveSettings,
        minCameraRatio: 0.05,
        maxCameraRatio: 20,
        renderLabels: showLabels,
        defaultNodeColor: '#999',
        defaultEdgeColor: '#ddd',
        edgeLabelSize: 10,
        allowInvalidContainer: true,
        cameraSmoothingAnimation: {
          enabled: true,
          duration: 150,
          easing: 'cubic-bezier(0.25, 0.1, 0.25, 1)'
        },
        mouseWheelSensitivity: 1.2,
        nodeReducer: (node, data) => {
          const res = { ...data };
          
          if (data.highlighted) {
            res.color = '#ff5722';
            res.zIndex = 1;
          } else if (data.lowlighted) {
            res.color = '#e0e0e0';
            res.zIndex = 0;
          }
          
          res.size = data.size = nodeSize;
          
          if (data.hidden) {
            res.size = 0;
            res.label = '';
            res.hidden = true;
          }
          
          return res;
        },
        edgeReducer: (edge, data) => {
          const res = { ...data };
          
          if (data.highlighted) {
            res.color = '#ff5722';
            res.zIndex = 1;
            res.size = 2;
          } else if (data.lowlighted) {
            res.color = '#f0f0f0';
            res.size = 0.5;
            res.zIndex = 0;
          }
          
          return res;
        }
      });
      
      setLoadingMessage(`Applying initial layout...`);
      
      if (setRendererReady) {
        setTimeout(() => {
          console.log('Setting renderer ready state to true');
          setRendererReady(true);
        }, 100);
      }
      
      sigmaRef.current.on('clickNode', ({ node }) => {
        if (onNodeSelect && typeof onNodeSelect === 'function') {
          const nodeData = graph.getNodeAttributes(node);
          onNodeSelect(nodeData);
        }
      });
      
      sigmaRef.current.on('clickStage', () => {
        if (onNodeSelect && typeof onNodeSelect === 'function') {
          onNodeSelect(null);
        }
      });
      
      let lastCameraState = sigmaRef.current.getCamera().getState();
      let userInteracting = false;
      
      sigmaRef.current.getMouseCaptor().on('mousedown', () => {
        userInteracting = true;
        setUserHasInteracted(true);
      });
      
      sigmaRef.current.getMouseCaptor().on('mouseup', () => {
        setTimeout(() => {
          userInteracting = false;
        }, 300);
      });
      
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
        
        const hasMoved = 
          Math.abs(currentState.x - lastCameraState.x) > 0.01 || 
          Math.abs(currentState.y - lastCameraState.y) > 0.01 ||
          Math.abs(currentState.ratio - lastCameraState.ratio) > 0.01;
        
        if (hasMoved) {
          if (userInteracting && fa2WorkerRef.current && isForceAtlas2Running) {
            fa2WorkerRef.current.pause();
            
            clearTimeout(fa2WorkerRef.current.resumeTimeout);
            fa2WorkerRef.current.resumeTimeout = setTimeout(() => {
              if (!userInteracting && fa2WorkerRef.current && isForceAtlas2Running) {
                fa2WorkerRef.current.resume();
              }
            }, 1000);
          }
        }
        
        lastCameraState = currentState;
      });
      
      sigmaRef.current.on('enterNode', ({ node }) => {
        const connectedNodes = new Set();
        graph.forEachNeighbor(node, (neighbor) => {
          connectedNodes.add(neighbor);
          graph.setNodeAttribute(neighbor, 'highlighted', true);
          
          graph.forEachEdge(node, neighbor, (edge) => {
            graph.setEdgeAttribute(edge, 'highlighted', true);
          });
        });
        
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
        
        graph.setNodeAttribute(node, 'highlighted', true);
        
        sigmaRef.current.refresh();
      });
      
      sigmaRef.current.on('leaveNode', () => {
        graph.forEachNode((n) => {
          graph.setNodeAttribute(n, 'highlighted', false);
          graph.setNodeAttribute(n, 'lowlighted', false);
        });
        
        graph.forEachEdge((e) => {
          graph.setEdgeAttribute(e, 'highlighted', false);
          graph.setEdgeAttribute(e, 'lowlighted', false);
        });
        
        sigmaRef.current.refresh();
      });
      
      if (nodeCount > 0) {
        let staticIterations = 0;
        let staticSettings = {};
        
        if (newIsVeryLarge) {
          staticIterations = 20;
          staticSettings = {
            gravity: 1.8,
            scalingRatio: 8,
            slowDown: 40,
            edgeWeightInfluence: 1,
            barnesHutOptimize: true,
            barnesHutTheta: 0.9,
            linLogMode: true,
            outboundAttractionDistribution: true,
            adjustSizes: false,
          };
        } else if (newIsLarge) {
          staticIterations = 30;
          staticSettings = {
            gravity: 1.0,
            scalingRatio: 8,
            slowDown: 20,
            edgeWeightInfluence: 1,
            barnesHutOptimize: true,
            barnesHutTheta: 0.8,
            linLogMode: true,
            outboundAttractionDistribution: true,
          };
        } else {
          staticIterations = 50;
          staticSettings = {
            gravity: 0.2,
            scalingRatio: 4,
            slowDown: 10,
            edgeWeightInfluence: 1,
            linLogMode: false,
            outboundAttractionDistribution: false,
          };
        }
        
        console.log(`Applying initial ForceAtlas2 layout with ${staticIterations} iterations`);
        forceAtlas2.assign(graph, { iterations: staticIterations, settings: staticSettings });
        
        sigmaRef.current.refresh();
        
        if (!userHasInteracted) {
          sigmaRef.current.getCamera().animatedReset();
        }
      }
      
      console.log('Sigma instance created');
      
    } catch (error) {
      console.error('Error initializing graph:', error);
      setErrorState(`Failed to initialize graph visualization: ${error.message}`);
      
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
  
  useEffect(() => {
    if (!containerRef.current) return;
    
    resizeObserverRef.current = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      setContainerWidth(width);
      setContainerHeight(height);
      
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
  
  useEffect(() => {
    if (sigmaRef.current) {
      if (graphRef.current) {
        graphRef.current.forEachNode((node) => {
          graphRef.current.setNodeAttribute(node, 'size', nodeSize);
        });
      }
      
      sigmaRef.current.setSettings({ renderLabels: showLabels });
      
      sigmaRef.current.refresh();
    }
  }, [nodeSize, showLabels]);
  
  useEffect(() => {
    if (graphData) {
      const timer = setTimeout(() => {
        if (containerRef.current) {
          const rect = containerRef.current.getBoundingClientRect();
          console.log(`Container dimensions: ${rect.width}x${rect.height}`);
          
          if (rect.width > 0 && rect.height > 0) {
            initGraph();
          } else {
            console.warn("Container has zero dimensions, delaying graph initialization");
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
  
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);
  
  useEffect(() => {
    if (graphData && !sigmaRef.current) {
      setLoadingMessage('Initializing graph renderer...');
    }
  }, [graphData]);
  
  useEffect(() => {
    if (!containerRef.current) return;
    
    let prevWidth = 0;
    let prevHeight = 0;
    
    const checkContainerDimensions = () => {
      if (hasValidDimensions(containerRef.current)) {
        const rect = containerRef.current.getBoundingClientRect();
        const currentWidth = rect.width;
        const currentHeight = rect.height;
        
        if (sigmaRef.current && 
            (Math.abs(currentWidth - prevWidth) > 5 || Math.abs(currentHeight - prevHeight) > 5)) {
          console.log('Container dimensions changed significantly, refreshing Sigma');
          sigmaRef.current.refresh();
          
          prevWidth = currentWidth;
          prevHeight = currentHeight;
        }
      }
    };
    
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      prevWidth = rect.width;
      prevHeight = rect.height;
    }
    
    const observer = new MutationObserver(() => {
      checkContainerDimensions();
    });
    
    observer.observe(containerRef.current, { 
      attributes: true,
      attributeFilter: ['style', 'class']
    });
    
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
            maxWidth: '400px',
          }}
        >
          <Alert 
            severity="info" 
            variant="outlined"
            sx={{ boxShadow: 1, fontSize: '0.85rem', opacity: 0.85 }}
            onClose={() => setShowWarning(false)}
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