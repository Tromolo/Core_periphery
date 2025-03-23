import React from "react";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";
import { Card, Typography, Box, Divider, Grid } from "@mui/material";

const ConnectedComponentsChart = ({ metrics }) => {
  if (!metrics || !metrics.connected_components) return null;

  const { 
    num_components, 
    largest_component_size, 
    smallest_component_size,
    component_size_distribution 
  } = metrics.connected_components;

  const chartData = component_size_distribution?.map((item, index) => ({
    name: `Component ${index + 1}`,
    size: item
  })) || [];

  chartData.sort((a, b) => b.size - a.size);

  const summaryData = [
    { name: "Number of Components", value: num_components || 0 },
    { name: "Largest Component Size", value: largest_component_size || 0 },
    { name: "Smallest Component Size", value: smallest_component_size || 0 }
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <Box sx={{ 
          backgroundColor: 'rgba(255, 255, 255, 0.9)', 
          p: 1.5, 
          border: '1px solid #ccc',
          borderRadius: 1,
          boxShadow: '0px 2px 5px rgba(0,0,0,0.1)'
        }}>
          <Typography variant="body2" fontWeight="bold">
            {label}
          </Typography>
          <Typography variant="body2">
            Size: {payload[0].value} nodes
          </Typography>
        </Box>
      );
    }
    return null;
  };

  return (
    <Card sx={{ p: 4, boxShadow: 3, borderRadius: 2 }}>
      <Typography variant="h6" gutterBottom>
        Connected Components Analysis
      </Typography>
      <Divider sx={{ mb: 3 }} />

      <Grid container spacing={3}>
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

        <Grid item xs={12} md={8}>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
            Component Size Distribution
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart 
              data={chartData} 
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'Size (nodes)', angle: -90, position: 'insideLeft' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="size" 
                fill="#4C6EF5" 
                radius={[4, 4, 0, 0]}
                animationDuration={1500}
                isAnimationActive={true}
              />
            </BarChart>
          </ResponsiveContainer>
          <Typography variant="body2" sx={{ mt: 2, textAlign: 'center', color: 'text.secondary' }}>
            Hover over bars to see detailed component sizes
          </Typography>
        </Grid>
      </Grid>
    </Card>
  );
};

export default ConnectedComponentsChart;
