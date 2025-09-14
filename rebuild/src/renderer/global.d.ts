export {};

declare global {
  interface Window {
    api: {
      openSheetListener(cb: (data: { path: string }) => void): void;
    };
  }
}
