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
  CardActions,
  CircularProgress,
  FormGroup,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import { 
  Home as HomeIcon, 
  BarChart as BarChartIcon, 
  BubbleChart as BubbleChartIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import GraphUploader from "./components/GraphUploader";
import GraphVisualizer from './components/graph-visualizer';
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
  const [communityData, setCommunityData] = useState(null);
  const [fileInfo, setFileInfo] = useState(null);
  const [algorithmMetrics, setAlgorithmMetrics] = useState(null);
  const [nodeCsvFile, setNodeCsvFile] = useState(null);
  const [edgeCsvFile, setEdgeCsvFile] = useState(null);
  const [gdfFile, setGdfFile] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  
  const [selectedAnalyses, setSelectedAnalyses] = useState({
    networkStats: true,
    degreeDistribution: true,
    connectedComponents: true,
    communityAnalysis: true,
  });

  const initialNetworkMetricsState = {
    updateStats: (stats) => {
      setNetworkMetrics(prevMetrics => ({
        ...prevMetrics,
        ...stats
      }));
    }
  };
  
  const [networkMetrics, setNetworkMetrics] = useState(initialNetworkMetricsState);

  const navigateTo = (view) => {
    setCurrentView(view);
  };

  const resetState = () => {
    setGraphData(null);
    setAlgorithmMetrics(null);
    setNodeCsvFile(null);
    setEdgeCsvFile(null);
    setGdfFile(null);
    setNetworkMetrics(initialNetworkMetricsState);
    setCommunityData(null);
    setTabValue(0);
  };

  const handleGraphUpload = (data) => {
    console.log('Graph uploaded:', data);
    setGraphData(data);
    setTabValue(0);
  };

  const handleBasicNetworkUpload = (data) => {
    if (data.error) {
      console.error('Error uploading graph:', data.error);
      return;
    }
    
    setGraphData(data.graph_data);
    setCommunityData(data.community_data);
    setFileInfo({...data, loading: data.loading});
    
    setNetworkMetrics(prevMetrics => ({
      ...data.network_metrics,
      updateStats: prevMetrics.updateStats,
      loading: data.loading
    }));
    
    navigateTo('basic');
    
    setTabValue(0);
  };

  const handleAnalysis = (data) => {
    setGraphData(data.graph_data);
    setAlgorithmMetrics(data);
    setNodeCsvFile(data.node_csv_file);
    setEdgeCsvFile(data.edge_csv_file);
    setGdfFile(data.gdf_file);
    
    setNetworkMetrics(prevMetrics => ({
      ...data.network_metrics,
      updateStats: prevMetrics.updateStats
    }));
    
    navigateTo('core-periphery');
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleAnalysisSelectionChange = (event) => {
    setSelectedAnalyses({
      ...selectedAnalyses,
      [event.target.name]: event.target.checked,
    });
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
                <li>Network metrics</li>
                <li>Degree distribution</li>
                <li>Connected components analysis</li>
                <li>Community detection</li>
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
      
      {!graphData ? (
        <Box>
          <GraphUploader 
            onUpload={handleBasicNetworkUpload} 
            selectedAnalyses={selectedAnalyses}
          />
          <Card sx={{ 
            mt: 4, 
            p: 4,
            borderRadius: 2, 
            backgroundColor: 'rgba(0, 0, 0, 0.02)'
          }}>
            <Typography 
              variant="h6" 
              sx={{ 
                mb: 3,
                fontWeight: 600,
                color: 'primary.dark'
              }}
            >
              Select Analyses to Perform:
            </Typography>
            <FormGroup>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedAnalyses.networkStats}
                        onChange={handleAnalysisSelectionChange}
                        name="networkStats"
                      />
                    }
                    label="Network Statistics"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedAnalyses.degreeDistribution}
                        onChange={handleAnalysisSelectionChange}
                        name="degreeDistribution"
                      />
                    }
                    label="Degree Distribution"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedAnalyses.connectedComponents}
                        onChange={handleAnalysisSelectionChange}
                        name="connectedComponents"
                      />
                    }
                    label="Connected Components"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedAnalyses.communityAnalysis}
                        onChange={handleAnalysisSelectionChange}
                        name="communityAnalysis"
                      />
                    }
                    label="Community Analysis"
                  />
                </Grid>
              </Grid>
            </FormGroup>
          </Card>
        </Box>
      ) : (
        <>
          <Box sx={{ mb: 2 }}>
            <Button
              variant="contained"
              onClick={() => resetState()}
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
              {networkMetrics?.node_count && (
                <GraphStats 
                  graphData={graphData} 
                  metrics={networkMetrics}
                  communityData={communityData}
                  networkMetrics={networkMetrics}
                />
              )}
            </Grid>
          </Grid>

          {/* Conditionally render Degree Histogram */}
          {graphData && graphData.nodes && graphData.nodes.length > 0 && networkMetrics?.degree_distribution && (
            <Box sx={{ mt: 4, mb: 4 }}>
              <DegreeHistogram 
                graphData={graphData} 
                communityData={communityData} 
                networkMetrics={networkMetrics}
              />
            </Box>
          )}

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

          {graphData && graphData.nodes && graphData.nodes.length > 0 ? (
            <>
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
          ) : (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <CircularProgress />
              <Typography variant="h6" sx={{ mt: 2 }}>
                Loading analysis data...
              </Typography>
            </Box>
          )}
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