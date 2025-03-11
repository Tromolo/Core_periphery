import React, { useState, useEffect } from 'react';
import { Box, Card, Typography, Button, Grow } from '@mui/material';
import Plot from 'react-plotly.js';
import { useTheme } from '@mui/material/styles';
import { 
  Hub, 
  Timeline, 
  AccountTree, 
  DeviceHub,
  Download 
} from '@mui/icons-material';
import { 
  Grid, 
  Stack 
} from '@mui/material';

const GraphVisualizer = ({ graphData, metrics, plotData, csvFile, imageFile, gdfFile }) => {
  const theme = useTheme();


  const handleDownloadCSV = () => {
    if (!csvFile) {
      console.error('CSV file is not defined');
      return;
    }
    const csvFileUrl = `http://localhost:8080/static/${csvFile}`; 
    const link = document.createElement("a");
    link.setAttribute("href", csvFileUrl);
    link.setAttribute("download", csvFile);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadImage = async () => {
    if (!imageFile) {
      console.error('Image file is not defined');
      return;
    }
    
    const imageUrl = `http://localhost:8080/static/${imageFile}`;

    try {
      const response = await fetch(imageUrl);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const blob = await response.blob(); 
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", imageFile); 
      document.body.appendChild(link);
      link.click(); 
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading image:', error);
    }
  };

  const handleDownloadGDF = () => {
    if (!gdfFile) {
      console.error('GDF file is not defined');
      return;
    }
    
    const gdfFileUrl = `http://localhost:8080/static/${gdfFile}`;
    const link = document.createElement("a");
    link.setAttribute("href", gdfFileUrl);
    link.setAttribute("download", gdfFile);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
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
          Network Visualization
        </Typography>
      </Box>

      <Stack spacing={4}>
        <Grow in={true} timeout={500}>
          <Card
            sx={{
              p: 3,
              mb: 4,
              background: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7))',
              backdropFilter: 'blur(10px)',
              transition: 'transform 0.2s ease-in-out',
              '&:hover': {
                transform: 'scale(1.01)',
              },
            }}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              Interactive Network Visualization
            </Typography>
            <Plot
              data={plotData.data}
              layout={plotData.layout}
              config={{ displayModeBar: false }}
              style={{ width: '100%', height: 'auto' }}
            />
          </Card>
        </Grow>

        {metrics?.network_image && (
          <Grow in={true} timeout={700}>
            <Card
              sx={{
                p: 3,
                background: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7))',
                backdropFilter: 'blur(10px)',
                transition: 'transform 0.2s ease-in-out',
                '&:hover': {
                  transform: 'scale(1.01)',
                },
              }}
            >
              <Typography variant="h6" sx={{ mb: 2 }}>
                Static Network Visualization
              </Typography>
              <Box 
                component="img"
                src={`http://localhost:8080/static/${metrics.network_image}`}
                alt="Network visualization"
                sx={{
                  maxWidth: '100%',
                  height: 'auto',
                  borderRadius: '8px',
                }}
              />
            </Card>
          </Grow>
        )}

        {imageFile && (
          <Grow in={true} timeout={700}>
            <Card
              sx={{
                p: 3,
                background: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7))',
                backdropFilter: 'blur(10px)',
                transition: 'transform 0.2s ease-in-out',
                '&:hover': {
                  transform: 'scale(1.01)',
                },
              }}
            >
              <Typography variant="h6" sx={{ mb: 2 }}>
                Generated Network Visualization
              </Typography>
              {console.log("Image file URL:", `http://localhost:8080/static/${imageFile}`)}
              <Box 
                component="img"
                src={`http://localhost:8080/static/${imageFile}`}
                alt="Generated Network Visualization"
                sx={{
                  maxWidth: '100%',
                  height: 'auto',
                  borderRadius: '8px',
                }}
                onError={(e) => {
                  console.error("Failed to load image:", e);
                  console.error("Image URL was:", e.target.src);
                  e.target.onerror = null; // Prevent infinite loop
                  e.target.src = "https://via.placeholder.com/800x600?text=Visualization+Not+Available";
                }}
              />
            </Card>
          </Grow>
        )}

      {metrics && (
        <Grid container spacing={3} sx={{ ml: 2 }}> 
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Total Nodes"
              value={metrics.node_count}
              icon={<Hub />}
              delay={0}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Total Edges"
              value={metrics.edge_count}
              icon={<Timeline />}
              delay={100}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Core Size"
              value={metrics.core_stats?.core_size}
              icon={<AccountTree />}
              delay={200}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Periphery Size"
              value={metrics.core_stats?.periphery_size}
              icon={<DeviceHub />}
              delay={300}
            />
          </Grid>
        </Grid>
      )}
      </Stack>
      <Stack direction="row" spacing={2} sx={{ mt: 4, justifyContent: 'center' }}>
        {csvFile && (
          <Button 
            onClick={handleDownloadCSV} 
            variant="contained"
          >
            Download CSV
          </Button>
        )}
        {imageFile && (
          <Button 
            onClick={handleDownloadImage} 
            variant="contained"
          >
            Download Image
          </Button>
        )}
        {gdfFile && (
          <Button 
            onClick={handleDownloadGDF} 
            variant="contained"
          >
            Download GDF (Gephi)
          </Button>
        )}
      </Stack>
    </Box>
  );
};

const MetricCard = ({ title, value, icon, delay }) => {
  const theme = useTheme();
  
  return (
    <Grow in={true} timeout={500 + delay}>
      <Card
        sx={{
          p: 3,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          background: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7))',
          backdropFilter: 'blur(10px)',
          transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: `0 8px 32px -4px ${theme.palette.primary.main}20`
          }
        }}
      >
        <Box 
          sx={{ 
            color: theme.palette.primary.main,
            mb: 2,
            transform: 'scale(1.5)'
          }}
        >
          {icon}
        </Box>
        <Typography variant="h6" sx={{ color: 'text.secondary', mb: 1 }}>
          {title}
        </Typography>
        <Typography variant="h4" sx={{ color: theme.palette.primary.main, fontWeight: 'bold' }}>
          {typeof value === 'number' ? value.toFixed(0) : value || '0'}
        </Typography>
      </Card>
    </Grow>
  );
};

export default GraphVisualizer;