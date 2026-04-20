import React, { useMemo, useState, useEffect } from 'react';
import { Card, CardContent, Typography, Box, IconButton, Chip, Stack } from '@mui/material';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import FavoriteIcon from '@mui/icons-material/Favorite';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

const defaultAffirmations = [
  'You are doing an amazing job. One day at a time.',
  'Rest is productive. Your healing matters.',
  'You and your baby are learning together.',
  'It’s okay to ask for help. You deserve support.',
  'Small steps, big progress. Celebrate little wins.'
];

const AffirmationsDeck = ({ title = 'Daily Affirmations', items = defaultAffirmations }) => {
  const [index, setIndex] = useState(0);
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    const saved = localStorage.getItem('affirmation_favorites');
    if (saved) setFavorites(JSON.parse(saved));
  }, []);

  useEffect(() => {
    localStorage.setItem('affirmation_favorites', JSON.stringify(favorites));
  }, [favorites]);

  const isFav = useMemo(() => favorites.includes(items[index]), [favorites, items, index]);

  const toggleFav = () => {
    const current = items[index];
    setFavorites((prev) => prev.includes(current) ? prev.filter(x => x !== current) : [...prev, current]);
  };

  const prev = () => setIndex((i) => (i - 1 + items.length) % items.length);
  const next = () => setIndex((i) => (i + 1) % items.length);

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
          <Typography variant="h6">{title}</Typography>
          <Stack direction="row" spacing={1}>
            <Chip label={`${index + 1}/${items.length}`} size="small" />
            <IconButton onClick={toggleFav} color={isFav ? 'error' : 'default'} aria-label="favorite">
              {isFav ? <FavoriteIcon /> : <FavoriteBorderIcon />}
            </IconButton>
          </Stack>
        </Box>
        <Box display="flex" alignItems="center" justifyContent="space-between" gap={1}>
          <IconButton onClick={prev} aria-label="previous">
            <ChevronLeftIcon />
          </IconButton>
          <Box flex={1} sx={{ p: 3, textAlign: 'center', borderRadius: 2, bgcolor: 'rgba(183,148,244,0.08)' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              {items[index]}
            </Typography>
          </Box>
          <IconButton onClick={next} aria-label="next">
            <ChevronRightIcon />
          </IconButton>
        </Box>
      </CardContent>
    </Card>
  );
};

export default AffirmationsDeck;
