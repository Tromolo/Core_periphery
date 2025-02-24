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
  const theme = useTheme();

  if (!metrics) return null;

  return (
    <Box>
      <Typography 
        variant="h4" 
        sx={{ 
          mb: 4,
          textAlign: 'center',
          background: 'linear-gradient(45deg, #1a237e, #0d47a1)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          color: 'transparent',
          fontWeight: 'bold'
        }}
      >
        Network Statistics
      </Typography>

      <Grid container spacing={4}>
        <Grid item xs={12} lg={6}>
          <Grow in={true} timeout={500}>
            <Card sx={{ 
              height: '100%',
              background: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7))',
              backdropFilter: 'blur(10px)',
            }}>
              <CardContent>
                <Stack spacing={3}>
                  <Typography variant="h6" sx={{ 
                    fontWeight: 600,
                    color: theme.palette.primary.main 
                  }}>
                    Network Metrics
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Density" 
                        value={metrics.density}
                        icon={<Share />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Clustering" 
                        value={metrics.clustering}
                        icon={<AccountTree />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Modularity" 
                        value={metrics.modularity}
                        icon={<Hub />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Avg Path Length" 
                        value={metrics.avg_path_length}
                        icon={<Timeline />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Top Node Degree" 
                        value={metrics.top_nodes[0]?.degree || 'N/A'}
                        icon={<AccountTree />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Average Degree" 
                        value={metrics.avg_degree || 'N/A'}
                        icon={<Share />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Diameter" 
                        value={metrics.diameter || 'N/A'}
                        icon={<Timeline />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Assortativity" 
                        value={metrics.assortativity || 'N/A'}
                        icon={<Share />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Core Density" 
                        value={metrics.core_stats?.core_density || 'N/A'}
                        icon={<AccountTree />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Periphery Connectivity" 
                        value={metrics.periphery_core_connectivity || 'N/A'}
                        icon={<Share />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Betweenness Centrality" 
                        value={metrics.betweenness_centrality || 'N/A'}
                        icon={<Hub />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Edge Density" 
                        value={metrics.edge_density || 'N/A'}
                        icon={<Share />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Eigenvector Centrality" 
                        value={metrics.eigenvector_centrality || 'N/A'}
                        icon={<TrendingUp />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <StatCard 
                        label="Graph Connectivity" 
                        value={metrics.graph_connectivity || 'N/A'}
                        icon={<Lan />}
                        color={theme.palette.primary.main}
                      />
                    </Grid>
                  </Grid>
                </Stack>
              </CardContent>
            </Card>
          </Grow>
        </Grid>

        <Grid item xs={12} lg={6}>
          <Grow in={true} timeout={700}>
            <Card sx={{
              background: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7))',
              backdropFilter: 'blur(10px)',
            }}>
              <CardContent>
                <Typography variant="h6" sx={{ 
                  mb: 3, 
                  fontWeight: 600,
                  color: theme.palette.primary.main 
                }}>
                  Top Nodes by Coreness
                </Typography>
                {metrics.top_nodes.map((node, index) => (
                  <NodeCard key={index} node={node} index={index} />
                ))}
              </CardContent>
            </Card>
          </Grow>
        </Grid>
      </Grid>
    </Box>
  );
};

export default GraphStats;