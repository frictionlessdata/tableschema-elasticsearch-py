.PHONY: all install list readme release templates test version


PACKAGE := $(shell grep '^PACKAGE =' setup.py | cut -d "'" -f2)
VERSION := $(shell head -n 1 $(PACKAGE)/VERSION)
LEAD := $(shell head -n 1 LEAD.md)


all: list

install:
	pip install --upgrade -e .[develop]

list:
	@grep '^\.PHONY' Makefile | cut -d' ' -f2- | tr ' ' '\n'

readme:
	pip install md-toc
	pip install referencer
	referencer $(PACKAGE) README.md --in-place
	md_toc -p README.md github --header-levels 3
	sed -i '/(#tableschema-elasticsearch-py)/,+2d' README.md

release:
	git checkout master && git pull origin && git fetch -p && git diff
	@echo "\nContinuing in 10 seconds. Press <CTRL+C> to abort\n" && sleep 10
	@git log --pretty=format:"%C(yellow)%h%Creset %s%Cgreen%d" --reverse -20
	@echo "\nReleasing v$(VERSION) in 10 seconds. Press <CTRL+C> to abort\n" && sleep 10
	git commit -a -m 'v$(VERSION)' && git tag -a v$(VERSION) -m 'v$(VERSION)'
	git push --follow-tags

templates:
	sed -i -E "s/@(\w*)/@$(LEAD)/" .github/issue_template.md
	sed -i -E "s/@(\w*)/@$(LEAD)/" .github/pull_request_template.md

test:
	docker run -d -p 9200:9200 --name es -e discovery.type=single-node -e xpack.security.enabled=false elasticsearch:${ES_VER}
	sleep 20 && curl localhost:9200
	pylama $(PACKAGE)
	py.test -vvv --cov tableschema_elasticsearch --cov-report term-missing || echo 'TESTING FAILED'
	docker stop es && docker rm es

version:
	@echo $(VERSION)
