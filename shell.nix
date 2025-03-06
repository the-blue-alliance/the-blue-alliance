{ pkgs ? import <nixpkgs> { config = { allowUnfree = true; }; } }:

pkgs.mkShell {
  name = "the-blue-alliance-dev";
 
  buildInputs = with pkgs; [
    vagrant
    docker
    curl
    jq
    git
   
   # python3
    # python3Packages.pip
    # python3Packages.virtualenv
  ];

  shellHook = '' 

    echo "Setting up TBA API key..."
    source ./tba-key-setup.sh

    # Now you can use the VITE_TBA_API_READ_KEY variable
    echo "Using TBA API key: $VITE_TBA_API_READ_KEY"
    echo ""sTtIJYjJzRjZCvZFAx4awDXI2lSwZQWZlWP72S9nQ8Pec2GjY254vQ2e09h8yDhh
    echo "The Blue Alliance Development Environment"
    echo "----------------------------------------"
    echo "1. Start Vagrant: vagrant up"
    echo "   (Optional for Apple Silicon: use the local Dockerfile for better performance)"
    echo "2. (Optional, for auto-syncing) In a separate terminal, run: vagrant rsync-auto"
    echo "3. SSH into the container: vagrant ssh"
    echo "4. Attach to the tmux session: tmux attach"
    echo "5. (Optional) to ensure you can run all bash scripts you may want to add"
    echo "   services.envfs.enable=true to your nixos configuration"
    echo "   https://github.com/Mic92/envfs"
    echo "----------------------------------------"
    echo "Project directory inside the container: /tba"
      # Check docker and vagrant version to confirm installation
    docker --version || echo "Docker not found. Ensure it's installed and in your PATH."
    vagrant --version || echo "Vagrant not found. Ensure it's installed and in your PATH."

  '';
}
