import React from 'react';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';

// Lightweight resource carousel with static curated items, filtered by stage if provided
const defaultResources = [
  { id: 1, title: 'Week 1: Healing & Rest', tag: '0-2w', color: 'rgba(255,183,135,0.18)' },
  { id: 2, title: 'Latching Basics (Video)', tag: 'lactation', color: 'rgba(183,148,244,0.18)' },
  { id: 3, title: 'Postpartum Mood: When to seek help', tag: 'mental', color: 'rgba(134,239,172,0.18)' },
  { id: 4, title: 'Nutritious snacks for night feeds', tag: 'nutrition', color: 'rgba(147,197,253,0.18)' },
  { id: 5, title: 'Cesarean recovery: gentle movement', tag: 'recovery', color: 'rgba(255,183,135,0.18)' },
];

const ResourceCarousel = ({ title = 'Recommended for you', items = defaultResources, stageWeeks }) => {
  const filtered = Array.isArray(items) ? items.filter(r => {
    if (stageWeeks == null) return true;
    if (stageWeeks <= 2) return ['0-2w','lactation','nutrition'].includes(r.tag) || r.tag === '0-2w';
    if (stageWeeks <= 6) return ['lactation','mental','nutrition','recovery'].includes(r.tag);
    return true;
  }) : [];

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
          <Typography variant="h6">{title}</Typography>
          {stageWeeks != null && (
            <Chip size="small" label={`~${stageWeeks} wks`} />
          )}
        </Box>
        <Box display="flex" gap={2} sx={{ overflowX: 'auto', pb: 1 }}>
          {filtered.map((r) => (
            <Box key={r.id} sx={{ minWidth: 220 }}>
              <Box sx={{ p: 2, borderRadius: 2, bgcolor: r.color }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>{r.title}</Typography>
                <Typography variant="caption" color="text.secondary">{r.tag}</Typography>
              </Box>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default ResourceCarousel;
