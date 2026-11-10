import {useState} from 'react';
import {useProjects} from './useProjects';
import {ProblemPanel, ProjectRows, SelectedPanel, StatusField} from './ui';
import type {Project, Status} from './types';

export default function App() {
 const [status, setStatus] = useState<Status>('all');
 const [selected, setSelected] = useState<Project | null>(null);
 const {rows, loading, error, retry} = useProjects(status);

 return <>
  <header><h1>Projects</h1><p>Browse projects and keep one selected while filtering.</p></header>
  <main className="layout">
   <section className="panel" aria-label="Project list" aria-busy={loading}>
    <div className="filter">
     <StatusField value={status} onChange={setStatus}/>
     {!loading && !error && <span aria-live="polite">{rows.length} {rows.length === 1 ? 'project' : 'projects'}</span>}
    </div>
    {loading ? <p role="status">Loading projects…</p> : error ? <ProblemPanel message={error} retry={retry}/> : rows.length === 0 ? <p role="status">No projects found</p> : <ProjectRows rows={rows} selectedId={selected?.id ?? null} onSelect={setSelected}/>}
   </section>
   <SelectedPanel project={selected}/>
  </main>
 </>;
}
