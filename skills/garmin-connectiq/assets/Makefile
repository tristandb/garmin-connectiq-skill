# Generic Connect IQ Makefile.
#   make key                     create a developer key (once; keep keys/ out of git)
#   make build DEVICE=fr255      build bin/app-fr255.prg
#   make check PROXY=fenix7      compile against an installed device while a profile is missing
#   make test                    build with unit tests and run them in the simulator
#   make package                 Store package bin/app.iq (all devices in manifest.xml)
#   make deploy                  copy to a watch that mounts as a drive (/Volumes/GARMIN)
#   make deploy-mtp              copy to a watch that connects over MTP (needs: brew install libmtp)
#   make demo                    build a variant with the boolean property "demo" defaulting to true

SDK_DIR  := $(shell cat "$(HOME)/Library/Application Support/Garmin/ConnectIQ/current-sdk.cfg")
MONKEYC  := "$(SDK_DIR)bin/monkeyc"
MONKEYDO := "$(SDK_DIR)bin/monkeydo"
CONNECTIQ := "$(SDK_DIR)bin/connectiq"
APP      ?= app
DEVICE   ?= fr255
PROXY    ?= fenix7
KEY      := keys/developer_key.der
WATCH    ?= /Volumes/GARMIN/GARMIN/APPS
PROPS    := resources/settings/properties.xml

.PHONY: build check test package deploy deploy-mtp demo key clean

build: $(KEY)
	@mkdir -p bin
	$(MONKEYC) -d $(DEVICE) -f monkey.jungle -o bin/$(APP)-$(DEVICE).prg -y $(KEY) -w -l 1 -r

# Same screen size, different device: validates code when the real profile is not downloaded yet.
check: $(KEY)
	@mkdir -p bin
	@grep -v 'iq:product id="$(DEVICE)"' manifest.xml > bin/manifest-$(PROXY).xml
	@printf 'project.manifest = manifest-$(PROXY).xml\nbase.sourcePath = ../source\nbase.resourcePath = ../resources\n' > bin/$(PROXY).jungle
	$(MONKEYC) -d $(PROXY) -f bin/$(PROXY).jungle -o bin/$(APP)-$(PROXY).prg -y $(KEY) -w -l 1 -r

test: $(KEY)
	@mkdir -p bin
	$(MONKEYC) -d $(DEVICE) -f monkey.jungle -o bin/$(APP)-$(DEVICE)-test.prg -y $(KEY) -w -l 1 -t
	-pgrep -f "MacOS/simulator" >/dev/null || ($(CONNECTIQ) & sleep 8)
	$(MONKEYDO) bin/$(APP)-$(DEVICE)-test.prg $(DEVICE) -t

package: $(KEY)
	@mkdir -p bin
	$(MONKEYC) -e -f monkey.jungle -o bin/$(APP).iq -y $(KEY) -w -l 1 -r
	@echo "-> bin/$(APP).iq (upload at https://apps.garmin.com/developer/upload)"

deploy: build
	@test -d "$(WATCH)" || (echo "Watch not mounted at $(WATCH); if it connects as MTP use 'make deploy-mtp'" && exit 1)
	cp bin/$(APP)-$(DEVICE).prg "$(WATCH)/$(APP).prg"
	@echo "Copied. Eject the watch and unplug; it installs on disconnect."

deploy-mtp: build
	python3 scripts/mtp_send.py bin/$(APP)-$(DEVICE).prg

# The simulator keeps app settings between runs in $$TMPDIR/com.garmin.connectiq/GARMIN/APPS/SETTINGS/*.SET;
# delete that file after changing defaults.
demo: $(KEY)
	@mkdir -p bin
	@cp $(PROPS) bin/properties.xml.bak
	@sed -i '' 's#<property id="demo" type="boolean">false</property>#<property id="demo" type="boolean">true</property>#' $(PROPS)
	$(MONKEYC) -d $(DEVICE) -f monkey.jungle -o bin/$(APP)-$(DEVICE)-demo.prg -y $(KEY) -w -l 1; status=$$?; cp bin/properties.xml.bak $(PROPS); exit $$status

key:
	@mkdir -p keys
	openssl genrsa -out keys/developer_key.pem 4096
	openssl pkcs8 -topk8 -inform PEM -outform DER -in keys/developer_key.pem -out $(KEY) -nocrypt

$(KEY):
	@$(MAKE) key

clean:
	rm -rf bin
