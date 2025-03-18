import React from 'react';
import { 
  Box, 
  Card, 
  Typography, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper,
  Grow
} from '@mui/material';

const MetricsTable = ({ metrics }) => {
  if (!metrics) return null;

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
          Analysis Results
        </Typography>
      </Box>

      <Grow in={true} timeout={500}>
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
            Algorithm Parameters
          </Typography>
          <TableContainer component={Paper} sx={{ mb: 4, boxShadow: 'none' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Parameter</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Value</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {metrics.algorithm_params && Object.entries(metrics.algorithm_params).map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell>{key}</TableCell>
                    <TableCell>{value}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mb: 2, mt: 4 }}>
            Top Nodes by Coreness
          </Typography>
          <TableContainer component={Paper} sx={{ boxShadow: 'none', mb: 4 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Node ID</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Type</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Coreness</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Betweenness</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Degree</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {metrics.top_nodes && metrics.top_nodes.top_core_nodes && metrics.top_nodes.top_core_nodes.map((node) => (
                  <TableRow key={node.id}>
                    <TableCell>{node.id}</TableCell>
                    <TableCell>{node.type}</TableCell>
                    <TableCell>{node.coreness.toFixed(4)}</TableCell>
                    <TableCell>{node.betweenness.toFixed(4)}</TableCell>
                    <TableCell>{node.degree}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mb: 2, mt: 4 }}>
            Top Nodes by Peripheriness
          </Typography>
          <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Node ID</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Type</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Coreness</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Betweenness</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Degree</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {metrics.top_nodes && metrics.top_nodes.top_periphery_nodes && metrics.top_nodes.top_periphery_nodes.map((node) => (
                  <TableRow key={node.id}>
                    <TableCell>{node.id}</TableCell>
                    <TableCell>{node.type}</TableCell>
                    <TableCell>{node.coreness.toFixed(4)}</TableCell>
                    <TableCell>{node.betweenness.toFixed(4)}</TableCell>
                    <TableCell>{node.degree}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>
      </Grow>
    </Box>
  );
};

export default MetricsTable; 