export function createProjectList({ loadProjects, onChange }) {
  let state = { status: 'all', projects: [], selected: null, loading: false, error: null };
  let request = 0;

  function update(changes) {
    state = { ...state, ...changes };
    onChange(state);
  }

  return {
    getState: () => state,
    select(project) {
      update({ selected: project });
    },
    async load(status = state.status) {
      const current = ++request;
      update({ status, projects: [], loading: true, error: null });
      try {
        const projects = await loadProjects(status);
        if (current !== request) return;
        update({ projects, loading: false, error: null });
      } catch (error) {
        if (current !== request) return;
        update({ projects: [], loading: false, error });
      }
    },
  };
}
