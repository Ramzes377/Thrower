DC = docker compose


compose:
	${DC} up -d --build


compile-core-requirements:
	poetry export -f requirements.txt --output requirements.txt --without music,dev --without-hashes

