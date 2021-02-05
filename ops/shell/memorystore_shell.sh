#! /bin/bash
set -eE

# We need to connect to cloud memorystore using a jump compute VM
# This script will handle configuring the prod Google Cloud Resources
# (namely, starting the Compute Engine VM Jump Box and enabling the
# firewall rule allowing SSH from the public internet), and drop the
# user into a redis shell on the prod instance.
#
# Requirements to be installed locally: glcoud and jq

PROJECT="tbatv-prod-hrd"
FIREWALL_RULE="tba-memorystore-allow-ssh"
VM_NAME="redis-telnet-vm"
REDIS_NAME="tba-redis"
REDIS_REGION="us-central1"

DO_CLEANUP="true"

while test $# -gt 0; do
    case "$1" in
        -h|--help)
          echo "memorystore_shell.sh - a helpful wrapper script for connecting to Production Memorystore"
          echo " "
          echo "options:"
          echo "-h, --help                show help and exit"
          echo "--project=PROJECT         google cloud project to use, defaults to TBA prod"
          echo "--no-cleanup              skip turning down prod cloud resources after running"
          exit 0
          ;;
        --project*)
            PROJECT="${1//[^=]*=/}"
            shift
            ;;
        --no-cleanup)
            DO_CLEANUP="false"
            shift
            ;;
    esac 
done

cleanup_prod_resources() {
    echo ""

    if [ "$DO_CLEANUP" != "true" ] ; then
        echo "Skipping resource cleanup, don't forget!"
        exit 0
    fi

    echo "Cleaning up prod resources..."
    echo "Disabling SSH firewall rule..."
    gcloud --project "$PROJECT" compute firewall-rules update "$FIREWALL_RULE" --disabled

    echo "Disabling Jump Box VM..."
    gcloud --project "$PROJECT" compute instances stop "$VM_NAME"
}

trap 'cleanup_prod_resources' SIGINT
trap 'cleanup_prod_resources' ERR

# Make sure Firewall rule enabling SSH is enabled
ssh_disabled=$(gcloud --project "$PROJECT" compute firewall-rules describe --format json "$FIREWALL_RULE" | jq -r .disabled)
echo "SSH Firewall rule currently disabled?: $ssh_disabled"
if [ "$ssh_disabled" == "true" ] ; then
    echo "Enabling SSH firewall rule..."
    gcloud --project "$PROJECT" compute firewall-rules update "$FIREWALL_RULE" --no-disabled
fi

# Make sure jump box VM is up and running
vm_status=$(gcloud --project "$PROJECT" compute instances describe --format json "$VM_NAME" | jq -r .status)
echo "Jump Box VM Status: $vm_status"
if [ "$vm_status" == "TERMINATED" ] ; then
    echo "Starting VM..."
    gcloud --project "$PROJECT" compute instances start "$VM_NAME"
    echo "Waiting 15 seconds for VM to finish starting before attempting ssh..."
    sleep 15
elif [ "$vm_status" != "RUNNING" ] ; then
    echo "UNKNOWN VM STATE $vm_status"
    cleanup_prod_resources
    exit 1
fi

# Load the IP Address of redis
redis_ip=$(gcloud --project "$PROJECT" redis instances describe "$REDIS_NAME" --region "$REDIS_REGION" --format json | jq -r .host)
echo "Redis found at $redis_ip"

# SSH into jump box VM
echo "SSHing into Jump Box... Press ^D to exit redis shell"
gcloud --project "$PROJECT" compute ssh "$VM_NAME" -- redis-cli -h "$redis_ip"

cleanup_prod_resources
