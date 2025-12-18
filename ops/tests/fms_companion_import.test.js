const fetch = require("node-fetch");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execSync } = require("child_process");
const crypto = require("crypto");
const FormData = require("form-data");

jest.setTimeout(60000);

describe("FMS Companion Import", () => {
  let eventKey = null;
  let authId = null;
  let authSecret = null;
  let tempDir = null;
  let storagePath = null;

  afterAll(() => {
    // Clean up temp file after all tests have run
    if (tempDir && fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
      tempDir = null;
    }
  });

  it("should create a test offseason event", async () => {
    const testEventKey = '2025test';

    const response = await fetch(
      `http://0.0.0.0:8080/local/create_test_event/${testEventKey}`,
      {
        method: "POST",
      }
    );

    expect(response.status).toEqual(200);

    const data = await response.json();
    expect(data).toHaveProperty("event_key");
    expect(data).toHaveProperty("auth_id");
    expect(data).toHaveProperty("auth_secret");
    expect(data.event_key).toMatch(/^\d{4}test$/);

    eventKey = data.event_key;
    authId = data.auth_id;
    authSecret = data.auth_secret;
  });

  it("should upload the companion DB file", async () => {
    expect(eventKey).not.toBeNull();
    expect(authId).not.toBeNull();
    expect(authSecret).not.toBeNull();

    // Read the test DB file
    const dbFilePath = path.join(__dirname, "tba-offseason-backup.sqlite");
    const dbFileContent = fs.readFileSync(dbFilePath);

    // Calculate SHA256 hash for authentication
    const hash = crypto.createHash("sha256");
    hash.update(dbFileContent);
    const fileDigest = hash.digest("hex");

    // Prepare the request
    const requestPath = `/api/_eventwizard/event/${eventKey}/fms_companion_db`;

    // Calculate auth signature
    const authString = `${authSecret}${requestPath}${fileDigest}`;
    const authSig = crypto.createHash("md5").update(authString).digest("hex");

    // Create form data
    const formData = new FormData();
    formData.append("companionDb", dbFileContent, {
      filename: "tba-offseason-backup.sqlite",
      contentType: "application/x-sqlite3",
    });
    formData.append("fileDigest", fileDigest);

    const response = await fetch(`http://0.0.0.0:8080${requestPath}`, {
      method: "POST",
      headers: {
        "X-TBA-Auth-Id": authId,
        "X-TBA-Auth-Sig": authSig,
        ...formData.getHeaders(),
      },
      body: formData,
    });

    expect(response.status).toEqual(200);

    const data = await response.json();
    expect(data).toHaveProperty("Success");
    storagePath = data.storage_path;
  });

  it("should run the companion import docker container", async () => {
    expect(storagePath).not.toBeNull();

    try {
      const output = execSync(
        `\
        docker run --rm \
          --env LOG_LEVEL=debug \
          --env TBA_URL=http://host.containers.internal:8080/api/trusted/v1 \
          --env TBA_TRUSTED_AUTH_ID=${authId} \
          --env TBA_TRUSTED_AUTH_SECRET=${authSecret} \
          phillopreiato/tba-offseason-companion-import:latest \
          http://host.containers.internal:8080/_ah/gcs/${storagePath}\
        `,
        {
          encoding: "utf-8",
          stdio: "pipe",
        }
      );

      // If we get here, the command executed successfully
      console.log("Docker container output:", output);
      expect(output).toBeDefined();
    } catch (error) {
      // Log the error output for debugging
      console.error("Docker execution failed:", error.message);
      if (error.stdout) console.error("stdout:", error.stdout);
      if (error.stderr) console.error("stderr:", error.stderr);
      throw error;
    }
  });
});
