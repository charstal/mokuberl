COMMONENVVAR=GOOS=$(shell uname -s | tr A-Z a-z) GOARCH=$(subst x86_64,amd64,$(patsubst i%86,386,$(shell uname -m)))
BUILDENVVAR=CGO_ENABLED=0

.PHONY: all
all: build

.PHONY: build
build:
	$(COMMONENVVAR) $(BUILDENVVAR) go build -o ./_output/mokuberl ./cmd/scheduler/main.go

.PHONY: clean
clean:
	rm -rf ./_output