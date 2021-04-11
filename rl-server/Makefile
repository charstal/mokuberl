MAJOR=0
MINOR=0
PATCH=2
VERSION=v$(MAJOR).$(MINOR).$(PATCH)

.PHONY: code_gen
gen: 
	bash ./shell/run_codegen.sh

.PHONY: image
image:
	docker build -t mokuberl:rl-server-$(VERSION) .