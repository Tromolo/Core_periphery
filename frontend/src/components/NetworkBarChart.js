import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Card, Typography } from "@mui/material";

const NetworkBarChart = ({ stats }) => {
  if (!stats) return null;

  // Transform the data to match the expected format
  const data = [
    { name: "Vertices", value: stats.node_count || 0 },
    { name: "Edges", value: stats.edge_count || 0 },
    { name: "Density", value: parseFloat((stats.density || 0).toFixed(3)) },
    { name: "Avg Clustering", value: parseFloat((stats.clustering || 0).toFixed(3)) },
    { name: "Modularity", value: parseFloat((stats.modularity || 0).toFixed(3)) },
  ];

  // Add path length if available
  if (stats.avg_path_length) {
    data.push({ 
      name: "Avg Path Length", 
      value: parseFloat(stats.avg_path_length.toFixed(2)) 
    });
  }

  return (
    <Card sx={{ p: 4, boxShadow: 3, borderRadius: 2, textAlign: "center" }}>
      <Typography variant="h6" gutterBottom>
        Network Statistics
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="value" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default NetworkBarChart;