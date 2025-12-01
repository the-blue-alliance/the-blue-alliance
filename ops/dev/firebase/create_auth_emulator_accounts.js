#!/usr/bin/env node

const admin = require("firebase-admin");

// Get configuration from environment variables
const project = process.env.PROJECT_ID;
const emulatorHost =
  process.env.FIREBASE_AUTH_EMULATOR_HOST || "localhost:9099";

if (!project) {
  console.error("Error: PROJECT_ID environment variable is required");
  process.exit(1);
}

// Set emulator host
process.env.FIREBASE_AUTH_EMULATOR_HOST = emulatorHost;

// Initialize Firebase Admin
admin.initializeApp({ projectId: project });

async function createAccounts() {
  try {
    const auth = admin.auth();

    // Admin user
    const adminUid = "1";
    const adminEmail = "admin@thebluealliance.com";
    const adminName = "TBA Admin";

    // Regular user
    const userUid = "2";
    const userEmail = "user@thebluealliance.com";
    const userName = "TBA User";

    // Import users
    await auth.importUsers([
      {
        uid: adminUid,
        email: adminEmail,
        displayName: adminName,
        providerData: [
          {
            uid: adminUid,
            providerId: "google.com",
            email: adminEmail,
            displayName: adminName,
          },
          {
            uid: adminUid,
            providerId: "apple.com",
            email: adminEmail,
            displayName: adminName,
          },
        ],
        customClaims: { admin: true },
      },
      {
        uid: userUid,
        email: userEmail,
        displayName: userName,
        providerData: [
          {
            uid: userUid,
            providerId: "google.com",
            email: userEmail,
            displayName: userName,
          },
          {
            uid: userUid,
            providerId: "apple.com",
            email: userEmail,
            displayName: userName,
          },
        ],
        customClaims: {},
      },
    ]);

    console.log("Successfully created auth emulator accounts");
    process.exit(0);
  } catch (error) {
    console.error("Error creating accounts:", error);
    process.exit(1);
  }
}

createAccounts();
