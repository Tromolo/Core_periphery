import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Card, Typography, Box, Divider, Grid } from "@mui/material";

const ConnectedComponentsChart = ({ metrics }) => {
  if (!metrics || !metrics.connected_components) return null;

  const { 
    num_components, 
    largest_component_size, 
    smallest_component_size,
    component_size_distribution 
  } = metrics.connected_components;

  // Transform the component size distribution for the chart
  const chartData = component_size_distribution?.map((item, index) => ({
    name: `Component ${index + 1}`,
    size: item
  })) || [];

  // Sort by size in descending order
  chartData.sort((a, b) => b.size - a.size);

  // Summary statistics
  const summaryData = [
    { name: "Number of Components", value: num_components || 0 },
    { name: "Largest Component Size", value: largest_component_size || 0 },
    { name: "Smallest Component Size", value: smallest_component_size || 0 }
  ];

  return (
    <Card sx={{ p: 4, boxShadow: 3, borderRadius: 2 }}>
      <Typography variant="h6" gutterBottom>
        Connected Components Analysis
      </Typography>
      <Divider sx={{ mb: 3 }} />

      <Grid container spacing={3}>
        {/* Summary statistics */}
        <Grid item xs={12} md={4}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
              Summary Statistics
            </Typography>
            {summaryData.map((item, index) => (
              <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  {item.name}:
                </Typography>
                <Typography variant="body2" fontWeight="bold">
                  {item.value}
                </Typography>
              </Box>
            ))}
          </Box>
        </Grid>

        {/* Size distribution chart */}
        <Grid item xs={12} md={8}>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
            Component Size Distribution
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'Size (nodes)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="size" fill="#3f51b5" name="Component Size" />
            </BarChart>
          </ResponsiveContainer>
          <Typography variant="body2" sx={{ mt: 2, textAlign: 'center', color: 'text.secondary' }}>
            Distribution of connected component sizes in the network
          </Typography>
        </Grid>
      </Grid>
    </Card>
  );
};

export default ConnectedComponentsChart;
