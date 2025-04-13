import React from 'react';
import { Grid, Typography, Divider, Box } from '@mui/material';
import { 
  AccountTree, 
  DeviceHub,
  PieChart as PieChartIcon,
  CompareArrows,
  Insights,
  BlurOn,
} from '@mui/icons-material';
import MetricCard from './MetricCard';

const CorePeripheryMetrics = ({ graphData, metrics }) => {
  return (
    <Grid container spacing={2} sx={{ mt: 2 }}>
      <Grid item xs={12}>
        <Typography variant="h6" sx={{ mb: 1 }}>Core-Periphery Structure</Typography>
        <Divider sx={{ mb: 2 }} />
      </Grid>
      <Grid item xs={12} sm={6} md={4}>
        <MetricCard 
          title="Core Nodes" 
          value={getCoreCount(metrics, graphData)}
          icon={AccountTree}
          description="Number of nodes identified as part of the core"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4}>
        <MetricCard 
          title="Periphery Nodes" 
          value={getPeripheryCount(metrics, graphData)}
          icon={DeviceHub}
          description="Number of nodes identified as part of the periphery"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4}>
        <MetricCard 
          title="Core Percentage" 
          value={getCorePercentage(metrics, graphData)}
          icon={PieChartIcon}
          description="Percentage of nodes that are in the core"
        />
      </Grid>
      
      <Grid item xs={12} sm={6} md={4}>
        <MetricCard 
          title="Core Density" 
          value={getCoreDensity(metrics, graphData)}
          icon={BlurOn}
          description="How densely connected the core nodes are to each other"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4}>
        <MetricCard 
          title="Core-Periphery Connectivity" 
          value={getCorePeriConnectivity(metrics, graphData)}
          icon={CompareArrows}
          description="Average number of connections from periphery nodes to core nodes"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4}>
        <MetricCard 
          title="Periphery Isolation" 
          value={getPeripheryIsolation(metrics, graphData)}
          icon={Insights}
          description="Percentage of connections between periphery nodes"
        />
      </Grid>
    </Grid>
  );
};

const getCoreCount = (metrics, graphData) => {
  if (metrics?.core_stats?.core_size !== undefined) {
    return metrics.core_stats.core_size;
  }
  
  if (graphData?.nodes) {
    return graphData.nodes.filter(node => 
      node.type === 'C' || node.isCore === true
    ).length;
  }
  
  return 0;
};

const getPeripheryCount = (metrics, graphData) => {
  if (metrics?.core_stats?.periphery_size !== undefined) {
    return metrics.core_stats.periphery_size;
  }
  
  if (graphData?.nodes) {
    return graphData.nodes.filter(node => 
      node.type === 'P' || (node.isCore !== undefined && !node.isCore)
    ).length;
  }
  
  return 0;
};

const getCorePercentage = (metrics, graphData) => {
  if (metrics?.core_stats?.core_percentage !== undefined) {
    return `${metrics.core_stats.core_percentage.toFixed(1)}%`;
  }
  
  if (graphData?.nodes) {
    const totalNodes = graphData.nodes.length;
    const coreNodes = getCoreCount(metrics, graphData);
    
    if (totalNodes > 0) {
      const percentage = (coreNodes / totalNodes) * 100;
      return `${percentage.toFixed(1)}%`;
    }
  }
  
  return '0.0%';
};

const getCoreDensity = (metrics, graphData) => {
  if (metrics?.core_periphery_metrics?.core_density !== undefined) {
    const density = metrics.core_periphery_metrics.core_density;
    if (density > 0 && density < 0.01) {
      return density.toFixed(4);
    }
    return density.toFixed(2);
  }
  
  if (graphData?.nodes && graphData?.edges) {
    const coreNodes = graphData.nodes.filter(node => 
      node.type === 'C' || node.isCore === true
    );
    if (coreNodes.length <= 1) return '0';
    
    const coreNodeIds = new Set(coreNodes.map(node => node.id));
    let coreEdges = 0;
    let possibleCoreEdges = (coreNodes.length * (coreNodes.length - 1)) / 2;
    
    graphData.edges.forEach(edge => {
      if (coreNodeIds.has(edge.source) && coreNodeIds.has(edge.target)) {
        coreEdges++;
      }
    });
    
    const calculatedDensity = coreEdges / possibleCoreEdges;
    if (calculatedDensity > 0 && calculatedDensity < 0.01) {
      return calculatedDensity.toFixed(4);
    }
    return calculatedDensity.toFixed(2);
  }
  
  return '0';
};

const getCorePeriConnectivity = (metrics, graphData) => {
  if (metrics?.core_periphery_metrics?.periphery_core_connectivity !== undefined) {
    return metrics.core_periphery_metrics.periphery_core_connectivity.toFixed(2);
  }
  
  if (graphData?.nodes && graphData?.edges) {
    const peripheryNodes = graphData.nodes.filter(node => 
      node.type === 'P' || (node.isCore !== undefined && !node.isCore)
    );
    if (peripheryNodes.length === 0) return '0.00';
    
    const peripheryNodeIds = new Set(peripheryNodes.map(node => node.id));
    const coreNodeIds = new Set(graphData.nodes.filter(node => 
      node.type === 'C' || node.isCore === true
    ).map(node => node.id));
    let corePeriEdges = 0;
    
    graphData.edges.forEach(edge => {
      if ((coreNodeIds.has(edge.source) && peripheryNodeIds.has(edge.target)) ||
          (coreNodeIds.has(edge.target) && peripheryNodeIds.has(edge.source))) {
        corePeriEdges++;
      }
    });
    
    return (corePeriEdges / peripheryNodes.length).toFixed(2);
  }
  
  return '0.00';
};

const getPeripheryIsolation = (metrics, graphData) => {
  if (metrics?.core_periphery_metrics?.periphery_isolation !== undefined) {
    return metrics.core_periphery_metrics.periphery_isolation.toFixed(2) + '%';
  }
  
  if (graphData?.nodes && graphData?.edges) {
    const peripheryNodes = graphData.nodes.filter(node => 
      node.type === 'P' || (node.isCore !== undefined && !node.isCore)
    );
    if (peripheryNodes.length <= 1) return '0.00%';
    
    const peripheryNodeIds = new Set(peripheryNodes.map(node => node.id));
    let peripheryPeripheryEdges = 0;
    let totalEdges = graphData.edges.length;
    
    graphData.edges.forEach(edge => {
      if (peripheryNodeIds.has(edge.source) && peripheryNodeIds.has(edge.target)) {
        peripheryPeripheryEdges++;
      }
    });
    
    if (totalEdges === 0) return '0.00%';
    const peripheryIsolation = (peripheryPeripheryEdges / totalEdges) * 100;
    return peripheryIsolation.toFixed(2) + '%';
  }
  
  return '0.00%';
};

export default CorePeripheryMetrics; 