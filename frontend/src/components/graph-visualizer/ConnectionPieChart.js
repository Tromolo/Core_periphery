import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';

const ConnectionPieChart = ({ metrics, graphData }) => {
  const theme = useTheme();
  const edgeStats = useMemo(() => {
    // If we have backend-calculated connection patterns, use them
    if (metrics?.core_periphery_analysis?.connection_patterns) {
      const patterns = metrics.core_periphery_analysis.connection_patterns;
      return [
        { 
          name: 'C-C', 
          value: patterns.core_core.count, 
          percentage: patterns.core_core.percentage.toFixed(2) + '%',
          color: '#d32f2f',
          fullName: 'Core-Core'
        },
        { 
          name: 'C-P', 
          value: patterns.core_periphery.count, 
          percentage: patterns.core_periphery.percentage.toFixed(2) + '%',
          color: '#9c27b0',
          fullName: 'Core-Periphery'
        },
        { 
          name: 'P-P', 
          value: patterns.periphery_periphery.count, 
          percentage: patterns.periphery_periphery.percentage.toFixed(2) + '%',
          color: '#1976d2',
          fullName: 'Periphery-Periphery'
        }
      ];
    }
    
    // Fallback to calculating from graphData
    if (!graphData?.nodes || !graphData?.edges) return null;
    
    // Handle both formats: original graph data (type: 'C'/'P') and processed graph data (isCore: true/false)
    const coreNodeIds = new Set();
    graphData.nodes.forEach(node => {
      if ((node.type === 'C') || (node.isCore === true)) {
        coreNodeIds.add(node.id);
      }
    });
    
    let coreCore = 0;
    let corePeriphery = 0;
    let peripheryPeriphery = 0;
    
    graphData.edges.forEach(edge => {
      const sourceIsCore = coreNodeIds.has(edge.source);
      const targetIsCore = coreNodeIds.has(edge.target);
      
      if (sourceIsCore && targetIsCore) {
        coreCore++;
      } else if ((!sourceIsCore && targetIsCore) || (sourceIsCore && !targetIsCore)) {
        corePeriphery++;
      } else {
        peripheryPeriphery++;
      }
    });
    
    const total = graphData.edges.length;
    
    return [
      { 
        name: 'C-C', 
        value: coreCore, 
        percentage: ((coreCore / total) * 100).toFixed(1) + '%',
        color: '#d32f2f',
        fullName: 'Core-Core'
      },
      { 
        name: 'C-P', 
        value: corePeriphery, 
        percentage: ((corePeriphery / total) * 100).toFixed(1) + '%',
        color: '#9c27b0',
        fullName: 'Core-Periphery'
      },
      { 
        name: 'P-P', 
        value: peripheryPeriphery, 
        percentage: ((peripheryPeriphery / total) * 100).toFixed(1) + '%',
        color: '#1976d2',
        fullName: 'Periphery-Periphery'
      }
    ];
  }, [metrics, graphData]);
  
  if (!edgeStats) return <Typography>No data available</Typography>;
  
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={edgeStats}
          cx="50%"
          cy="50%"
          labelLine={{
            stroke: '#999',
            strokeWidth: 1,
            strokeDasharray: '2,2',
          }}
          label={({
            cx, cy, midAngle, innerRadius, outerRadius, percent, index, name, percentage
          }) => {
            const RADIAN = Math.PI / 180;
            // Increase distance from pie for label placement
            const radius = outerRadius * 1.2;
            const x = cx + radius * Math.cos(-midAngle * RADIAN);
            const y = cy + radius * Math.sin(-midAngle * RADIAN);
            
            return (
              <text
                x={x}
                y={y}
                fill={edgeStats[index].color}
                textAnchor={x > cx ? 'start' : 'end'}
                dominantBaseline="central"
                fontWeight="bold"
              >
                {`${name}: ${percentage}`}
              </text>
            );
          }}
          outerRadius={120}
          dataKey="value"
        >
          {edgeStats.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip 
          formatter={(value, name, props) => [
            `${value} (${props.payload.percentage})`,
            props.payload.fullName || name
          ]}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default ConnectionPieChart; 