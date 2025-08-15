# Goal:
- create a new .github/prompts/update-make-prompts.prompt.md that does the following procedure

## procedure:
- read the contents of .github/prompts/lint.prompt.md and .github/prompts/test.prompt.md
- open .github/prompts/VERSION and fetch INSTRUCTION_VERSION value which is in this format: YYYY-MM-DD.DAILY_INCREMENT_NUMBER
- analyze each file in .specstory/history/YYYY-MM-DD*.md, that have a filename start with a timestamp equal to or greater than INSTRUCTION_VERSION, one by one, for each history file do the following:
    - look for runs of `make test` or `make lint` 
    - determine if a new instruction is needed in the *.prompt.md file to address any issues that occurred running those commands
- update .github/prompts/lint.prompt.md and .github/prompts/test.prompt.md as needed
- run `date +%F` to get the current date in YYYY-MM-DD format
- update .github/prompts/VERSION to the new version using using the current date and YYYY-MM-DD.DAILY_INCREMENT_NUMBER  
  - If the current date is the same as the value already in INSTRUCTION_VERSION increment the DAILY_INCREMENT_NUMBER by 1

build the production stage docker image `docker build -t onboard:prod --target production .`
run that image `docker run -d --name onboard_prod_run -p 9830:9830 onboard:prod`
wait 20 seconds `sleep 20`
check the docker logs for the image for errors `docker logs onboard_prod_run`
stop the container `docker stop onboard_prod_run`
remove the container `docker rm -f onboard_prod_run`
fix errors and repeat till there are no errors building or in the logs