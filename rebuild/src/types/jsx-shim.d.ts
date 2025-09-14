// Temporary minimal JSX intrinsic elements shim until @types/react installed
declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}
