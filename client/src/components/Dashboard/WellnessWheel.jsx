import React, { useMemo } from 'react';
import { Card, CardContent, Typography, Box, Tooltip } from '@mui/material';

// Simple CSS conic-gradient based wellness wheel
// data: [{ label: 'Nutrition', value: 0.7, color: '#FFB787' }, ...]
const WellnessWheel = ({
  title = "Wellness Balance",
  data = [
    { label: 'Nutrition', value: 0.7, color: '#FFB787' },
    { label: 'Mental', value: 0.8, color: '#86efac' },
    { label: 'Breastfeeding', value: 0.6, color: '#b794f4' },
    { label: 'Sleep', value: 0.5, color: '#93c5fd' },
  ],
}) => {
  // Build conic-gradient string from values
  const gradient = useMemo(() => {
    const total = data.reduce((a, b) => a + b.value, 0) || 1;
    let acc = 0;
    const stops = data.map((d) => {
      const start = (acc / total) * 100;
      acc += d.value;
      const end = (acc / total) * 100;
      return `${d.color} ${start.toFixed(2)}% ${end.toFixed(2)}%`;
    });
    return `conic-gradient(${stops.join(', ')})`;
  }, [data]);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Box display="flex" alignItems="center" gap={3}>
          <Box sx={{ position: 'relative', width: 180, height: 180 }}>
            <Box sx={{ width: '100%', height: '100%', borderRadius: '50%', background: gradient }} />
            <Box sx={{
              position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
              width: 120, height: 120, borderRadius: '50%', background: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 1
            }}>
              <Typography variant="subtitle2" color="text.secondary">Today</Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'auto 1fr', rowGap: 1.2, columnGap: 1.2 }}>
            {data.map((d) => (
              <React.Fragment key={d.label}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: d.color, mt: '6px' }} />
                <Tooltip title={`${Math.round(d.value * 100)}%`} placement="right">
                  <Typography variant="body2">{d.label}</Typography>
                </Tooltip>
              </React.Fragment>
            ))}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default WellnessWheel;
