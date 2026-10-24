/** Resolve bundled assets under both Capacitor's root and GitHub Pages subpaths. */
export const asset = (path: string) =>
  `${import.meta.env.BASE_URL}${path.replace(/^\//, "")}`;
