MAJOR=0
MINOR=0
PATCH=1
VERSION=v$(MAJOR).$(MINOR).$(PATCH)

COMMONENVVAR=GOOS=$(shell uname -s | tr A-Z a-z) GOARCH=$(subst x86_64,amd64,$(patsubst i%86,386,$(shell uname -m)))
BUILDENVVAR=CGO_ENABLED=0

.PHONY: all
all: build

.PHONY: build
build:
	$(COMMONENVVAR) $(BUILDENVVAR) go build -o ./_output/schedule-extender ./cmd/scheduler/main.go

.PHONY: clean
clean:
	rm -rf ./_output

.PHONY: gen
gen:
	bash ./shell/code_gen.sh

.PHONY: image
image:
	docker build -t mokuberl:schedule-extender-$(VERSION) .