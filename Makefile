DC = docker compose



compose:
	${DC} up -d --build


reqs = requirements.txt
compile_settings = --output ${reqs} --without music,dev --without-hashes

compile-core-requirements:
	poetry export -f ${reqs} ${compile_settings}

