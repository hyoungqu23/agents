export type Status = 'all' | 'active' | 'archived' | 'paused';
export type Project = {id: string; name: string; status: Exclude<Status, 'all'>};
