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
image: build
	docker build -t scheduler-plugin-agent:$(VERSION) .

.PHONY: remote
remote: image
	docker tag scheduler-plugin-agent:$(VERSION) registry.cn-hangzhou.aliyuncs.com/charstal/scheduler-plugin-agent:$(VERSION)
	docker push registry.cn-hangzhou.aliyuncs.com/charstal/scheduler-plugin-agent:$(VERSION)
