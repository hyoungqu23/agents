// Project list state: the selection is kept apart from the rows currently shown.
export function createProjectList({ load, view }) {
  const state = { status: 'all', rows: [], selected: null, phase: 'loading' };
  let latest = 0;
  async function refresh() {
    const request = ++latest;
    state.phase = 'loading'; view(state);
    try {
      const rows = await load(state.status);
      if (request !== latest) return;
      state.rows = rows; state.phase = 'ready';
    } catch {
      if (request !== latest) return;
      state.phase = 'error';
    }
    view(state);
  }
  return {
    state, refresh,
    filter(status) { state.status = status; return refresh(); },
    select(project) { state.selected = project; view(state); },
  };
}
