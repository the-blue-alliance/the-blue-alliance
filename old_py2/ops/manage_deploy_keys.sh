#! /bin/bash

# A file to build a tarball of key files that get encrypted for travis
# Any file in here should MOST DEFINITELY be in .gitignore
# Run this script from the root of the repo. Use -c to build the archive, -x to extract

while getopts "cxd" o; do
    case "${o}" in
        c)
            echo "Creating key archive..."
            tar cvf ops/deploy_keys.tar static/javascript/tba_js/tba_keys.js ops/*deploy.json
            ;;
        x)
            echo "Extracting key archive..."
            tar xvf ops/deploy_keys.tar
            ;;
        d)
            echo "Fetching key bundle..."
            curl -o ops/deploy_keys.tar.enc $DEPLOY_KEY_FILE

            echo "Decrypting key bundle..."
            key="encrypted_${KEY_FILE_ENC_ID}_key"
            iv="encrypted_${KEY_FILE_ENC_ID}_iv"
            openssl aes-256-cbc -K ${!key} -iv ${!iv} -in ops/deploy_keys.tar.enc -out ops/deploy_keys.tar -d
            ;;
        *)
            exit -1
            ;;
    esac
done

