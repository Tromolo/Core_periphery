import React, { useState } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Grid, 
  Box,
  Chip,
  LinearProgress,
  useTheme,
  Grow,
  Stack,
  Button,
  Tooltip
} from '@mui/material';
import { 
  Timeline, 
  Hub, 
  Share, 
  AccountTree,
  TrendingUp,
  Lan,
  Download
} from '@mui/icons-material';

const generateCSV = (graphData, metrics, communityData) => {
  let nodes = [];
  if (graphData && graphData.nodes && graphData.nodes.length > 0) {
    nodes = graphData.nodes;
  } else if (communityData && communityData.graph_data && communityData.graph_data.nodes) {
    nodes = communityData.graph_data.nodes;
  }
  
  if (nodes.length === 0) {
    console.warn("No node data available for CSV export");
    return null;
  }

  const headers = ['Node ID', 'Degree', 'Community'];
  
  let csvContent = headers.join(',') + '\n';
  
  const communityMapping = communityData?.community_membership || {};
  
  nodes.forEach(node => {
    const nodeId = node.id || '';
    const degree = node.degree !== undefined ? node.degree : 0;
    const community = communityMapping[nodeId] !== undefined ? communityMapping[nodeId] : '';
    
    const row = [
      nodeId, 
      degree, 
      community
    ].join(',');
    
    csvContent += row + '\n';
  });
  
  return csvContent;
};

const downloadCSV = (graphData, metrics, communityData) => {
  try {
    const csvContent = generateCSV(graphData, metrics, communityData);
    
    if (!csvContent) {
      console.error("Failed to generate CSV: No data available");
      alert("No node data available for export");
      return;
    }
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `network_node_data_${timestamp}.csv`;
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setTimeout(() => {
      URL.revokeObjectURL(url);
    }, 100);
    
    console.log(`CSV export successful: ${filename}`);
  } catch (error) {
    console.error("Error during CSV export:", error);
    alert("Failed to export data: " + error.message);
  }
};

const StatCard = ({ label, value, icon, color }) => (
  <Box
    sx={{
      p: 2,
      borderRadius: 2,
      bgcolor: 'rgba(255,255,255,0.5)',
      height: '100%',
      display: 'flex',
      alignItems: 'center',
      gap: 2
    }}
  >
    <Box sx={{ color: color }}>
      {icon}
    </Box>
    <Box>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h6" sx={{ fontWeight: 600, color }}>
        {label === "Total Nodes" || label === "Total Edges" 
          ? parseInt(value || 0)
          : (typeof value === 'number' ? value.toFixed(3) : value || '0')}
      </Typography>
    </Box>
  </Box>
);

const NodeCard = ({ node, index }) => {
  const theme = useTheme();
  
  return (
    <Grow in={true} timeout={300 + (index * 100)}>
      <Card
        sx={{
          mb: 2,
          background: node.type === 'C' 
            ? `linear-gradient(135deg, ${theme.palette.primary.light}15, ${theme.palette.primary.main}15)`
            : `linear-gradient(135deg, ${theme.palette.secondary.light}15, ${theme.palette.secondary.main}15)`,
          transition: 'transform 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-4px)'
          }
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Node {node.id}
            </Typography>
            <Chip 
              label={node.type === 'C' ? 'Core' : 'Periphery'}
              size="small"
              icon={node.type === 'C' ? <Hub /> : <Share />}
              sx={{
                bgcolor: node.type === 'C' ? theme.palette.primary.main : theme.palette.secondary.main,
                color: 'white',
                fontWeight: 500,
                '& .MuiSvgIcon-root': {
                  color: 'white'
                }
              }}
            />
          </Box>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
              Coreness: {node.coreness.toFixed(3)}
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={node.coreness * 100}
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: 'rgba(0,0,0,0.1)',
                '& .MuiLinearProgress-bar': {
                  bgcolor: node.type === 'C' ? theme.palette.primary.main : theme.palette.secondary.main,
                  borderRadius: 4
                }
              }}
            />
          </Box>
        </CardContent>
      </Card>
    </Grow>
  );
};

const GraphStats = ({ graphData, metrics, communityData, networkMetrics }) => {
  if (!metrics) return null;
  const theme = useTheme();
  const [exportSuccess, setExportSuccess] = useState(false);
  
  const handleDownload = () => {
    try {
      downloadCSV(graphData, metrics, communityData);
      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (error) {
      console.error("Error handling download:", error);
    }
  };

  const averageDegree = networkMetrics?.basicStats?.avgDegree || 
                       metrics?.average_degree || 
                       metrics?.avg_degree || 
                       '0';
  
  console.log("GraphStats NetworkMetrics:", {
    basicStats: networkMetrics?.basicStats,
    avgDegree: networkMetrics?.basicStats?.avgDegree,
    metrics_avg: metrics?.average_degree || metrics?.avg_degree
  });

  return (
    <Card sx={{ p: 4, boxShadow: 3, borderRadius: 2 }}>
      <CardContent>
        <Stack spacing={3}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6" sx={{ 
              fontWeight: 600,
              color: theme.palette.primary.main 
            }}>
              Network Statistics
            </Typography>
            
            <Tooltip title="Export node data including ID, degree, and community membership">
              <Button
                variant="outlined"
                size="small"
                startIcon={<Download />}
                onClick={handleDownload}
                sx={{ 
                  borderRadius: 2,
                  bgcolor: exportSuccess ? 'success.light' : 'transparent',
                  '&:hover': {
                    bgcolor: exportSuccess ? 'success.light' : 'rgba(25, 118, 210, 0.04)'
                  }
                }}
              >
                {exportSuccess ? 'Downloaded!' : 'Export Node Data (CSV)'}
              </Button>
            </Tooltip>
          </Box>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Total Nodes" 
                value={metrics.node_count}
                icon={<Hub />}
                color={theme.palette.primary.main}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Total Edges" 
                value={metrics.edge_count}
                icon={<Timeline />}
                color={theme.palette.primary.main}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Density" 
                value={metrics.density}
                icon={<Share />}
                color={theme.palette.primary.main}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Clustering coefficient" 
                value={metrics.clustering}
                icon={<AccountTree />}
                color={theme.palette.primary.main}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Assortativity" 
                value={metrics.assortativity}
                icon={<Share />}
                color={theme.palette.primary.main}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Average degree" 
                value={averageDegree}
                icon={<Share />}
                color={theme.palette.primary.main}
              />
            </Grid>
          </Grid>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default GraphStats;