FROM node:lts
ARG FIREBASE_VERSION=13.3.0
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre bash curl jq && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    npm cache clean --force && \
    npm i -g firebase-tools@$FIREBASE_VERSION
WORKDIR /firebase
RUN npm i firebase-admin@$FIREBASE_VERSION yargs
COPY firebase.json /firebase/
COPY run_firebase_emulator.sh /firebase/
COPY create_firebase_emulator_auth_accounts.js /firebase/
RUN chmod +x /firebase/run_firebase_emulator.sh
CMD [ "/bin/bash" ]