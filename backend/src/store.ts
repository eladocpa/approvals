import { Approval } from './types';
import { v4 as uuidv4 } from 'uuid';

const now = new Date().toISOString();

const approvals: Approval[] = [
  {
    id: uuidv4(),
    title: 'Budget increase for Q1 marketing',
    description: 'Request to increase marketing budget by $5,000 for Q1 campaigns.',
    requestedBy: 'Alice Cohen',
    status: 'pending',
    createdAt: now,
    updatedAt: now,
    comments: [],
  },
  {
    id: uuidv4(),
    title: 'New vendor contract - Cloud hosting',
    description: 'Approve new 2-year contract with cloud hosting provider.',
    requestedBy: 'Bob Levi',
    status: 'approved',
    createdAt: now,
    updatedAt: now,
    comments: [
      {
        id: uuidv4(),
        author: 'Manager',
        text: 'Approved after reviewing terms.',
        createdAt: now,
      },
    ],
  },
  {
    id: uuidv4(),
    title: 'Remote work policy update',
    description: 'Update remote work policy to allow 3 days per week.',
    requestedBy: 'Dana Shapiro',
    status: 'rejected',
    createdAt: now,
    updatedAt: now,
    comments: [
      {
        id: uuidv4(),
        author: 'HR',
        text: 'Needs further review by legal.',
        createdAt: now,
      },
    ],
  },
];

export function getAll(): Approval[] {
  return approvals;
}

export function getById(id: string): Approval | undefined {
  return approvals.find((a) => a.id === id);
}

export function create(data: { title: string; description: string; requestedBy: string }): Approval {
  const approval: Approval = {
    id: uuidv4(),
    title: data.title,
    description: data.description,
    requestedBy: data.requestedBy,
    status: 'pending',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    comments: [],
  };
  approvals.unshift(approval);
  return approval;
}

export function updateStatus(
  id: string,
  status: 'pending' | 'approved' | 'rejected',
  comment?: string,
  author?: string
): Approval | undefined {
  const approval = approvals.find((a) => a.id === id);
  if (!approval) return undefined;
  approval.status = status;
  approval.updatedAt = new Date().toISOString();
  if (comment) {
    approval.comments.push({
      id: uuidv4(),
      author: author || 'System',
      text: comment,
      createdAt: new Date().toISOString(),
    });
  }
  return approval;
}

export function remove(id: string): boolean {
  const idx = approvals.findIndex((a) => a.id === id);
  if (idx === -1) return false;
  approvals.splice(idx, 1);
  return true;
}
