REQS = flask httpx uwsgi

# Use eth2.0-specs v0.12.3
ETH2_SPEC_COMMIT = 7748c70c15b030ca42ad9fa94cdb96d3d9e3e6e6

install:
	if [ ! -d "eth2.0-specs" ]; then git clone https://github.com/ethereum/eth2.0-specs; fi
	cd eth2.0-specs && git reset --hard $(ETH2_SPEC_COMMIT)
	pip3 install $(REQS); pip3 install ./eth2.0-specs
	python3 -m venv venv; . venv/bin/activate; which python3; pip3 install $(REQS); pip3 install ./eth2.0-specs

docker:
	if [ ! -d "eth2.0-specs" ]; then git clone https://github.com/ethereum/eth2.0-specs; fi
	cd eth2.0-specs && git reset --hard $(ETH2_SPEC_COMMIT)
	pip3 install $(REQS); pip3 install ./eth2.0-specs
	python3 -m venv venv; . venv/bin/activate; which python3; pip3 install $(REQS); pip3 install ./eth2.0-specs

clean:
	rm -rf venv __pycache__ eth2.0-specs
