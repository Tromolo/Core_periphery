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

const GraphVisualizer = ({ graphData, metrics, plotData, csvFile, imageFile }) => {
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
        
        <Button
          variant="contained"
          startIcon={<Download />}
          onClick={handleDownloadCSV}
          sx={{
            bgcolor: theme.palette.primary.main,
            '&:hover': {
              bgcolor: theme.palette.primary.dark,
            }
          }}
        >
          Download CSV
        </Button>
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
              style={{ width: '100%', height: '70vh' }}
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
              <Box 
                component="img"
                src={`http://localhost:8080/static/${imageFile}`}
                alt="Generated Network Visualization"
                sx={{
                  maxWidth: '100%',
                  height: 'auto',
                  borderRadius: '8px',
                }}
              />
            </Card>
          </Grow>
        )}

        {metrics && (
          <Grid container spacing={3}>
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