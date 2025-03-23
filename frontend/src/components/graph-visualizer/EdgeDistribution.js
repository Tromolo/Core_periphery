import React, { useMemo } from 'react';
import { Box, Grid, Typography, Paper } from '@mui/material';

const EdgeDistribution = ({ graphData }) => {
  const edgeStats = useMemo(() => {
    if (!graphData?.nodes || !graphData?.edges) return null;
    
    // Handle both formats: original graph data (type: 'C'/'P') and processed graph data (isCore: true/false)
    const coreNodeIds = new Set();
    graphData.nodes.forEach(node => {
      if ((node.type === 'C') || (node.isCore === true)) {
        coreNodeIds.add(node.id);
      }
    });
    
    let coreCore = 0;
    let corePeriphery = 0;
    let peripheryPeriphery = 0;
    
    graphData.edges.forEach(edge => {
      const sourceIsCore = coreNodeIds.has(edge.source);
      const targetIsCore = coreNodeIds.has(edge.target);
      
      if (sourceIsCore && targetIsCore) {
        coreCore++;
      } else if ((!sourceIsCore && targetIsCore) || (sourceIsCore && !targetIsCore)) {
        corePeriphery++;
      } else {
        peripheryPeriphery++;
      }
    });
    
    const total = graphData.edges.length;
    return {
      coreCore,
      corePeriphery,
      peripheryPeriphery,
      total,
      coreCorePct: ((coreCore / total) * 100).toFixed(1),
      corePeripheryPct: ((corePeriphery / total) * 100).toFixed(1),
      peripheryPeripheryPct: ((peripheryPeriphery / total) * 100).toFixed(1)
    };
  }, [graphData]);
  
  if (!edgeStats) return null;
  
  return (
    <Grid container spacing={2} sx={{ mt: 2 }}>
      <Grid item xs={12}>
        <Typography variant="h6" sx={{ mb: 1 }}>Connection Patterns</Typography>
        <Paper elevation={2} sx={{ p: 2, borderRadius: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Edge Distribution</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'rgba(211, 47, 47, 0.1)', borderRadius: 2 }}>
                <Typography variant="body2" color="error">Core-Core</Typography>
                <Typography variant="h6">{edgeStats.coreCore}</Typography>
                <Typography variant="caption">({edgeStats.coreCorePct}%)</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'rgba(158, 158, 158, 0.1)', borderRadius: 2 }}>
                <Typography variant="body2" color="text.secondary">Core-Periphery</Typography>
                <Typography variant="h6">{edgeStats.corePeriphery}</Typography>
                <Typography variant="caption">({edgeStats.corePeripheryPct}%)</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'rgba(25, 118, 210, 0.1)', borderRadius: 2 }}>
                <Typography variant="body2" color="primary">Periphery-Periphery</Typography>
                <Typography variant="h6">{edgeStats.peripheryPeriphery}</Typography>
                <Typography variant="caption">({edgeStats.peripheryPeripheryPct}%)</Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default EdgeDistribution; 