DC = docker compose
reqs = requirements.txt


compose:
	${DC} up -d --build


compile-core-requirements:
	poetry export -f ${reqs} --output ${reqs} --without music,dev --without-hashes

