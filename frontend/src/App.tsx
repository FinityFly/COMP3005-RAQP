import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CssBaseline,
  ThemeProvider,
  createTheme
} from '@mui/material';


const theme = createTheme({
  palette: {
    mode: 'light',
    background: {
      default: '#fff',
      paper: '#fff',
    },
    text: {
      primary: '#111',
    },
    primary: {
      main: '#111',
      contrastText: '#fff',
    },
  },
  typography: {
    fontFamily: 'Inter, Helvetica, Arial, sans-serif',
    fontWeightLight: 400,
    fontWeightRegular: 500,
    fontWeightMedium: 600,
    fontWeightBold: 700,
    h1: { fontWeight: 700 },
    h2: { fontWeight: 600 },
    h3: { fontWeight: 500 },
    h4: { fontWeight: 500 },
    h5: { fontWeight: 500 },
    h6: { fontWeight: 500 },
    subtitle1: { fontWeight: 500 },
    subtitle2: { fontWeight: 400 },
    body1: { fontWeight: 400 },
    body2: { fontWeight: 400 },
  },
});


const defaultTable = {
  columns: [],
  rows: []
};

function App() {
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');
  const [tableData, setTableData] = useState(defaultTable);
  const pageWidth = '40vw';

  const handleSubmit = async () => {
    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: input }),
      });
      const data = await response.json();
      setOutput(data.text || '');
      setTableData(data.table && data.table.columns && data.table.rows ? data.table : { columns: [], rows: [] });
    } catch (err) {
      setOutput('Error fetching data');
      setTableData({ columns: [], rows: [] });
    }
  };

    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            bgcolor: 'background.default',
            color: 'text.primary',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            fontFamily: 'Inter, Helvetica, Arial, sans-serif',
          }}
        >
          <Typography variant="h4" sx={{ mt: 20, mb: 4, fontWeight: 700, letterSpacing: 1 }}>
            Relational Algebra Query Processor
          </Typography>
          <Box
            sx={{
              width: '100vw',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 3,
            }}
          >
            <TextField
              label="Enter your query"
              variant="outlined"
              multiline
              minRows={10}
              maxRows={20}
              value={input}
              onChange={e => setInput(e.target.value)}
              sx={{
                mb: 2,
                bgcolor: '#fff',
                width: pageWidth,
                minWidth: 400,
                maxWidth: '50vw',
                height: '38vh',
                minHeight: 300,
                maxHeight: '40vh',
                '& .MuiOutlinedInput-root': {
                  color: '#111',
                  fontSize: '1.1rem',
                  fontFamily: 'inherit',
                  borderRadius: 4,
                  height: '100%',
                  alignItems: 'flex-start',
                },
              }}
              InputLabelProps={{ style: { color: '#111', fontWeight: 500 } }}
            />
            <Button
              variant="contained"
              color="primary"
              size="large"
              sx={{
                fontWeight: 600,
                fontSize: '1.1rem',
                borderRadius: 4,
                boxShadow: 1,
                py: 1.5,
                width: pageWidth,
                minWidth: 350,
                maxWidth: '50vw',
              }}
              onClick={handleSubmit}
            >
              Submit
            </Button>
            <Box sx={{ mt: 2, width: pageWidth, minWidth: 400, maxWidth: '50vw', alignItems: 'center', display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ width: '100%', height: '1px', bgcolor: '#ccc', mb: 2 }} />
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                Output:
              </Typography>
              <Paper
                sx={{
                  p: 3,
                  minHeight: '30vh',
                  maxHeight: '40vh',
                  bgcolor: '#fff',
                  color: '#111',
                  fontSize: '1.1rem',
                  fontFamily: 'inherit',
                  borderRadius: 4,
                  boxShadow: 2,
                  wordBreak: 'break-word',
                  overflowY: 'auto',
                  width: '100%',
                }}
                elevation={1}
              >
                {output}
              </Paper>
            </Box>
            <TableContainer component={Paper} sx={{ mt: 4, mb: 10, bgcolor: '#fff', boxShadow: 1, borderRadius: 2, width: pageWidth, minWidth: 400, maxWidth: '50vw', overflow: 'visible', maxHeight: 'none' }}>
              <Table>
                <TableHead>
                  <TableRow>
                    {tableData.columns && tableData.columns.map((col) => (
                      <TableCell key={col} sx={{ fontWeight: 600, color: '#111', fontSize: '1rem' }}>{col}</TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Array.isArray(tableData.rows) && tableData.rows.map((row: any[], idx: number) => (
                    <TableRow key={idx}>
                      {row.map((value: any, i: number) => (
                        <TableCell key={i} sx={{ color: '#111', fontSize: '1rem' }}>{value}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
          <Typography variant="h6" sx={{ mb: 4, fontWeight: 500, color: '#555', textAlign: 'center', width: pageWidth, minWidth: 400, maxWidth: '50vw' }}>
            COMP3005 | Daniel Lu
          </Typography>
        </Box>
      </ThemeProvider>
    );
}

export default App;