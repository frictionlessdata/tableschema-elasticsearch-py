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
	curl -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ES_VER}.deb && sudo dpkg -i --force-confnew elasticsearch-${ES_VER}.deb
	sudo -i service elasticsearch start
	sleep 20 && curl localhost:9200
	pylama $(PACKAGE)
	tox

version:
	@echo $(VERSION)
