export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

export interface Comment {
  id: string;
  author: string;
  text: string;
  createdAt: string;
}

export interface Approval {
  id: string;
  title: string;
  description: string;
  requestedBy: string;
  status: ApprovalStatus;
  createdAt: string;
  updatedAt: string;
  comments: Comment[];
}

export interface CreateApprovalDto {
  title: string;
  description: string;
  requestedBy: string;
}

export interface UpdateStatusDto {
  status: ApprovalStatus;
  comment?: string;
  author?: string;
}
