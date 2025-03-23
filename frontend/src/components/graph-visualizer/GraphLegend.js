import React from 'react';
import { Box, Typography, Paper, useTheme } from '@mui/material';

// Component to display a single legend item with color indicator
const LegendItem = ({ color, label }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', mr: 3, mb: 1 }}>
    <Box 
      sx={{ 
        width: 16, 
        height: 16, 
        backgroundColor: color, 
        borderRadius: '50%', 
        mr: 1, 
        border: '1px solid rgba(0, 0, 0, 0.1)',
      }} 
    />
    <Typography variant="body2">{label}</Typography>
  </Box>
);

const GraphLegend = () => {
  const theme = useTheme();
  
  return (
    <Paper 
      elevation={1} 
      sx={{ 
        p: 1.5, 
        mb: 2, 
        borderRadius: 1,
        backgroundColor: theme.palette.background.paper,
      }}
    >
      <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
        Graph Legend
      </Typography>
      
      <Box sx={{ display: 'flex', flexWrap: 'wrap' }}>
        {/* Node Types */}
        <Box sx={{ minWidth: '200px', mb: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
            Node Types:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap' }}>
            <LegendItem color="#d32f2f" label="Core" />
            <LegendItem color="#1976d2" label="Periphery" />
          </Box>
        </Box>
        
        {/* Edge Types */}
        <Box sx={{ minWidth: '250px' }}>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
            Edge Types:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap' }}>
            <LegendItem color="#d32f2f" label="Core-Core" />
            <LegendItem color="#9c27b0" label="Core-Periphery" />
            <LegendItem color="#1976d2" label="Periphery-Periphery" />
          </Box>
        </Box>
      </Box>
    </Paper>
  );
};

export default GraphLegend; 