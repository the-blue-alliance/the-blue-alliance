The Blue Alliance Git Hooks
===========================
Copy/Paste the following files into .git/hooks to enable them

May need to run the following:
`chmod +x .git/hooks/<hook-file-name>`

post-checkout
-------------
- Runs every time you checkout a branch
- Recompiles CSS and JS

pre-commit
----------
- Runs every time you make a commit
- Checks Python code for certain PEP8 codes
- Requires PEP8 `easy_install pep8`
