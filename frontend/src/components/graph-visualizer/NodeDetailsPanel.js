import React, { useMemo } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Chip, 
  Divider, 
  List, 
  ListItem, 
  ListItemText,
  useTheme
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import AccountTreeIcon from '@mui/icons-material/AccountTree';

const NodeDetailsPanel = ({ selectedNode, graphRef }) => {
  const theme = useTheme();
  
  // Calculate connected nodes
  const connectedNodes = useMemo(() => {
    if (!selectedNode || !graphRef) return [];
    
    const connections = [];
    graphRef.forEachNeighbor(selectedNode.id, (neighbor, attributes) => {
      connections.push({
        id: neighbor,
        label: graphRef.getNodeAttribute(neighbor, 'label') || neighbor,
        isCore: graphRef.getNodeAttribute(neighbor, 'isCore') || false
      });
    });
    
    return connections;
  }, [selectedNode, graphRef]);
  
  if (!selectedNode) return null;
  
  const isCore = selectedNode.isCore;
  
  return (
    <Paper
      elevation={3}
      sx={{
        p: 2,
        borderRadius: 2,
        mb: 2,
        border: `1px solid ${theme.palette.divider}`,
        maxHeight: '400px',
        overflow: 'auto'
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
        <InfoIcon sx={{ mr: 1, color: theme.palette.text.secondary }} />
        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
          Node Details
        </Typography>
      </Box>
      
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 0.5 }}>
          {selectedNode.label || selectedNode.id}
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Chip 
            label={isCore ? "Core" : "Periphery"} 
            size="small" 
            color={isCore ? "error" : "primary"}
            sx={{ mr: 1 }}
          />
          
          <Typography variant="body2" color="text.secondary">
            ID: {selectedNode.id}
          </Typography>
        </Box>
        
        {/* Display all attributes */}
        {Object.entries(selectedNode).filter(([key]) => 
          !['id', 'label', 'x', 'y', 'size', 'color', 'type', 'nodeType', 'isCore'].includes(key)
        ).map(([key, value]) => (
          <Box key={key} sx={{ mb: 0.5 }}>
            <Typography variant="caption" color="text.secondary" component="span">
              {key}:
            </Typography>{' '}
            <Typography variant="body2" component="span">
              {typeof value === 'number' ? value.toFixed(4) : String(value)}
            </Typography>
          </Box>
        ))}
      </Box>
      
      {/* Connected nodes section */}
      {connectedNodes.length > 0 && (
        <>
          <Divider sx={{ my: 1.5 }} />
          
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <AccountTreeIcon sx={{ mr: 1, color: theme.palette.text.secondary }} />
            <Typography variant="subtitle2">
              Connected Nodes ({connectedNodes.length})
            </Typography>
          </Box>
          
          <List dense disablePadding>
            {connectedNodes.slice(0, 10).map((node) => (
              <ListItem key={node.id} sx={{ py: 0.5 }}>
                <ListItemText 
                  primary={node.label || node.id}
                  secondary={`${node.isCore ? 'Core' : 'Periphery'} Node (ID: ${node.id})`}
                  primaryTypographyProps={{ variant: 'body2' }}
                  secondaryTypographyProps={{ variant: 'caption' }}
                />
              </ListItem>
            ))}
            
            {connectedNodes.length > 10 && (
              <ListItem sx={{ py: 0.5 }}>
                <ListItemText 
                  primary={`${connectedNodes.length - 10} more connections...`}
                  primaryTypographyProps={{ 
                    variant: 'body2', 
                    color: 'text.secondary',
                    fontStyle: 'italic'
                  }}
                />
              </ListItem>
            )}
          </List>
        </>
      )}
    </Paper>
  );
};

export default NodeDetailsPanel; 