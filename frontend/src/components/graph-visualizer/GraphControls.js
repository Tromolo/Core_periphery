import React, { useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Slider, 
  FormControlLabel, 
  Switch, 
  Button, 
  Typography, 
  Tooltip, 
  Divider 
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import CenterFocusStrongIcon from '@mui/icons-material/CenterFocusStrong';
import LabelIcon from '@mui/icons-material/Label';
import LabelOffIcon from '@mui/icons-material/LabelOff';

const GraphControls = ({
  toggleForceAtlas2,
  centerView,
  isForceAtlas2Running,
  nodeSize,
  handleNodeSizeChange,
  showLabels,
  handleToggleLabels,
  rendererReady
}) => {
  useEffect(() => {
    console.log("GraphControls rendererReady:", rendererReady);
  }, [rendererReady]);

  const safeToggleForceAtlas2 = () => {
    console.log("Attempting to toggle ForceAtlas2, rendererReady:", rendererReady);
    toggleForceAtlas2();
  };
  
  const safeCenterView = () => {
    console.log("Attempting to center view, rendererReady:", rendererReady);
    centerView();
  };
  
  const safeToggleLabels = () => {
    console.log("Attempting to toggle labels, rendererReady:", rendererReady);
    handleToggleLabels();
  };
  
  const safeHandleNodeSizeChange = (event, newValue) => {
    console.log("Attempting to change node size, rendererReady:", rendererReady);
    handleNodeSizeChange(event, newValue);
  };
  
  const forceEnabled = true;
  
  return (
    <Paper
      elevation={1}
      sx={{
        p: 1.5,
        mb: 2,
        borderRadius: 1,
      }}
    >
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
        <Box sx={{ minWidth: '240px' }}>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
            Layout Controls:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title={isForceAtlas2Running ? "Stop Force Layout" : "Start Force Layout"}>
              <Button
                variant={isForceAtlas2Running ? "contained" : "outlined"}
                color={isForceAtlas2Running ? "secondary" : "primary"}
                size="small"
                startIcon={isForceAtlas2Running ? <StopIcon /> : <PlayArrowIcon />}
                onClick={safeToggleForceAtlas2}
                disabled={false}
              >
                {isForceAtlas2Running ? "Stop Layout" : "Start Layout"}
              </Button>
            </Tooltip>
            
            <Tooltip title="Center View">
              <Button
                variant="outlined"
                color="primary"
                size="small"
                startIcon={<CenterFocusStrongIcon />}
                onClick={safeCenterView}
                disabled={false}
              >
                Center
              </Button>
            </Tooltip>
          </Box>
        </Box>
        
        <Divider orientation="vertical" flexItem />
        
        <Box sx={{ minWidth: '180px', maxWidth: '300px', flex: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
            Node Size:
          </Typography>
          <Slider
            value={nodeSize}
            min={1}
            max={10}
            step={0.5}
            onChange={safeHandleNodeSizeChange}
            valueLabelDisplay="auto"
            disabled={false}
            sx={{ 
              mt: 1,
              '& .MuiSlider-thumb': {
                transition: 'transform 0.2s',
              }
            }}
          />
        </Box>
        
        <Divider orientation="vertical" flexItem />
        
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
            Labels:
          </Typography>
          <Tooltip title={showLabels ? "Hide Labels" : "Show Labels"}>
            <Button
              variant={showLabels ? "contained" : "outlined"}
              color="primary"
              size="small"
              startIcon={showLabels ? <LabelIcon /> : <LabelOffIcon />}
              onClick={safeToggleLabels}
              disabled={false}
            >
              {showLabels ? "Hide Labels" : "Show Labels"}
            </Button>
          </Tooltip>
        </Box>
      </Box>
    </Paper>
  );
};

export default GraphControls; 