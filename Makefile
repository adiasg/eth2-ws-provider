REQS = flask httpx redis uwsgi pyyaml

# To use a specific Eth2 spec version, enter the commit hash here and uncomment relevant lines
# ETH2_SPEC_COMMIT =

install:
	if [ ! -d "eth2.0-specs" ]; then git clone https://github.com/ethereum/eth2.0-specs; fi
	# Uncomment the line below to use specific Eth2 spec version
	# cd eth2.0-specs && git reset --hard $(ETH2_SPEC_COMMIT)
	python3 -m venv venv; . venv/bin/activate; pip3 install $(REQS); pip3 install ./eth2.0-specs

docker:
	if [ ! -d "eth2.0-specs" ]; then git clone https://github.com/ethereum/eth2.0-specs; fi
	# Uncomment the line below to use specific Eth2 spec version
	# cd eth2.0-specs && git reset --hard $(ETH2_SPEC_COMMIT)
	pip3 install $(REQS); pip3 install ./eth2.0-specs

clean:
	rm -rf venv __pycache__ eth2.0-specs
