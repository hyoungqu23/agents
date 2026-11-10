import type {Project, Status} from './types';
export async function projects(status: Status = 'all', base = ''): Promise<Project[]> {
 const response = await fetch(`${base}/api/projects?status=${encodeURIComponent(status)}`);
 if (!response.ok) throw new Error('Could not load projects');
 return response.json();
}
