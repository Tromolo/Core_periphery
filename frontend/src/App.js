import React, { useState } from "react";
import { 
  Container, 
  Box, 
  Typography, 
  ThemeProvider, 
  createTheme,
  CssBaseline,
  Paper,
  Grow,
  Tabs,
  Tab,
  AppBar,
  Toolbar,
  Grid,
  Button,
  Card,
  CardContent,
  CardMedia,
  CardActionArea,
  Divider,
  CardActions
} from '@mui/material';
import { 
  Home as HomeIcon, 
  BarChart as BarChartIcon, 
  BubbleChart as BubbleChartIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import GraphUploader from "./components/GraphUploader";
import GraphVisualizer from "./components/GraphVisualizer";
import GraphStats from "./components/GraphStats";
import CommunityAnalysis from "./components/CommunityAnalysis";
import ConnectedComponentsChart from "./components/ConnectedComponentsChart";
import MetricsTable from "./components/MetricsTable";
import AlgorithmSelector from "./components/AlgorithmSelector";
import DegreeHistogram from './components/DegreeHistogram';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1a237e',
      light: '#534bae',
      dark: '#000051',
    },
    secondary: {
      main: '#0d47a1',
      light: '#5472d3',
      dark: '#002171',
    },
    background: {
      default: '#f5f5f7',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 800,
      fontSize: '2.5rem',
    },
    h4: {
      fontWeight: 700,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
  },
});

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [graphData, setGraphData] = useState(null);
  const [algorithmMetrics, setAlgorithmMetrics] = useState(null);
  const [nodeCsvFile, setNodeCsvFile] = useState(null);
  const [edgeCsvFile, setEdgeCsvFile] = useState(null);
  const [gdfFile, setGdfFile] = useState(null);
  const [networkMetrics, setNetworkMetrics] = useState(null);
  const [communityData, setCommunityData] = useState(null);
  const [selectedTab, setSelectedTab] = useState(0);

  const navigateTo = (view) => {
    setCurrentView(view);
  };

  const resetState = () => {
    setGraphData(null);
    setAlgorithmMetrics(null);
    setNodeCsvFile(null);
    setEdgeCsvFile(null);
    setGdfFile(null);
    setNetworkMetrics(null);
    setCommunityData(null);
    setSelectedTab(0);
  };

  const handleGraphUpload = (data) => {
    console.log('Graph uploaded:', data);
    setGraphData(data);
  };

  const handleBasicNetworkUpload = (data) => {
    console.log('Basic network upload data:', data);
    if (!data.network_metrics) {
      console.error('No network metrics in upload response');
      return;
    }

    // Set network metrics
    setNetworkMetrics(data.network_metrics);
    
    // Set community data
    setCommunityData(data.community_data);
    
    // Process graph data for visualization
    if (data.graph_data && data.graph_data.nodes && data.graph_data.edges) {
      console.log(`Graph data received: ${data.graph_data.nodes.length} nodes, ${data.graph_data.edges.length} edges`);
      
      // Set graph data with nodes and edges for visualization
      setGraphData({
        nodes: data.graph_data.nodes,
        edges: data.graph_data.edges,
        filename: data.filename,
        filesize: data.filesize,
        filetype: data.filetype,
        // If degree distribution is available, add it to the graph data
        degree_distribution: data.degree_distribution || []
      });
    } else {
      // Set graph data with just the file information
      setGraphData({
        filename: data.filename,
        filesize: data.filesize,
        filetype: data.filetype
      });
    }
    
    // Navigate to the basic network view tab
    setSelectedTab(0);
  };

  const handleAnalysis = (data) => {
    console.log('Analysis data received:', data);
    if (!data) {
      console.error('No analysis data received');
      return;
    }

    // Check if we have graph structure data
    if (data.graph_data) {
      console.log(`Graph data received: ${data.graph_data.nodes.length} nodes, ${data.graph_data.edges.length} edges`);
    } else {
      console.warn('No graph structure data received from backend');
    }

    // Process classifications - convert numeric classifications to 'C' and 'P' format
    const processedClassifications = {};
    if (data.classifications) {
      // Check if classifications is an array of numbers (0/1) or strings ('C'/'P')
      const isNumericClassification = typeof data.classifications[0] === 'number';
      
      data.classifications.forEach((val, index) => {
        if (isNumericClassification) {
          // Convert numeric classifications (1/0) to string format ('C'/'P')
          processedClassifications[index] = val === 1 ? 'C' : 'P';
        } else {
          // Already in string format
          processedClassifications[index] = val;
        }
      });
      
      console.log(`Processed ${Object.keys(processedClassifications).length} classifications`);
      
      // Log the distribution of core vs periphery nodes
      const coreCount = Object.values(processedClassifications).filter(c => c === 'C').length;
      const peripheryCount = Object.values(processedClassifications).filter(c => c === 'P').length;
      console.log(`Classification distribution: ${coreCount} core nodes, ${peripheryCount} periphery nodes`);
    }

    // Create a properly formatted graph data object for the GraphVisualizer
    const formattedGraphData = {
      nodes: [],
      edges: []
    };

    // If we have graph_data from the backend, use it directly
    if (data.graph_data && data.graph_data.nodes && data.graph_data.edges) {
      formattedGraphData.nodes = data.graph_data.nodes;
      formattedGraphData.edges = data.graph_data.edges;
    } 
    // Otherwise, create nodes and edges from classifications and coreness values
    else if (data.classifications) {
      // Create nodes based on classifications
      data.classifications.forEach((classification, index) => {
        const nodeType = typeof classification === 'number' 
          ? (classification === 1 ? 'C' : 'P')
          : classification;
        
        // Find coreness value from top_nodes if available
        let corenessValue = nodeType === 'C' ? 0.8 : 0.2; // Default values
        
        if (data.top_nodes) {
          const topNode = data.top_nodes.find(node => node.id === index);
          if (topNode) {
            corenessValue = topNode.coreness;
          }
        }
        
        formattedGraphData.nodes.push({
          id: index.toString(),
          type: nodeType,
          coreness: corenessValue
        });
      });
      
      // Create some basic edges based on node types
      // This is a fallback if no edge data is provided
      if (data.network_metrics && data.network_metrics.edge_count > 0) {
        console.log('No edge data provided, but network has edges. Creating placeholder edges.');
        // Create placeholder edges - this is not ideal but better than no visualization
        const coreNodes = formattedGraphData.nodes.filter(node => node.type === 'C').map(node => node.id);
        const peripheryNodes = formattedGraphData.nodes.filter(node => node.type === 'P').map(node => node.id);
        
        // Connect core nodes to each other
        for (let i = 0; i < coreNodes.length; i++) {
          for (let j = i + 1; j < coreNodes.length; j++) {
            if (Math.random() < 0.7) { // High probability for core-core connections
              formattedGraphData.edges.push({
                id: `${coreNodes[i]}-${coreNodes[j]}`,
                source: coreNodes[i],
                target: coreNodes[j]
              });
            }
          }
        }
        
        // Connect core nodes to periphery nodes
        for (let i = 0; i < coreNodes.length; i++) {
          for (let j = 0; j < peripheryNodes.length; j++) {
            if (Math.random() < 0.3) { // Medium probability for core-periphery connections
              formattedGraphData.edges.push({
                id: `${coreNodes[i]}-${peripheryNodes[j]}`,
                source: coreNodes[i],
                target: peripheryNodes[j]
              });
            }
          }
        }
        
        // Connect periphery nodes to each other
        for (let i = 0; i < peripheryNodes.length; i++) {
          for (let j = i + 1; j < peripheryNodes.length; j++) {
            if (Math.random() < 0.1) { // Low probability for periphery-periphery connections
              formattedGraphData.edges.push({
                id: `${peripheryNodes[i]}-${peripheryNodes[j]}`,
                source: peripheryNodes[i],
                target: peripheryNodes[j]
              });
            }
          }
        }
      }
    }
    
    console.log(`Formatted graph data: ${formattedGraphData.nodes.length} nodes, ${formattedGraphData.edges.length} edges`);
    
    // Update graph data with the formatted data
    setGraphData(formattedGraphData);

    // Set algorithm metrics
    setAlgorithmMetrics({
      node_count: data.network_metrics?.node_count,
      edge_count: data.network_metrics?.edge_count,
      core_stats: data.core_stats,
      algorithm_params: data.algorithm_params,
      top_nodes: data.top_nodes,
      image_file: data.image_file
    });

    // Set CSV and GDF files for download
    setNodeCsvFile(data.node_csv_file);
    setEdgeCsvFile(data.edge_csv_file);
    setGdfFile(data.gdf_file);
    
    console.log('Updated graph data and metrics');
  };

  const handleTabChange = (event, newValue) => {
    setSelectedTab(newValue);
  };

  const renderHomeView = () => (
    <Box>
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography 
          variant="h3" 
          sx={{ 
            mb: 2, 
            fontWeight: 'bold',
            background: 'linear-gradient(45deg, #1a237e, #0d47a1)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            color: 'transparent',
          }}
        >
          Network Analysis Tool
        </Typography>
        <Typography variant="h6" sx={{ color: 'text.secondary', maxWidth: 800, mx: 'auto' }}>
          Analyze and visualize network structures with advanced algorithms
        </Typography>
      </Box>

      <Grid container spacing={4} justifyContent="center">
        <Grid item xs={12} md={6}>
          <Card 
            sx={{ 
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              transition: 'transform 0.2s',
              '&:hover': {
                transform: 'translateY(-8px)',
                boxShadow: '0 12px 20px rgba(0, 0, 0, 0.1)'
              },
              borderRadius: 2,
              overflow: 'hidden'
            }}
          >
            <Box sx={{ 
              bgcolor: 'primary.main', 
              color: 'white', 
              p: 2,
              background: 'linear-gradient(45deg, #1a237e 30%, #0d47a1 90%)',
            }}>
              <BarChartIcon sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h5" component="div" sx={{ fontWeight: 'bold' }}>
                Basic Network Stats
              </Typography>
            </Box>
            <CardContent sx={{ flexGrow: 1, p: 3 }}>
              <Typography variant="body1" sx={{ mb: 2 }}>
                Analyze basic network metrics, community structure, and connected components without algorithm selection.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Features:
              </Typography>
              <ul>
                <li>Network density and clustering</li>
                <li>Path length and diameter</li>
                <li>Community detection</li>
                <li>Connected components analysis</li>
              </ul>
            </CardContent>
            <CardActions sx={{ p: 3, pt: 0 }}>
              <Button 
                variant="contained" 
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigateTo('basic')}
                sx={{ 
                  borderRadius: 2,
                  background: 'linear-gradient(45deg, #1a237e 30%, #0d47a1 90%)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #0d47a1 30%, #1a237e 90%)',
                  }
                }}
              >
                Start Analysis
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card 
            sx={{ 
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              transition: 'transform 0.2s',
              '&:hover': {
                transform: 'translateY(-8px)',
                boxShadow: '0 12px 20px rgba(0, 0, 0, 0.1)'
              },
              borderRadius: 2,
              overflow: 'hidden'
            }}
          >
            <Box sx={{ 
              bgcolor: 'primary.main', 
              color: 'white', 
              p: 2,
              background: 'linear-gradient(45deg, #1a237e 30%, #0d47a1 90%)',
            }}>
              <BubbleChartIcon sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h5" component="div" sx={{ fontWeight: 'bold' }}>
                Core-Periphery Analysis
              </Typography>
            </Box>
            <CardContent sx={{ flexGrow: 1, p: 3 }}>
              <Typography variant="body1" sx={{ mb: 2 }}>
                Identify core and peripheral nodes in your network using specialized algorithms.
                Visualize the core-periphery structure and analyze the results.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Features:
              </Typography>
              <ul>
                <li>Multiple core-periphery detection algorithms</li>
                <li>Interactive visualization</li>
                <li>Detailed metrics and statistics</li>
                <li>Export results in various formats</li>
              </ul>
            </CardContent>
            <CardActions sx={{ p: 3, pt: 0 }}>
              <Button 
                variant="contained" 
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigateTo('core-periphery')}
                sx={{ 
                  borderRadius: 2,
                  background: 'linear-gradient(45deg, #1a237e 30%, #0d47a1 90%)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #0d47a1 30%, #1a237e 90%)',
                  }
                }}
              >
                Start Analysis
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  const renderBasicNetworkView = () => (
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
          Basic Network Analysis
        </Typography>
        <Button 
          variant="outlined" 
          onClick={() => navigateTo('home')}
          sx={{ borderRadius: 2 }}
        >
          Back to Home
        </Button>
      </Box>
      
      {!networkMetrics ? (
        <Box>
          <GraphUploader onUpload={handleBasicNetworkUpload} />
        </Box>
      ) : (
        <>
          <Box sx={{ mb: 2 }}>
            <Button
              variant="contained"
              onClick={() => setNetworkMetrics(null)}
              sx={{
                color: 'white',
                background: 'linear-gradient(45deg, #0d47a1 30%, #1a237e 90%)',
              }}
            >
              Analyze Another Graph
            </Button>
          </Box>

          <Grid container spacing={4} sx={{ mb: 4 }}>
            <Grid item xs={12}>
              <GraphStats 
                graphData={graphData} 
                metrics={networkMetrics} 
                communityData={communityData}
              />
            </Grid>
          </Grid>

          {/* Add Degree Histogram */}
          {(graphData && graphData.nodes) || (communityData && communityData.graph_data) ? (
            <Box sx={{ mt: 4, mb: 4 }}>
              <DegreeHistogram 
                graphData={graphData} 
                communityData={communityData} 
                networkMetrics={networkMetrics}
              />
            </Box>
          ) : null}

          {networkMetrics?.connected_components && (
            <Box sx={{ mt: 4 }}>
              <ConnectedComponentsChart metrics={networkMetrics} />
            </Box>
          )}

          {communityData && (
            <Box sx={{ mt: 4 }}>
              <CommunityAnalysis communityData={communityData} />
            </Box>
          )}
        </>
      )}
    </Box>
  );

  const renderCorePeripheryView = () => (
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
          Core-Periphery Analysis
        </Typography>
        <Button 
          variant="outlined" 
          onClick={() => navigateTo('home')}
          sx={{ borderRadius: 2 }}
        >
          Back to Home
        </Button>
      </Box>

      {!algorithmMetrics ? (
        <Box>
          <AlgorithmSelector 
            graphData={graphData} 
            onAnalysis={handleAnalysis} 
            onUpload={handleGraphUpload}
          />
        </Box>
      ) : (
        <>
          <Box sx={{ mb: 4 }}>
            <Button 
              variant="contained" 
              onClick={resetState}
              sx={{ 
                borderRadius: 2,
                background: 'linear-gradient(45deg, #1a237e 30%, #0d47a1 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #0d47a1 30%, #1a237e 90%)',
                }
              }}
            >
              Analyze Another Graph
            </Button>
          </Box>

          <Box sx={{ mb: 5 }}>
            <GraphVisualizer 
              graphData={graphData} 
              metrics={algorithmMetrics} 
              nodeCsvFile={nodeCsvFile}
              edgeCsvFile={edgeCsvFile}
              gdfFile={gdfFile}
              imageFile={algorithmMetrics.image_file}
            />
          </Box>

          <Box sx={{ mb: 5 }}>
            <MetricsTable metrics={algorithmMetrics} />
          </Box>
        </>
      )}
    </Box>
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Box sx={{ minHeight: '100vh' }}>
          <Grow in={true} timeout={500}>
            <Paper 
              elevation={3} 
              sx={{ 
                p: 4, 
                borderRadius: 3,
                background: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7))',
                backdropFilter: 'blur(10px)',
              }}
            >
              {currentView === 'home' && renderHomeView()}
              {currentView === 'basic' && renderBasicNetworkView()}
              {currentView === 'core-periphery' && renderCorePeripheryView()}
            </Paper>
          </Grow>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;