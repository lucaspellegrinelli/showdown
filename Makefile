build:
	@docker build -t showdown .

run:
	@docker run -e PS_USERNAME=desafiobot -e PS_PASSWORD=desafiobot showdown
