import express from 'express';
import cors from 'cors';
import approvalsRouter from './routes';

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

app.use('/api/approvals', approvalsRouter);

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Approvals backend running on port ${PORT}`);
});
