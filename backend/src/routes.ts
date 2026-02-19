import { Router, Request, Response } from 'express';
import * as store from './store';
import { CreateApprovalDto, UpdateStatusDto } from './types';

const router = Router();

// GET /api/approvals
router.get('/', (_req: Request, res: Response) => {
  res.json(store.getAll());
});

// GET /api/approvals/:id
router.get('/:id', (req: Request, res: Response) => {
  const approval = store.getById(req.params.id);
  if (!approval) {
    res.status(404).json({ error: 'Not found' });
    return;
  }
  res.json(approval);
});

// POST /api/approvals
router.post('/', (req: Request, res: Response) => {
  const { title, description, requestedBy } = req.body as CreateApprovalDto;
  if (!title || !description || !requestedBy) {
    res.status(400).json({ error: 'title, description, and requestedBy are required' });
    return;
  }
  const approval = store.create({ title, description, requestedBy });
  res.status(201).json(approval);
});

// PATCH /api/approvals/:id/status
router.patch('/:id/status', (req: Request, res: Response) => {
  const { status, comment, author } = req.body as UpdateStatusDto;
  if (!status || !['pending', 'approved', 'rejected'].includes(status)) {
    res.status(400).json({ error: 'Valid status required: pending, approved, rejected' });
    return;
  }
  const updated = store.updateStatus(req.params.id, status, comment, author);
  if (!updated) {
    res.status(404).json({ error: 'Not found' });
    return;
  }
  res.json(updated);
});

// DELETE /api/approvals/:id
router.delete('/:id', (req: Request, res: Response) => {
  const deleted = store.remove(req.params.id);
  if (!deleted) {
    res.status(404).json({ error: 'Not found' });
    return;
  }
  res.status(204).send();
});

export default router;
