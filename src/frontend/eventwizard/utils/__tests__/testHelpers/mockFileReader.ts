/**
 * Mock FileReader for Node.js test environment.
 * Simulates browser FileReader API for reading files in tests.
 */
export class MockFileReader {
  result?: string;
  onload?: ((event: { target: MockFileReader }) => void) | null;

  async readAsBinaryString(blob: Blob | Buffer): Promise<void> {
    // Convert blob to buffer, then to binary string
    const reader = this;
    const arrayBuffer = (blob as any).arrayBuffer
      ? (blob as any).arrayBuffer()
      : Promise.resolve(blob);

    const buffer: ArrayBuffer | Buffer = await arrayBuffer;
    if (buffer instanceof ArrayBuffer) {
      reader.result = Buffer.from(buffer).toString("binary");
    } else if (Buffer.isBuffer(buffer)) {
      reader.result = buffer.toString("binary");
    } else {
      reader.result = buffer as any;
    }

    if (reader.onload) {
      reader.onload({ target: reader });
    }
  }
}

/**
 * Simple mock FileReader for tests that don't need actual file reading.
 * Returns mock data immediately for unit tests.
 */
export class SimpleMockFileReader {
  onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  result: string | ArrayBuffer | null = null;

  readAsBinaryString(_file: Blob): void {
    // Simulate async file read with mock data
    setTimeout(() => {
      const onloadCallback = this.onload as ((event: any) => void) | null;
      if (onloadCallback) {
        onloadCallback({ target: { result: "mock binary data" } });
      }
    }, 0);
  }
}

/**
 * Install MockFileReader globally for tests.
 * Call this in beforeAll or at the top of test files.
 */
export function installMockFileReader(): void {
  (global as any).FileReader = MockFileReader;
}

/**
 * Install SimpleMockFileReader globally for tests.
 * Use for unit tests that don't need real file reading.
 */
export function installSimpleMockFileReader(): void {
  (global as any).FileReader = SimpleMockFileReader;
}

/**
 * Restore the original FileReader (if any).
 * Call this in afterAll to clean up.
 */
export function restoreFileReader(): void {
  delete (global as any).FileReader;
}
