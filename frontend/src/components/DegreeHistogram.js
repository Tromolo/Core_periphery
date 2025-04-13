import React, { useMemo, useState, useCallback, useEffect, useRef } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid, Cell, ScatterChart, Scatter, ZAxis, ReferenceLine } from "recharts";
import { Card, Typography, Box, Divider, useTheme, Button, Stack, Switch, FormControlLabel, CircularProgress } from "@mui/material";
import { Refresh as RefreshIcon } from '@mui/icons-material';

const DegreeHistogram = ({ graphData, communityData, networkMetrics }) => {
  const theme = useTheme();
  const [forceUpdate, setForceUpdate] = useState(0);
  const [showLogScale, setShowLogScale] = useState(false);
  const chartContainerRef = useRef(null);
  const [chartLoading, setChartLoading] = useState(false);
  
  if ((!graphData || !graphData.nodes) && (!communityData || !communityData.graph_data || !communityData.graph_data.nodes)) {
    return null;
  }

  const nodes = useMemo(() => {
    if (graphData && graphData.nodes) {
      return graphData.nodes;
    } else if (communityData && communityData.graph_data && communityData.graph_data.nodes) {
      return communityData.graph_data.nodes;
    }
    return [];
  }, [graphData, communityData, forceUpdate]);

  const edges = useMemo(() => {
    if (graphData && graphData.edges) {
      return graphData.edges;
    } else if (communityData && communityData.graph_data && communityData.graph_data.edges) {
      return communityData.graph_data.edges;
    }
    return [];
  }, [graphData, communityData, forceUpdate]);

  const nodeDegreesMap = useMemo(() => {
    const degreeMap = {};
    
    nodes.forEach(node => {
      if (node.degree !== undefined) {
        degreeMap[node.id] = node.degree;
      } else {
        degreeMap[node.id] = 0;
      }
    });
    
    return degreeMap;
  }, [nodes, forceUpdate]);

  const handleRefresh = useCallback(() => {
    setChartLoading(true);
    setTimeout(() => {
    setForceUpdate(prev => prev + 1);
      setChartLoading(false);
    }, 300);
  }, []);

  const degreeDistribution = useMemo(() => {
    if (graphData?.degree_distribution) {
      console.log("Using pre-calculated degree distribution:", graphData.degree_distribution);
      const distribution = graphData.degree_distribution.map(item => ({
        degree: item.degree,
        count: item.count
      })).sort((a, b) => a.degree - b.degree);
    
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
    } else if (nodes.length > 0) {
      const degreeCounts = {};
      
      nodes.forEach(node => {
        const degree = nodeDegreesMap[node.id] || 0;
        degreeCounts[degree] = (degreeCounts[degree] || 0) + 1;
      });
      
      const distribution = Object.entries(degreeCounts)
        .map(([degree, count]) => ({
          degree: parseInt(degree),
          count
        }))
        .sort((a, b) => a.degree - b.degree);

      distribution.forEach(item => {
        if (item.degree > 0 && item.count > 0) {
          item.logDegree = Math.log10(item.degree);
          item.logCount = Math.log10(item.count);
          item.realDegree = item.degree;
        } else {
          item.logDegree = 0;
          item.logCount = 0;
          item.realDegree = 0;
        }
      });
      
      console.log("Manually calculated distribution:", distribution);
      return distribution;
    }
    
    return [];
  }, [graphData, nodes, nodeDegreesMap, forceUpdate]);

  const basicStats = useMemo(() => {
    if (!nodes.length || !edges.length) return {};
    
    const nodeCount = nodes.length;
    const edgeCount = edges.length;
    
    const degrees = nodes.map(node => {
      let degree = nodeDegreesMap[node.id] || 0;
      
      if (degree === 0 && node.degree !== undefined) {
        degree = node.degree;
      }
      
      return degree;
    });
    
    const sum = degrees.reduce((a, b) => a + b, 0);
    const avg = sum / degrees.length;
    const max = Math.max(...degrees);
    const min = Math.min(...degrees);
    
    const sortedDegrees = [...degrees].sort((a, b) => a - b);
    const mid = Math.floor(sortedDegrees.length / 2);
    const median = sortedDegrees.length % 2 === 0
      ? (sortedDegrees[mid - 1] + sortedDegrees[mid]) / 2
      : sortedDegrees[mid];
    
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

  useEffect(() => {
    if (networkMetrics && typeof networkMetrics.updateStats === 'function') {
      console.log("DegreeHistogram updating stats:", basicStats);
      try {
        if (Object.keys(basicStats).length > 0 && 
            (!networkMetrics.basicStats || 
              JSON.stringify(networkMetrics.basicStats) !== JSON.stringify(basicStats))) {
          networkMetrics.updateStats({
            basicStats: basicStats
          });
        }
      } catch (error) {
        console.error("Error updating network metrics:", error);
      }
    }
  }, [basicStats, networkMetrics]);

  const getBarColor = (degree) => {
    if (degree === 0) return theme.palette.grey[400];
    if (degree <= 2) return theme.palette.primary.light;
    if (degree <= 5) return '#3366CC'; // Brighter blue
    if (degree <= 10) return '#4285F4'; // blue
    if (degree <= 20) return '#7B1FA2'; // Purple
    if (degree <= 30) return '#C2185B'; // Pink
    return '#D32F2F'; // Red 
  };

  const getScatterPointColor = (degree, count) => {

    const logDegree = Math.log10(Math.max(1, degree));
    const maxLogDegree = Math.log10(Math.max(1, basicStats.maxDegree || 100));
    const normalizedDegree = logDegree / maxLogDegree;
    

    if (normalizedDegree < 0.2) {
      return `rgba(51, 102, 204, ${0.7 + normalizedDegree * 2})`; // bright blue
    } else if (normalizedDegree < 0.4) {
      return `rgba(106, 27, 154, ${0.7 + normalizedDegree})`; // deep purple
    } else if (normalizedDegree < 0.6) {
      return `rgba(194, 24, 91, ${0.8 + normalizedDegree * 0.2})`; // pink
    } else if (normalizedDegree < 0.8) {
      return `rgba(211, 47, 47, ${0.85 + normalizedDegree * 0.15})`; // red
    } else {
      return `rgba(230, 81, 0, ${0.9 + normalizedDegree * 0.1})`; // orange
    }
  };

  const handleToggleLogScale = () => {
    setChartLoading(true);
    setTimeout(() => {
    setShowLogScale(!showLogScale);
      setChartLoading(false);
    }, 300);
  };

  useEffect(() => {
    setChartLoading(true);
    const timer = setTimeout(() => {
      setChartLoading(false);
    }, 500);
    
    return () => clearTimeout(timer);
  }, [graphData, communityData, forceUpdate]);

  const renderScatterPlot = () => {
    const validLogData = degreeDistribution.filter(item => item.degree > 0 && item.count > 0);
    
    const maxCount = Math.max(...validLogData.map(d => d.count));
    const minSize = 5;
    const maxSize = 24;

    const maxDegree = Math.max(...validLogData.map(d => d.degree));
    const referenceValues = [];
    for (let i = 0; i <= Math.log10(maxDegree); i++) {
      referenceValues.push(Math.pow(10, i));
    }

    const enhancedData = validLogData.map(item => ({
      ...item,
      size: minSize + (maxSize - minSize) * (Math.log10(item.count) / Math.log10(maxCount)),
      pointColor: getScatterPointColor(item.degree, item.count)
    }));
    
    const maxLogX = Math.ceil(Math.log10(maxDegree)) + 0.1;
    const maxLogY = Math.ceil(Math.log10(maxCount)) + 0.1;
    
    const maxTickValue = Math.max(...degreeDistribution.map(d => d.degree), 1);
    const safeTicksArray = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000].filter(n => n <= maxTickValue * 1.2);
    
    return (
      <ScatterChart
        margin={{ top: 20, right: 40, left: 60, bottom: 50 }}
      >
        <CartesianGrid strokeDasharray="4 4" stroke="rgba(0,0,0,0.06)" />
        
        {referenceValues.map((value, index) => (
          <ReferenceLine 
            key={`ref-x-${index}`} 
            x={value} 
            stroke="rgba(0,0,0,0.1)" 
            strokeDasharray="3 3" 
          />
        ))}
        
        <XAxis 
          dataKey="degree"
          type="number"
          scale="log"
          domain={[0.9, Math.pow(10, maxLogX)]}
          allowDataOverflow={true}
          label={{ 
            value: 'Degree (log scale)', 
            position: 'insideBottom', 
            offset: -25,
            style: { textAnchor: 'middle', fontWeight: 500, fontSize: 12 }
          }}
          stroke="#666"
          tickMargin={10}
          ticks={safeTicksArray}
          tickFormatter={tick => {
            if (tick === 1 || tick === 10 || tick === 100 || tick === 1000) {
              return tick;
            }
            return '';
          }}
          interval={0}
        />
        <YAxis 
          dataKey="count"
          type="number"
          scale="log"
          domain={[0.9, Math.pow(10, maxLogY)]}
          allowDataOverflow={true}
          label={{ 
            value: 'Count (log scale)', 
            angle: -90, 
            position: 'insideLeft',
            offset: -35,
            style: { textAnchor: 'middle', fontWeight: 500, fontSize: 12 }
          }}
          stroke="#666"
          tickMargin={8}
          tick={{ fontSize: 12 }}
          width={45}
        />
        <Tooltip 
          formatter={(value, name) => {
            if (name === 'count') return [`${value} nodes`, 'Count'];
            return [value, 'Degree'];
          }}
          labelFormatter={(label) => `Degree: ${label}`}
          cursor={{ strokeDasharray: '3 3' }}
          contentStyle={{ 
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.1)',
            border: 'none',
            borderRadius: '4px',
            padding: '12px'
          }}
          wrapperStyle={{ zIndex: 100 }}
        />
        <Scatter 
          name="Degree Distribution"
          data={enhancedData} 
          shape="circle"
          isAnimationActive={false}
        >
          {enhancedData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={entry.pointColor}
              stroke="rgba(255, 255, 255, 0.7)"
              strokeWidth={1}
              r={entry.size}
            />
          ))}
        </Scatter>
      </ScatterChart>
    );
  };

  const renderBarChart = () => {
    return (
      <BarChart 
        data={degreeDistribution} 
        barCategoryGap="10%"
        barGap={0}
        margin={{ top: 20, right: 30, left: 60, bottom: 50 }}
      >
        <CartesianGrid strokeDasharray="4 4" stroke="#e0e0e0" />
        <XAxis 
          dataKey="degree"
          type="category"
          label={{ 
            value: 'Degree', 
            position: 'insideBottom', 
            offset: -25,
            style: { textAnchor: 'middle' }
          }}
          stroke="#666"
          tickMargin={10}
          interval={Math.ceil(degreeDistribution.length / 30)}
          height={50}
          tickFormatter={(value) => value}
        />
        <YAxis 
          scale="linear"
          domain={[0, dataMax => Math.ceil(dataMax * 1.1)]}
          label={{ 
            value: 'Count', 
            angle: -90, 
            position: 'insideLeft',
            offset: -35
          }}
          allowDecimals={false}
          stroke="#666"
          tickMargin={8}
          tick={{ fontSize: 12 }}
          width={45}
        />
        <Tooltip 
          formatter={(value) => [`${value} nodes`, 'Count']}
          labelFormatter={(label) => `Degree: ${label}`}
          contentStyle={{ 
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.1)',
            border: 'none',
            borderRadius: '4px',
            padding: '12px'
          }}
          cursor={{ fill: 'rgba(0, 0, 0, 0.1)' }}
        />
        <Bar 
          dataKey="count"
          fill={theme.palette.primary.main} 
          minPointSize={3}
          barSize={12}
          isAnimationActive={false}
          name="Count"
        >
          {degreeDistribution.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getBarColor(entry.degree)} />
          ))}
        </Bar>
      </BarChart>
    );
  };

  return (
    <Card sx={{ p: 4, boxShadow: 3, borderRadius: 2 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" sx={{ 
          fontWeight: 600,
          color: theme.palette.primary.main 
        }}>
          Degree Distribution
        </Typography>
        
        <Stack direction="row" spacing={2} alignItems="center">
            <FormControlLabel
              control={
                <Switch 
                  checked={showLogScale}
                  onChange={handleToggleLogScale}
                  size="small"
                color="primary"
                />
              }
              label="Log Scale"
            sx={{ '& .MuiFormControlLabel-label': { fontSize: '0.85rem' } }}
            />
          
          <Button 
            size="small" 
            variant="outlined" 
            onClick={handleRefresh}
            startIcon={<RefreshIcon />}
            sx={{ fontSize: '0.7rem' }}
          >
            Recalculate
          </Button>
        </Stack>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Analysis of how connections are distributed across nodes in the network
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
          <Box>
            <Typography variant="body2" color="text.secondary">
              Min Degree:
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {basicStats.minDegree || 0}
            </Typography>
          </Box>
        </Box>
      </Box>
      
      <Box 
        ref={chartContainerRef}
        sx={{ 
          height: 420, 
          width: '100%', 
          bgcolor: 'rgba(245, 245, 249, 0.5)', 
          borderRadius: 2,
          p: 2,
          border: '1px solid rgba(0, 0, 0, 0.05)',
          position: 'relative'
        }}
      >
        {chartLoading && (
          <Box sx={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            right: 0, 
            bottom: 0, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            bgcolor: 'rgba(255,255,255,0.7)',
            zIndex: 10
          }}>
            <CircularProgress size={40} />
          </Box>
        )}
        <ResponsiveContainer width="100%" height="100%">
          {showLogScale ? renderScatterPlot() : renderBarChart()}
      </ResponsiveContainer>
      </Box>
      
      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          This chart shows the frequency distribution of node degrees in the network.
          A degree represents the number of connections a node has. Networks with
          power-law degree distributions (appearing as a straight line in log-log plots)
          often exhibit scale-free properties typical of many real-world networks.
        </Typography>
      </Box>
    </Card>
  );
};

export default DegreeHistogram; 