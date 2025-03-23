import React from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Tooltip, 
  Snackbar,
  Alert
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import ImageIcon from '@mui/icons-material/Image';
import TableViewIcon from '@mui/icons-material/TableView';
import ShareIcon from '@mui/icons-material/Share';

const GraphHeader = ({ 
  nodeCsvFile, 
  edgeCsvFile, 
  gdfFile, 
  handleDownloadNodeCSV, 
  handleDownloadEdgeCSV, 
  handleDownloadGDF, 
  handleDownloadImage, 
  downloadSuccess 
}) => {
  return (
    <Box sx={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center', 
      mb: 2, 
      flexWrap: 'wrap'
    }}>
      {/* Left side - Title */}
      <Typography variant="h5" component="h2" sx={{ mr: 2, fontWeight: 'bold' }}>
        Graph Visualization
      </Typography>
      
      {/* Right side - Download buttons */}
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        {nodeCsvFile && (
          <Tooltip title="Download Node Data (CSV)">
            <Button
              variant="outlined"
              color="primary"
              size="small"
              startIcon={<TableViewIcon />}
              onClick={handleDownloadNodeCSV}
            >
              Nodes
            </Button>
          </Tooltip>
        )}
        
        {edgeCsvFile && (
          <Tooltip title="Download Edge Data (CSV)">
            <Button
              variant="outlined"
              color="primary"
              size="small"
              startIcon={<TableViewIcon />}
              onClick={handleDownloadEdgeCSV}
            >
              Edges
            </Button>
          </Tooltip>
        )}
        
        {gdfFile && (
          <Tooltip title="Download Graph Data (GDF)">
            <Button
              variant="outlined"
              color="primary"
              size="small"
              startIcon={<ShareIcon />}
              onClick={handleDownloadGDF}
            >
              GDF
            </Button>
          </Tooltip>
        )}
        
        <Tooltip title="Download Graph Image">
          <Button
            variant="contained"
            color="primary"
            size="small"
            startIcon={<ImageIcon />}
            onClick={handleDownloadImage}
          >
            Image
          </Button>
        </Tooltip>
      </Box>
      
      {/* Success notification */}
      <Snackbar 
        open={downloadSuccess} 
        autoHideDuration={2000} 
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="success" sx={{ width: '100%' }}>
          Image downloaded successfully!
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default GraphHeader; 