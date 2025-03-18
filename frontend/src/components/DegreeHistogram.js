import React, { useMemo, useState, useCallback } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid, Cell, Line, ComposedChart } from "recharts";
import { Card, Typography, Box, Divider, useTheme, Button, Dialog, DialogTitle, DialogContent, DialogActions, Paper, Stack, Switch, FormControlLabel, ToggleButtonGroup, ToggleButton } from "@mui/material";
import { Refresh as RefreshIcon, BarChart as BarChartIcon, BubbleChart as BubbleChartIcon } from '@mui/icons-material';

const DegreeHistogram = ({ graphData, communityData }) => {
  const theme = useTheme();
  const [debugOpen, setDebugOpen] = useState(false);
  const [forceUpdate, setForceUpdate] = useState(0);
  const [showLogScale, setShowLogScale] = useState(false);
  const [viewMode, setViewMode] = useState('byNode'); // Changed default to 'byNode' instead of 'distribution'
  const [nodeLimit, setNodeLimit] = useState(20); // Limit number of nodes to display
  
  // If no graph data is available, don't render anything
  if ((!graphData || !graphData.nodes) && (!communityData || !communityData.graph_data || !communityData.graph_data.nodes)) {
    return null;
  }

  // Determine which data source to use
  const nodes = useMemo(() => {
    if (graphData && graphData.nodes) {
      return graphData.nodes;
    } else if (communityData && communityData.graph_data && communityData.graph_data.nodes) {
      return communityData.graph_data.nodes;
    }
    return [];
  }, [graphData, communityData, forceUpdate]);

  // Get edges from the graph data
  const edges = useMemo(() => {
    if (graphData && graphData.edges) {
      return graphData.edges;
    } else if (communityData && communityData.graph_data && communityData.graph_data.edges) {
      return communityData.graph_data.edges;
    }
    return [];
  }, [graphData, communityData, forceUpdate]);

  // Calculate degree for each node based on edges
  const nodeDegreesMap = useMemo(() => {
    const degreeMap = {};
    
    // Initialize all nodes with degree 0
    nodes.forEach(node => {
      degreeMap[node.id] = 0;
    });
    
    // Count connections for each node
    edges.forEach(edge => {
      // Make sure source and target are strings for consistent comparison
      const source = String(edge.source);
      const target = String(edge.target);
      
      if (degreeMap[source] !== undefined) {
        degreeMap[source]++;
      } else {
        // If node wasn't in our initial list, add it
        degreeMap[source] = 1;
      }
      
      if (degreeMap[target] !== undefined) {
        degreeMap[target]++;
      } else {
        // If node wasn't in our initial list, add it
        degreeMap[target] = 1;
      }
    });
    
    // If we have no edges but nodes have degree property, use that
    if (edges.length === 0) {
      nodes.forEach(node => {
        if (node.degree !== undefined) {
          degreeMap[node.id] = node.degree;
        }
      });
    }
    
    console.log('Calculated node degrees:', degreeMap);
    console.log('Sample node from data:', nodes.length > 0 ? nodes[0] : 'No nodes');
    console.log('Sample edge from data:', edges.length > 0 ? edges[0] : 'No edges');
    
    return degreeMap;
  }, [nodes, edges, forceUpdate]);

  // Function to handle refresh
  const handleRefresh = useCallback(() => {
    setForceUpdate(prev => prev + 1);
  }, []);

  // Calculate degree distribution from graph data
  const degreeDistribution = useMemo(() => {
    // Count nodes by degree
    const degreeCounts = {};
    
    // Use the calculated degrees or fallback to node.degree if available
    nodes.forEach(node => {
      // First try to use our calculated degree
      let degree = nodeDegreesMap[node.id] || 0;
      
      // If that's 0, try to use the degree property from the node if available
      if (degree === 0 && node.degree !== undefined) {
        degree = node.degree;
      }
      
      // Count nodes with this degree
      degreeCounts[degree] = (degreeCounts[degree] || 0) + 1;
    });
    
    // Convert to array for chart
    const distribution = Object.entries(degreeCounts)
      .map(([degree, count]) => ({
        degree: parseInt(degree),
        count
      }))
      .sort((a, b) => a.degree - b.degree);
    
    // Add log values for power law analysis
    distribution.forEach(item => {
      if (item.degree > 0 && item.count > 0) {
        item.logDegree = Math.log10(item.degree);
        item.logCount = Math.log10(item.count);
      } else {
        item.logDegree = 0;
        item.logCount = 0;
      }
    });
    
    return distribution;
  }, [nodes, nodeDegreesMap, forceUpdate]);

  // Prepare data for node-by-node view
  const nodeByNodeData = useMemo(() => {
    // Create array of all nodes with their degrees
    const nodeData = Object.entries(nodeDegreesMap).map(([nodeId, degree]) => ({
      nodeId,
      degree,
      // Add any additional node properties we might want to display
      type: nodes.find(n => String(n.id) === String(nodeId))?.type || 'unknown'
    }));
    
    // Sort by degree (descending)
    nodeData.sort((a, b) => b.degree - a.degree);
    
    // Take top nodes by degree (limited by nodeLimit)
    return nodeData.slice(0, nodeLimit);
  }, [nodeDegreesMap, nodes, forceUpdate, nodeLimit]);

  // Calculate basic network statistics that can be reliably derived from the data
  const basicStats = useMemo(() => {
    // If we don't have nodes and edges, return empty stats
    if (!nodes.length || !edges.length) return {};
    
    // Total nodes and edges are straightforward
    const nodeCount = nodes.length;
    const edgeCount = edges.length;
    
    // Calculate degree-based statistics
    const degrees = nodes.map(node => {
      // First try to use our calculated degree
      let degree = nodeDegreesMap[node.id] || 0;
      
      // If that's 0, try to use the degree property from the node if available
      if (degree === 0 && node.degree !== undefined) {
        degree = node.degree;
      }
      
      return degree;
    });
    
    const sum = degrees.reduce((a, b) => a + b, 0);
    const avg = sum / degrees.length;
    const max = Math.max(...degrees);
    const min = Math.min(...degrees);
    
    // Calculate median
    const sortedDegrees = [...degrees].sort((a, b) => a - b);
    const mid = Math.floor(sortedDegrees.length / 2);
    const median = sortedDegrees.length % 2 === 0
      ? (sortedDegrees[mid - 1] + sortedDegrees[mid]) / 2
      : sortedDegrees[mid];
    
    // Calculate density
    // Density = 2*E/N(N-1) for undirected networks
    const density = (2 * edgeCount) / (nodeCount * (nodeCount - 1));
    
    return {
      nodes: nodeCount,
      edges: edgeCount,
      avgDegree: avg.toFixed(2),
      medianDegree: median.toFixed(2),
      maxDegree: max,
      minDegree: min,
      density: density.toFixed(4)
    };
  }, [nodes, edges, nodeDegreesMap, forceUpdate]);

  // Define colors for the bars based on degree value
  const getBarColor = (degree) => {
    if (degree <= 2) return theme.palette.info.light;
    if (degree <= 5) return theme.palette.primary.main;
    if (degree <= 10) return theme.palette.secondary.main;
    return theme.palette.error.main;
  };

  // Debug function to show data details
  const handleDebugClick = () => {
    setDebugOpen(true);
  };

  // Toggle log scale
  const handleToggleLogScale = () => {
    setShowLogScale(!showLogScale);
  };

  // Toggle view mode
  const handleViewModeChange = (event, newMode) => {
    if (newMode !== null) {
      setViewMode(newMode);
    }
  };

  // Handle node limit change
  const handleNodeLimitChange = (event) => {
    setNodeLimit(Math.max(5, parseInt(event.target.value) || 20));
  };

  return (
    <Card sx={{ p: 4, boxShadow: 3, borderRadius: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, color: theme.palette.primary.main }}>
          Node Degree Analysis
        </Typography>
        <Stack direction="row" spacing={1}>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={handleViewModeChange}
            size="small"
            aria-label="view mode"
          >
            <ToggleButton value="byNode" aria-label="by node view">
              <BubbleChartIcon fontSize="small" />
            </ToggleButton>
            <ToggleButton value="distribution" aria-label="distribution view">
              <BarChartIcon fontSize="small" />
            </ToggleButton>
          </ToggleButtonGroup>
          
          {viewMode === 'byNode' && (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Typography variant="caption" sx={{ mr: 1 }}>
                Show top:
              </Typography>
              <select 
                value={nodeLimit}
                onChange={handleNodeLimitChange}
                style={{ padding: '2px 5px', borderRadius: '4px', border: '1px solid #ccc' }}
              >
                <option value="10">10 nodes</option>
                <option value="20">20 nodes</option>
                <option value="50">50 nodes</option>
                <option value="100">100 nodes</option>
              </select>
            </Box>
          )}
          
          {viewMode === 'distribution' && (
            <FormControlLabel
              control={
                <Switch 
                  checked={showLogScale}
                  onChange={handleToggleLogScale}
                  size="small"
                />
              }
              label="Log Scale"
              sx={{ mr: 2 }}
            />
          )}
          
          <Button 
            size="small" 
            variant="outlined" 
            onClick={handleRefresh}
            startIcon={<RefreshIcon />}
            sx={{ fontSize: '0.7rem' }}
          >
            Recalculate
          </Button>
          <Button 
            size="small" 
            variant="outlined" 
            onClick={handleDebugClick}
            sx={{ fontSize: '0.7rem' }}
          >
            Debug Data
          </Button>
        </Stack>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {viewMode === 'distribution' 
          ? "Analysis of how connections are distributed across nodes in the network"
          : "Node degrees ordered by connection count, showing the most connected nodes"}
      </Typography>
      <Divider sx={{ mb: 3 }} />
      
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
          Degree Statistics
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Avg. Degree:
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {basicStats.avgDegree || 0}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Median Degree:
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {basicStats.medianDegree || 0}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Max Degree:
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {basicStats.maxDegree || 0}
            </Typography>
          </Box>
        </Box>
      </Box>
      
      <ResponsiveContainer width="100%" height={400}>
        {viewMode === 'distribution' ? (
          showLogScale ? (
            <ComposedChart data={degreeDistribution.filter(d => d.degree > 0 && d.count > 0)} margin={{ top: 20, right: 30, left: 20, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey="logDegree" 
                label={{ 
                  value: 'Log(Degree)', 
                  position: 'insideBottom', 
                  offset: -10,
                  style: { fill: theme.palette.text.secondary }
                }}
                tick={{ fill: theme.palette.text.secondary }}
                domain={['auto', 'auto']}
              />
              <YAxis 
                dataKey="logCount"
                label={{ 
                  value: 'Log(Count)', 
                  angle: -90, 
                  position: 'insideLeft',
                  style: { fill: theme.palette.text.secondary }
                }}
                tick={{ fill: theme.palette.text.secondary }}
                domain={['auto', 'auto']}
              />
              <Tooltip 
                formatter={(value, name) => [value.toFixed(2), name === 'logCount' ? 'Log(Count)' : 'Count']}
                labelFormatter={(value) => `Log(Degree): ${value.toFixed(2)}`}
                contentStyle={{ 
                  backgroundColor: theme.palette.background.paper,
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 4
                }}
              />
              <Legend wrapperStyle={{ paddingTop: 10 }} />
              <Line 
                type="monotone" 
                dataKey="logCount" 
                stroke={theme.palette.primary.main} 
                name="Log(Count)" 
                dot={{ fill: theme.palette.primary.main, r: 4 }}
              />
            </ComposedChart>
          ) : (
            <BarChart data={degreeDistribution} margin={{ top: 20, right: 30, left: 20, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey="degree" 
                label={{ 
                  value: 'Node Degree', 
                  position: 'insideBottom', 
                  offset: -10,
                  style: { fill: theme.palette.text.secondary }
                }}
                tick={{ fill: theme.palette.text.secondary }}
              />
              <YAxis 
                label={{ 
                  value: 'Number of Nodes', 
                  angle: -90, 
                  position: 'insideLeft',
                  style: { fill: theme.palette.text.secondary }
                }}
                tick={{ fill: theme.palette.text.secondary }}
              />
              <Tooltip 
                formatter={(value, name) => [value, 'Number of Nodes']}
                labelFormatter={(value) => `Degree: ${value}`}
                contentStyle={{ 
                  backgroundColor: theme.palette.background.paper,
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 4
                }}
              />
              <Legend wrapperStyle={{ paddingTop: 10 }} />
              <Bar 
                dataKey="count" 
                name="Node Count" 
                radius={[4, 4, 0, 0]}
              >
                {degreeDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.degree)} />
                ))}
              </Bar>
            </BarChart>
          )
        ) : (
          // Node-by-node view
          <BarChart data={nodeByNodeData} margin={{ top: 20, right: 30, left: 20, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis 
              dataKey="nodeId" 
              label={{ 
                value: 'Node ID', 
                position: 'insideBottom', 
                offset: -10,
                style: { fill: theme.palette.text.secondary }
              }}
              tick={{ fill: theme.palette.text.secondary }}
            />
            <YAxis 
              label={{ 
                value: 'Degree', 
                angle: -90, 
                position: 'insideLeft',
                style: { fill: theme.palette.text.secondary }
              }}
              tick={{ fill: theme.palette.text.secondary }}
              domain={[0, 'auto']}
            />
            <Tooltip 
              formatter={(value, name) => [value, 'Degree']}
              labelFormatter={(value) => `Node: ${value}`}
              contentStyle={{ 
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 4
              }}
            />
            <Legend wrapperStyle={{ paddingTop: 10 }} />
            <Bar 
              dataKey="degree" 
              name="Node Degree" 
              radius={[4, 4, 0, 0]}
            >
              {nodeByNodeData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.degree)} />
              ))}
            </Bar>
          </BarChart>
        )}
      </ResponsiveContainer>
      
      <Box sx={{ mt: 3, p: 2, bgcolor: 'rgba(0,0,0,0.02)', borderRadius: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
          What does this mean?
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {viewMode === 'distribution' ? (
            <>
              The degree distribution shows how connections are spread across nodes in the network. 
              Nodes with higher degrees are more central to the network's structure. 
              {showLogScale ? (
                <> 
                  In log-log scale, a straight line indicates a power-law distribution, typical of scale-free networks.
                  Scale-free networks have many nodes with few connections and a few highly connected hubs.
                </>
              ) : (
                <>
                  A long-tailed distribution (many low-degree nodes, few high-degree nodes) is typical of scale-free networks 
                  often found in real-world systems. Toggle to log scale to check for power-law distribution.
                </>
              )}
            </>
          ) : (
            <>
              This chart shows the degree (number of connections) for the top {nodeLimit} most connected nodes.
              These high-degree nodes are often the hubs of the network and play critical roles in information flow.
              Comparing the degree values across nodes helps identify the most important entities in the network structure.
            </>
          )}
        </Typography>
      </Box>

      {/* Debug Dialog */}
      <Dialog 
        open={debugOpen} 
        onClose={() => setDebugOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Debug Data</DialogTitle>
        <DialogContent>
          <Typography variant="subtitle1" gutterBottom>Node Count: {nodes.length}</Typography>
          <Typography variant="subtitle1" gutterBottom>Edge Count: {edges.length}</Typography>
          
          <Typography variant="subtitle1" sx={{ mt: 2 }}>Sample Nodes:</Typography>
          <Paper sx={{ p: 2, maxHeight: 200, overflow: 'auto', mb: 2 }}>
            <pre>{JSON.stringify(nodes.slice(0, 5), null, 2)}</pre>
          </Paper>
          
          <Typography variant="subtitle1">Sample Edges:</Typography>
          <Paper sx={{ p: 2, maxHeight: 200, overflow: 'auto', mb: 2 }}>
            <pre>{JSON.stringify(edges.slice(0, 5), null, 2)}</pre>
          </Paper>
          
          <Typography variant="subtitle1">Calculated Degrees (sample):</Typography>
          <Paper sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
            <pre>{JSON.stringify(
              Object.entries(nodeDegreesMap)
                .slice(0, 10)
                .reduce((obj, [key, value]) => {
                  obj[key] = value;
                  return obj;
                }, {}), 
              null, 2)}</pre>
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDebugOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default DegreeHistogram; 