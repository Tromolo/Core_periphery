import React, { useState } from "react";
import { 
  Container, 
  Box, 
  Typography, 
  ThemeProvider, 
  createTheme,
  CssBaseline,
  Paper,
  Grow
} from '@mui/material';
import GraphUploader from "./components/GraphUploader";
import GraphVisualizer from "./components/GraphVisualizer";
import GraphStats from "./components/GraphStats";

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
  },
});

function App() {
  const [graphData, setGraphData] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [plotData, setPlotData] = useState(null);

  const handleGraphUpload = (data) => {
    setGraphData(data.classifications);
    setMetrics(data.metrics);
    setPlotData(data.interactive_plot);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #f5f5f7 0%, #e8eaf6 100%)',
          py: 4
        }}
      >
        <Container maxWidth="xl">
          <Grow in={true} timeout={500}>
            <Paper
              elevation={0}
              sx={{
                p: 4,
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(20px)',
                borderRadius: 4,
                border: '1px solid rgba(255, 255, 255, 0.2)',
              }}
            >
              <Typography 
                variant="h1" 
                sx={{ 
                  textAlign: 'center',
                  mb: 5,
                  background: 'linear-gradient(45deg, #1a237e, #0d47a1)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  color: 'transparent',
                  textShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}
              >
                Network Analysis Dashboard
              </Typography>

              <GraphUploader onUpload={handleGraphUpload} />

              {graphData && (
                <>
                  <Box sx={{ mt: 5 }}>
                    <GraphStats graphData={graphData} metrics={metrics} />
                  </Box>

                  <Box sx={{ mt: 5 }}>
                    <GraphVisualizer 
                      graphData={graphData} 
                      metrics={metrics} 
                      plotData={plotData}
                    />
                  </Box>
                </>
              )}
            </Paper>
          </Grow>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;