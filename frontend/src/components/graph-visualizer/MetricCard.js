import React from 'react';
import { Paper, Typography, Box, Tooltip } from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

const MetricCard = ({ title, value, description, unit = '', valueColor, icon: Icon }) => {
  return (
    <Paper 
      elevation={1} 
      sx={{ 
        p: 1.5, 
        height: '100%', 
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        borderRadius: 1,
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          boxShadow: 3
        }
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle2" color="text.secondary" sx={{ mr: 0.5 }}>
          {title}
        </Typography>
        
        {description && (
          <Tooltip title={description} arrow placement="top">
            <InfoOutlinedIcon fontSize="small" color="action" sx={{ opacity: 0.6 }} />
          </Tooltip>
        )}
      </Box>
      
      <Box sx={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'baseline' }}>
          <Typography 
            variant="h5" 
            component="div" 
            sx={{ 
              fontWeight: 'bold',
              color: valueColor || 'text.primary'
            }}
          >
            {value}
          </Typography>
          
          {unit && (
            <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
              {unit}
            </Typography>
          )}
        </Box>
        
        {Icon && (
          <Icon color="action" sx={{ fontSize: 24, opacity: 0.7 }} />
        )}
      </Box>
    </Paper>
  );
};

export default MetricCard; 