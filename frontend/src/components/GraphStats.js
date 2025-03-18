import React from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Grid, 
  Box,
  Chip,
  LinearProgress,
  useTheme,
  Grow,
  Stack
} from '@mui/material';
import { 
  Timeline, 
  Hub, 
  Share, 
  AccountTree,
  TrendingUp,
  Lan
} from '@mui/icons-material';

const StatCard = ({ label, value, icon, color }) => (
  <Box
    sx={{
      p: 2,
      borderRadius: 2,
      bgcolor: 'rgba(255,255,255,0.5)',
      height: '100%',
      display: 'flex',
      alignItems: 'center',
      gap: 2
    }}
  >
    <Box sx={{ color: color }}>
      {icon}
    </Box>
    <Box>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h6" sx={{ fontWeight: 600, color }}>
        {typeof value === 'number' ? value.toFixed(3) : value || '0'}
      </Typography>
    </Box>
  </Box>
);

const NodeCard = ({ node, index }) => {
  const theme = useTheme();
  
  return (
    <Grow in={true} timeout={300 + (index * 100)}>
      <Card
        sx={{
          mb: 2,
          background: node.type === 'C' 
            ? `linear-gradient(135deg, ${theme.palette.primary.light}15, ${theme.palette.primary.main}15)`
            : `linear-gradient(135deg, ${theme.palette.secondary.light}15, ${theme.palette.secondary.main}15)`,
          transition: 'transform 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-4px)'
          }
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Node {node.id}
            </Typography>
            <Chip 
              label={node.type === 'C' ? 'Core' : 'Periphery'}
              size="small"
              icon={node.type === 'C' ? <Hub /> : <Share />}
              sx={{
                bgcolor: node.type === 'C' ? theme.palette.primary.main : theme.palette.secondary.main,
                color: 'white',
                fontWeight: 500,
                '& .MuiSvgIcon-root': {
                  color: 'white'
                }
              }}
            />
          </Box>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
              Coreness: {node.coreness.toFixed(3)}
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={node.coreness * 100}
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: 'rgba(0,0,0,0.1)',
                '& .MuiLinearProgress-bar': {
                  bgcolor: node.type === 'C' ? theme.palette.primary.main : theme.palette.secondary.main,
                  borderRadius: 4
                }
              }}
            />
          </Box>
        </CardContent>
      </Card>
    </Grow>
  );
};

const GraphStats = ({ graphData, metrics }) => {
  if (!metrics) return null;

  const theme = useTheme();

  return (
    <Card sx={{ p: 4, boxShadow: 3, borderRadius: 2 }}>
      <CardContent>
        <Stack spacing={3}>
          <Typography variant="h6" sx={{ 
            fontWeight: 600,
            color: theme.palette.primary.main 
          }}>
            Network Statistics
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Total Nodes" 
                value={metrics.node_count}
                icon={<Hub />}
                color={theme.palette.primary.main}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Total Edges" 
                value={metrics.edge_count}
                icon={<Timeline />}
                color={theme.palette.primary.main}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Density" 
                value={metrics.density?.toFixed(4)}
                icon={<Share />}
                color={theme.palette.primary.main}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Clustering" 
                value={metrics.clustering?.toFixed(4)}
                icon={<AccountTree />}
                color={theme.palette.primary.main}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Avg Path Length" 
                value={metrics.avg_path_length?.toFixed(4)}
                icon={<Timeline />}
                color={theme.palette.primary.main}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Diameter" 
                value={metrics.diameter}
                icon={<AccountTree />}
                color={theme.palette.primary.main}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StatCard 
                label="Assortativity" 
                value={metrics.assortativity?.toFixed(4)}
                icon={<Share />}
                color={theme.palette.primary.main}
              />
            </Grid>
          </Grid>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default GraphStats;