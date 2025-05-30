import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Box, Card, Grid, Typography, Paper, Divider, CircularProgress } from '@mui/material';
import GraphHeader from './GraphHeader';
import GraphLegend from './GraphLegend';
import GraphControls from './GraphControls';
import SigmaRenderer from './SigmaRenderer';
import NodeDetailsPanel from './NodeDetailsPanel';
import CorePeripheryMetrics from './CorePeripheryMetrics';
import EdgeDistribution from './EdgeDistribution';
import ConnectionPieChart from './ConnectionPieChart';

const GraphVisualizer = ({ graphData, metrics, nodeCsvFile, edgeCsvFile, gdfFile }) => {
  const [apiDataLoaded, setApiDataLoaded] = useState(false);
  const [graphRendering, setGraphRendering] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [showLabels, setShowLabels] = useState(false);
  const [nodeSize, setNodeSize] = useState(1.5);
  const [isForceAtlas2Running, setIsForceAtlas2Running] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const [graphDetail, setGraphDetail] = useState(100);
  const [isLargeGraph, setIsLargeGraph] = useState(false);
  const [rendererReady, setRendererReady] = useState(false);
  
  const sigmaRendererRef = useRef(null);
  
  useEffect(() => {
    console.log("Renderer ready state changed:", rendererReady);
    if (rendererReady) {
      setGraphRendering(false);
    }
  }, [rendererReady]);

  useEffect(() => {
    let mounted = true;
    
    if (graphData && graphData.nodes && graphData.edges) {
      if (mounted) {
        setApiDataLoaded(true);
        
        const isLarge = graphData.nodes.length > 1000 || graphData.edges.length > 3000;
        setIsLargeGraph(isLarge);
      }
    }
    
    return () => {
      mounted = false;
    };
  }, [graphData]);

  const handleDownloadNodeCSV = () => nodeCsvFile && window.open(`http://localhost:8080/download/${nodeCsvFile}`, '_blank');
  const handleDownloadEdgeCSV = () => edgeCsvFile && window.open(`http://localhost:8080/download/${edgeCsvFile}`, '_blank');
  const handleDownloadGDF = () => gdfFile && window.open(`http://localhost:8080/download/${gdfFile}`, '_blank');

  const handleDownloadImage = useCallback(() => {
    if (!sigmaRendererRef.current || !sigmaRendererRef.current.getSigma()) {
      console.error("Cannot download visualization: Sigma instance not available");
      return;
    }

    try {
      const sigmaInstance = sigmaRendererRef.current.getSigma();
      const containerRef = sigmaRendererRef.current.getContainer();
      
      let downloadSuccessful = false;
      
      if (typeof sigmaInstance.refresh === 'function') {
        sigmaInstance.refresh();
        
        const canvasRenderer = sigmaInstance.getCanvasRenderer?.() || 
                              sigmaInstance.getRenderer?.();
                              
        if (canvasRenderer && typeof canvasRenderer.snapshot === 'function') {
          console.log("Using Sigma's built-in snapshot method");
          const snapshot = canvasRenderer.snapshot({
            download: true,
            filename: 'graph_visualization.png',
            background: 'white'
          });
          
          downloadSuccessful = true;
          console.log("Visualization downloaded using Sigma's built-in method");
        }
      }
      
      if (!downloadSuccessful) {
        console.log("Falling back to manual canvas capture method");
        
        const sigmaContainer = document.querySelector('.sigma-container');
        
        if (!sigmaContainer) {
          console.error("Cannot download: Sigma container not found");
          return;
        }
        
        const canvases = sigmaContainer.querySelectorAll('canvas');
        
        if (!canvases || canvases.length === 0) {
          console.error("Cannot download: No canvas elements found");
          return;
        }
        
        const containerRect = sigmaContainer.getBoundingClientRect();
        const width = containerRect.width;
        const height = containerRect.height;
        
        const outputCanvas = document.createElement('canvas');
        outputCanvas.width = width;
        outputCanvas.height = height;
        const outputCtx = outputCanvas.getContext('2d');
        
        outputCtx.fillStyle = 'white';
        outputCtx.fillRect(0, 0, width, height);
        
        console.log(`Drawing ${canvases.length} canvases to output`);
        Array.from(canvases).forEach((canvas, index) => {
          try {
            if (canvas.width > 0 && canvas.height > 0) {
              outputCtx.drawImage(canvas, 0, 0, width, height);
              console.log(`Canvas ${index} drawn successfully`);
            } else {
              console.log(`Canvas ${index} skipped (empty/invalid dimensions)`);
            }
          } catch (e) {
            console.error(`Error drawing canvas ${index}:`, e);
          }
        });
        
        const link = document.createElement('a');
        link.download = 'graph_visualization.png';
        link.href = outputCanvas.toDataURL('image/png');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log("Visualization downloaded successfully via manual method");
      }
      
      setDownloadSuccess(true);
      setTimeout(() => {
        setDownloadSuccess(false);
      }, 2000);
    } catch (error) {
      console.error("Error downloading visualization:", error);
      alert("Failed to download the visualization: " + error.message);
    }
  }, []);

  const toggleForceAtlas2 = useCallback(() => {
    if (sigmaRendererRef.current && sigmaRendererRef.current.toggleForceAtlas2) {
      sigmaRendererRef.current.toggleForceAtlas2();
    }
  }, []);

  const centerView = useCallback(() => {
    if (sigmaRendererRef.current && sigmaRendererRef.current.centerView) {
      sigmaRendererRef.current.centerView();
    }
  }, []);

  const handleNodeSizeChange = useCallback((event, newValue) => {
    setNodeSize(newValue);
  }, []);

  const handleToggleLabels = useCallback(() => {
    setShowLabels(!showLabels);
  }, [showLabels]);

  useEffect(() => {
    return () => {
      if (sigmaRendererRef.current && sigmaRendererRef.current.getSigma) {
        const sigma = sigmaRendererRef.current.getSigma();
        if (sigma) {
          try {
            sigma.kill();
          } catch (e) {
            console.error("Error during cleanup:", e);
          }
        }
      }
    };
  }, []);

  return (
    <Card sx={{ p: 3, boxShadow: 3, borderRadius: 2, height: '100%' }}>
      <GraphHeader 
        nodeCsvFile={nodeCsvFile}
        edgeCsvFile={edgeCsvFile}
        gdfFile={gdfFile}
        handleDownloadNodeCSV={handleDownloadNodeCSV}
        handleDownloadEdgeCSV={handleDownloadEdgeCSV}
        handleDownloadGDF={handleDownloadGDF}
        handleDownloadImage={handleDownloadImage}
        downloadSuccess={downloadSuccess}
      />

      {!apiDataLoaded ? (
        <Box sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '400px'
        }}>
          <Typography variant="h6">Loading data from server...</Typography>
        </Box>
      ) : (
        <>
          <GraphLegend />
          
          <GraphControls 
            toggleForceAtlas2={toggleForceAtlas2}
            centerView={centerView}
            isForceAtlas2Running={isForceAtlas2Running}
            nodeSize={nodeSize}
            handleNodeSizeChange={handleNodeSizeChange}
            showLabels={showLabels}
            handleToggleLabels={handleToggleLabels}
            rendererReady={true}
          />

          <Box sx={{ 
            display: 'flex', 
            flexDirection: 'column', 
            height: '500px',
            width: '100%', 
            position: 'relative',
            minHeight: '500px',
            minWidth: '300px',
          }}>
            {graphRendering && (
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
                  zIndex: 5,
                  borderRadius: 1,
                  border: '1px solid rgba(0, 0, 0, 0.12)',
                }}
              >
                <Box sx={{ mb: 2, textAlign: 'center' }}>
                  <CircularProgress size={60} thickness={4} />
                  <Typography variant="h6" sx={{ mt: 2 }}>Rendering Graph Visualization</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', maxWidth: '80%', mx: 'auto' }}>
                    {isLargeGraph 
                      ? 'This is a large graph and may take a moment to render. You can explore the metrics below while waiting.' 
                      : 'Graph visualization is being prepared. You can explore the metrics below in the meantime.'}
                  </Typography>
                </Box>
              </Box>
            )}
            <SigmaRenderer 
              ref={sigmaRendererRef}
              graphData={graphData}
              nodeSize={nodeSize}
              showLabels={showLabels}
              onNodeSelect={setSelectedNode}
              isForceAtlas2Running={isForceAtlas2Running}
              setIsForceAtlas2Running={setIsForceAtlas2Running}
              graphDetail={graphDetail}
              isLargeGraph={isLargeGraph}
              loading={false}
              error={error}
              setRendererReady={setRendererReady}
            />
          </Box>

          {selectedNode && sigmaRendererRef.current && (
            <NodeDetailsPanel 
              selectedNode={selectedNode} 
              graphRef={sigmaRendererRef.current.getGraph && sigmaRendererRef.current.getGraph()}
            />
          )}
          
          <CorePeripheryMetrics 
            graphData={graphData} 
            metrics={metrics}
          />
          
          <EdgeDistribution graphData={graphData} />
          
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={12}>
              <Typography variant="h6" sx={{ mb: 1 }}>Connection Pattern Visualization</Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 2, 
                  borderRadius: 2,
                  height: 450,
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <Typography variant="subtitle1" gutterBottom>
                  Edge Distribution Pie Chart
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  This chart shows the distribution of connections between core and periphery nodes.
                  The three categories represented are Core-Core (red), Core-Periphery (purple), and 
                  Periphery-Periphery (blue) connections.
                </Typography>
                <Box sx={{ flexGrow: 1, minHeight: 350 }}>
                  <ConnectionPieChart 
                    graphData={graphData} 
                    metrics={metrics}
                  />
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 2, 
                  borderRadius: 2,
                  height: 450
                }}
              >
                <Typography variant="subtitle1" gutterBottom>
                  What This Means
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Core-Core connections:</strong> A high proportion indicates a densely connected core, typical of a strong core-periphery structure.
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Core-Periphery connections:</strong> These links show how well the periphery nodes are connected to the core. A healthy ratio suggests good information flow between core and periphery.
                </Typography>
                <Typography variant="body2">
                  <strong>Periphery-Periphery connections:</strong> A low proportion is typical in an ideal core-periphery structure, as periphery nodes tend to connect through core nodes rather than directly to each other.
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </>
      )}
    </Card>
  );
};

export default GraphVisualizer; 