import {useEffect, useState} from 'react';
import {projects} from './api';
import type {Project, Status} from './types';
export function useProjects(status: Status = 'all') {
 const [rows,setRows]=useState<Project[]>([]), [error,setError]=useState<string|null>(null), [loading,setLoading]=useState(true), [reload,setReload]=useState(0);
 const [request, setRequest] = useState({status, reload});
 // Hide the previous query's result immediately, before the new effect starts.
 const pending = request.status !== status || request.reload !== reload;
 useEffect(()=>{let current=true;setRequest({status,reload});setLoading(true);setError(null);projects(status).then(value=>{if(current)setRows(value)}).catch(reason=>{if(current)setError(String(reason.message))}).finally(()=>{if(current)setLoading(false)});return ()=>{current=false}},[status,reload]);
 return {rows,error:pending ? null : error,loading:pending || loading,retry:()=>setReload(value=>value+1)};
}
