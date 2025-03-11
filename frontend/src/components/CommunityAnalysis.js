import React from "react";
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Divider,
  Card,
  CardContent,
  Chip
} from "@mui/material";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

const CommunityAnalysis = ({ communityData }) => {
  if (!communityData) return null;

  const { 
    num_communities, 
    mean_size, 
    max_size, 
    min_size, 
    modularity, 
    size_distribution,
    visualization_file
  } = communityData;

  // Colors for the pie chart
  const COLORS = ['#1a237e', '#303f9f', '#3f51b5', '#5c6bc0', '#7986cb', '#9fa8da'];

  // Prepare data for pie chart
  const pieData = size_distribution.map(item => ({
    name: `Community ${item.community}`,
    value: item.size
  }));

  return (
    <Paper
      elevation={0}
      sx={{
        p: 4,
        borderRadius: 4,
        background: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        textAlign: "center",
      }}
    >
      <Typography variant="h4" sx={{ mb: 3, fontWeight: "bold", color: "primary.main" }}>
        Community Structure Analysis
      </Typography>

      <Grid container spacing={4}>
        <Grid item xs={12} md={6}>
          <Card elevation={0} sx={{ height: '100%', borderRadius: 4, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Community Statistics</Typography>
              <Divider sx={{ mb: 3 }} />
              
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                  <Typography variant="body1">Number of Communities:</Typography>
                  <Chip color="primary" label={num_communities} />
                </Box>
                
                <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                  <Typography variant="body1">Average Community Size:</Typography>
                  <Chip color="primary" label={mean_size} />
                </Box>
                
                <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                  <Typography variant="body1">Largest Community:</Typography>
                  <Chip color="primary" label={max_size} />
                </Box>
                
                <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                  <Typography variant="body1">Smallest Community:</Typography>
                  <Chip color="primary" label={min_size} />
                </Box>
                
                <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                  <Typography variant="body1">Modularity Score:</Typography>
                  <Chip color="primary" label={modularity.toFixed(3)} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card elevation={0} sx={{ height: '100%', borderRadius: 4, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Community Size Distribution</Typography>
              <Divider sx={{ mb: 2 }} />
              
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    fill="#8884d8"
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      
        <Grid item xs={12}>
          <Card elevation={0} sx={{ borderRadius: 4, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Community Size Distribution</Typography>
              <Divider sx={{ mb: 3 }} />
              
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={size_distribution}>
                  <XAxis 
                    dataKey="community" 
                    label={{ 
                      value: "Community ID", 
                      position: "insideBottom", 
                      dy: 10,
                      fill: "#1a237e"
                    }} 
                  />
                  <YAxis 
                    label={{ 
                      value: "Number of Nodes", 
                      angle: -90, 
                      position: "insideLeft",
                      dy: 50,
                      fill: "#1a237e"
                    }} 
                  />
                  <Tooltip 
                    formatter={(value, name) => [`${value} nodes`, 'Size']}
                    labelFormatter={(value) => `Community ${value}`}
                  />
                  <Bar 
                    dataKey="size" 
                    fill="#1a237e" 
                    radius={[4, 4, 0, 0]} 
                    animationDuration={1500}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        
        {visualization_file && (
          <Grid item xs={12}>
            <Card elevation={0} sx={{ borderRadius: 4, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>Community Visualization</Typography>
                <Divider sx={{ mb: 3 }} />
                
                <Box sx={{ textAlign: 'center' }}>
                  <img 
                    src={`http://localhost:8080/static/${visualization_file}`}
                    alt="Community Visualization" 
                    style={{ maxWidth: '100%', height: 'auto', borderRadius: '8px' }}
                    onError={(e) => {
                      console.error("Failed to load image:", e);
                      console.error("Image URL was:", e.target.src);
                      e.target.src = "https://via.placeholder.com/800x600?text=Visualization+Not+Available";
                    }}
                  />
                </Box>
                
                <Typography variant="body2" sx={{ mt: 2, textAlign: 'center', color: 'text.secondary' }}>
                  Each color represents a different community detected using the Louvain method.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Paper>
  );
};

export default CommunityAnalysis;