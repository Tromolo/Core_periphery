import React from 'react';
import { 
  Card, 
  Typography, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Paper,
  Box,
  Divider
} from '@mui/material';

const MetricsTable = ({ metrics }) => {
  if (!metrics) return null;

  // Define the metrics to display in the table
  const tableData = [
    { name: "Network Density", value: metrics.density?.toFixed(4) || "N/A", description: "Ratio of actual connections to possible connections" },
    { name: "Average Clustering Coefficient", value: metrics.clustering?.toFixed(4) || "N/A", description: "Measure of how nodes tend to cluster together" },
    { name: "Average Path Length", value: metrics.avg_path_length || "N/A", description: "Average number of steps along the shortest paths between all pairs of nodes" },
    { name: "Diameter", value: metrics.diameter || "N/A", description: "Maximum distance between any pair of nodes in the network" },
    { name: "Assortativity Coefficient", value: metrics.assortativity?.toFixed(4) || "N/A", description: "Tendency of nodes to connect to similar nodes" },
    { name: "Core-Periphery Coefficient", value: metrics.core_periphery_coefficient?.toFixed(4) || "N/A", description: "Measure of how well the network fits a core-periphery structure" },
    { name: "Modularity", value: metrics.modularity?.toFixed(4) || "N/A", description: "Measure of the strength of division into communities" }
  ];

  // Add core-periphery specific metrics if available
  if (metrics.core_stats) {
    tableData.push(
      { name: "Core Size", value: metrics.core_stats.core_size || "N/A", description: "Number of nodes in the core" },
      { name: "Periphery Size", value: metrics.core_stats.periphery_size || "N/A", description: "Number of nodes in the periphery" },
      { name: "Core Density", value: metrics.core_stats.core_density?.toFixed(4) || "N/A", description: "Density of connections within the core" },
      { name: "Periphery Density", value: metrics.core_stats.periphery_density?.toFixed(4) || "N/A", description: "Density of connections within the periphery" },
      { name: "Core-Periphery Density", value: metrics.core_stats.core_periphery_density?.toFixed(4) || "N/A", description: "Density of connections between core and periphery" }
    );
  }

  return (
    <Card sx={{ p: 4, boxShadow: 3, borderRadius: 2 }}>
      <Typography variant="h6" gutterBottom>
        Network Metrics Summary
      </Typography>
      <Divider sx={{ mb: 3 }} />
      
      <TableContainer component={Paper} elevation={0} sx={{ maxHeight: 440 }}>
        <Table stickyHeader aria-label="network metrics table">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f7' }}>Metric</TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f7' }}>Value</TableCell>
              <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f7' }}>Description</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tableData.map((row, index) => (
              <TableRow
                key={index}
                sx={{ '&:nth-of-type(odd)': { backgroundColor: 'rgba(0, 0, 0, 0.02)' } }}
              >
                <TableCell component="th" scope="row">
                  <Typography variant="body2" fontWeight="medium">
                    {row.name}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="body2" fontWeight="bold">
                    {row.value}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {row.description}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          These metrics provide a comprehensive overview of the network's structural properties.
        </Typography>
      </Box>
    </Card>
  );
};

export default MetricsTable; 