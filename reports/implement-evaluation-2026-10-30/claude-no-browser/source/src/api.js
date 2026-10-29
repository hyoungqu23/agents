export async function projects(status = 'all') {
  const response = await fetch(`/api/projects?status=${encodeURIComponent(status)}`);
  if (!response.ok) throw new Error('Could not load projects');
  return response.json();
}
