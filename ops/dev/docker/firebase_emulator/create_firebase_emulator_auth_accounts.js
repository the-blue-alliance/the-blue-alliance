#!/usr/bin/env node

import { initializeApp } from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';
import yargs from 'yargs/yargs';
import { argv as _argv, env, exit } from 'process';

const argv = yargs(_argv.slice(2))
    .env('FIREBASE')
    .option('project', {
        description: 'Project ID for auth emulator',
        type: 'string',
        demandOption: true,
    })
    .option('auth-emulator-host', {
        description: 'Hostname + port for auth emulator',
        type: 'string',
        default: 'firebase:9099',
    })
    .help()
    .parse();

try {
    env.FIREBASE_AUTH_EMULATOR_HOST = argv.emulatorHost ?? "firebase:9099";
    console.log(`Targeting Auth emulator at: ${env.FIREBASE_AUTH_EMULATOR_HOST}`);
    console.log(`Using project ID: ${argv.project}`);

    initializeApp({
        projectId: argv.project,
    });

    const usersToImport = [
        {
            uid: '1',
            email: 'admin@thebluealliance.com',
            displayName: 'TBA Admin',
            providerData: [
                {
                    uid: '1',
                    providerId: 'google.com',
                    email: 'admin@thebluealliance.com',
                    displayName: 'TBA Admin',
                },
                {
                    uid: '1',
                    providerId: 'apple.com',
                    email: 'admin@thebluealliance.com',
                    displayName: 'TBA Admin',
                },
            ],
            customClaims: { admin: true },
        },
        {
            uid: '2',
            email: 'user@thebluealliance.com',
            displayName: 'TBA User',
            providerData: [
                {
                    uid: '2',
                    providerId: 'google.com',
                    email: 'user@thebluealliance.com',
                    displayName: 'TBA User',
                },
                {
                    uid: '2',
                    providerId: 'apple.com',
                    email: 'user@thebluealliance.com',
                    displayName: 'TBA User',
                },
            ],
            customClaims: {},
        },
    ];

    console.log(`Attempting to import ${usersToImport.length} users...`);

    const result = await getAuth().importUsers(usersToImport);

    console.log('\nImport operation completed.');
    if (result.successCount > 0) {
        console.log('✅ Successfully imported users:');
        result.users.forEach((user) => {
            console.log(`- User UID: ${user.uid}`);
        });
    }

    if (result.failureCount > 0) {
        console.log(`❌ Failed to import users:`);
        result.errors.forEach((err) => {
            console.error(`- User UID ${err.uid}: ${err.error.message}`);
        });
        exit(1);
    }
} catch (error) {
    console.error('💥 An error occurred:', error);
    exit(1);
}